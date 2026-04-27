import streamlit as st
import pandas as pd
import joblib
import re
import matplotlib.pyplot as plt # Thêm thư viện vẽ biểu đồ
from googleapiclient.discovery import build
from underthesea import word_tokenize

# --- CẤU HÌNH (Giữ nguyên phần load model và API_KEY của bạn) ---
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"
model = joblib.load('mo_hinh_ai.pkl')
vectorizer = joblib.load('bo_tu_dien.pkl')

def lam_sach(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return word_tokenize(text, format="text")

# --- GIAO DIỆN ---
st.set_page_config(page_title="AI YouTube Sentiment", layout="wide")
st.title("🤖 Ứng dụng AI Phân Tích Bình Luận YouTube")

url = st.text_input("Dán link YouTube tại đây:", "https://youtu.be/M8A_rRVp3Oo?si=Z_kfK0wihmB439Mk")

if st.button("Bắt đầu phân tích"):
    try:
        # 1. Logic lấy Video ID chuẩn cho mọi loại link
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = url.split("/")[-1].split("?")[0]

        with st.spinner('Đang lấy dữ liệu...'):
            youtube = build('youtube', 'v3', developerKey=API_KEY)
            request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=50, textFormat="plainText")
            response = request.execute()

            data = []
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                sach = [lam_sach(comment)]
                so = vectorizer.transform(sach)
                
                # ------------------- ĐOẠN CẬP NHẬT -------------------
                # Sử dụng predict_proba để lấy mảng xác suất [Tiêu cực, Tích cực]
                xac_suat = model.predict_proba(so)[0] 
                ti_le_tich_cuc = xac_suat[1] # Lấy xác suất của nhãn 1
                
                # Quy đổi thang 10.0
                diem_so = round(ti_le_tich_cuc * 10, 1)
                
                # Logic Phân loại & Đề xuất
                label = "Tích cực" if diem_so >= 5.0 else "Tiêu cực"
                de_xuat = "Nên đề xuất" if diem_so >= 7.0 else "Không"
                
                # Thêm vào danh sách
                data.append([comment, label, diem_so, de_xuat])
                # -----------------------------------------------------

            # Cập nhật thêm cột cho DataFrame
            df_result = pd.DataFrame(data, columns=["Bình luận", "Kết quả AI", "Điểm (10.0)", "Đề xuất"])
            
            # --- HIỂN THỊ KẾT QUẢ ---
            st.success(f"Đã phân tích xong {len(data)} bình luận!")
            
            
            c1, c2 = st.columns([1, 1]) # Chia làm 2 cột
            
            with c1:
                st.write("### 📊 Thống kê chi tiết")
                st.dataframe(df_result, use_container_width=True)
            
            with c2:
                st.write("### 📈 Biểu đồ cảm xúc")
                # Vẽ biểu đồ tròn bằng Matplotlib
                labels = df_result["Kết quả AI"].value_counts().index
                sizes = df_result["Kết quả AI"].value_counts().values
                colors = ['#66b3ff', '#ff9999'] # Màu xanh cho tích cực, đỏ cho tiêu cực
                
                fig, ax = plt.subplots()
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                ax.axis('equal') 
                st.pyplot(fig) # Hiển thị biểu đồ lên web

    except Exception as e:
        st.error(f"Lỗi: {e}")