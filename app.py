import streamlit as st

st.set_page_config(
    page_title="Dashboard Tổng Hợp",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Dashboard Tổng Hợp")
st.write("Chào mừng bạn đến với hệ thống dashboard phân tích hiệu suất.")
st.info("Vui lòng chọn một dashboard từ thanh điều hướng bên trái để bắt đầu.", icon="👈")

st.sidebar.success("Chọn dashboard bạn muốn xem.")

# Streamlit sẽ tự động tìm và hiển thị các tệp trong thư mục 'pages'
# dưới dạng các trang điều hướng ở sidebar.
# Bạn không cần viết thêm code điều hướng ở đây.
