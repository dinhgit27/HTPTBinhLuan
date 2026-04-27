import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from transformers import pipeline

# --- CẤU HÌNH API & AI ---
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"

# Tải mô hình PhoBERT từ Hugging Face và lưu vào bộ nhớ đệm (cache) để không phải tải lại mỗi lần bấm nút
@st.cache_resource
def load_ai_model():
    # Sử dụng pipeline phân tích cảm xúc tiếng Việt chuyên dụng
    return pipeline("sentiment-analysis", model="wonrax/phobert-base-vietnamese-sentiment")

# --- GIAO DIỆN ---
st.set_page_config(page_title="AI YouTube Sentiment (PhoBERT)", layout="wide")
st.title("🤖 Ứng dụng AI Phân Tích Bình Luận (Sử dụng Hugging Face)")

url = st.text_input("Dán link YouTube tại đây:", "https://youtu.be/M8A_rRVp3Oo?si=Z_kfK0wihmB439Mk")

if st.button("Bắt đầu phân tích"):
    try:
        # Tải não bộ AI (Lần đầu chạy sẽ mất khoảng 1-2 phút để tải file ~500MB)
        with st.spinner('Đang khởi động não bộ PhoBERT...'):
            sentiment_analyzer = load_ai_model()

        # Logic lấy Video ID
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = url.split("/")[-1].split("?")[0]

        with st.spinner('Đang thu thập và phân tích ngữ nghĩa bình luận...'):
            youtube = build('youtube', 'v3', developerKey=API_KEY)
            request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=50, textFormat="plainText")
            response = request.execute()

            data = []
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                
                # Cắt bớt bình luận nếu quá dài (Mô hình Transformer giới hạn 256 token)
                short_comment = comment[:500] 
                
                # Gọi AI dự đoán
                ket_qua = sentiment_analyzer(short_comment)[0]
                nhan_ai = ket_qua['label']   # Trả về: POS (Tích cực), NEG (Tiêu cực), NEU (Trung tính)
                do_tu_tin = ket_qua['score'] # Trả về tỉ lệ % từ 0.0 đến 1.0

                # -----------------------------------------
                # LOGIC QUY ĐỔI ĐIỂM SỐ & ĐỀ XUẤT
                # -----------------------------------------
                if nhan_ai == 'POS':
                    label = "Tích cực"
                    diem_so = round(do_tu_tin * 10, 1)
                elif nhan_ai == 'NEG':
                    label = "Tiêu cực"
                    # Nếu chắc chắn là tiêu cực (vd: 0.9) thì điểm sẽ rất thấp: (1 - 0.9)*10 = 1.0 điểm
                    diem_so = round((1 - do_tu_tin) * 10, 1) 
                else:
                    label = "Trung tính"
                    diem_so = 5.0 # Mặc định điểm trung bình

                de_xuat = "Nên đề xuất" if diem_so >= 7.0 else "Không"
                
                data.append([comment, label, diem_so, de_xuat])

            df_result = pd.DataFrame(data, columns=["Bình luận", "Kết quả AI", "Điểm (10.0)", "Đề xuất"])
            
            # --- HIỂN THỊ KẾT QUẢ ---
            st.success(f"Đã phân tích cực sâu {len(data)} bình luận bằng PhoBERT!")
            
            c1, c2 = st.columns([1.5, 1]) 
            
            with c1:
                st.write("### 📊 Thống kê chi tiết")
                st.dataframe(df_result, use_container_width=True)
            
            with c2:
                st.write("### 📈 Biểu đồ cảm xúc")
                labels = df_result["Kết quả AI"].value_counts().index
                sizes = df_result["Kết quả AI"].value_counts().values
                
                # Setup màu sắc tương ứng: Tích cực (Xanh), Tiêu cực (Đỏ), Trung tính (Xám)
                color_map = {"Tích cực": "#66b3ff", "Tiêu cực": "#ff9999", "Trung tính": "#d9d9d9"}
                colors = [color_map[l] for l in labels]
                
                fig, ax = plt.subplots()
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                ax.axis('equal') 
                st.pyplot(fig)

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")