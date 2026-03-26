import streamlit as st
import cv2
import easyocr
import pandas as pd
import numpy as np
import io

# Cấu hình trang
st.set_page_config(page_title="Chuyển Ảnh Tuyển Sinh thành Excel", layout="wide")

st.title("Chuyển Đổi Ảnh Phiếu Thông Tin sang Excel")
st.markdown("""
Ứng dụng này giúp trích xuất thông tin cơ bản từ ảnh chụp phiếu đăng ký (chữ in hoặc viết tay rõ ràng).
Bạn nên **chụp ảnh thẳng góc, rõ nét và đủ ánh sáng** để có kết quả tốt nhất.
""")

# Khởi tạo mô hình OCR tiếng Việt (chỉ chạy một lần để tối ưu hiệu suất)
@st.cache_resource
def load_ocr_model():
    # 'vi' là mã cho tiếng Việt, 'en' cho tiếng Anh (để hỗ trợ các ký tự số, v.v.)
    return easyocr.Reader(['vi', 'en']) 

reader = load_ocr_model()

# --- GIAO DIỆN UPLOAD ẢNH ---
uploaded_file = st.file_uploader("Chọn một ảnh chụp phiếu thông tin...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 1. Hiển thị ảnh
    st.image(uploaded_file, caption='Ảnh đã tải lên', use_column_width=True)
    st.write("Đang xử lý ảnh... Vui lòng đợi trong giây giây.")

    # Convert ảnh thành định dạng OpenCV
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)

    # 2. Xử lý ảnh cơ bản (Preprocessing) - Tăng độ tương phản
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Áp dụng Thresholding để làm chữ nổi bật hơn
    _, binary_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY)
    # Bạn có thể dùng `adaptiveThreshold` nếu ảnh có ánh sáng không đều

    # 3. Chạy OCR
    with st.spinner("Đang 'đọc' chữ..."):
        # Lấy văn bản thô
        results = reader.readtext(binary_image, detail=0)
        full_text = " ".join(results) # Gộp lại thành một đoạn văn bản

    st.subheader("Văn bản thô đã đọc được:")
    st.code(full_text)

    # 4. Phân tích văn bản thành các trường dữ liệu (Cực kỳ quan trọng)
    # *Lưu ý: Phần này phụ thuộc rất lớn vào định dạng của phiếu thông tin của bạn.*
    # *Đây là một ví dụ cơ bản.*

    extracted_data = {
        "Họ và Tên": "",
        "Ngày sinh": "",
        "Số điện thoại": "",
        "Địa chỉ": "",
        "Email": ""
    }

    # Giả định dữ liệu theo thứ tự xuất hiện hoặc sử dụng RegEx (Regular Expressions)
    # Ví dụ: SĐT thường có 10 chữ số
    import re
    
    phone_match = re.search(r'(0\d{9})', full_text) # Tìm số 0 đầu và 9 chữ số sau
    if phone_match:
        extracted_data["Số điện thoại"] = phone_match.group(1)

    # Ví dụ: Ngày sinh thường có định dạng DD/MM/YYYY hoặc DD-MM-YYYY
    date_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', full_text)
    if date_match:
        extracted_data["Ngày sinh"] = date_match.group(1)

    # Cần thêm các logic khác dựa trên file thực tế của bạn
    # Ví dụ, tìm từ khóa "Họ và tên" rồi lấy dữ liệu sau nó.

    # 5. Hiển thị dữ liệu trích xuất dạng bảng
    st.subheader("Dữ liệu trích xuất dự kiến:")
    df_data = pd.DataFrame([extracted_data])
    st.dataframe(df_data)

    # 6. Cho phép tải xuống file Excel
    towrite = io.BytesIO()
    df_data.to_excel(towrite, index=False, header=True)
    towrite.seek(0)
    
    st.download_button(
        label="Tải dữ liệu xuống file Excel (.xlsx)",
        data=towrite,
        file_name="tuyen_sinh_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Hãy tải lên một bức ảnh để bắt đầu.")

# Hướng dẫn chi tiết ở sidebar
st.sidebar.title("Hướng dẫn")
st.sidebar.info("""
1.  Đảm bảo ảnh chụp phiếu thông tin phẳng.
2.  Chữ viết tay phải rõ ràng, không bị lem, gạch xóa.
3.  Ánh sáng phải đủ (tránh bị bóng).
4.  Nếu kết quả chưa chính xác, hãy chụp lại ảnh rõ hơn.
""")
