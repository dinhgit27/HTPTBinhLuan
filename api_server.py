from flask import Flask, request, jsonify
from flask_cors import CORS
from googleapiclient.discovery import build
import os
import pandas as pd
from transformers import pipeline
import platform
import warnings
import re
from collections import Counter
from underthesea import word_tokenize

# Tắt các cảnh báo không cần thiết
warnings.simplefilter('ignore', UserWarning)

app = Flask(__name__)
CORS(app)  # Cho phép gọi API từ C# hoặc n8n không bị lỗi CORS

# Cấu hình API Key và AI Models
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"
cached_models = {}

def get_ai_model(model_name):
    """Tải và lưu trữ mô hình trong bộ nhớ đệm (caching)"""
    if model_name not in cached_models:
        print(f"[API SERVER] Đang tải mô hình {model_name}...")
        cached_models[model_name] = pipeline("sentiment-analysis", model=model_name)
        print(f"[API SERVER] Mô hình {model_name} đã sẵn sàng!")
    return cached_models[model_name]

# Helper functions
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        return url.split("/")[-1].split("?")[0]

def get_all_comments(youtube, video_id, max_total=1000):
    all_comments = []
    next_page_token = None
    while len(all_comments) < max_total:
        request = youtube.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=100,
            pageToken=next_page_token, textFormat="plainText"
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
    return all_comments

@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint kiểm tra trạng thái máy chủ (Health Check)"""
    return jsonify({
        "status": "online",
        "system": platform.system(),
        "api_ready": True,
        "message": "Phân tán API Server đang hoạt động tốt!"
    }), 200

@app.route('/api/analyze', methods=['POST', 'GET'])
def analyze():
    """Endpoint nhận URL/Video ID và tiến hành phân tích cảm xúc và thống kê"""
    # Nhận tham số đầu vào từ JSON (POST) hoặc Query Parameters (GET)
    data_input = request.get_json() if request.is_json else request.values
    
    url = data_input.get("url")
    if not url:
        return jsonify({"success": False, "error": "Vui lòng cung cấp tham số 'url'!"}), 400
        
    lang = data_input.get("lang", "vi")  # 'vi' (PhoBERT) hoặc 'en' (DistilBERT)
    max_comments = int(data_input.get("max_comments", 200))
    
    # Thiết lập pipeline phân tích
    model_name = "wonrax/phobert-base-vietnamese-sentiment" if lang == "vi" else "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    
    try:
        video_id = extract_video_id(url)
        using_offline = False
        
        # 1. Thu thập dữ liệu (YouTube API có fallback offline)
        try:
            youtube = build('youtube', 'v3', developerKey=API_KEY)
            all_comments = get_all_comments(youtube, video_id, max_total=max_comments)
        except Exception:
            # Fallback sang offline
            if os.path.exists("binh_luan_youtube.csv"):
                offline_df = pd.read_csv("binh_luan_youtube.csv")
                col_candidates = ["BinhLuan", "Bình luận", offline_df.columns[0]]
                comment_col = next((c for c in col_candidates if c in offline_df.columns), None)
                if comment_col:
                    all_comments = offline_df[comment_col].dropna().tolist()[:max_comments]
                    using_offline = True
                else:
                    return jsonify({"success": False, "error": "API YouTube lỗi và dữ liệu offline không hợp lệ."}), 500
            else:
                return jsonify({"success": False, "error": "API YouTube lỗi và không có file lưu trữ offline dự phòng."}), 500
        
        if not all_comments:
            return jsonify({"success": False, "error": "Không tìm thấy bình luận nào!"}), 404
            
        # 2. Phân tích cảm xúc dùng AI Pipeline
        sentiment_analyzer = get_ai_model(model_name)
        total = len(all_comments)
        sentiment_counts = {"Tích cực": 0, "Tiêu cực": 0, "Trung tính": 0}
        total_score = 0
        details = []
        
        for comment in all_comments:
            try:
                short_text = comment[:200]
                result = sentiment_analyzer(short_text, truncation=True)[0]
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
                
            sentiment_counts[label] += 1
            total_score += score
            details.append({"comment": comment, "sentiment": label, "score": score})
            
        avg_score = round(total_score / total, 1)
        star_rating = round(avg_score / 2, 1)
        pos_pct = round((sentiment_counts["Tích cực"] / total) * 100, 1)
        
        if star_rating >= 4.0:
            summary = f"RẤT TÍCH CỰC ({pos_pct}% tích cực)"
            recommendation = "Nên đề xuất"
        elif star_rating >= 3.0:
            summary = f"KHÁ TÍCH CỰC ({pos_pct}% tích cực)"
            recommendation = "Cân nhắc"
        elif star_rating >= 2.0:
            summary = f"TRUNG BÌNH ({pos_pct}% tích cực)"
            recommendation = "Cần xem xét"
        else:
            summary = f"TIÊU CỰC ({pos_pct}% tích cực)"
            recommendation = "Không đề xuất"
            
        # Trả về kết quả JSON chuẩn hóa
        return jsonify({
            "success": True,
            "offline_mode": using_offline,
            "overall": {
                "video_id": video_id,
                "url": url,
                "total_comments": total,
                "average_score": avg_score,
                "star_rating": star_rating,
                "summary": summary,
                "recommendation": recommendation
            },
            "sentiment_distribution": {
                "positive": sentiment_counts["Tích cực"],
                "negative": sentiment_counts["Tiêu cực"],
                "neutral": sentiment_counts["Trung tính"]
            },
            "comments_sample": details[:10]  # Gửi mẫu 10 bình luận kèm điểm số chi tiết
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Chạy trên cổng 5000 (Cổng phân tán tiêu chuẩn)
    app.run(host='0.0.0.0', port=5000, debug=True)
