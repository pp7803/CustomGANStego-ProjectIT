set -e

echo "==================================="
echo "DIV2K Dataset Downloader"
echo "==================================="

# Create directories
mkdir -p div2k/train/images
mkdir -p div2k/val/images

# Download training set
echo "Downloading training set (3.2 GB)..."
wget -c http://data.vision.ee.ethz.ch/cvl/DIV2K/DIV2K_train_HR.zip -O DIV2K_train_HR.zip

# Download validation set
echo "Downloading validation set (350 MB)..."
wget -c http://data.vision.ee.ethz.ch/cvl/DIV2K/DIV2K_valid_HR.zip -O DIV2K_valid_HR.zip

# Extract training set
echo "Extracting training set..."
unzip -q DIV2K_train_HR.zip
mv DIV2K_train_HR/* div2k/train/images/
rmdir DIV2K_train_HR

# Extract validation set
echo "Extracting validation set..."
unzip -q DIV2K_valid_HR.zip
mv DIV2K_valid_HR/* div2k/val/images/
rmdir DIV2K_valid_HR

# Cleanup
rm DIV2K_train_HR.zip DIV2K_valid_HR.zip

echo "Dataset download complete!"
echo "Training images: $(ls div2k/train/images/*.png | wc -l)"
echo "Validation images: $(ls div2k/val/images/*.png | wc -l)"