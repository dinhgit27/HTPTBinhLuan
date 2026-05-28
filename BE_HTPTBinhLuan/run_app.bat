@echo off
chcp 65001 >nul
title Khởi chạy AI Comment Analyzer Pro

echo ===================================================
echo   CÀI ĐẶT VÀ KHỞI CHẠY AI COMMENT ANALYZER PRO
echo ===================================================
echo.

:: 1. Kiểm tra xem máy đã cài Python chưa
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python trên máy tính.
    echo Vui lòng tải và cài đặt Python từ https://www.python.org/downloads/
    echo (Lưu ý quan trọng: Nhớ tích vào ô "Add python.exe to PATH" khi cài đặt)
    echo.
    pause
    exit /b
)
echo [OK] Đã tìm thấy Python.

:: 2. Tạo môi trường ảo (Virtual Environment) nếu chưa có
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [*] Đang tạo môi trường ảo (.venv) để chạy độc lập...
    python -m venv .venv
)

:: 3. Kích hoạt môi trường ảo
echo.
echo [*] Đang kích hoạt môi trường ảo...
call .venv\Scripts\activate.bat

:: 4. Cập nhật pip và cài đặt thư viện
echo.
echo [*] Đang kiểm tra và cài đặt các thư viện cần thiết...
echo (Quá trình này có thể mất vài phút trong lần chạy đầu tiên, vui lòng đợi...)
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

:: 5. Khởi chạy ứng dụng
echo.
echo ===================================================
echo [*] HOÀN TẤT CÀI ĐẶT. ĐANG KHỞI CHẠY API SERVER...
echo ===================================================
python api_server.py

pause
