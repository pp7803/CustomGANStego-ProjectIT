@echo off
REM ============================================
REM Script Build Ung Dung CustomGANStego Windows
REM Bao gom: Kiem Tra Moi Truong - Cai Dat - Build - Huong Dan
REM ============================================

setlocal EnableDelayedExpansion

echo.
echo ========================================================
echo    Cong Cu Build Ung Dung CustomGANStego Windows
echo ========================================================
echo.

REM Lay duong dan thu muc script
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "VENV_DIR=%SCRIPT_DIR%venv"

REM ==================== BUOC 1: Kiem Tra Moi Truong ====================
echo [Buoc 1] Kiem Tra Moi Truong
echo --------------------------------------------------------

REM Kiem tra phien ban Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python!
    echo Vui long cai dat Python 3.10+ tu python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python: %PYTHON_VERSION%

REM Kiem tra moi truong ao
if exist "%VENV_DIR%" (
    echo [OK] Da tim thay moi truong ao: %VENV_DIR%
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo [INFO] Dang tao moi truong ao...
    echo.
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
    echo [OK] Da tao moi truong ao
)

echo.

REM ==================== BUOC 2: Cai Dat Dependencies ====================
echo [Buoc 2] Cai Dat Dependencies
echo --------------------------------------------------------

echo Dang nang cap pip...
python -m pip install --upgrade pip --quiet

echo Dang cai dat requirements...
pip install -r requirements.txt --quiet

REM Fix loi tuong thich scipy cho Python 3.13+ va PyInstaller
echo Kiem tra tuong thich scipy...
pip uninstall -y scipy 2>nul
echo Dang cai dat scipy tuong thich voi Python 3.13 va PyInstaller...
pip install "scipy>=1.14.0" --quiet

REM Kiem tra cac package quan trong
python -c "import torch" 2>nul
if %errorlevel% neq 0 (
    echo [CANH BAO] PyTorch chua duoc cai dat dung cach
    echo Dang cai dat PyTorch...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

python -c "import tkinter" 2>nul
if %errorlevel% neq 0 (
    echo [CANH BAO] tkinter khong kha dung
    echo Vui long cai dat tkinter cho phien ban Python cua ban
)

echo [OK] Tat ca dependencies da duoc cai dat
echo.

REM ==================== BUOC 3: Kiem Tra File Model ====================
echo [Buoc 3] Kiem Tra File Model
echo --------------------------------------------------------

if exist "%PROJECT_DIR%\results\model\" (
    dir /b "%PROJECT_DIR%\results\model\*.dat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Da tim thay file model trong results/model/
    ) else (
        echo [CANH BAO] Khong tim thay file model
        echo Vui long train model truoc: python train.py
    )
) else (
    echo [CANH BAO] Khong tim thay thu muc results/model/
    echo Vui long train model truoc: python train.py
)

echo.

REM ==================== BUOC 4: Kiem Tra File Ung Dung ====================
echo [Buoc 4] Kiem Tra File Ung Dung
echo --------------------------------------------------------

REM Kiem tra neu steganography_app.py ton tai, neu khong thi copy tu macOSApp
if not exist "%SCRIPT_DIR%steganography_app.py" (
    echo [INFO] Dang copy steganography_app.py tu macOSApp...
    copy "%PROJECT_DIR%\macOSApp\steganography_app.py" "%SCRIPT_DIR%steganography_app.py" >nul
    echo [OK] Da copy steganography_app.py
) else (
    REM Kiem tra neu file rong hoac qua nho
    for %%A in ("%SCRIPT_DIR%steganography_app.py") do (
        if %%~zA LSS 100 (
            echo [INFO] File rong, dang copy lai...
            copy /y "%PROJECT_DIR%\macOSApp\steganography_app.py" "%SCRIPT_DIR%steganography_app.py" >nul
            echo [OK] Da copy lai steganography_app.py
        ) else (
            echo [OK] Da tim thay steganography_app.py
        )
    )
)

echo.

REM ==================== BUOC 5: Build Ung Dung ====================
echo [Buoc 5] Build Ung Dung Windows
echo --------------------------------------------------------

if exist "dist" (
    echo Dang don dep ban build cu...
    rmdir /s /q dist 2>nul
)
if exist "build" (
    rmdir /s /q build 2>nul
)

echo Dang chay PyInstaller...
echo (Qua trinh nay co the mat vai phut)
echo.

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
    --collect-all torch ^
    --collect-all torchvision ^
    --collect-all imageio ^
    --collect-all skimage ^
    --collect-all scipy ^
    --collect-all PIL ^
    --collect-all matplotlib ^
    --hidden-import numbers ^
    --hidden-import scipy._lib ^
    --hidden-import scipy._lib.messagestream ^
    --hidden-import scipy._lib._ccallback_c ^
    --hidden-import scipy._lib._testutils ^
    --hidden-import scipy.stats ^
    --hidden-import scipy.stats._stats_py ^
    --hidden-import scipy.stats.distributions ^
    --hidden-import scipy.stats._distn_infrastructure ^
    --hidden-import scipy.stats._continuous_distns ^
    --hidden-import scipy.stats._discrete_distns ^
    --hidden-import scipy.stats._multivariate ^
    --hidden-import scipy.stats._constants ^
    --hidden-import scipy.stats._stats_mstats_common ^
    --hidden-import scipy.stats._resampling ^
    --hidden-import scipy.stats._entropy ^
    --hidden-import scipy.stats.morestats ^
    --hidden-import scipy.special ^
    --hidden-import scipy.special._ufuncs ^
    --hidden-import scipy.special._cdflib ^
    --hidden-import scipy.special.cython_special ^
    --hidden-import scipy.linalg ^
    --hidden-import scipy.linalg._fblas ^
    --hidden-import scipy.linalg._flapack ^
    --hidden-import scipy.linalg.cython_blas ^
    --hidden-import scipy.linalg.cython_lapack ^
    --hidden-import scipy.integrate ^
    --hidden-import scipy.interpolate ^
    --hidden-import scipy.ndimage ^
    --hidden-import scipy.ndimage._ni_support ^
    --hidden-import scipy.sparse ^
    --hidden-import scipy.sparse.linalg ^
    --hidden-import scipy.sparse.csgraph ^
    --hidden-import reedsolo ^
    --hidden-import Crypto ^
    --hidden-import Crypto.Cipher ^
    --hidden-import Crypto.Cipher.AES ^
    --hidden-import Crypto.Cipher.PKCS1_OAEP ^
    --hidden-import Crypto.PublicKey ^
    --hidden-import Crypto.PublicKey.RSA ^
    --hidden-import Crypto.Random ^
    --hidden-import Crypto.Util ^
    --hidden-import Crypto.Util.Padding ^
    --collect-all reedsolo ^
    --collect-all pycryptodome ^
    steganography_app.py

if errorlevel 1 (
    echo.
    echo [LOI] Build that bai!
    echo.
    pause
    exit /b 1
)

echo [OK] Build hoan tat thanh cong
echo.

REM ==================== BUOC 6: Kiem Tra Ket Qua ====================
echo [Buoc 6] Dong Goi Ung Dung
echo --------------------------------------------------------

if exist "dist\CustomGANStego.exe" (
    echo [OK] Da tao file thuc thi: dist\CustomGANStego.exe
    
    REM Lay kich thuoc file
    for %%A in ("dist\CustomGANStego.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo      Kich thuoc: ~!SIZE_MB! MB
) else (
    echo [LOI] Khong tim thay file thuc thi!
    pause
    exit /b 1
)

echo.

REM ==================== BUOC 7: Huong Dan Su Dung ====================
echo [Buoc 7] Huong Dan Su Dung
echo ========================================================
echo.
echo BUILD THANH CONG!
echo.
echo Vi Tri Dau Ra:
echo   dist\CustomGANStego.exe
echo.
echo De Chay:
echo   1. Double-click: dist\CustomGANStego.exe
echo   2. Hoac tu dong lenh: .\dist\CustomGANStego.exe
echo.
echo Phan Phoi:
echo   - Copy dist\CustomGANStego.exe den bat ky may Windows nao
echo   - Khong can cai dat Python tren may dich
echo   - File model da duoc tich hop trong file thuc thi
echo.
echo Tinh Nang:
echo   - Encode:  Giau tin vao anh
echo   - Decode:  Trich xuat tin tu anh
echo   - Reverse: Khoi phuc anh goc tu anh stego
echo   - GenRSA:  Tao cap khoa RSA
echo   - Compare: Tinh PSNR/SSIM metrics
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
