import requests
import time
import os
import json
import re
from datetime import datetime, timezone
from transformers import pipeline
from platform_scrapers import get_comments, detect_platform

# ============================================
# CONFIG
# ============================================
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"
TELEGRAM_BOT_TOKEN = "8606918938:AAFlcQ33rMCw8z-uB6wYm96M8NG3SUfqkvE"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

print("[LOADING] Loading DistilBERT Multilingual model...")
sentiment_analyzer = pipeline("sentiment-analysis", model="lxyuan/distilbert-base-multilingual-cased-sentiments-student")
print("[READY] DistilBERT Multilingual model is ready!")

def get_platform_info(platform):
    """Lấy thông tin nhận diện UI cho nền tảng"""
    info = {
        "youtube": {"name": "YouTube", "icon": "🔴", "rec_pos": "✅ Nên xem/đề xuất", "rec_neg": "❌ Không đề xuất"},
        "tiktok": {"name": "TikTok", "icon": "🎵", "rec_pos": "✅ Rất đáng xem", "rec_neg": "❌ Bỏ qua"},
        "shopee": {"name": "Shopee", "icon": "🛍️", "rec_pos": "✅ Nên mua", "rec_neg": "❌ Né gấp"},
        "facebook": {"name": "Facebook", "icon": "👥", "rec_pos": "✅ Bài viết hay", "rec_neg": "❌ Thông tin toxic"}
    }
    return info.get(platform, {"name": "Website", "icon": "🌐", "rec_pos": "✅ Nên xem", "rec_neg": "❌ Không đề xuất"})

def analyze_link(url):
    """Phân tích video/link đa nền tảng và trả về kết quả"""
    try:
        all_comments, platform, is_offline = get_comments(url, 1000, API_KEY)
        p_info = get_platform_info(platform)
        
        offline_warning = ""
        if is_offline:
            offline_warning = f"⚠️ *[Offline Mode]* Mạng chậm hoặc API chặn. Sử dụng dữ liệu dự phòng của {p_info['name']}!\n\n"
        
        if not all_comments:
            return None, f"❌ Không tìm thấy bình luận nào cho link {p_info['name']} này."
        
        data = []
        total_score = 0
        sentiment_counts = {"Tích cực": 0, "Tiêu cực": 0, "Trung tính": 0}
        
        for comment in all_comments:
            try:
                short = comment[:200]
                result = sentiment_analyzer(short, truncation=True)[0]
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
            
            total_score += score
            sentiment_counts[label] += 1
            data.append(score)
        
        avg_score = round(total_score / len(data), 1) if data else 0
        star_rating = round(avg_score / 2, 1)
        total = len(data)
        pos_pct = round((sentiment_counts["Tích cực"] / total) * 100, 1)
        
        if star_rating >= 4.0:
            summary = f"🟢 RẤT TÍCH CỰC ({pos_pct}% tích cực)"
            rec = p_info["rec_pos"]
        elif star_rating >= 3.0:
            summary = f"🟡 KHÁ TÍCH CỰC ({pos_pct}% tích cực)"
            rec = "⚠️ Cân nhắc"
        elif star_rating >= 2.0:
            summary = f"🟠 TRUNG BÌNH ({pos_pct}% tích cực)"
            rec = "❓ Cần xem xét"
        else:
            summary = f"🔴 TIÊU CỰC ({pos_pct}% tích cực)"
            rec = p_info["rec_neg"]
        
        result_text = f"""{offline_warning}{p_info['icon']} *{p_info['name']} Comment AI Analyzer*

🔗 *Link:* {url}
⭐ *Điểm:* {avg_score}/10 ({star_rating}/5 sao)

📊 *Thống kê ({total} bình luận):*
• 🟢 Tích cực: {sentiment_counts['Tích cực']} ({round(sentiment_counts['Tích cực']/total*100,1)}%)
• 🔴 Tiêu cực: {sentiment_counts['Tiêu cực']} ({round(sentiment_counts['Tiêu cực']/total*100,1)}%)
• ⚪ Trung tính: {sentiment_counts['Trung tính']} ({round(sentiment_counts['Trung tính']/total*100,1)}%)

💡 *Đánh giá:* {summary}
📌 *Đề xuất:* {rec}
"""
        return result_text, None
        
    except Exception as e:
        return None, f"❌ Lỗi xử lý: {str(e)}"

# ============================================
# TELEGRAM BOT CORE
# ============================================
def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"offset": offset, "limit": 10}
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json()
    except Exception as e:
        print(f"⚠️ Lỗi kết nối Telegram: {e}")
        return {"ok": False}

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Lỗi gửi tin nhắn: {e}")
        return False

def main():
    print("[RUNNING] Multi-Platform Telegram Bot is running...")
    print("[INFO] Send YouTube, TikTok, Shopee, or Facebook links to analyze!")
    print("[INFO] Press Ctrl+C to stop\n")
    
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            
            if not updates.get("ok"):
                time.sleep(5)
                continue
            
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                
                if "message" not in update or "text" not in update["message"]:
                    continue
                
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message["text"].strip()
                
                if text.startswith("/start"):
                    # Check if connection parameter is present
                    parts = text.split("connect_")
                    if len(parts) > 1:
                        user_id = parts[1].strip()
                        linked = False
                        email = None
                        
                        try:
                            if os.path.exists("users_local.json"):
                                with open("users_local.json", "r", encoding="utf-8") as f:
                                    users = json.load(f)
                                for u_email, u_data in users.items():
                                    if u_data.get("user_id") == user_id:
                                        u_data["telegram_chat_id"] = chat_id
                                        u_data["telegram_username"] = message["chat"].get("username") or message["chat"].get("first_name") or "User"
                                        email = u_email
                                        linked = True
                                        break
                                if linked:
                                    with open("users_local.json", "w", encoding="utf-8") as f:
                                        json.dump(users, f, ensure_ascii=False, indent=4)
                        except Exception as e:
                            print(f"[TELEGRAM BOT] Lỗi lưu liên kết: {e}")
                            
                        if linked:
                            success_msg = f"""🎉 *Liên kết tài khoản thành công!*

Tài khoản Telegram của bạn đã được kết nối với email: `{email}` trên hệ thống AI Comment Analyzer Pro.

Từ bây giờ:
1. Bạn sẽ tự động nhận được báo cáo phân tích tại đây khi chạy phân tích trên Website (nếu bật tùy chọn trong cài đặt Trang cá nhân).
2. Bạn có thể gửi trực tiếp link YouTube, TikTok, Facebook, Shopee vào đây để bot phân tích và tự động lưu lịch sử vào tài khoản web của bạn!"""
                            send_message(chat_id, success_msg)
                        else:
                            send_message(chat_id, "❌ Mã liên kết không hợp lệ hoặc tài khoản không tồn tại trên hệ thống. Vui lòng kiểm tra lại!")
                        continue
                        
                    welcome_msg = """👋 *Chào mừng đến với AI Comment Analyzer Đa Nền Tảng!*

🤖 Bot sử dụng AI để phân tích cảm xúc bình luận thời gian thực.
Hỗ trợ 4 nền tảng lớn:
🔴 *YouTube* (Đánh giá video)
🎵 *TikTok* (Phân tích trend)
🛍️ *Shopee* (Nhận định chất lượng hàng hóa)
👥 *Facebook* (Dư luận bài đăng)

📩 *Cách dùng:* Chỉ cần dán link vào đây, bot sẽ tự động nhận diện và phân tích!
"""
                    send_message(chat_id, welcome_msg)
                    continue
                
                # Bắt mọi link http/https
                if text.startswith("http://") or text.startswith("https://"):
                    # Check link authentication
                    email = None
                    try:
                        if os.path.exists("users_local.json"):
                            with open("users_local.json", "r", encoding="utf-8") as f:
                                users = json.load(f)
                            for u_email, u_data in users.items():
                                if u_data.get("telegram_chat_id") == chat_id:
                                    email = u_email
                                    break
                    except Exception as e:
                        print(f"[TELEGRAM BOT] Lỗi đọc user list: {e}")
                        
                    if not email:
                        connect_err_msg = """⚠️ *Tài khoản Telegram của bạn chưa được liên kết!*

Vui lòng truy cập trang cá nhân của bạn trên website và click vào Email ở thanh menu -> **Kết nối Telegram** để thực hiện liên kết trước khi sử dụng bot nhé."""
                        send_message(chat_id, connect_err_msg)
                        continue

                    p_name = detect_platform(text)
                    if p_name == "unknown":
                        send_message(chat_id, "❓ Link không thuộc hệ sinh thái hỗ trợ (YouTube, TikTok, Shopee, Facebook). Vui lòng thử lại!")
                        continue
                        
                    p_info = get_platform_info(p_name)
                    send_message(chat_id, f"⏳ Đang phân tích bình luận {p_info['name']}... Vui lòng đợi!")
                    
                    result, error = analyze_link(text)
                    if error:
                        send_message(chat_id, error)
                    else:
                        send_message(chat_id, result)
                        
                        # Save to local history
                        try:
                            score_match = re.search(r"⭐ \*Điểm:\* ([\d\.]+)/10", result)
                            avg_score = float(score_match.group(1)) if score_match else 5.0
                            
                            history = []
                            if os.path.exists("history_local.json"):
                                with open("history_local.json", "r", encoding="utf-8") as f:
                                    history = json.load(f)
                                    
                            timestamp_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                            new_record = {
                                "email": email,
                                "url": text,
                                "platform": p_name,
                                "score": avg_score,
                                "timestamp": timestamp_str
                            }
                            history.append(new_record)
                            with open("history_local.json", "w", encoding="utf-8") as f:
                                json.dump(history, f, ensure_ascii=False, indent=4)
                        except Exception as hist_err:
                            print(f"[TELEGRAM BOT] Lỗi lưu lịch sử: {hist_err}")
                else:
                    send_message(chat_id, "❓ Vui lòng gửi một đường link (bắt đầu bằng http) hợp lệ!\n\nGửi `/start` để xem hướng dẫn.")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n[STOPPED] Bot has stopped!")
            break
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
