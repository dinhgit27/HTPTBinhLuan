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

# Tiền xử lý văn bản
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[\W_]+', ' ', text)
    return text

def extract_cjk_tokens(text):
    """Trích xuất các từ/cụm từ Tiếng Trung, Tiếng Nhật, Tiếng Hàn (CJK) từ văn bản"""
    tokens = []
    # Khối Unicode CJK (Trung/Nhật/Hàn) bao gồm Kanji, Hiragana, Katakana, Hangul
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+')
    cjk_blocks = cjk_pattern.findall(text)
    
    # Danh sách các từ dừng (stopwords) phổ biến của CJK
    cjk_stopwords = set([
        # Tiếng Trung (Giản thể + Phồn thể)
        '的', '了', '我', '你', '他', '她', '它', '们', '这', '那', '是', '在', '不', '也', '有', '之', '和', '与', '被', '让',
        '很', '太', '都', '就', '去', '来', '到', '上', '下', '里', '个', '着', '过', '得', '而', '及', '以', '但', '吗', '呢',
        # Tiếng Nhật (Trợ từ)
        'の', 'に', 'は', 'を', 'た', 'が', 'と', 'も', 'で', 'す', 'だ', 'て', 'いる', 'する', 'から', 'まで', 'など', 'たい',
        # Tiếng Hàn (Trợ từ)
        '이', '그', '저', '은', '는', '을', '를', '에', '에서', '로', '으로', '과', '와', '도', '만', '의', '에'
    ])
    
    for block in cjk_blocks:
        n = len(block)
        if n == 1:
            if block not in cjk_stopwords:
                tokens.append(block)
        elif n == 2:
            if block not in cjk_stopwords:
                tokens.append(block)
        else:
            # Chiết xuất 2-gram (Từ ghép 2 ký tự - phổ biến nhất trong CJK)
            for i in range(n - 1):
                bigram = block[i:i+2]
                if bigram[0] not in cjk_stopwords and bigram[1] not in cjk_stopwords:
                    tokens.append(bigram)
            # Chiết xuất 3-gram (Cụm từ 3 ký tự)
            for i in range(n - 2):
                trigram = block[i:i+3]
                tokens.append(trigram)
            # Chiết xuất các ký tự đơn lẻ (chỉ lấy những từ không phải hạt từ trợ từ)
            for i in range(n):
                unigram = block[i]
                if unigram not in cjk_stopwords:
                    tokens.append(unigram)
    return tokens

def extract_keywords(comments, top_k=50, language='vi'):
    # comments: List[str]
    cleaned = [clean_text(c) for c in comments]
    tokens = []
    
    if language == 'vi':
        for c in cleaned:
            # Tách từ tiếng Việt
            tokens += word_tokenize(c, format="text").split()
            # Trích xuất thêm từ CJK nếu có lẫn trong bình luận
            tokens += extract_cjk_tokens(c)
        stopwords = set(['và', 'là', 'của', 'có', 'cho', 'với', 'rất', 'quá', 'nhưng', 'thì', 'một', 'này', 'đã', 'còn', 'nên', 'được', 'cũng', 'đang', 'khi', 'vì', 'để', 'nhiều', 'ít', 'nữa', 'nào', 'sẽ', 'bị', 'tới', 'tôi', 'bạn', 'anh', 'chị', 'em', 'chúng', 'ta', 'họ', 'ai', 'gì', 'đó', 'ở', 'trong', 'ra', 'vào', 'lên', 'xuống', 'về', 'từ', 'sao', 'đi', 'đến', 'các', 'những', 'này', 'kia', 'ấy', 'vậy', 'thế', 'nhiều', 'ít', 'rồi', 'luôn', 'nhé', 'nha', 'ơi', 'ạ', 'ha', 'à', 'nhỉ'])
    else:  # English & other languages (bao gồm cả CJK)
        for c in cleaned:
            # Tách từ hệ chữ Latin (Anh, Pháp, Đức...)
            tokens += re.findall(r'\b\w{2,}\b', c)
            # Tách từ hệ chữ tượng hình CJK (Trung, Nhật, Hàn)
            tokens += extract_cjk_tokens(c)
        stopwords = set(['the', 'and', 'a', 'of', 'to', 'is', 'in', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word', 'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said', 'there', 'use', 'an', 'each', 'which', 'she', 'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'him', 'into', 'time', 'has', 'look', 'two', 'more', 'write', 'go', 'see', 'no', 'way', 'could', 'people', 'my', 'than', 'first', 'water', 'been', 'call', 'who', 'oil', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part', 'very', 'really', 'good', 'bad', 'so', 'great', 'awesome', 'nice', 'video', 'youtube', 'comment'])
        
    tokens = [t for t in tokens if t not in stopwords and len(t) > 1]
    counter = Counter(tokens)
    return counter.most_common(top_k)

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
        "C:\\Windows\\Fonts\\msyh.ttc",  # Microsoft YaHei (CJK)
        "C:\\Windows\\Fonts\\simhei.ttf",   # SimHei (Chinese)
    ]
    for path in windows_fonts:
        if os.path.exists(path):
            return path
    # Fallback via matplotlib
    try:
        import matplotlib.font_manager as fm
        fallback = fm.findfont(fm.FontProperties(family="sans-serif"))
        if os.path.exists(fallback):
            return fallback
    except Exception:
        pass
    return None

def plot_wordcloud(keywords, title=None):
    font_path = get_vietnamese_font_path()
    font_prop = fm.FontProperties(fname=font_path)
    
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
        ax.set_title(title, fontproperties=font_prop, color='#F1F1F1', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    return plt

def plot_keyword_bar_chart(keywords, title=None, top_n=15):
    """
    Vẽ biểu đồ cột ngang liệt kê các từ khóa hàng đầu một cách dễ đọc, hiện đại.
    """
    font_path = get_vietnamese_font_path()
    font_prop = fm.FontProperties(fname=font_path)
    
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


