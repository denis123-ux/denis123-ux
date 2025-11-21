#!/usr/bin/env python3
"""
ASYMPTOTIC ANALYSIS

Study the precise asymptotic behavior of:
1. Odd/Even ratio as n → ∞
2. Complexity ratio as n → ∞
3. Derive theoretical formulas
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from typing import List, Dict, Tuple
import json
from datetime import datetime
from tqdm import tqdm

from graph_engine import quick_trajectory
from complexity import KolmogorovComplexityAnalyzer


def study_odd_even_convergence(max_n: int = 10**9, num_samples: int = 2000):
    """
    Study how O/E ratio converges as n → ∞

    Key question: Does ratio converge to log(4)/log(3) ≈ 1.26?
    (This is the theoretical value if Collatz behaves like random walk)
    """
    print("\n" + "="*70)
    print("ODD/EVEN RATIO ASYMPTOTIC ANALYSIS")
    print("="*70)

    # Theoretical prediction from random walk model
    # If each bit is random, P(odd) = 1/2
    # But after 3n+1, always even, so:
    # Expected O/E = 1/E[consecutive evens after odd]
    # E[consecutive evens] = sum_{k=1}^∞ k × P(k trailing zeros) = 2
    # So O/E ≈ 1/2 in naive model

    # More refined: ln(2)/ln(3) ≈ 0.63 from density arguments
    theoretical_ratio = np.log(2) / np.log(3)

    print(f"\nTheoretical prediction (ln(2)/ln(3)): {theoretical_ratio:.6f}")

    # Sample across wide range
    log_samples = np.logspace(2, np.log10(max_n), num=num_samples)
    samples = log_samples.astype(int)
    samples = np.unique(samples)

    results = []

    for n in tqdm(samples, desc="Analyzing"):
        n = int(n)
        traj = quick_trajectory(n)

        odd = sum(1 for x in traj[:-1] if x % 2 == 1)
        even = len(traj) - 1 - odd

        if even > 0:
            results.append({
                'n': n,
                'log_n': np.log(n),
                'ratio': odd / even,
                'stopping_time': len(traj) - 1,
            })

    # Convert to arrays
    log_n = np.array([r['log_n'] for r in results])
    ratios = np.array([r['ratio'] for r in results])

    # Fit: ratio = a + b/log(n) + c/log²(n)
    def asymptotic_fit(x, a, b, c):
        return a + b/x + c/x**2

    try:
        popt, pcov = curve_fit(asymptotic_fit, log_n, ratios, p0=[0.5, 0, 0])
        limit_estimate = popt[0]
        fit_quality = 1 - np.var(ratios - asymptotic_fit(log_n, *popt)) / np.var(ratios)
    except:
        popt = [np.mean(ratios), 0, 0]
        limit_estimate = popt[0]
        fit_quality = 0

    print(f"\nAsymptotic fit: ratio = {popt[0]:.6f} + {popt[1]:.4f}/log(n) + {popt[2]:.4f}/log²(n)")
    print(f"Fit R² = {fit_quality:.4f}")
    print(f"\nEstimated limit as n → ∞: {limit_estimate:.6f}")
    print(f"Theoretical (ln(2)/ln(3)): {theoretical_ratio:.6f}")
    print(f"Difference: {abs(limit_estimate - theoretical_ratio):.6f}")

    # Check if converging to theoretical value
    close_to_theory = abs(limit_estimate - theoretical_ratio) < 0.1

    print(f"\n✓ Close to theoretical ln(2)/ln(3): {close_to_theory}")

    return {
        'limit_estimate': limit_estimate,
        'theoretical': theoretical_ratio,
        'fit_params': popt.tolist(),
        'fit_r2': fit_quality,
    }


def derive_stopping_time_formula(max_n: int = 10**8, num_samples: int = 2000):
    """
    Derive formula for expected stopping time

    Theoretical: E[T_n] ≈ c × log(n) for some constant c
    """
    print("\n" + "="*70)
    print("STOPPING TIME FORMULA DERIVATION")
    print("="*70)

    log_samples = np.logspace(2, np.log10(max_n), num=num_samples)
    samples = log_samples.astype(int)
    samples = np.unique(samples)

    results = []

    for n in tqdm(samples, desc="Computing"):
        n = int(n)
        traj = quick_trajectory(n)
        results.append({
            'n': n,
            'log_n': np.log(n),
            'T': len(traj) - 1,
        })

    log_n = np.array([r['log_n'] for r in results])
    T = np.array([r['T'] for r in results])

    # Linear fit: T = a × log(n) + b
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_n, T)

    print(f"\nLinear fit: T = {slope:.4f} × log(n) + {intercept:.4f}")
    print(f"R² = {r_value**2:.4f}")

    # Theoretical prediction: c = 1 / ln(decay_factor)
    # decay_factor ≈ 0.888, so c ≈ 1/0.1186 ≈ 8.4
    theoretical_c = 1 / 0.1186

    print(f"\nEmpirical constant c = {slope:.4f}")
    print(f"Theoretical (1/decay_rate) = {theoretical_c:.4f}")

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'theoretical_c': theoretical_c,
    }


def derive_complexity_formula(max_n: int = 10**8, num_samples: int = 1500):
    """
    Derive precise formula for K(T_n) / log(log(n))

    Test multiple functional forms:
    1. ratio = L (constant)
    2. ratio = a + b/log(n)
    3. ratio = a + b/log(n) + c/log²(n)
    4. ratio = a × log(n)^(-α) + L
    """
    print("\n" + "="*70)
    print("COMPLEXITY FORMULA DERIVATION")
    print("="*70)

    analyzer = KolmogorovComplexityAnalyzer()

    log_samples = np.logspace(3, np.log10(max_n), num=num_samples)
    samples = log_samples.astype(int)
    samples = np.unique(samples)

    results = []

    for n in tqdm(samples, desc="Analyzing"):
        n = int(n)
        traj = quick_trajectory(n)

        if len(traj) < 3:
            continue

        metrics = analyzer.analyze_trajectory(traj)
        log_log_n = np.log(np.log(n))

        if log_log_n > 0:
            results.append({
                'n': n,
                'log_n': np.log(n),
                'log_log_n': log_log_n,
                'K': metrics.kolmogorov_estimate,
                'ratio': metrics.kolmogorov_estimate / log_log_n,
            })

    log_n = np.array([r['log_n'] for r in results])
    ratios = np.array([r['ratio'] for r in results])

    # Model 1: Constant
    model1_L = np.mean(ratios)
    model1_sse = np.sum((ratios - model1_L)**2)

    # Model 2: a + b/log(n)
    slope2, intercept2, _, _, _ = stats.linregress(1/log_n, ratios)
    model2_pred = intercept2 + slope2 / log_n
    model2_sse = np.sum((ratios - model2_pred)**2)

    # Model 3: a + b/log(n) + c/log²(n)
    X3 = np.column_stack([np.ones_like(log_n), 1/log_n, 1/log_n**2])
    coeffs3, _, _, _ = np.linalg.lstsq(X3, ratios, rcond=None)
    model3_pred = coeffs3[0] + coeffs3[1]/log_n + coeffs3[2]/log_n**2
    model3_sse = np.sum((ratios - model3_pred)**2)

    # Model 4: a × log(n)^(-α) + L (power law decay to limit)
    def power_decay(x, a, alpha, L):
        return a * x**(-alpha) + L

    try:
        popt4, _ = curve_fit(power_decay, log_n, ratios, p0=[1, 0.5, 0.1], maxfev=5000)
        model4_pred = power_decay(log_n, *popt4)
        model4_sse = np.sum((ratios - model4_pred)**2)
    except:
        popt4 = [0, 0, np.mean(ratios)]
        model4_sse = model1_sse

    print("\nModel Comparison:")
    print("-"*60)
    print(f"Model 1 (constant L = {model1_L:.4f}): SSE = {model1_sse:.4f}")
    print(f"Model 2 (a + b/log(n)): SSE = {model2_sse:.4f}")
    print(f"         a = {intercept2:.4f}, b = {slope2:.4f}")
    print(f"Model 3 (a + b/log(n) + c/log²(n)): SSE = {model3_sse:.4f}")
    print(f"         a = {coeffs3[0]:.4f}, b = {coeffs3[1]:.4f}, c = {coeffs3[2]:.4f}")
    print(f"Model 4 (a×log(n)^(-α) + L): SSE = {model4_sse:.4f}")
    print(f"         a = {popt4[0]:.4f}, α = {popt4[1]:.4f}, L = {popt4[2]:.4f}")

    # Best model
    sses = [model1_sse, model2_sse, model3_sse, model4_sse]
    best_idx = np.argmin(sses)
    models = ["Constant", "Linear in 1/log(n)", "Quadratic in 1/log(n)", "Power law decay"]

    print(f"\nBest model: {models[best_idx]}")

    # Final limit estimate
    limits = [model1_L, intercept2, coeffs3[0], popt4[2]]
    best_limit = limits[best_idx]

    print(f"\n🎯 FINAL COMPLEXITY FORMULA:")
    if best_idx == 0:
        print(f"   K(T_n) / log(log(n)) ≈ {best_limit:.4f}")
    elif best_idx == 1:
        print(f"   K(T_n) / log(log(n)) ≈ {intercept2:.4f} + {slope2:.4f}/log(n)")
    elif best_idx == 2:
        print(f"   K(T_n) / log(log(n)) ≈ {coeffs3[0]:.4f} + {coeffs3[1]:.4f}/log(n) + {coeffs3[2]:.4f}/log²(n)")
    else:
        print(f"   K(T_n) / log(log(n)) ≈ {popt4[0]:.4f} × log(n)^(-{popt4[1]:.4f}) + {popt4[2]:.4f}")

    print(f"\n   As n → ∞: K(T_n) / log(log(n)) → {best_limit:.4f}")

    return {
        'model_sses': sses,
        'best_model': models[best_idx],
        'limit_estimate': best_limit,
        'model2_params': {'a': intercept2, 'b': slope2},
        'model3_params': {'a': coeffs3[0], 'b': coeffs3[1], 'c': coeffs3[2]},
        'model4_params': {'a': popt4[0], 'alpha': popt4[1], 'L': popt4[2]},
    }


def main():
    print("="*70)
    print("🔬 ASYMPTOTIC ANALYSIS - DERIVING EXACT FORMULAS")
    print("="*70)

    results = {}

    # Study O/E ratio convergence
    print("\n" + "▓"*70)
    results['odd_even'] = study_odd_even_convergence(max_n=10**9, num_samples=1500)

    # Derive stopping time formula
    print("\n" + "▓"*70)
    results['stopping_time'] = derive_stopping_time_formula(max_n=10**8, num_samples=1500)

    # Derive complexity formula
    print("\n" + "▓"*70)
    results['complexity'] = derive_complexity_formula(max_n=10**8, num_samples=1500)

    # FINAL SUMMARY
    print("\n" + "="*70)
    print("📋 ASYMPTOTIC FORMULAS SUMMARY")
    print("="*70)

    print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│ ASYMPTOTIC FORMULAS FOR COLLATZ CONJECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 1. ODD/EVEN RATIO:                                                  │
│    lim(n→∞) [#odd / #even] = {results['odd_even']['limit_estimate']:.4f}                              │
│    Theoretical (ln2/ln3) = {results['odd_even']['theoretical']:.4f}                              │
│                                                                     │
│ 2. STOPPING TIME:                                                   │
│    E[T_n] ≈ {results['stopping_time']['slope']:.2f} × log(n) + {results['stopping_time']['intercept']:.2f}                             │
│    R² = {results['stopping_time']['r_squared']:.4f}                                                  │
│                                                                     │
│ 3. COMPLEXITY RATIO:                                                │
│    Best model: {results['complexity']['best_model']:<40}  │
│    K(T_n) / log(log(n)) → {results['complexity']['limit_estimate']:.4f} as n → ∞                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
    """)

    # Check consistency
    print("\n" + "="*70)
    print("🔍 CONSISTENCY CHECK")
    print("="*70)

    # From O/E ratio, compute decay factor
    c = results['odd_even']['limit_estimate']
    p_odd = c / (1 + c)
    decay_factor = (3 ** p_odd) * (0.5 ** (1 - p_odd))
    decay_rate = -np.log(decay_factor)

    print(f"\nFrom O/E ratio {c:.4f}:")
    print(f"  Decay factor = {decay_factor:.4f}")
    print(f"  Decay rate = {decay_rate:.4f} per step")

    # Predicted stopping time coefficient
    predicted_c = 1 / decay_rate
    actual_c = results['stopping_time']['slope']

    print(f"\nPredicted stopping time coefficient: {predicted_c:.2f}")
    print(f"Actual stopping time coefficient: {actual_c:.2f}")
    print(f"Agreement: {100 * min(predicted_c, actual_c) / max(predicted_c, actual_c):.1f}%")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'../results/asymptotic_analysis_{timestamp}.json'

    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
            return float(obj)
        return obj

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=convert)

    print(f"\n✓ Saved to {output_path}")


if __name__ == '__main__':
    main()
