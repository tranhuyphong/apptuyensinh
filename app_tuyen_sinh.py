import streamlit as st
import cv2
import pytesseract
import pandas as pd
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="TBD - Trạm Nhập Liệu Tuyển Sinh", layout="wide")
st.title("📑 Trạm Nhập Liệu Tuyển Sinh - ĐH Thái Bình Dương")

# Định nghĩa Tọa độ vùng cắt (giữ nguyên như bản trước)
ROI_LAYOUT = {
    "Họ và Tên":     (0.208, 0.106, 0.281, 0.038),
    "Ngày sinh":     (0.631, 0.106, 0.207, 0.038),
    "Trường THPT":   (0.208, 0.136, 0.281, 0.038),
    "Điện thoại":    (0.631, 0.136, 0.207, 0.038),
    "Email":          (0.208, 0.166, 0.281, 0.038),
    "Số CC/CCCD":    (0.631, 0.166, 0.207, 0.038),
    "Địa chỉ liên hệ": (0.208, 0.196, 0.630, 0.038),
}

def preprocess_for_viewing(crop_img):
    """Hàm xử lý ảnh để mắt người nhìn rõ nhất (không dùng Threshold)"""
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    # Tăng độ tương phản một chút
    alpha = 1.3 # Contrast control (1.0-3.0)
    beta = 0   # Brightness control (0-100)
    adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    # Phóng to ảnh để nhìn rõ nét chữ
    resized = cv2.resize(adjusted, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    return resized

def preprocess_for_ocr(crop_img):
    """Hàm xử lý ảnh để máy đọc (Thresholding)"""
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    binary = cv2.adaptiveThreshold(resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)
    return binary

uploaded_file = st.file_uploader("Tải lên ảnh chụp phiếu đăng ký (Chụp thẳng, rõ nét)...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Đọc ảnh sang định dạng OpenCV
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    original_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    height, width, _ = original_img.shape
    extracted_data = {}
    
    # Hiển thị ảnh gốc ở sidebar để đối chiếu nếu cần
    st.sidebar.image(original_img, caption='Ảnh gốc', use_container_width=True, channels="BGR")
    st.sidebar.markdown("---")
    st.sidebar.info("Mẹo: Nhấn `Tab` để di chuyển nhanh giữa các ô nhập liệu.")

    with st.spinner("Đang trích xuất dữ liệu..."):
        st.subheader("Nhập liệu và đối chiếu (Sửa lỗi chính tả ngay tại đây)")
        
        # Tạo giao diện lưới để hiển thị ảnh cắt và ô nhập liệu
        cols = st.columns(2) # 2 trường trên một dòng cho gọn
        
        for idx, (field_name, roi_pct) in enumerate(ROI_LAYOUT.items()):
            # Chuyển tọa độ % sang pixel
            x, y, w, h = roi_pct
            ix, iy, iw, ih = int(x * width), int(y * height), int(w * width), int(h * height)
            
            # Cắt ảnh
            crop_img = original_img[iy:iy+ih, ix:ix+iw]
            
            # Xử lý ảnh để mắt nhìn rõ (Không dùng Threshold)
            view_img = preprocess_for_viewing(crop_img)
            
            # Xử lý ảnh để máy đọc (Dùng Threshold)
            ocr_img = preprocess_for_ocr(crop_img)
            
            # Đọc chữ bằng OCR (Mặc định nếu Tesseract không đọc được gì thì để trống)
            config = '--psm 7' # Đọc một dòng chữ
            raw_text = pytesseract.image_to_string(ocr_img, lang='vie+eng', config=config).strip()
            
            # Hiển thị ảnh và ô nhập liệu
            with cols[idx % 2]:
                # Hiển thị ảnh cắt
                st.image(view_img, caption=f"Đối chiếu: {field_name}", use_container_width=True, channels="GRAY")
                # Ô nhập liệu cho phép sửa
                extracted_data[field_name] = st.text_input(f"Nhập/Sửa {field_name}", raw_text, key=field_name)

    # --- TẠO FILE EXCEL CHUẨN ---
    st.markdown("---")
    st.subheader("Bảng dữ liệu cuối cùng (Sẵn sàng tải xuống)")
    df = pd.DataFrame([extracted_data])
    st.dataframe(df, use_container_width=True)

    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, header=True, engine='openpyxl')
    towrite.seek(0)
    
    st.download_button(
        label="📥 Tải xuống File Excel (.xlsx)",
        data=towrite,
        file_name="du_lieu_tuyen_sinh_TBD.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
