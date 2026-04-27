import requests
import time
import re
from googleapiclient.discovery import build
from transformers import pipeline

# ============================================
# CONFIG
# ============================================
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"
TELEGRAM_BOT_TOKEN = "8606918938:AAFlcQ33rMCw8z-uB6wYm96M8NG3SUfqkvE"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

print("⏳ Đang tải mô hình PhoBERT...")
sentiment_analyzer = pipeline("sentiment-analysis", model="wonrax/phobert-base-vietnamese-sentiment")
print("✅ Mô hình PhoBERT đã sẵn sàng!")

# ============================================
# YOUTUBE FUNCTIONS
# ============================================
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

def analyze_youtube_video(url):
    """Phân tích video YouTube và trả về kết quả"""
    try:
        video_id = extract_video_id(url)
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        all_comments = get_all_comments(youtube, video_id, max_total=1000)
        
        if not all_comments:
            return None, "❌ Video không có bình luận hoặc không tìm thấy video."
        
        data = []
        total_score = 0
        sentiment_counts = {"Tích cực": 0, "Tiêu cực": 0, "Trung tính": 0}
        
        for comment in all_comments:
            try:
                short = comment[:200]
                result = sentiment_analyzer(short, truncation=True)[0]
                label_ai = result['label']
                conf = result['score']
                
                if label_ai == 'POS':
                    label = "Tích cực"
                    score = round(conf * 10, 1)
                elif label_ai == 'NEG':
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
            rec = "✅ Nên đề xuất"
        elif star_rating >= 3.0:
            summary = f"🟡 KHÁ TÍCH CỰC ({pos_pct}% tích cực)"
            rec = "⚠️ Cân nhắc"
        elif star_rating >= 2.0:
            summary = f"🟠 TRUNG BÌNH ({pos_pct}% tích cực)"
            rec = "❓ Cần xem xét"
        else:
            summary = f"🔴 TIÊU CỰC ({pos_pct}% tích cực)"
            rec = "❌ Không đề xuất"
        
        result_text = f"""🔴 *YouTube Comment AI Analyzer*

📺 *Link:* {url}
⭐ *Điểm:* {avg_score}/10 ({star_rating}/5 sao)

📊 *Thống kê:*
• 🟢 Tích cực: {sentiment_counts['Tích cực']} ({round(sentiment_counts['Tích cực']/total*100,1)}%)
• 🔴 Tiêu cực: {sentiment_counts['Tiêu cực']} ({round(sentiment_counts['Tiêu cực']/total*100,1)}%)
• ⚪ Trung tính: {sentiment_counts['Trung tính']} ({round(sentiment_counts['Trung tính']/total*100,1)}%)
• 💬 Tổng: {total} bình luận

💡 *Đánh giá:* {summary}
📌 *Đề xuất:* {rec}
"""
        return result_text, None
        
    except Exception as e:
        return None, f"❌ Lỗi: {str(e)}"

# ============================================
# TELEGRAM BOT
# ============================================
def get_updates(offset=None):
    """Lấy tin nhắn mới từ Telegram"""
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"offset": offset, "limit": 10}
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json()
    except Exception as e:
        print(f"⚠️ Lỗi kết nối Telegram: {e}")
        return {"ok": False}

def send_message(chat_id, text):
    """Gửi tin nhắn qua Telegram"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Lỗi gửi tin nhắn: {e}")
        return False

def is_youtube_link(text):
    """Kiểm tra xem text có phải link YouTube không"""
    youtube_patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[\w-]+',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/[\w-]+',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/[\w-]+'
    ]
    for pattern in youtube_patterns:
        if re.search(pattern, text):
            return True
    return False

def extract_youtube_link(text):
    """Trích xuất link YouTube từ text"""
    youtube_patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[\w-]+',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/[\w-]+',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/[\w-]+'
    ]
    for pattern in youtube_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

# ============================================
# MAIN LOOP
# ============================================
def main():
    print("🤖 Telegram Bot đang chạy...")
    print("📩 Gửi link YouTube cho bot để phân tích!")
    print("⛔ Nhấn Ctrl+C để dừng\n")
    
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            
            if not updates.get("ok"):
                time.sleep(5)
                continue
            
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                
                if "message" not in update:
                    continue
                
                message = update["message"]
                chat_id = message["chat"]["id"]
                
                # Chỉ xử lý tin nhắn text
                if "text" not in message:
                    continue
                
                text = message["text"]
                
                # Kiểm tra lệnh /start
                if text == "/start":
                    welcome_msg = """👋 *Chào mừng bạn đến với YouTube Comment AI Analyzer!*

🤖 Bot này giúp bạn phân tích cảm xúc bình luận YouTube bằng AI PhoBERT.

📩 *Cách dùng:*
Gửi link YouTube cho bot, ví dụ:
`https://www.youtube.com/watch?v=xxxxx`

📊 Bot sẽ trả về:
• Điểm đánh giá (0-10)
• Phân bố sentiment
• Đề xuất nên/không nên xem

⚡ Bắt đầu ngay bằng cách gửi link YouTube!
"""
                    send_message(chat_id, welcome_msg)
                    continue
                
                # Kiểm tra link YouTube
                if is_youtube_link(text):
                    link = extract_youtube_link(text)
                    
                    # Thông báo đang xử lý
                    send_message(chat_id, "⏳ Đang phân tích video... Vui lòng đợi!")
                    
                    # Phân tích
                    result, error = analyze_youtube_video(link)
                    
                    if error:
                        send_message(chat_id, error)
                    else:
                        send_message(chat_id, result)
                else:
                    send_message(chat_id, "❓ Vui lòng gửi link YouTube hợp lệ!\n\nGửi `/start` để xem hướng dẫn.")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n👋 Bot đã dừng!")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
