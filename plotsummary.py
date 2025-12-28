#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Training Plots Summary Visualizer
==================================

Đọc và tổng hợp tất cả training plots từ thư mục results/plots/
để tạo comprehensive visualization của quá trình training.

Features:
- Tự động parse filenames để extract metrics
- Group metrics theo epoch
- Plot tất cả metrics trong 1 figure với subplots
- Bao gồm reverse hiding metrics (reverse_psnr, reverse_ssim)
- Save summary visualization
- Print training statistics

File Format Expected:
    {metric_name}_{epoch}_{value}_{timestamp}.png
    
Example filenames:
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
    Parse plot filename to extract metric info.
    
    Format: {metric}_{epoch}_{value}_{timestamp}.png
    Example: decoder_acc_0_0.7163_2025-12-11_06:18:25.png
    
    Returns:
        dict with keys: metric, epoch, value, timestamp
        or None if parsing fails
    """
    # Remove .png extension
    name = filename.replace('.png', '')
    
    # Split by underscore
    parts = name.split('_')
    
    if len(parts) < 5:  # metric_epoch_value_date_time (min 5 parts)
        return None
    
    try:
        # The pattern is: {metric}_{epoch}_{value}_{YYYY-MM-DD}_{HH:MM:SS}
        # Example: bpp_0_0.8651_2025-12-11_06:18:25
        # Example: decoder_acc_0_0.7163_2025-12-11_06:18:25
        # Example: reverse_psnr_0_23.3474_2025-12-11_06:18:26
        
        # Strategy: Work backwards from the end
        # Last 2 parts are always date and time
        # Before that is the value (float)
        # Before that is the epoch (int)
        # Everything before that is the metric name
        
        if len(parts) < 5:
            return None
        
        # Extract from the end
        time_part = parts[-1]  # HH:MM:SS
        date_part = parts[-2]  # YYYY-MM-DD
        value_part = parts[-3]  # float value
        epoch_part = parts[-4]  # epoch number
        metric_parts = parts[:-4]  # metric name (may have underscores)
        
        # Parse values
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
    Collect all metrics from plot files.
    
    Returns:
        dict: {metric_name: [(epoch, value), ...]}
    """
    plots_path = Path(plots_dir)
    
    if not plots_path.exists():
        print(f"❌ Error: Directory not found: {plots_dir}")
        return {}
    
    metrics_data = defaultdict(list)
    
    # Get all PNG files
    png_files = list(plots_path.glob('*.png'))
    
    if not png_files:
        print(f"❌ Error: No PNG files found in {plots_dir}")
        return {}
    
    print(f"📊 Found {len(png_files)} plot files")
    
    # Parse each file
    parsed_count = 0
    failed_files = []
    for png_file in png_files:
        info = parse_filename(png_file.name)
        if info:
            metrics_data[info['metric']].append((info['epoch'], info['value']))
            parsed_count += 1
        else:
            failed_files.append(png_file.name)
    
    print(f"✅ Successfully parsed {parsed_count} files")
    if failed_files:
        print(f"⚠️  Failed to parse {len(failed_files)} files")
    
    # Sort by epoch
    for metric in metrics_data:
        metrics_data[metric].sort(key=lambda x: x[0])
    
    return dict(metrics_data)


def plot_summary(metrics_data, output_file='summary_plots/training_summary.png'):
    """
    Create comprehensive summary plot with all metrics.
    """
    if not metrics_data:
        print("❌ No data to plot")
        return
    
    # Define metric groups and their properties
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
    
    # Filter metrics that we have data for and order them
    priority_order = [
        'decoder_acc', 'psnr', 'ssim', 
        'reverse_psnr', 'reverse_ssim',
        'encoder_mse', 'decoder_loss', 'bpp'
    ]
    available_metrics = [m for m in priority_order if m in metrics_data]
    
    # Add any other metrics not in priority list
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
        print("❌ No recognized metrics found")
        return
    
    # Create figure with subplots (4 columns for better layout)
    n_metrics = len(available_metrics)
    n_cols = 4
    n_rows = (n_metrics + n_cols - 1) // n_cols
    
    fig = plt.figure(figsize=(20, 4 * n_rows))
    gs = gridspec.GridSpec(n_rows, n_cols, figure=fig, hspace=0.3, wspace=0.25)
    
    print(f"\n{'='*80}")
    print(f"📈 Training Metrics Summary")
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
        
        # Plot with markers
        ax.plot(epochs, values, 
                marker='o', 
                markersize=3,
                linewidth=2, 
                color=config['color'],
                label=metric,
                alpha=0.8)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Labels and title
        ax.set_xlabel('Epoch', fontsize=10, fontweight='bold')
        ax.set_ylabel(config['ylabel'], fontsize=10, fontweight='bold')
        ax.set_title(f"{config['ylabel']}", fontsize=11, fontweight='bold', pad=10)
        
        # Set y-axis limits if specified
        if config['ylim']:
            ax.set_ylim(config['ylim'])
        
        # Highlight best value
        if config['better'] == 'higher':
            best_idx = values.index(max(values))
            best_epoch = epochs[best_idx]
            best_val = values[best_idx]
            ax.plot(best_epoch, best_val, 'r*', markersize=12, 
                   label=f'Best: {best_val:.4f}', zorder=5)
        elif config['better'] == 'lower':
            best_idx = values.index(min(values))
            best_epoch = epochs[best_idx]
            best_val = values[best_idx]
            ax.plot(best_epoch, best_val, 'r*', markersize=12,
                   label=f'Best: {best_val:.4f}', zorder=5)
        
        ax.legend(loc='best', fontsize=8, framealpha=0.9)
        
        # Print statistics
        min_val = min(values)
        max_val = max(values)
        final_val = values[-1]
        initial_val = values[0]
        mean_val = sum(values) / len(values)
        
        print(f"{config['ylabel']:30s}")
        print(f"  Initial (epoch {epochs[0]:3d}):  {initial_val:12.6f}")
        print(f"  Final   (epoch {epochs[-1]:3d}):  {final_val:12.6f}")
        
        if config['better'] == 'higher':
            best_val = max_val
            best_epoch = epochs[values.index(best_val)]
            improvement = ((final_val - initial_val) / initial_val * 100) if initial_val != 0 else 0
            print(f"  Best    (epoch {best_epoch:3d}):  {best_val:12.6f} ⭐")
            print(f"  Mean:                    {mean_val:12.6f}")
            print(f"  Improvement:             {improvement:+.2f}%")
        elif config['better'] == 'lower':
            best_val = min_val
            best_epoch = epochs[values.index(best_val)]
            reduction = ((initial_val - final_val) / initial_val * 100) if initial_val != 0 else 0
            print(f"  Best    (epoch {best_epoch:3d}):  {best_val:12.6f} ⭐")
            print(f"  Mean:                    {mean_val:12.6f}")
            print(f"  Reduction:               {reduction:+.2f}%")
        else:
            print(f"  Mean:                    {mean_val:12.6f}")
            print(f"  Range:                   [{min_val:.6f}, {max_val:.6f}]")
        print()
    
    # Overall title
    all_epochs_list = []
    for data_points in metrics_data.values():
        for epoch, _ in data_points:
            all_epochs_list.append(epoch)
    total_epochs = max(all_epochs_list) if all_epochs_list else 0
    
    fig.suptitle(f'Training Progress Summary - All Metrics (Total: {total_epochs + 1} epochs)', 
                 fontsize=16, 
                 fontweight='bold',
                 y=0.998)
    
    # Save figure
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"{'='*80}")
    print(f"✅ Summary plot saved to: {output_file}")
    print(f"{'='*80}\n")
    
    # Show plot
    plt.show()


def print_epoch_summary(metrics_data):
    """Print summary of available epochs and metrics per epoch."""
    if not metrics_data:
        return
    
    # Get all epochs across all metrics
    all_epochs = set()
    for metric_values in metrics_data.values():
        all_epochs.update(epoch for epoch, _ in metric_values)
    
    all_epochs = sorted(all_epochs)
    
    print(f"\n{'='*80}")
    print(f"📊 Dataset Summary")
    print(f"{'='*80}\n")
    print(f"Total Metrics: {len(metrics_data)}")
    print(f"Total Epochs:  {len(all_epochs)}")
    print(f"Epoch Range:   {min(all_epochs)} → {max(all_epochs)}\n")
    
    print(f"Available Metrics:")
    for metric, values in sorted(metrics_data.items()):
        print(f"  • {metric:20s} : {len(values):3d} data points")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize training progress from plots directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python plotsummary.py
  python plotsummary.py --plots-dir results/plots --output summary.png
        """
    )
    parser.add_argument(
        '--plots-dir',
        type=str,
        default='results/plots',
        help='Directory containing training plots (default: results/plots)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='summary_plots/training_summary.png',
        help='Output filename for summary plot (default: training_summary.png)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔍 Training Plots Summary Tool")
    print("="*80 + "\n")
    print(f"📂 Reading from: {args.plots_dir}")
    print(f"💾 Output file:  {args.output}\n")
    
    # Collect metrics
    metrics_data = collect_metrics(args.plots_dir)
    
    if not metrics_data:
        print("\n❌ No metrics data collected. Check your plots directory.")
        return
    
    # Print summary
    print_epoch_summary(metrics_data)
    
    # Plot summary
    plot_summary(metrics_data, args.output)


if __name__ == '__main__':
    main()
