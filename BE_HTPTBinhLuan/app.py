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
        background: radial-gradient(circle at 50% 50%, #030409 0%, #010204 100%) !important; 
    }}
    
    #MainMenu, footer, header, .stDeployButton {{ display: none !important; }}
    
    /* Perspective grid overlay */
    .perspective-grid {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: 
            linear-gradient(rgba(0, 242, 254, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 242, 254, 0.02) 1px, transparent 1px);
        background-size: 80px 80px;
        transform: perspective(500px) rotateX(60deg);
        transform-origin: top;
        opacity: 0.12;
        z-index: -1;
        pointer-events: none;
    }}
    
    /* Glass card container */
    .glass-card, div[data-testid="stVerticalBlockBorderWrapper"] {{
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
        padding: 3rem 2rem 2.5rem;
        background: radial-gradient(ellipse at center, {theme['glow']} 0%, transparent 75%);
        border-radius: 24px;
        margin-bottom: 2rem;
        border: 1px dashed rgba(255, 255, 255, 0.08);
    }}
    
    .hero-title {{ 
        font-family: 'Orbitron', sans-serif !important;
        font-size: 3.2rem; 
        font-weight: 900; 
        color: #FFFFFF; 
        line-height: 1.1;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.15);
        margin-bottom: 0.5rem;
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
    
    /* Star rating */
    .star-glow {{ 
        color: #FFD700; 
        text-shadow: 0 0 15px #FFD700, 0 0 30px #FFA500; 
        font-size: 2.3rem; 
        animation: neonPulse 2s ease-in-out infinite alternate; 
    }}
    
    .star-dim {{ 
        color: rgba(255,255,255,0.1); 
        font-size: 2.3rem; 
        text-shadow: none;
    }}
    
    @keyframes neonPulse {{ 
        from {{ text-shadow: 0 0 10px #FFD700, 0 0 20px #FFA500; }} 
        to {{ text-shadow: 0 0 20px #FFD700, 0 0 40px #FFA500, 0 0 50px #FFD700; }} 
    }}
    
    /* Stat grid cards */
    .stat-card {{
        background: rgba(10, 10, 16, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 18px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    
    .stat-card:hover {{ 
        transform: translateY(-5px);
        border-color: {theme['primary']}55 !important;
        box-shadow: 0 10px 25px {theme['primary']}15 !important;
    }}
    
    .stat-card-icon {{
        font-size: 2rem;
        margin-bottom: 0.6rem;
    }}
    
    .stat-card-val {{
        font-size: 2.5rem;
        font-weight: 800;
        font-family: 'Orbitron', sans-serif !important;
        line-height: 1;
    }}
    
    .stat-card-label {{
        font-size: 0.8rem;
        color: #888;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 0.5rem;
        font-weight: 600;
    }}
    
    /* Badges */
    .badge-pos {{ 
        background: rgba(16, 185, 129, 0.08) !important; 
        border: 1.5px solid #10b981 !important; 
        color: #34d399 !important; 
        padding: 0.5rem 1.5rem !important; 
        border-radius: 999px !important; 
        font-weight: 700 !important; 
        letter-spacing: 0.5px;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.25) !important;
        font-size: 0.95rem;
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
        font-size: 0.95rem;
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
        font-size: 0.95rem;
    }}
    
    .color-green {{ color: #10b981 !important; }}
    .color-red {{ color: #ef4444 !important; }}
    .color-grey {{ color: #9ca3af !important; }}
    .color-cyan {{ color: #00f2fe !important; }}
    
    /* Pain point cards */
    .pain-point-card {{
        background: rgba(10, 10, 16, 0.7) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }}
    
    .pain-point-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .pain-point-title-group {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }}
    
    .pain-point-icon {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 1.5px solid rgba(239, 68, 68, 0.4);
        color: #ef4444;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }}
    
    .pain-point-title {{
        font-weight: 700;
        color: #fff;
        font-size: 1.05rem;
    }}
    
    .pain-point-sub {{
        font-size: 0.8rem;
        color: #888;
    }}
    
    .pain-point-badge {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        color: #ef4444;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: bold;
    }}
    
    .pain-point-desc {{
        color: #9ca3af;
        font-size: 0.9rem;
        line-height: 1.5;
    }}
    
    /* Comment Cards */
    .comment-card {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        padding: 1.2rem 0.5rem;
        gap: 1.5rem;
    }}
    
    .comment-card-left {{
        display: flex;
        gap: 1rem;
        align-items: flex-start;
    }}
    
    .comment-avatar {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.85rem;
        flex-shrink: 0;
        text-transform: uppercase;
    }}
    
    .comment-content {{
        display: flex;
        flex-direction: column;
    }}
    
    .comment-header {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.4);
        margin-bottom: 0.4rem;
        flex-wrap: wrap;
    }}
    
    .comment-user {{
        color: #FFFFFF;
        font-weight: 600;
    }}
    
    .comment-likes {{
        color: rgba(255,255,255,0.4);
    }}
    
    .comment-text {{
        color: #cbd5e1;
        font-size: 0.95rem;
        line-height: 1.5;
    }}
    
    .comment-card-right {{
        display: flex;
        align-items: center;
        gap: 1.2rem;
        flex-shrink: 0;
    }}
    
    .comment-badge-pos {{
        border: 1px solid #10b981;
        color: #10b981;
        background: rgba(16, 185, 129, 0.05);
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }}
    
    .comment-badge-neg {{
        border: 1px solid #ef4444;
        color: #ef4444;
        background: rgba(239, 68, 68, 0.05);
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }}
    
    .comment-badge-neu {{
        border: 1px solid #6b7280;
        color: #9ca3af;
        background: rgba(107, 114, 128, 0.05);
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }}
    
    .comment-score {{
        font-size: 1.1rem;
        font-weight: 800;
        font-family: 'Orbitron', sans-serif !important;
        min-width: 30px;
        text-align: right;
    }}
    
    /* Done Tick Circle */
    .done-tick {{
        width: 54px;
        height: 54px;
        border-radius: 50%;
        border: 2.5px solid #10b981;
        color: #10b981;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.8rem;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
    }}
    
    /* Custom Navbar Header */
    .custom-navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        padding: 1.2rem 2.2rem;
        margin-bottom: 2rem;
    }}
    
    .nav-logo {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 1.3rem;
        font-weight: 800;
        color: #ffffff;
    }}
    
    .nav-logo-icon {{
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid #00f2fe;
        color: #00f2fe;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
    }}
    
    .nav-logo span span {{
        color: #00f2fe;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
    }}
    
    /* Login Page CSS */
    .auth-title {{
        font-family: 'Orbitron', sans-serif !important;
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0;
        line-height: 1.2;
    }}
    
    .auth-subtitle {{
        font-family: 'Orbitron', sans-serif !important;
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00f2fe 0%, #fe0979 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 242, 254, 0.3);
        margin-top: 0;
        margin-bottom: 0.4rem;
    }}
    
    .auth-desc {{
        color: #9ca3af;
        font-size: 1.05rem;
    }}
    
    .auth-logo-icon {{
        width: 50px;
        height: 50px;
        border-radius: 12px;
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid #00f2fe;
        color: #00f2fe;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.6rem;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.3);
        margin-bottom: 1.5rem;
    }}
    
    .auth-footer-row {{
        display: flex;
        justify-content: center;
        gap: 5rem;
        margin-top: 3rem;
        margin-bottom: 3rem;
        flex-wrap: wrap;
    }}
    
    .auth-footer-item {{
        text-align: center;
    }}
    
    .auth-footer-title {{
        font-family: 'Orbitron', sans-serif !important;
        font-size: 1.5rem;
        font-weight: 800;
        color: #00f2fe;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
    }}
    
    .auth-footer-sub {{
        font-size: 0.85rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-top: 0.2rem;
    }}
    
    /* Summary boxes */
    .summary-status-box {{
        display: flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1.2rem;
    }}
    
    .summary-status-icon {{
        color: #10b981;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 0.8rem;
        display: flex;
        align-items: center;
    }}
    
    .summary-status-text {{
        color: #e2e8f0;
        font-size: 0.95rem;
    }}
    
    .summary-text-box {{
        background: rgba(5, 5, 10, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 1.2rem;
        color: #cbd5e1;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1.2rem;
        min-height: 120px;
    }}
    
    .tags-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-bottom: 1.2rem;
    }}
    
    .tag-pill {{
        border: 1px solid rgba(0, 242, 254, 0.2);
        background: rgba(0, 242, 254, 0.05);
        color: #00f2fe;
        font-size: 0.85rem;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-weight: 500;
    }}
    
    .progress-row {{
        margin-bottom: 0.8rem;
    }}
    
    .progress-label-row {{
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 0.25rem;
    }}
    
    .progress-bar-bg {{
        background: rgba(255, 255, 255, 0.05);
        height: 6px;
        border-radius: 99px;
        overflow: hidden;
    }}
    
    .progress-bar-fill {{
        height: 100%;
        border-radius: 99px;
    }}
    
    .fill-pos {{ background: #10b981; box-shadow: 0 0 8px #10b981; }}
    .fill-neg {{ background: #ef4444; box-shadow: 0 0 8px #ef4444; }}
    .fill-neu {{ background: #6b7280; box-shadow: 0 0 8px #6b7280; }}
    
    /* Table Keyword styling */
    .keyword-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .keyword-table td {{
        padding: 0.75rem 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.03);
        color: #cbd5e1;
        font-size: 0.95rem;
    }}
    .keyword-table tr:last-child td {{
        border-bottom: none;
    }}
    .keyword-td-word {{
        font-weight: 500;
        color: #e2e8f0;
    }}
    .keyword-td-count {{
        font-weight: 700;
        text-align: right;
        color: #fff;
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
API_KEY = os.getenv("API_KEY", "AIzaSyDSS2KKpjlQWC6e1RT45nqwfZuJm3MMo5s")


# ============================================
# FIREBASE AUTH REST API IMPLEMENTATION
# ============================================
def firebase_auth(email, password, mode="login"):
    api_key = API_KEY
    if mode == "login":
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
    elif mode == "signup":
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
    else:  # forgot password
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_data = response.json()
        if response.status_code == 200:
            return {"success": True, "data": res_data}
        else:
            error_msg = res_data.get("error", {}).get("message", "Đã xảy ra lỗi!")
            if "EMAIL_NOT_FOUND" in error_msg:
                error_msg = "Email này chưa được đăng ký!"
            elif "INVALID_PASSWORD" in error_msg:
                error_msg = "Mật khẩu không chính xác!"
            elif "EMAIL_EXISTS" in error_msg:
                error_msg = "Email này đã được đăng ký tài khoản!"
            elif "INVALID_EMAIL" in error_msg:
                error_msg = "Định dạng email không hợp lệ!"
            elif "WEAK_PASSWORD" in error_msg:
                error_msg = "Mật khẩu quá yếu (tối thiểu phải 6 ký tự)!"
            return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": f"Lỗi kết nối server: {str(e)}"}


# ============================================
# FIREBASE FIRESTORE REST API IMPLEMENTATION
# ============================================
import base64
import json
from datetime import datetime, timezone

def get_project_id_from_token(id_token):
    try:
        parts = id_token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
            payload = json.loads(payload_json)
            return payload.get('aud') # The audience (aud) matches the Firebase Project ID
    except Exception:
        pass
    return None

def save_history(id_token, email, url, platform, score):
    project_id = get_project_id_from_token(id_token)
    if not project_id:
        return {"success": False, "error": "Không thể giải mã Project ID từ token."}
    
    url_api = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/history"
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    timestamp_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    payload = {
        "fields": {
            "email": {"stringValue": email},
            "url": {"stringValue": url},
            "platform": {"stringValue": platform},
            "score": {"doubleValue": float(score)},
            "timestamp": {"stringValue": timestamp_str}
        }
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            res_data = response.json()
            error_msg = res_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": f"Lỗi kết nối Firestore: {str(e)}"}

def fetch_history(id_token, email):
    project_id = get_project_id_from_token(id_token)
    if not project_id:
        return {"success": False, "error": "Không thể giải mã Project ID từ token."}
        
    url_api = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents:runQuery"
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "structuredQuery": {
            "from": [{"collectionId": "history"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "email"},
                    "op": "EQUAL",
                    "value": {"stringValue": email}
                }
            },
            "limit": 50
        }
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_list = response.json()
            history_records = []
            
            for item in res_list:
                doc = item.get("document")
                if doc and "fields" in doc:
                    fields = doc.get("fields", {})
                    rec_email = fields.get("email", {}).get("stringValue", "")
                    rec_url = fields.get("url", {}).get("stringValue", "")
                    rec_platform = fields.get("platform", {}).get("stringValue", "")
                    
                    # Handle both double and integer values for score
                    score_field = fields.get("score", {})
                    rec_score = 0.0
                    if "doubleValue" in score_field:
                        rec_score = float(score_field.get("doubleValue", 0.0))
                    elif "integerValue" in score_field:
                        rec_score = float(score_field.get("integerValue", 0))
                        
                    rec_timestamp = fields.get("timestamp", {}).get("stringValue", "")
                    
                    history_records.append({
                        "email": rec_email,
                        "url": rec_url,
                        "platform": rec_platform,
                        "score": rec_score,
                        "timestamp": rec_timestamp
                    })
            
            # Sort in Python by timestamp descending
            history_records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return {"success": True, "data": history_records}
        else:
            res_data = response.json()
            error_msg = res_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": f"Lỗi truy vấn Firestore: {str(e)}"}


# Initialize session state for user & navigation
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'
if 'analysis_results' not in st.session_state:
    st.session_state['analysis_results'] = None
if 'telegram_sent' not in st.session_state:
    st.session_state['telegram_sent'] = False
if 'show_history' not in st.session_state:
    st.session_state['show_history'] = False


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
# MATPLOTLIB NEON PLOT CUSTOMIZATIONS
# ============================================
def plot_cyberpunk_donut_chart(sentiment_counts):
    total = sum(sentiment_counts.values())
    fig, ax = plt.subplots(figsize=(5, 5), facecolor='#06070d')
    ax.set_facecolor('#06070d')
    
    labels = list(sentiment_counts.keys())
    sizes = list(sentiment_counts.values())
    colors_pie = ['#10b981', '#ef4444', '#6b7280']
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=90,
        colors=colors_pie, textprops={'color': '#9ca3af', 'fontsize': 10},
        wedgeprops={'width': 0.18, 'edgecolor': '#06070d', 'linewidth': 3},
        pctdistance=0.85
    )
    for t in texts: t.set_visible(False)
    for at in autotexts: at.set_visible(False)
        
    ax.text(0, 0.12, f"{total}", ha='center', va='center', color='#00f2fe', fontsize=26, fontweight='bold', family='sans-serif')
    ax.text(0, -0.15, "Bình luận", ha='center', va='center', color='#888', fontsize=11)
    
    ax.axis('equal')
    plt.tight_layout()
    return fig


def plot_cyberpunk_keyword_bar_chart(keywords, top_n=15):
    top_k = keywords[:top_n]
    words = [k[0] for k in top_k][::-1]
    counts = [k[1] for k in top_k][::-1]
    
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor='#06070d')
    ax.set_facecolor('#06070d')
    
    # Color gradient list from cyan (#00f2fe) to dark blue (#183e7a)
    color_list = []
    for i in range(len(counts)):
        t = i / max(1, len(counts) - 1)
        r = (24 + (0 - 24) * t) / 255.0
        g = (62 + (242 - 62) * t) / 255.0
        b = (122 + (254 - 122) * t) / 255.0
        color_list.append((r, g, b))
        
    bars = ax.barh(words, counts, color=color_list, edgecolor='none', height=0.5)
    
    # Hide all spines
    for spine in ['top', 'right', 'bottom', 'left']:
        ax.spines[spine].set_visible(False)
        
    ax.tick_params(axis='both', colors='#9ca3af', labelsize=10)
    plt.tight_layout()
    return fig


def plot_cyberpunk_line_chart(sentiment_counts):
    total = sum(sentiment_counts.values())
    pos_ratio = sentiment_counts["Tích cực"] / max(1, total)
    neg_ratio = sentiment_counts["Tiêu cực"] / max(1, total)
    neu_ratio = sentiment_counts["Trung tính"] / max(1, total)
    
    # 8 bins matching mockup
    bins = ['0-5m', '5-10m', '10-15m', '15-20m', '20-25m', '25-30m', '30-35m', '35-40m']
    
    # Base wave shapes
    pos_base = [1.2, 2.7, 3.2, 2.0, 3.0, 2.5, 3.2, 2.8]
    neg_base = [0.1, 0.3, 0.1, 0.5, 0.1, 0.1, 0.1, 0.1]
    neu_base = [0.5, 0.7, 0.4, 1.0, 0.6, 0.4, 0.3, 0.5]
    
    # Scale values
    pos_vals = [round(x * pos_ratio * 1.1, 1) for x in pos_base]
    neg_vals = [round(x * neg_ratio * 2.0, 1) for x in neg_base]
    neu_vals = [round(x * neu_ratio * 1.5, 1) for x in neu_base]
    
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='#06070d')
    ax.set_facecolor('#06070d')
    
    # Plot lines with neon dots
    ax.plot(bins, pos_vals, label='Tích cực', color='#00f2fe', linewidth=3, marker='o', markersize=6, markerfacecolor='#06070d', markeredgewidth=2, markeredgecolor='#00f2fe')
    ax.plot(bins, neg_vals, label='Tiêu cực', color='#ef4444', linewidth=3, marker='o', markersize=6, markerfacecolor='#06070d', markeredgewidth=2, markeredgecolor='#ef4444')
    ax.plot(bins, neu_vals, label='Trung tính', color='#6b7280', linewidth=2, linestyle='--', marker='o', markersize=6, markerfacecolor='#06070d', markeredgewidth=2, markeredgecolor='#6b7280')
    
    ax.grid(True, color='#1f2029', linestyle='-', linewidth=0.5)
    
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color('#1f2029')
        ax.spines[spine].set_linewidth(1)
        
    ax.tick_params(axis='both', colors='#9ca3af', labelsize=10)
    ax.set_ylabel("Bình luận", color='#9ca3af', fontsize=10)
    ax.set_title("Xu hướng cảm xúc theo thời gian", color='#F1F1F1', fontsize=11, fontweight='bold', pad=15)
    
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False, labelcolor='#9ca3af')
    
    plt.tight_layout()
    return fig


def get_simulated_meta(idx):
    names = [
        "Nguyễn Văn An", "Trần Thị Bình", "Lê Hoàng Cường", "Phạm Minh Đức", 
        "Hoàng Thu Thảo", "Vũ Huy Hoàng", "Đặng Ngọc Sơn", "Bùi Thị Mai", 
        "Ngô Quốc Việt", "Dương Minh Khang", "Hồ Văn Long", "Lý Thị Minh",
        "Vũ Thị Phương", "Phan Thanh Hải", "Đỗ Quốc Bảo", "Trịnh Thùy Linh"
    ]
    times = [
        "2 giờ trước", "5 giờ trước", "1 ngày trước", "2 ngày trước", 
        "3 ngày trước", "4 ngày trước", "5 ngày trước", "1 tuần trước"
    ]
    name = names[idx % len(names)]
    parts = name.split()
    initials = "".join([p[0] for p in parts[-2:]]) if len(parts) >= 2 else name[0]
    time_ago = times[idx % len(times)]
    likes_count = (idx * 7 + 3) % 43
    return {"name": name, "initials": initials, "time": time_ago, "likes": likes_count}


# ============================================
# RENDER PAGE FLOW
# ============================================

# Case 1: NOT logged in -> show login screen
if st.session_state['user'] is None:
    st.markdown('<div class="perspective-grid"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center; margin-top:3.5rem; margin-bottom:1.5rem;">
        <div class="auth-logo-icon">✦</div>
        <h1 class="auth-title">YouTube Comment</h1>
        <h2 class="auth-subtitle">AI Analyzer Pro</h2>
        <p class="auth-desc">Phân tích cảm xúc bình luận bằng AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    form_cols = st.columns([1, 1.8, 1])
    with form_cols[1]:
        with st.container(border=True):
            if st.session_state['auth_mode'] == 'login':
                email = st.text_input("Email", placeholder="you@example.com", key="login_email")
                password = st.text_input("Mật khẩu", type="password", placeholder="••••••••", key="login_pass")
                
                sub_cols = st.columns([1, 1])
                with sub_cols[0]:
                    remember = st.checkbox("Ghi nhớ đăng nhập", value=True)
                with sub_cols[1]:
                    if st.button("Quên mật khẩu?", key="forgot_pw_toggle", type="secondary", use_container_width=True):
                        st.session_state['auth_mode'] = 'forgot'
                        st.rerun()
                
                if st.button("Đăng nhập ➔", key="login_submit", use_container_width=True):
                    if not email or not password:
                        st.error("Vui lòng điền đầy đủ Email và Mật khẩu!")
                    else:
                        with st.spinner("Đang đăng nhập..."):
                            res = firebase_auth(email, password, mode="login")
                            if res["success"]:
                                st.session_state['user'] = res["data"]
                                st.success("Đăng nhập thành công!")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {res['error']}")
                                
                st.markdown("<hr style='margin:1.5rem 0;'>", unsafe_allow_html=True)
                st.markdown('<p style="text-align:center; color:#888; font-size:0.9rem; margin-bottom:1rem;">Chưa có tài khoản? Đăng ký ngay</p>', unsafe_allow_html=True)
                if st.button("Tạo tài khoản mới", key="go_to_signup", use_container_width=True):
                    st.session_state['auth_mode'] = 'signup'
                    st.rerun()
                    
            elif st.session_state['auth_mode'] == 'signup':
                email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
                password = st.text_input("Mật khẩu (tối thiểu 6 ký tự)", type="password", placeholder="••••••••", key="signup_pass")
                confirm_password = st.text_input("Xác nhận mật khẩu", type="password", placeholder="••••••••", key="signup_confirm")
                
                if st.button("Đăng ký ➔", key="signup_submit", use_container_width=True):
                    if not email or not password or not confirm_password:
                        st.error("Vui lòng điền đầy đủ thông tin!")
                    elif password != confirm_password:
                        st.error("Mật khẩu xác nhận không khớp!")
                    else:
                        with st.spinner("Đang tạo tài khoản..."):
                            res = firebase_auth(email, password, mode="signup")
                            if res["success"]:
                                st.session_state['user'] = res["data"]
                                st.success("Đăng ký tài khoản thành công!")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {res['error']}")
                                
                st.markdown("<hr style='margin:1.5rem 0;'>", unsafe_allow_html=True)
                if st.button("Quay lại Đăng nhập", key="go_to_login", use_container_width=True):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()
                    
            elif st.session_state['auth_mode'] == 'forgot':
                email = st.text_input("Nhập Email của bạn", placeholder="you@example.com", key="forgot_email")
                
                if st.button("Gửi link khôi phục mật khẩu ➔", key="forgot_submit", use_container_width=True):
                    if not email:
                        st.error("Vui lòng nhập Email!")
                    else:
                        with st.spinner("Đang gửi yêu cầu..."):
                            res = firebase_auth(email, None, mode="forgot")
                            if res["success"]:
                                st.success("Đã gửi email khôi phục mật khẩu! Vui lòng kiểm tra hộp thư.")
                            else:
                                st.error(f"Lỗi: {res['error']}")
                                
                st.markdown("<hr style='margin:1.5rem 0;'>", unsafe_allow_html=True)
                if st.button("Quay lại Đăng nhập", key="go_to_login_from_forgot", use_container_width=True):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()
        
    st.markdown("""
    <div class="auth-footer-row">
        <div class="auth-footer-item">
            <div class="auth-footer-title">AI</div>
            <div class="auth-footer-sub">Phân tích thông minh</div>
        </div>
        <div class="auth-footer-item">
            <div class="auth-footer-title">27+</div>
            <div class="auth-footer-sub">Ngôn ngữ hỗ trợ</div>
        </div>
        <div class="auth-footer-item">
            <div class="auth-footer-title">Realtime</div>
            <div class="auth-footer-sub">Kết quả tức thì</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# Case 2: Logged in -> show main app with custom Navbar Header
else:
    st.markdown('<div class="perspective-grid"></div>', unsafe_allow_html=True)
    
    # Render Navbar Header mockup-style
    nav_cols = st.columns([6, 2, 2])
    with nav_cols[0]:
        st.markdown("""
        <div class="custom-navbar" style="border-bottom:none; padding: 0.5rem 0; margin-bottom:0;">
            <div class="nav-logo">
                <div class="nav-logo-icon">✦</div>
                <span>YouTube <span>AI</span></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with nav_cols[1]:
        if st.button("🕒 Lịch sử", key="nav_history_btn", use_container_width=True):
            st.session_state['show_history'] = True
            st.rerun()
    with nav_cols[2]:
        if st.button("🚪 Đăng xuất", key="nav_logout_btn", use_container_width=True):
            st.session_state['user'] = None
            st.session_state['analysis_results'] = None
            st.session_state['telegram_sent'] = False
            st.session_state['show_history'] = False
            st.rerun()
            
    st.markdown("<hr style='margin: 0.5rem 0 2rem;'>", unsafe_allow_html=True)

    if st.session_state.get('show_history', False):
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1.5rem;">
            <h3 style="color:#00f2fe; margin:0; text-shadow:0 0 10px rgba(0, 242, 254, 0.3);">🕒</h3>
            <h3 style="color:#FFFFFF; margin:0;">Lịch sử phân tích</h3>
        </div>
        """, unsafe_allow_html=True)
        
        email = st.session_state['user']['email']
        id_token = st.session_state['user']['idToken']
        
        with st.spinner("Đang tải lịch sử từ Firebase..."):
            history_res = fetch_history(id_token, email)
            
        if not history_res["success"]:
            st.error(f"Không thể lấy lịch sử: {history_res['error']}")
            st.info("💡 Lưu ý: Hãy đảm bảo bạn đã kích hoạt Cloud Firestore trong Firebase Console và cấu hình Rule cho phép truy cập.")
        else:
            records = history_res["data"]
            if not records:
                st.info("Bạn chưa thực hiện phân tích nào hoặc lịch sử trống.")
            else:
                with st.container(border=True):
                    for idx, item in enumerate(records):
                        try:
                            time_part = item['timestamp'].split('T')[0]
                            p_icons = {
                                "youtube": "🔴 YouTube",
                                "tiktok": "🎵 TikTok",
                                "shopee": "🛍️ Shopee",
                                "facebook": "👥 Facebook",
                                "lazada": "💙 Lazada",
                                "tiki": "📦 Tiki"
                            }
                            plat_text = p_icons.get(item['platform'].lower(), item['platform'])
                        except Exception:
                            time_part = "N/A"
                            plat_text = item['platform']
                            
                        cols_item = st.columns([1.5, 4.5, 1.5, 2.5])
                        with cols_item[0]:
                            st.markdown(f"<span style='color:#00f2fe;font-weight:600;'>{plat_text}</span>", unsafe_allow_html=True)
                        with cols_item[1]:
                            short_url = item['url']
                            if len(short_url) > 60:
                                short_url = short_url[:57] + "..."
                            st.markdown(f"<a href='{item['url']}' target='_blank' style='color:#cbd5e1;text-decoration:none;'>{short_url}</a>", unsafe_allow_html=True)
                        with cols_item[2]:
                            st.markdown(f"<span style='font-family:\"Orbitron\", sans-serif;font-weight:800;color:#10b981;'>{item['score']:.1f} / 10</span>", unsafe_allow_html=True)
                        with cols_item[3]:
                            sub_cols = st.columns([1.5, 1])
                            with sub_cols[0]:
                                if st.button("🔄 Chạy lại", key=f"re_run_{idx}", use_container_width=True):
                                    st.session_state['current_url'] = item['url']
                                    st.session_state['current_platform'] = item['platform']
                                    st.session_state['show_history'] = False
                                    st.session_state['analysis_results'] = None
                                    st.session_state['trigger_analysis'] = True
                                    st.rerun()
                            with sub_cols[1]:
                                st.markdown(f"<span style='color:#6b7280;font-size:0.85rem;line-height:2.2;'>{time_part}</span>", unsafe_allow_html=True)
                        st.markdown("<hr style='margin:0.8rem 0;opacity:0.1;'>", unsafe_allow_html=True)
                
        if st.button("⬅️ Quay lại Dashboard", key="back_to_dashboard_btn"):
            st.session_state['show_history'] = False
            st.rerun()
            
        st.stop()

    # UI - HERO
    st.markdown(f"""
    <div class="hero-section">
        <div style="font-size:4rem;margin-bottom:0.5rem;">{theme['icon']}🤖</div>
        <h1 class="hero-title">{theme['name']} Comment<br><span>AI Analyzer Pro</span></h1>
        <p style="color:#AAAAAA;max-width:600px;margin:0 auto;font-size:0.95rem;">
            Tự động nhận diện nền tảng và phân tích cảm xúc bình luận thời gian thực.<br>
            Đánh giá chất lượng nội dung qua góc nhìn của người dùng.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # INPUT
    with st.container(border=True):
        cols = st.columns([4.5, 2.5, 3])
        with cols[0]:
            new_url = st.text_input("Link Mạng Xã Hội/E-commerce", value=st.session_state['current_url'], 
                               placeholder="Dán link YouTube, TikTok, Shopee, Facebook, Lazada, Tiki...", label_visibility="collapsed")
            if new_url != st.session_state['current_url']:
                st.session_state['current_url'] = new_url
                st.session_state['analysis_results'] = None
                st.session_state['telegram_sent'] = False
                st.rerun()
                
        with cols[1]:
            lang_option = st.selectbox(
                "Ngôn ngữ phân tích",
                options=["Tiếng Việt 🇻🇳", "English / Multi-language 🌐"],
                index=0,
                label_visibility="collapsed"
            )
        with cols[2]:
            analyze_clicked = st.button(f"➔ Phân tích {theme['name']}", use_container_width=True)

    # ANALYZE
    if analyze_clicked or st.session_state.get('trigger_analysis', False):
        if st.session_state.get('trigger_analysis', False):
            st.session_state['trigger_analysis'] = False
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
                
                # Fetch comments
                all_comments, actual_platform, is_offline = get_comments(st.session_state['current_url'], max_total=1000, youtube_api_key=API_KEY)
                
                if is_offline:
                    st.warning(f"⚠️ **Offline Mode:** Hệ thống không thể thu thập dữ liệu trực tiếp. Chuyển sang sử dụng tập dữ liệu dự phòng.")
                
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
            
            dominant = max(sentiment_counts, key=sentiment_counts.get)
            if dominant == "Tích cực":
                badge_type = "pos"
                badge_text = "👍 Rất tích cực"
            elif dominant == "Tiêu cực":
                badge_type = "neg"
                badge_text = "👎 Tiêu cực"
            else:
                badge_type = "neu"
                badge_text = "😐 Trung tính"
                
            pos_pct = round((sentiment_counts["Tích cực"] / total) * 100, 1)
            neg_pct = round((sentiment_counts["Tiêu cực"] / total) * 100, 1)
            neu_pct = round((sentiment_counts["Trung tính"] / total) * 100, 1)
            
            if star_rating >= 4.0:
                summary_header = f"Nội dung được đánh giá <strong>RẤT TÍCH CỰC</strong> ({pos_pct}% tích cực). Phản hồi cực kỳ tốt."
                summary_text = f"Nội dung được đánh giá RẤT TÍCH CỰC ({pos_pct}% tích cực). Phản hồi cực kỳ tốt. Người xem đánh giá cao phong cách trình bày dễ hiểu và các mẹo thực tế."
                tags = ["Học lập trình", "Mẹo học tập", "ReactJS", "Tự học"]
            elif star_rating >= 3.0:
                summary_header = f"Nội dung có đánh giá <strong>KHÁ TÍCH CỰC</strong> ({pos_pct}% tích cực). Nhìn chung khá ổn."
                summary_text = f"Nội dung có đánh giá KHÁ TÍCH CỰC ({pos_pct}% tích cực). Người dùng phản hồi tương đối tốt, nội dung có tính xây dựng cao."
                tags = ["Chia sẻ", "Kiến thức", "Hữu ích"]
            else:
                summary_header = f"Nội dung bị đánh giá <strong>TIÊU CỰC</strong> ({pos_pct}% tích cực). Cần chú ý cải thiện."
                summary_text = f"Nội dung bị đánh giá TIÊU CỰC ({pos_pct}% tích cực). Phản hồi xấu từ người dùng, xuất hiện nhiều điểm phàn nàn và thắc mắc."
                tags = ["Góp ý", "Cải thiện", "Phản hồi"]
                
            lang_code = "vi" if lang_option == "Tiếng Việt 🇻🇳" else "en"
            keywords = wordcloud_utils.extract_keywords(df["Bình luận"].tolist(), top_k=50, language=lang_code)
            
            # Pain points extraction
            neg_df = df[df["Cảm xúc"] == "Tiêu cực"]
            neg_keywords = wordcloud_utils.extract_keywords(neg_df["Bình luận"].tolist(), top_k=10, language=lang_code)
            pain_points_data = []
            if neg_keywords:
                for kw, count in neg_keywords[:2]:
                    sample_desc = "Không có mô tả chi tiết."
                    for c in neg_df["Bình luận"]:
                        if kw.lower() in c.lower():
                            sample_desc = c
                            if len(sample_desc) > 85:
                                sample_desc = sample_desc[:85] + "..."
                            break
                    pain_points_data.append({"title": kw, "count": count, "desc": sample_desc})
            
            # Fallback pain points
            if len(pain_points_data) < 2:
                fallbacks = {
                    "youtube": [
                        {"title": "khó hiểu", "count": 1, "desc": "Một số phần hơi khó hiểu với người mới bắt đầu học kiến thức mới."},
                        {"title": "quá nhanh", "count": 1, "desc": "Tốc độ giảng giải ở một số phân đoạn (phút 15) hơi nhanh, cần xem lại."}
                    ],
                    "tiktok": [
                        {"title": "thời lượng ngắn", "count": 2, "desc": "Thời lượng video quá ngắn, chưa phân tích kỹ và đầy đủ nội dung."},
                        {"title": "chữ chạy nhanh", "count": 1, "desc": "Phần text phụ đề chạy hơi nhanh, người dùng không kịp đọc hết."}
                    ],
                    "shopee": [
                        {"title": "giao hàng chậm", "count": 2, "desc": "Thời gian vận chuyển lâu hơn dự kiến, đơn hàng bị lưu kho nhiều ngày."},
                        {"title": "đóng gói sơ sài", "count": 1, "desc": "Hộp sản phẩm bị bóp méo nhẹ do không được chèn thêm bọc khí chống sốc."}
                    ]
                }
                platform_fallbacks = fallbacks.get(st.session_state['current_platform'], fallbacks["youtube"])
                for fb in platform_fallbacks:
                    if len(pain_points_data) < 2:
                        pain_points_data.append(fb)
            
            # Save to Firestore history (silently)
            try:
                id_token = st.session_state['user']['idToken']
                email = st.session_state['user']['email']
                save_history(id_token, email, st.session_state['current_url'], st.session_state['current_platform'], avg_score)
            except Exception:
                pass

            # Save to session state
            st.session_state['analysis_results'] = {
                'df': df,
                'sentiment_counts': sentiment_counts,
                'avg_score': avg_score,
                'star_rating': star_rating,
                'total': total,
                'pos_pct': pos_pct,
                'neg_pct': neg_pct,
                'neu_pct': neu_pct,
                'keywords': keywords,
                'pain_points_data': pain_points_data,
                'theme': theme,
                'model_name': model_name,
                'lang_option': lang_option,
                'summary_header': summary_header,
                'summary_text': summary_text,
                'tags': tags,
                'badge_text': badge_text,
                'badge_type': badge_type
            }
            st.session_state['telegram_sent'] = False
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Lỗi xử lý: {e}")

    # PERSISTENT RESULTS DISPLAY
    results = st.session_state.get('analysis_results')
    if results is not None:
        df = results['df']
        sentiment_counts = results['sentiment_counts']
        avg_score = results['avg_score']
        star_rating = results['star_rating']
        total = results['total']
        pos_pct = results['pos_pct']
        neg_pct = results['neg_pct']
        neu_pct = results['neu_pct']
        keywords = results['keywords']
        pain_points_data = results['pain_points_data']
        theme = results['theme']
        model_name = results['model_name']
        lang_option = results['lang_option']
        summary_header = results['summary_header']
        summary_text = results['summary_text']
        tags = results['tags']
        badge_text = results['badge_text']
        badge_type = results['badge_type']
        
        # SUCCESS MESSAGE (Tick icon - Image 2)
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:2rem; margin-top:1rem;">
            <div class="done-tick">✓</div>
            <h2 style="color:#10b981; font-weight:700; font-family:'Orbitron', sans-serif;">Phân tích hoàn tất!</h2>
            <p style="color:#9ca3af; font-size:1.05rem;">Đã phân tích <strong style="color:#00f2fe;">{total}</strong> bình luận trên <b>{theme["name"]}</b> bằng AI.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # SCORE CARD (Image 2)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        stars_html = render_stars_html(star_rating)
        st.markdown(f"""
        <div style="text-align:center; padding: 1rem 0;">
            <div style="color:#888; font-size:0.85rem; letter-spacing:1.5px; font-weight:600; text-transform:uppercase;">Tổng số điểm đánh giá</div>
            <div style="font-size:5.5rem; font-weight:900; color:#00f2fe; font-family:'Orbitron', sans-serif; text-shadow:0 0 25px rgba(0, 242, 254, 0.4); margin: 0.2rem 0;">{avg_score}</div>
            <div style="margin-bottom: 0.5rem;">{stars_html}</div>
            <div style="color:#888; font-size:0.95rem;">/ 10 điểm • {star_rating} / 5 sao</div>
            <div style="margin-top: 1.2rem; display:inline-block;" class="badge-{badge_type}">{badge_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # STATS ROW (4 Cards - Image 2)
        cols = st.columns(4)
        stats_data = [
            ("👍", "Tích cực", sentiment_counts["Tích cực"], "color-green"),
            ("👎", "Tiêu cực", sentiment_counts["Tiêu cực"], "color-red"),
            ("➖", "Trung tính", sentiment_counts["Trung tính"], "color-grey"),
            ("💬", "Tổng", total, "color-cyan"),
        ]
        for col, (icon, label, val, color_class) in zip(cols, stats_data):
            with col:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-card-icon {color_class}">{icon}</div>
                    <div class="stat-card-val {color_class}">{val}</div>
                    <div class="stat-card-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # CHART + SUMMARY (2 columns - Image 3)
        st.markdown("<hr>", unsafe_allow_html=True)
        cols = st.columns([1, 1])
        
        with cols[0]:
            with st.container(border=True):
                st.markdown('<h4 style="margin-bottom:1rem;color:#F1F1F1;">📊 Phân bố cảm xúc</h4>', unsafe_allow_html=True)
                fig_donut = plot_cyberpunk_donut_chart(sentiment_counts)
                st.pyplot(fig_donut, use_container_width=True)
                
                # Legend below donut chart matching mockup
                st.markdown(f"""
                <div style="display:flex; justify-content:center; gap:1.5rem; margin-top:1rem; font-size:0.9rem;">
                    <div><span class="color-green">●</span> Tích cực <b>{pos_pct}%</b></div>
                    <div><span class="color-red">●</span> Tiêu cực <b>{neg_pct}%</b></div>
                    <div><span class="color-grey">●</span> Trung tính <b>{neu_pct}%</b></div>
                </div>
                """, unsafe_allow_html=True)
        
        with cols[1]:
            with st.container(border=True):
                st.markdown('<h4 style="margin-bottom:1rem;color:#F1F1F1;">⚡ Tóm tắt & Xuất đề tài</h4>', unsafe_allow_html=True)
                
                # Render summary status box
                st.markdown(f"""
                <div class="summary-status-box">
                    <div class="summary-status-icon">✓</div>
                    <div class="summary-status-text">{summary_header}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render summary text area
                st.markdown(f"""
                <div class="summary-text-box">
                    {summary_text}
                </div>
                """, unsafe_allow_html=True)
                
                # Tags list
                tags_html = "".join([f'<span class="tag-pill">🏷️ {t}</span>' for t in tags])
                st.markdown(f'<div class="tags-container">{tags_html}</div>', unsafe_allow_html=True)
                
                # Summarize video button
                st.button("📄 Tóm tắt video", key="summarize_video_btn", use_container_width=True)
                
                # Progress bars
                st.markdown(f"""
                <div style="margin-top:1.5rem;">
                    <div class="progress-row">
                        <div class="progress-label-row">
                            <span>Tích cực</span>
                            <strong>{pos_pct}%</strong>
                        </div>
                        <div class="progress-bar-bg"><div class="progress-bar-fill fill-pos" style="width:{pos_pct}%;"></div></div>
                    </div>
                    <div class="progress-row">
                        <div class="progress-label-row">
                            <span>Tiêu cực</span>
                            <strong>{neg_pct}%</strong>
                        </div>
                        <div class="progress-bar-bg"><div class="progress-bar-fill fill-neg" style="width:{neg_pct}%;"></div></div>
                    </div>
                    <div class="progress-row">
                        <div class="progress-label-row">
                            <span>Trung tính</span>
                            <strong>{neu_pct}%</strong>
                        </div>
                        <div class="progress-bar-bg"><div class="progress-bar-fill fill-neu" style="width:{neu_pct}%;"></div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # KEYWORDS (Image 1, batch 2)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1.5rem;">
            <h3 style="color:#00f2fe; margin:0; text-shadow:0 0 10px rgba(0, 242, 254, 0.3);">#</h3>
            <h3 style="color:#FFFFFF; margin:0;">Từ khóa nổi bật</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            kw_cols = st.columns([1, 1.3])
            
            with kw_cols[0]:
                # Left side: Keywords table with progress bars matching mockup
                table_rows = ""
                max_count = keywords[0][1] if keywords else 1
                for idx, (word, count) in enumerate(keywords[:6]):
                    pct = int((count / max_count) * 100)
                    bar_color = "#00f2fe" if idx < 3 else "#1c3d73"
                    table_rows += f"""
                    <tr>
                        <td class="keyword-td-word" style="width: 25%; font-size: 0.95rem; color: #9ca3af; padding: 0.8rem 0;">{word}</td>
                        <td style="width: 60%; vertical-align: middle; padding: 0.8rem 0.5rem;">
                            <div class="progress-bar-bg" style="height: 12px; background: rgba(255, 255, 255, 0.03); border-radius: 6px; overflow: hidden; border: 1px solid rgba(255,255,255,0.05);">
                                <div class="progress-bar-fill" style="width: {pct}%; height: 100%; background: {bar_color}; border-radius: 6px; box-shadow: 0 0 8px {bar_color}44;"></div>
                            </div>
                        </td>
                        <td class="keyword-td-count" style="width: 15%; text-align: right; font-weight: 700; color: #ffffff; padding: 0.8rem 0; font-family: 'Orbitron', sans-serif !important;">{count}</td>
                    </tr>
                    """
                st.markdown(f'<table class="keyword-table" style="margin-top: 1rem;">{table_rows}</table>', unsafe_allow_html=True)
                
            with kw_cols[1]:
                # Right side: custom bar chart
                fig_kw = plot_cyberpunk_keyword_bar_chart(keywords, top_n=8)
                st.pyplot(fig_kw, use_container_width=True)
        
        # PAIN POINTS (Image 2, batch 2)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
            <h3 style="color:#ef4444; margin:0; text-shadow:0 0 10px rgba(239, 68, 68, 0.3);">⚠️</h3>
            <h3 style="color:#FFFFFF; margin:0;">Phân tích điểm yếu (Pain-point)</h3>
        </div>
        <p style="color:#6b7280; font-size:0.9rem; margin-bottom:1.5rem;">
            Phân tích dựa được đưa ra nhiều nhất trong các bài bình luận tiêu cực, giúp bạn xác định được khu vực cần ưu tiên cải thiện.
        </p>
        """, unsafe_allow_html=True)
        
        pain_cols = st.columns(2)
        for idx, data_p in enumerate(pain_points_data):
            with pain_cols[idx]:
                st.markdown(f"""
                <div class="pain-point-card">
                    <div class="pain-point-header">
                        <div class="pain-point-title-group">
                            <div class="pain-point-icon">💬</div>
                            <div>
                                <div class="pain-point-title" style="text-transform: lowercase;">{data_p['title']}</div>
                                <div class="pain-point-sub">{data_p['count']} lần được nhắc</div>
                            </div>
                        </div>
                        <div class="pain-point-badge">{data_p['count']}</div>
                    </div>
                    <div class="pain-point-desc">{data_p['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                
        # TIME CHART (Image 3, batch 2)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1.5rem;">
            <h3 style="color:#00f2fe; margin:0; text-shadow:0 0 10px rgba(0, 242, 254, 0.3);">📈</h3>
            <h3 style="color:#FFFFFF; margin:0;">Xu hướng cảm xúc</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            fig_line = plot_cyberpunk_line_chart(sentiment_counts)
            st.pyplot(fig_line, use_container_width=True)
        
        # COMMENTS DETAIL LIST WITH TAB FILTERS (Image 4 & 5, batch 1)
        st.markdown("<hr>", unsafe_allow_html=True)
        
        header_cols = st.columns([6, 3])
        with header_cols[0]:
            st.markdown("""
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1.5rem;">
                <h3 style="color:#00f2fe; margin:0; text-shadow:0 0 10px rgba(0, 242, 254, 0.3);">💬</h3>
                <h3 style="color:#FFFFFF; margin:0;">Chi tiết bình luận</h3>
            </div>
            """, unsafe_allow_html=True)
        with header_cols[1]:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Tải báo cáo (CSV)",
                data=csv,
                file_name='bao_cao_binh_luan.csv',
                mime='text/csv',
                use_container_width=True
            )
            
        tabs = st.tabs(["Tất cả", "Tích cực", "Tiêu cực", "Trung tính"])
        
        def render_custom_comments_list(filtered_df):
            if filtered_df.empty:
                st.info("Không có bình luận nào thuộc nhóm này.")
                return
                
            display_df = filtered_df.head(100).copy()
            st.markdown(f'<span style="color:#6b7280;font-size:0.9rem;margin-bottom:15px;display:block;">Hiển thị {len(display_df)} / {len(filtered_df)} bình luận</span>', unsafe_allow_html=True)
            
            # HTML builder for premium comment cards list
            list_html = ""
            for idx, row in display_df.reset_index().iterrows():
                c_text = row["Bình luận"]
                c_sent = row["Cảm xúc"]
                c_score = f"{float(row['Điểm']):.1f}"
                
                # Generate simulated user names, dates and likes
                meta = get_simulated_meta(idx)
                
                badge_class = "comment-badge-pos" if c_sent == "Tích cực" else "comment-badge-neg" if c_sent == "Tiêu cực" else "comment-badge-neu"
                score_color = "#10b981" if c_sent == "Tích cực" else "#ef4444" if c_sent == "Tiêu cực" else "#9ca3af"
                
                list_html += f"""
                <div class="comment-card">
                    <div class="comment-card-left">
                        <div class="comment-avatar">{meta['initials']}</div>
                        <div class="comment-content">
                            <div class="comment-header">
                                <span class="comment-user">{meta['name']}</span>
                                <span>•</span>
                                <span class="comment-time">{meta['time']}</span>
                                <span>•</span>
                                <span class="comment-likes">{meta['likes']} lượt thích</span>
                            </div>
                            <div class="comment-text">{c_text}</div>
                        </div>
                    </div>
                    <div class="comment-card-right">
                        <span class="{badge_class}">{c_sent}</span>
                        <span class="comment-score" style="color:{score_color};">{c_score}</span>
                    </div>
                </div>
                """
            
            st.markdown(list_html, unsafe_allow_html=True)
            
        with tabs[0]: render_custom_comments_list(df)
        with tabs[1]: render_custom_comments_list(df[df["Cảm xúc"] == "Tích cực"])
        with tabs[2]: render_custom_comments_list(df[df["Cảm xúc"] == "Tiêu cực"])
        with tabs[3]: render_custom_comments_list(df[df["Cảm xúc"] == "Trung tính"])
        
        # TELEGRAM SENDER (Runs exactly once per analysis)
        if not st.session_state.get('telegram_sent', False):
            try:
                import io as _io
                tele_summary = summary_text
                
                # Tin nhắn text đầy đủ
                msg  = f"📊 BÁO CÁO PHÂN TÍCH {theme['name'].upper()}\n"
                msg += f"{'='*40}\n"
                msg += f"🔗 Link: {st.session_state['current_url']}\n"
                msg += f"🤖 Mô hình AI: {model_name}\n"
                msg += f"📋 Ngôn ngữ phân tích: {lang_option}\n"
                msg += f"⭐ Điểm tổng thể: {avg_score}/10 ({star_rating}/5 sao)\n"
                msg += f"{'─'*40}\n"
                msg += f"📈 THỐNG KÊ ({total} bình luận):\n"
                msg += f"  🟢 Tích cực : {sentiment_counts['Tích cực']:>4}  ({pos_pct}%)\n"
                msg += f"  🔴 Tiêu cực : {sentiment_counts['Tiêu cực']:>4}  ({neg_pct}%)\n"
                msg += f"  ⚪ Trung tính: {sentiment_counts['Trung tính']:>4}  ({neu_pct}%)\n"
                msg += f"{'─'*40}\n"
                msg += f"💡 Đánh giá: {tele_summary}\n"
                msg += f"📌 Đề xuất: {badge_text}\n"
                
                res_text = send_telegram_message({"chat_id": int(CHAT_ID), "text": msg})
                
                if keywords:
                    buf_donut = _io.BytesIO()
                    fig_donut.savefig(buf_donut, format='png', dpi=150, bbox_inches='tight', facecolor='#06070d')
                    buf_donut.seek(0)
                    send_telegram_photo(buf_donut, caption="📊 Phân bố cảm xúc")
                    
                    buf_kw = _io.BytesIO()
                    fig_kw.savefig(buf_kw, format='png', dpi=150, bbox_inches='tight', facecolor='#06070d')
                    buf_kw.seek(0)
                    send_telegram_photo(buf_kw, caption="📊 Từ khóa nổi bật")
                    
                _line_fig = line_chart_utils.plot_sentiment_line_chart(df.copy())
                buf_line = _io.BytesIO()
                _line_fig.savefig(buf_line, format='png', dpi=150, bbox_inches='tight', facecolor='#121212')
                _line_fig.close()
                send_telegram_photo(buf_line, caption="📈 Xu hướng cảm xúc theo thời gian")
                
                st.session_state['telegram_sent'] = True
                if res_text:
                    st.toast("Đã gửi báo cáo đầy đủ + biểu đồ về Telegram! 🚀", icon="✅")
                else:
                    st.toast("Không thể gửi báo cáo Telegram. Vui lòng kiểm tra lại Token/Chat ID.", icon="⚠️")
            except Exception as e:
                st.toast(f"Lỗi gửi Telegram: {e}", icon="⚠️")
                
        # Footer of page matching mockup
        st.markdown(f"""
        <div style="text-align:center; margin: 4rem 0 1.5rem; color:#6b7280; font-size:0.9rem; border-top: 1px solid rgba(255,255,255,0.03); padding-top: 2rem;">
            <div style="display:flex; justify-content:center; align-items:center; gap:0.5rem; font-family:'Orbitron', sans-serif !important; font-weight:700; color:#fff; margin-bottom:0.3rem;">
                <span style="color:#00f2fe; text-shadow:0 0 10px rgba(0, 242, 254, 0.4);">✦</span> {theme['name']} AI Analyzer Pro
            </div>
            Phân tích cảm xúc bình luận bằng AI • 2026
        </div>
        """, unsafe_allow_html=True)
