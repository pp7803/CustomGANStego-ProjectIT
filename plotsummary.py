#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Công Cụ Hiển Thị Tổng Hợp Biểu Đồ Huấn Luyện
==================================

Đọc và tổng hợp tất cả các biểu đồ huấn luyện từ thư mục results/plots/
để tạo phân tích trực quan toàn diện của quá trình huấn luyện.

Tính năng:
- Tự động phân tích tên file để trích xuất chỉ số
- Nhóm chỉ số theo epoch
- Vẽ tất cả chỉ số trong 1 hình với các biểu đồ con
- Bao gồm các chỉ số reverse hiding (reverse_psnr, reverse_ssim)
- Lưu phân tích tổng hợp
- In thống kê huấn luyện

Định dạng file mong đợi:
    {tên_chỉ_số}_{epoch}_{giá_trị}_{thời_gian}.png
    
Ví dụ tên file:
    - decoder_acc_0_0.7163_2025-12-11_06:18:25.png
    - psnr_0_22.4346_2025-12-11_06:18:25.png
    - reverse_psnr_0_23.3474_2025-12-11_06:18:26.png
"""

import os
import re
import argparse
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def parse_filename(filename):
    """
    Phân tích tên file biểu đồ để trích xuất thông tin chỉ số.
    
    Định dạng: {chỉ_số}_{epoch}_{giá_trị}_{thời_gian}.png
    Ví dụ: decoder_acc_0_0.7163_2025-12-11_06:18:25.png
    
    Trả về:
        dict với các khóa: metric, epoch, value, timestamp
        hoặc None nếu phân tích thất bại
    """
    name = filename.replace('.png', '')
    
    parts = name.split('_')
    
    if len(parts) < 5:
        return None
    
    try:
        if len(parts) < 5:
            return None
        
        time_part = parts[-1]  # HH:MM:SS
        date_part = parts[-2]  # YYYY-MM-DD
        value_part = parts[-3]  # float value
        epoch_part = parts[-4]  # epoch number
        metric_parts = parts[:-4]  # metric name (may have underscores)
        
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
    """
    Thu thập tất cả các chỉ số từ các file biểu đồ.
    
    Trả về:
        dict: {tên_chỉ_số: [(epoch, giá_trị), ...]}
    """
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
    failed_files = []
    for png_file in png_files:
        info = parse_filename(png_file.name)
        if info:
            metrics_data[info['metric']].append((info['epoch'], info['value']))
            parsed_count += 1
        else:
            failed_files.append(png_file.name)
    
    print(f"Đã phân tích thành công {parsed_count} file")
    if failed_files:
        print(f"Không phân tích được {len(failed_files)} file")
    
    for metric in metrics_data:
        metrics_data[metric].sort(key=lambda x: x[0])
    
    return dict(metrics_data)


def plot_summary(metrics_data, output_file='summary_plots/training_summary.png'):
    """
    Tạo biểu đồ tổng hợp toàn diện với tất cả các chỉ số.
    """
    if not metrics_data:
        print("Không có dữ liệu để vẽ")
        return
    
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
    
    priority_order = [
        'decoder_acc', 'psnr', 'ssim', 
        'reverse_psnr', 'reverse_ssim',
        'encoder_mse', 'decoder_loss', 'bpp'
    ]
    available_metrics = [m for m in priority_order if m in metrics_data]
    
    for m in metrics_data.keys():
        if m not in available_metrics:
            available_metrics.append(m)
            metric_config[m] = {
                'ylabel': m.replace('_', ' ').title(),
                'color': '#777777',
                'better': 'neutral',
                'ylim': None
            }
    
    if not available_metrics:
        print("Không tìm thấy chỉ số nào")
        return
    
    n_metrics = len(available_metrics)
    n_cols = 4
    n_rows = (n_metrics + n_cols - 1) // n_cols
    
    fig = plt.figure(figsize=(20, 4 * n_rows))
    gs = gridspec.GridSpec(n_rows, n_cols, figure=fig, hspace=0.3, wspace=0.25)
    
    print(f"\n{'='*80}")
    print(f"Tổng Hợp Các Chỉ Số Huấn Luyện")
    print(f"{'='*80}\n")
    
    for idx, metric in enumerate(available_metrics):
        row = idx // n_cols
        col = idx % n_cols
        ax = fig.add_subplot(gs[row, col])
        
        epochs, values = zip(*metrics_data[metric])
        config = metric_config.get(metric, {
            'ylabel': metric.replace('_', ' ').title(),
            'color': '#777777',
            'better': 'neutral',
            'ylim': None
        })
        
        ax.plot(epochs, values, 
                marker='o', 
                markersize=3,
                linewidth=2, 
                color=config['color'],
                label=metric,
                alpha=0.8)
        
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        ax.set_xlabel('Epoch', fontsize=10, fontweight='bold')
        ax.set_ylabel(config['ylabel'], fontsize=10, fontweight='bold')
        ax.set_title(f"{config['ylabel']}", fontsize=11, fontweight='bold', pad=10)
        
        if config['ylim']:
            ax.set_ylim(config['ylim'])
        
        if config['better'] == 'higher':
            best_idx = values.index(max(values))
            best_epoch = epochs[best_idx]
            best_val = values[best_idx]
            ax.plot(best_epoch, best_val, 'r*', markersize=12, 
                   label=f'Tốt nhất: {best_val:.4f}', zorder=5)
        elif config['better'] == 'lower':
            best_idx = values.index(min(values))
            best_epoch = epochs[best_idx]
            best_val = values[best_idx]
            ax.plot(best_epoch, best_val, 'r*', markersize=12,
                   label=f'Tốt nhất: {best_val:.4f}', zorder=5)
        
        ax.legend(loc='best', fontsize=8, framealpha=0.9)
        
        # Tính toán các giá trị thống kê
        initial_val = values[0]
        final_val = values[-1]
        max_val = max(values)
        min_val = min(values)
        mean_val = sum(values) / len(values)
        
        print(f"{config['ylabel']:30s}")
        print(f"  Ban đầu (epoch {epochs[0]:3d}):  {initial_val:12.6f}")
        print(f"  Cuối    (epoch {epochs[-1]:3d}):  {final_val:12.6f}")
        
        if config['better'] == 'higher':
            best_val = max_val
            best_epoch = epochs[values.index(best_val)]
            improvement = ((final_val - initial_val) / initial_val * 100) if initial_val != 0 else 0
            print(f"  Tốt nhất (epoch {best_epoch:3d}):  {best_val:12.6f}")
            print(f"  Trung bình:                {mean_val:12.6f}")
            print(f"  Cải thiện:                {improvement:+.2f}%")
        elif config['better'] == 'lower':
            best_val = min_val
            best_epoch = epochs[values.index(best_val)]
            reduction = ((initial_val - final_val) / initial_val * 100) if initial_val != 0 else 0
            print(f"  Tốt nhất (epoch {best_epoch:3d}):  {best_val:12.6f}")
            print(f"  Trung bình:                {mean_val:12.6f}")
            print(f"  Giảm:                      {reduction:+.2f}%")
        else:
            print(f"  Trung bình:                {mean_val:12.6f}")
            print(f"  Khoảng:                    [{min_val:.6f}, {max_val:.6f}]")
        print()
    
    # Overall title
    all_epochs_list = []
    for data_points in metrics_data.values():
        for epoch, _ in data_points:
            all_epochs_list.append(epoch)
    total_epochs = max(all_epochs_list) if all_epochs_list else 0
    
    fig.suptitle(f'Tổng Hợp Tiến Trình Huấn Luyện - Tất Cả Chỉ Số (Tổng: {total_epochs + 1} epochs)', 
                 fontsize=16, 
                 fontweight='bold',
                 y=0.998)
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"{'='*80}")
    print(f"Biểu đồ tổng hợp đã lưu vào: {output_file}")
    print(f"{'='*80}\n")
    
    plt.show()


def print_epoch_summary(metrics_data):
    """In tổng hợp các epoch khả dụng và chỉ số theo epoch."""
    if not metrics_data:
        return
    
    all_epochs = set()
    for metric_values in metrics_data.values():
        all_epochs.update(epoch for epoch, _ in metric_values)
    
    all_epochs = sorted(all_epochs)
    
    print(f"\n{'='*80}")
    print(f"Tổng Hợp Dữ Liệu")
    print(f"{'='*80}\n")
    print(f"Tổng số chỉ số: {len(metrics_data)}")
    print(f"Tổng số epoch:  {len(all_epochs)}")
    print(f"Khoảng epoch:   {min(all_epochs)} → {max(all_epochs)}\n")
    
    print(f"Các chỉ số khả dụng:")
    for metric, values in sorted(metrics_data.items()):
        print(f"  • {metric:20s} : {len(values):3d} điểm dữ liệu")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Hiển thị tiến trình huấn luyện từ thư mục biểu đồ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python plotsummary.py
  python plotsummary.py --plots-dir results/plots --output summary.png
        """
    )
    parser.add_argument(
        '--plots-dir',
        type=str,
        default='results/plots',
        help='Thư mục chứa các biểu đồ huấn luyện (mặc định: results/plots)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='summary_plots/training_summary.png',
        help='Tên file đầu ra cho biểu đồ tổng hợp (mặc định: training_summary.png)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("Công Cụ Tổng Hợp Biểu Đồ Huấn Luyện")
    print("="*80 + "\n")
    print(f"Đang đọc từ: {args.plots_dir}")
    print(f"File đầu ra:  {args.output}\n")
    
    metrics_data = collect_metrics(args.plots_dir)
    
    if not metrics_data:
        print("\nKhông thu thập được dữ liệu chỉ số. Kiểm tra thư mục biểu đồ của bạn.")
        return
    
    print_epoch_summary(metrics_data)
    
    plot_summary(metrics_data, args.output)


if __name__ == '__main__':
    main()
