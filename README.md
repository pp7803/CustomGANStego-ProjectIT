# CustomGANStego

## Giới thiệu

CustomGANStego là hệ thống giấu tin (steganography) dựa trên Generative Adversarial Networks (GAN), cho phép nhúng thông tin bí mật vào ảnh với chất lượng cao và khả năng khôi phục ảnh gốc (reversible steganography).

### Tính năng chính

- Giấu tin sử dụng kiến trúc GAN với WGAN-GP
- Hỗ trợ mã hóa hybrid RSA + AES cho bảo mật cao
- Khả năng khôi phục ảnh cover từ ảnh stego (Reverse Hiding)
- Đạt độ chính xác giải mã cao (>95%)
- Chất lượng ảnh stego tốt (PSNR >35dB, SSIM >0.90)
- Hỗ trợ nhiều nền tảng: CUDA, MPS (Apple Silicon), CPU

### Kiến trúc hệ thống

Hệ thống bao gồm 4 module chính:

1. **Encoder**: Nhúng thông tin vào ảnh cover để tạo ảnh stego
2. **Decoder**: Trích xuất thông tin từ ảnh stego
3. **Critic**: Phân biệt ảnh cover và ảnh stego (adversarial training)
4. **Reverse Decoder**: Khôi phục ảnh cover từ ảnh stego

## Yêu cầu hệ thống

### Phần cứng

- GPU khuyến nghị: NVIDIA GPU với CUDA hoặc Apple Silicon với MPS
- RAM: Tối thiểu 8GB, khuyến nghị 16GB+
- Dung lượng: Tối thiểu 10GB cho dataset và models

### Phần mềm

- Python 3.8+
- PyTorch 1.13+
- CUDA 11.0+ (nếu sử dụng NVIDIA GPU)

## Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd CustomGANStego
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

Các thư viện chính:
- torch
- torchvision
- torchmetrics
- pillow
- imageio
- scikit-image
- reedsolo
- pycryptodome (tùy chọn, cho encryption)

### 3. Chuẩn bị dataset

Dataset mặc định: DIV2K

Cấu trúc thư mục:
```
div2k/
├── train/
│   └── images/
└── val/
    └── images/
```

Tải dataset:
```bash
bash scripts/download-dataset.sh
```

Hoặc tải thủ công từ: https://data.vision.ee.ethz.ch/cvl/DIV2K/

## Hướng dẫn sử dụng

### 1. Training Model

#### Cấu hình training

Mở file `train.py` và điều chỉnh các hyperparameters:

```python
epochs = 60              # Số epoch
batch_size = 4           # Batch size
data_depth = 2           # Độ sâu data channel
hidden_size = 32         # Kích thước hidden layers

# Learning rates
lr_critic = 2e-4
lr_encoder_decoder = 2e-4

# Loss weights
weight_mse = 50.0
weight_ssim = 20.0
weight_perceptual = 5.0
weight_decoder = 10.0
weight_adversarial = 0.005
weight_reverse = 50.0
```

#### Chạy training

```bash
python train.py
```

Model sẽ được lưu trong thư mục `results/model/` với tên format:
```
accX.XXXX_psnrXX.XX_ssimX.XXXX_YYYY-MM-DD_HH:MM:SS.dat
```

Ví dụ: `acc0.9534_psnr35.12_ssim0.9234_2025-12-23_10:30:45.dat`

#### Theo dõi quá trình training

Training plots được lưu trong `results/plots/`. Để xem tổng hợp:

```bash
python plotsummary.py
```

Metrics được theo dõi:
- Decoder Accuracy: Độ chính xác trích xuất
- PSNR: Chất lượng ảnh stego
- SSIM: Độ tương đồng cấu trúc
- Reverse PSNR/SSIM: Chất lượng khôi phục
- Encoder MSE: Sai số encoder
- Decoder Loss: Loss của decoder
- BPP: Bits per pixel

### 2. Giấu tin (Encoding)

#### Chế độ cơ bản (không mã hóa)

```bash
python runencode.py <cover_image> "<secret_text>"
```

Ví dụ:
```bash
python runencode.py test.png "This is my secret message"
```

Output mặc định: `stego_<input_name>.png`

#### Chỉ định file output

```bash
python runencode.py cover.png "Secret" --output my_stego.png
```

#### Chế độ mã hóa (RSA + AES)

Tạo cặp khóa RSA:
```bash
python genRSA.py --bits 2048 --public public_key.pem --private private_key.pem
```

Encode với encryption:
```bash
python runencode.py cover.png "Confidential message" --encrypt --public-key public_key.pem
```

#### Chỉ định model cụ thể

```bash
python runencode.py cover.png "Secret" --model results/model/acc0.95_psnr35.dat
```

Nếu không chỉ định `--model`, hệ thống tự động chọn model tốt nhất từ `results/model/`.

### 3. Trích xuất tin (Decoding)

#### Chế độ cơ bản

```bash
python rundecode.py <stego_image>
```

Ví dụ:
```bash
python rundecode.py stego_test.png
```

#### Lưu kết quả vào file

```bash
python rundecode.py stego.png output.txt
```

#### Giải mã với encryption

```bash
python rundecode.py stego.png --encrypt --private-key private_key.pem
```

Hoặc lưu vào file:
```bash
python rundecode.py stego.png secret.txt --encrypt --private-key private_key.pem
```

### 4. Khôi phục ảnh gốc (Reverse Hiding)

```bash
python runreverse.py <stego_image>
```

Ví dụ:
```bash
python runreverse.py stego_test.png
```

Output mặc định: `<input_name>_reversehiding.png`

Chỉ định output:
```bash
python runreverse.py stego.png recovered_cover.png
```

### 5. Đánh giá chất lượng

Tính PSNR và SSIM giữa các ảnh:

```bash
python compute_metrics.py
```

Chỉnh sửa đường dẫn ảnh trong file để so sánh:
- Cover vs Stego: Đánh giá chất lượng giấu tin
- Cover vs Recovered: Đánh giá khả năng khôi phục

## Cấu trúc thư mục

```
CustomGANStego/
├── train.py                  # Training script
├── runencode.py             # Encode script (giấu tin)
├── rundecode.py             # Decode script (trích xuất)
├── runreverse.py            # Reverse hiding script
├── genRSA.py                # Generate RSA keypairs
├── compute_metrics.py       # Tính metrics PSNR/SSIM
├── plotsummary.py           # Visualize training progress
├── encoder.py               # Encoder models
├── decoder.py               # Decoder models
├── critic.py                # Critic model
├── reverse_decoder.py       # Reverse decoder model
├── enhancedstegan.py        # Core steganography functions
├── requirements.txt         # Dependencies
├── div2k/                   # Dataset directory
│   ├── train/
│   │   └── images/
│   └── val/
│       └── images/
├── results/                 # Training outputs
│   ├── model/              # Saved models
│   └── plots/              # Training plots
├── macOSApp/               # macOS application
├── windowsApp/             # Windows application
└── webApp/                 # Web application
    ├── BE/                 # Backend (Node.js)
    └── FE/                 # Frontend (React)
```

## Lưu ý quan trọng

### Training

1. **Dataset**: Đảm bảo dataset DIV2K được đặt đúng vị trí trong `div2k/train/images/` và `div2k/val/images/`

2. **Memory**: Training yêu cầu GPU với memory đủ lớn. Nếu gặp lỗi OOM (Out of Memory), giảm `batch_size` trong `train.py`

3. **Device**: Hệ thống tự động phát hiện device (CUDA > MPS > CPU). Để force CPU:
   ```python
   device = torch.device('cpu')
   ```

4. **Convergence**: Model thường đạt target sau 40-50 epochs. Có thể stop early nếu metrics đã đạt yêu cầu

5. **Checkpoint**: Model tốt nhất được lưu dựa trên:
   - Decoder Accuracy >= 95%
   - PSNR >= 35 dB
   - SSIM >= 0.90

### Encoding/Decoding

1. **Format ảnh**: Hỗ trợ PNG, JPG, BMP. Khuyến nghị PNG để giữ chất lượng

2. **Kích thước**: Ảnh cover nên có kích thước đủ lớn để chứa message. Capacity phụ thuộc vào `data_depth`

3. **Model consistency**: Phải dùng cùng model (hoặc model cùng architecture) cho encode và decode

4. **Encryption**:
   - Public key cho encoding
   - Private key cho decoding
   - Không mất private key, không thể giải mã
   - RSA key size: 2048 hoặc 4096 bits

5. **Error correction**: Hệ thống tự động apply Reed-Solomon error correction code để tăng độ tin cậy

### Reverse Hiding

1. **Lossless recovery**: Có thể khôi phục gần như hoàn toàn ảnh cover gốc

2. **Quality**: Reverse PSNR thường đạt >35 dB, Reverse SSIM >0.90

3. **Security**: Sau khi reverse, không còn흔 tích của steganography trong ảnh

### Performance

1. **Decoder Accuracy**: Target >= 95% để đảm bảo trích xuất chính xác

2. **PSNR**: 
   - >40 dB: Excellent (không nhìn thấy khác biệt)
   - 35-40 dB: Good (khác biệt rất nhỏ)
   - 30-35 dB: Acceptable (có thể nhận thấy nhẹ)

3. **SSIM**:
   - >0.95: Excellent
   - 0.90-0.95: Good
   - <0.90: Cần cải thiện

## Troubleshooting

### Lỗi thường gặp

**1. CUDA Out of Memory**
```
RuntimeError: CUDA out of memory
```
Giải pháp: Giảm `batch_size` trong `train.py`

**2. Dataset not found**
```
FileNotFoundError: div2k/train/images
```
Giải pháp: Chạy `bash scripts/download-dataset.sh` hoặc tạo thư mục thủ công

**3. Model not found**
```
No model found. Train a model first
```
Giải pháp: Chạy `python train.py` để train model

**4. Crypto module not found**
```
ModuleNotFoundError: No module named 'Crypto'
```
Giải pháp: `pip install pycryptodome`

**5. Decoding accuracy thấp**

Nguyên nhân:
- Model chưa được train đủ
- Dùng sai model cho decode
- Ảnh stego bị nén hoặc biến đổi

Giải pháp:
- Train thêm epochs
- Dùng đúng model đã encode
- Lưu ảnh stego ở format lossless (PNG)

### Tối ưu hóa

**Training nhanh hơn:**
- Tăng `batch_size` nếu GPU memory cho phép
- Giảm `n_critic` xuống 1-2
- Tăng learning rate (nhưng cẩn thận với stability)

**Chất lượng cao hơn:**
- Tăng `epochs`
- Tăng `weight_mse` và `weight_ssim`
- Giảm `weight_decoder` một chút (trade-off accuracy vs quality)

**Decoder accuracy cao hơn:**
- Tăng `weight_decoder` lên 15-20
- Giảm các weight khác
- Train đủ epochs cho convergence

## Tài liệu tham khảo

1. Goodfellow, I., et al. (2014). Generative Adversarial Networks
2. Arjovsky, M., et al. (2017). Wasserstein GAN
3. Gulrajani, I., et al. (2017). Improved Training of Wasserstein GANs
4. Zhu, J., et al. (2018). HiDDeN: Hiding Data with Deep Networks
5. Baluja, S. (2017). Hiding Images in Plain Sight: Deep Steganography

## License

MIT License

## Contact

Để báo lỗi hoặc đóng góp, vui lòng tạo issue trên GitHub repository.
