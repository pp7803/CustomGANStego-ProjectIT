@echo off
REM ============================================
REM Script build cho Ứng Dụng CustomGANStego Windows
REM Bao gồm: Kiểm Tra Môi Trường → Build → Hướng Dẫn Sử Dụng
REM ============================================

REM Enable UTF-8 encoding for proper emoji display
chcp 65001 >nul 2>&1

echo.
echo ========================================================
echo    Công Cụ Build Ứng Dụng Windows CustomGANStego
echo ========================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "PRJVENV_DIR=%PROJECT_DIR%\prjvenv"

REM ==================== BƯỚC 1: Kiểm Tra Môi Trường ====================
echo [Bước 1] Kiểm Tra Môi Trường
echo --------------------------------------------------------

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python!
    echo Vui lòng cài đặt Python 3.8 trở lên từ python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python: %PYTHON_VERSION%

REM Check virtual environment
if exist "%PRJVENV_DIR%" (
    echo [OK] Đã tìm thấy môi trường ảo
    call "%PRJVENV_DIR%\Scripts\activate.bat"
) else (
    echo [CẢNH BÁO] Không tìm thấy môi trường ảo tại: %PRJVENV_DIR%
    echo.
    set /p CREATE_VENV="Tạo môi trường ảo ngay bây giờ? (y/n): "
    if /i "%CREATE_VENV%"=="y" (
        echo Đang tạo môi trường ảo...
        cd /d "%PROJECT_DIR%"
        python -m venv prjvenv
        call prjvenv\Scripts\activate.bat
        cd /d "%SCRIPT_DIR%"
        echo [OK] Đã tạo môi trường ảo
    ) else (
        echo Không thể tiếp tục mà không có môi trường ảo
        pause
        exit /b 1
    )
)

echo.

REM ==================== BƯỚC 2: Cài Đặt Dependencies ====================
echo [Bước 2] Cài Đặt Dependencies
echo --------------------------------------------------------

echo Đang nâng cấp pip...
python -m pip install --upgrade pip --quiet

echo Đang cài đặt requirements...
pip install -r requirements.txt --quiet

REM Check critical packages
python -c "import torch" 2>nul
if %errorlevel% neq 0 (
    echo [CẢNH BÁO] PyTorch chưa được cài đặt đúng cách
    echo Đang cài đặt PyTorch...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

python -c "import tkinter" 2>nul
if %errorlevel% neq 0 (
    echo [CẢNH BÁO] tkinter không khả dụng
    echo Vui lòng cài đặt tkinter cho phiên bản Python của bạn
)

echo [OK] Tất cả dependencies đã được cài đặt
echo.

REM ==================== BƯỚC 3: Kiểm Tra File Model ====================
echo [Bước 3] Kiểm Tra File Model
echo --------------------------------------------------------

if exist "%PROJECT_DIR%\results\model\" (
    dir /b "%PROJECT_DIR%\results\model\*.dat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Đã tìm thấy file model trong results/model/
    ) else (
        echo [CẢNH BÁO] Không tìm thấy file model
        echo Vui lòng huấn luyện model trước: python train.py
    )
) else (
    echo [CẢNH BÁO] Không tìm thấy thư mục results/model/
    echo Vui lòng huấn luyện model trước: python train.py
)

echo.

REM ==================== BƯỚC 4: Build Ứng Dụng ====================
echo [Bước 4] Build Ứng Dụng Windows
echo --------------------------------------------------------

if exist "dist" (
    echo Đang dọn dẹp bản build cũ...
    rmdir /s /q dist 2>nul
)
if exist "build" (
    rmdir /s /q build 2>nul
)

echo Đang chạy PyInstaller...
python -m PyInstaller --clean ^
    --name=CustomGANStego ^
    --windowed ^
    --onefile ^
    --add-data "%PROJECT_DIR%\results\model;results\model" ^
    --add-data "%PROJECT_DIR%\encoder.py;." ^
    --add-data "%PROJECT_DIR%\decoder.py;." ^
    --add-data "%PROJECT_DIR%\critic.py;." ^
    --add-data "%PROJECT_DIR%\reverse_decoder.py;." ^
    --add-data "%PROJECT_DIR%\enhancedstegan.py;." ^
    --hidden-import torch ^
    --hidden-import torchvision ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --hidden-import skimage ^
    --hidden-import Crypto ^
    --hidden-import imageio ^
    --hidden-import imageio.core ^
    --hidden-import imageio.plugins ^
    --hidden-import reedsolo ^
    --hidden-import zlib ^
    --hidden-import matplotlib ^
    --collect-all torch ^
    --collect-all torchvision ^
    --collect-all imageio ^
    steganography_app.py

if errorlevel 1 (
    echo.
    echo [LỖI] Build thất bại!
    echo.
    pause
    exit /b 1
)

echo [OK] Hoàn tất build thành công
echo.

REM ==================== BƯỚC 5: Tạo Gói Ứng Dụng (Tùy chọn) ====================
echo [Bước 5] Đóng Gói Ứng Dụng
echo --------------------------------------------------------

if exist "dist\CustomGANStego.exe" (
    echo [OK] Đã tạo file thực thi: dist\CustomGANStego.exe
    
    REM Get file size
    for %%A in ("dist\CustomGANStego.exe") do set SIZE=%%~zA
    set /a SIZE_MB=%SIZE% / 1048576
    echo      Kích thước: ~%SIZE_MB% MB
) else (
    echo [LỖI] Không tìm thấy file thực thi!
    pause
    exit /b 1
)

echo.

REM ==================== BƯỚC 6: Hướng Dẫn Sử Dụng ====================
echo [Bước 6] Hướng Dẫn Sử Dụng
echo ========================================================
echo.
echo BUILD THÀNH CÔNG!
echo.
echo Vị Trí Đầu Ra:
echo   dist\CustomGANStego.exe
echo.
echo Để Chạy:
echo   1. Double-click: dist\CustomGANStego.exe
echo   2. Hoặc từ lệnh: .\dist\CustomGANStego.exe
echo.
echo Phân Phối:
echo   - Sao chép dist\CustomGANStego.exe vào bất kỳ PC Windows nào
echo   - Không cần cài đặt Python trên PC đích
echo   - File model đã được tích hợp trong file thực thi
echo.
echo Lưu Ý:
echo   - Lần chạy đầu có thể mất 10-15 giây để giải nén
echo   - Antivirus có thể chặn exe (false positive)
echo   - Thêm ngoại lệ nếu cần
echo.
echo Khắc Phục Sự Cố:
echo   - Nếu app không khởi động, chạy từ command prompt để xem lỗi
echo   - Kiểm tra Windows Defender / log Antivirus
echo   - Đảm bảo file model tồn tại trong results\model\
echo.

pause
