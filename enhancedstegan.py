import os
import re
import torch
import torch.nn as nn
from PIL import Image
import numpy as np
try:
    from imageio import imread, imwrite
except ImportError:
    import imageio.v2 as imageio
    imread = imageio.imread
    imwrite = imageio.imwrite
import zlib
from reedsolo import RSCodec
from collections import Counter

from encoder import BasicEncoder, ResidualEncoder
from decoder import BasicDecoder

rs = RSCodec(250)

_BYTE_TO_BITS = [[(b >> (7-i)) & 1 for i in range(8)] for b in range(256)]

def text_to_bits(text):
    """Chuyển text thành bits"""
    return bytearray_to_bits(text_to_bytearray(text))

def bits_to_text(bits):
    """Chuyển bits thành text"""
    return bytearray_to_text(bits_to_bytearray(bits))

def bytearray_to_bits(x):
    """Chuyển bytearray thành list bits - ĐÃ TỐI ƯU với bảng tra cứu"""
    result = []
    for byte in x:
        result.extend(_BYTE_TO_BITS[byte])
    return result

def bits_to_bytearray(bits):
    """Chuyển bits thành bytearray - ĐÃ TỐI ƯU với numpy"""
    if isinstance(bits, list):
        bits = np.array(bits, dtype=np.uint8)
    n_bytes = len(bits) // 8
    bits = bits[:n_bytes * 8].reshape(-1, 8)
    # Vector hóa: [b7,b6,b5,b4,b3,b2,b1,b0] -> giá trị byte
    weights = np.array([128, 64, 32, 16, 8, 4, 2, 1], dtype=np.uint8)
    return bytearray((bits * weights).sum(axis=1).astype(np.uint8))

def text_to_bytearray(text):
    """Nén và thêm error correction"""
    assert isinstance(text, str), "mong đợi một chuỗi string"
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
        return False

# MÔ HÌNH ENCODER
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

# MÔ HÌNH DECODER
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

# MÔ HÌNH REVERSE DECODER
class ReverseDecoder(nn.Module):
    def _conv2d(self, in_channels, out_channels):
        return nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            padding=1
        )

    def _build_models(self):
        """
        Kiến trúc tương tự như BasicDecoder nhưng đầu ra là ảnh RGB (3 kênh)
        Sử dụng kết nối residual để cải thiện luồng gradient
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
            self._conv2d(self.hidden_size, 3),
            nn.Tanh()
        )

        return self.conv1, self.conv2, self.conv3, self.conv4, self.conv5

    def __init__(self, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self._models = self._build_models()

    def forward(self, stego_image):
        x = self._models[0](stego_image)
        x_1 = self._models[1](x)
        x_2 = self._models[2](x_1)
        x_3 = self._models[3](x_2)
        x_4 = self._models[4](x_3)
        
        recovered_cover = stego_image + x_4
        
        recovered_cover = torch.clamp(recovered_cover, -1.0, 1.0)
        
        return recovered_cover

# PAYLOAD & MESSAGE
def make_payload(width, height, depth, text):
    """Tạo payload từ text để ẩn vào ảnh"""
    message = text_to_bits(text) + [0] * 32
    payload = message
    while len(payload) < width * height * depth:
        payload += message
    payload = payload[:width * height * depth]
    return torch.FloatTensor(payload).view(1, depth, height, width)

def make_message(image, decoder, device, max_attempts=50):
    """Giải mã message từ ảnh stego - ĐÃ TỐI ƯU cho các model độ chính xác cao"""
    image = image.to(device)
    
    with torch.no_grad():
        decoded = (decoder(image).view(-1) > 0).to(torch.uint8)
        bits = decoded.cpu().numpy()
    
    raw_bytes = bits_to_bytearray(bits)
    
    # Phương pháp 1: Dừng sớm với giới hạn số lần thử (nhanh cho payload lớn)
    attempts = 0
    for candidate in raw_bytes.split(b'\x00\x00\x00\x00'):
        if len(candidate) < 10:  # Quá ngắn, bỏ qua
            continue
        
        attempts += 1
        if attempts > max_attempts:
            print(f"Đã đạt giới hạn số lần thử ({max_attempts}), thử voting...")
            break
            
        result = bytearray_to_text(bytearray(candidate))
        if result:
            return result  # Trả về sớm khi tìm thấy message hợp lệ
    
    # Phương pháp 2: Fallback với voting có giới hạn
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
            if candidates[result] >= 2:
                return result
    
    if len(candidates) == 0:
        raise ValueError(f'Không tìm thấy message sau {attempts} lần thử. '\
                        'Điều này có thể xảy ra với payload mã hóa rất lớn. '\
                        'Hãy thử sử dụng văn bản thuần hoặc message nhỏ hơn.')
    
    return candidates.most_common(1)[0][0]

def encode_message(cover_image_path, secret_text, output_path, model_path=None):
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    print(f"Đang sử dụng thiết bị: {device}")
    
    data_depth = 2
    hidden_size = 32
    encoder = ResidualEncoder(data_depth, hidden_size).to(device)
    
    # Tải model nếu có
    if model_path:
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        encoder.load_state_dict(checkpoint['state_dict_encoder'])
        print("Đã tải encoder đã được huấn luyện trước")
    
    encoder.eval()
    
    cover_im = imread(cover_image_path, pilmode='RGB') / 127.5 - 1.0
    cover = torch.FloatTensor(cover_im).permute(2, 1, 0).unsqueeze(0)
    cover_size = cover.size()
    
    payload = make_payload(cover_size[3], cover_size[2], data_depth, secret_text)
    
    cover = cover.to(device)
    payload = payload.to(device)
    
    with torch.no_grad():
        generated = encoder.forward(cover, payload)[0].clamp(-1.0, 1.0)
    
    generated = (generated.permute(2, 1, 0).detach().cpu().numpy() + 1.0) * 127.5
    imwrite(output_path, generated.astype('uint8'))
    
    print(f"Đã mã hóa message vào: {output_path}")
    print(f"Văn bản bí mật: {secret_text}")

def decode_message(stego_image_path, model_path=None):
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    print(f"Đang sử dụng thiết bị: {device}")
    
    data_depth = 2
    hidden_size = 32
    decoder = BasicDecoder(data_depth, hidden_size).to(device)
    
    if model_path:
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        decoder.load_state_dict(checkpoint['state_dict_decoder'])
        print("Đã tải decoder đã được huấn luyện trước")
    
    decoder.eval()
    
    image = imread(stego_image_path, pilmode='RGB') / 127.5 - 1.0
    image = torch.FloatTensor(image).permute(2, 1, 0).unsqueeze(0)
    
    with torch.no_grad():
        text = make_message(image, decoder, device)
    
    print(f"Đã giải mã message từ: {stego_image_path}")
    print(f"Văn bản bí mật: {text}")
    
    return text

def reverse_hiding(stego_image_path, output_path, model_path=None):
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    print(f"Đang sử dụng thiết bị: {device}")
    
    hidden_size = 32
    reverse_decoder = ReverseDecoder(hidden_size).to(device)
    
    if model_path:
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        if 'state_dict_reverse_decoder' in checkpoint:
            reverse_decoder.load_state_dict(checkpoint['state_dict_reverse_decoder'])
            print("Đã tải reverse decoder đã được huấn luyện trước")
        else:
            raise ValueError("Không tìm thấy trọng số reverse decoder trong checkpoint model. "
                           "Model này không được huấn luyện với khả năng reverse hiding.")
    else:
        raise ValueError("Không cung cấp đường dẫn model. Reverse hiding yêu cầu model đã được huấn luyện.")
    
    reverse_decoder.eval()
    
    stego_im = imread(stego_image_path, pilmode='RGB') / 127.5 - 1.0
    stego = torch.FloatTensor(stego_im).permute(2, 1, 0).unsqueeze(0)
    stego = stego.to(device)
    
    with torch.no_grad():
        recovered_cover = reverse_decoder(stego)[0].clamp(-1.0, 1.0)
    
    recovered_cover = (recovered_cover.permute(2, 1, 0).detach().cpu().numpy() + 1.0) * 127.5
    imwrite(output_path, recovered_cover.astype('uint8'))
    
    print(f"Đã khôi phục ảnh cover và lưu vào: {output_path}")
    
    return recovered_cover