from googleapiclient.discovery import build
import pandas as pd

# 1. Điền API Key của bạn vào đây (nhớ giữ lại cặp dấu ngoặc kép "")
API_KEY = "AIzaSyDo1_HgQDTSqw1BIezKMu45Y3BYKk091Tw"

def lay_binh_luan_youtube(video_id, max_results=50):
    # Khởi tạo kết nối với YouTube
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    # Gửi yêu cầu lấy bình luận
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText"
    )
    
    response = request.execute()
    
    # Lọc lấy nội dung bình luận từ dữ liệu trả về
    danh_sach_binh_luan = []
    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
        danh_sach_binh_luan.append(comment)
        
    return danh_sach_binh_luan

# 2. Thử nghiệm với một Video trên YouTube
# Giả sử link là: https://www.youtube.com/watch?v=H74KtyE2ZHM
# Thì Video ID chính là phần chữ sau dấu "="
VIDEO_ID = "FoymeD0cwuo"

print("Đang kết nối YouTube và lấy bình luận...")
# Lấy thử 50 bình luận
comments = lay_binh_luan_youtube(VIDEO_ID, max_results=50)

# 3. Chuyển thành bảng dữ liệu Pandas và in ra màn hình
df = pd.DataFrame(comments, columns=['BinhLuan'])
print("\n--- ĐÃ LẤY ĐƯỢC CÁC BÌNH LUẬN SAU ---")
print(df.head()) # In ra 5 dòng đầu tiên để xem thử

# 4. Lưu lại thành file CSV để dành cho bước phân tích cảm xúc
df.to_csv('binh_luan_youtube.csv', index=False, encoding='utf-8-sig')
print("\nĐã lưu thành công vào file binh_luan_youtube.csv!")