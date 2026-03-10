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
        # Dự đoán cảm xúc
        sach = [lam_sach(comment)]
        so = vectorizer.transform(sach)
        du_doan = int(model.predict(so)[0]) # 0 hoặc 1
        
        results.append({"comment": comment, "sentiment": du_doan})
    
    # In ra kết quả dạng JSON để C# đọc
    print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    # Nhận Video ID từ tham số dòng lệnh (C# gửi sang)
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        get_comments_and_predict(video_id)