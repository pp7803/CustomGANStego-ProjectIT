#!/bin/bash

# Script thiết lập cho Dự Án CustomGANStego
# Script này tạo môi trường ảo và cài đặt tất cả dependencies

set -e  # Thoát khi có lỗi

echo "=== Thiết Lập Môi Trường CustomGANStego ==="
echo ""

# Kiểm tra Python 3 đã được cài đặt chưa
if ! command -v python3 &> /dev/null; then
    echo "Lỗi: Python 3 chưa được cài đặt. Vui lòng cài đặt Python 3.8 trở lên."
    exit 1
fi

# Hiển thị phiên bản Python
PYTHON_VERSION=$(python3 --version)
echo "Tìm thấy $PYTHON_VERSION"
echo ""

# Tạo môi trường ảo
if [ -d "prjvenv" ]; then
    echo "Môi trường ảo 'prjvenv' đã tồn tại."
    read -p "Bạn có muốn tạo lại không? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Đang xóa môi trường ảo hiện tại..."
        rm -rf prjvenv
    else
        echo "Sử dụng môi trường ảo hiện tại."
    fi
fi

if [ ! -d "prjvenv" ]; then
    echo "Đang tạo môi trường ảo 'prjvenv'..."
    python3 -m venv prjvenv
    echo "Đã tạo môi trường ảo"
    echo ""
fi

# Kích hoạt môi trường ảo
echo "Đang kích hoạt môi trường ảo..."
source prjvenv/bin/activate

# Nâng cấp pip
echo "Đang nâng cấp pip..."
pip install --upgrade pip
echo ""

# Cài đặt requirements
if [ -f "requirements.txt" ]; then
    echo "Đang cài đặt dependencies từ requirements.txt..."
    pip install -r requirements.txt
    echo ""
    echo "Đã cài đặt tất cả dependencies thành công"
else
    echo "Lỗi: Không tìm thấy requirements.txt"
    exit 1
fi

echo ""
echo "=== Thiết Lập Hoàn Tất! ==="
echo ""
echo "Để kích hoạt môi trường ảo, chạy:"
echo "  source prjvenv/bin/activate"
echo ""
echo "Để tắt khi hoàn thành, chạy:"
echo "  deactivate"
echo ""
