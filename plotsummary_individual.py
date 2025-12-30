"""
Công Cụ Hiển Thị Biểu Đồ Huấn Luyện Riêng Biệt
=====================================

Tạo biểu đồ riêng biệt cho từng chỉ số để dễ nhìn và phân tích.
Mỗi biểu đồ sẽ được lưu thành file riêng với kích thước lớn hơn.

Tính năng:
- Vẽ từng chễ số ra file riêng
- Kích thước lớn, rõ ràng, dễ đọc
- Nổi bật giá trị tốt nhất
- Thêm chú thích chi tiết
- Tự động tạo thư mục đầu ra

Cách dùng:
    python plotsummary_individual.py
    python plotsummary_individual.py --plots-dir results/plots --output-dir summary_plots
"""

import os
import argparse
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def parse_filename(filename):
    """Phân tích tên file biểu đồ để trích xuất thông tin chỉ số."""
    name = filename.replace('.png', '')
    parts = name.split('_')
    
    if len(parts) < 5:
        return None
    
    try:
        time_part = parts[-1]
        date_part = parts[-2]
        value_part = parts[-3]
        epoch_part = parts[-4]
        metric_parts = parts[:-4]
        
        epoch = int(epoch_part)
        value = float(value_part)
        metric = '_'.join(metric_parts)
        timestamp = f"{date_part}_{time_part}"
        
        return {
            'metric': metric,
            'epoch': epoch,
            'value': value,
            'timestamp': timestamp,
            'filename': filename
        }
    except (ValueError, IndexError):
        return None


def collect_metrics(plots_dir):
    """Thu thập tất cả các chỉ số từ các file biểu đồ."""
    plots_path = Path(plots_dir)
    
    if not plots_path.exists():
        print(f"Lỗi: Không tìm thấy thư mục: {plots_dir}")
        return {}
    
    metrics_data = defaultdict(list)
    png_files = list(plots_path.glob('*.png'))
    
    if not png_files:
        print(f"Lỗi: Không tìm thấy file PNG nào trong {plots_dir}")
        return {}
    
    print(f"Đã tìm thấy {len(png_files)} file biểu đồ")
    
    parsed_count = 0
    for png_file in png_files:
        info = parse_filename(png_file.name)
        if info:
            metrics_data[info['metric']].append((info['epoch'], info['value']))
            parsed_count += 1
    
    print(f"Đã phân tích thành công {parsed_count} file")
    
    for metric in metrics_data:
        metrics_data[metric].sort(key=lambda x: x[0])
    
    return dict(metrics_data)


def plot_individual_metric(metric_name, data_points, config, output_dir):
    """Vẽ biểu đồ riêng biệt cho chỉ số với hiển thị rõ ràng và lớn."""
    
    epochs, values = zip(*data_points)
    
    plt.figure(figsize=(12, 7))
    
    plt.plot(epochs, values, 
             marker='o', 
             markersize=8,
             linewidth=3, 
             color=config['color'],
             alpha=0.8,
             label=config['ylabel'])
    
    plt.grid(True, alpha=0.3, linestyle='--', linewidth=1)
    
    if config['better'] == 'higher':
        best_idx = values.index(max(values))
        best_epoch = epochs[best_idx]
        best_val = values[best_idx]
        plt.plot(best_epoch, best_val, 'r*', markersize=20, 
                label=f'Tốt nhất: {best_val:.4f}', zorder=5)
        
        plt.annotate(f'Tốt nhất: {best_val:.4f}\nEpoch {best_epoch}',
                    xy=(best_epoch, best_val),
                    xytext=(10, 20),
                    textcoords='offset points',
                    fontsize=11,
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red'))
        
    elif config['better'] == 'lower':
        best_idx = values.index(min(values))
        best_epoch = epochs[best_idx]
        best_val = values[best_idx]
        plt.plot(best_epoch, best_val, 'r*', markersize=20,
                label=f'Tốt nhất: {best_val:.4f}', zorder=5)
        
        plt.annotate(f'Tốt nhất: {best_val:.4f}\nEpoch {best_epoch}',
                    xy=(best_epoch, best_val),
                    xytext=(10, -30),
                    textcoords='offset points',
                    fontsize=11,
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red'))
    
    plt.xlabel('Epoch', fontsize=14, fontweight='bold')
    plt.ylabel(config['ylabel'], fontsize=14, fontweight='bold')
    plt.title(f"{config['ylabel']} - Tiến trình huấn luyện", 
             fontsize=16, fontweight='bold', pad=15)
    
    if config['ylim']:
        plt.ylim(config['ylim'])
    
    plt.legend(loc='best', fontsize=12, framealpha=0.9)
    
    min_val = min(values)
    max_val = max(values)
    final_val = values[-1]
    initial_val = values[0]
    mean_val = sum(values) / len(values)
    
    stats_text = f"Ban đầu: {initial_val:.4f}\n"
    stats_text += f"Cuối cùng: {final_val:.4f}\n"
    stats_text += f"Trung bình: {mean_val:.4f}\n"
    
    if config['better'] == 'higher':
        improvement = ((final_val - initial_val) / initial_val * 100) if initial_val != 0 else 0
        stats_text += f"Cải thiện: {improvement:+.2f}%"
    elif config['better'] == 'lower':
        reduction = ((initial_val - final_val) / initial_val * 100) if initial_val != 0 else 0
        stats_text += f"Giảm: {reduction:+.2f}%"
    
    plt.text(0.02, 0.98, stats_text,
            transform=plt.gca().transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, f'{metric_name}_detailed.png')
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Đã lưu: {output_path}")
    
    return {
        'initial': initial_val,
        'final': final_val,
        'best': best_val,
        'best_epoch': best_epoch,
        'mean': mean_val,
        'improvement': improvement if config['better'] == 'higher' else reduction
    }


def plot_all_individual(metrics_data, output_dir='summary_plots'):
    """Tạo biểu đồ riêng biệt cho tất cả các chỉ số."""
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nOutput directory: {output_dir}\n")
    
    metric_config = {
        'decoder_acc': {
            'ylabel': 'Decoder Accuracy',
            'color': '#2E86AB',
            'better': 'higher',
            'ylim': [0, 1.05]
        },
        'psnr': {
            'ylabel': 'PSNR (dB)',
            'color': '#A23B72',
            'better': 'higher',
            'ylim': None
        },
        'ssim': {
            'ylabel': 'SSIM',
            'color': '#F18F01',
            'better': 'higher',
            'ylim': [0, 1.05]
        },
        'reverse_psnr': {
            'ylabel': 'Reverse PSNR (dB)',
            'color': '#C73E1D',
            'better': 'higher',
            'ylim': None
        },
        'reverse_ssim': {
            'ylabel': 'Reverse SSIM',
            'color': '#6A994E',
            'better': 'higher',
            'ylim': [0, 1.05]
        },
        'encoder_mse': {
            'ylabel': 'Encoder MSE',
            'color': '#BC4B51',
            'better': 'lower',
            'ylim': None
        },
        'decoder_loss': {
            'ylabel': 'Decoder Loss',
            'color': '#8B5A3C',
            'better': 'lower',
            'ylim': None
        },
        'bpp': {
            'ylabel': 'Bits Per Pixel',
            'color': '#5E548E',
            'better': 'higher',
            'ylim': None
        }
    }
    
    stats_summary = {}
    
    print("="*80)
    print("Đang tạo các biểu đồ riêng biệt...")
    print("="*80 + "\n")
    
    for metric_name, data_points in metrics_data.items():
        config = metric_config.get(metric_name, {
            'ylabel': metric_name.replace('_', ' ').title(),
            'color': '#777777',
            'better': 'higher',
            'ylim': None
        })
        
        print(f"Đang vẽ: {config['ylabel']}")
        stats = plot_individual_metric(metric_name, data_points, config, output_dir)
        stats_summary[metric_name] = stats
    
    print("\n" + "="*80)
    print("TỔNG KẾT KẾT QUẢ HUẤN LUYỆN")
    print("="*80 + "\n")
    
    for metric_name, stats in stats_summary.items():
        config = metric_config.get(metric_name, {'ylabel': metric_name})
        print(f"{config['ylabel']:30s}")
        print(f"  Ban đầu: {stats['initial']:12.6f}")
        print(f"  Cuối:     {stats['final']:12.6f}")
        print(f"  Tốt nhất: {stats['best']:12.6f} (Epoch {stats['best_epoch']})")
        print(f"  TB:       {stats['mean']:12.6f}")
        if 'improvement' in stats:
            print(f"  Thay đổi: {stats['improvement']:+.2f}%")
        print()
    
    print("="*80)
    print(f"Tất cả biểu đồ đã lưu vào: {output_dir}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Tạo biểu đồ riêng biệt cho từng chỉ số huấn luyện",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--plots-dir',
        type=str,
        default='results/plots',
        help='Thư mục chứa các biểu đồ huấn luyện (mặc định: results/plots)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='summary_plots',
        help='Thư mục đầu ra cho các biểu đồ riêng (mặc định: summary_plots)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("Công Cụ Hiển Thị Biểu Đồ Huấn Luyện Riêng Biệt")
    print("="*80 + "\n")
    print(f"Đầu vào:  {args.plots_dir}")
    print(f"Đầu ra: {args.output_dir}\n")
    
    metrics_data = collect_metrics(args.plots_dir)
    
    if not metrics_data:
        print("\nKhông thu thập được dữ liệu chỉ số. Kiểm tra thư mục biểu đồ của bạn.")
        return
    
    plot_all_individual(metrics_data, args.output_dir)


if __name__ == '__main__':
    main()

