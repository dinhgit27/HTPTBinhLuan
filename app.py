import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from transformers import pipeline
import time
import requests

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="YouTube Comment AI Analyzer",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CUSTOM CSS - YOUTUBE DARK THEME
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #0a0a0a 0%, #0f0f0f 50%, #1a0a0a 100%) !important; }
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    .glass-card {
        background: rgba(31, 31, 31, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 24px !important;
        padding: 2rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .hero-section {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, rgba(255,0,0,0.05) 0%, transparent 50%);
        border-radius: 24px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .hero-title { font-size: 3.5rem; font-weight: 900; color: #F1F1F1; line-height: 1.1; }
    .hero-title span {
        background: linear-gradient(135deg, #FF4444, #FF0000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stTextInput > div > div > input {
        background: rgba(40, 40, 40, 0.8) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 16px !important;
        color: #F1F1F1 !important;
        padding: 1rem 1.25rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #FF0000 !important;
        box-shadow: 0 0 0 3px rgba(255,0,0,0.15) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #FF0000, #CC0000) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 0.875rem 2.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(255,0,0,0.3) !important;
        width: 100% !important;
    }
    .star-glow {
        color: #FFD700;
        text-shadow: 0 0 20px #FFD700, 0 0 40px #FFD700;
        font-size: 2.5rem;
        animation: pulse 2s ease-in-out infinite alternate;
    }
    .star-dim { color: #333; font-size: 2.5rem; }
    @keyframes pulse { from { text-shadow: 0 0 20px #FFD700; } to { text-shadow: 0 0 30px #FFD700, 0 0 50px #FFA500; } }
    .stat-box {
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }
    .badge-pos {
        background: linear-gradient(135deg, rgba(76,175,80,0.2), rgba(76,175,80,0.05)) !important;
        border: 1px solid rgba(76,175,80,0.3) !important;
        color: #81C784 !important;
        padding: 0.4rem 1rem !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
    }
    .badge-neg {
        background: linear-gradient(135deg, rgba(244,67,54,0.2), rgba(244,67,54,0.05)) !important;
        border: 1px solid rgba(244,67,54,0.3) !important;
        color: #E57373 !important;
        padding: 0.4rem 1rem !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
    }
    .badge-neu {
        background: linear-gradient(135deg, rgba(158,158,158,0.2), rgba(158,158,158,0.05)) !important;
        border: 1px solid rgba(158,158,158,0.3) !important;
        color: #BDBDBD !important;
        padding: 0.4rem 1rem !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
    }
    .chart-container {
        background: rgba(31,31,31,0.4);
        border-radius: 24px;
        padding: 2rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    hr { border-color: rgba(255,255,255,0.05) !important; margin: 2rem 0 !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0a0a0a; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #FF0000; }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIG
# ============================================
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"
TELEGRAM_BOT_TOKEN = "8606918938:AAFlcQ33rMCw8z-uB6wYm96M8NG3SUfqkvE"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
CHAT_ID = "8585436965"

@st.cache_resource(show_spinner=False)
def load_ai_model(model_name):
    return pipeline("sentiment-analysis", model=model_name)

def escape_telegram_markdown(text):
    """Escape ký tự đặc biệt cho Telegram MarkdownV2 hoặc loại bỏ Markdown lỗi"""
    # Thay ** (markdown của Streamlit) thành * (markdown của Telegram)
    text = text.replace("**", "*")
    return text

def send_telegram_image(chat_id, image, caption=None):
    """Gửi ảnh (biểu đồ) qua Telegram Bot"""
    try:
        url = f"{TELEGRAM_API}/sendPhoto"
        files = {"photo": image}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        response = requests.post(url, data=data, files=files, timeout=20)
        data = response.json()
        if response.status_code == 200 and data.get("ok"):
            return True, None
        else:
            error_msg = data.get("description", "Unknown error")
            return False, error_msg
    except Exception as e:
        return False, str(e)

def send_telegram_message(chat_id, message):
    """Gửi tin nhắn qua Telegram Bot và trả về (success, error_msg)"""
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
            # Không dùng parse_mode để tránh lỗi markdown
        }
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        if response.status_code == 200 and data.get("ok"):
            return True, None
        else:
            error_msg = data.get("description", "Unknown error")
            return False, error_msg
    except Exception as e:
        return False, str(e)

def get_all_comments(youtube, video_id, max_total=1000):
    all_comments = []
    next_page_token = None
    while len(all_comments) < max_total:
        request = youtube.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=100,
            pageToken=next_page_token, textFormat="plainText"
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

def render_stars_html(rating):
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    html = ""
    for i in range(full):
        html += '<span class="star-glow">★</span>'
    if half:
        html += '<span class="star-glow" style="opacity:0.6">★</span>'
    for i in range(empty):
        html += '<span class="star-dim">★</span>'
    return f'<div style="text-align:center;margin:10px 0;">{html}</div>'

# ============================================
# UI - HERO
# ============================================
st.markdown("""
<div class="hero-section">
    <div style="font-size:4rem;margin-bottom:0.5rem;">🔴🤖</div>
    <h1 class="hero-title">YouTube Comment<br><span>AI Analyzer</span></h1>
    <p style="color:#AAAAAA;max-width:600px;margin:0 auto;">
        Phân tích cảm xúc bình luận tiếng Việt bằng PhoBERT.<br>
        Đánh giá chất lượng video qua góc nhìn người xem.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================
# INPUT
# ============================================
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    cols = st.columns([4, 2, 2])
    with cols[0]:
        url = st.text_input("Link YouTube", value="https://www.youtube.com/watch?v=FoymeD0cwuo", 
                           placeholder="Dán link YouTube...", label_visibility="collapsed")
    with cols[1]:
        lang_option = st.selectbox(
            "Ngôn ngữ phân tích",
            options=["Tiếng Việt 🇻🇳", "English / Multi-language 🌐"],
            index=0,
            label_visibility="collapsed"
        )
    with cols[2]:
        analyze_clicked = st.button("🔍 Phân tích", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# ANALYZE
# ============================================
if analyze_clicked:
    try:
        progress_placeholder = st.empty()
        
        # Chọn mô hình AI tương ứng dựa theo ngôn ngữ phân tích
        if lang_option == "Tiếng Việt 🇻🇳":
            model_name = "wonrax/phobert-base-vietnamese-sentiment"
            model_desc = "PhoBERT (~500MB)"
            lang_code = "vi"
        else:
            model_name = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
            model_desc = "DistilBERT Multilingual (~270MB)"
            lang_code = "en"
            
        with progress_placeholder.container():
            st.markdown('<div class="glass-card" style="text-align:center;padding:3rem;">', unsafe_allow_html=True)
            st.markdown(f"""
                <div style="width:80px;height:80px;margin:0 auto 1rem;border:4px solid rgba(255,0,0,0.1);
                     border-top-color:#FF0000;border-radius:50%;animation:spin 1s linear infinite;"></div>
                <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
                <h3 style="color:#F1F1F1;">Đang khởi động AI 🧠</h3>
                <p style="color:#888;">Tải mô hình {model_desc}...</p>
            """, unsafe_allow_html=True)
            bar = st.progress(0)
            st.markdown('</div>', unsafe_allow_html=True)
        
        sentiment_analyzer = load_ai_model(model_name)
        bar.progress(20)
        
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = url.split("/")[-1].split("?")[0]
        
        progress_placeholder.empty()
        
        with st.spinner(''):
            st.markdown('<div class="glass-card" style="text-align:center;padding:2rem;">', unsafe_allow_html=True)
            st.markdown('<p style="color:#F1F1F1;font-size:1.2rem;font-weight:600;">📥 Đang lấy bình luận từ YouTube...</p>', unsafe_allow_html=True)
            progress_bar = st.progress(30)
            st.markdown('</div>', unsafe_allow_html=True)
            
            try:
                youtube = build('youtube', 'v3', developerKey=API_KEY)
                all_comments = get_all_comments(youtube, video_id, max_total=1000)
            except Exception as e:
                # Chế độ dự phòng offline (Offline Backup Mode) phòng trường hợp mất mạng / hết hạn quota API
                import os
                if os.path.exists("binh_luan_youtube.csv"):
                    try:
                        offline_df = pd.read_csv("binh_luan_youtube.csv")
                        col_candidates = ["BinhLuan", "Bình luận", offline_df.columns[0]]
                        comment_col = None
                        for c in col_candidates:
                            if c in offline_df.columns:
                                comment_col = c
                                break
                        if comment_col:
                            all_comments = offline_df[comment_col].dropna().tolist()[:1000]
                            st.warning("⚠️ Không thể kết nối tới API YouTube (Hết quota hoặc mất mạng). Hệ thống đã tự động kích hoạt Chế độ Ngoại tuyến (Offline Backup) và đang phân tích dữ liệu mẫu.")
                        else:
                            st.error("❌ Không thể kết nối API YouTube và không tìm thấy cột dữ liệu hợp lệ trong file offline.")
                            st.stop()
                    except Exception as offline_err:
                        st.error(f"❌ Không thể kết nối API YouTube và gặp lỗi khi đọc dữ liệu dự phòng offline: {offline_err}")
                        st.stop()
                else:
                    st.error("❌ Không thể kết nối API YouTube (Hết quota hoặc mất mạng) và không tìm thấy file dữ liệu offline dự phòng (binh_luan_youtube.csv).")
                    st.stop()
            
            if not all_comments:
                st.error("❌ Video không có bình luận hoặc không tìm thấy video.")
                st.stop()
            
            progress_bar.progress(50)
            
            data = []
            total_score = 0
            sentiment_counts = {"Tích cực": 0, "Tiêu cực": 0, "Trung tính": 0}
            
            for i, comment in enumerate(all_comments):
                try:
                    short = comment[:200]
                    result = sentiment_analyzer(short, truncation=True)[0]
                    label_ai = result['label'].upper()
                    conf = result['score']
                    
                    if label_ai in ['POS', 'POSITIVE']:
                        label = "Tích cực"
                        score = round(conf * 10, 1)
                    elif label_ai in ['NEG', 'NEGATIVE']:
                        label = "Tiêu cực"
                        score = round((1 - conf) * 10, 1)
                    else:
                        label = "Trung tính"
                        score = 5.0
                except Exception:
                    label = "Trung tính"
                    score = 5.0
                
                total_score += score
                sentiment_counts[label] += 1
                data.append([comment, label, score])
                
                if i % 50 == 0:
                    progress_bar.progress(min(50 + int((i / len(all_comments)) * 40), 90))
            
            progress_bar.progress(100)
            time.sleep(0.3)
        
        df = pd.DataFrame(data, columns=["Bình luận", "Cảm xúc", "Điểm"])
        avg_score = round(total_score / len(data), 1) if data else 0
        star_rating = round(avg_score / 2, 1)
        total = len(data)
        progress_placeholder.empty()
        
        # SUCCESS
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;background: linear-gradient(135deg, rgba(76,175,80,0.1), transparent);">
            <div style="font-size:3rem;margin-bottom:0.5rem;">✅</div>
            <h2 style="color:#81C784;">Phân tích hoàn tất!</h2>
            <p style="color:#888;">Đã phân tích <strong style="color:#F1F1F1;">{total}</strong> bình luận bằng PhoBERT</p>
        </div>
        """, unsafe_allow_html=True)
        
        # SCORE CARD
        st.markdown('<div class="glass-card" style="text-align:center;">', unsafe_allow_html=True)
        st.markdown('<p style="color:#888;text-transform:uppercase;letter-spacing:2px;font-size:0.9rem;margin-bottom:1rem;">Điểm đánh giá tổng thể</p>', unsafe_allow_html=True)
        score_cols = st.columns([1, 2, 1])
        with score_cols[1]:
            st.markdown(render_stars_html(star_rating), unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:5rem;font-weight:900;background:linear-gradient(135deg,#FFD700,#FFA500);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{avg_score}</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:#888;font-size:1.1rem;">/ 10 điểm • {star_rating} / 5 sao</p>', unsafe_allow_html=True)
            
            dominant = max(sentiment_counts, key=sentiment_counts.get)
            if dominant == "Tích cực":
                badge = '<span class="badge-pos" style="font-size:1.1rem;padding:0.6rem 2rem;">🟢 Rất tích cực</span>'
            elif dominant == "Tiêu cực":
                badge = '<span class="badge-neg" style="font-size:1.1rem;padding:0.6rem 2rem;">🔴 Tiêu cực</span>'
            else:
                badge = '<span class="badge-neu" style="font-size:1.1rem;padding:0.6rem 2rem;">🟡 Trung tính</span>'
            st.markdown(f'<div style="margin-top:1rem;">{badge}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # STATS ROW
        cols = st.columns(4)
        stats = [
            ("🟢", "Tích cực", sentiment_counts["Tích cực"], "#81C784"),
            ("🔴", "Tiêu cực", sentiment_counts["Tiêu cực"], "#E57373"),
            ("⚪", "Trung tính", sentiment_counts["Trung tính"], "#BDBDBD"),
            ("💬", "Tổng", total, "#F1F1F1"),
        ]
        for col, (icon, label, val, color) in zip(cols, stats):
            with col:
                st.markdown(f"""
                <div class="stat-box">
                    <div style="font-size:2rem;margin-bottom:0.5rem;">{icon}</div>
                    <div style="font-size:2.5rem;font-weight:800;color:{color};">{val}</div>
                    <div style="font-size:0.9rem;color:#888;text-transform:uppercase;letter-spacing:1px;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # CHART + SUMMARY
        st.markdown("<hr>", unsafe_allow_html=True)
        cols = st.columns([1, 1])
        
        with cols[0]:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 style="text-align:center;margin-bottom:1rem;color:#F1F1F1;">📊 Phân bố cảm xúc</h3>', unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(6, 6), facecolor='#121212')
            ax.set_facecolor('#121212')
            labels = list(sentiment_counts.keys())
            sizes = list(sentiment_counts.values())
            colors_pie = ['#10b981', '#ef4444', '#6b7280']
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors_pie, textprops={'color': '#F1F1F1', 'fontsize': 11, 'fontweight': '500'},
                wedgeprops={'width': 0.35, 'edgecolor': '#121212', 'linewidth': 3},
                pctdistance=0.82
            )
            for autotext in autotexts:
                autotext.set_color('#F1F1F1')
                autotext.set_fontweight('bold')
            
            # Thêm tổng số bình luận ở tâm biểu đồ tròn (Donut chart)
            ax.text(
                0, 0, f"{total}\nBình luận", 
                ha='center', va='center', 
                color='#F1F1F1', fontsize=14, fontweight='bold'
            )
            
            ax.axis('equal')
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown('<div class="glass-card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown('<h3 style="margin-bottom:1rem;color:#F1F1F1;">💡 Tóm tắt & Đề xuất</h3>', unsafe_allow_html=True)
            
            pos_pct = round((sentiment_counts["Tích cực"] / total) * 100, 1)
            
            if star_rating >= 4.0:
                summary = f"🟢 Video được đánh giá **RẤT TÍCH CỰC** ({pos_pct}% tích cực). Nội dung chất lượng cao, phù hợp để đề xuất!"
                rec = "✅ **Nên đề xuất** – Phản hồi tốt từ người xem"
                rec_color = "#81C784"
            elif star_rating >= 3.0:
                summary = f"🟡 Video có đánh giá **KHÁ TÍCH CỰC** ({pos_pct}% tích cực). Có thể cân nhắc đề xuất."
                rec = "⚠️ **Cân nhắc** – Có một số ý kiến trái chiều"
                rec_color = "#FFD54F"
            elif star_rating >= 2.0:
                summary = f"🟠 Video có đánh giá **TRUNG BÌNH** ({pos_pct}% tích cực). Cần xem xét kỹ hơn."
                rec = "❓ **Cần xem xét** – Nội dung gây tranh cãi"
                rec_color = "#FF9800"
            else:
                summary = f"🔴 Video có đánh giá **TIÊU CỰC** ({pos_pct}% tích cực). Không nên đề xuất."
                rec = "❌ **Không đề xuất** – Phản hồi xấu từ người xem"
                rec_color = "#E57373"
            
            st.markdown(f'<p style="color:#ccc;line-height:1.6;margin-bottom:1.5rem;">{summary}</p>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border-radius:16px;padding:1.5rem;border-left:4px solid {rec_color};">
                <p style="color:{rec_color};font-weight:700;font-size:1.1rem;margin:0;">{rec}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div style="margin-top:1.5rem;">', unsafe_allow_html=True)
            for label, count in sentiment_counts.items():
                pct = round((count / total) * 100, 1)
                color = "#4CAF50" if label == "Tích cực" else "#f44336" if label == "Tiêu cực" else "#9E9E9E"
                st.markdown(f"""
                <div style="margin-bottom:0.75rem;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem;">
                        <span style="color:#ccc;font-size:0.9rem;">{label}</span>
                        <span style="color:#F1F1F1;font-weight:600;">{pct}%</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.05);border-radius:999px;height:8px;overflow:hidden;">
                        <div style="background:{color};height:100%;border-radius:999px;width:{pct}%;box-shadow:0 0 10px {color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # COMMENTS TABLE
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="margin-bottom:1rem;color:#F1F1F1;">📋 Chi tiết bình luận <span style="color:#888;font-size:0.9rem;">({min(total, 100)} hiển thị)</span></h3>', unsafe_allow_html=True)
        display_df = df.head(100).copy()
        display_df["Điểm"] = display_df["Điểm"].apply(lambda x: f"{x:.1f}")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Bình luận": st.column_config.TextColumn("Bình luận", width="large"),
                "Cảm xúc": st.column_config.TextColumn("Cảm xúc", width="small"),
                "Điểm": st.column_config.TextColumn("Điểm", width="small"),
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)

        from wordcloud_utils import extract_keywords, plot_keyword_bar_chart
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-bottom:1.5rem;color:#F1F1F1;">📊 Thống kê từ khóa nổi bật</h3>', unsafe_allow_html=True)
        lang_code = "vi" if lang_option == "Tiếng Việt 🇻🇳" else "en"
        keywords = extract_keywords(df["Bình luận"].tolist(), top_k=50, language=lang_code)
        
        # Thiết kế dạng 2 cột: Bên trái là Bảng liệt kê chi tiết, Bên phải là Biểu đồ trực quan hóa
        key_cols = st.columns([4, 5])
        
        with key_cols[0]:
            st.markdown('<p style="color:#888;font-size:0.95rem;margin-bottom:0.75rem;">📋 Danh sách từ khóa (Top 50)</p>', unsafe_allow_html=True)
            kw_df = pd.DataFrame(keywords, columns=["Từ khóa", "Số lần xuất hiện"])
            kw_df["Tần suất"] = kw_df["Số lần xuất hiện"].apply(lambda x: f"{x} lần")
            
            st.dataframe(
                kw_df[["Từ khóa", "Tần suất"]],
                use_container_width=True,
                hide_index=True,
                height=380,
                column_config={
                    "Từ khóa": st.column_config.TextColumn("Từ khóa", width="large"),
                    "Tần suất": st.column_config.TextColumn("Tần suất", width="small")
                }
            )
            
        with key_cols[1]:
            st.markdown('<p style="color:#888;font-size:0.95rem;margin-bottom:0.75rem;">📈 Biểu đồ cột ngang (Top 15)</p>', unsafe_allow_html=True)
            bar_plt = plot_keyword_bar_chart(keywords, title=None, top_n=15)
            st.pyplot(bar_plt, use_container_width=True)
            bar_plt.close()
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ============================================
        # BIỂU ĐỒ ĐƯỜNG CẢM XÚC THEO THỜI GIAN
        # ============================================
        from line_chart_utils import plot_sentiment_line_chart
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-bottom:1rem;color:#F1F1F1;">📈 Biểu đồ cảm xúc theo thời gian</h3>', unsafe_allow_html=True)
        line_plt = plot_sentiment_line_chart(df)
        st.pyplot(line_plt, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ============================================
        # TỰ ĐỘNG GỬI TELEGRAM
        # ============================================
        with st.spinner("📨 Đang gửi kết quả về Telegram..."):
            import io
            pos = sentiment_counts["Tích cực"]
            neg = sentiment_counts["Tiêu cực"]
            neu = sentiment_counts["Trung tính"]
            # Escape markdown để tránh lỗi parse Telegram
            safe_summary = escape_telegram_markdown(summary)
            safe_rec = escape_telegram_markdown(rec)
            telegram_msg = f"""🔴 *YouTube Comment AI Analyzer*
\n📺 *Link:* {url}
⭐ *Điểm:* {avg_score}/10 ({star_rating}/5 sao)
\n📊 *Thống kê:*
• 🟢 Tích cực: {pos} ({round(pos/total*100,1)}%)
• 🔴 Tiêu cực: {neg} ({round(neg/total*100,1)}%)
• ⚪ Trung tính: {neu} ({round(neu/total*100,1)}%)
• 💬 Tổng: {total} bình luận
\n💡 *Tóm tắt:*
{safe_summary}
\n📌 *Đề xuất:* {safe_rec}
"""
            # Gửi text
            success, error = send_telegram_message(CHAT_ID, telegram_msg)
            # Gửi ảnh biểu đồ tròn
            pie_buf = io.BytesIO()
            fig, ax = plt.subplots(figsize=(6, 6), facecolor='#121212')
            ax.set_facecolor('#121212')
            labels = list(sentiment_counts.keys())
            sizes = list(sentiment_counts.values())
            colors_pie = ['#10b981', '#ef4444', '#6b7280']
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors_pie, textprops={'color': '#F1F1F1', 'fontsize': 11, 'fontweight': '500'},
                wedgeprops={'width': 0.35, 'edgecolor': '#121212', 'linewidth': 3},
                pctdistance=0.82
            )
            for autotext in autotexts:
                autotext.set_color('#F1F1F1')
                autotext.set_fontweight('bold')
            
            # Thêm tổng số bình luận ở tâm biểu đồ tròn (Donut chart)
            ax.text(
                0, 0, f"{total}\nBình luận", 
                ha='center', va='center', 
                color='#F1F1F1', fontsize=14, fontweight='bold'
            )
            
            ax.axis('equal')
            plt.tight_layout()
            fig.savefig(pie_buf, format='png', bbox_inches='tight', facecolor='#121212', transparent=False)
            pie_buf.seek(0)
            send_telegram_image(CHAT_ID, pie_buf, caption="Biểu đồ tròn cảm xúc")
            plt.close(fig)
            # Gửi Biểu đồ từ khóa nổi bật (Dạng danh sách trực quan)
            wc_buf = io.BytesIO()
            bar_plt = plot_keyword_bar_chart(keywords, title="Biểu đồ từ khóa xuất hiện nhiều nhất", top_n=15)
            bar_plt.savefig(wc_buf, format='png', bbox_inches='tight', facecolor='#121212', transparent=False)
            wc_buf.seek(0)
            send_telegram_image(CHAT_ID, wc_buf, caption="Biểu đồ từ khóa xuất hiện nhiều nhất")
            bar_plt.close()
            # Gửi Line chart
            line_buf = io.BytesIO()
            line_plt = plot_sentiment_line_chart(df)
            line_plt.savefig(line_buf, format='png', bbox_inches='tight')
            line_buf.seek(0)
            send_telegram_image(CHAT_ID, line_buf, caption="Biểu đồ cảm xúc theo thời gian")
            line_plt.close()
            if success:
                st.success("✅ Đã tự động gửi kết quả và biểu đồ về Telegram!")
            else:
                st.error(f"❌ Gửi Telegram thất bại: {error}")
        
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")

