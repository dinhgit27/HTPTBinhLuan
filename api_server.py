from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
from transformers import pipeline
import platform
import warnings
from platform_scrapers import get_comments, detect_platform

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

@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint kiểm tra trạng thái máy chủ (Health Check)"""
    return jsonify({
        "status": "online",
        "system": platform.system(),
        "api_ready": True,
        "message": "Phân tán API Server đa nền tảng đang hoạt động tốt!"
    }), 200

@app.route('/api/analyze', methods=['POST', 'GET'])
def analyze():
    """Endpoint nhận URL và tiến hành phân tích cảm xúc đa nền tảng"""
    data_input = request.get_json() if request.is_json else request.values
    
    url = data_input.get("url")
    if not url:
        return jsonify({"success": False, "error": "Vui lòng cung cấp tham số 'url'!"}), 400
        
    lang = data_input.get("lang", "vi")
    max_comments = int(data_input.get("max_comments", 200))
    
    # Thiết lập pipeline phân tích
    model_name = "wonrax/phobert-base-vietnamese-sentiment" if lang == "vi" else "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    
    try:
        # 1. Thu thập dữ liệu qua platform_scrapers (Tự động nhận diện nền tảng)
        all_comments, detected_platform, using_offline = get_comments(url, max_comments, API_KEY)
        
        if not all_comments:
            return jsonify({"success": False, "error": "Không tìm thấy bình luận nào cho liên kết này!"}), 404
            
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
        
        # Đề xuất dựa theo nền tảng
        if detected_platform == "shopee":
            rec_pos = "Nên mua"
            rec_mid = "Cân nhắc kỹ"
            rec_neg = "Không nên mua"
        else:
            rec_pos = "Nên đề xuất"
            rec_mid = "Cân nhắc"
            rec_neg = "Không đề xuất"

        if star_rating >= 4.0:
            summary = f"RẤT TÍCH CỰC ({pos_pct}% tích cực)"
            recommendation = rec_pos
        elif star_rating >= 3.0:
            summary = f"KHÁ TÍCH CỰC ({pos_pct}% tích cực)"
            recommendation = rec_mid
        elif star_rating >= 2.0:
            summary = f"TRUNG BÌNH ({pos_pct}% tích cực)"
            recommendation = "Cần xem xét"
        else:
            summary = f"TIÊU CỰC ({pos_pct}% tích cực)"
            recommendation = rec_neg
            
        return jsonify({
            "success": True,
            "platform": detected_platform,
            "offline_mode": using_offline,
            "overall": {
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
    # Chạy trên cổng 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
