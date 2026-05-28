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

def _fetch_all_replies_text(youtube, parent_id, max_replies):
    """Lấy toàn bộ replies (text only) của một thread."""
    replies = []
    page_token = None
    while len(replies) < max_replies:
        try:
            req = youtube.comments().list(
                part="snippet", parentId=parent_id,
                maxResults=100, pageToken=page_token,
                textFormat="plainText"
            )
            resp = req.execute()
        except Exception:
            break
        for c in resp.get('items', []):
            text = c.get('snippet', {}).get('textDisplay', '')
            if text:
                replies.append(text)
            if len(replies) >= max_replies:
                break
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return replies


def scrape_youtube(url, max_total, api_key):
    try:
        video_id = extract_youtube_video_id(url)
        youtube = build('youtube', 'v3', developerKey=api_key)
        all_comments = []
        next_page_token = None
        
        while len(all_comments) < max_total:
            request = youtube.commentThreads().list(
                part="snippet,replies", videoId=video_id, maxResults=100,
                pageToken=next_page_token, textFormat="plainText"
            )
            response = request.execute()
            items = response.get('items', [])
            if not items:
                break
                
            for item in items:
                # Top-level comment
                thread_id = item['id']
                top_snippet = item['snippet']['topLevelComment']['snippet']
                all_comments.append(top_snippet['textDisplay'])
                if len(all_comments) >= max_total:
                    break
                
                # Replies: lấy đầy đủ
                total_reply_count = item['snippet'].get('totalReplyCount', 0)
                replies_obj = item.get('replies', {})
                embedded_replies = replies_obj.get('comments', [])
                embedded_count = len(embedded_replies)
                
                if total_reply_count > 0 and total_reply_count > embedded_count:
                    remaining = max_total - len(all_comments)
                    full_replies = _fetch_all_replies_text(
                        youtube, thread_id, min(total_reply_count, remaining)
                    )
                    all_comments.extend(full_replies)
                else:
                    for reply in embedded_replies:
                        reply_text = reply.get('snippet', {}).get('textDisplay', '')
                        if reply_text:
                            all_comments.append(reply_text)
                        if len(all_comments) >= max_total:
                            break
                        
                if len(all_comments) >= max_total:
                    break
                    
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        print(f"[SCRAPER] YouTube API: thu thập được {len(all_comments)} bình luận (bao gồm replies)")
        if all_comments:
            return all_comments, False
        else:
            raise Exception("No comments found via API.")
    except Exception as e:
        print(f"[SCRAPER] YouTube API lỗi, fallback offline: {e}")
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


# ==========================================================
# RICH UNIFIED INTERFACE (For api_server to avoid hardcoded mock author info)
# ==========================================================
def format_published_at(iso_str):
    if not iso_str:
        return "vài giờ trước"
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        seconds = diff.total_seconds()
        if seconds < 0:
            return "vừa xong"
        
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)} phút trước"
            
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)} giờ trước"
            
        days = hours / 24
        if days < 30:
            return f"{int(days)} ngày trước"
            
        months = days / 30
        if months < 12:
            return f"{int(months)} tháng trước"
            
        years = months / 12
        return f"{int(years)} năm trước"
    except Exception:
        return "vài ngày trước"


def load_offline_comments_rich(platform, max_total=1000):
    raw = load_offline_comments(platform, max_total)
    rich = []
    for idx, comment in enumerate(raw):
        names = ["Nguyễn Văn An", "Trần Thị Bình", "Lê Hoàng Cường", "Phạm Minh Đức", "Hoàng Thu Thảo", "Vũ Huy Hoàng", "Đặng Ngọc Sơn"]
        times = ["2 giờ trước", "5 giờ trước", "1 ngày trước", "2 ngày trước", "3 ngày trước"]
        likes_count = (idx * 7 + 3) % 43
        name = names[idx % len(names)]
        time_ago = times[idx % len(times)]
        rich.append({
            "text": comment,
            "author": name,
            "likes": likes_count,
            "published_at": time_ago
        })
    return rich


def _fetch_all_replies_rich(youtube, parent_id, max_replies, format_fn):
    """Lấy toàn bộ replies của một comment thread qua comments.list API."""
    replies = []
    page_token = None
    while len(replies) < max_replies:
        try:
            req = youtube.comments().list(
                part="snippet", parentId=parent_id,
                maxResults=100, pageToken=page_token,
                textFormat="plainText"
            )
            resp = req.execute()
        except Exception:
            break
        for c in resp.get('items', []):
            s = c.get('snippet', {})
            text = s.get('textDisplay', '')
            if not text:
                continue
            replies.append({
                "text": text,
                "author": s.get('authorDisplayName', 'Người dùng YouTube'),
                "likes": s.get('likeCount', 0),
                "published_at": format_fn(s.get('publishedAt', ''))
            })
            if len(replies) >= max_replies:
                break
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return replies


def scrape_youtube_rich(url, max_total, api_key):
    try:
        video_id = extract_youtube_video_id(url)
        youtube = build('youtube', 'v3', developerKey=api_key)
        all_comments = []
        next_page_token = None
        
        while len(all_comments) < max_total:
            request = youtube.commentThreads().list(
                part="snippet,replies", videoId=video_id, maxResults=100,
                pageToken=next_page_token, textFormat="plainText"
            )
            response = request.execute()
            items = response.get('items', [])
            if not items:
                break
                
            for item in items:
                # Top-level comment
                thread_id = item['id']
                top_snippet = item['snippet']['topLevelComment']['snippet']
                comment_text = top_snippet['textDisplay']
                author = top_snippet.get('authorDisplayName', 'Người dùng YouTube')
                likes = top_snippet.get('likeCount', 0)
                published_at = top_snippet.get('publishedAt', '')
                time_str = format_published_at(published_at)
                
                all_comments.append({
                    "text": comment_text,
                    "author": author,
                    "likes": likes,
                    "published_at": time_str
                })
                if len(all_comments) >= max_total:
                    break
                
                # Replies: lấy đầy đủ nếu có nhiều hơn embedded
                total_reply_count = item['snippet'].get('totalReplyCount', 0)
                replies_obj = item.get('replies', {})
                embedded_replies = replies_obj.get('comments', [])
                embedded_count = len(embedded_replies)
                
                if total_reply_count > 0 and total_reply_count > embedded_count:
                    # Gọi API riêng để lấy toàn bộ replies
                    remaining = max_total - len(all_comments)
                    full_replies = _fetch_all_replies_rich(
                        youtube, thread_id, min(total_reply_count, remaining), format_published_at
                    )
                    all_comments.extend(full_replies)
                else:
                    # Dùng embedded replies (đủ rồi)
                    for reply in embedded_replies:
                        r_snippet = reply.get('snippet', {})
                        r_text = r_snippet.get('textDisplay', '')
                        if not r_text:
                            continue
                        r_author = r_snippet.get('authorDisplayName', 'Người dùng YouTube')
                        r_likes = r_snippet.get('likeCount', 0)
                        r_published = r_snippet.get('publishedAt', '')
                        r_time = format_published_at(r_published)
                        all_comments.append({
                            "text": r_text,
                            "author": r_author,
                            "likes": r_likes,
                            "published_at": r_time
                        })
                        if len(all_comments) >= max_total:
                            break
                        
                if len(all_comments) >= max_total:
                    break
                    
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        print(f"[SCRAPER] YouTube Rich API: thu thập được {len(all_comments)} bình luận (bao gồm replies)")
        if all_comments:
            return all_comments, False
        else:
            raise Exception("No comments found via API.")
    except Exception as e:
        print(f"[SCRAPER] YouTube Rich API lỗi, fallback offline: {e}")
        return load_offline_comments_rich("youtube", max_total), True


def scrape_shopee_rich(url, max_total):
    shopid, itemid = extract_shopee_ids(url)
    if not shopid or not itemid:
        return load_offline_comments_rich("shopee", max_total), True
        
    api_url = f"https://shopee.vn/api/v2/item/get_ratings?itemid={itemid}&shopid={shopid}&offset=0&limit=50&filter=0&type=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": url
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            ratings = data.get("data", {}).get("ratings", [])
            comments_rich = []
            for r in ratings:
                comment = r.get("comment")
                if comment:
                    author = r.get("author_username", "Người dùng Shopee")
                    ctime = r.get("ctime", 0)
                    time_str = "vài ngày trước"
                    if ctime > 0:
                        from datetime import datetime, timezone
                        try:
                            dt = datetime.fromtimestamp(ctime, tz=timezone.utc)
                            time_str = format_published_at(dt.isoformat())
                        except Exception:
                            pass
                    rating_star = r.get("rating_star", 5)
                    comments_rich.append({
                        "text": comment,
                        "author": author,
                        "likes": rating_star,
                        "published_at": time_str
                    })
            if comments_rich:
                return comments_rich[:max_total], False
        
        return load_offline_comments_rich("shopee", max_total), True
    except Exception:
        return load_offline_comments_rich("shopee", max_total), True


def get_comments_rich(url, max_total=1000, youtube_api_key=None):
    platform = detect_platform(url)
    
    if platform == "youtube":
        comments, is_offline = scrape_youtube_rich(url, max_total, youtube_api_key)
        return comments, platform, is_offline
        
    elif platform == "shopee":
        comments, is_offline = scrape_shopee_rich(url, max_total)
        return comments, platform, is_offline
        
    elif platform == "tiktok":
        comments = load_offline_comments_rich("tiktok", max_total)
        return comments, platform, True
        
    elif platform == "facebook":
        comments = load_offline_comments_rich("facebook", max_total)
        return comments, platform, True
        
    elif platform == "lazada":
        comments = load_offline_comments_rich("lazada", max_total)
        return comments, platform, True
        
    elif platform == "tiki":
        comments = load_offline_comments_rich("tiki", max_total)
        return comments, platform, True
        
    else:
        comments, is_offline = scrape_youtube_rich(url, max_total, youtube_api_key)
        return comments, "youtube", is_offline
