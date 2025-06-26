import plotly.express as px

def plot_trends_line_chart(st, df):
    """Vẽ biểu đồ line chart xu hướng Lượt xem và Tương tác."""
    try:
        y_cols = ["Lượt xem (views)", "Engagement (like/ cmt/ share)"]
        fig = px.line(
            df, x='Ngày Bắt Đầu', y=y_cols, color='Tên kênh',
            title='Xu Hướng Lượt Xem và Tương Tác',
            labels={'value': 'Số lượng', 'variable': 'Chỉ số', 'Ngày Bắt Đầu': 'Ngày'},
            markers=True
        )
        fig.update_layout(legend_title_text='Tên kênh')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ xu hướng: {e}")

def plot_follower_growth_line_chart(st, df):
    """Vẽ biểu đồ line chart tăng trưởng Follower."""
    try:
        fig = px.line(
            df, x='Ngày Bắt Đầu', y='Follower', color='Tên kênh',
            title='Tăng Trưởng Follower',
            labels={'Follower': 'Số lượng Follower', 'Ngày Bắt Đầu': 'Ngày'},
            markers=True
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
