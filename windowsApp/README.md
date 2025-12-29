# CustomGANStego Windows Application

Ứng dụng Windows với giao diện đồ họa cho hệ thống giấu tin (steganography) sử dụng Deep Learning với GAN.

## Features

- **📝 Encode** - Giấu tin vào ảnh với GAN
- **🔍 Decode** - Trích xuất tin từ ảnh stego
- **⏮️ Reverse** - Khôi phục ảnh gốc (lossless)
- **🔑 GenRSA** - Tạo khóa RSA cho mã hóa
- **📊 Compare** - Tính PSNR/SSIM/MSE metrics
- **🔒 Encryption** - RSA+AES hybrid encryption

## Quick Start

### One-Command Build

```cmd
cd windowsApp
build_app.bat
```

**Output:**

- `dist\CustomGANStego.exe` - Windows executable (~150-200 MB)

Script sẽ tự động:

1. ✅ Kiểm tra Python và dependencies
2. ✅ Tạo/activate virtual environment
3. ✅ Cài đặt packages thiếu
4. ✅ Kiểm tra model files
5. ✅ Build executable với PyInstaller
6. ✅ Hướng dẫn sử dụng

### Run Application

**Từ Build:**

```cmd
dist\CustomGANStego.exe
```

**Hoặc Double-click:**

- Mở Windows Explorer
- Vào thư mục `dist\`
- Double-click `CustomGANStego.exe`

**Development Mode:**

```cmd
cd windowsApp
python steganography_app.py
```

## Requirements

### System Requirements

- **OS**: Windows 7/8/10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Python**: 3.8+ (for building only, not needed for running .exe)

### Build Requirements

Nếu build từ source:

```cmd
pip install -r requirements.txt
```

Dependencies chính:

- torch>=2.0.0
- torchvision>=0.15.0
- Pillow>=9.0.0
- scikit-image>=0.20.0
- pycryptodome>=3.17.0
- pyinstaller>=5.10.0

## 🔨 Build từ Source

### Bước 1: Setup môi trường

```cmd
cd windowsApp
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Bước 2: Chuẩn bị model

Đảm bảo có model trong `results\model\`:

```cmd
dir ..\results\model\*.dat
```

Nếu chưa có, train model trước:

```cmd
cd ..
python train.py
cd windowsApp
```

### Bước 3: Build executable

**Tự động (khuyến nghị):**

```cmd
build_app.bat
```

**Thủ công:**

```cmd
pyinstaller --clean ^
    --name="CustomGANStego" ^
    --windowed ^
    --onefile ^
    --add-data="../results/model;results/model" ^
    --add-data="../encoder.py;." ^
    --add-data="../decoder.py;." ^
    --add-data="../critic.py;." ^
    --add-data="../reverse_decoder.py;." ^
    --add-data="../enhancedstegan.py;." ^
    --hidden-import=torch ^
    --collect-all torch ^
    steganography_app.py
```

### Bước 4: Test executable

```cmd
dist\CustomGANStego.exe
```

## Sử dụng Application

### Interface Overview

App có 5 tabs chính:

1. **📝 Encode Tab**

   - Chọn ảnh cover
   - Nhập tin cần giấu
   - Tùy chọn mã hóa RSA+AES
   - Export ảnh stego

2. **🔍 Decode Tab**

   - Chọn ảnh stego
   - Tùy chọn giải mã
   - Xem/lưu tin đã trích xuất

3. **⏮️ Reverse Tab**

   - Chọn ảnh stego
   - Khôi phục ảnh cover gốc
   - Preview trước/sau

4. **🔑 GenRSA Tab**

   - Tạo cặp khóa RSA
   - Chọn độ dài khóa (1024-4096 bits)
   - Lưu public/private key

5. **📊 Compare Tab**
   - So sánh 2 ảnh
   - Tính PSNR/SSIM/MSE
   - Hiển thị difference map

### Workflow Example

#### 1. Tạo khóa RSA (lần đầu)

- Vào tab **🔑 GenRSA**
- Chọn độ dài khóa: 2048 bits
- Chọn thư mục lưu
- Click "🔑 Tạo khóa"
- Lưu `public_key.pem` và `private_key.pem`

#### 2. Giấu tin có mã hóa

- Vào tab **📝 Encode**
- Click "Chọn ảnh..." → chọn ảnh cover
- Nhập tin cần giấu
- ✅ Check "Sử dụng mã hóa RSA+AES"
- Click "Chọn public key..." → chọn `public_key.pem`
- Click "🚀 Encode"
- Lưu ảnh stego

#### 3. Trích xuất tin

- Vào tab **🔍 Decode**
- Click "Chọn ảnh..." → chọn ảnh stego
- ✅ Check "Giải mã RSA+AES"
- Click "Chọn private key..." → chọn `private_key.pem`
- Click "🔍 Decode"
- Tin sẽ hiển thị trong textbox
- Có thể click "💾 Save" để lưu ra file

#### 4. Khôi phục ảnh gốc

- Vào tab **⏮️ Reverse**
- Click "Chọn ảnh..." → chọn ảnh stego
- Click "⏮️ Reverse"
- Lưu ảnh đã khôi phục
- Preview hiển thị stego vs recovered

#### 5. Đánh giá chất lượng

- Vào tab **📊 Compare**
- Click "Chọn ảnh 1..." → chọn cover gốc
- Click "Chọn ảnh 2..." → chọn stego/recovered
- Click "📊 Tính Metrics"
- Xem PSNR/SSIM/MSE
- Click "💾 Save PNG" để lưu comparison

## Customization

### Theme & Style

File `steganography_app.py` sử dụng Windows native theme:

```python
style = ttk.Style()
style.theme_use('vista')  # Windows Vista/7/8/10/11
```

Có thể thay đổi theme:

- `'winnative'` - Windows classic
- `'clam'` - Modern flat
- `'alt'` - Alternative
- `'default'` - Default

### Window Size

Mặc định: 1200x800

Thay đổi trong `steganography_app.py`:

```python
self.root.geometry("1400x900")  # Larger window
```

### Icon

Thêm icon cho app:

1. Tạo file `icon.ico` (256x256 hoặc 128x128)
2. Đặt trong thư mục `windowsApp\`
3. Update build command:
   ```cmd
   --icon=icon.ico
   ```

## 📦 Distribution

### Chuẩn bị cho Distribution

**File cần có:**

- `dist\CustomGANStego.exe` - Ứng dụng chính

**Optional:**

- `README.txt` - Hướng dẫn sử dụng
- `sample_images\` - Ảnh mẫu để test
- `LICENSE.txt` - License information

### Tạo Installer (Optional)

Sử dụng NSIS hoặc Inno Setup để tạo installer:

**Inno Setup Script Example:**

```iss
[Setup]
AppName=CustomGANStego
AppVersion=1.0
DefaultDirName={pf}\CustomGANStego
DefaultGroupName=CustomGANStego
OutputDir=installer
OutputBaseFilename=CustomGANStego-Setup

[Files]
Source: "dist\CustomGANStego.exe"; DestDir: "{app}"
Source: "README.txt"; DestDir: "{app}"

[Icons]
Name: "{group}\CustomGANStego"; Filename: "{app}\CustomGANStego.exe"
```

### Code Signing (Optional)

Để tránh Windows SmartScreen warning:

1. Mua code signing certificate
2. Sign executable:
   ```cmd
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\CustomGANStego.exe
   ```

## Troubleshooting

### App không khởi động

**Triệu chứng:** Double-click không có gì xảy ra

**Giải pháp:**

1. Chạy từ Command Prompt để xem error:
   ```cmd
   dist\CustomGANStego.exe
   ```
2. Check Windows Event Viewer → Application logs
3. Tạm tắt Antivirus và thử lại

### Antivirus cảnh báo

**Triệu chứng:** Windows Defender/Antivirus block .exe

**Giải pháp:**

- False positive do PyInstaller
- Thêm exception trong Antivirus
- Upload file lên VirusTotal để verify
- Submit false positive report đến antivirus vendor

### DLL không tìm thấy

**Triệu chứng:** Error "VCRUNTIME140.dll not found"

**Giải pháp:**

- Cài Visual C++ Redistributable:
  https://aka.ms/vs/17/release/vc_redist.x64.exe

### Model không load

**Triệu chứng:** "⚠️ No model found"

**Giải pháp:**

1. Check model files trong build:
   ```cmd
   pyinstaller --log-level DEBUG ...
   ```
2. Verify --add-data path đúng
3. Rebuild với đường dẫn model chính xác

### App chậm khởi động

**Triệu chứng:** Lần đầu mở mất 10-20 giây

**Giải pháp:**

- Normal behavior (PyInstaller extract files)
- Lần sau sẽ nhanh hơn
- Không thể tránh với --onefile mode

### Out of Memory

**Triệu chứng:** App crash khi encode ảnh lớn

**Giải pháp:**

- Giảm kích thước ảnh input
- Resize ảnh xuống 1024x1024 hoặc nhỏ hơn
- Tăng RAM máy tính

## Advanced

### Multi-file Build

Nếu muốn build nhỏ hơn (không bundle everything):

```cmd
pyinstaller --onedir steganography_app.py
```

Tạo thư mục `dist\CustomGANStego\` với nhiều files.

### Custom PyInstaller Spec

Tạo file `steganography_app.spec` để customize:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['steganography_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../results/model', 'results/model'),
        ('../*.py', '.'),
    ],
    hiddenimports=['torch', 'torchvision', 'PIL', 'numpy', 'skimage', 'Crypto'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CustomGANStego',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    console=False,  # Windowed mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

Build với spec:

```cmd
pyinstaller steganography_app.spec
```

### UPX Compression

Giảm kích thước exe với UPX:

1. Download UPX: https://upx.github.io/
2. Extract vào PATH
3. Build với `--upx-dir`:
   ```cmd
   pyinstaller --upx-dir=C:\path\to\upx ...
   ```

## Additional Resources

- **PyInstaller Docs**: https://pyinstaller.org/
- **Windows Dev Center**: https://developer.microsoft.com/windows/
- **Inno Setup**: https://jrsoftware.org/isinfo.php
- **NSIS**: https://nsis.sourceforge.io/

## Support

Nếu gặp vấn đề:

1. Check [Troubleshooting](#-troubleshooting) section
2. Run với console mode để xem errors:
   ```cmd
   pyinstaller --console steganography_app.py
   ```
3. Create issue trên GitHub với:
   - Windows version
   - Python version
   - Error message/screenshot
   - Build log

## License

MIT License - Xem file LICENSE trong project root.

## Credits

- **CustomGANStego Team**
- Built with PyInstaller, PyTorch, and tkinter
- Windows-optimized version
