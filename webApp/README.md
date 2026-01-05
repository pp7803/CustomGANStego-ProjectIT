# CustomGANStego Web API

RESTful API cho các thao tác steganography dựa trên GAN. Giấu tin trong ảnh, trích xuất tin ẩn và phân tích ảnh.

## Tính năng

- **Encode**: Giấu tin bí mật vào ảnh sử dụng GAN
- **Decode**: Trích xuất tin ẩn từ ảnh stego
- **Reverse**: Khôi phục ảnh cover gốc (lossless)
- **Compare**: Tính toán metrics PSNR/SSIM/MSE giữa các ảnh
- **GenRSA**: Tạo cặp khóa RSA cho mã hóa
- **Encryption**: Mã hóa lai RSA+AES tùy chọn cho tin nhắn

## Cấu trúc dự án

```
webApp/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── encoder.py             # Mạng nơ-ron Encoder
│   ├── decoder.py             # Mạng nơ-ron Decoder
│   ├── critic.py              # Mạng Critic
│   ├── reverse_decoder.py     # Reverse decoder
│   ├── enhancedstegan.py      # Hàm steganography cốt lõi
│   ├── requirements.txt       # Dependencies Python
│   ├── setup.sh               # Script thiết lập
│   ├── venv/                  # Môi trường ảo (tự động tạo)
│   ├── model/                 # File model
│   ├── uploads/               # Upload tạm thời
│   ├── outputs/               # Đầu ra được tạo
│   └── keys/                  # Khóa RSA được tạo
└── frontend/
    ├── src/                   # React source code
    ├── package.json           # Node dependencies
    └── vite.config.js         # Vite config
```

## Khởi động nhanh

### 1. Thiết lập Backend

```bash
cd webApp/backend
./setup.sh
```

Script này sẽ:

- Tạo môi trường ảo Python
- Cài đặt tất cả dependencies
- Chuẩn bị API server

### 2. Chạy Development Server (Backend)

```bash
source venv/bin/activate
python app.py
```

Server chạy tại: `http://localhost:3012`

### 3. Thiết lập và chạy Frontend

```bash
cd webApp/frontend
npm install
npm run dev
```

Frontend chạy tại: `http://localhost:5000`

### 4. Chạy Production Server

**Backend:**

```bash
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:3012 --timeout 600 app:app
```

**Frontend:**

```bash
npm run build
npm run preview
```

## API Endpoints

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "healthy",
  "service": "CustomGANStego API",
  "crypto_available": true,
  "python_version": "3.11.x",
  "torch_version": "2.x.x"
}
```

### Encode (Giấu tin)

```http
POST /encode
Content-Type: multipart/form-data

cover_image: [file]              # Ảnh cover
message: "Tin bí mật"            # Tin cần giấu
use_encryption: true             # Tùy chọn mã hóa
public_key: [file]               # Nếu use_encryption=true
return_url: true                 # Tùy chọn, mặc định=true
```

Response (khi return_url=true):

```json
{
  "success": true,
  "stego_url": "http://localhost:3012/files/uuid_stego.png",
  "filename": "uuid_stego.png"
}
```

Response (khi return_url=false): File ảnh PNG (tải trực tiếp)

### Decode (Trích xuất tin)

```http
POST /decode
Content-Type: multipart/form-data

Phương pháp 1 - Upload file:
stego_image: [file]              # Ảnh stego
use_decryption: true             # Tùy chọn giải mã
private_key: [file]              # Nếu use_decryption=true

Phương pháp 2 - Dùng URL:
stego_url: "http://example.com/image.png"
use_decryption: true
private_key: [file]
```

Response:

```json
{
  "success": true,
  "message": "Tin bí mật"
}
```

### Reverse (Khôi phục ảnh gốc)

```http
POST /reverse
Content-Type: multipart/form-data

stego_image: [file]
```

Response: File ảnh PNG (ảnh cover đã khôi phục)

### Compare (Tính metrics)

```http
POST /compare
Content-Type: multipart/form-data

image1: [file]
image2: [file]
```

Response:

```json
{
  "success": true,
  "metrics": {
    "psnr": 45.67,
    "ssim": 0.98,
    "mse": 12.34
  }
}
```

### Tạo khóa RSA

```http
POST /genrsa
Content-Type: multipart/form-data

key_size: 2048                   # 1024, 2048, 3072, hoặc 4096
```

Response: File ZIP chứa `private_key.pem` và `public_key.pem`

### Truy xuất file

```http
GET /files/<filename>
```

Trả về file ảnh từ thư mục outputs của server.

## Ví dụ sử dụng

### Sử dụng cURL

**Encode (trả về URL):**

```bash
curl -X POST http://localhost:3012/encode \
  -F "cover_image=@cover.png" \
  -F "message=Xin chào" \
  -F "return_url=true"
```

**Decode từ URL:**

```bash
curl -X POST http://localhost:3012/decode \
  -F "stego_url=http://localhost:3012/files/abc123_stego.png"
```

**Reverse:**

```bash
curl -X POST http://localhost:3012/reverse \
  -F "stego_image=@stego.png" \
  -o recovered.png
```

**Compare:**

```bash
curl -X POST http://localhost:3012/compare \
  -F "image1=@cover.png" \
  -F "image2=@stego.png"
```

**Tạo khóa RSA:**

```bash
curl -X POST http://localhost:3012/genrsa \
  -F "key_size=2048" \
  -o keys.zip
```

### Sử dụng Python

```python
import requests

# Encode - nhận URL
with open('cover.png', 'rb') as f:
    response = requests.post(
        'http://localhost:3012/encode',
        files={'cover_image': f},
        data={'message': 'Tin bí mật', 'return_url': 'true'}
    )
    result = response.json()
    stego_url = result['stego_url']

# Decode từ URL
response = requests.post(
    'http://localhost:3012/decode',
    data={'stego_url': stego_url}
)
print(response.json()['message'])
```

### Sử dụng JavaScript/React

```javascript
import { encodeImage, decodeImage } from "./api";

// Encode
const result = await encodeImage(coverFile, message, false);
console.log("Stego URL:", result.stego_url);

// Decode từ URL
const decoded = await decodeImage(null, stegoUrl, false);
console.log("Tin đã giải mã:", decoded.message);
```

## Cấu hình

Chỉnh sửa `app.py`:

```python
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Port configuration
app.run(host='0.0.0.0', port=3012, debug=True)
```

## Yêu cầu hệ thống

- Python 3.8+
- Node.js 16+ (cho frontend)
- 4GB RAM tối thiểu (8GB khuyến nghị)
- CUDA GPU (tùy chọn)

## Dependencies

**Backend:** Flask, PyTorch, Pillow, scikit-image, pycryptodome, gunicorn

**Frontend:** React, Vite, Axios, Tailwind CSS

Xem `backend/requirements.txt` và `frontend/package.json`.

## Lưu ý bảo mật

1. **Upload file**: Tự động xóa sau 24 giờ
2. **Mã hóa**: Dùng RSA+AES cho tin nhạy cảm
3. **HTTPS**: Dùng reverse proxy với SSL trong production
4. **CORS**: Đã cấu hình, điều chỉnh cho domain cụ thể

## Triển khai Production

### Nginx + Gunicorn

**Backend:**

```bash
gunicorn -w 4 -b 127.0.0.1:3012 --timeout 600 app:app
```

**Nginx config:**

```nginx
location /api {
    proxy_pass http://127.0.0.1:3012;
    proxy_read_timeout 600s;
}
```

**Frontend:**

```bash
npm run build
# Serve dist/ với nginx
```

### Docker

```bash
docker-compose up -d
```

## Khắc phục sự cố

**Model không tìm thấy:**

```bash
cp ../results/model/*.dat backend/model/
```

**Port đã dùng:**

```bash
lsof -i :3012
kill -9 <PID>
```

**Decode từ URL timeout:**

- Đã fix: Server detect localhost và đọc file local
- Hoặc dùng nhiều worker: `gunicorn -w 4`

## Hiệu năng

- Encode: ~2-5s/ảnh
- Decode: ~1-3s/ảnh
- Reverse: ~2-4s/ảnh
- Compare: <1s

## License

MIT License - Xem LICENSE trong thư mục gốc

## Hỗ trợ

Chi tiết API: `backend/API_EXAMPLES.txt`

---

**CustomGANStego Web API** - Steganography as a Service 🔒🖼️
