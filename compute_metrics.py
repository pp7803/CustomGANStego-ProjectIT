"""
Tính toán các chỉ số PSNR, SSIM để so sánh ảnh cover/stego/recovered
"""
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

def load_image(path):
    """Tải ảnh và chuyển đổi sang mảng numpy"""
    img = Image.open(path).convert('RGB')
    return np.array(img)

def compute_metrics(img1_path, img2_path, label):
    """Tính toán PSNR và SSIM giữa 2 ảnh"""
    img1 = load_image(img1_path)
    img2 = load_image(img2_path)
    
    if img1.shape != img2.shape:
        print(f"Cảnh báo: Kích thước ảnh không khớp cho {label}")
        print(f"   {img1_path}: {img1.shape}")
        print(f"   {img2_path}: {img2.shape}")
        return None, None
    
    psnr_val = psnr(img1, img2)
    ssim_val = ssim(img1, img2, channel_axis=2, data_range=255)
    
    return psnr_val, ssim_val

if __name__ == "__main__":
    print("="*60)
    print("Tính Toán Chỉ Số Chất Lượng Ảnh")
    print("="*60)
    
    print("\n1. Cover vs Stego (Chất lượng ảnh giấu tin)")
    psnr_cs, ssim_cs = compute_metrics("../test2.png", "demo_stego.png", "Cover-Stego")
    if psnr_cs:
        print(f"   PSNR: {psnr_cs:.2f} dB")
        print(f"   SSIM: {ssim_cs:.4f}")
    
    print("\n2. Cover vs Recovered (Khả năng khôi phục)")
    psnr_cr, ssim_cr = compute_metrics("../test2.png", "recovered_cover.png", "Cover-Recovered")
    if psnr_cr:
        print(f"   PSNR: {psnr_cr:.2f} dB")
        print(f"   SSIM: {ssim_cr:.4f}")
    
    print("\n" + "="*60)
    print("Tổng Kết")
    print("="*60)
    print(f"Cover → Stego:     PSNR = {psnr_cs:.2f} dB, SSIM = {ssim_cs:.4f}")
    print(f"Cover → Recovered: PSNR = {psnr_cr:.2f} dB, SSIM = {ssim_cr:.4f}")
    print("="*60)
