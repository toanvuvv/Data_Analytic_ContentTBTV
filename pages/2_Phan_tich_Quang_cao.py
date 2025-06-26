import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Nhập các hàm đã được tách ra từ module utils
# Giả định các hàm này tồn tại, nếu không, chúng ta sẽ định nghĩa chúng ở đây
try:
    from utils.data_processing import extract_camp_blocks
    from utils.helpers import to_excel
except ImportError:
    # Fallback function if utils are not found
    def extract_camp_blocks(df):
        all_data = []
        current_camp = None
        date_cols = []
        for i, row in df.iterrows():
            if str(row.iloc[0]).lower().strip() == 'camp':
                current_camp = str(row.iloc[1]).strip() if pd.notnull(row.iloc[1]) else None
                date_cols = [v for v in row.iloc[2:].dropna() if str(v).strip().lower() != "tổng" and not str(v).strip().lower().startswith("tổng")]
                continue
            if current_camp and pd.notnull(row.iloc[1]) and str(row.iloc[1]).strip() != "":
                criteria = str(row.iloc[1]).strip()
                for idx, date in enumerate(date_cols):
                    value = row.iloc[idx + 2] if (idx + 2) < len(row) else None
                    if pd.isnull(value) or str(value).strip() == '':
                        value = 0
                    if pd.notnull(date):
                        all_data.append({'campaign': current_camp, 'criteria': criteria, 'date': date, 'value': value})
        return pd.DataFrame(all_data)

    from io import BytesIO
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='FilteredData')
        return output.getvalue()


# ========================== CẤU HÌNH TRANG ==========================
st.set_page_config(layout="wide")


# ========================== CÁC HẰNG SỐ CẤU HÌNH ==========================
DEFAULT_SHEETS = "duyanh,duc"

def render_campaign_dashboard():
    """
    Hàm chính để render toàn bộ giao diện và logic của dashboard Quảng cáo.
    """
    st.header("📈 Phân Tích Hiệu Suất Chiến Dịch Quảng Cáo")

    # ========================== NHẬP DỮ LIỆU (SIDEBAR) ==========================
    st.sidebar.header("Nhập Dữ Liệu Quảng Cáo")
    uploaded_file = st.sidebar.file_uploader("Chọn file Excel", type=["xlsx"], key="ad_uploader")
    
    sheets_input = st.sidebar.text_input(
        "Nhập tên các sheet cần phân tích (phân tách bởi dấu phẩy):",
        value=DEFAULT_SHEETS,
        key="ad_sheets"
    )
    sheets_to_read = [s.strip() for s in sheets_input.split(',') if s.strip()]

    if not uploaded_file:
        st.info("💡 Vui lòng upload file Excel chứa dữ liệu quảng cáo để bắt đầu.")
        st.stop()

    xls = pd.ExcelFile(uploaded_file)
    st.sidebar.write(f"File có {len(xls.sheet_names)} sheet:")
    st.sidebar.write(xls.sheet_names)
    st.sidebar.success(f"Sẽ phân tích các sheet: {sheets_to_read}")

    # ========================== ĐỌC & XỬ LÝ DỮ LIỆU ==========================
    all_df = []
    for sheet in sheets_to_read:
        if sheet not in xls.sheet_names:
            st.warning(f"Sheet '{sheet}' không tồn tại trong file Excel. Bỏ qua...")
            continue
        try:
            df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
            df_extracted = extract_camp_blocks(df_raw)
            if not df_extracted.empty:
                df_extracted['sheet'] = sheet
                all_df.append(df_extracted)
        except Exception as e:
            st.error(f"Lỗi khi đọc hoặc xử lý sheet '{sheet}': {e}")

    if not all_df:
        st.error("Không trích xuất được dữ liệu từ bất kỳ sheet nào. Vui lòng kiểm tra tên sheet và định dạng file.")
        st.stop()

    df_full = pd.concat(all_df, ignore_index=True)
    df_pivot = df_full.pivot_table(
        index=['sheet', 'campaign', 'date'],
        columns='criteria',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    df_pivot['date'] = pd.to_datetime(df_pivot['date'], errors='coerce')

    numeric_cols = [
        'Doanh số', 'Đầu tư ngân sách', 'KH Tiềm Năng (Mess)', 
        'Số Lượng Khách Hàng', 'Số đơn hàng'
    ]
    for col in numeric_cols:
        if col in df_pivot.columns:
            df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce').fillna(0)
        else:
            df_pivot[col] = 0
            
    # ========================== BỘ LỌC DỮ LIỆU (SIDEBAR) ==========================
    st.sidebar.header("Bộ lọc Dữ liệu")
    
    # --- Lấy giá trị cho bộ lọc ---
    min_date = df_pivot['date'].min().date()
    max_date = df_pivot['date'].max().date()
    unique_sheets = df_pivot['sheet'].unique()
    unique_campaigns = df_pivot['campaign'].unique()

    # --- Tạo các widget lọc ---
    selected_date_range = st.sidebar.date_input(
        "Lọc theo khoảng thời gian:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )
    
    selected_sheets = st.sidebar.multiselect("Lọc theo người chạy:", options=unique_sheets, default=unique_sheets)
    selected_campaigns = st.sidebar.multiselect("Lọc theo chiến dịch:", options=unique_campaigns, default=unique_campaigns)
    
    # --- Áp dụng bộ lọc ---
    if len(selected_date_range) != 2:
        st.warning("Vui lòng chọn đủ ngày bắt đầu và kết thúc.")
        st.stop()

    start_date, end_date = selected_date_range
    
    df_filtered = df_pivot[
        (df_pivot['date'].dt.date >= start_date) &
        (df_pivot['date'].dt.date <= end_date) &
        (df_pivot['sheet'].isin(selected_sheets)) &
        (df_pivot['campaign'].isin(selected_campaigns))
    ]

    if df_filtered.empty:
        st.warning("Không có dữ liệu nào phù hợp với bộ lọc của bạn. Vui lòng thử lại.")
        st.stop()

    # ========================== KPI TỔNG QUAN (DỰA TRÊN DỮ LIỆU ĐÃ LỌC) ==========================
    st.subheader("KPI Tổng quan (từ dữ liệu đã lọc)")
    tong_doanh_so = df_filtered['Doanh số'].sum()
    tong_ngan_sach = df_filtered['Đầu tư ngân sách'].sum()
    tong_kh_tiem_nang = df_filtered['KH Tiềm Năng (Mess)'].sum()
    tong_kh_moi = df_filtered['Số Lượng Khách Hàng'].sum()
    tong_don_hang = tong_kh_moi
    roas = tong_doanh_so / tong_ngan_sach if tong_ngan_sach > 0 else 0
    chi_phi_tren_mess = tong_ngan_sach / tong_kh_tiem_nang if tong_kh_tiem_nang > 0 else 0
    chi_phi_tren_kh_moi = tong_ngan_sach / tong_kh_moi if tong_kh_moi > 0 else 0
    ty_le_chuyen_doi = (tong_kh_moi / tong_kh_tiem_nang) * 100 if tong_kh_tiem_nang > 0 else 0
    gia_tri_tb_don = tong_doanh_so / tong_don_hang if tong_don_hang > 0 else 0
    giao_dich_tb_moi_kh = tong_don_hang / tong_kh_moi if tong_kh_moi > 0 else 0

    row1_col1, row1_col2, row1_col3, row1_col4, row1_col5 = st.columns(5)
    row1_col1.metric("Doanh số", f"{tong_doanh_so:,.0f} VNĐ")
    row1_col2.metric("Đầu tư ngân sách", f"{tong_ngan_sach:,.0f} VNĐ")
    row1_col3.metric("ROAS", f"{roas:.2f}")
    row1_col4.metric("KH Tiềm Năng (Mess)", f"{tong_kh_tiem_nang:,.0f}")
    row1_col5.metric("Chi phí / mess mới", f"{chi_phi_tren_mess:,.0f} VNĐ")

    row2_col1, row2_col2, row2_col3, row2_col4, row2_col5 = st.columns(5)
    row2_col1.metric("Số Lượng Khách Hàng", f"{tong_kh_moi:,.0f}")
    row2_col2.metric("Chi phí / KH mới (CAC)", f"{chi_phi_tren_kh_moi:,.0f} VNĐ")
    row2_col3.metric("Tỷ lệ chuyển đổi", f"{ty_le_chuyen_doi:.2f}%")
    row2_col4.metric("Giá Trị TB đơn (AOV)", f"{gia_tri_tb_don:,.0f} VNĐ")
    row2_col5.metric("Số GD TB / KH", f"{giao_dich_tb_moi_kh:.2f}")
    st.divider()

    # ========================== SO SÁNH HIỆU SUẤT (ĐÃ THIẾT KẾ LẠI) ==========================
    st.subheader("So sánh Hiệu suất")
    tab1, tab2 = st.tabs(["So sánh theo Người chạy Ads", "So sánh theo Chiến dịch"])

    with tab1:
        st.markdown("#### Phân tích tổng quan theo người chạy")
        df_sheet_sum = df_filtered.groupby('sheet').agg({
            'Doanh số': 'sum',
            'Đầu tư ngân sách': 'sum',
            'Số Lượng Khách Hàng': 'sum'
        }).reset_index()
        
        df_sheet_sum['ROAS'] = df_sheet_sum.apply(lambda r: r['Doanh số'] / r['Đầu tư ngân sách'] if r['Đầu tư ngân sách'] > 0 else 0, axis=1)
        df_sheet_sum['CAC'] = df_sheet_sum.apply(lambda r: r['Đầu tư ngân sách'] / r['Số Lượng Khách Hàng'] if r['Số Lượng Khách Hàng'] > 0 else 0, axis=1)
        
        if not df_sheet_sum.empty:
            fig_scatter = px.scatter(
                df_sheet_sum, x='CAC', y='ROAS', size='Doanh số', color='sheet',
                hover_name='sheet', size_max=50, title='Phân Tích Hiệu Quả Người Chạy (CAC vs. ROAS)',
                labels={'CAC': 'Chi phí / Khách hàng mới (VNĐ)', 'ROAS': 'Lợi nhuận trên chi tiêu quảng cáo'}
            )
            fig_scatter.add_annotation(text="<b>Góc lý tưởng</b><br>(Chi phí thấp, Lợi nhuận cao)",
                      align='left', showarrow=False, xref='paper', yref='paper', x=0.05, y=0.95)
            st.plotly_chart(fig_scatter, use_container_width=True)

            with st.expander("📘 Hướng dẫn đọc biểu đồ Phân Tích Hiệu Quả"):
                st.write("""
                Biểu đồ này giúp bạn đánh giá hiệu suất của từng người chạy quảng cáo dựa trên 2 chỉ số cốt lõi: **Chi phí để có một khách hàng mới (CAC)** và **Lợi nhuận trên chi tiêu quảng cáo (ROAS)**.
                
                - **Trục hoành (X - Chi phí / KH mới):** Càng sang trái càng tốt (chi phí thấp hơn).
                - **Trục tung (Y - ROAS):** Càng lên cao càng tốt (lợi nhuận cao hơn).
                - **Kích thước chấm tròn:** Thể hiện tổng **Doanh số** mà người đó mang về. Chấm càng to, doanh số càng lớn.
                
                **Vị trí lý tưởng** là ở góc trên bên trái của biểu đồ, nơi có chi phí thấp và lợi nhuận cao.
                """)
            
            fig_bar = px.bar(df_sheet_sum, x='sheet', y=['Doanh số', 'Đầu tư ngân sách'], barmode='group',
                             title="Tổng Doanh số và Ngân sách theo Người chạy", text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Không có dữ liệu của người chạy ads để hiển thị với bộ lọc hiện tại.")
        

    with tab2:
        st.markdown("#### Phân tích tổng quan theo chiến dịch")
        df_camp_sum = df_filtered.groupby(['sheet', 'campaign']).agg({
            'Doanh số': 'sum', 'Đầu tư ngân sách': 'sum'
        }).reset_index()
        df_camp_sum['ROAS'] = df_camp_sum.apply(lambda r: r['Doanh số'] / r['Đầu tư ngân sách'] if r['Đầu tư ngân sách'] > 0 else 0, axis=1)
        df_camp_sum = df_camp_sum[df_camp_sum['Doanh số'] > 0]
        
        if not df_camp_sum.empty:
            st.markdown("##### Cơ cấu Doanh số và Hiệu quả ROAS")
            fig_treemap = px.treemap(
                df_camp_sum, path=[px.Constant("Tất cả chiến dịch"), 'sheet', 'campaign'],
                values='Doanh số', color='ROAS', color_continuous_scale='RdYlGn',
                hover_data={'ROAS': ':.2f', 'Đầu tư ngân sách': ':,.0f'},
                title='Cơ Cấu Doanh Số & Hiệu Quả ROAS Theo Từng Chiến Dịch'
            )
            fig_treemap.update_traces(textinfo='label+value', textfont_size=14)
            st.plotly_chart(fig_treemap, use_container_width=True)
            
            with st.expander("📘 Hướng dẫn đọc biểu đồ Treemap"):
                st.write("""
                Biểu đồ Treemap cho bạn cái nhìn tổng quan về hiệu suất của **tất cả** các chiến dịch đã lọc.
                
                - **Kích thước của mỗi ô chữ nhật:** Tỷ lệ thuận với **Doanh số** mà chiến dịch đó tạo ra. Ô càng lớn, đóng góp doanh số càng nhiều.
                - **Màu sắc của ô:** Thể hiện chỉ số **ROAS**.
                    - **Màu xanh lá:** ROAS cao, chiến dịch hiệu quả.
                    - **Màu vàng:** ROAS trung bình.
                    - **Màu đỏ:** ROAS thấp, chiến dịch kém hiệu quả, cần xem xét tối ưu.
                
                Bạn có thể click vào các ô lớn (tên người chạy) để zoom vào xem chi tiết các chiến dịch của riêng người đó.
                """)

            st.markdown("##### Phân nhóm hiệu suất chiến dịch")
            fig_bubble = px.scatter(
                df_camp_sum, x='Đầu tư ngân sách', y='Doanh số', size='ROAS',
                color='sheet', hover_name='campaign', title="Phân Nhóm Hiệu Suất Chiến Dịch", size_max=60
            )
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("Không có dữ liệu chiến dịch để hiển thị với bộ lọc hiện tại.")

    # ========================== PHÂN TÍCH XU HƯỚNG ==========================
    st.subheader("Phân tích Xu hướng theo thời gian")
    
    if not df_filtered.empty:
        df_trend = df_filtered.groupby('date').agg({
            'Doanh số': 'sum', 'Đầu tư ngân sách': 'sum'
        }).reset_index()
        df_trend['ROAS'] = df_trend.apply(lambda r: r['Doanh số'] / r['Đầu tư ngân sách'] if r['Đầu tư ngân sách'] > 0 else 0, axis=1)
        df_trend = df_trend.sort_values('date')

        st.markdown("##### Xu hướng Doanh số, Ngân sách và ROAS")
        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        fig_trend.add_trace(go.Bar(x=df_trend['date'], y=df_trend['Đầu tư ngân sách'], name='Ngân sách', marker_color='lightsalmon'), secondary_y=False)
        fig_trend.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['Doanh số'], name='Doanh số', mode='lines+markers', line=dict(color='royalblue', width=3)), secondary_y=False)
        fig_trend.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['ROAS'], name='ROAS', mode='lines', line=dict(color='lightgreen', dash='dot')), secondary_y=True)

        fig_trend.update_layout(
            title_text='Xu Hướng Tổng Thể Theo Thời Gian',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_trend.update_xaxes(title_text="Ngày")
        fig_trend.update_yaxes(title_text="<b>Số tiền (VNĐ)</b>", secondary_y=False)
        fig_trend.update_yaxes(title_text="<b>ROAS</b>", secondary_y=True)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        with st.expander("📘 Hướng dẫn đọc biểu đồ Xu Hướng"):
            st.write("""
            Biểu đồ này kết hợp 3 chỉ số quan trọng để theo dõi diễn biến hiệu suất theo thời gian.
            
            - **Cột màu cam (Ngân sách):** Cho thấy lượng tiền bạn đã chi tiêu mỗi ngày.
            - **Đường màu xanh dương (Doanh số):** Thể hiện doanh số thu về tương ứng.
            - **Đường màu xanh lá (ROAS):** Nằm ở trục tung bên phải, cho biết hiệu quả đầu tư của bạn.
            
            **Mục tiêu phân tích:**
            - Xem xét khi tăng/giảm ngân sách thì doanh số có tăng/giảm tương ứng không.
            - Xác định các giai đoạn có ROAS cao đột biến (có thể do chiến dịch hiệu quả, sản phẩm hot) hoặc ROAS thấp (cần tìm nguyên nhân).
            - So sánh xu hướng giữa các khoảng thời gian khác nhau bằng cách thay đổi bộ lọc.
            """)
    else:
        st.info("Không có dữ liệu xu hướng để hiển thị với bộ lọc hiện tại.")


    # ========================== TẢI XUỐNG DỮ LIỆU ==========================
    st.subheader("Bảng Dữ liệu chi tiết (đã lọc)")
    st.dataframe(df_filtered)
    excel_data = to_excel(df_filtered)
    st.download_button(
        label="📥 Tải xuống dữ liệu đã lọc (.xlsx)",
        data=excel_data,
        file_name="filtered_ad_campaign_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Chạy hàm render chính
if __name__ == "__main__":
    render_campaign_dashboard()
