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
    """Plot và save metrics với improved formatting"""
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
    
    # Add moving average line
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
        # Use absolute path
        plots_dir = os.path.join(os.path.dirname(__file__), 'results', 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        plot_path = os.path.join(plots_dir, '%s_%d_%.4f_%s.png' %
                        (name, train_epoch, values[-1], now.strftime("%Y-%m-%d_%H:%M:%S")))
        get_fig.savefig(plot_path, dpi=100, bbox_inches='tight')


def compute_gradient_penalty(critic, real_data, fake_data, device):
    """
    Gradient Penalty cho WGAN-GP (thay thế weight clipping)
    Giúp training ổn định hơn và quality tốt hơn
    """
    batch_size = real_data.size(0)
    alpha = torch.rand(batch_size, 1, 1, 1, device=device)
    
    # Interpolate between real and fake
    interpolates = (alpha * real_data + (1 - alpha) * fake_data).requires_grad_(True)
    
    # Get critic scores
    d_interpolates = critic(interpolates)
    
    # Compute gradients
    gradients = torch.autograd.grad(
        outputs=d_interpolates,
        inputs=interpolates,
        grad_outputs=torch.ones_like(d_interpolates),
        create_graph=True,
        retain_graph=True,
        only_inputs=True
    )[0]
    
    # Compute gradient penalty
    gradients = gradients.view(batch_size, -1)
    gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean()
    
    return gradient_penalty


def main():
    # ========== HYPERPARAMETERS ==========
    data_dir = 'div2k'
    epochs = 60  # Giảm xuống 60 (enough với config tối ưu)
    data_depth = 2
    hidden_size = 32  # Giữ 32
    batch_size = 4  # Giữ 4
    
    # Learning rates (higher for faster learning)
    lr_critic = 2e-4      # Tăng lên 2e-4
    lr_encoder_decoder = 2e-4  # Tăng lên 2e-4 (học nhanh hơn)
    
    # Loss weights (OPTIMIZED: 99% Accuracy + 37 dB PSNR)
    # Target: Acc ≈ 99% + PSNR ≈ 37 dB
    weight_mse = 70.0            # GIẢM NHẸ (80→70) - Vẫn đủ cho PSNR 37+
    weight_ssim = 25.0           # GIẢM NHẸ (30→25) - Vẫn preserve structure
    weight_perceptual = 8.0      # GIỮ NGUYÊN - Color preservation
    weight_decoder = 25.0        # TĂNG MẠNH (15→25) - CRITICAL for 99% accuracy!
    weight_adversarial = 0.005   # GIỮ NGUYÊN (very small)
    weight_reverse = 50.0        # GIẢM NHẸ (60→50) - Trade-off for accuracy
    
    # Decoder ratio: 25/(70+25+8+25+50) = 14.0% (was 7.8%)
    # Higher decoder ratio → faster convergence to 99%
    
    # WGAN-GP parameters
    use_gradient_penalty = True  # Dùng GP thay weight clipping
    lambda_gp = 10.0            # GP coefficient
    n_critic = 2                # Giảm xuống 2 lần (nhanh hơn)
    
    # Early stopping configuration
    stop_on_target = True       # Stop immediately when target reached (save time)
    patience = 25               # Stop if no improvement for N epochs (increased for 99% target)
    min_psnr = 37.0            # Target PSNR: 37 dB (increased from 35)
    min_ssim = 0.90            # Target SSIM: 0.90
    min_decoder_acc = 0.99     # Target Accuracy: 99% (increased from 95%)
    target_psnr = 38.0         # Excellent PSNR: 38 dB (stretch goal)
    
    # Device detection
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    
    # FIX: pin_memory only for CUDA
    use_pin_memory = (device.type == 'cuda')
    
    print(f"\n{'='*70}")
    print(f"IMPROVED TRAINING CONFIGURATION")
    print(f"{'='*70}")
    print(f"Device: {device}")
    print(f"Pin Memory: {use_pin_memory}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"LR Critic: {lr_critic}")
    print(f"LR Encoder/Decoder: {lr_encoder_decoder}")
    print(f"\nLoss weights:")
    print(f"  MSE: {weight_mse}")
    print(f"  SSIM: {weight_ssim}")
    print(f"  Perceptual: {weight_perceptual}")
    print(f"  Decoder: {weight_decoder}")
    print(f"  Adversarial: {weight_adversarial}")
    print(f"  Reverse Hiding: {weight_reverse}")
    print(f"\nWGAN-GP: {use_gradient_penalty}")
    print(f"Critic iterations: {n_critic}")
    print(f"\nEarly Stopping:")
    print(f"  Stop on target: {stop_on_target}")
    print(f"  Patience: {patience} epochs")
    print(f"\nTargets:")
    print(f"  Min Decoder Accuracy: {min_decoder_acc:.1%}")
    print(f"  Min PSNR: {min_psnr:.1f} dB")
    print(f"  Min SSIM: {min_ssim:.2f}")
    print(f"  Excellent PSNR: {target_psnr:.1f} dB")
    print(f"{'='*70}\n")

    # SSIM metric
    ssim_metric = StructuralSimilarityIndexMeasure(data_range=2.0).to(device)  # [-1,1] range = 2.0

    # Perceptual loss (VGG16 features) - ENABLED for better color preservation
    use_perceptual_loss = False
    vgg = None
    try:
        print("Loading VGG16 for perceptual loss (IMPORTANT for color preservation)...")
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        from torchvision.models import VGG16_Weights
        vgg = vgg16(weights=VGG16_Weights.DEFAULT).features[:16].to(device).eval()
        for param in vgg.parameters():
            param.requires_grad = False
        use_perceptual_loss = True
        print("✅ VGG16 loaded successfully - Perceptual loss ENABLED")
    except Exception as e:
        print(f"⚠️  Warning: Could not load VGG16: {e}")
        print("   Training will continue without perceptual loss (color may shift)")
        print("   💡 Consider installing torchvision properly for best results")
        weight_perceptual = 0.0  # Disable perceptual loss

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

    # Data augmentation
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
        num_workers=0,  # Giảm xuống 0 để tránh multiprocessing issues
        pin_memory=False  # Disable pin_memory để tiết kiệm RAM
    )

    valid_set = datasets.ImageFolder(os.path.join(data_dir, "val/"), transform=transform)
    valid_loader = torch.utils.data.DataLoader(
        valid_set, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=0,  # Giảm xuống 0
        pin_memory=False  # Disable pin_memory
    )

    # ========== MODELS ==========
    # Use ResidualEncoder for better color preservation (image + delta)
    encoder = ResidualEncoder(data_depth, hidden_size).to(device)
    decoder = BasicDecoder(data_depth, hidden_size).to(device)
    reverse_decoder = ReverseDecoder(hidden_size).to(device)  # NEW: Reverse hiding
    critic = BasicCritic(hidden_size).to(device)
    
    # ========== OPTIMIZERS ==========
    cr_optimizer = Adam(critic.parameters(), lr=lr_critic, betas=(0.5, 0.999))
    en_de_optimizer = Adam(
        list(decoder.parameters()) + list(encoder.parameters()) + list(reverse_decoder.parameters()), 
        lr=lr_encoder_decoder, 
        betas=(0.5, 0.999)
    )
    
    # ========== LEARNING RATE SCHEDULERS ==========
    # Cosine annealing cho smooth decay
    scheduler_critic = CosineAnnealingLR(cr_optimizer, T_max=epochs, eta_min=1e-6)
    scheduler_encdec = CosineAnnealingLR(en_de_optimizer, T_max=epochs, eta_min=1e-6)
    
    # ========== EARLY STOPPING ==========
    best_psnr = -float('inf')  # Bắt đầu từ -inf thay vì 0.0
    best_ssim = -float('inf')  # Bắt đầu từ -inf thay vì 0.0
    best_epoch = 0
    patience_counter = 0

    # ========== TRAINING LOOP ==========
    for ep in range(epochs):
        metrics = {field: list() for field in METRIC_FIELDS}
        
        print(f"\n{'='*70}")
        print(f"Epoch {ep+1}/{epochs} | LR Critic: {cr_optimizer.param_groups[0]['lr']:.6f} | LR EncDec: {en_de_optimizer.param_groups[0]['lr']:.6f}")
        print(f"{'='*70}")
        
        # ========== PHASE 1: TRAIN CRITIC (n_critic times) ==========
        encoder.eval()  # Freeze encoder during critic training
        decoder.eval()
        reverse_decoder.eval()
        critic.train()
        
        print(f"Training Critic ({n_critic}x iterations)...")
        
        # FIX: Train critic properly - iterate through dataset n_critic times
        for _ in range(n_critic):
            for cover, _ in tqdm(train_loader, desc=f"Critic iter {_+1}/{n_critic}", leave=False):
                gc.collect()
                cover = cover.to(device)
                N, _, H, W = cover.size()
                
                # Random payload
                payload = torch.zeros((N, data_depth, H, W), device=device).random_(0, 2)
                
                # Generate stego (no gradients)
                with torch.no_grad():
                    generated = encoder(cover, payload)
                
                # Critic scores
                cover_score = critic(cover).mean()
                generated_score = critic(generated).mean()
                
                # WGAN loss
                critic_loss = generated_score - cover_score
                
                # Add gradient penalty (if enabled)
                if use_gradient_penalty:
                    gp = compute_gradient_penalty(critic, cover, generated, device)
                    critic_loss += lambda_gp * gp
                
                # Backprop
                cr_optimizer.zero_grad()
                critic_loss.backward()
                cr_optimizer.step()
                
                # Weight clipping (only if NOT using GP)
                if not use_gradient_penalty:
                    for p in critic.parameters():
                        p.data.clamp_(-0.1, 0.1)
                
                metrics['train.cover_score'].append(cover_score.item())
                metrics['train.generated_score'].append(generated_score.item())

        # ========== PHASE 2: TRAIN ENCODER-DECODER + REVERSE ==========
        encoder.train()
        decoder.train()
        reverse_decoder.train()
        critic.eval()  # Freeze critic
        
        print("Training Encoder-Decoder...")
        for cover, _ in tqdm(train_loader, desc="Encoder-Decoder", leave=False):
            gc.collect()
            cover = cover.to(device)
            N, _, H, W = cover.size()
            
            # Random payload
            payload = torch.zeros((N, data_depth, H, W), device=device).random_(0, 2)
            
            # Forward pass
            generated = encoder(cover, payload)
            decoded = decoder(generated)
            recovered_cover = reverse_decoder(generated)  # NEW: Reverse hiding
            
            # ========== COMPUTE LOSSES ==========
            # 1. Encoder MSE (image similarity)
            encoder_mse = mse_loss(generated, cover)
            
            # 2. SSIM Loss (structural similarity)
            ssim_value = ssim_metric(generated, cover)
            ssim_loss = 1.0 - ssim_value  # Convert to loss (lower is better)
            
            # 3. Perceptual Loss (VGG features) - HIGH QUALITY
            if use_perceptual_loss and vgg is not None:
                # Normalize from [-1,1] to [0,1] for VGG
                gen_normalized = (generated + 1.0) / 2.0
                cover_normalized = (cover + 1.0) / 2.0
                gen_features = vgg(gen_normalized)
                cover_features = vgg(cover_normalized)
                perceptual_loss = mse_loss(gen_features, cover_features)
            else:
                perceptual_loss = torch.tensor(0.0, device=device)
            
            # 4. Decoder loss (payload recovery)
            decoder_loss = binary_cross_entropy_with_logits(decoded, payload)
            decoder_acc = (decoded >= 0.0).eq(payload >= 0.5).sum().float() / payload.numel()
            
            # 5. Adversarial loss
            generated_score = critic(generated).mean()
            
            # 6. Reverse hiding loss
            reverse_mse = mse_loss(recovered_cover, cover)
            
            # ========== TOTAL LOSS (WEIGHTED SUM - OPTIMIZED FOR PSNR) ==========
            total_loss = (
                weight_mse * encoder_mse +              # Image quality (MSE) - HIGH
                weight_ssim * ssim_loss +                # Image quality (SSIM) - HIGH
                weight_perceptual * perceptual_loss +    # Perceptual quality - MEDIUM
                weight_decoder * decoder_loss +          # Payload recovery
                weight_adversarial * generated_score +   # Fool critic - LOW
                weight_reverse * reverse_mse             # Reverse hiding - HIGH
            )
            
            # Backprop
            en_de_optimizer.zero_grad()
            total_loss.backward()
            
            # Gradient clipping để prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(encoder.parameters(), max_norm=1.0)
            torch.nn.utils.clip_grad_norm_(decoder.parameters(), max_norm=1.0)
            torch.nn.utils.clip_grad_norm_(reverse_decoder.parameters(), max_norm=1.0)
            
            en_de_optimizer.step()
            
            # Track metrics
            metrics['train.encoder_mse'].append(encoder_mse.item())
            metrics['train.decoder_loss'].append(decoder_loss.item())
            metrics['train.decoder_acc'].append(decoder_acc.item())
            metrics['train.ssim_loss'].append(ssim_loss.item())
            metrics['train.perceptual_loss'].append(perceptual_loss.item())
            metrics['train.reverse_mse'].append(reverse_mse.item())
            metrics['train.total_loss'].append(total_loss.item())

        # ========== PHASE 3: VALIDATION ==========
        encoder.eval()
        decoder.eval()
        reverse_decoder.eval()
        critic.eval()
        
        print("Validating...")
        with torch.no_grad():
            for cover, _ in tqdm(valid_loader, desc="Validation", leave=False):
                gc.collect()
                cover = cover.to(device)
                N, _, H, W = cover.size()
                
                payload = torch.zeros((N, data_depth, H, W), device=device).random_(0, 2)
                
                generated = encoder(cover, payload)
                decoded = decoder(generated)
                recovered_cover = reverse_decoder(generated)  # NEW
                
                encoder_mse = mse_loss(generated, cover)
                decoder_loss = binary_cross_entropy_with_logits(decoded, payload)
                decoder_acc = (decoded >= 0.0).eq(payload >= 0.5).sum().float() / payload.numel()
                generated_score = critic(generated).mean()
                cover_score = critic(cover).mean()
                
                # Reverse hiding metrics (NEW)
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
        
        # ========== COMPUTE EPOCH AVERAGES ==========
        avg_psnr = np.mean(metrics['val.psnr'])
        avg_ssim = np.mean(metrics['val.ssim'])
        avg_decoder_acc = np.mean(metrics['val.decoder_acc'])
        avg_bpp = np.mean(metrics['val.bpp'])
        avg_reverse_psnr = np.mean(metrics['val.reverse_psnr'])
        avg_reverse_ssim = np.mean(metrics['val.reverse_ssim'])
        
        # ========== PRINT SUMMARY ==========
        print(f"\n{'─'*70}")
        print(f"Epoch {ep+1} Summary:")
        print(f"{'─'*70}")
        print(f"📊 Decoder Performance:")
        print(f"   Train Accuracy: {np.mean(metrics['train.decoder_acc']):.4f}")
        print(f"   Val   Accuracy: {avg_decoder_acc:.4f}")
        print(f"   Train Loss:     {np.mean(metrics['train.decoder_loss']):.6f}")
        print(f"   Val   Loss:     {np.mean(metrics['val.decoder_loss']):.6f}")
        print(f"\n🖼️  Image Quality (Stego):")
        print(f"   Train MSE:  {np.mean(metrics['train.encoder_mse']):.6f}")
        print(f"   Val   MSE:  {np.mean(metrics['val.encoder_mse']):.6f}")
        print(f"   Val   SSIM: {avg_ssim:.4f} {'✅' if avg_ssim > min_ssim else '❌'}")
        print(f"   Val   PSNR: {avg_psnr:.2f} dB {'✅' if avg_psnr > min_psnr else '❌'}")
        print(f"\n🔄 Reverse Hiding (Cover Recovery):")
        print(f"   Train MSE:  {np.mean(metrics['train.reverse_mse']):.6f}")
        print(f"   Val   MSE:  {np.mean(metrics['val.reverse_mse']):.6f}")
        print(f"   Val   SSIM: {avg_reverse_ssim:.4f}")
        print(f"   Val   PSNR: {avg_reverse_psnr:.2f} dB")
        print(f"\n💾 Capacity:")
        print(f"   Val BPP: {avg_bpp:.4f}")
        print(f"\n🎭 Adversarial:")
        print(f"   Cover Score:     {np.mean(metrics['val.cover_score']):.4f}")
        print(f"   Generated Score: {np.mean(metrics['val.generated_score']):.4f}")
        print(f"   Margin:          {np.mean(metrics['val.cover_score']) - np.mean(metrics['val.generated_score']):.4f}")
        
        # ========== EARLY STOPPING CHECK ==========
        improved = False
        
        # Track best metrics (regardless of thresholds)
        if avg_psnr > best_psnr:
            best_psnr = avg_psnr
            improved = True
        if avg_ssim > best_ssim:
            best_ssim = avg_ssim
            improved = True
        
        # Bonus: also consider decoder accuracy improvement
        if avg_decoder_acc > 0.90 and (avg_psnr > best_psnr * 0.95):
            improved = True
        
        if improved:
            best_epoch = ep + 1
            patience_counter = 0
            print(f"\n✅ NEW BEST! Epoch {best_epoch}: PSNR={best_psnr:.2f}dB, SSIM={best_ssim:.4f}, Acc={avg_decoder_acc:.2%}")
        else:
            patience_counter += 1
            print(f"\n⏳ No improvement for {patience_counter}/{patience} epochs (Best: Epoch {best_epoch}, PSNR={best_psnr:.2f}dB)")
        
        # Quality assessment (focus on 99% accuracy + 37 dB PSNR)
        target_reached = False
        if avg_decoder_acc >= 0.99 and avg_psnr >= 37.0 and avg_ssim >= 0.90:
            print(f"🎉🎉🎉 PERFECT MODEL - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB")
            target_reached = True
            print(f"🏁 99% accuracy + 37 dB PSNR achieved! Will stop after saving.")
        elif avg_decoder_acc >= 0.98 and avg_psnr >= 37.0 and avg_ssim >= 0.90:
            print(f"🎉 EXCELLENT MODEL - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB")
            print(f"💡 Very close to 99% target, continue for perfection...")
        elif avg_decoder_acc >= 0.95 and avg_psnr >= 35.0:
            print(f"✅ GOOD MODEL - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB")
            print(f"💡 On track to 99%, keep training...")
        elif avg_decoder_acc >= 0.90:
            print(f"⚠️  FAIR - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB - Continue training")
        else:
            print(f"❌ POOR - Acc={avg_decoder_acc:.2%}, PSNR={avg_psnr:.1f}dB - Accuracy too low!")
        
        # ========== SAVE CHECKPOINT ==========
        now = datetime.datetime.now()
        name = "EN_DE_REV_ep%03d_acc%.4f_psnr%.2f_rpsnr%.2f_%s.dat" % (
            ep+1, 
            avg_decoder_acc,
            avg_psnr,
            avg_reverse_psnr,
            now.strftime("%Y%m%d_%H%M%S")
        )
        # Use absolute path to avoid working directory issues
        model_dir = os.path.join(os.path.dirname(__file__), 'results', 'model')
        os.makedirs(model_dir, exist_ok=True)  # Ensure directory exists
        fname = os.path.join(model_dir, name)
        
        states = {
            'state_dict_critic': critic.state_dict(),
            'state_dict_encoder': encoder.state_dict(),
            'state_dict_decoder': decoder.state_dict(),
            'state_dict_reverse_decoder': reverse_decoder.state_dict(),  # NEW
            'en_de_optimizer': en_de_optimizer.state_dict(),
            'cr_optimizer': cr_optimizer.state_dict(),
            'scheduler_critic': scheduler_critic.state_dict(),
            'scheduler_encdec': scheduler_encdec.state_dict(),
            'metrics': metrics,
            'train_epoch': ep,
            'best_psnr': best_psnr,
            'best_ssim': best_ssim,
            'best_reverse_psnr': avg_reverse_psnr,  # NEW
            'best_reverse_ssim': avg_reverse_ssim,  # NEW
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
        print(f"💾 Saved: {name}\n")
        
        # ========== PLOT METRICS ==========
        plot('encoder_mse', ep, metrics['val.encoder_mse'], True)
        plot('decoder_loss', ep, metrics['val.decoder_loss'], True)
        plot('decoder_acc', ep, metrics['val.decoder_acc'], True)
        plot('ssim', ep, metrics['val.ssim'], True)
        plot('psnr', ep, metrics['val.psnr'], True)
        plot('bpp', ep, metrics['val.bpp'], True)
        plot('reverse_psnr', ep, metrics['val.reverse_psnr'], True)
        plot('reverse_ssim', ep, metrics['val.reverse_ssim'], True)
        
        # ========== UPDATE LEARNING RATE ==========
        scheduler_critic.step()
        scheduler_encdec.step()
        
        # ========== EARLY STOPPING ==========
        # Stop if target reached (if enabled)
        if target_reached and stop_on_target:
            print(f"\n{'='*70}")
            print(f"🏁 STOPPING - TARGET REACHED at epoch {ep+1}")
            print(f"{'='*70}")
            print(f"Final metrics:")
            print(f"  Decoder Accuracy: {avg_decoder_acc:.2%}")
            print(f"  PSNR: {avg_psnr:.2f} dB")
            print(f"  SSIM: {avg_ssim:.4f}")
            print(f"  Reverse PSNR: {avg_reverse_psnr:.2f} dB")
            print(f"{'='*70}")
            print(f"💡 To train full {epochs} epochs, set stop_on_target=False")
            print(f"{'='*70}\n")
            break
        
        # Stop if no improvement for patience epochs
        if patience_counter >= patience:
            print(f"\n{'='*70}")
            print(f"⏹️  EARLY STOPPING - No improvement for {patience} epochs")
            print(f"{'='*70}")
            print(f"Best results at epoch {best_epoch}:")
            print(f"  PSNR: {best_psnr:.2f} dB")
            print(f"  SSIM: {best_ssim:.4f}")
            print(f"{'='*70}\n")
            break
        
        # Memory cleanup
        if device.type == 'cuda':
            torch.cuda.empty_cache()
        elif device.type == 'mps':
            torch.mps.empty_cache()
    
    print(f"\n{'='*70}")
    print(f"✅ TRAINING COMPLETE!")
    print(f"{'='*70}")
    print(f"Total epochs: {ep+1}")
    print(f"Best epoch: {best_epoch}")
    print(f"Best PSNR: {best_psnr:.2f} dB")
    print(f"Best SSIM: {best_ssim:.4f}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    # Create directories with absolute path (avoid working directory issues)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(script_dir, 'results', 'model')
    plots_dir = os.path.join(script_dir, 'results', 'plots')
    
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    print("✅ Directories created/verified:")
    print(f"   Model: {model_dir}")
    print(f"   Plots: {plots_dir}")
    
    main()