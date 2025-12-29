@echo off
REM ============================================
REM Build script for CustomGANStego Windows App
REM Includes: Environment Check → Build → Usage Guide
REM ============================================

REM Enable UTF-8 encoding for proper emoji display
chcp 65001 >nul 2>&1

echo.
echo ========================================================
echo    CustomGANStego Windows Application Builder
echo ========================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "PRJVENV_DIR=%PROJECT_DIR%\prjvenv"

REM ==================== STEP 1: Environment Check ====================
echo [Step 1] Checking Environment
echo --------------------------------------------------------

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python: %PYTHON_VERSION%

REM Check virtual environment
if exist "%PRJVENV_DIR%" (
    echo [OK] Virtual environment found
    call "%PRJVENV_DIR%\Scripts\activate.bat"
) else (
    echo [WARN] Virtual environment not found at: %PRJVENV_DIR%
    echo.
    set /p CREATE_VENV="Create virtual environment now? (y/n): "
    if /i "%CREATE_VENV%"=="y" (
        echo Creating virtual environment...
        cd /d "%PROJECT_DIR%"
        python -m venv prjvenv
        call prjvenv\Scripts\activate.bat
        cd /d "%SCRIPT_DIR%"
        echo [OK] Virtual environment created
    ) else (
        echo Cannot continue without virtual environment
        pause
        exit /b 1
    )
)

echo.

REM ==================== STEP 2: Install Dependencies ====================
echo [Step 2] Installing Dependencies
echo --------------------------------------------------------

echo Upgrading pip...
python -m pip install --upgrade pip --quiet

echo Installing requirements...
pip install -r requirements.txt --quiet

REM Check critical packages
python -c "import torch" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] PyTorch not installed correctly
    echo Installing PyTorch...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

python -c "import tkinter" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] tkinter not available
    echo Please install tkinter for your Python version
)

echo [OK] All dependencies installed
echo.

REM ==================== STEP 3: Check Model Files ====================
echo [Step 3] Checking Model Files
echo --------------------------------------------------------

if exist "%PROJECT_DIR%\results\model\" (
    dir /b "%PROJECT_DIR%\results\model\*.dat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Model files found in results/model/
    ) else (
        echo [WARN] No model files found
        echo Please train a model first: python train.py
    )
) else (
    echo [WARN] results/model/ directory not found
    echo Please train a model first: python train.py
)

echo.

REM ==================== STEP 4: Build Application ====================
echo [Step 4] Building Windows Application
echo --------------------------------------------------------

if exist "dist" (
    echo Cleaning old build...
    rmdir /s /q dist 2>nul
)
if exist "build" (
    rmdir /s /q build 2>nul
)

echo Running PyInstaller...
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
    echo [ERROR] Build failed!
    echo.
    pause
    exit /b 1
)

echo [OK] Build completed successfully
echo.

REM ==================== STEP 5: Create Installer (Optional) ====================
echo [Step 5] Package Application
echo --------------------------------------------------------

if exist "dist\CustomGANStego.exe" (
    echo [OK] Executable created: dist\CustomGANStego.exe
    
    REM Get file size
    for %%A in ("dist\CustomGANStego.exe") do set SIZE=%%~zA
    set /a SIZE_MB=%SIZE% / 1048576
    echo      Size: ~%SIZE_MB% MB
) else (
    echo [ERROR] Executable not found!
    pause
    exit /b 1
)

echo.

REM ==================== STEP 6: Usage Guide ====================
echo [Step 6] Usage Guide
echo ========================================================
echo.
echo BUILD SUCCESSFUL!
echo.
echo Output Location:
echo   dist\CustomGANStego.exe
echo.
echo To Run:
echo   1. Double-click: dist\CustomGANStego.exe
echo   2. Or from command: .\dist\CustomGANStego.exe
echo.
echo Distribution:
echo   - Copy dist\CustomGANStego.exe to any Windows PC
echo   - No Python installation required on target PC
echo   - Model files are bundled inside the executable
echo.
echo Note:
echo   - First run may take 10-15 seconds to extract
echo   - Antivirus may flag the exe (false positive)
echo   - Add exception if needed
echo.
echo Troubleshooting:
echo   - If app doesn't start, run from command prompt to see errors
echo   - Check Windows Defender / Antivirus logs
echo   - Ensure model files exist in results\model\
echo.

pause
