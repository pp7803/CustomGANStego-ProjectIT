#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RUNSTEGO - All-in-one Steganography Tool
========================================

Encode, Decode, and Reverse steganography with optional RSA+AES encryption.

Usage:
    python runstego.py encode <image> <text> [options]
    python runstego.py decode <stego_image> [options]
    python runstego.py reverse <stego_image> [options]

Examples:
    # Encode (hide message in image)
    python runstego.py encode cover.png "Secret message"
    python runstego.py encode cover.png "Confidential" --encrypt
    python runstego.py encode cover.png "Hello" --output stego.png
    
    # Decode (extract message from stego image)
    python runstego.py decode stego.png
    python runstego.py decode stego.png --output secret.txt
    python runstego.py decode stego.png --encrypt --private-key private_key.pem
    
    # Reverse (recover original cover image)
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
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Fix import path when running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhancedstegan import encode_message, decode_message, reverse_hiding

# Try to import crypto libraries
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ==================== UTILITY FUNCTIONS ====================

def compute_image_metrics(img1_path, img2_path):
    """
    Compute PSNR and correlation between two images.
    
    Args:
        img1_path: Path to first image
        img2_path: Path to second image
        
    Returns:
        tuple: (mse, psnr, correlation)
    """
    img1 = np.array(Image.open(img1_path).convert('RGB')).astype(np.float32)
    img2 = np.array(Image.open(img2_path).convert('RGB')).astype(np.float32)
    
    # Normalize to [0, 1]
    img1 = img1 / 255.0
    img2 = img2 / 255.0
    
    # MSE
    mse = np.mean((img1 - img2) ** 2)
    
    # PSNR (max pixel value = 1.0 for normalized images)
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 10 * np.log10(1.0 / mse)
    
    # Correlation
    correlation = np.corrcoef(img1.flatten(), img2.flatten())[0, 1]
    
    return mse, psnr, correlation


def create_comparison_image(cover_path, stego_path, recovered_path=None, output_path='comparison.png'):
    """
    Create a comparison visualization showing cover, stego, recovered, and difference images.
    
    Args:
        cover_path: Path to original cover image
        stego_path: Path to stego image
        recovered_path: Optional path to recovered image (for reverse hiding)
        output_path: Where to save the comparison image
    """
    # Load images
    cover_img = Image.open(cover_path).convert('RGB')
    stego_img = Image.open(stego_path).convert('RGB')
    
    # Compute metrics
    mse_stego, psnr_stego, corr_stego = compute_image_metrics(cover_path, stego_path)
    
    # Determine layout
    if recovered_path and os.path.exists(recovered_path):
        recovered_img = Image.open(recovered_path).convert('RGB')
        mse_recov, psnr_recov, corr_recov = compute_image_metrics(cover_path, recovered_path)
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        has_recovered = True
    else:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        has_recovered = False
    
    # Row 1: Original images
    axes[0, 0].imshow(cover_img)
    axes[0, 0].set_title('Original Cover Image', fontsize=12, fontweight='bold')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(stego_img)
    axes[0, 1].set_title(f'Stego Image\nPSNR: {psnr_stego:.2f} dB | MSE: {mse_stego:.6f}', fontsize=11)
    axes[0, 1].axis('off')
    
    if has_recovered:
        axes[0, 2].imshow(recovered_img)
        axes[0, 2].set_title(f'Recovered Image\nPSNR: {psnr_recov:.2f} dB | MSE: {mse_recov:.6f}', fontsize=11)
        axes[0, 2].axis('off')
    
    # Row 2: Difference images (amplified for visibility)
    cover_np = np.array(cover_img).astype(float)
    stego_np = np.array(stego_img).astype(float)
    
    axes[1, 0].imshow(np.zeros_like(cover_np, dtype=np.uint8))
    axes[1, 0].set_title('Reference (Black)', fontsize=12, fontweight='bold')
    axes[1, 0].axis('off')
    
    # Difference: Cover - Stego (amplified 10x)
    diff_stego = np.abs(cover_np - stego_np)
    diff_stego_amp = (diff_stego * 10).clip(0, 255).astype(np.uint8)
    axes[1, 1].imshow(diff_stego_amp)
    max_diff_stego = diff_stego.max()
    axes[1, 1].set_title(f'Diff: Cover - Stego (10x)\nMax diff: {max_diff_stego:.2f}', fontsize=11)
    axes[1, 1].axis('off')
    
    if has_recovered:
        recovered_np = np.array(recovered_img).astype(float)
        diff_recov = np.abs(cover_np - recovered_np)
        diff_recov_amp = (diff_recov * 10).clip(0, 255).astype(np.uint8)
        axes[1, 2].imshow(diff_recov_amp)
        max_diff_recov = diff_recov.max()
        axes[1, 2].set_title(f'Diff: Cover - Recovered (10x)\nMax diff: {max_diff_recov:.2f}', fontsize=11)
        axes[1, 2].axis('off')
    
    # Overall title
    title = 'Steganography Comparison'
    if has_recovered:
        title += f'\nCover→Stego: {psnr_stego:.2f} dB | Cover→Recovered: {psnr_recov:.2f} dB'
    else:
        title += f'\nCover→Stego PSNR: {psnr_stego:.2f} dB'
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Comparison image saved: {output_path}")
    
    # Return metrics for display
    return {
        'stego': {'mse': mse_stego, 'psnr': psnr_stego, 'corr': corr_stego},
        'recovered': {'mse': mse_recov, 'psnr': psnr_recov, 'corr': corr_recov} if has_recovered else None
    }


def pack_encrypted_payload(encrypted_aes_key: bytes, encrypted_aes_iv: bytes, ciphertext: bytes) -> bytes:
    """
    Pack encrypted data into compact binary format (instead of JSON + base64).
    
    Format:
        [2 bytes: key_len] [key_len bytes: encrypted_key]
        [2 bytes: iv_len] [iv_len bytes: encrypted_iv]
        [rest: ciphertext]
    
    This reduces payload from ~750 bytes (JSON+base64) to ~530 bytes (binary).
    """
    key_len = len(encrypted_aes_key)
    iv_len = len(encrypted_aes_iv)
    
    # Pack: H = unsigned short (2 bytes)
    packed = struct.pack(f'H{key_len}sH{iv_len}s', 
                         key_len, encrypted_aes_key,
                         iv_len, encrypted_aes_iv)
    packed += ciphertext
    
    return packed


def unpack_encrypted_payload(packed_data: bytes) -> tuple[bytes, bytes, bytes]:
    """
    Unpack binary encrypted payload.
    
    Returns:
        (encrypted_aes_key, encrypted_aes_iv, ciphertext)
    """
    offset = 0
    
    # Read key length and key
    key_len = struct.unpack('H', packed_data[offset:offset+2])[0]
    offset += 2
    encrypted_aes_key = packed_data[offset:offset+key_len]
    offset += key_len
    
    # Read IV length and IV
    iv_len = struct.unpack('H', packed_data[offset:offset+2])[0]
    offset += 2
    encrypted_aes_iv = packed_data[offset:offset+iv_len]
    offset += iv_len
    
    # Rest is ciphertext
    ciphertext = packed_data[offset:]
    
    return encrypted_aes_key, encrypted_aes_iv, ciphertext


def find_best_model(models_dir='results/model'):
    """Find best model by accuracy, PSNR, and reverse PSNR from results/model"""
    if not os.path.isdir(models_dir):
        return None
    
    # Pattern: EN_DE_REV_ep{epoch}_acc{acc}_psnr{psnr}_rpsnr{rpsnr}_{timestamp}.dat
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
        
        # Weighted scoring: accuracy (60%) + PSNR (25%) + reverse PSNR (15%)
        score = (acc - 0.9) * 100 * 0.6 + (psnr - 25) * 0.25 + (rpsnr - 25) * 0.15
        
        if score > best_score:
            best_score = score
            best = os.path.join(models_dir, fname)
    
    return best


def get_model_path(model_arg):
    """Get model path, auto-select if not specified"""
    if model_arg:
        return model_arg
    
    model = find_best_model()
    if model:
        print(f"🤖 Using best model: {os.path.basename(model)}")
        return model
    
    # Fallback
    if os.path.exists('image_models/a.dat'):
        return 'image_models/a.dat'
    
    print("❌ No model found. Train a model first: python train.py")
    return None


# ==================== ENCRYPTION FUNCTIONS ====================

def encrypt_with_aes(plaintext: str, key: bytes, iv: bytes) -> bytes:
    """Encrypt plaintext using AES-256-CBC."""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
    return cipher.encrypt(padded_data)


def encrypt_with_rsa(data: bytes, public_key_path: Path) -> bytes:
    """Encrypt data using RSA public key."""
    with open(public_key_path, 'rb') as f:
        public_key = RSA.import_key(f.read())
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)


def decrypt_with_rsa(encrypted_data: bytes, private_key_path: Path) -> bytes:
    """Decrypt data using RSA private key."""
    with open(private_key_path, 'rb') as f:
        private_key = RSA.import_key(f.read())
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(encrypted_data)


def decrypt_with_aes(ciphertext: bytes, key: bytes, iv: bytes) -> str:
    """Decrypt ciphertext using AES-256-CBC."""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    plaintext = unpad(decrypted_padded, AES.block_size)
    return plaintext.decode('utf-8')


# ==================== COMMAND HANDLERS ====================

def cmd_encode(args):
    """Handle encode command"""
    # Auto-generate output filename if not specified
    if args.output is None:
        input_path = Path(args.image)
        args.output = f"stego_{input_path.stem}.png"
    
    # Get model path
    model_path = get_model_path(args.model)
    if not model_path:
        return 1
    
    # Validate inputs
    if not os.path.exists(args.image):
        print(f"❌ Cover image not found: {args.image}")
        return 1
    
    if not os.path.exists(model_path):
        print(f"❌ Model checkpoint not found: {model_path}")
        return 1
    
    # Handle encryption
    if args.encrypt:
        if not CRYPTO_AVAILABLE:
            print("❌ Encryption requires pycryptodome. Install: pip install pycryptodome")
            return 1
        
        if not os.path.exists(args.public_key):
            print(f"⚠️  Public key not found: {args.public_key}")
            print("   Generating RSA keypair...")
            os.system("python genRSA.py")
            if not os.path.exists(args.public_key):
                print("❌ Failed to generate keys")
                return 1
        
        print("🔐 Starting encryption process...")
        print(f"📄 Secret text: {args.text}")
        
        # Step 1: Generate random AES key and IV
        aes_key = get_random_bytes(32)  # 256 bits
        aes_iv = get_random_bytes(16)   # 128 bits
        print(f"🔑 Generated AES-256 key: {len(aes_key)} bytes")
        print(f"🔑 Generated IV: {len(aes_iv)} bytes")
        
        # Step 2: Encrypt plaintext with AES
        ciphertext = encrypt_with_aes(args.text, aes_key, aes_iv)
        print(f"✅ AES encrypted ciphertext: {len(ciphertext)} bytes")
        
        # Step 3: Encrypt AES key and IV with RSA
        encrypted_aes_key = encrypt_with_rsa(aes_key, Path(args.public_key))
        encrypted_aes_iv = encrypt_with_rsa(aes_iv, Path(args.public_key))
        print(f"✅ RSA encrypted AES key: {len(encrypted_aes_key)} bytes")
        print(f"✅ RSA encrypted IV: {len(encrypted_aes_iv)} bytes")
        
        # Step 4: Pack payload in compact binary format (NOT JSON + base64)
        packed_payload = pack_encrypted_payload(encrypted_aes_key, encrypted_aes_iv, ciphertext)
        
        # Convert binary to base64 for text transmission
        message_to_hide = base64.b64encode(packed_payload).decode('utf-8')
        
        print(f"📦 Encrypted payload size: {len(message_to_hide)} bytes (binary format)")
        print(f"   ↳ Original JSON format would be ~{len(json.dumps({'aeskey': base64.b64encode(encrypted_aes_key).decode(), 'aesiv': base64.b64encode(encrypted_aes_iv).decode(), 'ciphertext': base64.b64encode(ciphertext).decode()}))} bytes")
    else:
        print("📝 Encoding without encryption...")
        print(f"📄 Secret text: {args.text}")
        message_to_hide = args.text
    
    # Hide message in image
    print(f"🖼️  Encoding into image: {args.image}")
    try:
        encode_message(
            cover_image_path=args.image,
            secret_text=message_to_hide,
            output_path=args.output,
            model_path=model_path
        )
    except Exception as e:
        print(f"❌ Encoding failed: {e}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS!")
    print(f"{'='*60}")
    print(f"📤 Original text: {args.text}")
    if args.encrypt:
        print(f"🔐 Encryption: AES-256-CBC + RSA-2048")
    else:
        print(f"📝 Encryption: None (plain text)")
    print(f"💾 Stego image: {args.output}")
    
    # Generate comparison image if requested
    if args.compare:
        print(f"\n📊 Generating comparison image...")
        comparison_path = f"comparison_{Path(args.output).stem}.png"
        try:
            metrics = create_comparison_image(
                cover_path=args.image,
                stego_path=args.output,
                recovered_path=None,
                output_path=comparison_path
            )
            print(f"\n📈 Image Quality Metrics:")
            print(f"   PSNR (Cover→Stego): {metrics['stego']['psnr']:.2f} dB")
            print(f"   MSE:  {metrics['stego']['mse']:.6f}")
            print(f"   Correlation: {metrics['stego']['corr']:.4f}")
            print(f"💾 Comparison saved: {comparison_path}")
        except Exception as e:
            print(f"⚠️  Warning: Failed to create comparison image: {e}")
    
    print(f"{'='*60}")
    return 0


def cmd_decode(args):
    """Handle decode command"""
    # Get model path
    model_path = get_model_path(args.model)
    if not model_path:
        return 1
    
    # Validate inputs
    if not os.path.exists(args.image):
        print(f"❌ Stego image not found: {args.image}")
        return 1
    
    if not os.path.exists(model_path):
        print(f"❌ Model checkpoint not found: {model_path}")
        return 1
    
    # Handle decryption
    if args.encrypt:
        if not CRYPTO_AVAILABLE:
            print("❌ Decryption requires pycryptodome. Install: pip install pycryptodome")
            return 1
        
        if not os.path.exists(args.private_key):
            print(f"❌ Private key not found: {args.private_key}")
            print("💡 Generate keys first: python genRSA.py")
            return 1
        
        print("🔓 Starting decryption process...")
    else:
        print("🔍 Extracting message...")
    
    print(f"🖼️  Stego image: {args.image}")
    
    # Extract hidden message from image
    try:
        extracted_message = decode_message(
            stego_image_path=args.image,
            model_path=model_path
        )
    except Exception as e:
        print(f"❌ Decoding failed: {e}")
        return 1
    
    print(f"✅ Extracted payload: {len(extracted_message)} bytes")
    
    # Handle encrypted vs plain message
    if args.encrypt:
        # Unpack binary encrypted payload
        try:
            # Try binary format first (new format)
            packed_data = base64.b64decode(extracted_message)
            encrypted_aes_key, encrypted_aes_iv, ciphertext = unpack_encrypted_payload(packed_data)
            print(f"✅ Unpacked binary payload (new format)")
        except Exception as e1:
            # Fallback to JSON format (old format - for backward compatibility)
            try:
                payload = json.loads(extracted_message)
                encrypted_aes_key = base64.b64decode(payload["aeskey"])
                encrypted_aes_iv = base64.b64decode(payload["aesiv"])
                ciphertext = base64.b64decode(payload["ciphertext"])
                print(f"✅ Parsed JSON payload (old format)")
            except Exception as e2:
                print(f"❌ Failed to parse encrypted payload:")
                print(f"   Binary format error: {e1}")
                print(f"   JSON format error: {e2}")
                print("💡 Maybe the message was not encrypted? Try without --encrypt flag.")
                return 1
        
        # Decrypt AES key and IV with RSA
        try:
            aes_key = decrypt_with_rsa(encrypted_aes_key, Path(args.private_key))
            aes_iv = decrypt_with_rsa(encrypted_aes_iv, Path(args.private_key))
            print(f"✅ RSA decrypted AES key and IV")
        except Exception as e:
            print(f"❌ RSA decryption failed: {e}")
            return 1
        
        # Decrypt ciphertext with AES
        try:
            secret_message = decrypt_with_aes(ciphertext, aes_key, aes_iv)
            print(f"✅ AES decrypted ciphertext")
        except Exception as e:
            print(f"❌ AES decryption failed: {e}")
            return 1
    else:
        secret_message = extracted_message
    
    # Output result
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS!")
    print(f"{'='*60}")
    print(f"📤 Recovered message:")
    print(f"{secret_message}")
    print(f"{'='*60}")
    
    if args.output:
        Path(args.output).write_text(secret_message, encoding='utf-8')
        print(f"💾 Saved to: {args.output}")
    
    return 0


def cmd_reverse(args):
    """Handle reverse command"""
    # Auto-generate output filename if not specified
    if args.output is None:
        input_path = Path(args.image)
        args.output = f"{input_path.stem}_recovered{input_path.suffix}"
    
    # Get model path
    model_path = get_model_path(args.model)
    if not model_path:
        return 1
    
    # Validate inputs
    if not os.path.exists(args.image):
        print(f"❌ Stego image not found: {args.image}")
        return 1
    
    if not os.path.exists(model_path):
        print(f"❌ Model checkpoint not found: {model_path}")
        return 1
    
    print("🔄 Starting reverse hiding process...")
    print(f"🖼️  Stego image: {args.image}")
    
    # Perform reverse hiding
    try:
        reverse_hiding(
            stego_image_path=args.image,
            output_path=args.output,
            model_path=model_path
        )
    except Exception as e:
        print(f"❌ Reverse hiding failed: {e}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS!")
    print(f"{'='*60}")
    print(f"📥 Stego image: {args.image}")
    print(f"📤 Recovered cover: {args.output}")
    
    # Generate comparison image if requested and cover image provided
    if args.compare and args.cover:
        if not os.path.exists(args.cover):
            print(f"⚠️  Warning: Cover image not found: {args.cover}")
            print(f"   Skipping comparison generation.")
        else:
            print(f"\n📊 Generating comparison image...")
            comparison_path = f"comparison_reverse_{Path(args.output).stem}.png"
            try:
                metrics = create_comparison_image(
                    cover_path=args.cover,
                    stego_path=args.image,
                    recovered_path=args.output,
                    output_path=comparison_path
                )
                print(f"\n📈 Image Quality Metrics:")
                print(f"   PSNR (Cover→Stego):     {metrics['stego']['psnr']:.2f} dB")
                print(f"   PSNR (Cover→Recovered): {metrics['recovered']['psnr']:.2f} dB")
                print(f"   Recovery Quality: {metrics['recovered']['corr']:.4f}")
                print(f"💾 Comparison saved: {comparison_path}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to create comparison image: {e}")
    elif args.compare:
        print(f"\n⚠️  Note: --compare requires --cover <original_image> to generate comparison")
    
    print(f"{'='*60}")
    
    return 0


# ==================== MAIN ====================

def main():
    # Create main parser with examples in epilog
    parser = argparse.ArgumentParser(
        prog='runstego',
        description='🔐 All-in-one Steganography Tool - Encode, Decode, and Reverse',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔒 ENCODE (Hide message in image):
  python runstego.py encode cover.png "Secret message"
  python runstego.py encode cover.png "Confidential" --encrypt
  python runstego.py encode cover.png "Hello" --output stego.png

🔓 DECODE (Extract message from stego image):
  python runstego.py decode stego.png
  python runstego.py decode stego.png --output secret.txt
  python runstego.py decode stego.png --encrypt

 REVERSE (Recover original cover image):
  python runstego.py reverse stego.png
  python runstego.py reverse stego.png --output recovered.png

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 WORKFLOW EXAMPLE:
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
    encode_parser.add_argument('image', type=str, help='Cover image path')
    encode_parser.add_argument('text', type=str, help='Secret text to hide')
    encode_parser.add_argument('--output', '-o', type=str, default=None,
                               help='Output stego image path (default: stego_<input>.png)')
    encode_parser.add_argument('--encrypt', '-e', action='store_true',
                               help='Enable RSA+AES encryption')
    encode_parser.add_argument('--public-key', type=str, default='public_key.pem',
                               help='RSA public key path (default: public_key.pem)')
    encode_parser.add_argument('--model', '-m', type=str, default=None,
                               help='Model checkpoint path (auto-selects best if not specified)')
    encode_parser.add_argument('--compare', '-c', action='store_true',
                               help='Generate comparison image showing cover vs stego with metrics')
    
    # ===== DECODE subcommand =====
    decode_parser = subparsers.add_parser(
        'decode',
        help='Extract secret message from stego image',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runstego.py decode stego.png
  python runstego.py decode stego.png --output secret.txt
  python runstego.py decode stego.png --encrypt
        """
    )
    decode_parser.add_argument('image', type=str, help='Stego image path')
    decode_parser.add_argument('--output', '-o', type=str, default=None,
                               help='Output text file (default: print to console)')
    decode_parser.add_argument('--encrypt', '-e', action='store_true',
                               help='Decrypt with RSA+AES')
    decode_parser.add_argument('--private-key', type=str, default='private_key.pem',
                               help='RSA private key path (default: private_key.pem)')
    decode_parser.add_argument('--model', '-m', type=str, default=None,
                               help='Model checkpoint path (auto-selects best if not specified)')
    
    # ===== REVERSE subcommand =====
    reverse_parser = subparsers.add_parser(
        'reverse',
        help='Recover original cover image from stego',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runstego.py reverse stego.png
  python runstego.py reverse stego.png --output recovered.png
        """
    )
    reverse_parser.add_argument('image', type=str, help='Stego image path')
    reverse_parser.add_argument('--output', '-o', type=str, default=None,
                                help='Output recovered image (default: <input>_recovered.png)')
    reverse_parser.add_argument('--cover', type=str, default=None,
                                help='Original cover image path (required for comparison)')
    reverse_parser.add_argument('--model', '-m', type=str, default=None,
                                help='Model checkpoint path (auto-selects best if not specified)')
    reverse_parser.add_argument('--compare', '-c', action='store_true',
                                help='Generate comparison image showing cover/stego/recovered with metrics')
    
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
