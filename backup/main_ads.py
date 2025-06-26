import streamlit as st
import pandas as pd
from io import BytesIO, StringIO
import plotly.express as px

st.set_page_config(page_title="Ad Campaign Dashboard", layout="wide")

st.sidebar.title("Upload file Excel")
uploaded_file = st.sidebar.file_uploader("Chọn file Excel", type=["xlsx"])

# HARD-CODE DANH SÁCH NHÂN VIÊN (sheet name)
# Thay đổi tên sheet cho phù hợp với file của bạn
SHEETS_TO_READ = ["duyanh","duc"]  # Thêm/xóa tên sheet ở đây

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    st.sidebar.write(f"File có {len(xls.sheet_names)} sheet:")
    st.sidebar.write(xls.sheet_names)
    st.sidebar.success(f"Sẽ phân tích các sheet: {SHEETS_TO_READ}")
else:
    st.info("Vui lòng upload file Excel để bắt đầu phân tích.")
    st.stop() # Dừng thực thi nếu chưa có file

# =========== 2. Extract dữ liệu (function) ==============
def extract_camp_blocks(df):
    """
    Trích xuất dữ liệu từ các block campaign,
    Loại bỏ cột Tổng khi lấy date_cols.
    """
    all_data = []
    current_camp = None
    date_cols = []
    for i, row in df.iterrows():
        # Nếu là dòng bắt đầu campaign
        if str(row.iloc[0]).lower().strip() == 'camp':
            current_camp = str(row.iloc[1]).strip() if pd.notnull(row.iloc[1]) else None
            # Lọc chỉ lấy các giá trị là ngày, loại bỏ "Tổng"
            date_cols = [
                v for v in row.iloc[2:].dropna()
                if str(v).strip().lower() != "tổng" and not str(v).strip().lower().startswith("tổng")
            ]
            continue

        # Nếu đã xác định block campaign, và dòng này là chỉ số (cột B có tên chỉ số)
        if current_camp and pd.notnull(row.iloc[1]) and str(row.iloc[1]).strip() != "":
            criteria = str(row.iloc[1]).strip()
            for idx, date in enumerate(date_cols):
                value = row.iloc[idx+2] if (idx+2)<len(row) else None
                # Nếu value bị rỗng/null/chuỗi trắng, chuyển thành 0
                if pd.isnull(value) or str(value).strip() == '':
                    value = 0
                if pd.notnull(date):
                    all_data.append({
                        'campaign': current_camp,
                        'criteria': criteria,
                        'date': date,
                        'value': value
                    })
    return pd.DataFrame(all_data)


# =========== 3. Đọc & xử lý dữ liệu ===========
if uploaded_file:
    all_df = []
    # st.divider()
    # st.header("🔬 Quá trình xử lý & Debug")

    for sheet in SHEETS_TO_READ:
        # st.subheader(f"Đang xử lý Sheet: '{sheet}'")
        try:
            # Đọc file không có header
            df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
            
            # # --- DEBUG: HIỂN THỊ DỮ LIỆU THÔ ---
            # st.write(f"🐞 **DEBUG 1:** Dữ liệu thô đọc từ sheet '{sheet}' (5 dòng đầu)")
            # st.dataframe(df_raw.head())

            # Bỏ qua dòng header gốc và reset index
            df = df_raw.copy() # Sử dụng copy để tránh SettingWithCopyWarning
            df = df.reset_index(drop=True)

            # Trích xuất dữ liệu
            df_extracted = extract_camp_blocks(df)

            # # --- DEBUG: HIỂN THỊ DỮ LIỆU ĐÃ TRÍCH XUẤT ---
            # st.write(f"🐞 **DEBUG 2:** Dữ liệu đã trích xuất từ sheet '{sheet}'")
            if not df_extracted.empty:
                # st.dataframe(df_extracted)
                df_extracted['sheet'] = sheet
                all_df.append(df_extracted)
            # else:
                # st.warning(f"Không có dữ liệu nào được trích xuất từ sheet '{sheet}'. Vui lòng kiểm tra định dạng.")

        except Exception as e:
            st.error(f"Lỗi khi đọc hoặc xử lý sheet '{sheet}': {e}")

    # === Kiểm tra sau khi trích xuất từ tất cả các sheet ===
    if not all_df:
        st.error("Không trích xuất được dữ liệu từ bất kỳ sheet nào được chỉ định. Vui lòng kiểm tra lại tên sheet và định dạng file.")
        st.stop()

    # Ghép các dataframe lại
    df_full = pd.concat(all_df, ignore_index=True)

    # # --- DEBUG: HIỂN THỊ DỮ LIỆU TỔNG HỢP ---
    # st.subheader("Tổng hợp dữ liệu từ các sheet")
    # st.write("🐞 **DEBUG 3:** Dữ liệu tổng hợp từ tất cả các sheet (trước khi xoay bảng)")
    # st.dataframe(df_full)

    # Xoay bảng để các chỉ số thành cột
    df_pivot = df_full.pivot_table(
        index=['sheet', 'campaign', 'date'],
        columns='criteria',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Chuyển đổi kiểu dữ liệu cho các cột số liệu quan trọng
    # Danh sách các cột cần chuyển đổi, bạn có thể thêm/bớt nếu cần
    numeric_cols = ['Doanh số', 'Đầu tư ngân sách', 'Chi phí KH mới', 'KH Tiềm Năng (Mess)']
    for col in numeric_cols:
        if col in df_pivot.columns:
            # errors='coerce' sẽ biến các giá trị không phải số thành NaN (Not a Number)
            df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce')

    # # --- DEBUG: HIỂN THỊ DỮ LIỆU SAU KHI PIVOT ---
    # st.write("🐞 **DEBUG 4:** Dữ liệu sau khi xoay bảng (pivot) và chuyển đổi kiểu dữ liệu")
    # st.dataframe(df_pivot)
    
    # # Ghi lại thông tin kiểu dữ liệu để kiểm tra
    # st.write("Kiểu dữ liệu của các cột sau khi xử lý:")
    # # Chuyển dtypes thành chuỗi để st.text có thể hiển thị
    # buffer = StringIO()
    # df_pivot.info(buf=buffer)
    # s = buffer.getvalue()
    # st.text(s)


    # =========== TÍNH TOÁN KPI TỔNG QUAN =============
    # Fillna(0) để các phép tính không bị lỗi nếu có giá trị rỗng
    tong_doanh_so = df_pivot['Doanh số'].sum() if 'Doanh số' in df_pivot.columns else 0
    tong_ngan_sach = df_pivot['Đầu tư ngân sách'].sum() if 'Đầu tư ngân sách' in df_pivot.columns else 0
    # Dùng .sum() vì KH Tiềm Năng (Mess) đã được tách ra theo ngày
    tong_kh_moi = df_pivot['KH Tiềm Năng (Mess)'].sum() if 'KH Tiềm Năng (Mess)' in df_pivot.columns else 0
    roas = tong_doanh_so / tong_ngan_sach if tong_ngan_sach > 0 else 0

    st.divider()
    # =========== II. MAIN AREA - DASHBOARD =============
    st.header("📊 Dashboard Quản lý Quảng cáo")
    st.subheader("KPI Tổng quan")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Doanh số", f"{tong_doanh_so:,.0f} VNĐ")
    col2.metric("Tổng Ngân sách", f"{tong_ngan_sach:,.0f} VNĐ")
    col3.metric("ROAS Tổng thể", f"{roas:.2f}")
    col4.metric("Tổng Số KH Mới (Mess)", f"{tong_kh_moi:,.0f}")

    st.divider()
    st.subheader("So sánh Hiệu suất")
    tab1, tab2 = st.tabs(["So sánh theo Người chạy Ads", "So sánh theo Chiến dịch"])

    with tab1:
        st.markdown("#### Doanh số, Ngân sách và ROAS theo người chạy")
        # Gom nhóm theo sheet (người chạy)
        df_sheet_sum = df_pivot.groupby('sheet').agg({
            'Doanh số': 'sum',
            'Đầu tư ngân sách': 'sum',
            'KH Tiềm Năng (Mess)': 'sum'
        }).reset_index()
        
        df_sheet_sum['ROAS'] = df_sheet_sum['Doanh số'] / df_sheet_sum['Đầu tư ngân sách']
        # Tính CAC (Chi phí cho mỗi khách hàng mới)
        if 'KH Tiềm Năng (Mess)' in df_sheet_sum.columns:
            df_sheet_sum['CAC'] = df_sheet_sum['Đầu tư ngân sách'] / df_sheet_sum['KH Tiềm Năng (Mess)']


        fig = px.bar(df_sheet_sum, x='sheet', y=['Doanh số', 'Đầu tư ngân sách'], barmode='group',
                     title="Tổng Doanh số và Ngân sách theo Người chạy", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.bar(df_sheet_sum, x='sheet', y='ROAS', title="So sánh ROAS giữa các Người chạy", text_auto='.2f')
        st.plotly_chart(fig2, use_container_width=True)
        
        if 'CAC' in df_sheet_sum.columns:
            fig3 = px.bar(df_sheet_sum, x='sheet', y='CAC', title="Chi phí mỗi KH mới (CAC)", text_auto=',.0f')
            st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        st.markdown("#### Phân tích hiệu suất các chiến dịch")
        # Tính toán trên từng chiến dịch
        df_camp_sum = df_pivot.groupby(['sheet', 'campaign']).agg({
             'Doanh số': 'sum',
            'Đầu tư ngân sách': 'sum'
        }).reset_index()
        df_camp_sum['ROAS'] = df_camp_sum['Doanh số'] / df_camp_sum['Đầu tư ngân sách']
        df_camp_sum = df_camp_sum.sort_values('ROAS', ascending=False)
        
        st.markdown("##### Top 10 chiến dịch theo ROAS")
        top_roas = df_camp_sum.head(10)
        fig4 = px.bar(top_roas, x='campaign', y='ROAS', color='sheet', text_auto='.2f')
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown("##### Top 10 chiến dịch theo Doanh số")
        top_sales = df_camp_sum.sort_values('Doanh số', ascending=False).head(10)
        fig5 = px.bar(top_sales, x='campaign', y='Doanh số', color='sheet', text_auto=True)
        st.plotly_chart(fig5, use_container_width=True)

        st.markdown("##### Biểu đồ Bong bóng (Ngân sách vs. Doanh số vs. ROAS)")
        # Loại bỏ các chiến dịch không có ngân sách hoặc doanh số để biểu đồ rõ ràng hơn
        df_camp_plot = df_camp_sum[(df_camp_sum['Đầu tư ngân sách'] > 0) & (df_camp_sum['Doanh số'] > 0)]
        fig6 = px.scatter(
            df_camp_plot,
            x='Đầu tư ngân sách',
            y='Doanh số',
            size='ROAS',
            color='sheet',
            hover_name='campaign',
            title="Phân nhóm hiệu suất chiến dịch",
            size_max=60
        )
        st.plotly_chart(fig6, use_container_width=True)


    st.subheader("Phân tích Xu hướng theo thời gian")
    # Đảm bảo cột date có định dạng datetime để sắp xếp đúng
    df_pivot['date'] = pd.to_datetime(df_pivot['date'], errors='coerce')
    df_pivot_time = df_pivot.dropna(subset=['date'])

    # Thêm lựa chọn tính ROAS vào df_pivot_time
    if 'Doanh số' in df_pivot_time.columns and 'Đầu tư ngân sách' in df_pivot_time.columns:
        # Tránh chia cho 0
        df_pivot_time['ROAS'] = df_pivot_time.apply(
            lambda row: row['Doanh số'] / row['Đầu tư ngân sách'] if row['Đầu tư ngân sách'] > 0 else 0,
            axis=1
        )
        metrics = ['Doanh số', 'Đầu tư ngân sách', 'ROAS']
    else:
        metrics = ['Doanh số', 'Đầu tư ngân sách']


    metric = st.selectbox("Chọn chỉ số để xem xu hướng", metrics)
    group_by = st.radio("Nhóm theo", ['sheet', 'campaign'], horizontal=True)

    fig7 = px.line(
        df_pivot_time.sort_values('date'),
        x='date',
        y=metric,
        color=group_by,
        title=f"Xu hướng {metric} theo thời gian",
        markers=True
    )
    st.plotly_chart(fig7, use_container_width=True)


    st.subheader("Tải xuống Dữ liệu chi tiết đã xử lý")
    st.dataframe(df_pivot)
    out_buffer = BytesIO()
    # Chuyển df_pivot sang excel và ghi vào buffer
    with pd.ExcelWriter(out_buffer, engine='xlsxwriter') as writer:
        df_pivot.to_excel(writer, index=False, sheet_name='processed_data')
    
    st.download_button(
        label="Tải dữ liệu đã xử lý (.xlsx)",
        data=out_buffer.getvalue(),
        file_name="data_processed.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
