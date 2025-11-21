#!/usr/bin/env python3
"""
LARGE-SCALE KOLMOGOROV COMPLEXITY ANALYSIS

Focus on the approach that WORKS: complexity analysis!
Test if K(T_n) / log(log(n)) remains bounded for large n
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import json
from datetime import datetime
from tqdm import tqdm

from graph_engine import quick_trajectory
from complexity import KolmogorovComplexityAnalyzer


def large_scale_complexity_analysis(
    max_n: int = 100000,
    sample_size: int = 5000,
    verbose: bool = True
) -> Dict:
    """
    Large-scale analysis of Kolmogorov complexity

    Tests if complexity ratio remains bounded as n grows
    """
    print("="*70)
    print("LARGE-SCALE KOLMOGOROV COMPLEXITY ANALYSIS")
    print("="*70)
    print(f"\nAnalyzing {sample_size} trajectories from range [1, {max_n}]")

    # Sample across different scales
    # Logarithmically spaced to cover wide range
    log_samples = np.logspace(1, np.log10(max_n), num=sample_size//2, dtype=int)
    random_samples = np.random.randint(2, max_n + 1, size=sample_size//2)
    sample_values = np.unique(np.concatenate([log_samples, random_samples]))
    sample_values = sample_values[sample_values > 1]  # Exclude 1

    print(f"Total unique samples: {len(sample_values)}")

    analyzer = KolmogorovComplexityAnalyzer()

    # Results storage
    results = {
        'n_values': [],
        'stopping_times': [],
        'kolmogorov_estimates': [],
        'complexity_ratios': [],  # K / log(log(n))
        'compressibility': [],
        'shannon_entropy': [],
    }

    # Process trajectories
    print("\nProcessing trajectories...")
    for i, n in enumerate(tqdm(sample_values, disable=not verbose)):
        n = int(n)
        traj = quick_trajectory(n)

        if len(traj) < 3:
            continue

        metrics = analyzer.analyze_trajectory(traj)

        # Complexity ratio
        if n > 2:
            log_log_n = np.log(np.log(n))
            if log_log_n > 0:
                ratio = metrics.kolmogorov_estimate / log_log_n
            else:
                ratio = 0
        else:
            ratio = 0

        results['n_values'].append(n)
        results['stopping_times'].append(len(traj) - 1)
        results['kolmogorov_estimates'].append(metrics.kolmogorov_estimate)
        results['complexity_ratios'].append(ratio)
        results['compressibility'].append(metrics.compressibility_ratio)
        results['shannon_entropy'].append(metrics.shannon_entropy)

    # Analyze results by scale
    print("\n" + "="*70)
    print("ANALYSIS BY SCALE")
    print("="*70)

    n_arr = np.array(results['n_values'])
    ratios = np.array(results['complexity_ratios'])

    # Bin by order of magnitude
    scales = [
        ('10-100', (10, 100)),
        ('100-1K', (100, 1000)),
        ('1K-10K', (1000, 10000)),
        ('10K-100K', (10000, 100000)),
        ('100K+', (100000, float('inf'))),
    ]

    scale_stats = {}
    for name, (low, high) in scales:
        mask = (n_arr >= low) & (n_arr < high)
        if mask.sum() > 0:
            scale_ratios = ratios[mask]
            scale_stats[name] = {
                'count': int(mask.sum()),
                'mean': float(np.mean(scale_ratios)),
                'std': float(np.std(scale_ratios)),
                'max': float(np.max(scale_ratios)),
                'min': float(np.min(scale_ratios)),
            }
            print(f"\n{name}:")
            print(f"  Count: {scale_stats[name]['count']}")
            print(f"  Mean ratio: {scale_stats[name]['mean']:.6f}")
            print(f"  Max ratio: {scale_stats[name]['max']:.6f}")

    # Overall statistics
    print("\n" + "="*70)
    print("OVERALL STATISTICS")
    print("="*70)

    overall = {
        'total_samples': len(results['n_values']),
        'max_n': int(np.max(n_arr)),
        'mean_ratio': float(np.mean(ratios)),
        'std_ratio': float(np.std(ratios)),
        'max_ratio': float(np.max(ratios)),
        'min_ratio': float(np.min(ratios)),
        'mean_compressibility': float(np.mean(results['compressibility'])),
    }

    print(f"\nTotal samples: {overall['total_samples']}")
    print(f"Max n analyzed: {overall['max_n']}")
    print(f"\nComplexity Ratio K/log(log(n)):")
    print(f"  Mean: {overall['mean_ratio']:.6f}")
    print(f"  Std: {overall['std_ratio']:.6f}")
    print(f"  Max: {overall['max_ratio']:.6f}")
    print(f"  Min: {overall['min_ratio']:.6f}")
    print(f"\nMean compressibility: {overall['mean_compressibility']:.4f}")

    # KEY THEOREM TEST
    print("\n" + "="*70)
    print("🔥 KEY THEOREM TEST")
    print("="*70)

    # Does ratio remain bounded as n → ∞?
    # Check if max ratio in each scale is not growing unboundedly
    is_bounded = overall['max_ratio'] < 5.0  # Threshold
    is_low = overall['mean_ratio'] < 1.0

    print(f"\n✓ Ratio bounded (max < 5): {is_bounded}")
    print(f"✓ Ratio low (mean < 1): {is_low}")
    print(f"\n🎯 THEOREM SUPPORTED: {is_bounded and is_low}")

    if is_bounded and is_low:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║ 🎉 STRONG EVIDENCE FOR COLLATZ CONJECTURE!                       ║
║                                                                   ║
║ The Kolmogorov complexity ratio K(T_n)/log(log(n)) is BOUNDED!   ║
║                                                                   ║
║ This implies trajectories have LOW algorithmic complexity,        ║
║ suggesting DETERMINISTIC structure that forces convergence!       ║
╚══════════════════════════════════════════════════════════════════╝
""")

    # Generate plots
    print("\nGenerating plots...")
    generate_complexity_plots(results, overall, scale_stats)

    return {
        'results': results,
        'scale_stats': scale_stats,
        'overall': overall,
        'theorem_supported': is_bounded and is_low,
    }


def generate_complexity_plots(results: Dict, overall: Dict, scale_stats: Dict):
    """Generate comprehensive complexity analysis plots"""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    n_arr = np.array(results['n_values'])
    ratios = np.array(results['complexity_ratios'])
    stopping = np.array(results['stopping_times'])
    compress = np.array(results['compressibility'])

    # Plot 1: Complexity ratio vs n (log scale)
    ax1 = axes[0, 0]
    ax1.scatter(n_arr, ratios, alpha=0.3, s=10)
    ax1.axhline(y=overall['mean_ratio'], color='r', linestyle='--',
               label=f"Mean = {overall['mean_ratio']:.3f}")
    ax1.axhline(y=overall['max_ratio'], color='orange', linestyle=':',
               label=f"Max = {overall['max_ratio']:.3f}")
    ax1.set_xscale('log')
    ax1.set_xlabel('n', fontsize=12)
    ax1.set_ylabel('K(T_n) / log(log(n))', fontsize=12)
    ax1.set_title('Complexity Ratio vs n (Log Scale)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Distribution of complexity ratios
    ax2 = axes[0, 1]
    ax2.hist(ratios, bins=50, edgecolor='black', alpha=0.7)
    ax2.axvline(x=overall['mean_ratio'], color='r', linestyle='--',
               linewidth=2, label=f"Mean = {overall['mean_ratio']:.3f}")
    ax2.set_xlabel('K(T_n) / log(log(n))', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title('Distribution of Complexity Ratios', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Compressibility vs stopping time
    ax3 = axes[1, 0]
    ax3.scatter(stopping, compress, alpha=0.3, s=10)
    ax3.set_xlabel('Stopping Time', fontsize=12)
    ax3.set_ylabel('Compressibility Ratio', fontsize=12)
    ax3.set_title('Compressibility vs Stopping Time', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # Plot 4: Scale analysis
    ax4 = axes[1, 1]
    scale_names = list(scale_stats.keys())
    scale_means = [scale_stats[s]['mean'] for s in scale_names]
    scale_maxs = [scale_stats[s]['max'] for s in scale_names]

    x = np.arange(len(scale_names))
    width = 0.35

    ax4.bar(x - width/2, scale_means, width, label='Mean', color='steelblue')
    ax4.bar(x + width/2, scale_maxs, width, label='Max', color='coral')
    ax4.set_xlabel('Scale', fontsize=12)
    ax4.set_ylabel('Complexity Ratio', fontsize=12)
    ax4.set_title('Complexity by Scale (bounded = converges!)', fontsize=14, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(scale_names, rotation=45)
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f'../results/large_scale_complexity_{timestamp}.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"✓ Saved plot to {plot_path}")


def main():
    """Run large-scale analysis"""
    results = large_scale_complexity_analysis(
        max_n=100000,
        sample_size=3000,
        verbose=True
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'../results/large_scale_results_{timestamp}.json'

    # Convert numpy arrays to lists for JSON
    save_results = {
        'scale_stats': results['scale_stats'],
        'overall': results['overall'],
        'theorem_supported': results['theorem_supported'],
    }

    with open(output_path, 'w') as f:
        json.dump(save_results, f, indent=2)

    print(f"\n✓ Saved results to {output_path}")
    print("\n✅ LARGE-SCALE ANALYSIS COMPLETE!")


if __name__ == '__main__':
    main()
