# CustomGANStego Web API

RESTful API for GAN-based steganography operations. Hide messages in images, extract hidden messages, and perform image analysis.

## Features

- **Encode**: Hide secret messages in images using GAN
- **Decode**: Extract hidden messages from stego images
- **Reverse**: Recover original cover image (lossless)
- **Compare**: Calculate PSNR/SSIM/MSE metrics between images
- **GenRSA**: Generate RSA key pairs for encryption
- **Encryption**: Optional RSA+AES hybrid encryption for messages

## Project Structure

```
webApp/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── encoder.py             # Encoder neural network
│   ├── decoder.py             # Decoder neural network
│   ├── critic.py              # Critic network
│   ├── reverse_decoder.py     # Reverse decoder
│   ├── enhancedstegan.py      # Core steganography functions
│   ├── requirements.txt       # Python dependencies
│   ├── setup.sh               # Setup script
│   ├── venv/                  # Virtual environment (auto-created)
│   ├── results/               # Model files
│   ├── uploads/               # Temporary uploads
│   ├── outputs/               # Generated outputs
│   └── keys/                  # Generated RSA keys
└── README.md
```

## Quick Start

### 1. Setup

```bash
cd webApp/backend
./setup.sh
```

This will:

- Create a Python virtual environment
- Install all dependencies
- Prepare the API server

### 2. Run Development Server

```bash
source venv/bin/activate
python app.py
```

Server runs at: `http://localhost:5000`

### 3. Run Production Server

```bash
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 app:app
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
  "crypto_available": true
}
```

### Encode (Hide Message)

```http
POST /encode
Content-Type: multipart/form-data

cover_image: [file]
message: "Secret message"
use_encryption: true (optional)
public_key: [file] (if use_encryption=true)
return_url: true (optional, default=true)
```

Response (when return_url=true):
```json
{
  "success": true,
  "stego_url": "http://localhost:5000/files/uuid_stego.png",
  "filename": "uuid_stego.png"
}
```

Response (when return_url=false): PNG image file (direct download)

### Decode (Extract Message)

```http
POST /decode
Content-Type: multipart/form-data

Method 1 - Upload file:
stego_image: [file]
use_decryption: true (optional)
private_key: [file] (if use_decryption=true)

Method 2 - Use URL:
stego_url: "http://example.com/image.png"
use_decryption: true (optional)
private_key: [file] (if use_decryption=true)
```

Response:
```json
{
  "success": true,
  "message": "Secret message"
}
```

### Reverse (Recover Original)

```http
POST /reverse
Content-Type: multipart/form-data

stego_image: [file]
```

Response: PNG image file (recovered cover)

### Compare (Calculate Metrics)

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

### Generate RSA Keys

```http
POST /genrsa
Content-Type: multipart/form-data

key_size: 2048
```

Response: ZIP file containing `private_key.pem` and `public_key.pem`

### Serve Files

```http
GET /files/<filename>
```

Returns the image file from server outputs folder.

## Example Usage

### Using cURL

**Encode (return URL):**
```bash
curl -X POST http://localhost:5000/encode \
  -F "cover_image=@cover.png" \
  -F "message=Hello World" \
  -F "return_url=true"
```

Response:
```json
{
  "success": true,
  "stego_url": "http://localhost:5000/files/abc123_stego.png",
  "filename": "abc123_stego.png"
}
```

**Encode (download file):**
```bash
curl -X POST http://localhost:5000/encode \
  -F "cover_image=@cover.png" \
  -F "message=Hello World" \
  -F "return_url=false" \
  -o stego.png
```

**Decode from uploaded file:**
```bash
curl -X POST http://localhost:5000/decode \
  -F "stego_image=@stego.png"
```

**Decode from URL:**
```bash
curl -X POST http://localhost:5000/decode \
  -F "stego_url=http://example.com/stego.png"
```

**Reverse:**

```bash
curl -X POST http://localhost:5000/reverse \
  -F "stego_image=@stego.png" \
  -o recovered.png
```

**Compare:**

```bash
curl -X POST http://localhost:5000/compare \
  -F "image1=@cover.png" \
  -F "image2=@stego.png"
```

**Generate RSA Keys:**

```bash
curl -X POST http://localhost:5000/genrsa \
  -F "key_size=2048" \
  -o keys.zip
```

### Using Python

```python
import requests

# Encode
with open('cover.png', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/encode',
        files={'cover_image': f},
        data={'message': 'Secret message'}
    )
    with open('stego.png', 'wb') as out:
        out.write(response.content)

# Decode
with open('stego.png', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/decode',
        files={'stego_image': f}
    )
    print(response.json()['message'])
```

## Configuration

Edit `app.py` to configure:

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
```

## Requirements

- Python 3.8+
- 4GB RAM minimum (8GB recommended)
- CUDA GPU (optional, for faster processing)

## Dependencies

Core:

- Flask 2.3+
- PyTorch 2.0+
- Pillow 9.0+
- scikit-image 0.20+
- pycryptodome 3.17+

See `requirements.txt` for complete list.

## Security Notes

1. **File Uploads**: Files are auto-deleted after 24 hours
2. **Encryption**: Use RSA+AES for sensitive messages
3. **API Keys**: Add authentication for production use
4. **HTTPS**: Use reverse proxy (nginx) with SSL in production

## Production Deployment

### Using Nginx

1. Install nginx and configure reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. Run with gunicorn:

```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t customganstego-api .
docker run -p 5000:5000 customganstego-api
```

## Troubleshooting

**Import Error:**

```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Model Not Found:**

```bash
# Ensure results/model/ exists with .dat files
ls -la results/model/
```

**Port Already in Use:**

```bash
# Change port in app.py or use environment variable
export FLASK_RUN_PORT=5001
python app.py
```

## Performance

- **Encode**: ~2-5 seconds per image
- **Decode**: ~1-3 seconds per image
- **Reverse**: ~2-4 seconds per image
- **Compare**: < 1 second

_Times vary based on image size and hardware_

## API Rate Limiting

For production, add rate limiting:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/encode', methods=['POST'])
@limiter.limit("10 per minute")
def encode():
    ...
```

## License

MIT License - See LICENSE in project root

## Support

For issues and questions, see main project README or create an issue on GitHub.
