# 🎨 AI Comment Analyzer Pro - Frontend Service

Thư mục này chứa mã nguồn **Frontend** của hệ thống phân tích cảm xúc bình luận, được phát triển bằng React, Vite, TypeScript, Tailwind CSS và UI components của shadcn/ui.

> [!TIP]
> Để xem hướng dẫn đầy đủ cách cài đặt và khởi chạy cho cả **Frontend** và **Backend**, vui lòng đọc tài liệu **[README.md ở thư mục gốc của dự án](../README.md)**.

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh Frontend

1. Đảm bảo bạn đã cài đặt **Node.js (v18+)** và **npm**.
2. Mở Terminal tại thư mục `FE_HTPTBinhLuan`:
   ```bash
   cd FE_HTPTBinhLuan
   ```
3. Cài đặt các thư viện Node.js:
   ```bash
   npm install
   ```
4. Khởi chạy máy chủ phát triển (Vite Dev Server):
   ```bash
   npm run dev
   ```
5. Mở trình duyệt và truy cập vào địa chỉ hiển thị trên màn hình:
   * Mặc định: [http://localhost:5173](http://localhost:5173)

---

## ⚙️ Cấu Hình Kết Nối API

* Frontend được cấu hình mặc định để giao tiếp với Flask API Server tại `http://localhost:5000`.
* Hãy đảm bảo Flask Server của Backend đã được chạy thành công trước khi tiến hành phân tích các liên kết bình luận trên giao diện.
