import re
import os
import pandas as pd
import requests
from googleapiclient.discovery import build

def detect_platform(url):
    """Xác định nền tảng từ URL"""
    url_lower = str(url).lower()
    
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "tiktok.com" in url_lower:
        return "tiktok"
    elif "shopee.vn" in url_lower or "shopee.com" in url_lower:
        return "shopee"
    elif "facebook.com" in url_lower or "fb.com" in url_lower:
        return "facebook"
    elif "lazada.vn" in url_lower or "lazada.com" in url_lower:
        return "lazada"
    elif "tiki.vn" in url_lower:
        return "tiki"
    else:
        return "unknown"

def load_offline_comments(platform, max_total=1000):
    """Nạp dữ liệu giả lập/dự phòng từ file CSV tương ứng"""
    filename = f"binh_luan_{platform}.csv"
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            col_candidates = ["BinhLuan", "Bình luận", df.columns[0]]
            comment_col = next((c for c in col_candidates if c in df.columns), None)
            if comment_col:
                return df[comment_col].dropna().tolist()[:max_total]
        except Exception:
            return []
    return []

# ==========================================================
# YOUTUBE
# ==========================================================
def extract_youtube_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "shorts/" in url:
        return url.split("shorts/")[1].split("?")[0]
    else:
        return url.split("/")[-1].split("?")[0]

def scrape_youtube(url, max_total, api_key):
    try:
        video_id = extract_youtube_video_id(url)
        youtube = build('youtube', 'v3', developerKey=api_key)
        all_comments = []
        next_page_token = None
        
        while len(all_comments) < max_total:
            request = youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100,
                pageToken=next_page_token, textFormat="plainText"
            )
            response = request.execute()
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                all_comments.append(comment)
                if len(all_comments) >= max_total:
                    break
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        if all_comments:
            return all_comments, False
        else:
            raise Exception("No comments found via API.")
    except Exception as e:
        # Fallback to offline mode
        return load_offline_comments("youtube", max_total), True

# ==========================================================
# SHOPEE
# ==========================================================
def extract_shopee_ids(url):
    match1 = re.search(r"shopee\.vn/product/(\d+)/(\d+)", url)
    if match1:
        return match1.group(1), match1.group(2)
    match2 = re.search(r"i\.(\d+)\.(\d+)", url)
    if match2:
        return match2.group(1), match2.group(2)
    return None, None

def scrape_shopee(url, max_total):
    shopid, itemid = extract_shopee_ids(url)
    if not shopid or not itemid:
        return load_offline_comments("shopee", max_total), True
        
    api_url = f"https://shopee.vn/api/v2/item/get_ratings?itemid={itemid}&shopid={shopid}&offset=0&limit=50&filter=0&type=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": url
    }
    
    try:
        # Trải nghiệm Shopee API (Có thể bị chặn 403 tuỳ theo Cloudflare)
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            ratings = data.get("data", {}).get("ratings", [])
            comments = [r.get("comment") for r in ratings if r.get("comment")]
            if comments:
                return comments[:max_total], False
        
        # Nếu chặn/lỗi -> Fallback Offline
        return load_offline_comments("shopee", max_total), True
    except Exception:
        return load_offline_comments("shopee", max_total), True

# ==========================================================
# UNIFIED INTERFACE
# ==========================================================
def get_comments(url, max_total=1000, youtube_api_key=None):
    """
    Trả về: (comments, platform, is_offline)
    """
    platform = detect_platform(url)
    
    if platform == "youtube":
        comments, is_offline = scrape_youtube(url, max_total, youtube_api_key)
        return comments, platform, is_offline
        
    elif platform == "shopee":
        comments, is_offline = scrape_shopee(url, max_total)
        return comments, platform, is_offline
        
    elif platform == "tiktok":
        # Do TikTok chặn gắt, sử dụng simulator Data
        comments = load_offline_comments("tiktok", max_total)
        return comments, platform, True
        
    elif platform == "facebook":
        # Do Facebook Graph API cần App Token, sử dụng simulator Data
        comments = load_offline_comments("facebook", max_total)
        return comments, platform, True
        
    elif platform == "lazada":
        comments = load_offline_comments("lazada", max_total)
        return comments, platform, True
        
    elif platform == "tiki":
        comments = load_offline_comments("tiki", max_total)
        return comments, platform, True
        
    else:
        # Nếu unknown, thử dùng youtube
        comments, is_offline = scrape_youtube(url, max_total, youtube_api_key)
        return comments, "youtube", is_offline
