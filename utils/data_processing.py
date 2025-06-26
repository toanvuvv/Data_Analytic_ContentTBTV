import pandas as pd
import re
from datetime import datetime

def parse_week(week_str, year=None):
    """
    Hàm chuyển đổi chuỗi tuần 'dd/mm - dd/mm' thành datetime.
    Tự động phát hiện năm và xử lý trường hợp tuần跨năm.
    """
    if year is None:
        year = datetime.now().year
        
    m = re.match(r"(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})", str(week_str))
    if m:
        d1, m1, d2, m2 = map(int, m.groups())
        try:
            # Xử lý trường hợp tuần跨năm (ví dụ: 28/12/2023 - 03/01/2024)
            if m1 > m2:
                return datetime(year - 1, m1, d1), datetime(year, m2, d2)
            else:
                return datetime(year, m1, d1), datetime(year, m2, d2)
        except ValueError:
            return None, None
    return None, None

def extract_social_data(df, key_cells, metric_mapping):
    """
    Trích xuất và chuẩn hóa dữ liệu Social Media từ DataFrame thô.
    """
    rows = df.shape[0]
    all_data = []

    # Tìm dòng header chứa 'Chỉ số'
    header_row_idx = None
    for i in range(rows):
        # Cột thứ 3 (index 2)
        if str(df.iloc[i, 2]).strip().lower() == "chỉ số":
            header_row_idx = i
            break

    if header_row_idx is None:
        # Không tìm thấy header, không thể xử lý
        return pd.DataFrame()

    header_row = df.iloc[header_row_idx]
    # Lấy các cột thời gian từ dòng header
    time_cols = [j for j in range(3, df.shape[1]) if pd.notna(header_row[j])]

    # Xác định vị trí bắt đầu của từng kênh dựa trên key_cells
    channel_data = {}
    if key_cells:
        for i in range(rows):
            for j in range(df.shape[1]):
                cell_value = str(df.iloc[i, j]).strip().upper()
                if cell_value in key_cells:
                    channel_name = str(df.iloc[i, j + 1]).strip() if j + 1 < df.shape[1] and pd.notna(df.iloc[i, j + 1]) else cell_value
                    channel_data[i] = {"Kênh": cell_value, "Tên kênh": channel_name}
                    break

    # Duyệt qua các dòng dữ liệu để trích xuất chỉ số
    for r in range(header_row_idx + 1, rows):
        metric_raw = str(df.iloc[r, 2]).strip()
        if not metric_raw or metric_raw.lower().startswith("báo cáo"):
            continue

        # Xác định kênh hiện tại dựa vào vị trí dòng
        current_channel_info = {}
        for section_start_row, info in channel_data.items():
            if r >= section_start_row:
                current_channel_info = info
        
        if not current_channel_info:
            continue

        channel = current_channel_info.get("Kênh", "N/A")
        channel_name = current_channel_info.get("Tên kênh", "N/A")
        metric_standard = metric_mapping.get(metric_raw, metric_raw)

        # Lấy giá trị theo từng cột thời gian
        for c in time_cols:
            time_label = str(header_row[c]).strip()
            value = df.iloc[r, c]

            if pd.isna(value) or value == "":
                continue

            numeric_value = pd.to_numeric(value, errors='coerce')
            if pd.isna(numeric_value):
                continue

            start_date, end_date = parse_week(time_label)
            time_type = "Tháng" if "tháng" in time_label.lower() else "Tuần"

            all_data.append({
                "Kênh": channel, "Tên kênh": channel_name, "Chỉ số thô": metric_raw,
                "Chỉ số chuẩn": metric_standard, "Loại thời gian": time_type,
                "Mốc thời gian": time_label, "Ngày Bắt Đầu": start_date,
                "Ngày Kết Thúc": end_date, "Giá trị": numeric_value,
            })

    if not all_data:
        return pd.DataFrame()

    df_out = pd.DataFrame(all_data)
    df_out['Giá trị'] = pd.to_numeric(df_out['Giá trị'], errors='coerce').fillna(0)
    return df_out

def extract_camp_blocks(df):
    """
    Trích xuất dữ liệu từ các block campaign trong file quảng cáo.
    """
    all_data = []
    current_camp = None
    date_cols = []
    for i, row in df.iterrows():
        # Dòng bắt đầu block campaign
        if str(row.iloc[0]).lower().strip() == 'camp':
            current_camp = str(row.iloc[1]).strip() if pd.notnull(row.iloc[1]) else None
            # Lấy danh sách ngày, loại bỏ cột "Tổng"
            date_cols = [
                v for v in row.iloc[2:].dropna()
                if str(v).strip().lower() != "tổng" and not str(v).strip().lower().startswith("tổng")
            ]
            continue

        # Dòng chứa chỉ số
        if current_camp and pd.notnull(row.iloc[1]) and str(row.iloc[1]).strip() != "":
            criteria = str(row.iloc[1]).strip()
            for idx, date in enumerate(date_cols):
                value = row.iloc[idx + 2] if (idx + 2) < len(row) else None
                if pd.isnull(value) or str(value).strip() == '':
                    value = 0
                if pd.notnull(date):
                    all_data.append({
                        'campaign': current_camp, 'criteria': criteria,
                        'date': date, 'value': value
                    })
    return pd.DataFrame(all_data)
