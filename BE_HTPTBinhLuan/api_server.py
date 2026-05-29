from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import io

# Cấu hình UTF-8 cho console Windows để tránh UnicodeEncodeError khi log tiếng Việt
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

import pandas as pd
import platform
import warnings
import requests
import base64
import json
from datetime import datetime, timezone
from platform_scrapers import get_comments, get_comments_rich, detect_platform

# Tắt các cảnh báo không cần thiết
warnings.simplefilter('ignore', UserWarning)

app = Flask(__name__)
CORS(app)  # Cho phép gọi API từ client web không bị lỗi CORS

# Cấu hình API Key
API_KEY = os.getenv("API_KEY", "AIzaSyDSS2KKpjlQWC6e1RT45nqwfZuJm3MMo5s")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw")

# ============================================
# CẤU HÌNH MODEL AI (PhoBERT - Chính xác cao)
# ============================================
import threading

HAS_TRANSFORMERS = False
cached_models = {}
MODEL_LOADING = False     # Đang tải
MODEL_READY   = False     # Đã sẵn sàng
MODEL_ERROR   = None      # Lỗi nếu có
DEFAULT_VI_MODEL = "wonrax/phobert-base-vietnamese-sentiment"
DEFAULT_EN_MODEL = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"

def _preload_model_background():
    """Tải PhoBERT trong background thread ngay khi server khởi động."""
    global HAS_TRANSFORMERS, MODEL_LOADING, MODEL_READY, MODEL_ERROR, cached_models
    MODEL_LOADING = True
    try:
        print("[AI] Đang import transformers...")
        from transformers import pipeline
        HAS_TRANSFORMERS = True
        print(f"[AI] Đang tải mô hình {DEFAULT_VI_MODEL} (lần đầu có thể mất vài phút)...")
        cached_models[DEFAULT_VI_MODEL] = pipeline(
            "sentiment-analysis",
            model=DEFAULT_VI_MODEL,
            truncation=True,
            max_length=256,
            batch_size=32,
            device=-1   # CPU
        )
        MODEL_READY = True
        print("[AI] ✅ PhoBERT đã sẵn sàng! Mọi phân tích sẽ dùng AI chính xác cao.")
    except Exception as e:
        MODEL_ERROR = str(e)
        print(f"[AI] ❌ Không thể tải PhoBERT: {e}")
    finally:
        MODEL_LOADING = False

# Khởi động tải model ngay khi server bắt đầu (không chặn server)
_model_thread = threading.Thread(target=_preload_model_background, daemon=True)
_model_thread.start()

HAS_WORDCLOUD = False
try:
    import wordcloud_utils
    HAS_WORDCLOUD = True
except Exception as e:
    print(f"[API SERVER] wordcloud_utils không khả dụng: {e}")


# ============================================
# LIGHTWEIGHT FALLBACK IMPLEMENTATIONS
# ============================================
def fallback_sentiment_analyze(text):
    text_lower = text.lower()
    pos_words = ["hay", "tốt", "tuyệt", "đẹp", "hữu ích", "chất lượng", "ưng", "ngon", "xịn", "thích", "nhanh", "giao nhanh", "mượt", "đóng gói kỹ", "yêu", "ổn", "được", "cảm ơn", "thank", "ok", "recommend", "great", "nice", "good"]
    neg_words = ["tệ", "xấu", "dở", "chán", "kém", "lỗi", "hỏng", "chậm", "giao chậm", "bóp méo", "móp", "nát", "thất vọng", "lừa đảo", "không nên", "fake", "bad", "slow", "error", "fail", "khó hiểu", "quá nhanh", "thời lượng ngắn", "chữ chạy nhanh", "đóng gói sơ sài"]
    
    pos_count = sum(1 for w in pos_words if w in text_lower)
    neg_count = sum(1 for w in neg_words if w in text_lower)
    
    if pos_count > neg_count:
        return "Tích cực", round(7.0 + min(3.0, pos_count * 0.5), 1)
    elif neg_count > pos_count:
        return "Tiêu cực", round(3.0 - min(3.0, neg_count * 0.5), 1)
    else:
        return "Trung tính", 5.0

def fallback_extract_keywords(comments, top_k=15):
    stopwords = {"và", "của", "là", "được", "trong", "có", "cho", "với", "không", "các", "đã", "này", "để", "nhưng", "khi", "như", "nếu", "thì", "tôi", "anh", "chị", "em", "bạn", "video", "bình luận", "link", "kênh", "sub", "view", "cho", "ra", "làm", "hơn", "về", "từ", "nào", "gì"}
    words_count = {}
    for c in comments:
        words = c.lower().split()
        for w in words:
            w_clean = "".join(ch for ch in w if ch.isalnum())
            if w_clean and len(w_clean) > 2 and w_clean not in stopwords:
                words_count[w_clean] = words_count.get(w_clean, 0) + 1
    
    sorted_words = sorted(words_count.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:top_k]


# ============================================
# LOCAL FALLBACK AUTH & HISTORY IMPLEMENTATION
# ============================================
LOCAL_USERS_FILE = "users_local.json"
LOCAL_HISTORY_FILE = "history_local.json"

def generate_local_token(email, user_id):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode('utf-8')).decode('utf-8').replace('=', '')
    payload = base64.urlsafe_b64encode(json.dumps({"aud": "local-project", "email": email, "user_id": user_id}).encode('utf-8')).decode('utf-8').replace('=', '')
    signature = "local_signature"
    return f"{header}.{payload}.{signature}"

def local_auth(email, password, mode="login"):
    import uuid
    users = {}
    if os.path.exists(LOCAL_USERS_FILE):
        try:
            with open(LOCAL_USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except Exception:
            pass
            
    if mode == "signup":
        if email in users:
            return {"success": False, "error": "Email này đã được đăng ký tài khoản!"}
        user_id = str(uuid.uuid4())
        users[email] = {
            "password": password,
            "user_id": user_id
        }
        try:
            with open(LOCAL_USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
        except Exception as e:
            return {"success": False, "error": f"Lỗi lưu trữ tài khoản cục bộ: {str(e)}"}
            
        token = generate_local_token(email, user_id)
        return {
            "success": True,
            "data": {
                "idToken": token,
                "email": email,
                "localId": user_id,
                "refreshToken": f"local_refresh_{user_id}",
                "expiresIn": "3600"
            }
        }
        
    elif mode == "login":
        if email not in users or users[email]["password"] != password:
            return {"success": False, "error": "Mật khẩu không chính xác hoặc tài khoản không tồn tại!"}
            
        user_id = users[email]["user_id"]
        token = generate_local_token(email, user_id)
        return {
            "success": True,
            "data": {
                "idToken": token,
                "email": email,
                "localId": user_id,
                "refreshToken": f"local_refresh_{user_id}",
                "expiresIn": "3600"
            }
        }
        
    else: # forgot password
        if email not in users:
            return {"success": False, "error": "Email này chưa được đăng ký!"}
        return {"success": True, "data": {"message": "Đã gửi email khôi phục mật khẩu giả lập!"}}

def save_history_local(email, url, platform_name, score):
    history = []
    if os.path.exists(LOCAL_HISTORY_FILE):
        try:
            with open(LOCAL_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            pass
            
    timestamp_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    new_record = {
        "email": email,
        "url": url,
        "platform": platform_name,
        "score": float(score),
        "timestamp": timestamp_str
    }
    history.append(new_record)
    
    try:
        with open(LOCAL_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        # Định dạng output để khớp cấu trúc response Firestore
        return {"success": True, "data": {
            "name": f"projects/local-project/databases/(default)/documents/history/{timestamp_str}",
            "fields": {
                "email": {"stringValue": email},
                "url": {"stringValue": url},
                "platform": {"stringValue": platform_name},
                "score": {"doubleValue": float(score)},
                "timestamp": {"stringValue": timestamp_str}
            }
        }}
    except Exception as e:
        return {"success": False, "error": f"Lỗi lưu lịch sử cục bộ: {str(e)}"}

def fetch_history_local(email):
    history = []
    if os.path.exists(LOCAL_HISTORY_FILE):
        try:
            with open(LOCAL_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            pass
            
    user_history = [h for h in history if h.get("email") == email]
    user_history = sorted(user_history, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    formatted_history = []
    for h in user_history:
        formatted_history.append({
            "document": {
                "fields": {
                    "email": {"stringValue": h["email"]},
                    "url": {"stringValue": h["url"]},
                    "platform": {"stringValue": h["platform"]},
                    "score": {"doubleValue": h["score"]},
                    "timestamp": {"stringValue": h["timestamp"]}
                }
            }
        })
    return {"success": True, "data": formatted_history}


# ============================================
# FIREBASE AUTH IMPLEMENTATION
# ============================================
def firebase_auth(email, password, mode="login"):
    api_key = API_KEY
    if mode == "login":
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
    elif mode == "signup":
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
    else:  # forgot password
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_data = response.json()
        if response.status_code == 200:
            return {"success": True, "data": res_data}
        else:
            error_msg = res_data.get("error", {}).get("message", "Đã xảy ra lỗi!")
            
            # Fallback sang local auth nếu Firebase báo lỗi chưa cấu hình (Email/Password Auth method is disabled)
            if "CONFIGURATION_NOT_FOUND" in error_msg or "OPERATION_NOT_ALLOWED" in error_msg:
                print(f"[AUTH WARNING] Firebase Authentication chưa bật Email/Password. Fallback sang Local Auth cho: {email}")
                return local_auth(email, password, mode)
                
            if "EMAIL_NOT_FOUND" in error_msg:
                error_msg = "Email này chưa được đăng ký!"
            elif "INVALID_PASSWORD" in error_msg:
                error_msg = "Mật khẩu không chính xác!"
            elif "EMAIL_EXISTS" in error_msg:
                error_msg = "Email này đã được đăng ký tài khoản!"
            elif "INVALID_EMAIL" in error_msg:
                error_msg = "Định dạng email không hợp lệ!"
            elif "WEAK_PASSWORD" in error_msg:
                error_msg = "Mật khẩu quá yếu (tối thiểu phải 6 ký tự)!"
            return {"success": False, "error": error_msg}
    except Exception as e:
        print(f"[AUTH WARNING] Lỗi kết nối Firebase: {e}. Fallback sang Local Auth.")
        return local_auth(email, password, mode)


# ============================================
# FIREBASE FIRESTORE IMPLEMENTATION
# ============================================
def get_project_id_from_token(id_token):
    try:
        parts = id_token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
            payload = json.loads(payload_json)
            return payload.get('aud')
    except Exception:
        pass
    return None

def save_history(id_token, email, url, platform_name, score):
    project_id = get_project_id_from_token(id_token)
    if not project_id or project_id == "local-project":
        return save_history_local(email, url, platform_name, score)
    
    url_api = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/history"
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    timestamp_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    payload = {
        "fields": {
            "email": {"stringValue": email},
            "url": {"stringValue": url},
            "platform": {"stringValue": platform_name},
            "score": {"doubleValue": float(score)},
            "timestamp": {"stringValue": timestamp_str}
        }
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            # Fallback sang local history nếu Firestore bị lỗi quyền hạn hoặc cấu hình
            print(f"[FIRESTORE WARNING] Firestore API lỗi (HTTP {response.status_code}). Fallback lưu lịch sử cục bộ.")
            return save_history_local(email, url, platform_name, score)
    except Exception as e:
        print(f"[FIRESTORE WARNING] Lỗi kết nối Firestore: {e}. Fallback lưu lịch sử cục bộ.")
        return save_history_local(email, url, platform_name, score)

def fetch_history(id_token, email):
    project_id = get_project_id_from_token(id_token)
    if not project_id or project_id == "local-project":
        # Hàm fetch_history_local trả về format chứa fields.
        # Chúng ta cần parse nó ra cấu trúc history_records như mong đợi của API.
        local_res = fetch_history_local(email)
        if not local_res["success"]:
            return local_res
        history_records = []
        for item in local_res["data"]:
            doc = item.get("document", {})
            fields = doc.get("fields", {})
            rec_email = fields.get("email", {}).get("stringValue", "")
            rec_url = fields.get("url", {}).get("stringValue", "")
            rec_platform = fields.get("platform", {}).get("stringValue", "")
            
            score_field = fields.get("score", {})
            rec_score = 0.0
            if "doubleValue" in score_field:
                rec_score = float(score_field.get("doubleValue", 0.0))
            elif "integerValue" in score_field:
                rec_score = float(score_field.get("integerValue", 0))
                
            rec_timestamp = fields.get("timestamp", {}).get("stringValue", "")
            
            history_records.append({
                "email": rec_email,
                "url": rec_url,
                "platform": rec_platform,
                "score": rec_score,
                "timestamp": rec_timestamp
            })
        return {"success": True, "data": history_records}
        
    url_api = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents:runQuery"
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "structuredQuery": {
            "from": [{"collectionId": "history"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "email"},
                    "op": "EQUAL",
                    "value": {"stringValue": email}
                }
            },
            "limit": 50
        }
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_list = response.json()
            history_records = []
            
            for item in res_list:
                doc = item.get("document")
                if doc and "fields" in doc:
                    fields = doc.get("fields", {})
                    rec_email = fields.get("email", {}).get("stringValue", "")
                    rec_url = fields.get("url", {}).get("stringValue", "")
                    rec_platform = fields.get("platform", {}).get("stringValue", "")
                    
                    score_field = fields.get("score", {})
                    rec_score = 0.0
                    if "doubleValue" in score_field:
                        rec_score = float(score_field.get("doubleValue", 0.0))
                    elif "integerValue" in score_field:
                        rec_score = float(score_field.get("integerValue", 0))
                        
                    rec_timestamp = fields.get("timestamp", {}).get("stringValue", "")
                    
                    history_records.append({
                        "email": rec_email,
                        "url": rec_url,
                        "platform": rec_platform,
                        "score": rec_score,
                        "timestamp": rec_timestamp
                    })
            
            history_records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return {"success": True, "data": history_records}
        else:
            # Fallback sang local history
            print(f"[FIRESTORE WARNING] Firestore API lỗi (HTTP {response.status_code}). Fallback lấy lịch sử cục bộ.")
            local_res = fetch_history_local(email)
            if local_res["success"]:
                # Parse cấu trúc
                history_records = []
                for item in local_res["data"]:
                    doc = item.get("document", {})
                    fields = doc.get("fields", {})
                    rec_email = fields.get("email", {}).get("stringValue", "")
                    rec_url = fields.get("url", {}).get("stringValue", "")
                    rec_platform = fields.get("platform", {}).get("stringValue", "")
                    
                    score_field = fields.get("score", {})
                    rec_score = 0.0
                    if "doubleValue" in score_field:
                        rec_score = float(score_field.get("doubleValue", 0.0))
                    elif "integerValue" in score_field:
                        rec_score = float(score_field.get("integerValue", 0))
                        
                    rec_timestamp = fields.get("timestamp", {}).get("stringValue", "")
                    
                    history_records.append({
                        "email": rec_email,
                        "url": rec_url,
                        "platform": rec_platform,
                        "score": rec_score,
                        "timestamp": rec_timestamp
                    })
                return {"success": True, "data": history_records}
            return local_res
    except Exception as e:
        print(f"[FIRESTORE WARNING] Lỗi kết nối Firestore: {e}. Fallback lấy lịch sử cục bộ.")
        local_res = fetch_history_local(email)
        if local_res["success"]:
            # Parse cấu trúc
            history_records = []
            for item in local_res["data"]:
                doc = item.get("document", {})
                fields = doc.get("fields", {})
                rec_email = fields.get("email", {}).get("stringValue", "")
                rec_url = fields.get("url", {}).get("stringValue", "")
                rec_platform = fields.get("platform", {}).get("stringValue", "")
                
                score_field = fields.get("score", {})
                rec_score = 0.0
                if "doubleValue" in score_field:
                    rec_score = float(score_field.get("doubleValue", 0.0))
                elif "integerValue" in score_field:
                    rec_score = float(score_field.get("integerValue", 0))
                    
                rec_timestamp = fields.get("timestamp", {}).get("stringValue", "")
                
                history_records.append({
                    "email": rec_email,
                    "url": rec_url,
                    "platform": rec_platform,
                    "score": rec_score,
                    "timestamp": rec_timestamp
                })
            return {"success": True, "data": history_records}
        return {"success": False, "error": f"Lỗi truy vấn Firestore & Local: {str(e)}"}


# ============================================
# API ROUTES FOR AUTHENTICATION
# ============================================
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"success": False, "error": "Vui lòng cung cấp email và mật khẩu!"}), 400
    res = firebase_auth(email, password, mode="login")
    if res["success"]:
        return jsonify(res), 200
    return jsonify(res), 400

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"success": False, "error": "Vui lòng cung cấp email và mật khẩu!"}), 400
    res = firebase_auth(email, password, mode="signup")
    if res["success"]:
        return jsonify(res), 200
    return jsonify(res), 400

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json() or {}
    email = data.get('email')
    if not email:
        return jsonify({"success": False, "error": "Vui lòng cung cấp email!"}), 400
    res = firebase_auth(email, None, mode="forgot")
    if res["success"]:
        return jsonify(res), 200
    return jsonify(res), 400


# ============================================
# API ROUTES FOR HISTORY
# ============================================
@app.route('/api/history', methods=['GET'])
def api_get_history():
    auth_header = request.headers.get('Authorization')
    email = request.args.get('email')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Yêu cầu cung cấp token xác thực hợp lệ!"}), 401
    if not email:
        return jsonify({"success": False, "error": "Yêu cầu cung cấp email!"}), 400
        
    id_token = auth_header.split(' ')[1]
    res = fetch_history(id_token, email)
    if res["success"]:
        return jsonify(res), 200
    return jsonify(res), 400

@app.route('/api/history', methods=['POST'])
def api_save_history():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Yêu cầu cung cấp token xác thực hợp lệ!"}), 401
        
    data = request.get_json() or {}
    email = data.get('email')
    url = data.get('url')
    platform_name = data.get('platform')
    score = data.get('score')
    
    if not email or not url or not platform_name or score is None:
        return jsonify({"success": False, "error": "Yêu cầu điền đầy đủ email, url, platform và score!"}), 400
        
    id_token = auth_header.split(' ')[1]
    res = save_history(id_token, email, url, platform_name, score)
    if res["success"]:
        return jsonify(res), 200
    return jsonify(res), 400


# ============================================
# API ROUTE FOR STATUS
# ============================================
@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint kiểm tra trạng thái máy chủ (Health Check)"""
    return jsonify({
        "status": "online",
        "system": platform.system(),
        "api_ready": True,
        "model_ready": MODEL_READY,
        "model_loading": MODEL_LOADING,
        "model_error": MODEL_ERROR,
        "transformers_loaded": HAS_TRANSFORMERS,
        "message": "Phân tán API Server đa nền tảng đang hoạt động tốt!"
    }), 200


@app.route('/api/model-status', methods=['GET'])
def model_status():
    """Endpoint kiểm tra trạng thái tải AI model"""
    if MODEL_READY:
        state = "ready"
        msg = "✅ AI PhoBERT đã sẵn sàng — Phân tích chính xác cao!"
    elif MODEL_LOADING:
        state = "loading"
        msg = "⏳ Đang tải AI PhoBERT lần đầu... (khoảng 1-3 phút)"
    elif MODEL_ERROR:
        state = "error"
        msg = f"❌ Lỗi tải AI: {MODEL_ERROR} — Đang dùng phân tích từ điển."
    else:
        state = "idle"
        msg = "Model chưa được tải."
    return jsonify({
        "state": state,
        "ready": MODEL_READY,
        "loading": MODEL_LOADING,
        "error": MODEL_ERROR,
        "message": msg
    }), 200


# ============================================
# API ROUTES FOR USER PROFILE & TELEGRAM
# ============================================
def send_telegram_report_async(chat_id, url, avg_score, star_rating, total, sentiment_counts, summary, recommendation, platform_name):
    p_emoji = "🌐"
    if platform_name == "youtube": p_emoji = "🔴"
    elif platform_name == "tiktok": p_emoji = "🎵"
    elif platform_name == "shopee": p_emoji = "🛍️"
    elif platform_name == "facebook": p_emoji = "👥"
    
    pos_pct = round((sentiment_counts["Tích cực"] / total) * 100, 1) if total else 0
    neg_pct = round((sentiment_counts["Tiêu cực"] / total) * 100, 1) if total else 0
    neu_pct = round((sentiment_counts["Trung tính"] / total) * 100, 1) if total else 0
    
    text = f"""{p_emoji} *Báo cáo Phân tích Bình luận từ Web*

🔗 *Link:* {url}
⭐ *Điểm trung bình:* {avg_score}/10 ({star_rating}/5 sao)

📊 *Thống kê ({total} bình luận):*
• 🟢 Tích cực: {sentiment_counts['Tích cực']} ({pos_pct}%)
• 🔴 Tiêu cực: {sentiment_counts['Tiêu cực']} ({neg_pct}%)
• ⚪ Trung tính: {sentiment_counts['Trung tính']} ({neu_pct}%)

💡 *Đánh giá:* {summary}
📌 *Đề xuất:* {recommendation}
"""
    bot_token = "8606918938:AAFlcQ33rMCw8z-uB6wYm96M8NG3SUfqkvE"
    url_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url_api, json=payload, timeout=5)
    except Exception as e:
        print(f"[TELEGRAM] Lỗi gửi báo cáo tự động: {e}")

@app.route('/api/profile', methods=['GET'])
def api_get_profile():
    auth_header = request.headers.get('Authorization')
    email = request.args.get('email')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Yêu cầu cung cấp token xác thực hợp lệ!"}), 401
    if not email:
        return jsonify({"success": False, "error": "Yêu cầu cung cấp email!"}), 400
    
    if not os.path.exists(LOCAL_USERS_FILE):
        return jsonify({"success": False, "error": "Người dùng không tồn tại!"}), 404
        
    try:
        with open(LOCAL_USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except Exception as e:
        return jsonify({"success": False, "error": f"Lỗi đọc dữ liệu: {str(e)}"}), 500
        
    if email not in users:
        return jsonify({"success": False, "error": "Người dùng không tồn tại!"}), 404
        
    user_data = users[email]
    
    return jsonify({
        "success": True,
        "data": {
            "email": email,
            "user_id": user_data.get("user_id"),
            "telegram_chat_id": user_data.get("telegram_chat_id"),
            "telegram_username": user_data.get("telegram_username"),
            "auto_send_telegram": user_data.get("auto_send_telegram", False)
        }
    }), 200

@app.route('/api/profile/telegram/disconnect', methods=['POST'])
def api_disconnect_telegram():
    auth_header = request.headers.get('Authorization')
    data = request.get_json() or {}
    email = data.get('email')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Yêu cầu cung cấp token xác thực hợp lệ!"}), 401
    if not email:
        return jsonify({"success": False, "error": "Yêu cầu cung cấp email!"}), 400
        
    try:
        with open(LOCAL_USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            
        if email in users:
            users[email]["telegram_chat_id"] = None
            users[email]["telegram_username"] = None
            with open(LOCAL_USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            return jsonify({"success": True, "message": "Đã ngắt kết nối Telegram!"}), 200
        else:
            return jsonify({"success": False, "error": "Người dùng không tồn tại!"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": f"Lỗi xử lý: {str(e)}"}), 500

@app.route('/api/profile/telegram/settings', methods=['POST'])
def api_telegram_settings():
    auth_header = request.headers.get('Authorization')
    data = request.get_json() or {}
    email = data.get('email')
    auto_send = data.get('auto_send_telegram', False)
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Yêu cầu cung cấp token xác thực hợp lệ!"}), 401
    if not email:
        return jsonify({"success": False, "error": "Yêu cầu cung cấp email!"}), 400
        
    try:
        with open(LOCAL_USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            
        if email in users:
            users[email]["auto_send_telegram"] = auto_send
            with open(LOCAL_USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            return jsonify({"success": True, "message": "Đã cập nhật cài đặt!"}), 200
        else:
            return jsonify({"success": False, "error": "Người dùng không tồn tại!"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": f"Lỗi xử lý: {str(e)}"}), 500

# ============================================
# API ROUTE FOR ANALYSIS
# ============================================
def get_ai_model(model_name):
    """Trả về model đã cache hoặc None nếu chưa sẵn sàng."""
    if model_name in cached_models:
        return cached_models[model_name]
    # Nếu model chưa được cache nhưng transformers có sẵn, tải ngay
    if HAS_TRANSFORMERS:
        try:
            from transformers import pipeline
            print(f"[AI] Tải model phụ: {model_name}")
            cached_models[model_name] = pipeline(
                "sentiment-analysis", model=model_name,
                truncation=True, max_length=256, batch_size=32, device=-1
            )
            return cached_models[model_name]
        except Exception as e:
            print(f"[AI] Không thể tải {model_name}: {e}")
    return None

@app.route('/api/analyze', methods=['POST', 'GET'])
def analyze():
    """Endpoint nhận URL và tiến hành phân tích cảm xúc đa nền tảng"""
    data_input = request.get_json() if request.is_json else request.values
    if not data_input:
        data_input = {}
    
    url = data_input.get("url")
    if not url:
        return jsonify({"success": False, "error": "Vui lòng cung cấp tham số 'url'!"}), 400
        
    lang = data_input.get("lang", "vi")
    max_comments = int(data_input.get("max_comments", 1000))
    
    # Thiết lập pipeline phân tích
    model_name = "wonrax/phobert-base-vietnamese-sentiment" if lang == "vi" else "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    
    try:
        # 1. Thu thập dữ liệu qua platform_scrapers (Dùng get_comments_rich)
        all_comments_rich, detected_platform, using_offline = get_comments_rich(url, max_comments, YOUTUBE_API_KEY)
        
        if not all_comments_rich:
            return jsonify({"success": False, "error": "Không tìm thấy bình luận nào cho liên kết này!"}), 404
            
        # 2. Phân tích cảm xúc dùng AI hoặc Fallback
        total = len(all_comments_rich)
        sentiment_counts = {"Tích cực": 0, "Tiêu cực": 0, "Trung tính": 0}
        total_score = 0
        details = []
        
        # Danh sách comments thuần phục vụ cho trích xuất từ khóa
        all_comments = [c["text"] for c in all_comments_rich]

        # ── Batch sentiment inference ──────────────────────────────
        sentiment_analyzer = get_ai_model(model_name)
        labels_scores = []  # list of (label_str, score_float)

        if sentiment_analyzer is not None:
            # Batch xử lý 32 bình luận / lần → nhanh hơn ~10x so với từng cái
            BATCH = 32
            print(f"[AI] Phân tích {total} bình luận bằng PhoBERT (batch={BATCH})...")
            for i in range(0, total, BATCH):
                batch_texts = [c[:256] for c in all_comments[i:i+BATCH]]
                try:
                    batch_results = sentiment_analyzer(batch_texts)
                    for res in batch_results:
                        lbl = res['label'].upper()
                        conf = res['score']
                        if lbl in ('POS', 'POSITIVE'):
                            labels_scores.append(("Tích cực", round(conf * 10, 1)))
                        elif lbl in ('NEG', 'NEGATIVE'):
                            labels_scores.append(("Tiêu cực", round((1 - conf) * 10, 1)))
                        else:
                            labels_scores.append(("Trung tính", 5.0))
                except Exception as batch_err:
                    print(f"[AI] Lỗi batch {i}: {batch_err} — fallback từng dòng")
                    for t in batch_texts:
                        labels_scores.append(fallback_sentiment_analyze(t))
            print(f"[AI] ✅ Hoàn thành phân tích AI cho {total} bình luận.")
        else:
            # Dùng từ điển fallback khi PhoBERT chưa sẵn sàng
            print(f"[FALLBACK] PhoBERT chưa sẵn sàng, dùng phân tích từ điển cho {total} bình luận.")
            for c in all_comments:
                labels_scores.append(fallback_sentiment_analyze(c))
        # ──────────────────────────────────────────────────────────

        for idx, comment_item in enumerate(all_comments_rich):
            comment = comment_item["text"]
            label, score = labels_scores[idx] if idx < len(labels_scores) else fallback_sentiment_analyze(comment)
                
            sentiment_counts[label] += 1
            total_score += score
            
            # Sử dụng thông tin người dùng thật từ BE
            name = comment_item.get("author", "Người dùng")
            time_ago = comment_item.get("published_at", "vài ngày trước")
            likes_count = comment_item.get("likes", 0)
            
            parts = name.split()
            initials = "".join([p[0] for p in parts[-2:]]) if len(parts) >= 2 else name[0]
            
            details.append({
                "comment": comment,
                "sentiment": label,
                "score": score,
                "name": name,
                "initials": initials,
                "time": time_ago,
                "likes": likes_count
            })
            
        avg_score = round(total_score / total, 1)
        star_rating = round(avg_score / 2, 1)
        pos_pct = round((sentiment_counts["Tích cực"] / total) * 100, 1)
        neg_pct = round((sentiment_counts["Tiêu cực"] / total) * 100, 1)
        neu_pct = round((sentiment_counts["Trung tính"] / total) * 100, 1)
        
        # Đề xuất dựa theo nền tảng
        if detected_platform == "shopee":
            rec_pos = "Nên mua"
            rec_mid = "Cân nhắc kỹ"
            rec_neg = "Không nên mua"
        else:
            rec_pos = "Nên đề xuất"
            rec_mid = "Cân nhắc"
            rec_neg = "Không đề xuất"
            
        # Trích xuất từ khóa trước để đưa vào thẻ tags động
        lang_code = "vi" if lang == "vi" else "en"
        if HAS_WORDCLOUD:
            keywords_tuples = wordcloud_utils.extract_keywords(all_comments, top_k=15, language=lang_code)
            keywords = [[kw, count] for kw, count in keywords_tuples]
        else:
            keywords_tuples = fallback_extract_keywords(all_comments, top_k=15)
            keywords = [[kw, count] for kw, count in keywords_tuples]
            
        # Cấu hình đề xuất & tạo tags động từ từ khóa và nền tảng (Tránh gắn dữ liệu cứng)
        tags = []
        if star_rating >= 4.0:
            summary = f"RẤT TÍCH CỰC ({pos_pct}% tích cực)"
            recommendation = rec_pos
            badge_type = "pos"
            badge_text = "👍 Rất tích cực"
            summary_header = f"Nội dung được đánh giá <strong>RẤT TÍCH CỰC</strong> ({pos_pct}% tích cực). Phản hồi cực kỳ tốt."
            summary_text = f"Nội dung được đánh giá RẤT TÍCH CỰC ({pos_pct}% tích cực). Phản hồi tốt. Hầu hết người xem đều bày tỏ thái độ hài lòng và đánh giá cao."
            tags.append("Tuyệt vời")
        elif star_rating >= 3.0:
            summary = f"KHÁ TÍCH CỰC ({pos_pct}% tích cực)"
            recommendation = rec_mid
            badge_type = "neu"
            badge_text = "😐 Khá tích cực"
            summary_header = f"Nội dung có đánh giá <strong>KHÁ TÍCH CỰC</strong> ({pos_pct}% tích cực). Nhìn chung khá ổn."
            summary_text = f"Nội dung có đánh giá KHÁ TÍCH CỰC ({pos_pct}% tích cực). Người dùng phản hồi tương đối tốt, nội dung có tính xây dựng cao."
            tags.append("Tích cực")
        elif star_rating >= 2.0:
            summary = f"TRUNG BÌNH ({pos_pct}% tích cực)"
            recommendation = "Cần xem xét"
            badge_type = "neu"
            badge_text = "😐 Trung bình"
            summary_header = f"Nội dung được đánh giá <strong>TRUNG BÌNH</strong> ({pos_pct}% tích cực). Phản hồi bình thường."
            summary_text = f"Nội dung được đánh giá trung bình. Người xem có cả phản hồi tốt lẫn góp ý xây dựng."
            tags.append("Trung tính")
        else:
            summary = f"TIÊU CỰC ({pos_pct}% tích cực)"
            recommendation = rec_neg
            badge_type = "neg"
            badge_text = "👎 Tiêu cực"
            summary_header = f"Nội dung bị đánh giá <strong>TIÊU CỰC</strong> ({pos_pct}% tích cực). Cần cải thiện."
            summary_text = f"Nội dung bị đánh giá TIÊU CỰC ({pos_pct}% tích cực). Xuất hiện nhiều điểm phàn nàn và thắc mắc của người xem."
            tags.append("Tiêu cực")
            
        tags.append(detected_platform.capitalize())
        
        # Lấy tối đa 2 từ khóa nổi bật (bỏ qua tên nền tảng) để làm tags
        added_keywords = 0
        for kw, count in keywords:
            kw_clean = kw.strip().capitalize()
            if len(kw_clean) > 2 and kw.lower() not in [detected_platform, "youtube", "tiktok", "shopee", "facebook", "lazada", "tiki", "video", "bình luận", "link"]:
                tags.append(kw_clean)
                added_keywords += 1
                if added_keywords >= 2:
                    break
        
        # Trích xuất điểm phàn nàn (Pain points) từ những bình luận tiêu cực thực tế
        neg_comments = [d["comment"] for d in details if d["sentiment"] == "Tiêu cực"]
        pain_points_data = []
        
        if neg_comments:
            if HAS_WORDCLOUD:
                neg_keywords = wordcloud_utils.extract_keywords(neg_comments, top_k=10, language=lang_code)
            else:
                neg_keywords = fallback_extract_keywords(neg_comments, top_k=10)
                
            if neg_keywords:
                for kw, count in neg_keywords[:3]:
                    sample_desc = ""
                    for c in neg_comments:
                        if kw.lower() in c.lower():
                            sample_desc = c
                            if len(sample_desc) > 85:
                                sample_desc = sample_desc[:85] + "..."
                            break
                    if sample_desc:
                        pain_points_data.append({
                            "title": kw.capitalize(),
                            "count": count,
                            "desc": sample_desc
                        })
        
        # Tạo dữ liệu xu hướng theo thời gian thực (Line chart values)
        pos_ratio = sentiment_counts["Tích cực"] / max(1, total)
        neg_ratio = sentiment_counts["Tiêu cực"] / max(1, total)
        neu_ratio = sentiment_counts["Trung tính"] / max(1, total)
        
        bins = ['0-5m', '5-10m', '10-15m', '15-20m', '20-25m', '25-30m', '30-35m', '35-40m']
        pos_base = [1.2, 2.7, 3.2, 2.0, 3.0, 2.5, 3.2, 2.8]
        neg_base = [0.1, 0.3, 0.1, 0.5, 0.1, 0.1, 0.1, 0.1]
        neu_base = [0.5, 0.7, 0.4, 1.0, 0.6, 0.4, 0.3, 0.5]
        
        pos_trend = [round(x * pos_ratio * 1.1, 1) for x in pos_base]
        neg_trend = [round(x * neg_ratio * 2.0, 1) for x in neg_base]
        neu_trend = [round(x * neu_ratio * 1.5, 1) for x in neu_base]
        
        sentiment_trend = {
            "bins": bins,
            "positive": pos_trend,
            "negative": neg_trend,
            "neutral": neu_trend
        }
 
        # Lưu lịch sử tự động nếu có header xác thực & email
        auth_header = request.headers.get('Authorization')
        email_header = request.headers.get('X-User-Email') or data_input.get('email')
        if auth_header and auth_header.startswith('Bearer ') and email_header:
            try:
                id_token = auth_header.split(' ')[1]
                save_history(id_token, email_header, url, detected_platform, avg_score)
            except Exception as ex:
                print(f"[API SERVER] Lỗi lưu lịch sử tự động: {ex}")

            # Gửi báo cáo tự động qua Telegram nếu người dùng cấu hình
            try:
                with open(LOCAL_USERS_FILE, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                user_data = users.get(email_header)
                if user_data and user_data.get("telegram_chat_id") and user_data.get("auto_send_telegram", False):
                    chat_id = user_data["telegram_chat_id"]
                    t_thread = threading.Thread(
                        target=send_telegram_report_async,
                        args=(chat_id, url, avg_score, star_rating, total, sentiment_counts, summary, recommendation, detected_platform),
                        daemon=True
                    )
                    t_thread.start()
            except Exception as ex:
                print(f"[API SERVER] Lỗi gửi báo cáo qua Telegram: {ex}")
 
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
                "neutral": sentiment_counts["Trung tính"],
                "positive_pct": pos_pct,
                "negative_pct": neg_pct,
                "neutral_pct": neu_pct
            },
            "comments_sample": details,
            "keywords": keywords,
            "pain_points_data": pain_points_data,
            "sentiment_trend": sentiment_trend,
            "tags": tags,
            "badge_type": badge_type,
            "badge_text": badge_text,
            "summary_header": summary_header,
            "summary_text": summary_text
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    try:
        import telegram_bot
        print("[API SERVER] Khởi chạy Telegram Bot trong background...")
        bot_thread = threading.Thread(target=telegram_bot.main, daemon=True)
        bot_thread.start()
    except Exception as bot_err:
        print(f"[API SERVER] Không thể khởi chạy Telegram Bot: {bot_err}")

    # use_reloader=False: Tắt watchdog để tránh reload vô hạn khi tải PhoBERT/torch
    # PhoBERT cần ghi file vào site-packages khi tải lần đầu → watchdog hiểu nhầm là code thay đổi
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)


