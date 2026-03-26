import streamlit as st
import cv2
import pytesseract
import pandas as pd
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="Máy quét Tuyển sinh", layout="centered")
st.title("📑 Quét Ảnh Phiếu Thông Tin sang Excel")

# Hướng dẫn
with st.expander("Hướng dẫn sử dụng"):
    st.write("1. Chụp ảnh phiếu rõ nét, đủ sáng.")
    st.write("2. Tải ảnh lên và đợi máy 'đọc'.")
    st.write("3. Kiểm tra kết quả và tải file Excel.")

uploaded_file = st.file_uploader("Chọn ảnh chụp phiếu...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Hiển thị ảnh
    image = Image.open(uploaded_file)
    st.image(image, caption='Ảnh đã tải lên', use_container_width=True)
    
    with st.spinner("Đang trích xuất dữ liệu..."):
        # Chuyển sang OpenCV để xử lý
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Đọc chữ bằng Tesseract (ngôn ngữ Tiếng Việt + Tiếng Anh)
        text = pytesseract.image_to_string(gray, lang='vie+eng')
        
    st.subheader("Nội dung máy đọc được:")
    st.text_area("Văn bản thô", text, height=200)

    # Tạo bảng dữ liệu giả định (Bạn có thể sửa lại phần này)
    data = {"Nội dung trích xuất": [line for line in text.split('\n') if line.strip()]}
    df = pd.DataFrame(data)

    # Xuất file Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Tải xuống file Excel",
        data=output.getvalue(),
        file_name="du_lieu_tuyen_sinh.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
