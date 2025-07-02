

import plotly.express as px
import pandas as pd # Import pandas if not already imported

import plotly.express as px
import pandas as pd
import streamlit as st # Đảm bảo bạn đã import streamlit là 'st'

def plot_trends_interactive_line_charts(st, df):
    """
    Vẽ biểu đồ line chart xu hướng Lượt xem và Tương tác.
    Cho phép chọn kênh để xem và so sánh dễ dàng hơn.
    """
    try:
        all_channels = df['Tên kênh'].unique()
        
        # Thêm widget multiselect để người dùng chọn các kênh
        st.subheader("Chọn kênh để xem xu hướng Lượt xem và Tương tác:")
        selected_channels_trends = st.multiselect(
            'Kênh:',
            options=all_channels,
            default=list(all_channels) # Mặc định chọn tất cả các kênh
        )

        if not selected_channels_trends:
            st.info("Vui lòng chọn ít nhất một kênh để hiển thị biểu đồ xu hướng.")
            return

        # Lọc DataFrame chỉ với các kênh đã chọn
        df_filtered = df[df['Tên kênh'].isin(selected_channels_trends)]

        # Biểu đồ cho Lượt xem (views)
        st.subheader("Xu Hướng Lượt Xem")
        fig_views = px.line(
            df_filtered,
            x='Ngày Bắt Đầu',
            y="Lượt xem (views)",
            color='Tên kênh', # Giữ màu sắc để phân biệt các kênh trên cùng một biểu đồ
            title='Xu Hướng Lượt Xem Theo Kênh Được Chọn',
            labels={'value': 'Lượt xem', 'Ngày Bắt Đầu': 'Ngày'},
            markers=True,
            height=500 # Đặt chiều cao cố định để dễ nhìn
        )
        fig_views.update_layout(legend_title_text='Tên kênh')
        st.plotly_chart(fig_views, use_container_width=True)

        # Biểu đồ cho Engagement (like/ cmt/ share)
        st.subheader("Xu Hướng Tương Tác")
        fig_engagement = px.line(
            df_filtered,
            x='Ngày Bắt Đầu',
            y="Engagement (like/ cmt/ share)",
            color='Tên kênh', # Giữ màu sắc để phân biệt các kênh trên cùng một biểu đồ
            title='Xu Hướng Tương Tác Theo Kênh Được Chọn',
            labels={'value': 'Tương tác', 'Ngày Bắt Đầu': 'Ngày'},
            markers=True,
            height=500 # Đặt chiều cao cố định để dễ nhìn
        )
        fig_engagement.update_layout(legend_title_text='Tên kênh')
        st.plotly_chart(fig_engagement, use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ xu hướng: {e}")

def plot_follower_growth_interactive_line_chart(st, df):
    """
    Vẽ biểu đồ line chart tăng trưởng Follower.
    Cho phép chọn kênh để xem và so sánh dễ dàng hơn.
    """
    try:
        all_channels = df['Tên kênh'].unique()
        
        # Thêm widget multiselect để người dùng chọn các kênh
        st.subheader("Chọn kênh để xem tăng trưởng Follower:")
        selected_channels_follower = st.multiselect(
            'Kênh:',
            options=all_channels,
            default=list(all_channels), # Mặc định chọn tất cả các kênh
            key='follower_channels_select' # Đặt key duy nhất nếu có nhiều multiselect trên cùng một trang
        )

        if not selected_channels_follower:
            st.info("Vui lòng chọn ít nhất một kênh để hiển thị biểu đồ tăng trưởng Follower.")
            return

        # Lọc DataFrame chỉ với các kênh đã chọn
        df_filtered = df[df['Tên kênh'].isin(selected_channels_follower)]

        # Biểu đồ tăng trưởng Follower
        st.subheader("Tăng Trưởng Follower")
        fig = px.line(
            df_filtered,
            x='Ngày Bắt Đầu',
            y='Follower',
            color='Tên kênh', # Giữ màu sắc để phân biệt các kênh trên cùng một biểu đồ
            title='Tăng Trưởng Follower Theo Kênh Được Chọn',
            labels={'Follower': 'Số lượng Follower', 'Ngày Bắt Đầu': 'Ngày'},
            markers=True,
            height=500 # Đặt chiều cao cố định để dễ nhìn
        )
        fig.update_layout(legend_title_text='Tên kênh')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ follower: {e}")

def plot_comparison_bar_chart(st, df, x_col, y_col, title):
    """Vẽ biểu đồ cột để so sánh hiệu suất."""
    try:
        fig = px.bar(
            df.sort_values(y_col, ascending=False),
            x=x_col, y=y_col, title=title, text_auto=True,
            labels={y_col: 'Tổng giá trị', x_col: x_col}
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ so sánh '{title}': {e}")

def plot_content_pie_chart(st, df, content_metrics):
    """Vẽ biểu đồ tròn thể hiện cơ cấu nội dung."""
    try:
        content_totals = df[content_metrics].sum()
        content_totals = content_totals[content_totals > 0] 

        if not content_totals.empty:
            fig = px.pie(
                names=content_totals.index, values=content_totals.values,
                title='Tỷ Trọng Các Loại Nội Dung Đã Đăng', hole=0.3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Không có dữ liệu về loại nội dung trong khoảng thời gian đã chọn.")
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ cơ cấu nội dung: {e}")

def plot_performance_bar_chart(st, df_sheet_sum):
    """Vẽ biểu đồ Doanh số và Ngân sách theo người chạy."""
    st.markdown("#### Doanh số và Ngân sách theo người chạy")
    fig = px.bar(
        df_sheet_sum, x='sheet', y=['Doanh số', 'Đầu tư ngân sách'], barmode='group',
        title="Tổng Doanh số và Ngân sách theo Người chạy", text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_roas_bar_chart(st, df_sheet_sum):
    """Vẽ biểu đồ ROAS theo người chạy."""
    st.markdown("#### ROAS theo người chạy")
    fig = px.bar(
        df_sheet_sum, x='sheet', y='ROAS', title="So sánh ROAS giữa các Người chạy", text_auto='.2f'
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_cac_bar_chart(st, df_sheet_sum):
    """Vẽ biểu đồ Chi phí mỗi KH mới (CAC) theo người chạy."""
    if 'CAC' in df_sheet_sum.columns:
        st.markdown("#### Chi phí mỗi Khách hàng mới (CAC)")
        fig = px.bar(
            df_sheet_sum, x='sheet', y='CAC', title="Chi phí mỗi KH mới (CAC)", text_auto=',.0f'
        )
        st.plotly_chart(fig, use_container_width=True)

def plot_campaign_performance_bar(st, df_camp_sum):
    """Vẽ biểu đồ hiệu suất chiến dịch (Top ROAS và Doanh số)."""
    st.markdown("##### Top 10 chiến dịch theo ROAS")
    top_roas = df_camp_sum.sort_values('ROAS', ascending=False).head(10)
    fig_roas = px.bar(top_roas, x='campaign', y='ROAS', color='sheet', text_auto='.2f')
    st.plotly_chart(fig_roas, use_container_width=True)

    st.markdown("##### Top 10 chiến dịch theo Doanh số")
    top_sales = df_camp_sum.sort_values('Doanh số', ascending=False).head(10)
    fig_sales = px.bar(top_sales, x='campaign', y='Doanh số', color='sheet', text_auto=True)
    st.plotly_chart(fig_sales, use_container_width=True)

def plot_performance_bubble_chart(st, df_camp_sum):
    """Vẽ biểu đồ bong bóng thể hiện hiệu suất chiến dịch."""
    st.markdown("##### Biểu đồ Bong bóng (Ngân sách vs. Doanh số vs. ROAS)")
    df_plot = df_camp_sum[(df_camp_sum['Đầu tư ngân sách'] > 0) & (df_camp_sum['Doanh số'] > 0)]
    if not df_plot.empty:
        fig = px.scatter(
            df_plot, x='Đầu tư ngân sách', y='Doanh số', size='ROAS',
            color='sheet', hover_name='campaign',
            title="Phân nhóm hiệu suất chiến dịch", size_max=60
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không đủ dữ liệu để vẽ biểu đồ bong bóng.")

def plot_time_series_line_chart(st, df, metric, group_by):
    """Vẽ biểu đồ xu hướng theo thời gian cho các chỉ số quảng cáo."""
    fig = px.line(
        df.sort_values('date'), x='date', y=metric, color=group_by,
        title=f"Xu hướng {metric} theo thời gian", markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
import streamlit as st
import pandas as pd
import plotly.express as px

# (Các hàm plot khác của bạn ở đây...)

def plot_content_distribution_bar_chart(st, df, content_columns):
    """
    Vẽ biểu đồ cột nhóm thể hiện tỷ trọng các loại nội dung trên từng kênh.
    df: DataFrame ở dạng wide, đã được lọc.
    content_columns: list các cột chứa số lượng của từng loại nội dung.
    """
    st.write("#### 📊 Tỷ Trọng Loại Nội Dung Theo Kênh")

    # 1. Chỉ chọn các cột cần thiết: Tên kênh và các cột nội dung, sau đó tính tổng cho mỗi kênh
    df_content = df[['Tên kênh'] + content_columns].copy()
    df_grouped = df_content.groupby('Tên kênh')[content_columns].sum().reset_index()

    # 2. Chuyển từ định dạng wide sang long để dễ vẽ biểu đồ
    df_melted = df_grouped.melt(
        id_vars=['Tên kênh'], 
        value_vars=content_columns, 
        var_name='Loại nội dung', 
        value_name='Số lượng'
    )

    # 3. Tính tổng số bài đăng cho mỗi kênh để tính tỷ lệ phần trăm
    # Dùng transform để broadcast tổng số bài đăng về lại cho mỗi dòng của kênh tương ứng
    df_melted['Tổng bài đăng'] = df_melted.groupby('Tên kênh')['Số lượng'].transform('sum')
    
    # 4. Tính tỷ lệ phần trăm, tránh lỗi chia cho 0
    df_melted['Tỷ lệ (%)'] = (df_melted['Số lượng'] / df_melted['Tổng bài đăng'].replace(0, 1)) * 100

    # 5. Vẽ biểu đồ
    fig = px.bar(
        df_melted,
        x='Tên kênh',
        y='Tỷ lệ (%)',
        color='Loại nội dung',
        barmode='group',
        title='Phân Bổ Tỷ Lệ Các Loại Nội Dung Theo Kênh',
        labels={
            'Tỷ lệ (%)': 'Tỷ lệ (%)',
            'Tên kênh': 'Kênh',
            'Loại nội dung': 'Loại Nội Dung'
        },
        text=df_melted['Tỷ lệ (%)'].apply(lambda x: f'{x:.1f}%'),
        height=500,
        color_discrete_map={ # Bạn có thể tùy chỉnh màu sắc ở đây
             "Video/ clips/ Reels": "#1f77b4",
             "Text + Ảnh": "#ff7f0e",
             "Back + text": "#2ca02c"
         }
    )

    # Tùy chỉnh giao diện biểu đồ
    fig.update_layout(
        xaxis_title='Kênh',
        yaxis_title='Tỷ lệ phân phối (%)',
        legend_title='Loại Nội Dung',
        yaxis=dict(ticksuffix='%'),
        uniformtext_minsize=8, 
        uniformtext_mode='hide',
        xaxis={'categoryorder':'total descending'} # Sắp xếp các kênh theo tổng tỷ lệ
    )
    fig.update_traces(textposition='outside')

    st.plotly_chart(fig, use_container_width=True)

