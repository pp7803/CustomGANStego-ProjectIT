import os
import re
import torch
import torch.nn as nn
from PIL import Image
import numpy as np
try:
    from imageio import imread, imwrite
except ImportError:
    # For imageio v3+
    import imageio.v2 as imageio
    imread = imageio.imread
    imwrite = imageio.imwrite
import zlib
from reedsolo import RSCodec
from collections import Counter

from encoder import BasicEncoder, ResidualEncoder
from decoder import BasicDecoder

# ==================== CÁC HÀM TIỆN ÍCH ====================
rs = RSCodec(250)

# Pre-computed lookup table for fast byte-to-bits conversion
_BYTE_TO_BITS = [[(b >> (7-i)) & 1 for i in range(8)] for b in range(256)]

def text_to_bits(text):
    """Chuyển text thành bits"""
    return bytearray_to_bits(text_to_bytearray(text))

def bits_to_text(bits):
    """Chuyển bits thành text"""
    return bytearray_to_text(bits_to_bytearray(bits))

def bytearray_to_bits(x):
    """Chuyển bytearray thành list bits - OPTIMIZED với lookup table"""
    result = []
    for byte in x:
        result.extend(_BYTE_TO_BITS[byte])
    return result

def bits_to_bytearray(bits):
    """Chuyển bits thành bytearray - OPTIMIZED với numpy"""
    if isinstance(bits, list):
        bits = np.array(bits, dtype=np.uint8)
    n_bytes = len(bits) // 8
    bits = bits[:n_bytes * 8].reshape(-1, 8)
    # Vectorized: [b7,b6,b5,b4,b3,b2,b1,b0] -> byte value
    weights = np.array([128, 64, 32, 16, 8, 4, 2, 1], dtype=np.uint8)
    return bytearray((bits * weights).sum(axis=1).astype(np.uint8))

def text_to_bytearray(text):
    """Nén và thêm error correction"""
    assert isinstance(text, str), "expected a string"
    x = zlib.compress(text.encode("utf-8"))
    x = rs.encode(bytearray(x))
    return x

def bytearray_to_text(x):
    """Giải nén và sửa lỗi"""
    try:
        text = rs.decode(x)[0]
        text = zlib.decompress(text)
        return text.decode("utf-8")
    except BaseException as e:
        # print(f"Error decoding: {e}")
        return False

# ==================== ENCODER MODEL ====================
class DenseEncoder(nn.Module):
    def __init__(self, data_depth=4, hidden_size=32):
        super().__init__()
        self.data_depth = data_depth
        self.hidden_size = hidden_size
        self.name = "DenseEncoder"
        
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, hidden_size, 3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(hidden_size),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(hidden_size + data_depth, hidden_size, 3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(hidden_size),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(hidden_size * 2 + data_depth, hidden_size, 3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(hidden_size),
        )
        self.conv4 = nn.Sequential(
            nn.Conv2d(hidden_size * 3 + data_depth, 3, 3, padding=1)
        )

    def forward(self, image, data):
        x = self.conv1(image)
        x_list = [x]
        x_1 = self.conv2(torch.cat(x_list + [data], dim=1))
        x_list.append(x_1)
        x_2 = self.conv3(torch.cat(x_list + [data], dim=1))
        x_list.append(x_2)
        x_3 = self.conv4(torch.cat(x_list + [data], dim=1))
        return image + x_3

# ==================== DECODER MODEL ====================
class DenseDecoder(nn.Module):
    def __init__(self, data_depth=4, hidden_size=32):
        super().__init__()
        self.data_depth = data_depth
        self.hidden_size = hidden_size
        self.name = "DenseDecoder"
        
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, hidden_size, 3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(hidden_size),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(hidden_size, hidden_size, 3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(hidden_size),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(hidden_size * 2, hidden_size, 3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(hidden_size)
        )
        self.conv4 = nn.Sequential(
            nn.Conv2d(hidden_size * 3, data_depth, 3, padding=1),
        )

    def forward(self, image):
        x = self.conv1(image)
        x_list = [x]
        x_1 = self.conv2(torch.cat(x_list, dim=1))
        x_list.append(x_1)
        x_2 = self.conv3(torch.cat(x_list, dim=1))
        x_list.append(x_2)
        x_3 = self.conv4(torch.cat(x_list, dim=1))
        return x_3

# ==================== REVERSE DECODER MODEL ====================
class ReverseDecoder(nn.Module):
    """
    The ReverseDecoder module takes a steganographic image and attempts to 
    reconstruct the original cover image (Reverse Hiding).
    
    This enables:
    - Lossless recovery of original image
    - Reversible steganography
    - Higher security (can remove traces)
    
    Input: (N, 3, H, W) - Stego image
    Output: (N, 3, H, W) - Recovered cover image
    """

    def _conv2d(self, in_channels, out_channels):
        return nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            padding=1
        )

    def _build_models(self):
        """
        Architecture similar to BasicDecoder but output is RGB image (3 channels)
        Uses residual connections for better gradient flow
        """
        self.conv1 = nn.Sequential(
            self._conv2d(3, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv2 = nn.Sequential(
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv3 = nn.Sequential(
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv4 = nn.Sequential(
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv5 = nn.Sequential(
            self._conv2d(self.hidden_size, 3),  # Output RGB
            nn.Tanh()  # Output range [-1, 1] to match normalized images
        )

        return self.conv1, self.conv2, self.conv3, self.conv4, self.conv5

    def __init__(self, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self._models = self._build_models()

    def forward(self, stego_image):
        """
        Forward pass with residual connection
        
        Args:
            stego_image: Steganographic image (N, 3, H, W)
            
        Returns:
            recovered_cover: Reconstructed cover image (N, 3, H, W)
        """
        x = self._models[0](stego_image)
        x_1 = self._models[1](x)
        x_2 = self._models[2](x_1)
        x_3 = self._models[3](x_2)
        x_4 = self._models[4](x_3)
        
        # Residual connection: stego + delta = cover
        # This helps network learn only the difference
        recovered_cover = stego_image + x_4
        
        # Clamp to valid range [-1, 1]
        recovered_cover = torch.clamp(recovered_cover, -1.0, 1.0)
        
        return recovered_cover

# ==================== PAYLOAD & MESSAGE ====================
def make_payload(width, height, depth, text):
    """Tạo payload từ text để ẩn vào ảnh"""
    message = text_to_bits(text) + [0] * 32
    payload = message
    while len(payload) < width * height * depth:
        payload += message
    payload = payload[:width * height * depth]
    return torch.FloatTensor(payload).view(1, depth, height, width)

def make_message(image, decoder, device, max_attempts=50):
    """Giải mã message từ ảnh stego - OPTIMIZED for high accuracy models"""
    image = image.to(device)
    
    with torch.no_grad():
        # Decode bits directly on GPU/MPS
        decoded = (decoder(image).view(-1) > 0).to(torch.uint8)
        bits = decoded.cpu().numpy()
    
    # Fast conversion to bytearray
    raw_bytes = bits_to_bytearray(bits)
    
    # OPTIMIZATION 1: Early stopping with attempt limit (fast for large payloads)
    attempts = 0
    for candidate in raw_bytes.split(b'\x00\x00\x00\x00'):
        if len(candidate) < 10:  # Too short, skip
            continue
        
        attempts += 1
        if attempts > max_attempts:
            print(f"⚠️  Reached max attempts ({max_attempts}), trying voting...")
            break
            
        result = bytearray_to_text(bytearray(candidate))
        if result:
            return result  # Early return on first valid message
    
    # OPTIMIZATION 2: Fallback with limited voting (for large encrypted payloads)
    # Only check first N candidates to avoid hanging
    candidates = Counter()
    attempts = 0
    max_voting_attempts = max_attempts * 2
    
    for candidate in raw_bytes.split(b'\x00\x00\x00\x00'):
        if len(candidate) < 10:
            continue
            
        attempts += 1
        if attempts > max_voting_attempts:
            break
            
        result = bytearray_to_text(bytearray(candidate))
        if result:
            candidates[result] += 1
            # If we found a valid result with multiple votes, return early
            if candidates[result] >= 2:
                return result
    
    if len(candidates) == 0:
        raise ValueError(f'Failed to find message after {attempts} attempts. '\
                        'This may happen with very large encrypted payloads. '\
                        'Try using plain text or smaller messages.')
    
    return candidates.most_common(1)[0][0]

# ==================== MAIN FUNCTIONS ====================
def encode_message(cover_image_path, secret_text, output_path, model_path=None):
    """
    ENCODE: Giấu tin nhắn vào ảnh
    """
    # Add MPS support for Mac
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    print(f"Using device: {device}")
    
    # Khởi tạo models - SỬ DỤNG ResidualEncoder để giảm color shift
    data_depth = 2  # Phải khớp với model đã train
    hidden_size = 32
    # ResidualEncoder = image + delta → better color preservation
    encoder = ResidualEncoder(data_depth, hidden_size).to(device)
    
    # Load model nếu có
    if model_path:
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        encoder.load_state_dict(checkpoint['state_dict_encoder'])
        print("✓ Loaded pretrained encoder")
    
    encoder.eval()
    
    # Đọc ảnh cover
    cover_im = imread(cover_image_path, pilmode='RGB') / 127.5 - 1.0
    cover = torch.FloatTensor(cover_im).permute(2, 1, 0).unsqueeze(0)
    cover_size = cover.size()
    
    # Tạo payload từ text
    payload = make_payload(cover_size[3], cover_size[2], data_depth, secret_text)
    
    # Encode
    cover = cover.to(device)
    payload = payload.to(device)
    
    with torch.no_grad():
        generated = encoder.forward(cover, payload)[0].clamp(-1.0, 1.0)
    
    # Chuyển về ảnh và lưu
    generated = (generated.permute(2, 1, 0).detach().cpu().numpy() + 1.0) * 127.5
    imwrite(output_path, generated.astype('uint8'))
    
    print(f"✓ Encoded message into: {output_path}")
    print(f"✓ Secret text: {secret_text}")

def decode_message(stego_image_path, model_path=None):
    """
    DECODE: Giải mã tin nhắn từ ảnh stego
    """
    # Add MPS support for Mac
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    print(f"Using device: {device}")
    
    # Khởi tạo decoder - SỬA DỤNG BasicDecoder thay vì DenseDecoder
    data_depth = 2  # Phải khớp với model đã train
    hidden_size = 32
    decoder = BasicDecoder(data_depth, hidden_size).to(device)
    
    # Load model nếu có
    if model_path:
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        decoder.load_state_dict(checkpoint['state_dict_decoder'])
        print("✓ Loaded pretrained decoder")
    
    decoder.eval()
    
    # Đọc ảnh stego
    image = imread(stego_image_path, pilmode='RGB') / 127.5 - 1.0
    image = torch.FloatTensor(image).permute(2, 1, 0).unsqueeze(0)
    
    # Decode
    with torch.no_grad():
        text = make_message(image, decoder, device)
    
    print(f"✓ Decoded message from: {stego_image_path}")
    print(f"✓ Secret text: {text}")
    
    return text

def reverse_hiding(stego_image_path, output_path, model_path=None):
    """
    REVERSE HIDING: Khôi phục ảnh cover gốc từ ảnh stego
    
    Args:
        stego_image_path: Đường dẫn đến ảnh stego
        output_path: Đường dẫn lưu ảnh cover đã khôi phục
        model_path: Đường dẫn đến model checkpoint (optional)
    
    Returns:
        recovered_cover: Ảnh cover đã khôi phục (numpy array)
    """
    # Device detection
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    print(f"Using device: {device}")
    
    # Khởi tạo reverse decoder
    hidden_size = 32
    reverse_decoder = ReverseDecoder(hidden_size).to(device)
    
    # Load model nếu có
    if model_path:
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        if 'state_dict_reverse_decoder' in checkpoint:
            reverse_decoder.load_state_dict(checkpoint['state_dict_reverse_decoder'])
            print("✓ Loaded pretrained reverse decoder")
        else:
            print("⚠️  Warning: No reverse_decoder weights found in checkpoint")
            print("   Using randomly initialized weights (will not work well)")
    else:
        print("⚠️  Warning: No model path provided")
        print("   Using randomly initialized weights (will not work well)")
    
    reverse_decoder.eval()
    
    # Đọc ảnh stego
    stego_im = imread(stego_image_path, pilmode='RGB') / 127.5 - 1.0
    stego = torch.FloatTensor(stego_im).permute(2, 1, 0).unsqueeze(0)
    stego = stego.to(device)
    
    # Reverse hiding - khôi phục cover
    with torch.no_grad():
        recovered_cover = reverse_decoder(stego)[0].clamp(-1.0, 1.0)
    
    # Chuyển về ảnh và lưu
    recovered_cover = (recovered_cover.permute(2, 1, 0).detach().cpu().numpy() + 1.0) * 127.5
    imwrite(output_path, recovered_cover.astype('uint8'))
    
    print(f"✓ Recovered cover image saved to: {output_path}")
    
    return recovered_cover

# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    def find_best_model(models_dir='results/model'):
        """Return path to best model file in `models_dir` based on accuracy then PSNR.

        Expected filename pattern contains `acc{acc}` and `psnr{psnr}` like:
        EN_DE_REV_ep052_acc0.9845_psnr33.70_rpsnr26.93_20251211_150551.dat
        """
        if not os.path.isdir(models_dir):
            return None

        best = None
        best_acc = -1.0
        best_psnr = -1.0
        pattern = re.compile(r"acc([0-9]*\.?[0-9]+).*psnr([0-9]*\.?[0-9]+)")

        for fname in os.listdir(models_dir):
            if not fname.endswith('.dat'):
                continue
            m = pattern.search(fname)
            if not m:
                continue
            try:
                acc = float(m.group(1))
                psnr = float(m.group(2))
            except Exception:
                continue

            # prefer higher accuracy, break ties with higher PSNR
            if acc > best_acc or (acc == best_acc and psnr > best_psnr):
                best_acc = acc
                best_psnr = psnr
                best = os.path.join(models_dir, fname)

        return best

    MODEL_PATH = find_best_model()
    if MODEL_PATH:
        print(f"Using best model: {MODEL_PATH}")
    else:
        print("No model found in results/model; set MODEL_PATH manually if needed")
    
    # VÍ DỤ 1: ENCODE (Giấu tin)
    print("\n=== ENCODING ===")
    encode_message(
        cover_image_path="div2k/myval/_/0805.png",
        secret_text="We are busy in Neural Networks project!",
        output_path="stego_output.png",
        model_path=MODEL_PATH  # Hoặc None nếu không có model
    )
    
    # VÍ DỤ 2: DECODE (Giải mã tin nhắn)
    print("\n=== DECODING MESSAGE ===")
    decoded_text = decode_message(
        stego_image_path="stego_output.png",
        model_path=MODEL_PATH  # Hoặc None nếu không có model
    )
    
    # VÍ DỤ 3: REVERSE HIDING (Khôi phục ảnh gốc)
    print("\n=== REVERSE HIDING (RECOVER COVER) ===")
    recovered_cover = reverse_hiding(
        stego_image_path="stego_output.png",
        output_path="recovered_cover.png",
        model_path=MODEL_PATH  # BẮT BUỘC phải có model đã train reverse_decoder
    )
    
    print("\n=== COMPLETE ===")
    print("✓ Original cover → Stego (with hidden message)")
    print("✓ Stego → Decoded message")
    print("✓ Stego → Recovered cover (reverse hiding)")