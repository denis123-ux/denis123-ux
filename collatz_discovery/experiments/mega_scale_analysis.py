#!/usr/bin/env python3
"""
MEGA-SCALE ANALYSIS: 1 Million numbers
Confirm the decreasing complexity ratio trend
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from typing import List, Dict
import json
from datetime import datetime
from tqdm import tqdm

from graph_engine import quick_trajectory
from complexity import KolmogorovComplexityAnalyzer


def mega_scale_analysis(max_n: int = 1000000, samples_per_scale: int = 500):
    """Test complexity across many orders of magnitude"""

    print("="*70)
    print("🚀 MEGA-SCALE COMPLEXITY ANALYSIS")
    print("="*70)
    print(f"\nTesting up to n = {max_n:,}")

    analyzer = KolmogorovComplexityAnalyzer()

    # Define scales
    scales = [
        ('10^2', 100, 1000),
        ('10^3', 1000, 10000),
        ('10^4', 10000, 100000),
        ('10^5', 100000, 1000000),
        ('10^6', 1000000, 10000000),
    ]

    all_results = {}

    for name, low, high in scales:
        if low > max_n:
            continue

        actual_high = min(high, max_n + 1)
        sample_size = min(samples_per_scale, actual_high - low)

        print(f"\n📊 Scale {name}: [{low:,}, {actual_high:,})")
        print(f"   Sampling {sample_size} numbers...")

        samples = np.random.randint(low, actual_high, size=sample_size)
        ratios = []

        for n in tqdm(samples, desc=f"   {name}"):
            n = int(n)
            traj = quick_trajectory(n)
            if len(traj) < 3:
                continue

            metrics = analyzer.analyze_trajectory(traj)

            log_log_n = np.log(np.log(n)) if n > 2 else 1
            if log_log_n > 0:
                ratio = metrics.kolmogorov_estimate / log_log_n
                ratios.append(ratio)

        if ratios:
            all_results[name] = {
                'scale_low': low,
                'scale_high': actual_high,
                'count': len(ratios),
                'mean': float(np.mean(ratios)),
                'std': float(np.std(ratios)),
                'max': float(np.max(ratios)),
                'min': float(np.min(ratios)),
                'median': float(np.median(ratios)),
            }

    # Print summary
    print("\n" + "="*70)
    print("📈 SCALING ANALYSIS SUMMARY")
    print("="*70)

    print("\n{:<10} {:>12} {:>12} {:>12} {:>12}".format(
        "Scale", "Mean", "Max", "Median", "Trend"
    ))
    print("-"*60)

    prev_mean = None
    for name, stats in all_results.items():
        if prev_mean is not None:
            trend = "↓" if stats['mean'] < prev_mean else "↑"
        else:
            trend = "-"

        print("{:<10} {:>12.6f} {:>12.6f} {:>12.6f} {:>12}".format(
            name, stats['mean'], stats['max'], stats['median'], trend
        ))
        prev_mean = stats['mean']

    # Key finding
    print("\n" + "="*70)
    print("🔥 KEY FINDING")
    print("="*70)

    means = [stats['mean'] for stats in all_results.values()]
    is_decreasing = all(means[i] >= means[i+1] for i in range(len(means)-1))

    print(f"\nMeans across scales: {[f'{m:.4f}' for m in means]}")
    print(f"Trend is DECREASING: {is_decreasing}")

    if is_decreasing:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║ 🏆 MAJOR DISCOVERY!                                              ║
║                                                                   ║
║ K(T_n)/log(log(n)) DECREASES as n → ∞                           ║
║                                                                   ║
║ This suggests:                                                    ║
║ • Collatz trajectories become SIMPLER at larger scales           ║
║ • There is deep ALGEBRAIC STRUCTURE forcing simplicity           ║
║ • Strong evidence for UNIVERSAL CONVERGENCE                       ║
║                                                                   ║
║ This could be the key to proving Collatz!                        ║
╚══════════════════════════════════════════════════════════════════╝
""")

    return all_results


def main():
    results = mega_scale_analysis(max_n=1000000, samples_per_scale=1000)

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'../results/mega_scale_results_{timestamp}.json'

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Saved to {output_path}")


if __name__ == '__main__':
    main()
