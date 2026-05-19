import re
import os
from collections import Counter
from underthesea import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import warnings

# Ẩn các cảnh báo thiếu Glyph từ Matplotlib khi thực hiện cơ chế fallback font
warnings.simplefilter('ignore', UserWarning)

# Cấu hình font chữ đa ngôn ngữ hỗ trợ cả Tiếng Việt, Tiếng Anh & Tiếng Trung/Nhật/Hàn cho biểu đồ
if platform.system() == "Windows":
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Calibri', 'Segoe UI', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
else:
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial']

# Tiền xử lý văn bản
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[\W_]+', ' ', text)
    return text

def extract_keywords(comments, top_k=50, language='vi'):
    # comments: List[str]
    cleaned = [clean_text(c) for c in comments]
    tokens = []
    
    if language == 'vi':
        for c in cleaned:
            tokens += word_tokenize(c, format="text").split()
        stopwords = set(['và', 'là', 'của', 'có', 'cho', 'với', 'rất', 'quá', 'nhưng', 'thì', 'một', 'này', 'đã', 'còn', 'nên', 'được', 'cũng', 'đang', 'khi', 'vì', 'để', 'nhiều', 'ít', 'nữa', 'nào', 'sẽ', 'bị', 'tới', 'tôi', 'bạn', 'anh', 'chị', 'em', 'chúng', 'ta', 'họ', 'ai', 'gì', 'đó', 'ở', 'trong', 'ra', 'vào', 'lên', 'xuống', 'về', 'từ', 'sao', 'đi', 'đến', 'các', 'những', 'này', 'kia', 'ấy', 'vậy', 'thế', 'nhiều', 'ít', 'rồi', 'luôn', 'nhé', 'nha', 'ơi', 'ạ', 'ha', 'à', 'nhỉ', 'nhỉ', 'nhỉ'])
    else:  # English & other languages
        for c in cleaned:
            # Tách từ tiếng Anh bằng Regex đơn giản
            tokens += re.findall(r'\b\w{2,}\b', c)
        stopwords = set(['the', 'and', 'a', 'of', 'to', 'is', 'in', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word', 'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said', 'there', 'use', 'an', 'each', 'which', 'she', 'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'him', 'into', 'time', 'has', 'look', 'two', 'more', 'write', 'go', 'see', 'no', 'way', 'could', 'people', 'my', 'than', 'first', 'water', 'been', 'call', 'who', 'oil', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part', 'very', 'really', 'good', 'bad', 'so', 'great', 'awesome', 'nice', 'video', 'youtube', 'comment'])
        
    tokens = [t for t in tokens if t not in stopwords and len(t) > 1]
    counter = Counter(tokens)
    return counter.most_common(top_k)

def get_vietnamese_font():
    """Tìm đường dẫn font hỗ trợ tiếng Việt trên Windows hoặc hệ thống."""
    windows_fonts = [
        "C:\\Windows\\Fonts\\msyh.ttc",  # Microsoft YaHei (Hỗ trợ cả Việt, Anh, Trung)
        "C:\\Windows\\Fonts\\Arial.ttf",
        "C:\\Windows\\Fonts\\Calibri.ttf",
        "C:\\Windows\\Fonts\\SegoeUI.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\times.ttf"
    ]
    for path in windows_fonts:
        if os.path.exists(path):
            return path
    
    # Dự phòng tìm font Sans-Serif từ Matplotlib
    try:
        font_path = fm.findfont(fm.FontProperties(family='sans-serif'))
        if os.path.exists(font_path):
            return font_path
    except:
        pass
    return None

def plot_wordcloud(keywords, title=None):
    font_path = get_vietnamese_font()
    
    wc = WordCloud(
        width=1000,
        height=500,
        background_color="#121212",  # Màu nền tối hiện đại
        font_path=font_path,
        colormap="cool",             # Bảng màu neon xanh-tím nổi bật
        max_words=100,
        random_state=42
    )
    freq_dict = dict(keywords)
    wc.generate_from_frequencies(freq_dict)
    
    fig = plt.figure(figsize=(10, 5), facecolor='#121212')
    ax = fig.add_subplot(111)
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    if title:
        ax.set_title(title, color='#F1F1F1', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    return plt

def plot_keyword_bar_chart(keywords, title=None, top_n=15):
    """
    Vẽ biểu đồ cột ngang liệt kê các từ khóa hàng đầu một cách dễ đọc, hiện đại.
    """
    top_k = keywords[:top_n]
    words = [k[0] for k in top_k][::-1]  # Đảo ngược để nhiều nhất nằm ở trên cùng
    counts = [k[1] for k in top_k][::-1]
    
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='#121212')
    ax.set_facecolor('#121212')
    
    # Vẽ các thanh ngang màu neon xanh lam rực rỡ
    bars = ax.barh(words, counts, color='#00d2ff', edgecolor='none', height=0.6)
    
    # Ghi số lần xuất hiện ở cuối mỗi thanh
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + (max(counts) * 0.015), 
            bar.get_y() + bar.get_height()/2, 
            f'{int(width)}', 
            ha='left', va='center', 
            color='#F1F1F1', 
            fontsize=10, 
            fontweight='bold'
        )
        
    ax.grid(True, axis='x', color='#2a2a2a', linestyle='--', linewidth=0.5)
    
    for spine in ['top', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)
    ax.spines['left'].set_color('#374151')
    ax.spines['left'].set_linewidth(1)
    
    ax.tick_params(axis='both', colors='#9ca3af', labelsize=11)
    
    if title:
        ax.set_title(title, color='#F1F1F1', fontsize=14, fontweight='bold', pad=20)
        
    plt.tight_layout()
    return plt


