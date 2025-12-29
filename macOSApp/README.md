# CustomGANStego macOS Application

Ứng dụng macOS với giao diện đồ họa cho hệ thống giấu tin (steganography) sử dụng Deep Learning với GAN.

## Features

- **📝 Encode** - Giấu tin vào ảnh với GAN
- **🔍 Decode** - Trích xuất tin từ ảnh stego
- **⏮️ Reverse** - Khôi phục ảnh gốc (lossless)
- **🔑 GenRSA** - Tạo khóa RSA cho mã hóa
- **📊 Compare** - Tính PSNR/SSIM/MSE metrics
- **🔒 Encryption** - RSA+AES hybrid encryption

## Quick Start

### One-Command Build

```bash
cd macOSApp
chmod +x build_app.sh
./build_app.sh
```

**Output:**

- `dist/CustomGANStego.app` - macOS app bundle
- `dist/CustomGANStego-macOS.dmg` - DMG installer (171 MB)

Script sẽ tự động:

1. ✅ Kiểm tra Python và dependencies
2. ✅ Tạo/activate virtual environment
3. ✅ Cài đặt packages thiếu
4. ✅ Kiểm tra model files
5. ✅ Build app bundle
6. ✅ Tạo DMG installer
7. ✅ Hướng dẫn sử dụng

### Install from DMG (Recommended)

```bash
# Open DMG
open dist/CustomGANStego-macOS.dmg

# Drag app to Applications folder
# Then open from Launchpad
```

### Run Directly

```bash
open dist/CustomGANStego.app
```

### Development Mode

```bash
cd macOSApp
source ../prjvenv/bin/activate
python steganography_app.py
```

## 📦 Requirements

```
torch>=2.0.0
torchvision>=0.15.0
Pillow>=9.0.0
imageio>=2.25.0
numpy>=1.24.0
scikit-image>=0.20.0
matplotlib>=3.7.0
pycryptodome>=3.17.0
reedsolo>=1.7.0
pyinstaller>=5.10.0
```

Auto-installed by `build_app.sh`

## 📖 Usage Guide

### 1. Encode (Giấu tin)

1. Tab **📝 Encode**
2. Chọn ảnh cover
3. Nhập tin nhắn
4. (Optional) Enable RSA+AES encryption
5. Click **🚀 Encode**
6. Lưu ảnh stego

### 2. Decode (Trích xuất)

1. Tab **🔍 Decode**
2. Chọn ảnh stego
3. (If encrypted) Enable decryption + chọn private key
4. Click **🔍 Decode**
5. Xem tin nhắn

### 3. Reverse (Khôi phục)

1. Tab **⏮️ Reverse**
2. Chọn ảnh stego
3. Click **⏮️ Reverse**
4. Lưu ảnh recovered

### 4. GenRSA (Tạo khóa)

1. Tab **🔑 GenRSA**
2. Chọn key size (2048 bits recommended)
3. Chọn thư mục lưu
4. Click **🔑 Tạo khóa**
5. Nhận public_key.pem + private_key.pem

### 5. Compare (So sánh)

1. Tab **📊 Compare**
2. Chọn 2 ảnh
3. Click **📊 Tính Metrics**
4. Xem PSNR/SSIM/MSE
5. (Optional) Lưu comparison image

## 🎯 Workflow Examples

### Basic Steganography

```
Cover.png + "Secret" → Encode → Stego.png
Stego.png → Decode → "Secret"
```

### With Encryption

```
GenRSA → public_key.pem + private_key.pem
Cover.png + "Secret" + public_key → Encode → Stego.png
Stego.png + private_key → Decode → "Secret"
```

### Reversible Steganography

```
Cover.png → Encode → Stego.png
Stego.png → Reverse → Recovered.png
Compare: Cover vs Recovered (PSNR >45 dB)
```

## Quality Metrics

| Metric | Good      | Excellent |
| ------ | --------- | --------- |
| PSNR   | 30-40 dB  | >40 dB    |
| SSIM   | 0.90-0.95 | >0.95     |
| MSE    | <100      | <50       |

## Troubleshooting

### App không mở (macOS security)

```bash
xattr -cr dist/CustomGANStego.app
open dist/CustomGANStego.app
```

### Model not found

```bash
cd ..
python train.py  # Train models first
```

### Dependencies missing

```bash
pip install -r requirements.txt
```

## 📁 Structure

```
macOSApp/
├── steganography_app.py      # Main app
├── steganography_app.spec    # PyInstaller config
├── build_app.sh              # Build script (with env check)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── dist/                     # Build output
    └── CustomGANStego.app    # macOS app bundle
```

## 🔒 Security Notes

- **Private key**: KHÔNG chia sẻ
- **Public key**: Có thể chia sẻ công khai
- **Stego image**: An toàn để gửi (tin đã mã hóa)
- **Backup**: Lưu private key ở nơi an toàn

## Tips

- Use PNG for best quality
- PSNR >40 dB = invisible to human eye
- Enable encryption for sensitive data
- Backup private keys securely
- Check comparison metrics before sending

## License

Project CustomGANStego - CNTT

---

**Built with ❤️ using PyTorch, scikit-image, and PyInstaller**

For more info, see parent project README.

## Tính năng

- **📝 Encode (Giấu tin)**: Nhúng tin nhắn bí mật vào ảnh với GAN
- **🔍 Decode (Trích xuất)**: Trích xuất tin nhắn từ ảnh stego
- **⏮️ Reverse Hiding**: Khôi phục ảnh gốc từ ảnh stego (lossless recovery)
- **🔑 GenRSA**: Tạo cặp khóa RSA cho mã hóa
- **📊 Compare & Metrics**: So sánh ảnh và tính PSNR/SSIM/MSE
- **🔒 RSA + AES Encryption**: Mã hóa hybrid cho bảo mật cao
- **🖼️ Visual Comparison**: Hiển thị ảnh comparison với difference maps

## Giao diện

App có 5 tabs chính:

1. **📝 Encode** - Giấu tin vào ảnh
2. **🔍 Decode** - Trích xuất tin từ ảnh
3. **⏮️ Reverse** - Khôi phục ảnh gốc
4. **🔑 GenRSA** - Tạo khóa RSA
5. **📊 Compare** - So sánh và tính metrics

## Cài đặt và Build

### Bước 1: Cài đặt dependencies

```bash
# Di chuyển vào thư mục macOSApp
cd macOSApp

# Kích hoạt virtual environment (nếu có)
source ../../prjvenv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### Bước 2: Chạy trực tiếp (Development Mode)

```bash
python steganography_app.py
```

### Bước 3: Build thành macOS App Bundle

```bash
# Cho phép thực thi build script
chmod +x build_app.sh

# Build app
./build_app.sh
```

App sẽ được tạo tại: `dist/CustomGANStego.app`

### Bước 4: Cài đặt vào Applications (Optional)

```bash
# Copy app vào thư mục Applications
cp -r dist/CustomGANStego.app /Applications/

# Chạy từ Launchpad hoặc Finder
open /Applications/CustomGANStego.app
```

## 📦 Requirements

```
torch>=2.0.0              # Deep Learning framework
torchvision>=0.15.0       # Computer Vision
Pillow>=9.0.0             # Image processing
imageio>=2.25.0           # Image I/O
numpy>=1.24.0             # Numerical computing
scikit-image>=0.20.0      # PSNR/SSIM metrics
matplotlib>=3.7.0         # Visualization
pycryptodome>=3.17.0      # RSA+AES encryption
reedsolo>=1.7.0           # Error correction
pyinstaller>=5.10.0       # Build tool
```

## 📖 Hướng dẫn sử dụng chi tiết

### 1. Encode - Giấu tin vào ảnh

**Bước 1:** Chọn ảnh Cover

- Click nút "Chọn ảnh..."
- Chọn ảnh PNG/JPG làm cover image

**Bước 2:** Nhập tin cần giấu

- Gõ hoặc paste tin nhắn vào text box
- Có thể nhập văn bản dài tùy ý

**Bước 3:** (Tùy chọn) Bật mã hóa

- Check ✅ "Sử dụng mã hóa RSA+AES"
- Chọn public key (.pem file)

**Bước 4:** Encode

- Click "🚀 Encode"
- Chọn nơi lưu ảnh stego
- Đợi quá trình hoàn tất

**Kết quả:** Ảnh stego với tin đã được giấu bên trong

---

### 2. Decode - Trích xuất tin

**Bước 1:** Chọn ảnh Stego

- Click "Chọn ảnh..."
- Chọn ảnh stego đã tạo trước đó

**Bước 2:** (Nếu có mã hóa) Giải mã

- Check ✅ "Giải mã RSA+AES"
- Chọn private key (.pem file)

**Bước 3:** Decode

- Click "🔍 Decode"
- Tin nhắn sẽ hiển thị trong text box

**Bước 4:** Lưu kết quả (optional)

- Click "💾 Save"
- Lưu tin nhắn ra file .txt

---

### 3. Reverse - Khôi phục ảnh gốc

**Bước 1:** Chọn ảnh Stego

- Click "Chọn ảnh..."
- Chọn ảnh stego cần khôi phục

**Bước 2:** Reverse

- Click "⏮️ Reverse"
- Chọn nơi lưu ảnh đã khôi phục
- Đợi quá trình xử lý

**Bước 3:** Xem kết quả

- Ảnh stego và recovered sẽ hiển thị song song
- So sánh trực quan

**Bước 4:** Lưu (optional)

- Click "💾 Save" để lưu lại file

---

### 4. GenRSA - Tạo cặp khóa RSA

**Bước 1:** Chọn độ dài khóa

- ⚪ 1024 bits - Nhanh, bảo mật thấp
- ⚪ 2048 bits - ✅ Khuyến nghị (default)
- ⚪ 3072 bits - Bảo mật cao
- ⚪ 4096 bits - Bảo mật rất cao, chậm hơn

**Bước 2:** Chọn thư mục lưu

- Click "Chọn thư mục..."
- Chọn nơi lưu cặp khóa

**Bước 3:** Tạo khóa

- Click "🔑 Tạo khóa"
- Đợi quá trình tạo khóa

**Kết quả:**

- `public_key.pem` - Dùng để mã hóa (có thể chia sẻ)
- `private_key.pem` - Dùng để giải mã (⚠️ GIỮ BÍ MẬT!)

---

### 5. Compare - So sánh và tính Metrics

**Bước 1:** Chọn 2 ảnh để so sánh

- Ảnh 1: Cover/Original
- Ảnh 2: Stego/Recovered

**Bước 2:** Tính metrics

- Click "📊 Tính Metrics"
- Đợi tính toán

**Kết quả hiển thị:**

**Metrics:**

- **PSNR** (Peak Signal-to-Noise Ratio)
  - > 40 dB: ✅ Chất lượng rất tốt
  - > 30 dB: ✓ Chất lượng tốt
  - < 30 dB: ⚠️ Chất lượng trung bình
- **SSIM** (Structural Similarity Index)
  - > 0.95: ✅ Tương đồng rất cao
  - > 0.90: ✓ Tương đồng cao
  - < 0.90: ⚠️ Tương đồng trung bình
- **MSE** (Mean Squared Error)
  - Càng nhỏ càng tốt

**Visual Comparison:**

- 3 ảnh song song: Img1 | Img2 | Difference (10x)
- Difference map cho thấy sự khác biệt (được amplify 10 lần)

**Bước 3:** Lưu kết quả

- Click "💾 Save PNG"
- Lưu ảnh comparison để báo cáo

---

## 🎯 Workflow điển hình

### Scenario 1: Giấu tin đơn giản (không mã hóa)

```
1. Encode tab:
   - Chọn cover.png
   - Nhập: "Hello World"
   - Encode → stego.png

2. Decode tab:
   - Chọn stego.png
   - Decode → "Hello World"

3. Compare tab:
   - Ảnh 1: cover.png
   - Ảnh 2: stego.png
   - Metrics: PSNR ~45 dB, SSIM ~0.99
```

### Scenario 2: Giấu tin có mã hóa

```
1. GenRSA tab:
   - Chọn 2048 bits
   - Tạo khóa → public_key.pem, private_key.pem

2. Encode tab:
   - Chọn cover.png
   - Nhập: "Secret message"
   - ✅ Mã hóa RSA+AES
   - Chọn public_key.pem
   - Encode → encrypted_stego.png

3. Decode tab:
   - Chọn encrypted_stego.png
   - ✅ Giải mã RSA+AES
   - Chọn private_key.pem
   - Decode → "Secret message"
```

### Scenario 3: Reversible Steganography

```
1. Encode tab:
   - cover.png + "Secret" → stego.png

2. Reverse tab:
   - stego.png → recovered.png

3. Compare tab:
   - Ảnh 1: cover.png
   - Ảnh 2: recovered.png
   - Metrics: PSNR ~50 dB (gần như giống hệt)
```

---

## Troubleshooting

### Lỗi: "Model not found"

**Giải pháp:**

```bash
# Đảm bảo đã train model
cd ..
python train.py

# Model sẽ được lưu tại: results/model/
```

### Lỗi: "pycryptodome not found"

**Giải pháp:**

```bash
pip install pycryptodome
```

### Lỗi: "tkinter not found"

**Giải pháp (macOS):**

```bash
# Cài lại Python với tkinter support
brew install python-tk@3.11
```

### App không mở được sau build

**Giải pháp:**

```bash
# macOS security: Allow app from unidentified developer
xattr -cr dist/CustomGANStego.app
open dist/CustomGANStego.app
```

---

## 📁 Cấu trúc thư mục

```
macOSApp/
├── steganography_app.py      # Main app source
├── steganography_app.spec    # PyInstaller spec
├── build_app.sh              # Build script
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── .gitignore               # Git ignore
├── build/                   # Build artifacts (ignored)
└── dist/                    # Distribution
    └── CustomGANStego.app   # Final macOS app
```

---

## 🔒 Bảo mật

**⚠️ LƯU Ý QUAN TRỌNG:**

1. **Private key:** KHÔNG bao giờ chia sẻ private key
2. **Public key:** Có thể chia sẻ công khai
3. **Stego image:** An toàn để chia sẻ (tin đã được mã hóa và giấu)
4. **Backup keys:** Sao lưu private key ở nơi an toàn

**Quy trình bảo mật tốt:**

```
Alice                          Bob
-----                          ---
1. Tạo RSA keypair
2. Gửi public_key cho Bob  →
3.                         ←   Bob: Encode với public_key
4.                         ←   Nhận stego.png
5. Decode với private_key
6. Đọc được tin nhắn
```

---

## So sánh với các phương pháp khác

| Phương pháp        | PSNR   | SSIM  | Dung lượng | Tốc độ     | Reverse  |
| ------------------ | ------ | ----- | ---------- | ---------- | -------- |
| **CustomGANStego** | 40+ dB | 0.99+ | Cao        | Nhanh      | ✅ Có    |
| LSB                | 50+ dB | 0.99+ | Thấp       | Rất nhanh  | ❌ Không |
| DCT-based          | 40+ dB | 0.95+ | Trung bình | Trung bình | ❌ Không |
| DWT-based          | 35+ dB | 0.93+ | Trung bình | Chậm       | ❌ Không |

**Ưu điểm CustomGANStego:**

- ✅ Khả năng reverse (khôi phục ảnh gốc)
- ✅ PSNR cao (>45 dB)
- ✅ SSIM rất cao (>0.99)
- ✅ Chống steganalysis tốt nhờ GAN
- ✅ Tích hợp mã hóa RSA+AES

---

## 🎓 Tài liệu tham khảo

- **Paper:** "Hiding Images in Plain Sight: Deep Steganography" (Baluja, 2017)
- **GAN:** "Generative Adversarial Networks" (Goodfellow et al., 2014)
- **RSA:** "A Method for Obtaining Digital Signatures" (Rivest et al., 1978)

---

## 👨‍💻 Development

### Run with debugging

```bash
python steganography_app.py --debug
```

### Rebuild after changes

```bash
./build_app.sh
```

### Clean build

```bash
rm -rf build dist __pycache__ *.spec.bak
./build_app.sh
```

---

## License

Project CustomGANStego - CNTT

---

## 🙏 Credits

- PyTorch Team
- scikit-image
- PyCryptodome
- PyInstaller
- CustomGANStego Team

---

**Chúc bạn sử dụng app thành công! 🚀**

Nếu có vấn đề, vui lòng mở issue trên GitHub. 3. Chọn đường dẫn output cho ảnh recovered 4. Click **🔄 Recover Cover Image**

### 4. Cài đặt (Settings)

- **Model Path**: Chọn file model (.dat)
- **Auto-detect**: Tự động tìm model tốt nhất
- **Generate RSA Keys**: Tạo cặp khóa RSA mới

## Về mã hóa RSA+AES

Khi bật encryption:

- **AES-256-CBC** được sử dụng để mã hóa tin nhắn
- **RSA** được sử dụng để mã hóa AES key
- Cần có cặp khóa RSA (public/private key)

Tạo cặp khóa:

```bash
# Sử dụng app
Settings > Generate 2048-bit RSA Keys

# Hoặc command line
python ../genRSA.py --bits 2048
```

## Troubleshooting

### "Steganography modules not available"

- Đảm bảo đang ở đúng thư mục project
- Kiểm tra các file encoder.py, decoder.py tồn tại trong thư mục cha

### "No model found"

- Train model trước: `python ../train.py`
- Hoặc chọn model thủ công trong Settings

### "Crypto modules not available"

```bash
pip install pycryptodome
```

### Build app thất bại

```bash
# Cài đặt PyInstaller
pip install pyinstaller

# Clean và rebuild
rm -rf build dist
pyinstaller steganography_app.spec
```

## License

MIT License - CustomGANStego Team
