# utils/auth.py

import streamlit as st

def check_password():
    """Trả về True nếu người dùng đã đăng nhập, ngược lại hiển thị form đăng nhập."""
    
    # Kiểm tra xem 'password_correct' đã được khởi tạo trong session_state chưa
    # Nếu chưa, mặc định là False
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # Nếu đã xác thực thành công, trả về True
    if st.session_state["password_correct"]:
        return True

    # --- FORM ĐĂNG NHẬP ---
    # Sử dụng st.form để người dùng có thể nhập cả hai trường trước khi gửi
    with st.form("Credentials"):
        st.header("🔐 Vui lòng đăng nhập để tiếp tục")
        username = st.text_input("Tài khoản", key="username")
        password = st.text_input("Mật khẩu", type="password", key="password")
        submitted = st.form_submit_button("Đăng nhập")

        if submitted:
            # --- TÀI KHOẢN VÀ MẬT KHẨU HARD-CODE ---
            # !!! Thay đổi tài khoản và mật khẩu của bạn ở đây
            CORRECT_USERNAME = "taybactv@gmail.com"
            CORRECT_PASSWORD = "taybactv12" # Thay bằng mật khẩu bạn muốn
            
            if username == CORRECT_USERNAME and password == CORRECT_PASSWORD:
                st.session_state["password_correct"] = True
                # Xóa các thông tin nhạy cảm khỏi session_state sau khi dùng
                del st.session_state["username"]
                del st.session_state["password"]
                st.rerun() # Tải lại trang để hiển thị nội dung chính
            else:
                st.error("😕 Tài khoản hoặc mật khẩu không đúng")
    
    # Ngăn không cho phần còn lại của ứng dụng chạy nếu chưa đăng nhập
    st.stop()