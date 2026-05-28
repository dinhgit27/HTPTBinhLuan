@echo off
chcp 65001 >nul
title Khởi Chạy AI Comment Analyzer Pro - Đồng Thời Cả 2 Server

echo ===================================================================
2: echo           KHỞI CHẠY HỆ THỐNG AI COMMENT ANALYZER PRO
3: echo ===================================================================
4: echo.
5: echo [*] Đang khởi chạy Backend Flask API Server trong cửa sổ mới...
6: start "Backend Flask API (Port 5000)" cmd /k "cd BE_HTPTBinhLuan && .venv\Scripts\activate.bat && python api_server.py"
7: 
8: echo [*] Đang khởi chạy Frontend Vite React Server trong cửa sổ mới...
9: start "Frontend Vite React (Port 8080)" cmd /k "cd FE_HTPTBinhLuan && npm run dev"
10: 
11: echo.
12: echo ===================================================================
13: echo   [OK] CẢ 2 SERVER ĐANG ĐƯỢC KHỞI CHẠY ĐỒNG THỜI!
14: echo   - Giao diện Web chính (React): http://localhost:8080
15: echo   - Máy chủ Backend API (Flask): http://localhost:5000
16: echo.
17: echo   * Lưu ý: Không đóng hai cửa sổ lệnh mới mở để duy trì ứng dụng.
18: echo ===================================================================
19: echo.
20: pause
