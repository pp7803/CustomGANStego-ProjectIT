set -e

echo "==================================="
echo "Công Cụ Tải Xuống Dataset DIV2K"
echo "==================================="

# Tạo thư mục
mkdir -p div2k/train/images
mkdir -p div2k/val/images

# Tải xuống tập huấn luyện
echo "Đang tải tập huấn luyện (3.2 GB)..."
wget -c http://data.vision.ee.ethz.ch/cvl/DIV2K/DIV2K_train_HR.zip -O DIV2K_train_HR.zip

# Tải xuống tập kiểm định
echo "Đang tải tập kiểm định (350 MB)..."
wget -c http://data.vision.ee.ethz.ch/cvl/DIV2K/DIV2K_valid_HR.zip -O DIV2K_valid_HR.zip

# Giải nén tập huấn luyện
echo "Đang giải nén tập huấn luyện..."
unzip -q DIV2K_train_HR.zip
mv DIV2K_train_HR/* div2k/train/images/
rmdir DIV2K_train_HR

# Giải nén tập kiểm định
echo "Đang giải nén tập kiểm định..."
unzip -q DIV2K_valid_HR.zip
mv DIV2K_valid_HR/* div2k/val/images/
rmdir DIV2K_valid_HR

# Dọn dẹp
rm DIV2K_train_HR.zip DIV2K_valid_HR.zip

echo "Tải xuống dataset hoàn tất!"
echo "Ảnh huấn luyện: $(ls div2k/train/images/*.png | wc -l)"
echo "Ảnh kiểm định: $(ls div2k/val/images/*.png | wc -l)"