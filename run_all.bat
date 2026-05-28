@echo off
chcp 65001 >nul
title Khởi Chạy AI Comment Analyzer Pro - Đồng Thời Cả 2 Server

echo ===================================================================
echo           KHỞI CHẠY HỆ THỐNG AI COMMENT ANALYZER PRO
echo ===================================================================
echo.
echo [*] Đang khởi chạy Backend Flask API Server trong cửa sổ mới...
start "Backend Flask API (Port 5000)" cmd /k "cd BE_HTPTBinhLuan && .venv\Scripts\activate.bat && python api_server.py"

echo [*] Đang khởi chạy Frontend Vite React Server trong cửa sổ mới...
start "Frontend Vite React (Port 8080)" cmd /k "cd FE_HTPTBinhLuan && npm run dev"

echo.
echo ===================================================================
echo   [OK] CẢ 2 SERVER ĐANG ĐƯỢC KHỞI CHẠY ĐỒNG THỜI!
echo   - Giao diện Web chính (React): http://localhost:8080
echo   - Máy chủ Backend API (Flask): http://localhost:5000
echo.
echo   * Lưu ý: Không đóng hai cửa sổ lệnh mới mở để duy trì ứng dụng.
echo ===================================================================
echo.
pause
