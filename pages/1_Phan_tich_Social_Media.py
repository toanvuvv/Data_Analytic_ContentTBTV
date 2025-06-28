import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.auth import check_password
# Nhập các hàm đã được tách ra từ module utils
from utils.data_processing import extract_social_data
from utils.plotting import (
    plot_trends_line_chart,
    plot_follower_growth_line_chart,
    plot_comparison_bar_chart,
    plot_content_pie_chart,
    plot_content_distribution_bar_chart # <-- THÊM HÀM MỚI
)
from utils.helpers import to_excel
st.set_page_config(layout="wide")
# ========================== CÁC HẰNG SỐ CẤU HÌNH ==========================
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

REQUIRED_METRICS = [
    "Follower", "Lượt xem (views)", "Engagement (like/ cmt/ share)",
    "Total content publish", "Video/ clips/ Reels", "Text + Ảnh", "Back + text"
]

CONTENT_METRICS = ["Video/ clips/ Reels", "Text + Ảnh", "Back + text"]
check_password()
st.set_page_config(layout="wide")

# Vị trí file tạm để lưu link Google Sheet cho trang Social
LINK_FILE_SOCIAL = "temp_social_gsheet_link.txt"

def save_link_social(link):
    """Lưu link vào file tạm."""
    try:
        with open(LINK_FILE_SOCIAL, "w") as f:
            f.write(link)
    except Exception as e:
        st.sidebar.warning(f"Không thể lưu link: {e}")

def load_link_social():
    """Đọc link từ file tạm nếu có."""
    if os.path.exists(LINK_FILE_SOCIAL):
        try:
            with open(LINK_FILE_SOCIAL, "r") as f:
                return f.read().strip()
        except Exception as e:
            st.sidebar.warning(f"Không thể đọc link đã lưu: {e}")
    return ""

def render_social_dashboard():
    """
    Hàm chính để render toàn bộ giao diện và logic của dashboard Social Media.
    """
    st.header("📊 Phân Tích Hiệu Suất Kênh Social Media")

    # ========================== NHẬP DỮ LIỆU (SIDEBAR) ==========================
    st.sidebar.header("Nhập Dữ Liệu Social")
    data_source = st.sidebar.radio(
        "Chọn nguồn dữ liệu:",
        options=['Upload file Excel', 'Google Sheet (link public share)'],
        horizontal=True,
        key="social_source"
    )

    key_cell_input = st.sidebar.text_input(
        "Nhập danh sách key cell (phân tách bởi dấu phẩy):", value="FB,TT,OA",
        key="social_keys"
    )
    key_cells = [s.strip().upper() for s in key_cell_input.split(",") if s.strip()]

    df_raw = None
    if data_source == 'Upload file Excel':
        uploaded_file = st.sidebar.file_uploader("Chọn file Excel của bạn", type=["xlsx", "xls"], key="social_uploader")
        if uploaded_file:
            try:
                df_raw = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
            except Exception as e:
                st.error(f"Lỗi khi xử lý file Excel: {e}")
                
    elif data_source == 'Google Sheet (link public share)':
        saved_link = load_link_social()
        sheet_url = st.sidebar.text_input(
            "Dán link Google Sheet đã share:", 
            value=saved_link, 
            key="social_gsheet"
        )
        
        if sheet_url:
            if sheet_url != saved_link:
                save_link_social(sheet_url)
            
            try:
                csv_export_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit', '/export?format=csv')
                df_raw = pd.read_csv(csv_export_url, header=None)
            except Exception as e:
                st.error(f"Lỗi khi đọc Google Sheet. Hãy chắc chắn link là public. Lỗi: {e}")

    if df_raw is None:
        st.info("💡 Vui lòng nhập dữ liệu cho dashboard Social Media để bắt đầu.")
        st.stop()

    # ========================== XỬ LÝ & CHUẨN HÓA DATA ==========================
    df_long = extract_social_data(df_raw, key_cells=key_cells, metric_mapping=METRIC_MAPPING)
    if df_long.empty:
        st.warning("Không trích xuất được dữ liệu hợp lệ. Vui lòng kiểm tra lại file đầu vào và các key cell.")
        st.stop()

    pivot_cols = ['Kênh', 'Tên kênh', 'Ngày Bắt Đầu', 'Ngày Kết Thúc', 'Mốc thời gian', 'Loại thời gian']
    df_wide = df_long.pivot_table(index=pivot_cols, columns='Chỉ số chuẩn', values='Giá trị', aggfunc='sum').reset_index()

    for col in REQUIRED_METRICS:
        if col not in df_wide.columns:
            df_wide[col] = 0
        else:
            df_wide[col] = pd.to_numeric(df_wide[col], errors='coerce').fillna(0)
            
    # Tính tổng số nội dung được đăng (Total content publish) từ các loại nội dung chi tiết
    df_wide['Total content publish'] = df_wide[CONTENT_METRICS].sum(axis=1)

    df_wide = df_wide[pivot_cols + REQUIRED_METRICS]

    # ========================== BỘ LỌC (SIDEBAR) ==========================
    st.sidebar.header("Bộ Lọc Social:")
    unique_channel_names = sorted(df_wide['Tên kênh'].unique())
    selected_channel_names = st.sidebar.multiselect(
        "Chọn Tên Kênh:",
        options=unique_channel_names,
        default=list(unique_channel_names),
        key="social_channels"
    )

    valid_dates = pd.to_datetime(df_wide['Ngày Bắt Đầu'], errors='coerce').dropna()
    if valid_dates.empty:
        st.error("Không có dữ liệu ngày hợp lệ trong file.")
        st.stop()

    min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
    selected_date_range = st.sidebar.date_input(
        "Chọn khoảng thời gian:",
        value=(min_date, max_date),
        min_value=min_date, max_value=max_date,
        format="DD/MM/YYYY",
        key="social_daterange"
    )

    if len(selected_date_range) != 2:
        st.warning("Vui lòng chọn đủ ngày bắt đầu và ngày kết thúc.")
        st.stop()
    start_date, end_date = selected_date_range

    df_filtered = df_wide[
        (df_wide['Tên kênh'].isin(selected_channel_names)) &
        (pd.to_datetime(df_wide['Ngày Bắt Đầu']).dt.date >= start_date) &
        (pd.to_datetime(df_wide['Ngày Bắt Đầu']).dt.date <= end_date)
    ].copy()

    if df_filtered.empty:
        st.warning("Không có dữ liệu cho lựa chọn của bạn.")
        st.stop()

    # ========================== KPI TỔNG QUAN ==========================
    st.subheader("Tổng Quan Hiệu Suất (Performance KPIs)")
    total_views = int(df_filtered["Lượt xem (views)"].sum())
    total_engagement = int(df_filtered["Engagement (like/ cmt/ share)"].sum())
    total_content = int(df_filtered["Total content publish"].sum())

    latest_followers_per_channel = df_filtered.sort_values(by='Ngày Bắt Đầu').groupby('Tên kênh').tail(1)
    total_followers_end_period = int(latest_followers_per_channel['Follower'].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Lượt xem (Views)", f"{total_views:,}")
    col2.metric("Tổng Tương tác (Engagement)", f"{total_engagement:,}")
    col3.metric("Follower (Cuối kỳ)", f"{total_followers_end_period:,}")
    col4.metric("Tổng số bài đăng", f"{total_content:,}")
    st.markdown("---")

    # ========================== BIỂU ĐỒ ==========================
    st.subheader("Phân Tích Chi Tiết")
    c1, c2 = st.columns((6, 4))

    with c1:
        st.write("#### 📈 Xu Hướng Theo Thời Gian")
        plot_trends_line_chart(st, df_filtered)
        plot_follower_growth_line_chart(st, df_filtered)

    with c2:
        st.write("#### 📊 So Sánh Hiệu Suất Giữa Các Kênh")
        df_grouped = df_filtered.groupby('Tên kênh').agg({
            "Lượt xem (views)": 'sum',
            "Engagement (like/ cmt/ share)": 'sum'
        }).reset_index()
        plot_comparison_bar_chart(st, df_grouped, 'Tên kênh', "Lượt xem (views)", "Tổng Lượt Xem Theo Tên Kênh")
        plot_comparison_bar_chart(st, df_grouped, 'Tên kênh', "Engagement (like/ cmt/ share)", "Tổng Tương Tác Theo Tên Kênh")
    
    st.markdown("---") # Thêm đường kẻ ngang phân tách

    # ======================= PHÂN TÍCH CƠ CẤU NỘI DUNG (CẬP NHẬT) =======================
    st.subheader("Phân Tích Cơ Cấu Nội Dung")
    # Biểu đồ tròn thể hiện cơ cấu nội dung tổng thể
    plot_content_pie_chart(st, df_filtered, CONTENT_METRICS)
    
    # Biểu đồ cột thể hiện tỷ trọng nội dung theo từng kênh (phần mới)
    plot_content_distribution_bar_chart(st, df_filtered, CONTENT_METRICS)


    # ========================== BẢNG CHI TIẾT & DOWNLOAD ==========================
    st.markdown("---")
    st.subheader("Bảng Dữ Liệu Chi Tiết")
    # Sắp xếp lại cột để dễ đọc hơn
    display_cols = pivot_cols + [col for col in REQUIRED_METRICS if col in df_filtered.columns]
    st.dataframe(df_filtered[display_cols])

    try:
        excel_data = to_excel(df_filtered)
        st.download_button(
            label="📥 Tải xuống dữ liệu đã lọc (Excel)",
            data=excel_data,
            file_name=f"social_filtered_data_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Lỗi khi tạo file Excel để tải xuống: {e}")

# Chạy hàm render chính
if __name__ == "__main__":
    render_social_dashboard()
