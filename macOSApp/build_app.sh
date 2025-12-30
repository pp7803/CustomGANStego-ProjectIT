#!/bin/bash

set -e

echo "Công Cụ Build Ứng Dụng macOS CustomGANStego"
echo "=============================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PRJVENV_DIR="$PROJECT_DIR/prjvenv"

echo "Bước 1: Kiểm Tra Môi Trường"
echo "----------------------------------------"

if ! command -v python3 &> /dev/null; then
    echo "Không tìm thấy Python 3!"
    echo "Vui lòng cài đặt Python 3.8 trở lên"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python: $PYTHON_VERSION"

if [ -d "$PRJVENV_DIR" ]; then
    echo "Đã tìm thấy môi trường ảo"
    source "$PRJVENV_DIR/bin/activate"
else
    echo "Không tìm thấy môi trường ảo tại: $PRJVENV_DIR"
    echo ""
    read -p "Tạo môi trường ảo ngay bây giờ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Đang tạo môi trường ảo..."
        cd "$PROJECT_DIR"
        python3 -m venv prjvenv
        source prjvenv/bin/activate
        cd "$SCRIPT_DIR"
        echo "Đã tạo môi trường ảo"
    else
        echo "Không thể tiếp tục mà không có môi trường ảo"
        exit 1
    fi
fi

echo ""
echo "Đang kiểm tra dependencies..."

python3 - <<EOF
import sys
errors = []

try:
    import tkinter
    print("tkinter")
except ImportError:
    errors.append("tkinter")
    print("tkinter - REQUIRED")

try:
    import torch
    print("torch")
except ImportError:
    errors.append("torch")
    print("torch - REQUIRED")

try:
    from PIL import Image
    print("Pillow")
except ImportError:
    errors.append("Pillow")
    print("Pillow - REQUIRED")

try:
    import numpy
    print("numpy")
except ImportError:
    errors.append("numpy")
    print("numpy - REQUIRED")

try:
    from skimage.metrics import peak_signal_noise_ratio
    print("scikit-image")
except ImportError:
    errors.append("scikit-image")
    print("scikit-image - REQUIRED")

try:
    import matplotlib
    print("matplotlib")
except ImportError:
    errors.append("matplotlib")
    print("matplotlib - REQUIRED")

try:
    from Crypto.PublicKey import RSA
    print("pycryptodome")
except ImportError:
    print("pycryptodome - OPTIONAL (encryption disabled)")

try:
    import imageio
    print("imageio")
except ImportError:
    errors.append("imageio")
    print("imageio - REQUIRED")

try:
    import reedsolo
    print("reedsolo")
except ImportError:
    errors.append("reedsolo")
    print("reedsolo - REQUIRED")

try:
    import PyInstaller
    print("pyinstaller")
except ImportError:
    errors.append("pyinstaller")
    print("pyinstaller - REQUIRED for build")

if errors:
    print(f"\nThiếu {len(errors)} gói bắt buộc")
    sys.exit(1)
else:
    print("\nTất cả dependencies OK")
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "Đang cài đặt dependencies còn thiếu..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Cài đặt dependencies thất bại"
        exit 1
    fi
    echo "Đã cài đặt dependencies"
fi

echo ""
echo "Đang kiểm tra file model..."
MODEL_DIR="$PROJECT_DIR/results/model"
if [ -d "$MODEL_DIR" ]; then
    MODEL_COUNT=$(ls -1 "$MODEL_DIR"/*.dat 2>/dev/null | wc -l)
    if [ $MODEL_COUNT -gt 0 ]; then
        echo "Tìm thấy $MODEL_COUNT file model"
        BEST_MODEL=$(ls -1 "$MODEL_DIR"/*.dat | sort | tail -n 1 | xargs basename)
        echo "   Tốt nhất: $BEST_MODEL"
    else
        echo "Không tìm thấy file .dat model trong $MODEL_DIR"
        echo "   App sẽ hoạt động nhưng có thể chất lượng giảm"
    fi
else
    echo "Không tìm thấy thư mục model: $MODEL_DIR"
    echo "   Chạy 'python train.py' để huấn luyện model trước"
fi

python3 - <<EOF
import sys
sys.path.insert(0, "$PROJECT_DIR")
try:
    from enhancedstegan import encode_message, decode_message, reverse_hiding
    print("Module enhancedstegan OK")
except ImportError as e:
    print(f"Module enhancedstegan THẤT BẠI: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "Kiểm tra module dự án thất bại"
    exit 1
fi

echo ""
echo "Hoàn thành kiểm tra môi trường!"
echo ""

echo "Bước 2: Build Ứng Dụng"
echo "----------------------------------------"

echo "Đang dọn dẹp các bản build cũ..."
cd "$SCRIPT_DIR"
rm -rf build dist __pycache__ *.spec.bak

echo "Đang build với PyInstaller..."
pyinstaller steganography_app.spec

if [ -d "dist/CustomGANStego.app" ]; then
    echo ""
    echo "=============================================="
    echo "BUILD THÀNH CÔNG!"
    echo "=============================================="
    
    APP_SIZE=$(du -sh "dist/CustomGANStego.app" | awk '{print $1}')
    echo ""
    echo "Chi Tiết Ứng Dụng:"
    echo "   Vị trí: $SCRIPT_DIR/dist/CustomGANStego.app"
    echo "   Kích thước: $APP_SIZE"
    echo ""
    
    echo "Bước 3: Tạo Gói Phân Phối"
    echo "----------------------------------------"
    
    echo "Chọn định dạng phân phối:"
    echo "  1) ZIP archive (khuyến nghị - nhỏ hơn, nhanh hơn)"
    echo "  2) DMG disk image (trình cài đặt macOS truyền thống)"
    echo "  3) Bỏ qua đóng gói (chỉ dùng .app trực tiếp)"
    read -p "Nhập lựa chọn [1-3] (mặc định: 1): " PACKAGE_CHOICE
    PACKAGE_CHOICE=${PACKAGE_CHOICE:-1}
    
    if [ "$PACKAGE_CHOICE" = "1" ]; then
        ZIP_NAME="CustomGANStego-macOS.zip"
        ZIP_PATH="$SCRIPT_DIR/dist/$ZIP_NAME"
        rm -f "$ZIP_PATH"
        
        echo "Đang tạo file ZIP..."
        cd "$SCRIPT_DIR/dist"
        zip -r -q "$ZIP_NAME" CustomGANStego.app
        cd "$SCRIPT_DIR"
        
        if [ -f "$ZIP_PATH" ]; then
            ZIP_SIZE=$(du -sh "$ZIP_PATH" | awk '{print $1}')
            echo "Tạo ZIP thành công!"
            echo "   Vị trí: $ZIP_PATH"
            echo "   Kích thước: $ZIP_SIZE"
        else
            echo "Tạo ZIP thất bại"
        fi
        
    elif [ "$PACKAGE_CHOICE" = "2" ]; then
        DMG_NAME="CustomGANStego-macOS.dmg"
        DMG_PATH="$SCRIPT_DIR/dist/$DMG_NAME"
        TEMP_DMG="$SCRIPT_DIR/dist/temp.dmg"
        VOLUME_NAME="CustomGANStego"
        
        rm -f "$DMG_PATH" "$TEMP_DMG"
        
        echo "Đang tạo disk image (có thể mất một chút thời gian)..."
        
        hdiutil create -size 3000m -fs HFS+ -volname "$VOLUME_NAME" "$TEMP_DMG" > /dev/null 2>&1
        
        MOUNT_DIR=$(hdiutil attach "$TEMP_DMG" | grep "/Volumes/$VOLUME_NAME" | awk '{print $3}')
        
        if [ -z "$MOUNT_DIR" ]; then
            echo "Không thể mount DMG tạm thời"
            echo "   Bỏ qua tạo DMG"
        else
            echo "Đang copy app vào DMG..."
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
            
            echo "Đang hoàn thiện DMG..."
            hdiutil detach "$MOUNT_DIR" > /dev/null 2>&1
            
            hdiutil convert "$TEMP_DMG" -format UDZO -o "$DMG_PATH" > /dev/null 2>&1
            rm -f "$TEMP_DMG"
            
            if [ -f "$DMG_PATH" ]; then
                DMG_SIZE=$(du -sh "$DMG_PATH" | awk '{print $1}')
                echo "Tạo DMG thành công!"
                echo "   Vị trí: $DMG_PATH"
                echo "   Kích thước: $DMG_SIZE"
            else
                echo "Tạo DMG thất bại"
            fi
        fi
    else
        echo "Bỏ qua tạo gói"
        echo "   Sử dụng dist/CustomGANStego.app trực tiếp"
    fi
    
    echo ""
    
    echo "Bước 4: Phân Phối & Sử Dụng"
    echo "=============================================="
    echo ""
    echo "Các File Đã Tạo:"
    echo ""
    echo "1) App Bundle:"
    echo "   dist/CustomGANStego.app"
    echo ""
    echo "2) Trình Cài Đặt DMG:"
    echo "   dist/$DMG_NAME"
    echo ""
    echo "=============================================="
    echo "Cách Sử Dụng:"
    echo "=============================================="
    echo ""
    echo "Tùy chọn A - Cài đặt từ DMG (Khuyến nghị):"
    echo "   1. Mở dist/$DMG_NAME"
    echo "   2. Kéo app vào thư mục Applications"
    echo "   3. Eject disk image"
    echo "   4. Mở từ Launchpad"
    echo ""
    echo "Tùy chọn B - Chạy trực tiếp:"
    echo "   open dist/CustomGANStego.app"
    echo ""
    echo "Tùy chọn C - Cài đặt thủ công:"
    echo "   cp -r dist/CustomGANStego.app /Applications/"
    echo ""
    echo "Nếu macOS chặn app:"
    echo "   xattr -cr dist/CustomGANStego.app"
    echo "   (hoặc cho app đã cài: xattr -cr /Applications/CustomGANStego.app)"
    echo ""
    echo "=============================================="
    echo "Phân Phối:"
    echo "=============================================="
    echo ""
    echo "Chia sẻ file DMG với người dùng:"
    echo "   • File: dist/$DMG_NAME"
    echo "   • Double-click để mở"
    echo "   • Kéo vào Applications"
    echo "   • Xong!"
    echo ""
    echo "=============================================="
    echo "Tính Năng:"
    echo "=============================================="
    echo ""
    echo "Encode:  Giấu tin trong ảnh"
    echo "Decode:  Trích xuất tin từ ảnh"
    echo "Reverse: Khôi phục ảnh cover gốc"
    echo "GenRSA:  Tạo cặp khóa RSA"
    echo "Compare: Tính chỉ số PSNR/SSIM"
    echo ""
    echo "=============================================="
    echo "Mẹo:"
    echo "=============================================="
    echo ""
    echo "• Dùng ảnh PNG để có chất lượng tốt nhất"
    echo "• Bật mã hóa cho dữ liệu nhạy cảm"
    echo "• Giữ khóa riêng tư an toàn!"
    echo "• Kiểm tra metrics: PSNR > 40 dB là xuất sắc"
    echo ""
    echo "=============================================="
    echo ""
    
    read -p "Mở app ngay bây giờ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Đang mở CustomGANStego..."
        open dist/CustomGANStego.app
    else
        read -p "Mở file DMG? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Đang mở DMG..."
            open "dist/$DMG_NAME"
        fi
    fi
    
    echo ""
    echo "Hoàn tất! Chúc bạn sử dụng CustomGANStego vui vẻ!"
    echo ""
    echo "Phân phối: dist/$DMG_NAME"
    echo ""
    
else
    echo ""
    echo "=============================================="
    echo "BUILD THẤT BẠI!"
    echo "=============================================="
    echo ""
    echo "Vấn đề thường gặp:"
    echo "• Kiểm tra thông báo lỗi ở trên"
    echo "• Đảm bảo tất cả dependencies đã được cài"
    echo "• Thử: pip install -r requirements.txt"
    echo "• Kiểm tra phiên bản PyInstaller"
    echo ""
    exit 1
fi
