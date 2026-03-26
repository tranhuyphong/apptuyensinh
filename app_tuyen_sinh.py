import streamlit as st
import cv2
import pytesseract
import pandas as pd
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="Nhập liệu Tuyển sinh TBD", layout="wide")
st.title("📑 Trạm Hỗ Trợ Nhập Liệu Tuyển Sinh")

# Tọa độ vùng cắt (ROI) chuẩn theo mẫu phiếu của bạn
ROI_LAYOUT = {
    "Họ và Tên":     (0.208, 0.106, 0.281, 0.038),
    "Ngày sinh":     (0.631, 0.106, 0.207, 0.038),
    "Trường THPT":   (0.208, 0.136, 0.281, 0.038),
    "Điện thoại":    (0.631, 0.136, 0.207, 0.038),
    "Email":          (0.208, 0.166, 0.281, 0.038),
    "Số CC/CCCD":    (0.631, 0.166, 0.207, 0.038),
    "Địa chỉ liên hệ": (0.208, 0.196, 0.630, 0.038),
}

def get_clean_image(crop_img):
    """Xử lý ảnh để mắt người dễ đọc nhất"""
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    # Tăng độ tương phản để nét mực rõ hơn trên nền giấy
    alpha = 1.5 
    beta = -20  
    adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    # Phóng to ảnh gấp 3 lần để nhìn cho rõ
    return cv2.resize(adjusted, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

uploaded_files = st.file_uploader("Tải lên các ảnh phiếu (Có thể chọn nhiều file)...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    if 'data_list' not in st.session_state:
        st.session_state.data_list = []
    
    # Duyệt qua từng file đã tải lên
    for file in uploaded_files:
        with st.expander(f"🔍 ĐANG NHẬP PHIẾU: {file.name}", expanded=True):
            file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            h_orig, w_orig, _ = img.shape
            
            row_data = {"Tên File": file.name}
            cols = st.columns(2)
            
            for idx, (field, roi) in enumerate(ROI_LAYOUT.items()):
                x, y, w, h = roi
                ix, iy, iw, ih = int(x * w_orig), int(y * h_orig), int(w * w_orig), int(h * h_orig)
                crop = img[iy:iy+ih, ix:ix+iw]
                
                # Hiển thị ảnh phóng to để người dùng nhìn và gõ
                with cols[idx % 2]:
                    st.image(get_clean_image(crop), caption=f"Nhìn vào đây để gõ: {field}", use_container_width=True)
                    # Chúng ta để trống hoàn toàn để bạn nhập cho chính xác
                    row_data[field] = st.text_input(f"Nhập {field}", key=f"{file.name}_{field}")
            
            if st.button(f"Xác nhận phiếu {file.name}"):
                st.session_state.data_list.append(row_data)
                st.success("Đã lưu tạm dòng này!")

    # Hiển thị bảng kết quả tổng hợp
    if st.session_state.data_list:
        st.markdown("---")
        st.subheader("📊 Bảng dữ liệu tổng hợp")
        final_df = pd.DataFrame(st.session_state.data_list)
        st.dataframe(final_df, use_container_width=True)

        # Xuất file Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 TẢI FILE EXCEL TỔNG HỢP",
            data=buffer.getvalue(),
            file_name="tong_hop_tuyen_sinh.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
