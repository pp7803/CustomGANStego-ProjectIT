#!/usr/bin/env python3
"""
Tính toán metrics PSNR, SSIM để so sánh ảnh cover/stego/recovered
"""
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

def load_image(path):
    """Load ảnh và chuyển sang numpy array"""
    img = Image.open(path).convert('RGB')
    return np.array(img)

def compute_metrics(img1_path, img2_path, label):
    """Tính PSNR và SSIM giữa 2 ảnh"""
    img1 = load_image(img1_path)
    img2 = load_image(img2_path)
    
    # Đảm bảo cùng kích thước
    if img1.shape != img2.shape:
        print(f"⚠️  Warning: Image sizes don't match for {label}")
        print(f"   {img1_path}: {img1.shape}")
        print(f"   {img2_path}: {img2.shape}")
        return None, None
    
    # Tính PSNR và SSIM
    psnr_val = psnr(img1, img2)
    ssim_val = ssim(img1, img2, channel_axis=2, data_range=255)
    
    return psnr_val, ssim_val

if __name__ == "__main__":
    print("="*60)
    print("📊 Computing Image Quality Metrics")
    print("="*60)
    
    # 1. Cover vs Stego
    print("\n1️⃣  Cover vs Stego (Chất lượng ảnh giấu tin)")
    psnr_cs, ssim_cs = compute_metrics("../test2.png", "demo_stego.png", "Cover-Stego")
    if psnr_cs:
        print(f"   PSNR: {psnr_cs:.2f} dB")
        print(f"   SSIM: {ssim_cs:.4f}")
    
    # 2. Cover vs Recovered
    print("\n2️⃣  Cover vs Recovered (Khả năng khôi phục)")
    psnr_cr, ssim_cr = compute_metrics("../test2.png", "recovered_cover.png", "Cover-Recovered")
    if psnr_cr:
        print(f"   PSNR: {psnr_cr:.2f} dB")
        print(f"   SSIM: {ssim_cr:.4f}")
    
    print("\n" + "="*60)
    print("✅ Summary")
    print("="*60)
    print(f"Cover → Stego:     PSNR = {psnr_cs:.2f} dB, SSIM = {ssim_cs:.4f}")
    print(f"Cover → Recovered: PSNR = {psnr_cr:.2f} dB, SSIM = {ssim_cr:.4f}")
    print("="*60)
