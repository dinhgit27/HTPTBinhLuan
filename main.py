import pandas as pd
import re
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import joblib # Đã thêm thư viện đóng gói

# 1. ĐỌC VÀ LÀM SẠCH DỮ LIỆU
df = pd.read_csv('binh_luan_youtube.csv')
df = df.dropna(subset=['Nhan'])

def lam_sach_van_ban(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = word_tokenize(text, format="text")
    return text.strip()

print("Đang dọn dẹp dữ liệu...")
df['BinhLuan_Sach'] = df['BinhLuan'].apply(lam_sach_van_ban)

# 2. HUẤN LUYỆN AI
print("Đang biến chữ thành số và dạy AI...\n")
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['BinhLuan_Sach'])
y = df['Nhan']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = MultinomialNB()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
diem_so = accuracy_score(y_test, y_pred)
print(f"✅ Độ chính xác của AI trên tập kiểm tra: {diem_so * 100:.2f}%\n")

# 3. TEST AI
cau_test = ["nhạc này nghe buồn ngủ chán quá"]
cau_test_sach = [lam_sach_van_ban(cau_test[0])]
cau_test_so = vectorizer.transform(cau_test_sach)

# ------------------- ĐOẠN CẬP NHẬT -------------------
xac_suat_test = model.predict_proba(cau_test_so)[0]
diem_test = round(xac_suat_test[1] * 10, 1)
nhan_test = 1 if diem_test >= 5.0 else 0

print("--- TEST AI ---")
print(f"Câu khách hàng viết: '{cau_test[0]}'")
print(f"Điểm số AI đánh giá: {diem_test}/10.0")
print("Đề xuất:", "Nên đề xuất ✅" if diem_test >= 7.0 else "Không đề xuất ❌")
print("AI phân loại:", "Tích cực 😍" if nhan_test == 1 else "Tiêu cực 😡")
# -----------------------------------------------------