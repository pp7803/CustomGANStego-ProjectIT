#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Training Plots Individual Visualizer
=====================================

Tạo biểu đồ riêng biệt cho từng metric để dễ nhìn và phân tích.
Mỗi biểu đồ sẽ được save thành file riêng với kích thước lớn hơn.

Features:
- Plot từng metric ra file riêng
- Kích thước lớn, rõ ràng, dễ đọc
- Highlight best value
- Thêm annotations chi tiết
- Tự động tạo thư mục output

Usage:
    python plotsummary_individual.py
    python plotsummary_individual.py --plots-dir results/plots --output-dir summary_plots
"""

import os
import argparse
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


def parse_filename(filename):
    """Parse plot filename to extract metric info."""
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
    """Collect all metrics from plot files."""
    plots_path = Path(plots_dir)
    
    if not plots_path.exists():
        print(f"❌ Error: Directory not found: {plots_dir}")
        return {}
    
    metrics_data = defaultdict(list)
    png_files = list(plots_path.glob('*.png'))
    
    if not png_files:
        print(f"❌ Error: No PNG files found in {plots_dir}")
        return {}
    
    print(f"📊 Found {len(png_files)} plot files")
    
    parsed_count = 0
    for png_file in png_files:
        info = parse_filename(png_file.name)
        if info:
            metrics_data[info['metric']].append((info['epoch'], info['value']))
            parsed_count += 1
    
    print(f"✅ Successfully parsed {parsed_count} files")
    
    # Sort by epoch
    for metric in metrics_data:
        metrics_data[metric].sort(key=lambda x: x[0])
    
    return dict(metrics_data)


def plot_individual_metric(metric_name, data_points, config, output_dir):
    """Plot individual metric with large, clear visualization."""
    
    epochs, values = zip(*data_points)
    
    # Create figure with larger size
    plt.figure(figsize=(12, 7))
    
    # Plot main line with better styling
    plt.plot(epochs, values, 
             marker='o', 
             markersize=8,
             linewidth=3, 
             color=config['color'],
             alpha=0.8,
             label=config['ylabel'])
    
    # Add grid
    plt.grid(True, alpha=0.3, linestyle='--', linewidth=1)
    
    # Highlight best value
    if config['better'] == 'higher':
        best_idx = values.index(max(values))
        best_epoch = epochs[best_idx]
        best_val = values[best_idx]
        plt.plot(best_epoch, best_val, 'r*', markersize=20, 
                label=f'Best: {best_val:.4f}', zorder=5)
        
        # Add annotation
        plt.annotate(f'Best: {best_val:.4f}\nEpoch {best_epoch}',
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
                label=f'Best: {best_val:.4f}', zorder=5)
        
        # Add annotation
        plt.annotate(f'Best: {best_val:.4f}\nEpoch {best_epoch}',
                    xy=(best_epoch, best_val),
                    xytext=(10, -30),
                    textcoords='offset points',
                    fontsize=11,
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red'))
    
    # Labels and title with larger fonts
    plt.xlabel('Epoch', fontsize=14, fontweight='bold')
    plt.ylabel(config['ylabel'], fontsize=14, fontweight='bold')
    plt.title(f"{config['ylabel']} - Training Progress", 
             fontsize=16, fontweight='bold', pad=15)
    
    # Set y-axis limits if specified
    if config['ylim']:
        plt.ylim(config['ylim'])
    
    # Legend
    plt.legend(loc='best', fontsize=12, framealpha=0.9)
    
    # Add statistics text box
    min_val = min(values)
    max_val = max(values)
    final_val = values[-1]
    initial_val = values[0]
    mean_val = sum(values) / len(values)
    
    stats_text = f"Initial: {initial_val:.4f}\n"
    stats_text += f"Final: {final_val:.4f}\n"
    stats_text += f"Mean: {mean_val:.4f}\n"
    
    if config['better'] == 'higher':
        improvement = ((final_val - initial_val) / initial_val * 100) if initial_val != 0 else 0
        stats_text += f"Improvement: {improvement:+.2f}%"
    elif config['better'] == 'lower':
        reduction = ((initial_val - final_val) / initial_val * 100) if initial_val != 0 else 0
        stats_text += f"Reduction: {reduction:+.2f}%"
    
    # Add text box with statistics
    plt.text(0.02, 0.98, stats_text,
            transform=plt.gca().transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure
    output_path = os.path.join(output_dir, f'{metric_name}_detailed.png')
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  ✅ Saved: {output_path}")
    
    return {
        'initial': initial_val,
        'final': final_val,
        'best': best_val,
        'best_epoch': best_epoch,
        'mean': mean_val,
        'improvement': improvement if config['better'] == 'higher' else reduction
    }


def plot_all_individual(metrics_data, output_dir='summary_plots'):
    """Create individual plots for all metrics."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📁 Output directory: {output_dir}\n")
    
    # Define metric configurations
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
    
    # Plot each metric
    stats_summary = {}
    
    print("="*80)
    print("📊 Creating individual plots...")
    print("="*80 + "\n")
    
    for metric_name, data_points in metrics_data.items():
        config = metric_config.get(metric_name, {
            'ylabel': metric_name.replace('_', ' ').title(),
            'color': '#777777',
            'better': 'higher',
            'ylim': None
        })
        
        print(f"📈 Plotting: {config['ylabel']}")
        stats = plot_individual_metric(metric_name, data_points, config, output_dir)
        stats_summary[metric_name] = stats
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TRAINING RESULTS SUMMARY")
    print("="*80 + "\n")
    
    for metric_name, stats in stats_summary.items():
        config = metric_config.get(metric_name, {'ylabel': metric_name})
        print(f"{config['ylabel']:30s}")
        print(f"  Initial: {stats['initial']:12.6f}")
        print(f"  Final:   {stats['final']:12.6f}")
        print(f"  Best:    {stats['best']:12.6f} (Epoch {stats['best_epoch']})")
        print(f"  Mean:    {stats['mean']:12.6f}")
        if 'improvement' in stats:
            print(f"  Change:  {stats['improvement']:+.2f}%")
        print()
    
    print("="*80)
    print(f"✅ All plots saved to: {output_dir}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Create individual plots for each training metric",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--plots-dir',
        type=str,
        default='results/plots',
        help='Directory containing training plots (default: results/plots)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='summary_plots',
        help='Output directory for individual plots (default: summary_plots)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔍 Training Plots Individual Visualizer")
    print("="*80 + "\n")
    print(f"📂 Input:  {args.plots_dir}")
    print(f"📁 Output: {args.output_dir}\n")
    
    # Collect metrics
    metrics_data = collect_metrics(args.plots_dir)
    
    if not metrics_data:
        print("\n❌ No metrics data collected. Check your plots directory.")
        return
    
    # Plot all individual metrics
    plot_all_individual(metrics_data, args.output_dir)


if __name__ == '__main__':
    main()

