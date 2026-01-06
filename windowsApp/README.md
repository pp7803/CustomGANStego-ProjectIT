# CustomGANStego Windows Application

Ứng dụng Windows với giao diện đồ họa cho hệ thống giấu tin (steganography) sử dụng Deep Learning với GAN.

## Features

- **🖼️ Encode** - Giấu tin vào ảnh với GAN
- **🔍 Decode** - Trích xuất tin từ ảnh stego
- **↩️ Reverse** - Khôi phục ảnh gốc (lossless)
- **🔐 GenRSA** - Tạo khóa RSA cho mã hóa
- **📊 Compare** - Tính PSNR/SSIM/MSE metrics
- **🔒 Encryption** - RSA+AES hybrid encryption

## Quick Start

### One-Command Build (Khuyến nghị)

```batch
cd windowsApp
build_app.bat
```

Script `build_app.bat` tích hợp tất cả chức năng:

1. **Tự động kiểm tra Python** - Yêu cầu Python 3.10+
2. **Tự động tạo venv riêng** - Tạo `windowsApp\venv\` nếu chưa có
3. **Tự động cài dependencies** - Cài đặt tất cả packages từ requirements.txt
4. **Kiểm tra model files** - Kiểm tra model đã train
5. **Build exe** - Tạo CustomGANStego.exe (onefile)
6. **Hướng dẫn sử dụng** - Interactive guide

**Output:**

- `dist\CustomGANStego.exe` - Windows executable (~294 MB)

### Run Directly

```batch
dist\CustomGANStego.exe
```

Hoặc double-click vào file exe.

## Virtual Environment (Môi trường ảo riêng)

Windows App sử dụng **môi trường ảo riêng** tại `windowsApp\venv\`, hoàn toàn độc lập với `prjvenv\` của thư mục cha.

### Tự động setup (được tích hợp trong build_app.bat)

Script `build_app.bat` sẽ tự động:

- Tạo `venv\` nếu chưa tồn tại
- Kích hoạt môi trường ảo
- Cài đặt dependencies nếu thiếu

**Không cần chạy script riêng!**

### Manual setup (nếu cần)

```batch
cd windowsApp

REM Tạo venv
python -m venv venv

REM Kích hoạt
venv\Scripts\activate.bat

REM Cài dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Sử dụng môi trường

```batch
REM Kích hoạt
venv\Scripts\activate.bat

REM Kiểm tra
where python
REM Nên hiển thị: ...\windowsApp\venv\Scripts\python.exe

REM Tắt
deactivate
```

### Development Mode

```batch
cd windowsApp
venv\Scripts\activate.bat
python steganography_app.py
```

## Requirements 📋

```
torch>=2.0.0              # Deep Learning framework
torchvision>=0.15.0       # Computer Vision
Pillow>=9.0.0             # Image processing
imageio>=2.25.0           # Image I/O
numpy>=1.24.0             # Numerical computing
scikit-image>=0.20.0      # PSNR/SSIM metrics
matplotlib>=3.7.0         # Visualization
opencv-python>=4.8.0      # OpenCV
scipy>=1.14.0             # Scientific computing (Python 3.13+)
pycryptodome>=3.17.0      # RSA+AES encryption
reedsolo>=1.7.0           # Error correction
psutil>=5.9.0             # System monitoring
pyinstaller>=5.10.0       # Build tool
```

Auto-installed by `build_app.bat`

## Usage Guide

### 1. Encode (Giấu tin)

1. Tab **🖼️ Encode**
2. Chọn ảnh cover
3. Nhập tin nhắn
4. (Optional) Enable RSA+AES encryption
5. Click **Encode**
6. Lưu ảnh stego

### 2. Decode (Trích xuất)

1. Tab **🔍 Decode**
2. Chọn ảnh stego
3. (If encrypted) Enable decryption + chọn private key
4. Click **Decode**
5. Xem tin nhắn

### 3. Reverse (Khôi phục)

1. Tab **↩️ Reverse**
2. Chọn ảnh stego
3. Click **Reverse**
4. Lưu ảnh recovered

### 4. GenRSA (Tạo khóa)

1. Tab **🔐 GenRSA**
2. Chọn key size (2048 bits recommended)
3. Chọn thư mục lưu
4. Click **Tạo khóa**
5. Nhận public_key.pem + private_key.pem

### 5. Compare (So sánh)

1. Tab **📊 Compare**
2. Chọn 2 ảnh
3. Click **Tính Metrics**
4. Xem PSNR/SSIM/MSE
5. (Optional) Lưu comparison image

## Workflow Examples

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

### App không mở / crash ngay khi khởi động

```batch
REM Chạy từ command prompt để xem lỗi
cd dist
CustomGANStego.exe

REM Nếu bị antivirus block, thêm exception
REM Windows Security > Virus & threat protection > Exclusions
```

### Model not found

```batch
cd ..
python train.py  # Train models first
```

### Dependencies missing

```batch
pip install -r requirements.txt
```

### scipy import error (NameError: 'obj')

```batch
REM Lỗi này xảy ra với scipy 1.11.x
REM Cần scipy>=1.14.0 cho Python 3.13

pip uninstall scipy
pip install "scipy>=1.14.0"
```

### PyInstaller build failed

```batch
REM Clean build
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q venv

REM Rebuild
build_app.bat
```

### Windows Defender blocks exe

1. Open Windows Security
2. Virus & threat protection
3. Protection history
4. Allow the blocked app
5. Or add exclusion for `dist\CustomGANStego.exe`

## Structure

```
windowsApp/
├── steganography_app.py      # Main app
├── build_app.bat             # Build script (with all hidden imports)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── build/                    # Build artifacts (ignored)
└── dist/                     # Distribution
    └── CustomGANStego.exe    # Windows executable
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
- First run may take 10-15 seconds to extract

## Hướng dẫn sử dụng chi tiết

### 1. Encode - Giấu tin vào ảnh

**Bước 1:** Chọn ảnh Cover
- Click nút "Chọn ảnh..."
- Chọn ảnh PNG/JPG làm cover image

**Bước 2:** Nhập tin cần giấu
- Gõ hoặc paste tin nhắn vào text box
- Có thể nhập văn bản dài tùy ý

**Bước 3:** (Tùy chọn) Bật mã hóa
- Check "Sử dụng mã hóa RSA+AES"
- Chọn public key (.pem file)

**Bước 4:** Encode
- Click "Encode"
- Chọn nơi lưu ảnh stego
- Đợi quá trình hoàn tất

**Kết quả:** Ảnh stego với tin đã được giấu bên trong

---

### 2. Decode - Trích xuất tin

**Bước 1:** Chọn ảnh Stego
- Click "Chọn ảnh..."
- Chọn ảnh stego đã tạo trước đó

**Bước 2:** (Nếu có mã hóa) Giải mã
- Check "Giải mã RSA+AES"
- Chọn private key (.pem file)

**Bước 3:** Decode
- Click "Decode"
- Tin nhắn sẽ hiển thị trong text box

**Bước 4:** Lưu kết quả (optional)
- Click "Save"
- Lưu tin nhắn ra file .txt

---

### 3. Reverse - Khôi phục ảnh gốc

**Bước 1:** Chọn ảnh Stego
- Click "Chọn ảnh..."
- Chọn ảnh stego cần khôi phục

**Bước 2:** Reverse
- Click "Reverse"
- Chọn nơi lưu ảnh đã khôi phục
- Đợi quá trình xử lý

**Bước 3:** Xem kết quả
- Ảnh stego và recovered sẽ hiển thị song song
- So sánh trực quan

---

### 4. GenRSA - Tạo cặp khóa RSA

**Bước 1:** Chọn độ dài khóa
- 1024 bits - Nhanh, bảo mật thấp
- 2048 bits - Khuyến nghị (default)
- 3072 bits - Bảo mật cao
- 4096 bits - Bảo mật rất cao, chậm hơn

**Bước 2:** Chọn thư mục lưu
- Click "Chọn thư mục..."
- Chọn nơi lưu cặp khóa

**Bước 3:** Tạo khóa
- Click "Tạo khóa"
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
- Click "Tính Metrics"
- Đợi tính toán

**Kết quả hiển thị:**

**Metrics:**
- **PSNR** (Peak Signal-to-Noise Ratio)
  - \> 40 dB: Chất lượng rất tốt
  - \> 30 dB: Chất lượng tốt
  - < 30 dB: Chất lượng trung bình
- **SSIM** (Structural Similarity Index)
  - \> 0.95: Tương đồng rất cao
  - \> 0.90: Tương đồng cao
  - < 0.90: Tương đồng trung bình
- **MSE** (Mean Squared Error)
  - Càng nhỏ càng tốt

---

## Workflow điển hình

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

## So sánh với các phương pháp khác

| Phương pháp        | PSNR   | SSIM  | Dung lượng | Tốc độ     | Reverse |
| ------------------ | ------ | ----- | ---------- | ---------- | ------- |
| **CustomGANStego** | 40+ dB | 0.99+ | Cao        | Nhanh      | ✅ Có   |
| LSB                | 50+ dB | 0.99+ | Thấp       | Rất nhanh  | ❌ Không|
| DCT-based          | 40+ dB | 0.95+ | Trung bình | Trung bình | ❌ Không|
| DWT-based          | 35+ dB | 0.93+ | Trung bình | Chậm       | ❌ Không|

**Ưu điểm CustomGANStego:**

- ✅ Khả năng reverse (khôi phục ảnh gốc)
- ✅ PSNR cao (>45 dB)
- ✅ SSIM rất cao (>0.99)
- ✅ Chống steganalysis tốt nhờ GAN
- ✅ Tích hợp mã hóa RSA+AES

---

## 🔐 Bảo mật

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

## 👨‍💻 Development

### Run with debugging

```batch
python steganography_app.py --debug
```

### Rebuild after changes

```batch
build_app.bat
```

### Clean build

```batch
rmdir /s /q build dist venv __pycache__
build_app.bat
```

---

## Tài liệu tham khảo

- **Paper:** "Hiding Images in Plain Sight: Deep Steganography" (Baluja, 2017)
- **GAN:** "Generative Adversarial Networks" (Goodfellow et al., 2014)
- **RSA:** "A Method for Obtaining Digital Signatures" (Rivest et al., 1978)

---

## License

Project CustomGANStego - CNTT

---

## Credits

- PyTorch Team
- scikit-image
- PyCryptodome
- PyInstaller
- CustomGANStego Team

---

**🎉 Chúc bạn sử dụng app thành công!**

Nếu có vấn đề, vui lòng mở issue trên GitHub.

