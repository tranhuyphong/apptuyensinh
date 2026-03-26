import streamlit as st
import cv2
import pytesseract
import pandas as pd
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="Quét Phiếu Tuyển Sinh TBD", layout="wide")
st.title("📑 Trích xuất Thông tin Phiếu Đăng ký Tuyển sinh - ĐH Thái Bình Dương")

# Định nghĩa Tọa độ các ô cần trích xuất (ROI - Regions of Interest)
# Tọa độ: (x, y, chiều_rộng, chiều_cao). Đơn vị là % của ảnh gốc để đảm bảo độ chính xác.
# *Lưu ý: Tọa độ này dựa trên ảnh mẫu của bạn, có thể cần tinh chỉnh nếu phiếu thay đổi.*
ROI_LAYOUT = {
    "Họ và Tên":     (0.208, 0.106, 0.281, 0.038),
    "Ngày sinh":     (0.631, 0.106, 0.207, 0.038),
    "Trường THPT":   (0.208, 0.136, 0.281, 0.038),
    "Điện thoại":    (0.631, 0.136, 0.207, 0.038),
    "Email":          (0.208, 0.166, 0.281, 0.038),
    "Số CC/CCCD":    (0.631, 0.166, 0.207, 0.038),
    "Địa chỉ liên hệ": (0.208, 0.196, 0.630, 0.038),
    # "Ngành/Chuyên ngành" và "Học bổng" phức tạp hơn, có thể cần AI chuyên dụng 
    # để nhận diện dấu tick và khoanh tròn, tạm thời chưa bao gồm trong code này.
}

def preprocess_for_ocr(crop_img):
    """Hàm xử lý ảnh nâng cao cho từng ô nhỏ"""
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    # Khử nhiễu mạnh cho ô nhỏ
    denoised = cv2.fastNlMeansDenoising(gray, h=15)
    # Phóng to để nét chữ to hơn (giúp Tesseract đọc tốt hơn)
    resized = cv2.resize(denoised, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    # Chuyển về trắng đen chuẩn (Adaptive Thresholding)
    binary = cv2.adaptiveThreshold(resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
    return binary

uploaded_file = st.file_uploader("Tải lên ảnh chụp phiếu đăng ký (Chụp thẳng, rõ nét)...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Đọc ảnh sang định dạng OpenCV
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    original_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Hiển thị ảnh gốc
    st.image(original_img, caption='Ảnh đã tải lên', use_container_width=True, channels="BGR")
    
    height, width, _ = original_img.shape
    extracted_data = {}
    
    with st.spinner("Đang trích xuất dữ liệu..."):
        st.subheader("Bản xem trước dữ liệu (Bạn có thể sửa lỗi)")
        cols = st.columns(2) # Hiển thị 2 ô trên một dòng cho gọn
        
        for idx, (field_name, roi_pct) in enumerate(ROI_LAYOUT.items()):
            # Chuyển tọa độ % sang pixel
            x, y, w, h = roi_pct
            ix, iy, iw, ih = int(x * width), int(y * height), int(w * width), int(h * height)
            
            # Cắt ảnh
            crop_img = original_img[iy:iy+ih, ix:ix+iw]
            
            # Xử lý ảnh nâng cao (Pre-processing)
            binary_img = preprocess_for_ocr(crop_img)
            
            # Đọc OCR trên ô đã xử lý
            # config='--psm 7' cho Tesseract biết đây là một dòng chữ đơn lẻ
            config = '--psm 7'
            text = pytesseract.image_to_string(binary_img, lang='vie+eng', config=config)
            
            # Hiển thị ô ảnh và nội dung đọc được để người dùng kiểm tra
            with cols[idx % 2]:
                st.image(binary_img, caption=field_name, use_container_width=True, channels="GRAY")
                extracted_data[field_name] = st.text_input(f"Sửa lỗi cho: {field_name}", text.strip())

    # --- TẠO FILE EXCEL CHUẨN ---
    st.markdown("---")
    st.subheader("Dữ liệu cuối cùng (sẵn sàng tải xuống):")
    df = pd.DataFrame([extracted_data])
    st.dataframe(df, use_container_width=True)

    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, header=True, engine='openpyxl')
    towrite.seek(0)
    
    st.download_button(
        label="📥 Tải xuống file Excel (.xlsx)",
        data=towrite,
        file_name="thong_tin_tuyen_sinh_TBD.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
