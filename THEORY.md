# Lý Thuyết Xây Dựng Mô Hình CustomGANStego

## Mục lục

1. [Generative Adversarial Networks (GAN)](#1-generative-adversarial-networks-gan)
2. [So sánh GAN và CNN](#2-so-sánh-gan-và-cnn)
3. [WGAN-GP trong Steganography](#3-wgan-gp-trong-steganography)
4. [Kiến trúc CustomGANStego](#4-kiến-trúc-customganstego)
5. [Loss Functions và Training Strategy](#5-loss-functions-và-training-strategy)
6. [Reverse Hiding - Tính Năng Độc Đáo](#6-reverse-hiding---tính-năng-độc-đáo)

---

## 1. Generative Adversarial Networks (GAN)

### 1.1 Khái niệm cơ bản

GAN là một framework học sâu được Ian Goodfellow và cộng sự giới thiệu năm 2014. GAN bao gồm hai mạng neural networks cạnh tranh với nhau:

**Generator (G)**: Mạng tạo dữ liệu giả từ noise hoặc input

- Input: Vector ngẫu nhiên hoặc dữ liệu cần transform
- Output: Dữ liệu synthetic (ảnh, âm thanh, text,...)
- Mục tiêu: Tạo dữ liệu giống thật nhất có thể để đánh lừa Discriminator

**Discriminator (D)**: Mạng phân biệt dữ liệu thật và giả

- Input: Dữ liệu (có thể là thật hoặc giả)
- Output: Xác suất dữ liệu là thật [0, 1]
- Mục tiêu: Phân biệt chính xác giữa dữ liệu thật và dữ liệu từ Generator

### 1.2 Quá trình Training

GAN được training theo cơ chế "adversarial" (đối kháng):

1. **Bước 1**: Discriminator được train trước

   - Nhận dữ liệu thật → output gần 1
   - Nhận dữ liệu giả từ Generator → output gần 0
   - Mục tiêu: Maximize khả năng phân biệt

2. **Bước 2**: Generator được train

   - Tạo dữ liệu giả
   - Nhận feedback từ Discriminator
   - Mục tiêu: Minimize khả năng Discriminator phát hiện ra giả

3. **Cân bằng Nash**: Training dừng khi đạt equilibrium
   - Generator tạo dữ liệu không thể phân biệt được với thật
   - Discriminator chỉ đoán đúng 50% (như tung đồng xu)

### 1.3 Loss Function của GAN

**Minimax Game**:

```
min_G max_D V(D,G) = E_x[log D(x)] + E_z[log(1 - D(G(z)))]
```

Trong đó:

- `x`: Dữ liệu thật
- `z`: Noise vector
- `G(z)`: Dữ liệu giả từ Generator
- `D(x)`: Xác suất x là thật
- `E`: Expected value

**Discriminator loss**:

```
L_D = -[log D(x) + log(1 - D(G(z)))]
```

**Generator loss**:

```
L_G = -log D(G(z))
```

### 1.4 GAN trong Steganography

Trong bài toán steganography, GAN được ứng dụng để:

**Generator (Encoder)**:

- Input: Ảnh cover + secret message
- Output: Ảnh stego chứa thông tin ẩn
- Mục tiêu: Tạo ảnh stego không thể phân biệt với ảnh cover

**Discriminator (Critic)**:

- Input: Ảnh (cover hoặc stego)
- Output: Score đánh giá ảnh là cover hay stego
- Mục tiêu: Phát hiện ảnh nào chứa thông tin ẩn

Cơ chế adversarial buộc Encoder phải tạo ảnh stego có chất lượng cao, khó phát hiện bởi steganalysis attacks.

---

## 2. So sánh GAN và CNN

### 2.1 Convolutional Neural Networks (CNN)

CNN là kiến trúc neural network chuyên xử lý dữ liệu có cấu trúc grid (ảnh, video):

**Đặc điểm**:

- Supervised learning: Cần labeled data để train
- Feedforward: Dữ liệu đi một chiều từ input đến output
- Các layers chính: Conv2D, Pooling, Fully Connected
- Ứng dụng: Classification, detection, segmentation

**Cấu trúc**:

```
Input Image → Conv Layers → Pooling → FC Layers → Output
```

**Training**:

- Loss function đơn giản (cross-entropy, MSE)
- Backpropagation trực tiếp
- Stable và dễ train hơn GAN

### 2.2 So sánh GAN vs CNN

| Tiêu chí      | CNN                | GAN                          |
| ------------- | ------------------ | ---------------------------- |
| Mục đích      | Phân loại, dự đoán | Sinh dữ liệu mới             |
| Learning type | Supervised         | Unsupervised/Semi-supervised |
| Architecture  | Single network     | Dual networks (G + D)        |
| Training      | Straightforward    | Adversarial (khó hơn)        |
| Loss          | Direct (MSE, CE)   | Minimax game                 |
| Stability     | Stable             | Có thể không ổn định         |
| Output        | Label/Value        | Synthetic data               |
| Gradient flow | Direct backprop    | Through discriminator        |

### 2.3 Tại sao dùng GAN cho Steganography?

**Ưu điểm của GAN**:

1. **Chất lượng ảnh cao**: Adversarial training buộc encoder phải tạo ảnh stego realistic

   - CNN thuần: Chỉ minimize reconstruction loss (MSE, SSIM)
   - GAN: Phải đánh lừa critic → ảnh phải "nhìn" giống thật

2. **Khả năng chống steganalysis**:

   - Critic đóng vai trò steganalyzer
   - Encoder học cách tránh các artifacts dễ phát hiện

3. **Không cần ground truth hoàn hảo**:

   - CNN cần biết chính xác ảnh stego "đúng" là gì
   - GAN chỉ cần biết ảnh cover và message cần ẩn

4. **Perceptual quality**:
   - GAN optimize cho perceptual similarity (con người nhìn)
   - CNN optimize cho pixel-wise similarity (máy tính đo)

**Khi nào dùng CNN?**:

- Bài toán classification đơn giản
- Cần training stable và nhanh
- Có đủ labeled data
- Không cần generate dữ liệu mới

**Khi nào dùng GAN?**:

- Cần generate dữ liệu realistic
- Bài toán steganography, style transfer, super-resolution
- Cần perceptual quality cao
- Có thể trade-off training complexity

### 2.4 Trong CustomGANStego

CustomGANStego kết hợp cả CNN và GAN:

**CNN components**:

- Encoder: CNN layers để embed message
- Decoder: CNN layers để extract message
- Reverse Decoder: CNN layers để recover cover

**GAN components**:

- Critic: Đánh giá chất lượng ảnh stego (adversarial)
- Training strategy: Minimax game giữa Encoder và Critic

**Hybrid approach**:

```
Encoder (CNN) ←─────┐
                    │ Adversarial
Critic (CNN) ───────┘

Decoder (CNN) → Message extraction
Reverse Decoder (CNN) → Cover recovery
```

---

## 3. WGAN-GP trong Steganography

### 3.1 Vấn đề của GAN truyền thống

**Mode collapse**: Generator chỉ tạo một vài loại output giống nhau

**Vanishing gradient**: Khi Discriminator quá mạnh, gradient về Generator = 0

**Training instability**: Loss oscillate, không converge

### 3.2 Wasserstein GAN (WGAN)

WGAN thay đổi loss function để stable hơn:

**Earth Mover's Distance**:

```
W(P_r, P_g) = inf_{γ∈Π(P_r,P_g)} E_{(x,y)~γ}[||x - y||]
```

**WGAN loss**:

```
L_D = E_x[D(x)] - E_z[D(G(z))]
L_G = E_z[D(G(z))]
```

**Ưu điểm**:

- Loss có ý nghĩa: Càng thấp càng tốt
- Training stable hơn
- Không bị mode collapse

**Nhược điểm**:

- Cần weight clipping để enforce Lipschitz constraint
- Weight clipping gây capacity limitation

### 3.3 WGAN with Gradient Penalty (WGAN-GP)

WGAN-GP thay weight clipping bằng gradient penalty:

**Gradient Penalty**:

```
λ * E_x̂[(||∇_x̂ D(x̂)||_2 - 1)^2]
```

Trong đó:

- `x̂ = αx + (1-α)G(z)`: Interpolation giữa real và fake
- `α ~ Uniform(0, 1)`
- `λ`: Penalty coefficient (thường = 10)

**Implementation trong CustomGANStego**:

```python
def compute_gradient_penalty(critic, real_data, fake_data, device):
    batch_size = real_data.size(0)
    alpha = torch.rand(batch_size, 1, 1, 1, device=device)

    # Interpolate giữa real và fake
    interpolates = (alpha * real_data + (1 - alpha) * fake_data).requires_grad_(True)

    # Tính critic score
    d_interpolates = critic(interpolates)

    # Tính gradient
    gradients = torch.autograd.grad(
        outputs=d_interpolates,
        inputs=interpolates,
        grad_outputs=torch.ones_like(d_interpolates),
        create_graph=True,
        retain_graph=True,
        only_inputs=True
    )[0]

    # Gradient penalty
    gradients = gradients.view(batch_size, -1)
    gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean()

    return gradient_penalty
```

**Critic Loss với GP**:

```python
critic_loss = generated_score - cover_score + lambda_gp * gradient_penalty
```

### 3.4 Tại sao WGAN-GP quan trọng cho Steganography?

1. **Stable training**: Steganography cần balance nhiều loss terms, WGAN-GP giúp training stable

2. **Smooth gradient**: Gradient penalty đảm bảo gradient flow tốt, encoder học hiệu quả

3. **No mode collapse**: Encoder không bị stuck vào một pattern nhúng cố định

4. **Meaningful loss**: Có thể track training progress qua critic loss

---

## 4. Kiến trúc CustomGANStego

### 4.1 Tổng quan hệ thống

CustomGANStego gồm 4 modules chính:

```
┌─────────────────────────────────────────────────────┐
│                  Training Phase                      │
│                                                      │
│  Cover Image + Message                              │
│         │                                            │
│         ▼                                            │
│    ┌─────────┐                                      │
│    │ Encoder │ ──────────────┐                     │
│    └─────────┘                │                     │
│         │                      │                     │
│         ▼                      ▼                     │
│    Stego Image            ┌────────┐               │
│         │                  │ Critic │ (Adversarial) │
│         │                  └────────┘               │
│         ├─────────┐            ▲                     │
│         │         │            │                     │
│         ▼         ▼            │                     │
│    ┌─────────┐ ┌────────────┐ │                    │
│    │ Decoder │ │ Reverse    │─┘                    │
│    └─────────┘ │ Decoder    │                      │
│         │       └────────────┘                      │
│         ▼             │                              │
│    Extracted      Recovered                         │
│    Message        Cover                             │
└─────────────────────────────────────────────────────┘
```

### 4.2 Encoder Network

**Mục đích**: Nhúng secret message vào cover image

**Architecture**: BasicEncoder / ResidualEncoder / DenseEncoder

```python
class BasicEncoder(nn.Module):
    def __init__(self, data_depth, hidden_size):
        # Conv1: Image branch
        self.conv1 = Conv2d(3 → hidden_size)

        # Conv2: Fusion layer (image + message)
        self.conv2 = Conv2d(hidden_size + data_depth → hidden_size)

        # Conv3-4: Processing layers
        self.conv3 = Conv2d(hidden_size → hidden_size)
        self.conv4 = Conv2d(hidden_size → 3)

    def forward(self, image, data):
        x = conv1(image)              # Extract image features
        x = conv2([x, data])          # Fuse with message
        x = conv3(x)                  # Process
        stego = conv4(x)              # Generate stego
        return stego
```

**ResidualEncoder**: Thêm residual connection

```python
def forward(self, image, data):
    delta = super().forward(image, data)
    return image + delta  # Stego = Cover + Δ
```

**Ưu điểm residual**:

- Encoder chỉ học difference, dễ hơn
- Preserve structure của cover image
- Better gradient flow

**DenseEncoder**: Thêm dense connections (DenseNet style)

```python
def forward(self, image, data):
    x1 = conv1(image)
    x2 = conv2([x1, data])
    x3 = conv3([x1, x2, data])    # Concatenate all previous
    x4 = conv4([x1, x2, x3, data])
    return image + x4
```

**Ưu điểm dense**:

- Feature reuse → fewer parameters
- Better gradient propagation
- Richer feature combinations

### 4.3 Decoder Network

**Mục đích**: Trích xuất message từ stego image

**Architecture**: BasicDecoder / DenseDecoder

```python
class BasicDecoder(nn.Module):
    def __init__(self, data_depth, hidden_size):
        self.conv1 = Conv2d(3 → hidden_size)
        self.conv2 = Conv2d(hidden_size → hidden_size)
        self.conv3 = Conv2d(hidden_size → hidden_size)
        self.conv4 = Conv2d(hidden_size → data_depth)

    def forward(self, stego):
        x = conv1(stego)
        x = conv2(x)
        x = conv3(x)
        message = conv4(x)  # Output: (N, data_depth, H, W)
        return message
```

**DenseDecoder**: Similar to DenseEncoder, dùng dense connections

**Output**: Binary tensor (N, data_depth, H, W)

- Mỗi pixel chứa `data_depth` bits
- Threshold > 0 để convert sang binary

### 4.4 Critic Network

**Mục đích**: Phân biệt cover và stego images (adversarial)

**Architecture**: BasicCritic (không dùng Discriminator vì là regression, không phải classification)

```python
class BasicCritic(nn.Module):
    def __init__(self, hidden_size):
        self.conv1 = Conv2d(3 → hidden_size)
        self.conv2 = Conv2d(hidden_size → hidden_size)
        self.conv3 = Conv2d(hidden_size → hidden_size)
        self.conv4 = Conv2d(hidden_size → 1)

    def forward(self, image):
        x = conv1(image)
        x = conv2(x)
        x = conv3(x)
        score = conv4(x)  # Output: (N, 1, H, W)
        return mean(score)  # Scalar score
```

**Critic vs Discriminator**:

- Discriminator: Output probability [0, 1]
- Critic: Output unbounded score (real number)
- Critic phù hợp với WGAN-GP

### 4.5 Reverse Decoder Network

**Mục đích**: Khôi phục cover image từ stego (reversible steganography)

**Innovation**: Cho phép xóa hoàn toàn dấu vết steganography

```python
class ReverseDecoder(nn.Module):
    def __init__(self, hidden_size):
        self.conv1 = Conv2d(3 → hidden_size)
        self.conv2 = Conv2d(hidden_size → hidden_size)
        self.conv3 = Conv2d(hidden_size → hidden_size)
        self.conv4 = Conv2d(hidden_size → hidden_size)
        self.conv5 = Conv2d(hidden_size → 3) + Tanh

    def forward(self, stego):
        x = conv1(stego)
        x = conv2(x)
        x = conv3(x)
        x = conv4(x)
        delta = conv5(x)

        # Residual: Cover = Stego + Δ_reverse
        cover = stego + delta
        return clamp(cover, -1, 1)
```

**Ứng dụng**:

- Khôi phục ảnh gốc sau khi truyền tin
- Xóa bỏ dấu vết steganography
- Forensics: Phát hiện đã từng chứa thông tin ẩn

---

## 5. Loss Functions và Training Strategy

### 5.1 Multi-objective Optimization

Steganography cần balance nhiều mục tiêu:

1. **Imperceptibility**: Ảnh stego phải giống cover
2. **Capacity**: Nhúng đủ thông tin
3. **Robustness**: Message phải trích xuất chính xác
4. **Security**: Khó phát hiện bởi steganalysis

Để đạt được, CustomGANStego dùng multi-loss training:

```python
total_loss = w1*L_mse + w2*L_ssim + w3*L_perceptual +
             w4*L_decoder + w5*L_adversarial + w6*L_reverse
```

### 5.2 Chi tiết các Loss Components

**1. MSE Loss (Mean Squared Error)**

```python
L_mse = MSE(stego, cover)
      = mean((stego - cover)^2)
```

**Mục đích**: Giữ ảnh stego gần với cover về pixel values

**Ưu điểm**:

- Đơn giản, dễ optimize
- Đảm bảo pixel-level similarity

**Nhược điểm**:

- Không capture perceptual quality
- Có thể tạo blurry images

**Weight**: `weight_mse = 50.0` (high để ưu tiên quality)

---

**2. SSIM Loss (Structural Similarity Index)**

```python
L_ssim = 1 - SSIM(stego, cover)
```

SSIM được tính dựa trên 3 thành phần:

- Luminance: `l(x,y) = (2μ_x μ_y + C1) / (μ_x^2 + μ_y^2 + C1)`
- Contrast: `c(x,y) = (2σ_x σ_y + C2) / (σ_x^2 + σ_y^2 + C2)`
- Structure: `s(x,y) = (σ_xy + C3) / (σ_x σ_y + C3)`

**Mục đích**: Preserve structural information

**Ưu điểm**:

- Better perceptual metric than MSE
- Sensitive to structural changes

**Weight**: `weight_ssim = 20.0`

---

**3. Perceptual Loss (VGG-based)**

```python
L_perceptual = MSE(VGG(stego), VGG(cover))
```

Sử dụng features từ pretrained VGG16:

- Extract features từ intermediate layers (conv3_3, conv4_3)
- Compare feature representations thay vì pixels

**Mục đích**: Preserve semantic content

**Ưu điểm**:

- Captures high-level perceptual similarity
- Less sensitive to small pixel changes

**Weight**: `weight_perceptual = 5.0` (optional, có thể tắt)

---

**4. Decoder Loss (Message Accuracy)**

```python
L_decoder = BCE(decoded_message, original_message)
          = -[y*log(ŷ) + (1-y)*log(1-ŷ)]
```

**Mục đích**: Đảm bảo message được trích xuất chính xác

**Quan trọng**: Loss này quyết định decoder accuracy

**Weight**: `weight_decoder = 10.0` (TĂNG để ưu tiên accuracy)

**Metrics**: Decoder Accuracy = % bits trích xuất đúng

---

**5. Adversarial Loss (WGAN-GP)**

```python
# Critic loss
L_critic = E[Critic(stego)] - E[Critic(cover)] + λ*GP

# Encoder adversarial loss
L_adv = -E[Critic(stego)]
```

**Mục đích**: Làm stego image khó phân biệt với cover

**Gradient Penalty**:

```python
GP = E[(||∇Critic(interpolated)||_2 - 1)^2]
```

**Weight**: `weight_adversarial = 0.005` (small để không overpower other losses)

**Lambda GP**: `lambda_gp = 10.0`

---

**6. Reverse Loss (Cover Recovery)**

```python
L_reverse = MSE(recovered_cover, original_cover) +
            (1 - SSIM(recovered_cover, original_cover))
```

**Mục đích**: Đảm bảo có thể khôi phục cover từ stego

**Ưu điểm**:

- Reversibility: Có thể undo steganography
- Security: Xóa dấu vết sau khi dùng

**Weight**: `weight_reverse = 50.0`

### 5.3 Training Strategy

**Two-stage training**: Critic và Encoder/Decoder train riêng

```python
# Stage 1: Train Critic (n_critic iterations)
for _ in range(n_critic):
    # Forward
    stego = encoder(cover, message)
    cover_score = critic(cover)
    stego_score = critic(stego.detach())

    # Gradient penalty
    gp = compute_gradient_penalty(critic, cover, stego, device)

    # Critic loss (WGAN-GP)
    critic_loss = stego_score - cover_score + lambda_gp * gp

    # Backward
    critic_optimizer.zero_grad()
    critic_loss.backward()
    critic_optimizer.step()

# Stage 2: Train Encoder/Decoder/Reverse Decoder
stego = encoder(cover, message)
decoded = decoder(stego)
recovered = reverse_decoder(stego)

# Calculate all losses
l_mse = mse_loss(stego, cover)
l_ssim = 1 - ssim_metric(stego, cover)
l_decoder = bce_loss(decoded, message)
l_reverse = mse_loss(recovered, cover)
stego_score = critic(stego)
l_adv = -stego_score.mean()

# Combined loss
total_loss = (weight_mse * l_mse +
              weight_ssim * l_ssim +
              weight_decoder * l_decoder +
              weight_adversarial * l_adv +
              weight_reverse * l_reverse)

# Backward
optimizer.zero_grad()
total_loss.backward()
optimizer.step()
```

**Hyperparameters**:

- `n_critic = 2`: Train critic 2 lần mỗi iteration
- `lr_critic = 2e-4`: Learning rate cho critic
- `lr_encoder_decoder = 2e-4`: Learning rate cho encoder/decoder
- `batch_size = 4`: Batch size (tùy GPU memory)
- `epochs = 60`: Số epochs training

**Learning Rate Scheduling**:

```python
scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
```

Cosine annealing giảm dần learning rate theo công thức:

```
lr_t = lr_min + (lr_max - lr_min) * (1 + cos(πt/T)) / 2
```

**Early Stopping**: Dừng khi đạt targets

- Decoder Accuracy >= 95%
- PSNR >= 35 dB
- SSIM >= 0.90

---

## 6. Reverse Hiding - Tính Năng Độc Đáo

### 6.1 Khái niệm Reversible Steganography

**Traditional steganography**:

```
Cover → [Embed] → Stego → [Extract] → Message
```

Sau khi extract message, không thể recover lại cover image chính xác.

**Reversible steganography**:

```
Cover → [Embed] → Stego → [Extract] → Message
                     ↓
                [Reverse] → Cover (recovered)
```

Có thể khôi phục lại cover image gần như hoàn hảo.

### 6.2 Tại sao cần Reversible Steganography?

**1. Security Enhancement**:

- Sau khi truyền tin, xóa bỏ steganography traces
- Người thứ ba không biết từng có thông tin ẩn
- Forensics khó phát hiện

**2. Cover Image Recovery**:

- Khôi phục ảnh gốc chất lượng cao
- Quan trọng với ảnh có giá trị (y tế, pháp lý)
- Tái sử dụng cover image cho lần sau

**3. Lossless Communication**:

- Không làm mất chất lượng cover image
- Important cho applications yêu cầu lossless
- Medical imaging, satellite imagery

**4. Dual-purpose Communication**:

- Channel 1: Secret message (hidden)
- Channel 2: Cover image (overt)
- Cả hai đều được bảo toàn

### 6.3 Implementation trong CustomGANStego

**Architecture Design**:

Reverse Decoder học ánh xạ ngược:

```
Encoder:   Cover + Message → Stego
Reverse:   Stego → Cover_recovered
```

**Training với Reverse Loss**:

```python
# Forward pass
stego = encoder(cover, message)
recovered = reverse_decoder(stego)

# Reverse loss
reverse_mse = mse_loss(recovered, cover)
reverse_ssim = 1 - ssim_metric(recovered, cover)
reverse_loss = reverse_mse + reverse_ssim

# Backprop
total_loss += weight_reverse * reverse_loss
```

**Residual Learning Strategy**:

```python
class ReverseDecoder(nn.Module):
    def forward(self, stego):
        delta = self.layers(stego)  # Learn difference
        recovered = stego + delta    # Add residual
        return clamp(recovered, -1, 1)
```

**Tại sao dùng residual?**:

- Stego ≈ Cover (only small differences)
- Easier to learn: Delta ≈ 0
- Better gradient flow
- Faster convergence

### 6.4 Performance Metrics

**Reverse PSNR**: Đo chất lượng khôi phục

```
RPSNR = 10 * log10(MAX^2 / MSE(recovered, cover))
```

Targets:

- RPSNR > 30 dB: Excellent
- RPSNR 25-30 dB: Good
- RPSNR < 25 dB: Cần improve

**Reverse SSIM**: Đo structural similarity

```
RSSIM = SSIM(recovered, cover)
```

Targets:

- RSSIM > 0.95: Excellent
- RSSIM 0.90-0.95: Good
- RSSIM < 0.90: Cần improve

**Trong CustomGANStego**:

- Best model (Epoch 33): RPSNR = 29.78 dB, RSSIM ~ 0.92
- Có thể recover cover với quality rất cao
- Imperceptible differences với naked eye

### 6.5 Usage Workflow

**Scenario: Secure Communication**

1. **Sender side**:

```bash
# Embed secret message
python runencode.py cover.png "Secret message" --encrypt

# Send: stego.png
```

2. **Receiver side**:

```bash
# Extract message
python rundecode.py stego.png --encrypt

# Recover cover (remove traces)
python runreverse.py stego.png

# Now: recovered_cover.png looks like original
# stego.png can be deleted safely
```

**Benefits**:

- Message extracted: Mission accomplished
- Cover recovered: No evidence of steganography
- Plausible deniability: "This is just a normal photo"

---

## Kết luận

CustomGANStego kết hợp nhiều kỹ thuật tiên tiến:

1. **GAN Framework**: Adversarial training cho imperceptibility
2. **WGAN-GP**: Stable training với gradient penalty
3. **CNN Architectures**: Efficient feature extraction và processing
4. **Multi-loss Optimization**: Balance giữa quality, capacity, robustness
5. **Reversible Design**: Khôi phục cover image cho security

**Key innovations**:

- Residual connections cho better learning
- Dense connections cho feature reuse
- Reverse decoder cho reversibility
- Weighted scoring cho model selection

Kiến trúc này đạt được:

- Decoder Accuracy: >98%
- PSNR: >32 dB
- SSIM: >0.90
- Reverse PSNR: >29 dB

Kết quả: Steganography system hiệu quả, an toàn, và có thể reverse được.
