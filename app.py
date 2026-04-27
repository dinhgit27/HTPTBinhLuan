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

def get_all_comments(youtube, video_id, max_total=1000):
    """Lấy tất cả bình luận với phân trang"""
    all_comments = []
    next_page_token = None
    
    while len(all_comments) < max_total:
        request = youtube.commentThreads().list(
            part="snippet", 
            videoId=video_id, 
            maxResults=100, 
            pageToken=next_page_token,
            textFormat="plainText"
        )
        response = request.execute()
        
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            all_comments.append(comment)
            if len(all_comments) >= max_total:
                break
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return all_comments

def render_stars(star_rating):
    """Tạo HTML/CSS cho 5 ngôi sao với animation sáng đèn"""
    full_stars = int(star_rating)
    partial = star_rating - full_stars
    
    stars_html = ""
    for i in range(5):
        if i < full_stars:
            # Sao sáng hoàn toàn với animation glow
            stars_html += '<span class="star glowing">★</span>'
        elif i == full_stars and partial >= 0.5:
            # Sao nửa sáng
            stars_html += '<span class="star half-glow">★</span>'
        else:
            # Sao tối
            stars_html += '<span class="star dim">★</span>'
    
    return f"""
    <style>
        .star-container {{
            font-size: 3rem;
            text-align: center;
            margin: 10px 0;
        }}
        .star {{
            display: inline-block;
            margin: 0 5px;
            transition: all 0.3s ease;
        }}
        .glowing {{
            color: #FFD700;
            text-shadow: 0 0 10px #FFD700, 0 0 20px #FFD700, 0 0 30px #FFD700;
            animation: pulse 1.5s ease-in-out infinite alternate;
        }}
        .half-glow {{
            color: #FFD700;
            text-shadow: 0 0 5px #FFD700;
            opacity: 0.7;
        }}
        .dim {{
            color: #555;
            opacity: 0.4;
        }}
        @keyframes pulse {{
            from {{ text-shadow: 0 0 10px #FFD700, 0 0 20px #FFD700; }}
            to {{ text-shadow: 0 0 20px #FFD700, 0 0 30px #FFD700, 0 0 40px #FFA500; }}
        }}
        .score-text {{
            font-size: 1.5rem;
            color: #FFD700;
            text-align: center;
            font-weight: bold;
            margin-top: 10px;
        }}
        .overall-card {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
    </style>
    <div class="overall-card">
        <div class="star-container">
            {stars_html}
        </div>
        <div class="score-text">{star_rating}/5.0 sao</div>
    </div>
    """

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
            
            # Lấy tất cả bình luận (tối đa 1000)
            all_comments = get_all_comments(youtube, video_id, max_total=1000)

            data = []
            total_score = 0
            
            for comment in all_comments:
                try:
                    # Cắt bớt bình luận nếu quá dài (PhoBERT giới hạn ~256 token)
                    # Tiếng Việt ~3-4 byte/token nên cắt 200 ký tự để an toàn
                    short_comment = comment[:200]
                    
                    # Gọi AI dự đoán với truncation để tránh lỗi vượt giới hạn token
                    ket_qua = sentiment_analyzer(short_comment, truncation=True)[0]
                    nhan_ai = ket_qua['label']   # Trả về: POS, NEG, NEU
                    do_tu_tin = ket_qua['score'] # Tỉ lệ % từ 0.0 đến 1.0

                    # -----------------------------------------
                    # LOGIC QUY ĐỔI ĐIỂM SỐ & ĐỀ XUẤT
                    # -----------------------------------------
                    if nhan_ai == 'POS':
                        label = "Tích cực"
                        diem_so = round(do_tu_tin * 10, 1)
                    elif nhan_ai == 'NEG':
                        label = "Tiêu cực"
                        diem_so = round((1 - do_tu_tin) * 10, 1) 
                    else:
                        label = "Trung tính"
                        diem_so = 5.0

                    de_xuat = "Nên đề xuất" if diem_so >= 7.0 else "Không"
                except Exception:
                    # Nếu lỗi token hoặc bất kỳ lỗi nào, gán trung tính để không gián đoạn
                    label = "Trung tính"
                    diem_so = 5.0
                    de_xuat = "Không"
                
                total_score += diem_so
                data.append([comment, label, diem_so, de_xuat])

            df_result = pd.DataFrame(data, columns=["Bình luận", "Kết quả AI", "Điểm (10.0)", "Đề xuất"])
            
            # Tính điểm tổng thể video
            avg_score = round(total_score / len(data), 1) if data else 0
            star_rating = round(avg_score / 2, 1)
            
            # --- HIỂN THỊ KẾT QUẢ ---
            st.success(f"Đã phân tích cực sâu {len(data)} bình luận bằng PhoBERT!")
            
            # Hiển thị điểm tổng thể và ngôi sao
            st.write("### ⭐ Đánh giá tổng thể video")
            st.markdown(render_stars(star_rating), unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Điểm trung bình (thang 10)", f"{avg_score}/10")
            with col2:
                st.metric("Tổng số bình luận phân tích", len(data))
            
            st.divider()
            
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

