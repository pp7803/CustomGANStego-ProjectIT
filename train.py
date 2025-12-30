import datetime
import matplotlib.pyplot as plt
from torch.nn.functional import binary_cross_entropy_with_logits, mse_loss

from critic import BasicCritic
from decoder import BasicDecoder
from encoder import BasicEncoder, ResidualEncoder
from reverse_decoder import ReverseDecoder

from torchvision import datasets, transforms
from torchvision.models import vgg16, VGG16_Weights
from IPython.display import clear_output
import torchvision
from torch.optim import Adam
from torch.optim.lr_scheduler import CosineAnnealingLR, ReduceLROnPlateau
import numpy as np
from torchmetrics.image import StructuralSimilarityIndexMeasure
from tqdm import tqdm
import torch
import torch.nn.functional as F
import os
import gc
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


def plot(name, train_epoch, values, save):
    """Vẽ và lưu các chỉ số với định dạng cải tiến"""
    clear_output(wait=True)
    plt.close('all')
    fig = plt.figure(figsize=(10, 6))
    plt.ion()
    plt.subplot(1, 1, 1)
    plt.title('Epoch %d -> %s: %.4f' % (train_epoch, name, values[-1]), fontsize=14)
    plt.ylabel(name, fontsize=12)
    plt.xlabel('Batch', fontsize=12)
    plt.plot(values, linewidth=2)
    plt.grid(True, alpha=0.3)
    
    if len(values) > 10:
        window = min(20, len(values) // 5)
        moving_avg = np.convolve(values, np.ones(window)/window, mode='valid')
        plt.plot(range(window-1, len(values)), moving_avg, 
                 'r--', linewidth=2, label=f'MA({window})')
        plt.legend()
    
    get_fig = plt.gcf()
    plt.draw()
    plt.pause(0.1)
    
    if save:
        now = datetime.datetime.now()
        plots_dir = os.path.join(os.path.dirname(__file__), 'results', 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        plot_path = os.path.join(plots_dir, '%s_%d_%.4f_%s.png' %
                        (name, train_epoch, values[-1], now.strftime("%Y-%m-%d_%H:%M:%S")))
        get_fig.savefig(plot_path, dpi=100, bbox_inches='tight')


def compute_gradient_penalty(critic, real_data, fake_data, device):
    """
    Gradient Penalty cho WGAN-GP (thay thế weight clipping)
    Giúp training ổn định hơn và chất lượng tốt hơn
    """
    batch_size = real_data.size(0)
    alpha = torch.rand(batch_size, 1, 1, 1, device=device)
    
    interpolates = (alpha * real_data + (1 - alpha) * fake_data).requires_grad_(True)
    
    d_interpolates = critic(interpolates)
    
    gradients = torch.autograd.grad(
        outputs=d_interpolates,
        inputs=interpolates,
        grad_outputs=torch.ones_like(d_interpolates),
        create_graph=True,
        retain_graph=True,
        only_inputs=True
    )[0]
    
    gradients = gradients.view(batch_size, -1)
    gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean()
    
    return gradient_penalty


def main():
    data_dir = 'div2k'
    epochs = 60
    data_depth = 2
    hidden_size = 32
    batch_size = 4
    
    lr_critic = 2e-4
    lr_encoder_decoder = 2e-4
    
    weight_mse = 70.0
    weight_ssim = 25.0
    weight_perceptual = 8.0
    weight_decoder = 25.0
    weight_adversarial = 0.005
    weight_reverse = 50.0
    
    use_gradient_penalty = True
    lambda_gp = 10.0
    n_critic = 2
    
    stop_on_target = True
    patience = 25
    min_psnr = 37.0
    min_ssim = 0.90
    min_decoder_acc = 0.99
    target_psnr = 38.0
    
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    
    use_pin_memory = (device.type == 'cuda')
    
    print(f"\n{'='*70}")
    print(f"CẤU HÌNH HUẤN LUYỆN CẢI TIẾN")
    print(f"{'='*70}")
    print(f"Thiết bị: {device}")
    print(f"Pin Memory: {use_pin_memory}")
    print(f"Số epoch: {epochs}")
    print(f"Kích thước batch: {batch_size}")
    print(f"LR Critic: {lr_critic}")
    print(f"LR Encoder/Decoder: {lr_encoder_decoder}")
    print(f"\nTrọng số Loss:")
    print(f"  MSE: {weight_mse}")
    print(f"  SSIM: {weight_ssim}")
    print(f"  Perceptual: {weight_perceptual}")
    print(f"  Decoder: {weight_decoder}")
    print(f"  Adversarial: {weight_adversarial}")
    print(f"  Reverse Hiding: {weight_reverse}")
    print(f"\nWGAN-GP: {use_gradient_penalty}")
    print(f"Số vòng lặp Critic: {n_critic}")
    print(f"\nDừng Sớm:")
    print(f"  Dừng khi đạt mục tiêu: {stop_on_target}")
    print(f"  Patience: {patience} epochs")
    print(f"\nMục tiêu:")
    print(f"  Độ chính xác Decoder tối thiểu: {min_decoder_acc:.1%}")
    print(f"  PSNR tối thiểu: {min_psnr:.1f} dB")
    print(f"  SSIM tối thiểu: {min_ssim:.2f}")
    print(f"  PSNR xuất sắc: {target_psnr:.1f} dB")
    print(f"{'='*70}\n")

    ssim_metric = StructuralSimilarityIndexMeasure(data_range=2.0).to(device)

    use_perceptual_loss = False
    vgg = None
    try:
        print("Đang tải VGG16 cho perceptual loss (QUAN TRỌNG để bảo toàn màu sắc)...")
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        from torchvision.models import VGG16_Weights
        vgg = vgg16(weights=VGG16_Weights.DEFAULT).features[:16].to(device).eval()
        for param in vgg.parameters():
            param.requires_grad = False
        use_perceptual_loss = True
        print("VGG16 đã tải thành công - Perceptual loss ĐÃ BẬT")
    except Exception as e:
        print(f"Cảnh báo: Không thể tải VGG16: {e}")
        print(f"   Huấn luyện sẽ tiếp tục không có perceptual loss (màu sắc có thể dịch chuyển)")
        print(f"   Cân nhắc cài đặt torchvision đúng cách để có kết quả tốt nhất")
        weight_perceptual = 0.0

    METRIC_FIELDS = [
        'val.encoder_mse',
        'val.decoder_loss',
        'val.decoder_acc',
        'val.cover_score',
        'val.generated_score',
        'val.ssim',
        'val.psnr',
        'val.bpp',
        'val.reverse_mse',
        'val.reverse_psnr',
        'val.reverse_ssim',
        'train.encoder_mse',
        'train.decoder_loss',
        'train.decoder_acc',
        'train.cover_score',
        'train.generated_score',
        'train.ssim_loss',
        'train.perceptual_loss',
        'train.reverse_mse',
        'train.total_loss',
    ]

    mu = [.5, .5, .5]
    sigma = [.5, .5, .5]

    transform = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(360, pad_if_needed=True),
        transforms.ToTensor(),
        transforms.Normalize(mu, sigma)
    ])

    train_set = datasets.ImageFolder(os.path.join(data_dir, "train/"), transform=transform)
    train_loader = torch.utils.data.DataLoader(
        train_set, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=0,
        pin_memory=False
    )

    valid_set = datasets.ImageFolder(os.path.join(data_dir, "val/"), transform=transform)
    valid_loader = torch.utils.data.DataLoader(
        valid_set, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=0,
        pin_memory=False
    )

    encoder = ResidualEncoder(data_depth, hidden_size).to(device)
    decoder = BasicDecoder(data_depth, hidden_size).to(device)
    reverse_decoder = ReverseDecoder(hidden_size).to(device)
    critic = BasicCritic(hidden_size).to(device)
    
    cr_optimizer = Adam(critic.parameters(), lr=lr_critic, betas=(0.5, 0.999))
    en_de_optimizer = Adam(
        list(decoder.parameters()) + list(encoder.parameters()) + list(reverse_decoder.parameters()), 
        lr=lr_encoder_decoder, 
        betas=(0.5, 0.999)
    )

    print("Đã khởi tạo toàn bộ mô hình và optimizer!")
    print(f"Encoder tham số: {sum(p.numel() for p in encoder.parameters()):,}")
    print(f"Decoder tham số: {sum(p.numel() for p in decoder.parameters()):,}")
    print(f"ReverseDecoder tham số: {sum(p.numel() for p in reverse_decoder.parameters()):,}")
    print(f"Critic tham số: {sum(p.numel() for p in critic.parameters()):,}")
    print(f"Tổng tham số có thể train: {sum(p.numel() for p in list(encoder.parameters()) + list(decoder.parameters()) + list(reverse_decoder.parameters()) + list(critic.parameters())):,}\n")
    
    scheduler_critic = CosineAnnealingLR(cr_optimizer, T_max=epochs, eta_min=1e-6)
    scheduler_encdec = CosineAnnealingLR(en_de_optimizer, T_max=epochs, eta_min=1e-6)
    
    best_psnr = -float('inf')
    best_ssim = -float('inf')
    best_epoch = 0
    patience_counter = 0

    for ep in range(epochs):
        metrics = {field: list() for field in METRIC_FIELDS}
        
        print(f"\n{'='*70}")
        print(f"Epoch {ep+1}/{epochs} | LR Critic: {cr_optimizer.param_groups[0]['lr']:.6f} | LR EncDec: {en_de_optimizer.param_groups[0]['lr']:.6f}")
        print(f"{'='*70}")
        
        encoder.eval()
        decoder.eval()
        reverse_decoder.eval()
        critic.train()
        
        print(f"Huấn luyện Critic ({n_critic}x vòng lặp)...")
        
        for _ in range(n_critic):
            for cover, _ in tqdm(train_loader, desc=f"Critic vòng {_+1}/{n_critic}", leave=False):
                gc.collect()
                cover = cover.to(device)
                N, _, H, W = cover.size()
                
                payload = torch.zeros((N, data_depth, H, W), device=device).random_(0, 2)
                
                with torch.no_grad():
                    generated = encoder(cover, payload)
                
                cover_score = critic(cover).mean()
                generated_score = critic(generated).mean()
                
                critic_loss = generated_score - cover_score
                
                if use_gradient_penalty:
                    gp = compute_gradient_penalty(critic, cover, generated, device)
                    critic_loss += lambda_gp * gp
                
                cr_optimizer.zero_grad()
                critic_loss.backward()
                cr_optimizer.step()
                
                if not use_gradient_penalty:
                    for p in critic.parameters():
                        p.data.clamp_(-0.1, 0.1)
                
                metrics['train.cover_score'].append(cover_score.item())
                metrics['train.generated_score'].append(generated_score.item())

        encoder.train()
        decoder.train()
        reverse_decoder.train()
        critic.eval()
        
        print("Huấn luyện Encoder-Decoder...")
        for cover, _ in tqdm(train_loader, desc="Encoder-Decoder", leave=False):
            gc.collect()
            cover = cover.to(device)
            N, _, H, W = cover.size()
            
            payload = torch.zeros((N, data_depth, H, W), device=device).random_(0, 2)
            
            generated = encoder(cover, payload)
            decoded = decoder(generated)
            recovered_cover = reverse_decoder(generated)
            
            encoder_mse = mse_loss(generated, cover)
            
            ssim_value = ssim_metric(generated, cover)
            ssim_loss = 1.0 - ssim_value
            
            if use_perceptual_loss and vgg is not None:
                gen_normalized = (generated + 1.0) / 2.0
                cover_normalized = (cover + 1.0) / 2.0
                gen_features = vgg(gen_normalized)
                cover_features = vgg(cover_normalized)
                perceptual_loss = mse_loss(gen_features, cover_features)
            else:
                perceptual_loss = torch.tensor(0.0, device=device)
            
            decoder_loss = binary_cross_entropy_with_logits(decoded, payload)
            decoder_acc = (decoded >= 0.0).eq(payload >= 0.5).sum().float() / payload.numel()
            
            generated_score = critic(generated).mean()
            
            reverse_mse = mse_loss(recovered_cover, cover)
            
            total_loss = (
                weight_mse * encoder_mse +
                weight_ssim * ssim_loss +
                weight_perceptual * perceptual_loss +
                weight_decoder * decoder_loss +
                weight_adversarial * generated_score +
                weight_reverse * reverse_mse
            )
            
            en_de_optimizer.zero_grad()
            total_loss.backward()
            
            torch.nn.utils.clip_grad_norm_(encoder.parameters(), max_norm=1.0)
            torch.nn.utils.clip_grad_norm_(decoder.parameters(), max_norm=1.0)
            torch.nn.utils.clip_grad_norm_(reverse_decoder.parameters(), max_norm=1.0)
            
            en_de_optimizer.step()
            
            metrics['train.encoder_mse'].append(encoder_mse.item())
            metrics['train.decoder_loss'].append(decoder_loss.item())
            metrics['train.decoder_acc'].append(decoder_acc.item())
            metrics['train.ssim_loss'].append(ssim_loss.item())
            metrics['train.perceptual_loss'].append(perceptual_loss.item())
            metrics['train.reverse_mse'].append(reverse_mse.item())
            metrics['train.total_loss'].append(total_loss.item())

        encoder.eval()
        decoder.eval()
        reverse_decoder.eval()
        critic.eval()
        
        print("Đang kiểm định...")
        with torch.no_grad():
            for cover, _ in tqdm(valid_loader, desc="Kiểm định", leave=False):
                gc.collect()
                cover = cover.to(device)
                N, _, H, W = cover.size()
                
                payload = torch.zeros((N, data_depth, H, W), device=device).random_(0, 2)
                
                generated = encoder(cover, payload)
                decoded = decoder(generated)
                recovered_cover = reverse_decoder(generated)
                
                encoder_mse = mse_loss(generated, cover)
                decoder_loss = binary_cross_entropy_with_logits(decoded, payload)
                decoder_acc = (decoded >= 0.0).eq(payload >= 0.5).sum().float() / payload.numel()
                generated_score = critic(generated).mean()
                cover_score = critic(cover).mean()
                
                reverse_mse = mse_loss(recovered_cover, cover)
                reverse_psnr = 10 * torch.log10(4 / reverse_mse)
                reverse_ssim = ssim_metric(recovered_cover, cover)
                
                metrics['val.encoder_mse'].append(encoder_mse.item())
                metrics['val.decoder_loss'].append(decoder_loss.item())
                metrics['val.decoder_acc'].append(decoder_acc.item())
                metrics['val.cover_score'].append(cover_score.item())
                metrics['val.generated_score'].append(generated_score.item())
                metrics['val.ssim'].append(ssim_metric(generated, cover).item())
                metrics['val.psnr'].append(10 * torch.log10(4 / encoder_mse).item())
                metrics['val.bpp'].append(data_depth * (2 * decoder_acc.item() - 1))
                metrics['val.reverse_mse'].append(reverse_mse.item())
                metrics['val.reverse_psnr'].append(reverse_psnr.item())
                metrics['val.reverse_ssim'].append(reverse_ssim.item())
        
        avg_psnr = np.mean(metrics['val.psnr'])
        avg_ssim = np.mean(metrics['val.ssim'])
        avg_decoder_acc = np.mean(metrics['val.decoder_acc'])
        avg_bpp = np.mean(metrics['val.bpp'])
        avg_reverse_psnr = np.mean(metrics['val.reverse_psnr'])
        avg_reverse_ssim = np.mean(metrics['val.reverse_ssim'])
        
        print(f"\n{'─'*70}")
        print(f"Tổng kết Epoch {ep+1}:")
        print(f"{'─'*70}")
        print(f"Hiệu suất Decoder:")
        print(f"   Độ chính xác Train: {np.mean(metrics['train.decoder_acc']):.4f}")
        print(f"   Độ chính xác Val:   {avg_decoder_acc:.4f}")
        print(f"   Loss Train:         {np.mean(metrics['train.decoder_loss']):.6f}")
        print(f"   Loss Val:           {np.mean(metrics['val.decoder_loss']):.6f}")
        print(f"\nChất lượng Ảnh (Stego):")
        print(f"   MSE Train:  {np.mean(metrics['train.encoder_mse']):.6f}")
        print(f"   MSE Val:    {np.mean(metrics['val.encoder_mse']):.6f}")
        print(f"   SSIM Val:   {avg_ssim:.4f}")
        print(f"   PSNR Val:   {avg_psnr:.2f} dB")
        print(f"\nReverse Hiding (Khôi phục Cover):")
        print(f"   MSE Train:  {np.mean(metrics['train.reverse_mse']):.6f}")
        print(f"   MSE Val:    {np.mean(metrics['val.reverse_mse']):.6f}")
        print(f"   SSIM Val:   {avg_reverse_ssim:.4f}")
        print(f"   PSNR Val:   {avg_reverse_psnr:.2f} dB")
        print(f"\nDung lượng:")
        print(f"   BPP Val: {avg_bpp:.4f}")
        print(f"\nAdversarial:")
        print(f"   Điểm Cover:     {np.mean(metrics['val.cover_score']):.4f}")
        print(f"   Điểm Generated: {np.mean(metrics['val.generated_score']):.4f}")
        print(f"   Margin:         {np.mean(metrics['val.cover_score']) - np.mean(metrics['val.generated_score']):.4f}")
        
        improved = False
        
        if avg_psnr > best_psnr:
            best_psnr = avg_psnr
            improved = True
        if avg_ssim > best_ssim:
            best_ssim = avg_ssim
            improved = True
        
        if avg_decoder_acc > 0.90 and (avg_psnr > best_psnr * 0.95):
            improved = True
        
        if improved:
            best_epoch = ep + 1
            patience_counter = 0
            print(f"\nMỚI TỐT NHẤT! Epoch {best_epoch}: PSNR={best_psnr:.2f}dB, SSIM={best_ssim:.4f}, Acc={avg_decoder_acc:.2%}")
        else:
            patience_counter += 1
            print(f"\nKhông cải thiện trong {patience_counter}/{patience} epochs (Tốt nhất: Epoch {best_epoch}, PSNR={best_psnr:.2f}dB)")
        
        target_reached = False
        if avg_decoder_acc >= 0.99 and avg_psnr >= 37.0 and avg_ssim >= 0.90:
            print(f"MÔ HÌNH HOÀN HẢO - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB")
            target_reached = True
            print(f"Đã đạt 99% độ chính xác + 37 dB PSNR! Sẽ dừng sau khi lưu.")
        elif avg_decoder_acc >= 0.98 and avg_psnr >= 37.0 and avg_ssim >= 0.90:
            print(f"MÔ HÌNH XUẤT SẮC - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB")
            print(f"Rất gần mục tiêu 99%, tiếp tục để hoàn thiện...")
        elif avg_decoder_acc >= 0.95 and avg_psnr >= 35.0:
            print(f"MÔ HÌNH TỐT - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB")
            print(f"Đang trên đường đạt 99%, tiếp tục huấn luyện...")
        elif avg_decoder_acc >= 0.90:
            print(f"KHẢ - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB - Tiếp tục huấn luyện")
        else:
            print(f"YẾU - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB - Độ chính xác quá thấp!")
        
        now = datetime.datetime.now()
        name = "EN_DE_REV_ep%03d_acc%.4f_psnr%.2f_rpsnr%.2f_%s.dat" % (
            ep+1, 
            avg_decoder_acc,
            avg_psnr,
            avg_reverse_psnr,
            now.strftime("%Y%m%d_%H%M%S")
        )
        model_dir = os.path.join(os.path.dirname(__file__), 'results', 'model')
        os.makedirs(model_dir, exist_ok=True)
        fname = os.path.join(model_dir, name)
        
        states = {
            'state_dict_critic': critic.state_dict(),
            'state_dict_encoder': encoder.state_dict(),
            'state_dict_decoder': decoder.state_dict(),
            'state_dict_reverse_decoder': reverse_decoder.state_dict(),
            'en_de_optimizer': en_de_optimizer.state_dict(),
            'cr_optimizer': cr_optimizer.state_dict(),
            'scheduler_critic': scheduler_critic.state_dict(),
            'scheduler_encdec': scheduler_encdec.state_dict(),
            'metrics': metrics,
            'train_epoch': ep,
            'best_psnr': best_psnr,
            'best_ssim': best_ssim,
            'best_reverse_psnr': avg_reverse_psnr,
            'best_reverse_ssim': avg_reverse_ssim,
            'hyperparameters': {
                'weight_mse': weight_mse,
                'weight_ssim': weight_ssim,
                'weight_perceptual': weight_perceptual,
                'weight_decoder': weight_decoder,
                'weight_adversarial': weight_adversarial,
                'weight_reverse': weight_reverse,
                'use_gradient_penalty': use_gradient_penalty,
                'n_critic': n_critic,
                'hidden_size': hidden_size,
            },
            'date': now.strftime("%Y-%m-%d_%H:%M:%S"),
        }
        torch.save(states, fname)
        print(f"Đã lưu: {name}\n")
        
        plot('encoder_mse', ep, metrics['val.encoder_mse'], True)
        plot('decoder_loss', ep, metrics['val.decoder_loss'], True)
        plot('decoder_acc', ep, metrics['val.decoder_acc'], True)
        plot('ssim', ep, metrics['val.ssim'], True)
        plot('psnr', ep, metrics['val.psnr'], True)
        plot('bpp', ep, metrics['val.bpp'], True)
        plot('reverse_psnr', ep, metrics['val.reverse_psnr'], True)
        plot('reverse_ssim', ep, metrics['val.reverse_ssim'], True)
        
        scheduler_critic.step()
        scheduler_encdec.step()
        
        if target_reached and stop_on_target:
            print(f"\n{'='*70}")
            print(f"DỪNG - ĐÃ ĐẠT MỤC TIÊU tại epoch {ep+1}")
            print(f"{'='*70}")
            print(f"Chỉ số cuối cùng:")
            print(f"  Độ chính xác Decoder: {avg_decoder_acc:.2%}")
            print(f"  PSNR: {avg_psnr:.2f} dB")
            print(f"  SSIM: {avg_ssim:.4f}")
            print(f"  Reverse PSNR: {avg_reverse_psnr:.2f} dB")
            print(f"{'='*70}")
            print(f"Để huấn luyện đủ {epochs} epochs, đặt stop_on_target=False")
            print(f"{'='*70}\n")
            break
        
        if patience_counter >= patience:
            print(f"\n{'='*70}")
            print(f"DỪNG SỚM - Không cải thiện trong {patience} epochs")
            print(f"{'='*70}")
            print(f"Kết quả tốt nhất tại epoch {best_epoch}:")
            print(f"  PSNR: {best_psnr:.2f} dB")
            print(f"  SSIM: {best_ssim:.4f}")
            print(f"{'='*70}\n")
            break
        
        if device.type == 'cuda':
            torch.cuda.empty_cache()
        elif device.type == 'mps':
            torch.mps.empty_cache()
    
    print(f"\n{'='*70}")
    print(f"HOÀN THÀNH HUẤN LUYỆN!")
    print(f"{'='*70}")
    print(f"Tổng số epochs: {ep+1}")
    print(f"Epoch tốt nhất: {best_epoch}")
    print(f"PSNR tốt nhất: {best_psnr:.2f} dB")
    print(f"SSIM tốt nhất: {best_ssim:.4f}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(script_dir, 'results', 'model')
    plots_dir = os.path.join(script_dir, 'results', 'plots')
    
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    print("Đã tạo/xác minh thư mục:")
    print(f"   Model: {model_dir}")
    print(f"   Plots: {plots_dir}")
    
    main()