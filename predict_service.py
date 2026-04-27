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

def get_comments_and_predict(video_id, max_total=1000):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    all_comments = []
    next_page_token = None
    
    while len(all_comments) < max_total:
        request = youtube.commentThreads().list(
            part="snippet", 
            videoId=video_id, 
            maxResults=100, 
            pageToken=next_page_token,
            textFormat="plainText"
        )
        response = request.execute()
        
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            all_comments.append(comment)
            if len(all_comments) >= max_total:
                break
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    results = []
    total_score = 0
    
    for comment in all_comments:
        sach = [lam_sach(comment)]
        so = vectorizer.transform(sach)
        
        # ------------------- ĐOẠN CẬP NHẬT -------------------
        xac_suat = model.predict_proba(so)[0]
        diem_so = round(xac_suat[1] * 10, 1)
        total_score += diem_so
        
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
    
    # Tính điểm tổng thể video
    avg_score = round(total_score / len(all_comments), 1) if all_comments else 0
    star_rating = round(avg_score / 2, 1)
    
    output = {
        "overall": {
            "average_score": avg_score,
            "star_rating": star_rating,
            "total_comments": len(all_comments)
        },
        "comments": results
    }
    
    # In ra kết quả dạng JSON
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    # Nhận Video ID từ tham số dòng lệnh (C# gửi sang)
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        get_comments_and_predict(video_id)