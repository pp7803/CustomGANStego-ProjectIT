@echo off
REM ============================================
REM All-in-One Build Script cho Windows App
REM ============================================
REM Chuc nang:
REM - Tu dong tao va cai dat venv rieng
REM - Kiem tra dependencies
REM - Build app executable
REM - Huong dan su dung
REM ============================================

REM Enable UTF-8 encoding for proper emoji display
chcp 65001 >nul 2>&1

echo.
echo ========================================================
echo    CustomGANStego Windows App Builder (All-in-One)
echo ========================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "VENV_DIR=%SCRIPT_DIR%venv"

REM Parse arguments
set "SETUP_ONLY=0"
if "%1"=="--setup-only" set "SETUP_ONLY=1"
if "%1"=="-s" set "SETUP_ONLY=1"

REM ==================== BUOC 1: Kiem Tra & Setup Moi Truong ====================
echo [Buoc 1] Kiem Tra ^& Setup Moi Truong
echo --------------------------------------------------------

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python!
    echo Vui long cai dat Python 3.8 tro len tu python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python: %PYTHON_VERSION%

REM Check and create virtual environment
if exist "%VENV_DIR%" (
    echo [OK] Tim thay moi truong ao rieng cua windowsApp
    call "%VENV_DIR%\Scripts\activate.bat"
    
    REM Kiem tra venv co bi hong khong
    if not exist "%VENV_DIR%\Scripts\pip.exe" (
        echo [CANH BAO] Moi truong ao bi hong, dang tao lai...
        rmdir /s /q "%VENV_DIR%"
        python -m venv "%VENV_DIR%"
        call "%VENV_DIR%\Scripts\activate.bat"
        echo [OK] Da tao lai moi truong ao
    )
) else (
    echo.
    echo Chua co moi truong ao rieng
    echo Dang tu dong tao moi truong ao tai: %VENV_DIR%
    echo.
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
    echo [OK] Da tao moi truong ao rieng
    echo.
    echo Dang nang cap pip...
    python -m pip install --upgrade pip -q
    echo [OK] Da nang cap pip
)

REM Kiem tra venv da duoc activate
if "%VIRTUAL_ENV%"=="" (
    echo [LOI] Khong the kich hoat moi truong ao
    pause
    exit /b 1
)

echo [OK] Moi truong ao: %VIRTUAL_ENV%

echo.

REM ==================== BUOC 2: Kiem Tra & Cai Dat Dependencies ====================
echo [Buoc 2] Kiem Tra ^& Cai Dat Dependencies
echo --------------------------------------------------------

echo Dang kiem tra dependencies...
python -c "import torch, torchvision, PIL, numpy, imageio, reedsolo, PyInstaller; from skimage.metrics import peak_signal_noise_ratio; import matplotlib; print('[OK] Tat ca dependencies da co')" 2>nul

if %errorlevel% neq 0 (
    echo Phat hien thieu dependencies, dang tu dong cai dat...
    echo.
    
    echo Nang cap pip...
    python -m pip install --upgrade pip -q
    
    echo Cai dat packages tu requirements.txt...
    pip install -r requirements.txt
    
    if %errorlevel% neq 0 (
        echo [LOI] Cai dat dependencies that bai
        echo.
        echo Thu cai thu cong:
        echo   %VENV_DIR%\Scripts\activate.bat
        echo   pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo [OK] Da cai dat xong, dang kiem tra lai...
    python -c "import torch, torchvision; from PIL import Image; import numpy, imageio, reedsolo; from skimage.metrics import peak_signal_noise_ratio; import matplotlib, PyInstaller; print('[OK] Tat ca dependencies da OK')"
    
    if %errorlevel% neq 0 (
        echo [LOI] Van con loi sau khi cai dat
        pause
        exit /b 1
    )
) else (
    echo [OK] Tat ca dependencies da san sang
)

echo.

REM Neu chi setup, dung lai o day
if "%SETUP_ONLY%"=="1" (
    echo.
    echo ========================================================
    echo [OK] Setup Hoan Tat!
    echo ========================================================
    echo.
    echo Moi truong ao: %VENV_DIR%
    echo.
    echo De su dung:
    echo   %VENV_DIR%\Scripts\activate.bat
    echo.
    echo De build app:
    echo   build_app.bat
    echo.
    echo De deactivate:
    echo   deactivate
    echo.
    pause
    exit /b 0
)

REM ==================== BUOC 3: Kiem Tra File Model ====================
echo [Buoc 3] Kiem Tra File Model
echo --------------------------------------------------------

if exist "%PROJECT_DIR%\results\model\" (
    dir /b "%PROJECT_DIR%\results\model\*.dat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Da tim thay file model trong results/model/
    ) else (
        echo [CANH BAO] Khong tim thay file model
        echo Vui long huan luyen model truoc: python train.py
    )
) else (
    echo [CANH BAO] Khong tim thay thu muc results/model/
    echo Vui long huan luyen model truoc: python train.py
)

echo.

REM ==================== BUOC 4: Build Ung Dung ====================
echo [Buoc 4] Build Ung Dung Windows
echo --------------------------------------------------------

REM Dong app neu dang chay
echo Kiem tra va dong process CustomGANStego neu dang chay...
tasklist /FI "IMAGENAME eq CustomGANStego.exe" 2>nul | find /I "CustomGANStego.exe" >nul
if %errorlevel% equ 0 (
    echo Dang dong CustomGANStego.exe...
    taskkill /F /IM CustomGANStego.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM Xoa cac file build cu
if exist "dist" (
    echo Dang xoa thu muc dist cu...
    attrib -r -h -s "dist\*.*" /s /d >nul 2>&1
    rmdir /s /q "dist" 2>nul
    timeout /t 1 /nobreak >nul
)

if exist "build" (
    echo Dang xoa thu muc build cu...
    attrib -r -h -s "build\*.*" /s /d >nul 2>&1
    rmdir /s /q "build" 2>nul
    timeout /t 1 /nobreak >nul
)

if exist "CustomGANStego.spec" (
    echo Xoa spec file cu...
    del /f /q "CustomGANStego.spec" 2>nul
)

echo Don dep hoan tat
echo.

echo Dang chay PyInstaller...
python -m PyInstaller --clean --name=CustomGANStego --windowed --onefile --add-data "%PROJECT_DIR%\results\model;results\model" --add-data "%PROJECT_DIR%\encoder.py;." --add-data "%PROJECT_DIR%\decoder.py;." --add-data "%PROJECT_DIR%\critic.py;." --add-data "%PROJECT_DIR%\reverse_decoder.py;." --add-data "%PROJECT_DIR%\enhancedstegan.py;." --hidden-import torch --hidden-import torchvision --hidden-import PIL --hidden-import numpy --hidden-import skimage --hidden-import Crypto --hidden-import imageio --hidden-import imageio.core --hidden-import imageio.plugins --hidden-import reedsolo --hidden-import matplotlib --hidden-import psutil --collect-all torch --collect-all torchvision --collect-all imageio steganography_app.py

if errorlevel 1 (
    echo.
    echo [LOI] Build that bai!
    echo.
    echo Debug:
    echo   %VENV_DIR%\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo   python -m PyInstaller steganography_app.py
    echo.
    pause
    exit /b 1
)

echo [OK] Hoan tat build thanh cong
echo.

REM ==================== BUOC 5: Tao Goi Ung Dung ====================
echo [Buoc 5] Dong Goi Ung Dung
echo --------------------------------------------------------

if exist "dist\CustomGANStego.exe" (
    echo [OK] Da tao file thuc thi: dist\CustomGANStego.exe
    
    REM Get file size
    for %%A in ("dist\CustomGANStego.exe") do set SIZE=%%~zA
    set /a SIZE_MB=%SIZE% / 1048576
    echo      Kich thuoc: ~%SIZE_MB% MB
) else (
    echo [LOI] Khong tim thay file thuc thi!
    pause
    exit /b 1
)

echo.

REM ==================== BUOC 6: Huong Dan Su Dung ====================
echo [Buoc 6] Huong Dan Su Dung
echo ========================================================
echo.
echo [OK] BUILD THANH CONG!
echo.
echo Vi Tri Dau Ra:
echo   dist\CustomGANStego.exe
echo.
echo De Chay:
echo   1. Double-click: dist\CustomGANStego.exe
echo   2. Hoac tu lenh: .\dist\CustomGANStego.exe
echo.
echo Phan Phoi:
echo   - Sao chep dist\CustomGANStego.exe vao bat ky PC Windows nao
echo   - Khong can cai dat Python tren PC dich
echo   - File model da duoc tich hop trong file thuc thi
echo.
echo Luu Y:
echo   - Lan chay dau co the mat 10-15 giay de giai nen
echo   - Antivirus co the chan exe (false positive)
echo   - Them ngoai le neu can
echo.
echo Khac Phuc Su Co:
echo   - Neu app khong khoi dong, chay tu command prompt de xem loi
echo   - Kiem tra Windows Defender / log Antivirus
echo   - Dam bao file model ton tai trong results\model\
echo.

pause
