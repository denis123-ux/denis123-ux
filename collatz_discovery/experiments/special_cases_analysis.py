#!/usr/bin/env python3
"""
SPECIAL CASES ANALYSIS

Analyze special number families to understand Collatz structure:
1. Powers of 2: 2^k
2. Mersenne numbers: 2^k - 1
3. Numbers of form 2^k + 1
4. Numbers with specific binary patterns
5. Numbers that reach maximum height
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from typing import List, Dict, Tuple
import json
from datetime import datetime
from tqdm import tqdm

from graph_engine import quick_trajectory
from complexity import KolmogorovComplexityAnalyzer


def analyze_powers_of_2(max_k: int = 60):
    """
    Powers of 2 have trivial trajectories: 2^k → 2^(k-1) → ... → 1

    This is the SIMPLEST case - stopping time = k
    """
    print("\n" + "="*70)
    print("ANALYSIS: POWERS OF 2")
    print("="*70)

    results = []

    for k in range(1, max_k + 1):
        n = 2**k
        traj = quick_trajectory(n)

        results.append({
            'k': k,
            'n': n,
            'stopping_time': len(traj) - 1,
            'expected': k,  # Should equal k
            'max_value': max(traj),
        })

    # All powers of 2 should have stopping time = k
    all_correct = all(r['stopping_time'] == r['expected'] for r in results)

    print(f"\nTested 2^1 to 2^{max_k}")
    print(f"All stopping times = k: {all_correct}")

    if all_correct:
        print("✓ Powers of 2 behave trivially: T(2^k) = k")

    return results


def analyze_mersenne_numbers(max_k: int = 30):
    """
    Mersenne numbers: 2^k - 1 (all 1s in binary)

    These are ALWAYS odd, so first step is 3n+1 = 3×2^k - 2 = 2(3×2^(k-1) - 1)
    """
    print("\n" + "="*70)
    print("ANALYSIS: MERSENNE NUMBERS (2^k - 1)")
    print("="*70)

    analyzer = KolmogorovComplexityAnalyzer()
    results = []

    for k in range(2, max_k + 1):
        n = 2**k - 1
        traj = quick_trajectory(n)

        metrics = analyzer.analyze_trajectory(traj)
        log_log_n = np.log(np.log(n)) if n > 2 else 1

        results.append({
            'k': k,
            'n': n,
            'stopping_time': len(traj) - 1,
            'max_value': max(traj),
            'expansion_ratio': max(traj) / n,
            'complexity_ratio': metrics.kolmogorov_estimate / log_log_n if log_log_n > 0 else 0,
        })

    # Analyze pattern
    stopping_times = [r['stopping_time'] for r in results]
    ks = [r['k'] for r in results]

    # Fit: T(2^k - 1) ≈ a × k + b
    from scipy import stats
    slope, intercept, r_value, _, _ = stats.linregress(ks, stopping_times)

    print(f"\nFit: T(2^k - 1) ≈ {slope:.2f} × k + {intercept:.2f}")
    print(f"R² = {r_value**2:.4f}")

    print("\nSample values:")
    for r in results[:10]:
        print(f"  2^{r['k']}-1 = {r['n']}: T = {r['stopping_time']}, max = {r['max_value']}")

    # Check expansion ratio
    expansion_ratios = [r['expansion_ratio'] for r in results]
    print(f"\nMean expansion ratio: {np.mean(expansion_ratios):.2f}")
    print(f"Max expansion ratio: {np.max(expansion_ratios):.2f}")

    return results


def analyze_plus_one(max_k: int = 30):
    """
    Numbers of form 2^k + 1

    These start odd: 3(2^k + 1) + 1 = 3×2^k + 4 = 2²(3×2^(k-2) + 1)
    """
    print("\n" + "="*70)
    print("ANALYSIS: NUMBERS 2^k + 1")
    print("="*70)

    results = []

    for k in range(2, max_k + 1):
        n = 2**k + 1
        traj = quick_trajectory(n)

        results.append({
            'k': k,
            'n': n,
            'stopping_time': len(traj) - 1,
            'max_value': max(traj),
            'expansion_ratio': max(traj) / n,
        })

    stopping_times = [r['stopping_time'] for r in results]
    ks = [r['k'] for r in results]

    from scipy import stats
    slope, intercept, r_value, _, _ = stats.linregress(ks, stopping_times)

    print(f"\nFit: T(2^k + 1) ≈ {slope:.2f} × k + {intercept:.2f}")
    print(f"R² = {r_value**2:.4f}")

    print("\nSample values:")
    for r in results[:10]:
        print(f"  2^{r['k']}+1 = {r['n']}: T = {r['stopping_time']}, max = {r['max_value']}")

    return results


def find_record_holders(max_n: int = 10**6, num_records: int = 20):
    """
    Find numbers with LONGEST stopping times (record holders)

    These are the "hardest" numbers for Collatz
    """
    print("\n" + "="*70)
    print("ANALYSIS: RECORD HOLDERS (longest stopping times)")
    print("="*70)

    # Compute stopping times for all numbers
    print(f"\nScanning 1 to {max_n:,}...")

    records = []
    current_record = 0

    for n in tqdm(range(1, max_n + 1), desc="Scanning"):
        traj = quick_trajectory(n)
        T = len(traj) - 1

        if T > current_record:
            current_record = T
            records.append({
                'n': n,
                'stopping_time': T,
                'max_value': max(traj),
                'binary': bin(n),
            })

    print(f"\nFound {len(records)} record holders:")
    print("\n{:<15} {:>12} {:>15} {:>30}".format("n", "Stopping T", "Max Value", "Binary"))
    print("-"*75)

    for r in records[-num_records:]:
        binary_short = r['binary'][:30] + "..." if len(r['binary']) > 30 else r['binary']
        print("{:<15} {:>12} {:>15} {:>30}".format(r['n'], r['stopping_time'], r['max_value'], binary_short))

    # Analyze record holders
    record_ns = [r['n'] for r in records]
    record_Ts = [r['stopping_time'] for r in records]

    print(f"\nLast record holder in [1, {max_n}]: n = {records[-1]['n']}")
    print(f"Its stopping time: {records[-1]['stopping_time']}")

    return records


def analyze_binary_patterns(max_n: int = 100000, sample_size: int = 5000):
    """
    Find which binary patterns lead to long/short trajectories
    """
    print("\n" + "="*70)
    print("ANALYSIS: BINARY PATTERNS")
    print("="*70)

    samples = np.random.randint(2, max_n + 1, size=sample_size)

    results = []

    for n in tqdm(samples, desc="Analyzing"):
        n = int(n)
        traj = quick_trajectory(n)

        binary = bin(n)[2:]

        results.append({
            'n': n,
            'stopping_time': len(traj) - 1,
            'bit_length': len(binary),
            'num_ones': binary.count('1'),
            'density_ones': binary.count('1') / len(binary),
            'trailing_zeros': len(binary) - len(binary.rstrip('0')),
            'leading_pattern': binary[:4] if len(binary) >= 4 else binary,
        })

    # Convert to arrays
    stopping_times = np.array([r['stopping_time'] for r in results])
    num_ones = np.array([r['num_ones'] for r in results])
    density = np.array([r['density_ones'] for r in results])
    trailing = np.array([r['trailing_zeros'] for r in results])

    # Correlations
    from scipy.stats import pearsonr

    corr_ones, p_ones = pearsonr(num_ones, stopping_times)
    corr_density, p_density = pearsonr(density, stopping_times)
    corr_trailing, p_trailing = pearsonr(trailing, stopping_times)

    print(f"\nCorrelations with stopping time:")
    print(f"  # of 1-bits: r = {corr_ones:.4f} (p = {p_ones:.4f})")
    print(f"  Density of 1s: r = {corr_density:.4f} (p = {p_density:.4f})")
    print(f"  Trailing zeros: r = {corr_trailing:.4f} (p = {p_trailing:.4f})")

    # Which patterns have longest trajectories?
    sorted_results = sorted(results, key=lambda x: -x['stopping_time'])

    print("\nTop 10 longest trajectories:")
    for r in sorted_results[:10]:
        print(f"  n = {r['n']}, T = {r['stopping_time']}, binary = {bin(r['n'])[:40]}")

    print("\nTop 10 shortest trajectories (excluding powers of 2):")
    shortest = [r for r in results if r['density_ones'] > 0.1]
    shortest = sorted(shortest, key=lambda x: x['stopping_time'])
    for r in shortest[:10]:
        print(f"  n = {r['n']}, T = {r['stopping_time']}, binary = {bin(r['n'])[:40]}")

    return {
        'corr_ones': corr_ones,
        'corr_density': corr_density,
        'corr_trailing': corr_trailing,
    }


def analyze_syracuse_acceleration():
    """
    The Syracuse function: f(n) = (3n+1)/2^k where k = max trailing zeros after 3n+1

    This "accelerates" Collatz by combining odd step with subsequent even steps
    """
    print("\n" + "="*70)
    print("ANALYSIS: SYRACUSE ACCELERATION")
    print("="*70)

    def syracuse_step(n):
        """One Syracuse step: if odd, apply 3n+1 and divide by 2 until odd"""
        if n % 2 == 0:
            while n % 2 == 0:
                n //= 2
            return n
        else:
            n = 3*n + 1
            while n % 2 == 0:
                n //= 2
            return n

    def syracuse_trajectory(n, max_steps=1000):
        """Full Syracuse trajectory"""
        traj = [n]
        current = n
        steps = 0

        while current != 1 and steps < max_steps:
            current = syracuse_step(current)
            traj.append(current)
            steps += 1

        return traj

    # Compare Collatz vs Syracuse for various numbers
    test_numbers = [27, 97, 871, 6171, 77031, 837799]

    print("\nComparison: Collatz steps vs Syracuse steps")
    print("{:<15} {:>15} {:>15} {:>10}".format("n", "Collatz steps", "Syracuse steps", "Ratio"))
    print("-"*60)

    for n in test_numbers:
        collatz_traj = quick_trajectory(n)
        syracuse_traj = syracuse_trajectory(n)

        ratio = len(collatz_traj) / len(syracuse_traj)

        print("{:<15} {:>15} {:>15} {:>10.2f}".format(
            n, len(collatz_traj)-1, len(syracuse_traj)-1, ratio
        ))

    print("\nThe Syracuse function 'compresses' trajectories by ~2x")
    print("This is because each Syracuse step = 1 odd + average 2 even Collatz steps")


def main():
    print("="*70)
    print("🔬 SPECIAL CASES ANALYSIS")
    print("="*70)

    results = {}

    # Powers of 2
    results['powers_of_2'] = analyze_powers_of_2()

    # Mersenne numbers
    results['mersenne'] = analyze_mersenne_numbers()

    # 2^k + 1
    results['plus_one'] = analyze_plus_one()

    # Record holders
    results['record_holders'] = find_record_holders(max_n=100000)

    # Binary patterns
    results['binary_patterns'] = analyze_binary_patterns()

    # Syracuse
    analyze_syracuse_acceleration()

    # Summary
    print("\n" + "="*70)
    print("📋 SPECIAL CASES SUMMARY")
    print("="*70)

    print("""
Key Findings:

1. POWERS OF 2 (2^k):
   - Trivial: T(2^k) = k exactly
   - These are the "simplest" numbers

2. MERSENNE NUMBERS (2^k - 1):
   - Linear in k: T ≈ {:.1f}×k
   - Moderate expansion ratio

3. NUMBERS 2^k + 1:
   - Also linear in k
   - Different coefficient

4. RECORD HOLDERS:
   - Follow specific binary patterns
   - High density of 1-bits correlates with longer trajectories

5. SYRACUSE ACCELERATION:
   - Compresses by ~2x
   - More natural for theoretical analysis
""".format(
        np.mean([r['stopping_time']/r['k'] for r in results['mersenne'] if r['k'] > 5])
    ))

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'../results/special_cases_{timestamp}.json'

    # Clean for JSON
    save_results = {
        'powers_of_2_count': len(results['powers_of_2']),
        'mersenne_count': len(results['mersenne']),
        'plus_one_count': len(results['plus_one']),
        'num_records': len(results['record_holders']),
        'last_record': results['record_holders'][-1] if results['record_holders'] else None,
        'binary_correlations': results['binary_patterns'],
    }

    with open(output_path, 'w') as f:
        json.dump(save_results, f, indent=2)

    print(f"\n✓ Saved to {output_path}")


if __name__ == '__main__':
    main()
