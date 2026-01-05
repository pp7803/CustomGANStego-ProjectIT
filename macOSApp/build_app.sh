#!/bin/bash

set -e

# ==========================================
# All-in-One Build Script cho macOS App
# ==========================================
# Chuc nang:
# - Tu dong tao va cai dat venv rieng
# - Kiem tra dependencies
# - Build app bundle
# - Tao DMG/ZIP installer
# ==========================================

echo "=========================================="
echo "CustomGANStego macOS App Builder"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/venv"

# Parse arguments
SETUP_ONLY=false
if [ "$1" = "--setup-only" ] || [ "$1" = "-s" ]; then
    SETUP_ONLY=true
fi

echo "Buoc 1: Kiem Tra & Setup Moi Truong"
echo "----------------------------------------"

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Khong tim thay Python 3!"
    echo "   Vui long cai dat Python 3.8 tro len"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python: $PYTHON_VERSION"

# Kiểm tra và tạo virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "✓ Tim thay moi truong ao rieng: $VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Kiểm tra xem có cần cài đặt lại không
    if [ ! -f "$VENV_DIR/bin/pip" ]; then
        echo "⚠️  Moi truong ao bi hu hong, dang tao lai..."
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        echo "✓ Da tao lai moi truong ao"
    fi
else
    echo ""
    echo "Chua co moi truong ao rieng"
    echo "Dang tu dong tao moi truong ao tai: $VENV_DIR"
    echo ""
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    echo "✓ Da tao moi truong ao rieng"
    echo ""
    echo "Dang nang cap pip..."
    pip install --upgrade pip -q
    echo "✓ Da nang cap pip"
fi

# Kiểm tra venv đã được activate
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Khong the kich hoat moi truong ao"
    exit 1
fi

echo "✓ Moi truong ao: $VIRTUAL_ENV"

echo ""
echo "Buoc 2: Kiem Tra & Cai Dat Dependencies"
echo "----------------------------------------"

echo "Dang kiem tra dependencies..."

# Tạm thời tắt exit on error để có thể xử lý kết quả
set +e

python3 - <<EOF
import sys
errors = []
installed = []

packages = {
    "tkinter": ("tkinter", True),
    "torch": ("torch", True),
    "Pillow": ("PIL", True),
    "numpy": ("numpy", True),
    "scikit-image": ("skimage.metrics", True),
    "matplotlib": ("matplotlib", True),
    "pycryptodome": ("Crypto.PublicKey", False),
    "imageio": ("imageio", True),
    "reedsolo": ("reedsolo", True),
    "pyinstaller": ("PyInstaller", True),
}

for name, (module, required) in packages.items():
    try:
        if "." in module:
            parts = module.split(".")
            mod = __import__(parts[0])
            for part in parts[1:]:
                mod = getattr(mod, part)
        else:
            __import__(module)
        installed.append(name)
        print(f"✓ {name}")
    except ImportError:
        if required:
            errors.append(name)
            print(f"✗ {name} - REQUIRED")
        else:
            print(f"⚠ {name} - OPTIONAL")

if errors:
    print(f"\nThieu {len(errors)} goi bat buoc")
    sys.exit(1)
else:
    print(f"\n✓ Tat ca {len(installed)} dependencies da san sang")
    sys.exit(0)
EOF

CHECK_RESULT=$?

# Bật lại exit on error
set -e

if [ $CHECK_RESULT -ne 0 ]; then
    echo ""
    echo "Dang tu dong cai dat dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Cai dat dependencies that bai"
        echo ""
        echo "Thu cai thu cong:"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        echo ""
        exit 1
    fi
    
    echo ""
    echo "✓ Da cai dat xong, dang kiem tra lai..."
    python3 - <<EOF
import sys
try:
    import torch, torchvision
    from PIL import Image
    import numpy, imageio, reedsolo
    from skimage.metrics import peak_signal_noise_ratio
    import matplotlib, PyInstaller
    print("✓ Xac nhan tat ca dependencies da OK")
except ImportError as e:
    print(f"✗ Van con thieu package: {e}")
    sys.exit(1)
EOF
    
    if [ $? -ne 0 ]; then
        echo "❌ Van con loi sau khi cai dat"
        exit 1
    fi
    echo "✓ Dependencies hoan tat"
fi

# Nếu chỉ setup, dừng lại ở đây
if [ "$SETUP_ONLY" = true ]; then
    echo ""
    echo "=========================================="
    echo "✅ Setup Hoan Tat!"
    echo "=========================================="
    echo ""
    echo "Moi truong ao: $VENV_DIR"
    echo ""
    echo "De su dung:"
    echo "  source venv/bin/activate"
    echo ""
    echo "De build app:"
    echo "  ./build_app.sh"
    echo ""
    echo "De deactivate:"
    echo "  deactivate"
    echo ""
    exit 0
fi

echo ""
echo "Buoc 3: Kiem Tra File Model"
echo "----------------------------------------"

echo "Dang kiem tra file model..."
MODEL_DIR="$PROJECT_DIR/results/model"
if [ -d "$MODEL_DIR" ]; then
    MODEL_COUNT=$(ls -1 "$MODEL_DIR"/*.dat 2>/dev/null | wc -l)
    if [ $MODEL_COUNT -gt 0 ]; then
        echo "Tim thay $MODEL_COUNT file model"
        BEST_MODEL=$(ls -1 "$MODEL_DIR"/*.dat | sort | tail -n 1 | xargs basename)
        echo "   Tot nhat: $BEST_MODEL"
    else
        echo "Khong tim thay file .dat model trong $MODEL_DIR"
        echo "   App se hoat dong nhung co the chat luong giam"
    fi
else
    echo "Khong tim thay thu muc model: $MODEL_DIR"
    echo "   Chay 'python train.py' de huan luyen model truoc"
fi

python3 - <<EOF
import sys
sys.path.insert(0, "$PROJECT_DIR")
try:
    from enhancedstegan import encode_message, decode_message, reverse_hiding
    print("Module enhancedstegan OK")
except ImportError as e:
    print(f"Module enhancedstegan THAT BAI: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Kiem tra module du an that bai"
    exit 1
fi

echo ""
echo "✅ Hoan thanh kiem tra moi truong!"
echo ""

echo "Buoc 4: Build Ung Dung"
echo "----------------------------------------"

echo "Dang don dep cac ban build cu..."
cd "$SCRIPT_DIR"
rm -rf build dist __pycache__ *.spec.bak

echo "Dang build voi PyInstaller..."
pyinstaller steganography_app.spec

if [ -d "dist/CustomGANStego.app" ]; then
    echo ""
    echo "=============================================="
    echo "✅ BUILD THANH CONG!"
    echo "=============================================="
    
    APP_SIZE=$(du -sh "dist/CustomGANStego.app" | awk '{print $1}')
    echo ""
    echo "Chi Tiet Ung Dung:"
    echo "   Vi tri: $SCRIPT_DIR/dist/CustomGANStego.app"
    echo "   Kich thuoc: $APP_SIZE"
    echo ""
    
    echo "Buoc 5: Tao Goi Phan Phoi"
    echo "----------------------------------------"
    
    echo "Chon dinh dang phan phoi:"
    echo "  1) ZIP archive (khuyen nghi - nho hon, nhanh hon)"
    echo "  2) DMG disk image (trinh cai dat macOS truyen thong)"
    echo "  3) Bo qua dong goi (chi dung .app truc tiep)"
    read -p "Nhap lua chon [1-3] (mac dinh: 1): " PACKAGE_CHOICE
    PACKAGE_CHOICE=${PACKAGE_CHOICE:-1}
    
    if [ "$PACKAGE_CHOICE" = "1" ]; then
        ZIP_NAME="CustomGANStego-macOS.zip"
        ZIP_PATH="$SCRIPT_DIR/dist/$ZIP_NAME"
        rm -f "$ZIP_PATH"
        
        echo "Dang tao file ZIP..."
        cd "$SCRIPT_DIR/dist"
        zip -r -q "$ZIP_NAME" CustomGANStego.app
        cd "$SCRIPT_DIR"
        
        if [ -f "$ZIP_PATH" ]; then
            ZIP_SIZE=$(du -sh "$ZIP_PATH" | awk '{print $1}')
            echo "Tao ZIP thanh cong!"
            echo "   Vi tri: $ZIP_PATH"
            echo "   Kich thuoc: $ZIP_SIZE"
        else
            echo "Tao ZIP that bai"
        fi
        
    elif [ "$PACKAGE_CHOICE" = "2" ]; then
        DMG_NAME="CustomGANStego-macOS.dmg"
        DMG_PATH="$SCRIPT_DIR/dist/$DMG_NAME"
        TEMP_DMG="$SCRIPT_DIR/dist/temp.dmg"
        VOLUME_NAME="CustomGANStego"
        
        rm -f "$DMG_PATH" "$TEMP_DMG"
        
        echo "Dang tao disk image (co the mat mot chut thoi gian)..."
        
        hdiutil create -size 3000m -fs HFS+ -volname "$VOLUME_NAME" "$TEMP_DMG" > /dev/null 2>&1
        
        MOUNT_DIR=$(hdiutil attach "$TEMP_DMG" | grep "/Volumes/$VOLUME_NAME" | awk '{print $3}')
        
        if [ -z "$MOUNT_DIR" ]; then
            echo "Khong the mount DMG tam thoi"
            echo "   Bo qua tao DMG"
        else
            echo "Dang copy app vao DMG..."
            cp -R "dist/CustomGANStego.app" "$MOUNT_DIR/"
            
            ln -s /Applications "$MOUNT_DIR/Applications"
            
            cp README.md "$MOUNT_DIR/README.txt"
            
            cat > "$MOUNT_DIR/INSTALL.txt" << 'EOL'
CustomGANStego - Installation Instructions
==========================================

1. Drag "CustomGANStego.app" to the "Applications" folder
2. Open from Launchpad or Applications folder
3. If macOS blocks the app, run in Terminal:
   xattr -cr /Applications/CustomGANStego.app

Features:
- Encode: Hide messages in images
- Decode: Extract hidden messages
- Reverse: Recover original images
- GenRSA: Generate encryption keys
- Compare: Calculate image metrics

For more information, see README.txt

Enjoy!
EOL
            
            echo "Dang hoan thien DMG..."
            hdiutil detach "$MOUNT_DIR" > /dev/null 2>&1
            
            hdiutil convert "$TEMP_DMG" -format UDZO -o "$DMG_PATH" > /dev/null 2>&1
            rm -f "$TEMP_DMG"
            
            if [ -f "$DMG_PATH" ]; then
                DMG_SIZE=$(du -sh "$DMG_PATH" | awk '{print $1}')
                echo "Tao DMG thanh cong!"
                echo "   Vi tri: $DMG_PATH"
                echo "   Kich thuoc: $DMG_SIZE"
            else
                echo "Tao DMG that bai"
            fi
        fi
    else
        echo "Bo qua tao goi"
        echo "   Su dung dist/CustomGANStego.app truc tiep"
    fi
    
    echo ""
    
    echo "Buoc 6: Phan Phoi & Su Dung"
    echo "=============================================="
    echo ""
    echo "Cac File Da Tao:"
    echo ""
    echo "1) App Bundle:"
    echo "   dist/CustomGANStego.app"
    echo ""
    echo "2) Trinh Cai Dat DMG:"
    echo "   dist/$DMG_NAME"
    echo ""
    echo "=============================================="
    echo "Cach Su Dung:"
    echo "=============================================="
    echo ""
    echo "Tuy chon A - Cai dat tu DMG (Khuyen nghi):"
    echo "   1. Mo dist/$DMG_NAME"
    echo "   2. Keo app vao thu muc Applications"
    echo "   3. Eject disk image"
    echo "   4. Mo tu Launchpad"
    echo ""
    echo "Tuy chon B - Chay truc tiep:"
    echo "   open dist/CustomGANStego.app"
    echo ""
    echo "Tuy chon C - Cai dat thu cong:"
    echo "   cp -r dist/CustomGANStego.app /Applications/"
    echo ""
    echo "Neu macOS chan app:"
    echo "   xattr -cr dist/CustomGANStego.app"
    echo "   (hoac cho app da cai: xattr -cr /Applications/CustomGANStego.app)"
    echo ""
    echo "=============================================="
    echo "Phan Phoi:"
    echo "=============================================="
    echo ""
    echo "Chia se file DMG voi nguoi dung:"
    echo "   • File: dist/$DMG_NAME"
    echo "   • Double-click de mo"
    echo "   • Keo vao Applications"
    echo "   • Xong!"
    echo ""
    echo "=============================================="
    echo "Tinh Nang:"
    echo "=============================================="
    echo ""
    echo "Encode:  Giau tin trong anh"
    echo "Decode:  Trich xuat tin tu anh"
    echo "Reverse: Khoi phuc anh cover goc"
    echo "GenRSA:  Tao cap khoa RSA"
    echo "Compare: Tinh chi so PSNR/SSIM"
    echo ""
    echo "=============================================="
    echo "Meo:"
    echo "=============================================="
    echo ""
    echo "• Dung anh PNG de co chat luong tot nhat"
    echo "• Bat ma hoa cho du lieu nhay cam"
    echo "• Giu khoa rieng tu an toan!"
    echo "• Kiem tra metrics: PSNR > 40 dB la xuat sac"
    echo ""
    echo "=============================================="
    echo ""
    
    read -p "Mo app ngay bay gio? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dang mo CustomGANStego..."
        open dist/CustomGANStego.app
    else
        read -p "Mo file DMG? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Dang mo DMG..."
            open "dist/$DMG_NAME"
        fi
    fi
    
    echo ""
    echo "Hoan tat! Chuc ban su dung CustomGANStego vui ve!"
    echo ""
    echo "Phan phoi: dist/$DMG_NAME"
    echo ""
    
else
    echo ""
    echo "=============================================="
    echo "❌ BUILD THAT BAI!"
    echo "=============================================="
    echo ""
    echo "Van de thuong gap:"
    echo "• Kiem tra thong bao loi o tren"
    echo "• Dam bao tat ca dependencies da duoc cai"
    echo "• Thu: ./build_app.sh --setup-only"
    echo "• Kiem tra phien ban PyInstaller"
    echo ""
    echo "Debug:"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  pyinstaller steganography_app.spec"
    echo ""
    exit 1
fi
