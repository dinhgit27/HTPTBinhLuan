import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from transformers import pipeline
import time
import requests
import platform
import warnings
import io
import importlib
import wordcloud_utils
import line_chart_utils
from platform_scrapers import get_comments, detect_platform
importlib.reload(wordcloud_utils)
importlib.reload(line_chart_utils)

warnings.simplefilter('ignore', UserWarning)

if platform.system() == "Windows":
    plt.rcParams['font.family'] = 'sans-serif'
    font_sans = ['Arial', 'Calibri', 'Segoe UI', 'Tahoma']
    import os
    possible_cjk = [
        ("C:\\Windows\\Fonts\\msyh.ttc", "Microsoft YaHei"),
        ("C:\\Windows\\Fonts\\msyhbd.ttc", "Microsoft YaHei"),
        ("C:\\Windows\\Fonts\\simhei.ttf", "SimHei"),
        ("C:\\Windows\\Fonts\\simsun.ttc", "SimSun")
    ]
    for path, name in possible_cjk:
        if os.path.exists(path):
            if name not in font_sans:
                font_sans.insert(0, name)
                break
    plt.rcParams['font.sans-serif'] = font_sans
else:
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial']

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Comment Analyzer Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# DYNAMIC THEME SYSTEM
# ============================================
def get_platform_theme(p_name):
    themes = {
        "youtube": {
            "name": "YouTube",
            "icon": "🔴",
            "bg_color": "#080101",
            "glow": "rgba(255, 0, 85, 0.25)",
            "primary": "#ff0055",
            "primary_grad": "linear-gradient(135deg, #ff0055 0%, #ff5500 100%)",
            "rec_pos": "Nên xem video",
            "rec_neg": "Bỏ qua video này"
        },
        "tiktok": {
            "name": "TikTok",
            "icon": "🎵",
            "bg_color": "#000508",
            "glow": "rgba(0, 242, 254, 0.25)",
            "primary": "#00f2fe",
            "primary_grad": "linear-gradient(135deg, #00f2fe 0%, #fe0979 100%)",
            "rec_pos": "Rất đáng xem",
            "rec_neg": "Flop chắc rồi"
        },
        "shopee": {
            "name": "Shopee",
            "icon": "🛍️",
            "bg_color": "#0b0400",
            "glow": "rgba(255, 102, 0, 0.25)",
            "primary": "#ff6600",
            "primary_grad": "linear-gradient(135deg, #ff6600 0%, #ffaa00 100%)",
            "rec_pos": "Nên mua ngay",
            "rec_neg": "Không nên mua"
        },
        "facebook": {
            "name": "Facebook",
            "icon": "👥",
            "bg_color": "#00030a",
            "glow": "rgba(0, 153, 255, 0.25)",
            "primary": "#0099ff",
            "primary_grad": "linear-gradient(135deg, #0099ff 0%, #00d4ff 100%)",
            "rec_pos": "Bài viết hay",
            "rec_neg": "Thông tin độc hại"
        },
        "lazada": {
            "name": "Lazada",
            "icon": "💙",
            "bg_color": "#04000b",
            "glow": "rgba(139, 92, 246, 0.25)",
            "primary": "#8b5cf6",
            "primary_grad": "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)",
            "rec_pos": "Nên mua ngay",
            "rec_neg": "Không nên mua"
        },
        "tiki": {
            "name": "Tiki",
            "icon": "📦",
            "bg_color": "#000508",
            "glow": "rgba(0, 229, 255, 0.25)",
            "primary": "#00e5ff",
            "primary_grad": "linear-gradient(135deg, #00e5ff 0%, #0084ff 100%)",
            "rec_pos": "Nên mua ngay",
            "rec_neg": "Không nên mua"
        }
    }
    return themes.get(p_name, themes["youtube"])

# Khởi tạo state
if 'current_url' not in st.session_state:
    st.session_state['current_url'] = "https://www.youtube.com/watch?v=FoymeD0cwuo"
if 'current_platform' not in st.session_state:
    st.session_state['current_platform'] = "youtube"

url_input = st.session_state['current_url']
detected = detect_platform(url_input)
if detected != "unknown" and detected != st.session_state['current_platform']:
    st.session_state['current_platform'] = detected
    
theme = get_platform_theme(st.session_state['current_platform'])

# Inject CSS Theme
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Orbitron:wght@400;700;900&display=swap');
    
    * {{ font-family: 'Inter', sans-serif !important; }}
    
    .stApp {{ 
        background: radial-gradient(circle at 50% 50%, {theme['bg_color']} 0%, #030303 100%) !important; 
    }}
    
    #MainMenu, footer, header, .stDeployButton {{ display: none !important; }}
    
    .glass-card {{
        background: rgba(10, 10, 16, 0.75) !important;
        backdrop-filter: blur(25px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 24px !important;
        padding: 2.2rem !important;
        margin-bottom: 1.8rem !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), 
                    inset 0 0 20px rgba(255, 255, 255, 0.01) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative;
    }}
    
    .glass-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        border-radius: 24px;
        pointer-events: none;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
    }}
    
    .hero-section {{
        text-align: center;
        padding: 4rem 2rem;
        background: radial-gradient(ellipse at center, {theme['glow']} 0%, transparent 75%);
        border-radius: 24px;
        margin-bottom: 2.5rem;
        border: 1px dashed rgba(255, 255, 255, 0.08);
        box-shadow: 0 0 50px rgba(0, 0, 0, 0.5);
    }}
    
    .hero-title {{ 
        font-family: 'Orbitron', sans-serif !important;
        font-size: 3.8rem; 
        font-weight: 900; 
        color: #FFFFFF; 
        line-height: 1.1;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.15);
    }}
    
    .hero-title span {{
        background: {theme['primary_grad']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Orbitron', sans-serif !important;
        text-shadow: 0 0 40px {theme['primary']}55;
    }}
    
    .stTextInput > div > div > input {{
        background: rgba(5, 5, 10, 0.85) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 16px !important;
        color: #FFFFFF !important;
        padding: 1.1rem 1.4rem !important;
        font-size: 1.05rem !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.8) !important;
        transition: all 0.3s ease !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {theme['primary']} !important;
        box-shadow: 0 0 20px {theme['primary']}33, inset 0 2px 4px rgba(0,0,0,0.8) !important;
    }}
    
    .stButton > button {{
        background: {theme['primary_grad']} !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 16px !important;
        padding: 0.95rem 2.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
        box-shadow: 0 0 25px {theme['primary']}44 !important;
        width: 100% !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    
    .stButton > button:hover {{ 
        transform: translateY(-2px) !important;
        box-shadow: 0 0 35px {theme['primary']}aa !important;
        border-color: rgba(255,255,255,0.3) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(1px) !important;
    }}
    
    .star-glow {{ 
        color: #FFD700; 
        text-shadow: 0 0 20px #FFD700, 0 0 40px #FFA500, 0 0 60px #FFD700; 
        font-size: 2.8rem; 
        animation: neonPulse 2s ease-in-out infinite alternate; 
    }}
    
    .star-dim {{ 
        color: rgba(255,255,255,0.05); 
        font-size: 2.8rem; 
        text-shadow: none;
    }}
    
    @keyframes neonPulse {{ 
        from {{ text-shadow: 0 0 15px #FFD700, 0 0 30px #FFA500; }} 
        to {{ text-shadow: 0 0 25px #FFD700, 0 0 50px #FFA500, 0 0 70px #FFD700; }} 
    }}
    
    .stat-box {{
        background: rgba(255, 255, 255, 0.015) !important;
        border-radius: 18px;
        padding: 1.6rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.4s ease;
    }}
    
    .stat-box:hover {{ 
        background: rgba(255, 255, 255, 0.03) !important; 
        transform: translateY(-6px);
        border-color: {theme['primary']}55 !important;
        box-shadow: 0 10px 25px {theme['primary']}15 !important;
    }}
    
    .badge-pos {{ 
        background: rgba(16, 185, 129, 0.08) !important; 
        border: 1.5px solid #10b981 !important; 
        color: #34d399 !important; 
        padding: 0.5rem 1.5rem !important; 
        border-radius: 999px !important; 
        font-weight: 700 !important; 
        letter-spacing: 0.5px;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.25) !important;
        text-shadow: 0 0 5px rgba(16, 185, 129, 0.5);
    }}
    
    .badge-neg {{ 
        background: rgba(239, 68, 68, 0.08) !important; 
        border: 1.5px solid #ef4444 !important; 
        color: #f87171 !important; 
        padding: 0.5rem 1.5rem !important; 
        border-radius: 999px !important; 
        font-weight: 700 !important; 
        letter-spacing: 0.5px;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.25) !important;
        text-shadow: 0 0 5px rgba(239, 68, 68, 0.5);
    }}
    
    .badge-neu {{ 
        background: rgba(107, 114, 128, 0.08) !important; 
        border: 1.5px solid #6b7280 !important; 
        color: #d1d5db !important; 
        padding: 0.5rem 1.5rem !important; 
        border-radius: 999px !important; 
        font-weight: 700 !important; 
        letter-spacing: 0.5px;
        box-shadow: 0 0 15px rgba(107, 114, 128, 0.15) !important;
    }}
    
    .chart-container {{ 
        background: rgba(10, 10, 16, 0.5); 
        border-radius: 24px; 
        padding: 2.2rem; 
        border: 1px solid rgba(255, 255, 255, 0.03); 
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }}
    
    hr {{ 
        border-color: rgba(255, 255, 255, 0.04) !important; 
        margin: 2.5rem 0 !important; 
    }}
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIG
# ============================================
import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env (if present)
load_dotenv()

# Telegram credentials – fallback to hard‑coded values for backward compatibility
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8606918938:AAFlcQ33rMCw8z-uB6wYm96M8NG3SUfqkvE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8585436965")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
API_KEY = os.getenv("API_KEY", "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw")


def send_telegram_message(payload):
    """Send a message via Telegram Bot API. Returns True on success, False otherwise."""
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def send_telegram_photo(buf, caption=""):
    """Send a photo (BytesIO buffer) via Telegram Bot API. Returns True on success."""
    try:
        url = f"{TELEGRAM_API}/sendPhoto"
        buf.seek(0)
        files = {"photo": ("chart.png", buf, "image/png")}
        data = {"chat_id": int(CHAT_ID)}
        if caption:
            data["caption"] = caption[:1024]
        response = requests.post(url, data=data, files=files, timeout=30)
        return response.status_code == 200
    except Exception:
        return False

@st.cache_resource(show_spinner=False)
def load_ai_model(model_name):
    return pipeline("sentiment-analysis", model=model_name)

def render_stars_html(rating):
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    html = ""
    for i in range(full): html += '<span class="star-glow">★</span>'
    if half: html += '<span class="star-glow" style="opacity:0.6">★</span>'
    for i in range(empty): html += '<span class="star-dim">★</span>'
    return f'<div style="text-align:center;margin:10px 0;">{html}</div>'

# ============================================
# UI - HERO
# ============================================
st.markdown(f"""
<div class="hero-section">
    <div style="font-size:4rem;margin-bottom:0.5rem;">{theme['icon']}🤖</div>
    <h1 class="hero-title">{theme['name']} Comment<br><span>AI Analyzer Pro</span></h1>
    <p style="color:#AAAAAA;max-width:600px;margin:0 auto;">
        Tự động nhận diện nền tảng và phân tích cảm xúc bình luận thời gian thực bằng PhoBERT/DistilBERT.<br>
        Đánh giá chất lượng nội dung qua góc nhìn người dùng.
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
        new_url = st.text_input("Link Mạng Xã Hội/E-commerce", value=st.session_state['current_url'], 
                           placeholder="Dán link YouTube, TikTok, Shopee, Facebook, Lazada, Tiki...", label_visibility="collapsed")
        if new_url != st.session_state['current_url']:
            st.session_state['current_url'] = new_url
            st.rerun()
            
    with cols[1]:
        lang_option = st.selectbox(
            "Ngôn ngữ phân tích",
            options=["Tiếng Việt 🇻🇳", "English / Multi-language 🌐"],
            index=0,
            label_visibility="collapsed"
        )
    with cols[2]:
        analyze_clicked = st.button(f"🔍 Phân tích {theme['name']}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# ANALYZE
# ============================================
if analyze_clicked:
    try:
        progress_placeholder = st.empty()
        
        if lang_option == "Tiếng Việt 🇻🇳":
            model_name = "wonrax/phobert-base-vietnamese-sentiment"
            model_desc = "PhoBERT (~500MB)"
        else:
            model_name = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
            model_desc = "DistilBERT Multilingual (~270MB)"
            
        with progress_placeholder.container():
            st.markdown('<div class="glass-card" style="text-align:center;padding:3rem;">', unsafe_allow_html=True)
            st.markdown(f"""
                <div style="width:80px;height:80px;margin:0 auto 1rem;border:4px solid {theme['glow']};
                     border-top-color:{theme['primary']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
                <h3 style="color:#F1F1F1;">Đang khởi động AI 🧠</h3>
                <p style="color:#888;">Tải mô hình {model_desc}...</p>
            """, unsafe_allow_html=True)
            bar = st.progress(0)
            st.markdown('</div>', unsafe_allow_html=True)
        
        sentiment_analyzer = load_ai_model(model_name)
        bar.progress(20)
        progress_placeholder.empty()
        
        with st.spinner(''):
            st.markdown('<div class="glass-card" style="text-align:center;padding:2rem;">', unsafe_allow_html=True)
            st.markdown(f'<p style="color:#F1F1F1;font-size:1.2rem;font-weight:600;">📥 Đang lấy bình luận từ {theme["name"]}...</p>', unsafe_allow_html=True)
            progress_bar = st.progress(30)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Fetch comments via unified scraper
            all_comments, actual_platform, is_offline = get_comments(st.session_state['current_url'], max_total=1000, youtube_api_key=API_KEY)
            
            if is_offline:
                st.warning(f"⚠️ **Offline Mode:** Hệ thống không thể thu thập dữ liệu trực tiếp (do giới hạn API hoặc chống bot của {theme['name']}). Chuyển sang sử dụng tập dữ liệu dự phòng.")
            
            if not all_comments:
                st.error("❌ Không tìm thấy bình luận nào hoặc link không hợp lệ.")
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
        
        # SUCCESS MESSAGE
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;background: linear-gradient(135deg, rgba(76,175,80,0.1), transparent);">
            <div style="font-size:3rem;margin-bottom:0.5rem;">✅</div>
            <h2 style="color:#81C784;">Phân tích hoàn tất!</h2>
            <p style="color:#888;">Đã phân tích <strong style="color:#F1F1F1;">{total}</strong> bình luận trên <b>{theme["name"]}</b> bằng AI.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # SCORE CARD
        st.markdown('<div class="glass-card" style="text-align:center;">', unsafe_allow_html=True)
        st.markdown('<p style="color:#888;text-transform:uppercase;letter-spacing:2px;font-size:0.9rem;margin-bottom:1rem;">Điểm đánh giá tổng thể</p>', unsafe_allow_html=True)
        score_cols = st.columns([1, 2, 1])
        with score_cols[1]:
            st.markdown(render_stars_html(star_rating), unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:5rem;font-weight:900;background:{theme["primary_grad"]};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{avg_score}</div>', unsafe_allow_html=True)
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
            fig, ax = plt.subplots(figsize=(6, 6), facecolor=theme['bg_color'])
            ax.set_facecolor(theme['bg_color'])
            labels = list(sentiment_counts.keys())
            sizes = list(sentiment_counts.values())
            colors_pie = ['#10b981', '#ef4444', '#6b7280']
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors_pie, textprops={'color': '#F1F1F1', 'fontsize': 11, 'fontweight': '500'},
                wedgeprops={'width': 0.35, 'edgecolor': theme['bg_color'], 'linewidth': 3},
                pctdistance=0.82
            )
            
            import matplotlib.font_manager as fm
            font_path = line_chart_utils.get_vietnamese_font_path()
            if font_path:
                font_pie = fm.FontProperties(fname=font_path, size=11)
                font_pie_bold = fm.FontProperties(fname=font_path, size=11, weight='bold')
                font_center = fm.FontProperties(fname=font_path, size=14, weight='bold')
                for t in texts: t.set_fontproperties(font_pie); t.set_color('#F1F1F1')
                for at in autotexts: at.set_fontproperties(font_pie_bold); at.set_color('#F1F1F1')
                ax.text(0, 0, f"{total}\nBình luận", ha='center', va='center', color='#F1F1F1', fontproperties=font_center)
            else:
                for autotext in autotexts: autotext.set_color('#F1F1F1'); autotext.set_fontweight('bold')
                ax.text(0, 0, f"{total}\nBình luận", ha='center', va='center', color='#F1F1F1', fontsize=14, fontweight='bold')
            
            ax.axis('equal')
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown('<div class="glass-card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown('<h3 style="margin-bottom:1rem;color:#F1F1F1;">💡 Tóm tắt & Đề xuất</h3>', unsafe_allow_html=True)
            pos_pct = round((sentiment_counts["Tích cực"] / total) * 100, 1)
            
            if star_rating >= 4.0:
                summary = f"🟢 Nội dung được đánh giá **RẤT TÍCH CỰC** ({pos_pct}% tích cực). Phản hồi cực kỳ tốt!"
                rec = theme["rec_pos"]
                rec_color = "#81C784"
            elif star_rating >= 3.0:
                summary = f"🟡 Nội dung có đánh giá **KHÁ TÍCH CỰC** ({pos_pct}% tích cực). Nhìn chung khá ổn."
                rec = "⚠️ Cân nhắc"
                rec_color = "#FFD54F"
            elif star_rating >= 2.0:
                summary = f"🟠 Nội dung có đánh giá **TRUNG BÌNH** ({pos_pct}% tích cực). Có nhiều ý kiến trái chiều."
                rec = "❓ Cần xem xét kỹ"
                rec_color = "#FF9800"
            else:
                summary = f"🔴 Nội dung bị đánh giá **TIÊU CỰC** ({pos_pct}% tích cực). Phản hồi xấu từ người dùng."
                rec = theme["rec_neg"]
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
        
        # COMMENTS TABLE & FILTER & EXPORT
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.markdown(f'<h3 style="margin-bottom:1rem;color:#F1F1F1;">📋 Chi tiết bình luận</h3>', unsafe_allow_html=True)
        with header_cols[1]:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Tải báo cáo (CSV)",
                data=csv,
                file_name='bao_cao_binh_luan.csv',
                mime='text/csv',
                use_container_width=True
            )
            
        tabs = st.tabs(["Tất cả", "Tích cực 🟢", "Tiêu cực 🔴", "Trung tính ⚪"])
        
        def render_dataframe(filtered_df):
            display_df = filtered_df.head(100).copy()
            display_df["Điểm"] = display_df["Điểm"].apply(lambda x: f"{float(x):.1f}" if pd.notnull(x) else "")
            st.markdown(f'<span style="color:#888;font-size:0.9rem;margin-bottom:10px;display:block;">Hiển thị {len(display_df)} / {len(filtered_df)} bình luận</span>', unsafe_allow_html=True)
            st.dataframe(
                display_df, use_container_width=True, hide_index=True,
                column_config={
                    "Bình luận": st.column_config.TextColumn("Bình luận", width="large"),
                    "Cảm xúc": st.column_config.TextColumn("Cảm xúc", width="small"),
                    "Điểm": st.column_config.TextColumn("Điểm", width="small"),
                }
            )

        with tabs[0]: render_dataframe(df)
        with tabs[1]: render_dataframe(df[df["Cảm xúc"] == "Tích cực"])
        with tabs[2]: render_dataframe(df[df["Cảm xúc"] == "Tiêu cực"])
        with tabs[3]: render_dataframe(df[df["Cảm xúc"] == "Trung tính"])
        
        st.markdown('</div>', unsafe_allow_html=True)

        # KEYWORDS
        lang_code = "vi" if lang_option == "Tiếng Việt 🇻🇳" else "en"
        keywords = wordcloud_utils.extract_keywords(df["Bình luận"].tolist(), top_k=50, language=lang_code)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-bottom:1.5rem;color:#F1F1F1;">📊 Thống kê từ khóa nổi bật</h3>', unsafe_allow_html=True)
        key_cols = st.columns([4, 5])
        with key_cols[0]:
            kw_df = pd.DataFrame(keywords, columns=["Từ khóa", "Số lần xuất hiện"])
            kw_df["Tần suất"] = kw_df["Số lần xuất hiện"].apply(lambda x: f"{x} lần")
            st.dataframe(kw_df[["Từ khóa", "Tần suất"]], use_container_width=True, hide_index=True, height=380)
        with key_cols[1]:
            bar_plt = wordcloud_utils.plot_keyword_bar_chart(keywords, title=None, top_n=15)
            # Update bar colors dynamically to match theme
            for patch in bar_plt.gca().patches:
                patch.set_facecolor(theme['primary'])
            st.pyplot(bar_plt, use_container_width=True)
            bar_plt.close()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # PAIN POINTS
        neg_df = df[df["Cảm xúc"] == "Tiêu cực"]
        if not neg_df.empty:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card" style="border-left: 4px solid #E57373;">', unsafe_allow_html=True)
            st.markdown('<h3 style="margin-bottom:1.5rem;color:#F1F1F1;">⚠️ Phân tích Điểm yếu (Pain-points)</h3>', unsafe_allow_html=True)
            st.markdown('<p style="color:#ccc;">Những vấn đề được nhắc đến nhiều nhất trong các bình luận tiêu cực, giúp bạn xác định được khu vực cần ưu tiên cải thiện.</p>', unsafe_allow_html=True)
            
            neg_keywords = wordcloud_utils.extract_keywords(neg_df["Bình luận"].tolist(), top_k=10, language=lang_code)
            
            if neg_keywords:
                top_k = min(5, len(neg_keywords))
                pain_cols = st.columns(top_k)
                for idx, (kw, count) in enumerate(neg_keywords[:top_k]):
                    with pain_cols[idx]:
                        st.markdown(f"""
                        <div style="background:rgba(229, 115, 115, 0.1); border: 1px solid rgba(229, 115, 115, 0.3); border-radius: 12px; padding: 1rem; text-align: center;">
                            <div style="font-size: 1.2rem; font-weight: bold; color: #E57373; margin-bottom: 0.5rem;">{kw}</div>
                            <div style="color: #F1F1F1; font-size: 1.5rem; font-weight: 900;">{count}</div>
                            <div style="color: #888; font-size: 0.8rem; text-transform: uppercase;">lần phàn nàn</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Chưa có đủ dữ liệu để trích xuất điểm yếu.")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TIME CHART
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-bottom:1rem;color:#F1F1F1;">📈 Xu hướng cảm xúc</h3>', unsafe_allow_html=True)
        line_plt = line_chart_utils.plot_sentiment_line_chart(df)
        st.pyplot(line_plt, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # GỬI BÁO CÁO QUA TELEGRAM
        try:
            import io as _io
            tele_summary = summary.replace("**", "")

            # ── 1. Tin nhắn text đầy đủ ──────────────────────────────────────
            msg  = f"📊 BÁO CÁO PHÂN TÍCH {theme['name'].upper()}\n"
            msg += f"{'='*40}\n"
            msg += f"🔗 Link: {st.session_state['current_url']}\n"
            msg += f"🤖 Mô hình AI: {model_name}\n"
            msg += f"📋 Ngôn ngữ phân tích: {lang_option}\n"
            msg += f"⭐ Điểm tổng thể: {avg_score}/10 ({star_rating}/5 sao)\n"
            msg += f"{'─'*40}\n"
            msg += f"📈 THỐNG KÊ ({total} bình luận):\n"
            msg += f"  🟢 Tích cực : {sentiment_counts['Tích cực']:>4}  ({round(sentiment_counts['Tích cực']/total*100, 1)}%)\n"
            msg += f"  🔴 Tiêu cực : {sentiment_counts['Tiêu cực']:>4}  ({round(sentiment_counts['Tiêu cực']/total*100, 1)}%)\n"
            msg += f"  ⚪ Trung tính: {sentiment_counts['Trung tính']:>4}  ({round(sentiment_counts['Trung tính']/total*100, 1)}%)\n"
            msg += f"{'─'*40}\n"
            msg += f"💡 Đánh giá: {tele_summary}\n"
            msg += f"📌 Đề xuất: {rec}\n"

            # Top từ khóa
            if 'keywords' in locals() and keywords:
                msg += f"{'─'*40}\n"
                msg += f"🔑 TOP TỪ KHÓA NỔI BẬT:\n"
                for i, (kw, cnt) in enumerate(keywords[:15], 1):
                    msg += f"  {i:>2}. {kw} ({cnt} lần)\n"

            # Pain-points
            if not neg_df.empty and 'neg_keywords' in locals() and neg_keywords:
                msg += f"{'─'*40}\n"
                msg += f"⚠️ PAIN-POINTS (Điểm yếu thường gặp):\n"
                for kw, count in neg_keywords[:10]:
                    msg += f"  - {kw} ({count} lần)\n"

            msg += f"{'='*40}\n"
            msg += f"🕐 Thời gian phân tích: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}"

            payload_text = {
                "chat_id": int(CHAT_ID),
                "text": msg,
                "disable_web_page_preview": True
            }
            res_text = send_telegram_message(payload_text)

            # ── 2. Ảnh biểu đồ phân bố cảm xúc (Pie) ───────────────────────
            try:
                fig_pie, ax_pie = plt.subplots(figsize=(6, 6), facecolor='#121212')
                ax_pie.set_facecolor('#121212')
                sizes_t = list(sentiment_counts.values())
                labels_t = list(sentiment_counts.keys())
                colors_t = ['#10b981', '#ef4444', '#6b7280']
                wedges_t, texts_t, autotexts_t = ax_pie.pie(
                    sizes_t, labels=labels_t, autopct='%1.1f%%', startangle=90,
                    colors=colors_t, textprops={'color': '#F1F1F1', 'fontsize': 12},
                    wedgeprops={'width': 0.4, 'edgecolor': '#121212', 'linewidth': 3},
                    pctdistance=0.82
                )
                import matplotlib.font_manager as _fm
                _fp = line_chart_utils.get_vietnamese_font_path()
                if _fp:
                    _fprop = _fm.FontProperties(fname=_fp, size=12)
                    _fpropc = _fm.FontProperties(fname=_fp, size=14, weight='bold')
                    for t in texts_t: t.set_fontproperties(_fprop)
                    for at in autotexts_t: at.set_fontproperties(_fprop); at.set_color('#F1F1F1')
                    ax_pie.text(0, 0, f"{total}\nBình luận", ha='center', va='center',
                                color='#F1F1F1', fontproperties=_fpropc)
                else:
                    ax_pie.text(0, 0, f"{total}\nBình luận", ha='center', va='center',
                                color='#F1F1F1', fontsize=14, fontweight='bold')
                ax_pie.set_title(f"Phân bố cảm xúc - {theme['name']}", color='#F1F1F1',
                                 fontsize=14, fontweight='bold', pad=20)
                ax_pie.axis('equal')
                plt.tight_layout()
                buf_pie = _io.BytesIO()
                fig_pie.savefig(buf_pie, format='png', dpi=150, bbox_inches='tight',
                                facecolor='#121212')
                plt.close(fig_pie)
                send_telegram_photo(buf_pie, caption=f"📊 Phân bố cảm xúc | {theme['name']} | {total} bình luận")
            except Exception:
                pass

            # ── 3. Ảnh biểu đồ top từ khóa (Bar) ───────────────────────────
            try:
                if 'keywords' in locals() and keywords:
                    _bar_fig = wordcloud_utils.plot_keyword_bar_chart(keywords, top_n=15)
                    buf_bar = _io.BytesIO()
                    _bar_fig.savefig(buf_bar, format='png', dpi=150, bbox_inches='tight',
                                     facecolor='#121212')
                    _bar_fig.close()
                    send_telegram_photo(buf_bar, caption="🔑 Top từ khóa nổi bật")
            except Exception:
                pass

            # ── 4. Ảnh biểu đồ xu hướng cảm xúc (Line) ─────────────────────
            try:
                _line_fig = line_chart_utils.plot_sentiment_line_chart(df.copy())
                buf_line = _io.BytesIO()
                _line_fig.savefig(buf_line, format='png', dpi=150, bbox_inches='tight',
                                  facecolor='#121212')
                _line_fig.close()
                send_telegram_photo(buf_line, caption="📈 Xu hướng cảm xúc theo thời gian")
            except Exception:
                pass

            if res_text:
                st.toast("Đã gửi báo cáo đầy đủ + biểu đồ về Telegram! 🚀", icon="✅")
            else:
                st.toast("Không thể gửi báo cáo Telegram. Vui lòng kiểm tra lại Token/Chat ID.", icon="⚠️")
        except Exception as e:
            st.toast(f"Lỗi gửi Telegram: {e}", icon="⚠️")
            
    except Exception as e:
        st.error(f"❌ Lỗi xử lý: {e}")
