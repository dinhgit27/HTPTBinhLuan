# ⚙️ AI Comment Analyzer Pro - Backend Service

Thư mục này chứa mã nguồn **Backend** của hệ thống phân tích cảm xúc bình luận, được phát triển bằng ngôn ngữ Python sử dụng framework Flask kết hợp với các mô hình trí tuệ nhân tạo (PhoBERT).

> [!TIP]
> Để xem hướng dẫn đầy đủ cách cài đặt và khởi chạy cho cả **Frontend** và **Backend**, vui lòng đọc tài liệu **[README.md ở thư mục gốc của dự án](../README.md)**.

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh Backend

### Cách 1: Khởi chạy nhanh (Chỉ dành cho Windows)
* Nhấp đúp chuột trực tiếp vào file **`run_app.bat`** tại thư mục này để hệ thống tự động cài đặt các thư viện và chạy Flask Server.

### Cách 2: Khởi chạy thủ công qua Terminal
1. Mở Terminal (CMD / PowerShell / bash) tại thư mục `BE_HTPTBinhLuan`:
   ```bash
   cd BE_HTPTBinhLuan
   ```
2. Tạo môi trường ảo `.venv` (nếu chưa có):
   ```bash
   python -m venv .venv
   ```
3. Kích hoạt môi trường ảo:
   * **Windows (CMD):** `.venv\Scripts\activate.bat`
   * **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
   * **macOS / Linux:** `source .venv/bin/activate`
4. Cài đặt các gói thư viện cần thiết:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Huấn luyện thử nghiệm mô hình cục bộ dự phòng (Chỉ chạy một lần đầu tiên nếu muốn sinh file mô hình dự phòng):
   ```bash
   python main.py
   ```
6. Khởi chạy Flask Server:
   ```bash
   python api_server.py
   ```
   *Flask Server sẽ chạy mặc định tại cổng `5000` (`http://localhost:5000`).*

---

## 🔌 Danh Sách Các Endpoint API Chính

* **Kiểm tra trạng thái hệ thống (GET):**
  `http://localhost:5000/api/status`
* **Kiểm tra trạng thái tải mô hình PhoBERT (GET):**
  `http://localhost:5000/api/model-status`
* **Gửi yêu cầu phân tích bình luận (POST):**
  `http://localhost:5000/api/analyze`
  * Body (JSON):
    ```json
    {
      "url": "ĐƯỜNG_DẪN_VIDEO_YOUTUBE",
      "max_comments": 1000
    }
    ```
