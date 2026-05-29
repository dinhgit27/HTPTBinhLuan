import sys
import json
import joblib
import re
import io
from underthesea import word_tokenize
from platform_scrapers import get_comments

# Cấu hình UTF-8 cho console để giao tiếp với C# chuẩn xác
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 1. CẤU HÌNH
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"
model = joblib.load('mo_hinh_ai.pkl')
vectorizer = joblib.load('bo_tu_dien.pkl')

def lam_sach(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return word_tokenize(text, format="text")

def get_comments_and_predict(url, max_total=1000):
    # Lấy dữ liệu đa nền tảng
    all_comments, platform, is_offline = get_comments(url, max_total, API_KEY)
    
    results = []
    total_score = 0
    
    for comment in all_comments:
        sach = [lam_sach(comment)]
        so = vectorizer.transform(sach)
        
        # Dự đoán bằng mô hình Naive Bayes đa nền tảng
        xac_suat = model.predict_proba(so)[0]
        diem_so = round(xac_suat[1] * 10, 1)
        total_score += diem_so
        
        label_text = "Tích cực" if diem_so >= 5.0 else "Tiêu cực"
        recommendation = True if diem_so >= 7.0 else False
        
        results.append({
            "comment": comment, 
            "sentiment": label_text,
            "score": diem_so,
            "is_recommended": recommendation
        })
    
    avg_score = round(total_score / len(all_comments), 1) if all_comments else 0
    star_rating = round(avg_score / 2, 1)
    
    output = {
        "platform": platform,
        "is_offline_mode": is_offline,
        "overall": {
            "average_score": avg_score,
            "star_rating": star_rating,
            "total_comments": len(all_comments)
        },
        "comments": results
    }
    
    # In ra kết quả dạng JSON để C# đọc
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    # Nhận URL từ tham số dòng lệnh (C# gửi sang)
    if len(sys.argv) > 1:
        url_input = sys.argv[1]
        get_comments_and_predict(url_input)
    else:
        # Test demo
        get_comments_and_predict("https://www.tiktok.com/@vt/video/12345", 50)