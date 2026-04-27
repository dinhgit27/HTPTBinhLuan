import sys
import json
import joblib
import re
from googleapiclient.discovery import build
from underthesea import word_tokenize

# 1. CẤU HÌNH
API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"
model = joblib.load('mo_hinh_ai.pkl')
vectorizer = joblib.load('bo_tu_dien.pkl')

def lam_sach(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return word_tokenize(text, format="text")

def get_comments_and_predict(video_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=20, textFormat="plainText")
    response = request.execute()

    results = []
    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
        
        sach = [lam_sach(comment)]
        so = vectorizer.transform(sach)
        
        # ------------------- ĐOẠN CẬP NHẬT -------------------
        xac_suat = model.predict_proba(so)[0]
        diem_so = round(xac_suat[1] * 10, 1)
        
        label_text = "Tích cực" if diem_so >= 5.0 else "Tiêu cực"
        recommendation = True if diem_so >= 7.0 else False
        
        # Đóng gói JSON với đầy đủ tham số
        results.append({
            "comment": comment, 
            "sentiment": label_text,
            "score": diem_so,
            "is_recommended": recommendation
        })
        # -----------------------------------------------------
    
    # In ra kết quả dạng JSON
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    # Nhận Video ID từ tham số dòng lệnh (C# gửi sang)
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        get_comments_and_predict(video_id)