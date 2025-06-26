import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import re
from datetime import datetime

st.set_page_config(
    page_title="Dashboard Phân Tích Hiệu Suất Kênh Social Media",
    page_icon="🗃️",
    layout="wide"
)

# ========================== CHUẨN HÓA TÊN CHỈ SỐ ==========================
# Ánh xạ các tên chỉ số có thể có từ file gốc sang tên chuẩn
# Giúp code linh hoạt hơn nếu tên trong file thay đổi nhẹ
METRIC_MAPPING = {
    "Follower": "Follower",
    "Lượt xem (views)": "Lượt xem (views)",
    "Engagement": "Engagement (like/ cmt/ share)",
    "Engagement (like/ cmt/ share)": "Engagement (like/ cmt/ share)",
    "Total content put": "Total content publish",
    "Total content publish": "Total content publish",
    "video clip": "Video/ clips/ Reels",
    "Video/ clips/ Reels": "Video/ clips/ Reels",
    "Reel Text + Ảnh": "Text + Ảnh",
    "Text + Ảnh": "Text + Ảnh",
    "Back - text": "Back + text",
    "Back + text": "Back + text"
}

# Danh sách các chỉ số chuẩn BẮT BUỘC phải có trong phân tích
REQUIRED_METRICS = [
    "Follower",
    "Lượt xem (views)",
    "Engagement (like/ cmt/ share)",
    "Total content publish",
    "Video/ clips/ Reels",
    "Text + Ảnh",
    "Back + text"
]

# Danh sách các cột chỉ số về loại nội dung
CONTENT_METRICS = [
    "Video/ clips/ Reels",
    "Text + Ảnh",
    "Back + text"
]


# ========================== HÀM XỬ LÝ DATA GỐC ==========================
def parse_week(week_str, year=None):
    """Hàm chuyển đổi chuỗi tuần 'dd/mm - dd/mm' thành datetime."""
    # THAY ĐỔI: Tự động phát hiện năm nếu không được cung cấp
    if year is None:
        year = datetime.now().year
        
    m = re.match(r"(\d{1,2})/(\d{1,2}) - (\d{1,2})/(\d{1,2})", str(week_str))
    if m:
        d1, m1, d2, m2 = map(int, m.groups())
        try:
            return datetime(year, m1, d1), datetime(year, m2, d2)
        except ValueError:
            # Xử lý trường hợp tuần跨năm (ví dụ: 28/12 - 03/01)
            try:
                if m1 > m2:
                    return datetime(year, m1, d1), datetime(year + 1, m2, d2)
                else:
                    return datetime(year, m1, d1), datetime(year, m2, d2)
            except ValueError:
                 return None, None
    return None, None

def extract_social_data(df, key_cells=None):
    """Trích xuất và chuẩn hóa dữ liệu từ DataFrame thô."""
    rows = df.shape[0]
    all_data = []

    header_row_idx = None
    for i in range(rows):
        # Cột thứ 3 (index 2) chứa 'Chỉ số'
        if str(df.iloc[i, 2]).strip().lower() == "chỉ số":
            header_row_idx = i
            break

    if header_row_idx is None:
        st.error("Lỗi: Không tìm thấy dòng tiêu đề 'Chỉ số' ở cột C. Vui lòng kiểm tra lại cấu trúc file.")
        return pd.DataFrame()

    header_row = df.iloc[header_row_idx]
    time_cols = [j for j in range(3, df.shape[1]) if pd.notna(header_row[j])]

    channel_data = {}
    if key_cells:
        for i in range(rows):
            for j in range(df.shape[1]):
                cell_value = str(df.iloc[i, j]).strip().upper()
                if cell_value in key_cells:
                    # Tên kênh thường ở ô kế bên
                    channel_name = str(df.iloc[i, j + 1]).strip() if j + 1 < df.shape[1] and pd.notna(df.iloc[i, j + 1]) else cell_value
                    channel_data[i] = {"Kênh": cell_value, "Tên kênh": channel_name}
                    break

    for r in range(header_row_idx + 1, rows):
        metric_raw = str(df.iloc[r, 2]).strip()
        if not metric_raw or metric_raw.lower().startswith("báo cáo"):
            continue

        current_channel_info = {}
        for section_start_row, info in channel_data.items():
            if r >= section_start_row:
                current_channel_info = info
        
        if not current_channel_info:
            continue

        channel = current_channel_info.get("Kênh", "N/A")
        channel_name = current_channel_info.get("Tên kênh", "N/A")
        
        metric_standard = METRIC_MAPPING.get(metric_raw, metric_raw)

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
                "Kênh": channel,
                "Tên kênh": channel_name,
                "Chỉ số thô": metric_raw,
                "Chỉ số chuẩn": metric_standard,
                "Loại thời gian": time_type,
                "Mốc thời gian": time_label,
                "Ngày Bắt Đầu": start_date,
                "Ngày Kết Thúc": end_date,
                "Giá trị": numeric_value,
            })

    if not all_data:
        return pd.DataFrame()

    df_out = pd.DataFrame(all_data)
    df_out['Giá trị'] = pd.to_numeric(df_out['Giá trị'], errors='coerce').fillna(0)
    return df_out

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='FilteredData')
    return output.getvalue()

# ========================== GIAO DIỆN DASHBOARD ==========================
st.title("📊 Dashboard Phân Tích Hiệu Suất Kênh Social Media")
st.sidebar.header("Nhập Dữ Liệu")

data_source = st.sidebar.radio(
    "Chọn nguồn dữ liệu:",
    options=['Upload file Excel', 'Google Sheet (link public share)'],
    horizontal=True
)

key_cell_input = st.sidebar.text_input(
    "Nhập danh sách key cell (phân tách bởi dấu phẩy):", value="FB,TT,OA"
)
key_cells = [s.strip().upper() for s in key_cell_input.split(",") if s.strip()]

df_raw = None
if data_source == 'Upload file Excel':
    uploaded_file = st.sidebar.file_uploader("Chọn file Excel của bạn", type=["xlsx", "xls"])
    if uploaded_file:
        try:
            df_raw = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        except Exception as e:
            st.error(f"Lỗi khi xử lý file Excel: {e}")
elif data_source == 'Google Sheet (link public share)':
    sheet_url = st.sidebar.text_input("Dán link Google Sheet đã share (Anyone with the link):")
    if sheet_url:
        try:
            csv_export_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit', '/export?format=csv')
            df_raw = pd.read_csv(csv_export_url, header=None)
        except Exception as e:
            st.error(f"Lỗi khi đọc Google Sheet. Hãy chắc chắn link là public và ở định dạng đúng. Lỗi: {e}")

if df_raw is None:
    st.info("💡 Vui lòng nhập dữ liệu để bắt đầu phân tích.")
    st.stop()

# ========== XỬ LÝ & CHUẨN HÓA DATA ==========z
df_long = extract_social_data(df_raw, key_cells=key_cells)
if df_long.empty:
    st.warning("Không trích xuất được dữ liệu hợp lệ. Vui lòng kiểm tra lại file đầu vào và các key cell đã nhập.")
    st.stop()

pivot_cols = ['Kênh', 'Tên kênh', 'Ngày Bắt Đầu', 'Ngày Kết Thúc', 'Mốc thời gian', 'Loại thời gian']
df_wide = df_long.pivot_table(index=pivot_cols, columns='Chỉ số chuẩn', values='Giá trị', aggfunc='sum').reset_index()

for col in REQUIRED_METRICS:
    if col not in df_wide.columns:
        df_wide[col] = 0
    else:
        df_wide[col] = pd.to_numeric(df_wide[col], errors='coerce').fillna(0)

df_wide = df_wide[pivot_cols + REQUIRED_METRICS]

# ========== BỘ LỌC ==========
st.sidebar.header("Bộ Lọc:")

# THAY ĐỔI: Lọc theo 'Tên kênh' thay vì 'Kênh'
unique_channel_names = sorted(df_wide['Tên kênh'].unique())
selected_channel_names = st.sidebar.multiselect(
    "Chọn Tên Kênh:", # THAY ĐỔI: Sửa lại nhãn
    options=unique_channel_names,
    default=list(unique_channel_names)
)

valid_dates = df_wide['Ngày Bắt Đầu'].dropna()
if valid_dates.empty:
    st.error("Không có dữ liệu ngày hợp lệ. Vui lòng kiểm tra định dạng ngày trong file.")
    st.stop()

min_date, max_date = valid_dates.min().date(), valid_dates.max().date()

selected_date_range = st.sidebar.date_input(
    "Chọn khoảng thời gian:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)

if len(selected_date_range) != 2:
    st.warning("Vui lòng chọn đủ ngày bắt đầu và ngày kết thúc.")
    st.stop()
start_date, end_date = selected_date_range

# THAY ĐỔI: Lọc dữ liệu theo 'Tên kênh' đã chọn
df_filtered = df_wide[
    (df_wide['Tên kênh'].isin(selected_channel_names)) &
    (df_wide['Ngày Bắt Đầu'].dt.date >= start_date) &
    (df_wide['Ngày Bắt Đầu'].dt.date <= end_date)
].copy()

if df_filtered.empty:
    st.warning("Không có dữ liệu cho lựa chọn của bạn. Vui lòng thử lại với bộ lọc khác.")
    st.stop()

# ========== KPI TỔNG QUAN ==========
st.header("Tổng Quan Hiệu Suất (Performance KPIs)")

total_views = int(df_filtered["Lượt xem (views)"].sum())
total_engagement = int(df_filtered["Engagement (like/ cmt/ share)"].sum())
total_content = int(df_filtered["Total content publish"].sum())

# THAY ĐỔI: Lấy follower cuối kỳ nhóm theo 'Tên kênh'
latest_followers_per_channel = df_filtered.sort_values('Ngày Bắt Đầu').groupby('Tên kênh').tail(1)
total_followers_end_period = int(latest_followers_per_channel['Follower'].sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Tổng Lượt xem (Views)", f"{total_views:,}")
col2.metric("Tổng Tương tác (Engagement)", f"{total_engagement:,}")
col3.metric("Follower (Cuối kỳ)", f"{total_followers_end_period:,}")
col4.metric("Tổng số bài đăng", f"{total_content:,}")

st.markdown("---")

# ========== BIỂU ĐỒ ==========
st.header("Phân Tích Chi Tiết")
c1, c2 = st.columns((6, 4))

with c1:
    st.subheader("📈 Xu Hướng Theo Thời Gian")
    y_cols_trends = ["Lượt xem (views)", "Engagement (like/ cmt/ share)"]
    try:
        fig_trends = px.line(
            df_filtered,
            x='Ngày Bắt Đầu',
            y=y_cols_trends,
            color='Tên kênh', # THAY ĐỔI: Phân màu theo 'Tên kênh'
            title='Xu Hướng Lượt Xem và Tương Tác',
            labels={'value': 'Số lượng', 'variable': 'Chỉ số', 'Ngày Bắt Đầu': 'Ngày'},
            markers=True
        )
        fig_trends.update_layout(legend_title_text='Tên kênh') # THAY ĐỔI
        st.plotly_chart(fig_trends, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ xu hướng: {e}")

    try:
        fig_followers = px.line(
            df_filtered,
            x='Ngày Bắt Đầu',
            y='Follower',
            color='Tên kênh', # THAY ĐỔI: Phân màu theo 'Tên kênh'
            title='Tăng Trưởng Follower',
            labels={'Follower': 'Số lượng Follower', 'Ngày Bắt Đầu': 'Ngày'},
            markers=True
        )
        fig_followers.update_layout(legend_title_text='Tên kênh') # THAY ĐỔI
        st.plotly_chart(fig_followers, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ follower: {e}")

with c2:
    st.subheader("📊 So Sánh Hiệu Suất Giữa Các Kênh")
    try:
        # THAY ĐỔI: Nhóm dữ liệu theo 'Tên kênh'
        df_grouped = df_filtered.groupby('Tên kênh').agg({
            "Lượt xem (views)": 'sum',
            "Engagement (like/ cmt/ share)": 'sum'
        }).reset_index()

        fig_bar_views = px.bar(
            df_grouped.sort_values("Lượt xem (views)", ascending=False),
            x='Tên kênh', # THAY ĐỔI
            y="Lượt xem (views)",
            title='Tổng Lượt Xem Theo Tên Kênh',
            text_auto=True,
            labels={"Lượt xem (views)": 'Tổng lượt xem', "Tên kênh": "Tên Kênh"}
        )
        st.plotly_chart(fig_bar_views, use_container_width=True)

        fig_bar_eng = px.bar(
            df_grouped.sort_values("Engagement (like/ cmt/ share)", ascending=False),
            x='Tên kênh', # THAY ĐỔI
            y="Engagement (like/ cmt/ share)",
            title='Tổng Tương Tác Theo Tên Kênh',
            text_auto=True,
            labels={"Engagement (like/ cmt/ share)": 'Tổng tương tác', "Tên kênh": "Tên Kênh"}
        )
        st.plotly_chart(fig_bar_eng, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ so sánh: {e}")

# ========== BIỂU ĐỒ CƠ CẤU NỘI DUNG ==========
st.header("Phân Tích Cơ Cấu Nội Dung")
try:
    content_totals = df_filtered[CONTENT_METRICS].sum()
    content_totals = content_totals[content_totals > 0] 

    if not content_totals.empty:
        fig_pie_content = px.pie(
            names=content_totals.index,
            values=content_totals.values,
            title='Tỷ Trọng Các Loại Nội Dung Đã Đăng',
            hole=0.3
        )
        fig_pie_content.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie_content, use_container_width=True)
    else:
        st.info("Không có dữ liệu về loại nội dung trong khoảng thời gian đã chọn.")
except Exception as e:
    st.error(f"Lỗi khi tạo biểu đồ cơ cấu nội dung: {e}")

# ========== BẢNG CHI TIẾT & DOWNLOAD ==========
st.markdown("---")
st.header("Bảng Dữ Liệu Chi Tiết")
st.dataframe(df_filtered)

try:
    excel_data = to_excel(df_filtered)
    st.download_button(
        label="📥 Tải xuống dữ liệu đã lọc (Excel)",
        data=excel_data,
        file_name=f"filtered_data_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
except Exception as e:
    st.error(f"Lỗi khi tạo file Excel để tải xuống: {e}")