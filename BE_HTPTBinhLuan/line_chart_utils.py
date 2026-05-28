import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import re
from underthesea import word_tokenize
from datetime import datetime
import platform
import warnings

# Ẩn các cảnh báo thiếu Glyph từ Matplotlib khi thực hiện cơ chế fallback font
warnings.simplefilter('ignore', UserWarning)

# Cấu hình font chữ đa ngôn ngữ thông minh
if platform.system() == "Windows":
    plt.rcParams['font.family'] = 'sans-serif'
    # Các font chữ tiếng Việt cực kỳ ổn định mặc định
    font_sans = ['Arial', 'Calibri', 'Segoe UI', 'Tahoma']
    
    # Kiểm tra xem có font tiếng Trung (CJK) nào thực sự được cài đặt trên máy không
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
                break  # Lấy font tiếng Trung tốt nhất tìm thấy đưa lên đầu tiên
                
    plt.rcParams['font.sans-serif'] = font_sans
else:
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial']

def get_vietnamese_font_path():
    """Return a font path that supports Vietnamese and CJK characters.
    Tries common Windows fonts first, then falls back to a Matplotlib sans‑serif font.
    """
    import os
    windows_fonts = [
        "C:\\Windows\\Fonts\\Arial.ttf",
        "C:\\Windows\\Fonts\\Calibri.ttf",
        "C:\\Windows\\Fonts\\SegoeUI.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\msyh.ttc",  # Microsoft YaHei (covers CJK)
        "C:\\Windows\\Fonts\\simhei.ttf",   # SimHei (Chinese)
    ]
    for path in windows_fonts:
        if os.path.exists(path):
            return path
    # Fallback to any available sans‑serif font via matplotlib
    try:
        import matplotlib.font_manager as fm
        fallback = fm.findfont(fm.FontProperties(family="sans-serif"))
        if os.path.exists(fallback):
            return fallback
    except Exception:
        pass
    return None

def extract_dates_from_comments(comments, date_pattern=r'\d{1,2}/\d{1,2}/\d{2,4}'):
    """
    Tìm ngày tháng trong bình luận (nếu có) theo pattern dd/mm/yyyy hoặc dd/mm/yy
    Trả về list ngày dạng datetime.date
    """
    dates = []
    for c in comments:
        match = re.search(date_pattern, c)
        if match:
            try:
                d = datetime.strptime(match.group(), "%d/%m/%Y").date()
            except:
                try:
                    d = datetime.strptime(match.group(), "%d/%m/%y").date()
                except:
                    continue
            dates.append(d)
    return dates

def plot_sentiment_line_chart(df, date_col=None, date_format="%d/%m/%Y"):
    """
    df: DataFrame có cột 'Bình luận', 'Cảm xúc', 'Ngày' (nếu có)
    Nếu không có cột ngày, sẽ random ngày cho demo
    """
    import numpy as np
    import matplotlib.font_manager as fm
    
    if date_col is None or date_col not in df.columns:
        # Sinh ngày ngẫu nhiên cho demo
        base = datetime.today().date()
        df["Ngày"] = [base - pd.Timedelta(days=int(x)) for x in np.linspace(0, 10, len(df))]
        date_col = "Ngày"
        
    # Đếm số lượng cảm xúc theo ngày và sắp xếp theo ngày tăng dần
    pivot = df.groupby([date_col, "Cảm xúc"]).size().unstack(fill_value=0)
    pivot = pivot.sort_index()
    
    # Thiết lập giao diện biểu đồ tối cực kỳ hiện đại
    fig, ax = plt.subplots(figsize=(10, 5), facecolor='#121212')
    ax.set_facecolor('#121212')
    
    # Màu sắc đại diện cho các nhóm cảm xúc (Neon hiện đại)
    colors = {
        "Tích cực": "#10b981",  # Xanh lục bảo (Emerald)
        "Tiêu cực": "#ef4444",  # Đỏ hồng (Rose)
        "Trung tính": "#6b7280"  # Xám (Zinc)
    }
    
    # Vẽ các đường cảm xúc
    for label in ["Tích cực", "Tiêu cực", "Trung tính"]:
        if label in pivot:
            x_vals = pivot.index
            y_vals = pivot[label]
            color = colors.get(label, "#9ca3af")
            
            # Vẽ đường và điểm
            ax.plot(
                x_vals, y_vals, 
                label=label, 
                color=color, 
                linewidth=3, 
                marker='o', 
                markersize=6, 
                markerfacecolor='#121212', 
                markeredgewidth=2,
                markeredgecolor=color
            )
            
            # Tô màu vùng phía dưới đường (với độ mờ thấp tạo hiệu ứng gradient)
            ax.fill_between(
                x_vals, y_vals, 0,
                color=color,
                alpha=0.08
            )
            
    # Tinh chỉnh lưới tọa độ và trục tọa độ
    ax.grid(True, which='both', color='#2a2a2a', linestyle='--', linewidth=0.5)
    
    # Định dạng các cạnh biểu đồ (spines)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color('#374151')
        ax.spines[spine].set_linewidth(1)
        
    # Nạp font vật lý trực tiếp
    font_path = get_vietnamese_font_path()
    if font_path:
        font_title = fm.FontProperties(fname=font_path, size=14, weight='bold')
        font_label = fm.FontProperties(fname=font_path, size=11)
        font_tick = fm.FontProperties(fname=font_path, size=10)
        font_legend = fm.FontProperties(fname=font_path, size=10)
    else:
        font_title, font_label, font_tick, font_legend = None, None, None, None

    # Cấu hình nhãn trục và tiêu đề bằng font chỉ định trực tiếp
    if font_label:
        ax.set_xlabel("Ngày", color='#9ca3af', fontproperties=font_label, labelpad=10)
        ax.set_ylabel("Số bình luận", color='#9ca3af', fontproperties=font_label, labelpad=10)
    else:
        ax.set_xlabel("Ngày", color='#9ca3af', fontsize=11, labelpad=10)
        ax.set_ylabel("Số bình luận", color='#9ca3af', fontsize=11, labelpad=10)
        
    if font_title:
        ax.set_title("Xu hướng cảm xúc theo thời gian", color='#F1F1F1', fontproperties=font_title, pad=20)
    else:
        ax.set_title("Xu hướng cảm xúc theo thời gian", color='#F1F1F1', fontsize=14, fontweight='bold', pad=20)
    
    # Tùy chỉnh tick values (thông số trên trục)
    ax.tick_params(axis='both', colors='#9ca3af', labelsize=10)
    if font_tick:
        for ticklabel in ax.get_xticklabels():
            ticklabel.set_fontproperties(font_tick)
        for ticklabel in ax.get_yticklabels():
            ticklabel.set_fontproperties(font_tick)
    
    # Tùy chỉnh chú thích (Legend) hiện đại
    legend = ax.legend(
        facecolor='#1e1e1e', 
        edgecolor='#2a2a2a', 
        loc='upper left'
    )
    for text in legend.get_texts():
        text.set_color('#F1F1F1')
        if font_legend:
            text.set_fontproperties(font_legend)
        else:
            text.set_fontsize(10)
        
    plt.tight_layout()
    return plt

