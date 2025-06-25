import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO


st.set_page_config(
    page_title="Social Media Performance Dashboard",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_data(uploaded_file):
    """Hàm để đọc và xử lý file Excel được tải lên"""
    try:
        df = pd.read_excel(uploaded_file)
        
        # Đổi tên các cột về tên chuẩn dùng cho dashboard
        df.rename(columns={
            'Total content publish': 'Total content put',
            'Video/ clip/ Reels': 'video clip',
            'Text + Ảnh': 'Reel Text + Ảnh',
            'Engagement (like/ cmt/ share)': 'Engagement',
        }, inplace=True)
        
        # Xử lý dữ liệu
        df['Kênh'] = df['Kênh'].ffill()
        df.dropna(subset=['Tuần'], inplace=True)
        df['Ngày Bắt Đầu'] = pd.to_datetime(df['Ngày Bắt Đầu'])
        
        # Chuyển các cột số về dạng numeric
        metric_cols = [
            'Follower', 'Lượt xem (views)', 'Engagement', 'Quan tâm OA',
            'Total content put', 'video clip', 'Reel Text + Ảnh', 'Back - text'
        ]
        for col in metric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Gộp tổng tương tác
        if 'Engagement' in df.columns and 'Quan tâm OA' in df.columns:
            df['Tổng tương tác'] = df['Engagement'] + df['Quan tâm OA']
        elif 'Engagement' in df.columns:
            df['Tổng tương tác'] = df['Engagement']
        elif 'Quan tâm OA' in df.columns:
            df['Tổng tương tác'] = df['Quan tâm OA']
        else:
            df['Tổng tương tác'] = 0
        
        return df
    except Exception as e:
        st.error(f"Lỗi khi xử lý file Excel: {e}")
        return None

def to_excel(df):
    """Hàm để chuyển đổi DataFrame sang file Excel trong bộ nhớ"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='FilteredData')
    processed_data = output.getvalue()
    return processed_data


# GIAO DIỆN DASHBOARD

st.title("📊 Dashboard Phân Tích Hiệu Suất Kênh Social Media")

# 1. Tải file lên
st.sidebar.header("Tải Dữ Liệu")
uploaded_file = st.sidebar.file_uploader("Chọn file Excel của bạn", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("💡 Vui lòng tải lên một file Excel để bắt đầu phân tích.")
    st.stop()

# Gọi hàm load_data
df = load_data(uploaded_file)

if df is None:
    st.warning("Không thể xử lý file Excel đã tải lên. Vui lòng kiểm tra lại định dạng file hoặc xem thông báo lỗi chi tiết ở trên.")
    st.stop()

# 2. Bộ lọc ở Sidebar
st.sidebar.header("Bộ Lọc:")

# Lọc theo Kênh
unique_channels = df['Kênh'].unique()
selected_channels = st.sidebar.multiselect(
    "Chọn Kênh:",
    options=unique_channels,
    default=unique_channels
)

# Lọc theo Thời gian
min_date = df['Ngày Bắt Đầu'].min().date()
max_date = df['Ngày Bắt Đầu'].max().date()
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

# 3. Lọc DataFrame dựa trên lựa chọn của người dùng
df_filtered = df[
    (df['Kênh'].isin(selected_channels)) &
    (df['Ngày Bắt Đầu'].dt.date >= start_date) &
    (df['Ngày Bắt Đầu'].dt.date <= end_date)
]

if df_filtered.empty:
    st.warning("Không có dữ liệu cho lựa chọn của bạn. Vui lòng thử lại với bộ lọc khác.")
    st.stop()

# ----- KPI & biểu đồ -----
st.header("Tổng Quan Hiệu Suất (Performance KPIs)")
total_views = int(df_filtered['Lượt xem (views)'].sum())
total_engagement = int(df_filtered['Tổng tương tác'].sum())
total_content = int(df_filtered['Total content put'].sum()) if 'Total content put' in df_filtered.columns else 0
latest_followers_per_channel = df_filtered.loc[df_filtered.groupby('Kênh')['Ngày Bắt Đầu'].idxmax()]
total_followers_end_period = int(latest_followers_per_channel['Follower'].sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Tổng Lượt xem (Views)", f"{total_views:,}")
col2.metric("Tổng Tương tác", f"{total_engagement:,}")
col3.metric("Follower (Cuối kỳ)", f"{total_followers_end_period:,}")
col4.metric("Tổng số bài đăng", f"{total_content:,}")

st.markdown("---")

# 5. Trực quan hóa dữ liệu
st.header("Phân Tích Chi Tiết")
c1, c2 = st.columns((6, 4)) # Cột trái rộng hơn

with c1:
    st.subheader("📈 Xu Hướng Theo Thời Gian")
    # Biểu đồ đường cho Lượt xem và Tương tác
    fig_trends = px.line(
        df_filtered,
        x='Ngày Bắt Đầu',
        y=['Lượt xem (views)', 'Tổng tương tác'],
        color='Kênh',
        title='Xu Hướng Lượt Xem và Tương Tác Hàng Tuần',
        labels={'value': 'Số lượng', 'Ngày Bắt Đầu': 'Ngày'},
        markers=True
    )
    fig_trends.update_layout(legend_title_text='Kênh')
    st.plotly_chart(fig_trends, use_container_width=True)

    # Biểu đồ đường cho Follower
    fig_followers = px.line(
        df_filtered,
        x='Ngày Bắt Đầu',
        y='Follower',
        color='Kênh',
        title='Tăng Trưởng Follower Hàng Tuần',
        labels={'Follower': 'Số lượng Follower', 'Ngày Bắt Đầu': 'Ngày'},
        markers=True
    )
    fig_followers.update_layout(legend_title_text='Kênh')
    st.plotly_chart(fig_followers, use_container_width=True)

with c2:
    st.subheader("📊 So Sánh Giữa Các Kênh")
    # Dữ liệu tổng hợp theo kênh
    df_grouped = df_filtered.groupby('Kênh').agg({
        'Lượt xem (views)': 'sum',
        'Tổng tương tác': 'sum',
        'Total content put': 'sum'
    }).reset_index()

    # Biểu đồ cột so sánh lượt xem
    fig_bar_views = px.bar(
        df_grouped.sort_values('Lượt xem (views)', ascending=False),
        x='Kênh',
        y='Lượt xem (views)',
        title='Tổng Lượt Xem Theo Kênh',
        text_auto=True,
        labels={'Lượt xem (views)': 'Tổng lượt xem'}
    )
    st.plotly_chart(fig_bar_views, use_container_width=True)

    # Biểu đồ cột so sánh tương tác
    fig_bar_eng = px.bar(
        df_grouped.sort_values('Tổng tương tác', ascending=False),
        x='Kênh',
        y='Tổng tương tác',
        title='Tổng Tương Tác Theo Kênh',
        text_auto=True,
        labels={'Tổng tương tác': 'Tổng tương tác'}
    )
    st.plotly_chart(fig_bar_eng, use_container_width=True)

# Phân tích cơ cấu nội dung
st.header("Phân Tích Cơ Cấu Nội Dung")
content_cols = ['video clip', 'Reel Text + Ảnh', 'Back - text']
content_totals = df_filtered[[col for col in content_cols if col in df_filtered.columns]].sum()
content_totals = content_totals[content_totals > 0]

if not content_totals.empty:
    fig_pie_content = px.pie(
        names=content_totals.index,
        values=content_totals.values,
        title='Tỷ Trọng Các Loại Nội Dung Đã Đăng (trong khoảng thời gian đã chọn)',
        hole=0.3
    )
    fig_pie_content.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie_content, use_container_width=True)
else:
    st.info("Không có dữ liệu về loại nội dung trong khoảng thời gian đã chọn.")

# 6. Hiển thị bảng dữ liệu chi tiết
st.markdown("---")
st.header("Bảng Dữ Liệu Chi Tiết")
st.dataframe(df_filtered)

# Nút tải xuống dữ liệu đã lọc
excel_data = to_excel(df_filtered)
st.download_button(
    label="📥 Tải xuống dữ liệu đã lọc (Excel)",
    data=excel_data,
    file_name=f"filtered_data_{start_date}_to_{end_date}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
