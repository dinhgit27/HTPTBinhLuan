import pandas as pd
import re
import sys
import io
import os
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import joblib

# Cấu hình UTF-8 cho console để in tiếng Việt và emoji không bị lỗi trên Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 1. ĐỌC VÀ TỔNG HỢP DỮ LIỆU ĐA NỀN TẢNG
print("🚀 Đang khởi động huấn luyện AI đa nền tảng...")
platform_files = [
    'binh_luan_youtube.csv',
    'binh_luan_tiktok.csv',
    'binh_luan_shopee.csv',
    'binh_luan_facebook.csv'
]

dfs = []
for file in platform_files:
    if os.path.exists(file):
        print(f"📥 Đang nạp dữ liệu từ: {file}")
        dfs.append(pd.read_csv(file))
    else:
        print(f"⚠️ Không tìm thấy file: {file}")

if not dfs:
    print("❌ Lỗi: Không tìm thấy bất kỳ file dữ liệu nào để huấn luyện!")
    sys.exit(1)

# Gộp tất cả các DataFrame lại
df = pd.concat(dfs, ignore_index=True)
df = df.dropna(subset=['Nhan'])

def lam_sach_van_ban(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = word_tokenize(text, format="text")
    return text.strip()

print(f"\n🧹 Đang dọn dẹp {len(df)} dòng dữ liệu từ các nền tảng...")
df['BinhLuan_Sach'] = df['BinhLuan'].apply(lam_sach_van_ban)

# 2. HUẤN LUYỆN AI
print("🧠 Đang số hóa chữ viết (TF-IDF Vectorizer) và huấn luyện AI...")
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['BinhLuan_Sach'])
y = df['Nhan']

# Chia dữ liệu huấn luyện và kiểm thử (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = MultinomialNB()
model.fit(X_train, y_train)

# Đánh giá độ chính xác
y_pred = model.predict(X_test)
diem_so = accuracy_score(y_test, y_pred)
print(f"\n✅ Độ chính xác của AI đa nền tảng trên tập kiểm tra: {diem_so * 100:.2f}%")

# Lưu trữ mô hình huấn luyện
joblib.dump(model, 'mo_hinh_ai.pkl')
joblib.dump(vectorizer, 'bo_tu_dien.pkl')
print("💾 Đã lưu mô hình mới ('mo_hinh_ai.pkl') và bộ từ điển ('bo_tu_dien.pkl') thành công!")

# 3. CHẠY THỬ NGHIỆM AI VỚI CÁC NỀN TẢNG KHÁC NHAU
print("\n--- TEST AI ĐA NỀN TẢNG ---")
test_sentences = [
    ("nhạc này nghe buồn ngủ chán quá", "YouTube"),
    ("trend này nhảy cuốn xỉu up xỉu down luôn á", "TikTok"),
    ("giao hàng siêu nhanh đóng gói cực chắc chắn 5 sao", "Shopee"),
    ("bài viết chia sẻ thông tin rất hữu ích ad ơi", "Facebook"),
    ("lừa đảo nha mọi người hàng nhận về rách nát", "Shopee")
]

for cau, platform in test_sentences:
    cau_sach = [lam_sach_van_ban(cau)]
    cau_so = vectorizer.transform(cau_sach)
    xac_suat = model.predict_proba(cau_so)[0]
    diem = round(xac_suat[1] * 10, 1)
    nhan = 1 if diem >= 5.0 else 0
    
    print(f"[{platform}] Câu: '{cau}'")
    print(f"  👉 Điểm số AI đánh giá: {diem}/10.0")
    print(f"  👉 AI phân loại: {'Tích cực 😍' if nhan == 1 else 'Tiêu cực 😡'}")
    print(f"  👉 Đề xuất: {'Nên đề xuất ✅' if diem >= 7.0 else 'Không đề xuất ❌'}\n")