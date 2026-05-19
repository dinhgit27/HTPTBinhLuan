# 📺 YouTube Comment AI Analyzer & Distributed Systems Architecture
> **Đồ án môn học:** Hệ Thống Phân Tán (Distributed Systems) / Phân Tích Dữ Liệu Lớn.
> Hệ thống phân tích cảm xúc bình luận YouTube thời gian thực sử dụng trí tuệ nhân tạo (AI PhoBERT + DistilBERT) với kiến trúc dịch vụ phân tán hoàn chỉnh.

---

## 📐 Kiến trúc Hệ thống Phân tán (Distributed Architecture)

Hệ thống được thiết kế theo mô hình **Microservices & Phân tán**, tích hợp nhiều phân hệ độc lập giao tiếp thông qua giao thức mạng HTTP RESTful API và cơ chế Long Polling:

```mermaid
graph TD
    User([Người Dùng])
    
    subgraph Clients [Phân Hệ Client / Giao Diện]
        Streamlit[Web App Streamlit - Port 8502]
        Telegram[Kênh Telegram Bot]
        CSharpApp[WinForms / C# Client]
    end

    subgraph Middleware [Phân Hệ Trung Gian / Điều Phối]
        n8n[n8n Workflow Automation]
    end

    subgraph Service [Phân Hệ Xử Lý Phân Tán - Python Server]
        FlaskServer[Flask API Server - Port 5000]
        SentimentPipeline[AI Sentiment Engine]
        PhoBERT[wonrax/phobert-base-vietnamese-sentiment]
        DistilBERT[lxyuan/distilbert-base-multilingual-cased-sentiments-student]
    end

    subgraph Data [Phân Hệ Dữ Liệu & API Ngoài]
        YoutubeAPI[YouTube Data API v3]
        OfflineCSV[(Dữ Liệu Offline Backup - CSV)]
    end

    %% Luồng giao tiếp
    User -->|Tương tác| Clients
    Streamlit -->|Gọi trực tiếp| YoutubeAPI
    Streamlit -->|Xử lý AI| SentimentPipeline
    
    Telegram -->|Long Polling| Telegram
    Telegram -->|Gọi trực tiếp| YoutubeAPI
    Telegram -->|Xử lý AI| SentimentPipeline
    
    CSharpApp -->|HTTP POST/GET| FlaskServer
    n8n -->|Webhook call| FlaskServer
    
    FlaskServer -->|Điều phối| SentimentPipeline
    FlaskServer -->|Truy xuất| YoutubeAPI
    
    YoutubeAPI -.->|Nếu lỗi / Mất mạng / Hết quota| OfflineCSV
    SentimentPipeline -->|Load| PhoBERT
    SentimentPipeline -->|Load| DistilBERT
```

---

## 🌟 Các Tính Năng Nổi Bật Sẵn Sàng Cho Báo Cáo

1. **Phân tích Cảm xúc Đa mô hình (Dual-Model Sentiment Engine):**
   * **Tiếng Việt 🇻🇳:** Sử dụng **PhoBERT** của VinAI để tối ưu hóa ngôn ngữ bản địa tốt nhất.
   * **English & Khác 🌐:** Sử dụng **DistilBERT Multilingual** hỗ trợ hơn 10 ngôn ngữ (Anh, Trung, Hàn, Nhật, Tây Ban Nha...).
2. **Cơ chế Dự phòng Ngoại tuyến (Offline Backup Fallback) - AN TOÀN TUYỆT ĐỐI:**
   * Tự động phát hiện khi YouTube API hết hạn quota (giới hạn 10.000 đơn vị/ngày) hoặc máy báo cáo mất kết nối internet.
   * Hệ thống sẽ tự động chuyển sang chế độ **Offline Mode**, sử dụng tệp dữ liệu lưu trữ dự phòng `binh_luan_youtube.csv` để xử lý phân tích và hiển thị kết quả bình thường thay vì bị sập hệ thống trước mặt hội đồng chấm thi!
3. **Đa dạng Phân hệ Client:**
   * Giao diện Dashboard Web trực quan, sinh động (Streamlit).
   * Bot tự động hóa tương tác thời gian thực qua ứng dụng di động (Telegram Bot).
   * Cổng API Microservice chuẩn hóa phục vụ tích hợp C# WinForms hoặc n8n.
4. **Vẽ biểu đồ thông minh (Multilingual Chart & Font Fallback):**
   * Hỗ trợ vẽ biểu đồ tiếng Trung/Nhật/Hàn (CJK) hoàn hảo mà không bị ô vuông rác nhờ cơ chế **Matplotlib Font Fallback** thông minh (Microsoft YaHei & SimHei).
   * Tự động ẩn các cảnh báo rác của hệ thống giúp logs luôn sạch đẹp.

---

## 🚀 Hướng Dẫn Khởi Chạy Từng Phân Hệ

Hãy mở các cửa sổ Terminal độc lập trong thư mục dự án và chạy các phân hệ sau:

### 1️⃣ Khởi chạy Giao diện Web (Streamlit Web Dashboard)
```bash
streamlit run app.py
```
* **Địa chỉ:** [http://localhost:8502](http://localhost:8502) (Hoặc cổng Streamlit mặc định)
* **Demo:** Nhập link YouTube, lựa chọn ngôn ngữ, hệ thống sẽ vẽ biểu đồ tròn cảm xúc, biểu đồ xu hướng thời gian, biểu đồ cột từ khóa nổi bật và hiển thị phân trang bình luận cùng điểm số 5 sao.

### 2️⃣ Khởi chạy Telegram Bot
```bash
python telegram_bot.py
```
* **Hoạt động:** Bot lắng nghe tin nhắn chứa link YouTube từ người dùng gửi đến, tự động phân tích và phản hồi thông tin tổng hợp về điểm số, số sao, tỷ lệ cảm xúc và đề xuất xem một cách tức thời.

### 3️⃣ Khởi chạy Flask API Server (Dịch vụ Phân tán)
```bash
python api_server.py
```
* **Cổng chạy:** `5000`
* **Kiểm tra trạng thái (Health Check):**
  * Gửi request `GET` đến: `http://localhost:5000/api/status`
* **Gọi Phân Tích qua API (GET hoặc POST):**
  * Gửi request đến: `http://localhost:5000/api/analyze`
  * **Tham số:** `{ "url": "LINK_YOUTUBE", "lang": "vi", "max_comments": 200 }` (Lựa chọn `lang="en"` để kích hoạt phân tích đa ngôn ngữ).
