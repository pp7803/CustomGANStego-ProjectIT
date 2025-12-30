"""
RUNSTEGO - Công Cụ Steganography Tất Cả Trong Một

Mã hóa, Giải mã, và Đảo ngược steganography với tùy chọn mã hóa RSA+AES.

Cách dùng:
    python runstego.py encode <ảnh> <văn_bản> [tùy_chọn]
    python runstego.py decode <ảnh_stego> [tùy_chọn]
    python runstego.py reverse <ảnh_stego> [tùy_chọn]

Ví dụ:
    # Encode (ẩn message vào ảnh)
    python runstego.py encode cover.png "Secret message"
    python runstego.py encode cover.png "Confidential" --encrypt
    python runstego.py encode cover.png "Hello" --output stego.png
    
    # Decode (trích xuất message từ ảnh stego)
    python runstego.py decode stego.png
    python runstego.py decode stego.png --output secret.txt
    python runstego.py decode stego.png --encrypt --private-key private_key.pem
    
    # Reverse (khôi phục ảnh cover gốc)
    python runstego.py reverse stego.png
    python runstego.py reverse stego.png --output recovered.png
"""

import os
import sys
import re
import json
import base64
import struct
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhancedstegan import encode_message, decode_message, reverse_hiding

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# UTILITY FUNCTIONS

def compute_image_metrics(img1_path, img2_path):
    """
    Tính toán PSNR và correlation giữa hai ảnh.
    
    Args:
        img1_path: Đường dẫn ảnh thứ nhất
        img2_path: Đường dẫn ảnh thứ hai
        
    Returns:
        tuple: (mse, psnr, correlation)
    """
    img1 = np.array(Image.open(img1_path).convert('RGB')).astype(np.float32)
    img2 = np.array(Image.open(img2_path).convert('RGB')).astype(np.float32)
    
    img1 = img1 / 255.0
    img2 = img2 / 255.0
    
    mse = np.mean((img1 - img2) ** 2)
    
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 10 * np.log10(1.0 / mse)
    
    correlation = np.corrcoef(img1.flatten(), img2.flatten())[0, 1]
    
    return mse, psnr, correlation


def create_comparison_image(cover_path, stego_path, recovered_path=None, output_path='comparison.png'):
    """
    Tạo ảnh so sánh hiển thị cover, stego, recovered và ảnh chênh lệch.
    
    Args:
        cover_path: Đường dẫn ảnh cover gốc
        stego_path: Đường dẫn ảnh stego
        recovered_path: Đường dẫn tùy chọn tới ảnh đã khôi phục (cho reverse hiding)
        output_path: Nơi lưu ảnh so sánh
    """
    cover_img = Image.open(cover_path).convert('RGB')
    stego_img = Image.open(stego_path).convert('RGB')
    
    mse_stego, psnr_stego, corr_stego = compute_image_metrics(cover_path, stego_path)
    
    if recovered_path and os.path.exists(recovered_path):
        recovered_img = Image.open(recovered_path).convert('RGB')
        mse_recov, psnr_recov, corr_recov = compute_image_metrics(cover_path, recovered_path)
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        has_recovered = True
    else:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        has_recovered = False
    
    axes[0, 0].imshow(cover_img)
    axes[0, 0].set_title('Ảnh Cover Gốc', fontsize=12, fontweight='bold')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(stego_img)
    axes[0, 1].set_title(f'Ảnh Stego\nPSNR: {psnr_stego:.2f} dB | MSE: {mse_stego:.6f}', fontsize=11)
    axes[0, 1].axis('off')
    
    if has_recovered:
        axes[0, 2].imshow(recovered_img)
        axes[0, 2].set_title(f'Ảnh Đã Khôi Phục\nPSNR: {psnr_recov:.2f} dB | MSE: {mse_recov:.6f}', fontsize=11)
        axes[0, 2].axis('off')
    
    cover_np = np.array(cover_img).astype(float)
    stego_np = np.array(stego_img).astype(float)
    
    axes[1, 0].imshow(np.zeros_like(cover_np, dtype=np.uint8))
    axes[1, 0].set_title('Tham Chiếu (Đen)', fontsize=12, fontweight='bold')
    axes[1, 0].axis('off')
    
    diff_stego = np.abs(cover_np - stego_np)
    diff_stego_amp = (diff_stego * 10).clip(0, 255).astype(np.uint8)
    axes[1, 1].imshow(diff_stego_amp)
    max_diff_stego = diff_stego.max()
    axes[1, 1].set_title(f'Chênh lệch: Cover - Stego (10x)\nChênh lệch tối đa: {max_diff_stego:.2f}', fontsize=11)
    axes[1, 1].axis('off')
    
    if has_recovered:
        recovered_np = np.array(recovered_img).astype(float)
        diff_recov = np.abs(cover_np - recovered_np)
        diff_recov_amp = (diff_recov * 10).clip(0, 255).astype(np.uint8)
        axes[1, 2].imshow(diff_recov_amp)
        max_diff_recov = diff_recov.max()
        axes[1, 2].set_title(f'Chênh lệch: Cover - Recovered (10x)\nChênh lệch tối đa: {max_diff_recov:.2f}', fontsize=11)
        axes[1, 2].axis('off')
    
    title = 'So Sánh Steganography'
    if has_recovered:
        title += f'\nCover→Stego: {psnr_stego:.2f} dB | Cover→Recovered: {psnr_recov:.2f} dB'
    else:
        title += f'\nCover→Stego PSNR: {psnr_stego:.2f} dB'
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Ảnh so sánh đã lưu: {output_path}")
    
    return {
        'stego': {'mse': mse_stego, 'psnr': psnr_stego, 'corr': corr_stego},
        'recovered': {'mse': mse_recov, 'psnr': psnr_recov, 'corr': corr_recov} if has_recovered else None
    }


def pack_encrypted_payload(encrypted_aes_key: bytes, encrypted_aes_iv: bytes, ciphertext: bytes) -> bytes:
    """
    Đóng gói dữ liệu mã hóa vào định dạng nhị phân nhỏ gọn (thay vì JSON + base64).
    
    Định dạng:
        [2 bytes: key_len] [key_len bytes: encrypted_key]
        [2 bytes: iv_len] [iv_len bytes: encrypted_iv]
        [phần còn lại: ciphertext]
    
    Điều này giảm payload từ ~750 bytes (JSON+base64) xuống ~530 bytes (nhị phân).
    """
    key_len = len(encrypted_aes_key)
    iv_len = len(encrypted_aes_iv)
    
    packed = struct.pack(f'H{key_len}sH{iv_len}s', 
                         key_len, encrypted_aes_key,
                         iv_len, encrypted_aes_iv)
    packed += ciphertext
    
    return packed


def unpack_encrypted_payload(packed_data: bytes) -> tuple[bytes, bytes, bytes]:
    """
    Giải nén payload mã hóa nhị phân.
    
    Returns:
        (encrypted_aes_key, encrypted_aes_iv, ciphertext)
    """
    offset = 0
    
    key_len = struct.unpack('H', packed_data[offset:offset+2])[0]
    offset += 2
    encrypted_aes_key = packed_data[offset:offset+key_len]
    offset += key_len
    
    iv_len = struct.unpack('H', packed_data[offset:offset+2])[0]
    offset += 2
    encrypted_aes_iv = packed_data[offset:offset+iv_len]
    offset += iv_len
    
    ciphertext = packed_data[offset:]
    
    return encrypted_aes_key, encrypted_aes_iv, ciphertext


def find_best_model(models_dir='results/model'):
    """Tìm model tốt nhất theo accuracy, PSNR, và reverse PSNR từ results/model"""
    if not os.path.isdir(models_dir):
        return None
    
    pattern = re.compile(r'acc([0-9]*\.?[0-9]+).*psnr([0-9]*\.?[0-9]+).*rpsnr([0-9]*\.?[0-9]+)')
    best = None
    best_score = -1.0
    
    for fname in os.listdir(models_dir):
        if not fname.endswith('.dat'):
            continue
        m = pattern.search(fname)
        if not m:
            continue
        try:
            acc = float(m.group(1))
            psnr = float(m.group(2))
            rpsnr = float(m.group(3))
        except:
            continue
        
        score = (acc - 0.9) * 100 * 0.6 + (psnr - 25) * 0.25 + (rpsnr - 25) * 0.15
        
        if score > best_score:
            best_score = score
            best = os.path.join(models_dir, fname)
    
    return best


def get_model_path(model_arg):
    """Lấy đường dẫn model, tự động chọn nếu không chỉ định"""
    if model_arg:
        return model_arg
    
    model = find_best_model()
    if model:
        print(f"Đang sử dụng model tốt nhất: {os.path.basename(model)}")
        return model
    
    if os.path.exists('image_models/a.dat'):
        return 'image_models/a.dat'
    
    print("Không tìm thấy model. Hãy huấn luyện model trước: python train.py")
    return None


# ENCRYPTION FUNCTIONS

def encrypt_with_aes(plaintext: str, key: bytes, iv: bytes) -> bytes:
    """Mã hóa plaintext sử dụng AES-256-CBC."""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
    return cipher.encrypt(padded_data)


def encrypt_with_rsa(data: bytes, public_key_path: Path) -> bytes:
    """Mã hóa dữ liệu sử dụng khóa public RSA."""
    with open(public_key_path, 'rb') as f:
        public_key = RSA.import_key(f.read())
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)


def decrypt_with_rsa(encrypted_data: bytes, private_key_path: Path) -> bytes:
    """Giải mã dữ liệu sử dụng khóa private RSA."""
    with open(private_key_path, 'rb') as f:
        private_key = RSA.import_key(f.read())
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(encrypted_data)


def decrypt_with_aes(ciphertext: bytes, key: bytes, iv: bytes) -> str:
    """Giải mã ciphertext sử dụng AES-256-CBC."""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    plaintext = unpad(decrypted_padded, AES.block_size)
    return plaintext.decode('utf-8')


# COMMAND HANDLERS

def cmd_encode(args):
    """Xử lý lệnh encode"""
    if args.output is None:
        input_path = Path(args.image)
        args.output = f"stego_{input_path.stem}.png"
    
    model_path = get_model_path(args.model)
    if not model_path:
        return 1
    
    if not os.path.exists(args.image):
        print(f"Không tìm thấy ảnh cover: {args.image}")
        return 1
    
    if not os.path.exists(model_path):
        print(f"Không tìm thấy checkpoint model: {model_path}")
        return 1
    
    if args.encrypt:
        if not CRYPTO_AVAILABLE:
            print("Mã hóa yêu cầu pycryptodome. Cài đặt: pip install pycryptodome")
            return 1
        
        if not os.path.exists(args.public_key):
            print(f"Không tìm thấy khóa public: {args.public_key}")
            print("   Đang tạo cặp khóa RSA...")
            os.system("python genRSA.py")
            if not os.path.exists(args.public_key):
                print("Không thể tạo khóa")
                return 1
        
        print("Đang bắt đầu quá trình mã hóa...")
        print(f"Văn bản bí mật: {args.text}")
        
        aes_key = get_random_bytes(32)  # 256 bits
        aes_iv = get_random_bytes(16)   # 128 bits
        print(f"Đã tạo khóa AES-256: {len(aes_key)} bytes")
        print(f"Đã tạo IV: {len(aes_iv)} bytes")
        
        ciphertext = encrypt_with_aes(args.text, aes_key, aes_iv)
        print(f"Ciphertext đã mã hóa AES: {len(ciphertext)} bytes")
        
        encrypted_aes_key = encrypt_with_rsa(aes_key, Path(args.public_key))
        encrypted_aes_iv = encrypt_with_rsa(aes_iv, Path(args.public_key))
        print(f"Khóa AES đã mã hóa RSA: {len(encrypted_aes_key)} bytes")
        print(f"IV đã mã hóa RSA: {len(encrypted_aes_iv)} bytes")
        
        packed_payload = pack_encrypted_payload(encrypted_aes_key, encrypted_aes_iv, ciphertext)
        
        message_to_hide = base64.b64encode(packed_payload).decode('utf-8')
        
        print(f"Kích thước payload đã mã hóa: {len(message_to_hide)} bytes (định dạng nhị phân)")
        print(f"   Định dạng JSON gốc sẽ là ~{len(json.dumps({'aeskey': base64.b64encode(encrypted_aes_key).decode(), 'aesiv': base64.b64encode(encrypted_aes_iv).decode(), 'ciphertext': base64.b64encode(ciphertext).decode()}))} bytes")
    else:
        print("Đang mã hóa không có encryption...")
        print(f"Văn bản bí mật: {args.text}")
        message_to_hide = args.text
    
    print(f"Đang mã hóa vào ảnh: {args.image}")
    try:
        encode_message(
            cover_image_path=args.image,
            secret_text=message_to_hide,
            output_path=args.output,
            model_path=model_path
        )
    except Exception as e:
        print(f"Mã hóa thất bại: {e}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"THÀNH CÔNG!")
    print(f"{'='*60}")
    print(f"Văn bản gốc: {args.text}")
    if args.encrypt:
        print(f"Mã hóa: AES-256-CBC + RSA-2048")
    else:
        print(f"Mã hóa: Không (văn bản thường)")
    print(f"Ảnh stego: {args.output}")
    
    if args.compare:
        print(f"\nĐang tạo ảnh so sánh...")
        comparison_path = f"comparison_{Path(args.output).stem}.png"
        try:
            metrics = create_comparison_image(
                cover_path=args.image,
                stego_path=args.output,
                recovered_path=None,
                output_path=comparison_path
            )
            print(f"\nCác Chỉ Số Chất Lượng Ảnh:")
            print(f"   PSNR (Cover→Stego): {metrics['stego']['psnr']:.2f} dB")
            print(f"   MSE:  {metrics['stego']['mse']:.6f}")
            print(f"   Correlation: {metrics['stego']['corr']:.4f}")
            print(f"So sánh đã lưu: {comparison_path}")
        except Exception as e:
            print(f"Cảnh báo: Không thể tạo ảnh so sánh: {e}")
    
    print(f"{'='*60}")
    return 0


def cmd_decode(args):
    """Xử lý lệnh decode"""
    model_path = get_model_path(args.model)
    if not model_path:
        return 1
    
    if not os.path.exists(args.image):
        print(f"Không tìm thấy ảnh stego: {args.image}")
        return 1
    
    if not os.path.exists(model_path):
        print(f"Không tìm thấy checkpoint model: {model_path}")
        return 1
    
    if args.encrypt:
        if not CRYPTO_AVAILABLE:
            print("Giải mã yêu cầu pycryptodome. Cài đặt: pip install pycryptodome")
            return 1
        
        if not os.path.exists(args.private_key):
            print(f"Không tìm thấy khóa private: {args.private_key}")
            print("Hãy tạo khóa trước: python genRSA.py")
            return 1
        
        print("Đang bắt đầu quá trình giải mã...")
    else:
        print("Đang trích xuất message...")
    
    print(f"Ảnh stego: {args.image}")
    
    try:
        extracted_message = decode_message(
            stego_image_path=args.image,
            model_path=model_path
        )
    except Exception as e:
        print(f"Giải mã thất bại: {e}")
        return 1
    
    print(f"Đã trích xuất payload: {len(extracted_message)} bytes")
    
    if args.encrypt:
        try:
            packed_data = base64.b64decode(extracted_message)
            encrypted_aes_key, encrypted_aes_iv, ciphertext = unpack_encrypted_payload(packed_data)
            print(f"Đã giải nén payload nhị phân (định dạng mới)")
        except Exception as e1:
            try:
                payload = json.loads(extracted_message)
                encrypted_aes_key = base64.b64decode(payload["aeskey"])
                encrypted_aes_iv = base64.b64decode(payload["aesiv"])
                ciphertext = base64.b64decode(payload["ciphertext"])
                print(f"Đã phân tích payload JSON (định dạng cũ)")
            except Exception as e2:
                print(f"Không thể phân tích payload mã hóa:")
                print(f"   Lỗi định dạng nhị phân: {e1}")
                print(f"   Lỗi định dạng JSON: {e2}")
                print("Có thể message không được mã hóa? Thử không dùng cờ --encrypt.")
                return 1
        
        try:
            aes_key = decrypt_with_rsa(encrypted_aes_key, Path(args.private_key))
            aes_iv = decrypt_with_rsa(encrypted_aes_iv, Path(args.private_key))
            print(f"Đã giải mã RSA khóa AES và IV")
        except Exception as e:
            print(f"Giải mã RSA thất bại: {e}")
            return 1
        
        try:
            secret_message = decrypt_with_aes(ciphertext, aes_key, aes_iv)
            print(f"Đã giải mã AES ciphertext")
        except Exception as e:
            print(f"Giải mã AES thất bại: {e}")
            return 1
    else:
        secret_message = extracted_message
    
    print(f"\n{'='*60}")
    print(f"THÀNH CÔNG!")
    print(f"{'='*60}")
    print(f"Message đã khôi phục:")
    print(f"{secret_message}")
    print(f"{'='*60}")
    
    if args.output:
        Path(args.output).write_text(secret_message, encoding='utf-8')
        print(f"Đã lưu vào: {args.output}")
    
    return 0


def cmd_reverse(args):
    """Xử lý lệnh reverse"""
    if args.output is None:
        input_path = Path(args.image)
        args.output = f"{input_path.stem}_recovered{input_path.suffix}"
    
    model_path = get_model_path(args.model)
    if not model_path:
        return 1
    
    if not os.path.exists(args.image):
        print(f"Không tìm thấy ảnh stego: {args.image}")
        return 1
    
    if not os.path.exists(model_path):
        print(f"Không tìm thấy checkpoint model: {model_path}")
        return 1
    
    print("Đang bắt đầu quá trình reverse hiding...")
    print(f"Ảnh stego: {args.image}")
    
    try:
        reverse_hiding(
            stego_image_path=args.image,
            output_path=args.output,
            model_path=model_path
        )
    except Exception as e:
        print(f"Reverse hiding thất bại: {e}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"THÀNH CÔNG!")
    print(f"{'='*60}")
    print(f"Ảnh stego: {args.image}")
    print(f"Cover đã khôi phục: {args.output}")
    
    if args.compare and args.cover:
        if not os.path.exists(args.cover):
            print(f"Không tìm thấy ảnh cover: {args.cover}")
            print(f"   Bỏ qua việc tạo so sánh.")
        else:
            print(f"\nĐang tạo ảnh so sánh...")
            comparison_path = f"comparison_reverse_{Path(args.output).stem}.png"
            try:
                metrics = create_comparison_image(
                    cover_path=args.cover,
                    stego_path=args.image,
                    recovered_path=args.output,
                    output_path=comparison_path
                )
                print(f"\nCác Chỉ Số Chất Lượng Ảnh:")
                print(f"   PSNR (Cover→Stego):     {metrics['stego']['psnr']:.2f} dB")
                print(f"   PSNR (Cover→Recovered): {metrics['recovered']['psnr']:.2f} dB")
                print(f"   Chất lượng khôi phục: {metrics['recovered']['corr']:.4f}")
                print(f"So sánh đã lưu: {comparison_path}")
            except Exception as e:
                print(f"Cảnh báo: Không thể tạo ảnh so sánh: {e}")
    elif args.compare:
        print(f"\nLưu ý: --compare yêu cầu --cover <ảnh_gốc> để tạo so sánh")
    
    print(f"{'='*60}")
    
    return 0


# MAIN

def main():
    parser = argparse.ArgumentParser(
        prog='runstego',
        description='Công Cụ Steganography Tất Cả Trong Một - Mã hóa, Giải mã và Đảo ngược',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENCODE (Hide message in image):
  python runstego.py encode cover.png "Secret message"
  python runstego.py encode cover.png "Confidential" --encrypt
  python runstego.py encode cover.png "Hello" --output stego.png

DECODE (Extract message from stego image):
  python runstego.py decode stego.png
  python runstego.py decode stego.png --output secret.txt
  python runstego.py decode stego.png --encrypt

REVERSE (Recover original cover image):
  python runstego.py reverse stego.png
  python runstego.py reverse stego.png --output recovered.png

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKFLOW EXAMPLE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # 1. Hide a secret message (with encryption)
  python runstego.py encode photo.png "My secret" --encrypt
  
  # 2. Extract the message later
  python runstego.py decode stego_photo.png --encrypt
  
  # 3. Recover the original image
  python runstego.py reverse stego_photo.png

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # ===== ENCODE subcommand =====
    encode_parser = subparsers.add_parser(
        'encode',
        help='Hide secret message in image',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runstego.py encode cover.png "Secret message"
  python runstego.py encode cover.png "Confidential" --encrypt
  python runstego.py encode cover.png "Hello" --output stego.png
        """
    )
    encode_parser.add_argument('image', type=str, help='Đường dẫn ảnh cover')
    encode_parser.add_argument('text', type=str, help='Văn bản bí mật để ẩn')
    encode_parser.add_argument('--output', '-o', type=str, default=None,
                               help='Đường dẫn ảnh stego đầu ra (mặc định: stego_<input>.png)')
    encode_parser.add_argument('--encrypt', '-e', action='store_true',
                               help='Bật mã hóa RSA+AES')
    encode_parser.add_argument('--public-key', type=str, default='public_key.pem',
                               help='Đường dẫn khóa công khai RSA (mặc định: public_key.pem)')
    encode_parser.add_argument('--model', '-m', type=str, default=None,
                               help='Đường dẫn checkpoint model (tự chọn tốt nhất nếu không chỉ định)')
    encode_parser.add_argument('--compare', '-c', action='store_true',
                               help='Tạo ảnh so sánh hiển thị cover vs stego với các chỉ số')
    
    # ===== DECODE subcommand =====
    decode_parser = subparsers.add_parser(
        'decode',
        help='Trích xuất thông điệp bí mật từ ảnh stego',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python runstego.py decode stego.png
  python runstego.py decode stego.png --output secret.txt
  python runstego.py decode stego.png --encrypt
        """
    )
    decode_parser.add_argument('image', type=str, help='Đường dẫn ảnh stego')
    decode_parser.add_argument('--output', '-o', type=str, default=None,
                               help='File văn bản đầu ra (mặc định: in ra console)')
    decode_parser.add_argument('--encrypt', '-e', action='store_true',
                               help='Giải mã với RSA+AES')
    decode_parser.add_argument('--private-key', type=str, default='private_key.pem',
                               help='Đường dẫn khóa riêng tư RSA (mặc định: private_key.pem)')
    decode_parser.add_argument('--model', '-m', type=str, default=None,
                               help='Đường dẫn checkpoint model (tự chọn tốt nhất nếu không chỉ định)')
    
    # ===== REVERSE subcommand =====
    reverse_parser = subparsers.add_parser(
        'reverse',
        help='Khôi phục ảnh cover gốc từ stego',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python runstego.py reverse stego.png
  python runstego.py reverse stego.png --output recovered.png
        """
    )
    reverse_parser.add_argument('image', type=str, help='Đường dẫn ảnh stego')
    reverse_parser.add_argument('--output', '-o', type=str, default=None,
                                help='Ảnh khôi phục đầu ra (mặc định: <input>_recovered.png)')
    reverse_parser.add_argument('--cover', type=str, default=None,
                                help='Đường dẫn ảnh cover gốc (cần để so sánh)')
    reverse_parser.add_argument('--model', '-m', type=str, default=None,
                                help='Đường dẫn checkpoint model (tự chọn tốt nhất nếu không chỉ định)')
    reverse_parser.add_argument('--compare', '-c', action='store_true',
                                help='Tạo ảnh so sánh hiển thị cover/stego/khôi-phục với các chỉ số')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command
    if args.command is None:
        parser.print_help()
        return 0
    
    # Execute command
    if args.command == 'encode':
        return cmd_encode(args)
    elif args.command == 'decode':
        return cmd_decode(args)
    elif args.command == 'reverse':
        return cmd_reverse(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())
