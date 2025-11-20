#!/usr/bin/env python3
"""
PHASE 1: Area Law Verification for Free Fermion CFT

PREREGISTERED HYPOTHESIS:
S(A) = (c/3) * log(|∂A|) + O(1)
where c = 0.5 (free fermion central charge)

PREDICTIONS:
- Linear fit R² > 0.99
- Slope c_fitted = 0.167 ± 0.01 (c/3 with c=0.5)
- p-value < 0.001

FALSIFIABILITY:
If R² < 0.95 OR |c_fitted - 0.167| > 0.05 → hypothesis is false

This experiment serves as a benchmark and validation of our methods
before proceeding to Phase 2 (metric extraction).
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from scipy.stats import linregress
import matplotlib.pyplot as plt
from typing import Dict, Any
import argparse
import time

from src.tensor_networks.free_fermion import (
    FreeFermionCFT,
    theoretical_area_law_coefficient,
    verify_area_law_analytically
)
from src.validation.statistical import (
    compute_mean_with_ci,
    hypothesis_test_mean,
    linear_regression_with_uncertainty
)
from src.validation.sanity_checks import (
    check_entropy_properties,
    check_area_law_scaling,
    run_all_sanity_checks
)
from src.utils.logging import AutoLogger
from src.utils.visualization import (
    plot_area_law_fit,
    plot_entanglement_entropy_vs_size
)


def run_single_experiment(
    n_sites: int,
    boundary: str,
    seed: int
) -> Dict[str, Any]:
    """
    Run a single area law experiment.

    Args:
        n_sites: Number of lattice sites
        boundary: Boundary conditions
        seed: Random seed

    Returns:
        Dictionary with results
    """
    np.random.seed(seed)

    # Create CFT
    cft = FreeFermionCFT(n_sites, boundary)

    # Compute entanglement for various subsystem sizes
    sizes = []
    entropies = []

    max_size = min(n_sites // 2, 40)  # Don't go too large
    min_size = 4  # Exclude very small L (large finite-size effects)

    for L in range(min_size, max_size + 1):
        subsystem = list(range(L))
        S = cft.entanglement_entropy(subsystem)

        # Sanity check
        check_result = check_entropy_properties(S, L, d_phys=2)
        if not check_result['all_passed']:
            print(f"Warning: Entropy sanity check failed for L={L}")

        sizes.append(L)
        entropies.append(S)

    # Fit area law: S = a * log(L) + b
    sizes_array = np.array(sizes)
    entropies_array = np.array(entropies)

    log_sizes = np.log(sizes_array)

    # Linear regression with uncertainty
    fit_results = linear_regression_with_uncertainty(log_sizes, entropies_array)

    return {
        'n_sites': n_sites,
        'boundary': boundary,
        'seed': seed,
        'sizes': sizes,
        'entropies': entropies,
        'slope': fit_results['slope'],
        'intercept': fit_results['intercept'],
        'r_squared': fit_results['r_squared'],
        'p_value': fit_results['p_value'],
        'std_err_slope': fit_results['std_err_slope'],
        'rmse': fit_results['rmse']
    }


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Phase 1: Area Law Verification'
    )
    parser.add_argument(
        '--n_sites',
        type=int,
        default=64,
        help='Number of lattice sites (default: 64)'
    )
    parser.add_argument(
        '--n_runs',
        type=int,
        default=10,
        help='Number of independent runs (default: 10)'
    )
    parser.add_argument(
        '--boundary',
        type=str,
        default='open',
        choices=['open', 'periodic'],
        help='Boundary conditions'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='results',
        help='Output directory'
    )
    parser.add_argument(
        '--quick_test',
        action='store_true',
        help='Run quick test with fewer runs'
    )

    args = parser.parse_args()

    # Quick test mode
    if args.quick_test:
        args.n_runs = 3
        args.n_sites = 128  # Need larger system for CFT limit

    # Initialize logger
    logger = AutoLogger(
        "phase1_area_law",
        output_dir=os.path.join(args.output_dir, "logs")
    )

    # Preregister hypothesis
    theoretical_coeff = theoretical_area_law_coefficient()
    logger.preregister(
        hypothesis="Area law for entanglement entropy in 1D free fermion CFT",
        prediction=f"S(L) = {theoretical_coeff:.6f} * log(L) + const, R² > 0.99",
        method="Free fermion correlation matrix method + linear regression",
        falsifiability="If R² < 0.95 OR |slope - 0.167| > 0.05 → FALSE"
    )

    print(f"\n{'='*70}")
    print(f"PHASE 1: AREA LAW VERIFICATION")
    print(f"{'='*70}")
    print(f"Parameters:")
    print(f"  Sites: {args.n_sites}")
    print(f"  Runs: {args.n_runs}")
    print(f"  Boundary: {args.boundary}")
    print(f"  Theoretical c/3: {theoretical_coeff:.6f}")
    print(f"{'='*70}\n")

    # Run experiments
    results = []
    start_time = time.time()

    for run_idx in range(args.n_runs):
        print(f"Run {run_idx + 1}/{args.n_runs}...", end=" ", flush=True)

        result = run_single_experiment(
            n_sites=args.n_sites,
            boundary=args.boundary,
            seed=42 + run_idx
        )

        results.append(result)
        logger.log_result(result)

        print(f"slope = {result['slope']:.6f}, R² = {result['r_squared']:.6f}")

    elapsed = time.time() - start_time
    print(f"\nCompleted {args.n_runs} runs in {elapsed:.2f} seconds\n")

    # Analyze results
    results_df = pd.DataFrame(results)

    slopes = results_df['slope'].values
    r_squared = results_df['r_squared'].values

    # Statistical analysis
    print(f"{'='*70}")
    print(f"STATISTICAL ANALYSIS")
    print(f"{'='*70}")

    slope_stats = compute_mean_with_ci(slopes, confidence=0.95)
    print(f"Slope (c/3):")
    print(f"  Mean: {slope_stats['mean']:.6f}")
    print(f"  Std:  {slope_stats['std']:.6f}")
    print(f"  95% CI: [{slope_stats['ci_lower']:.6f}, {slope_stats['ci_upper']:.6f}]")

    r2_stats = compute_mean_with_ci(r_squared, confidence=0.95)
    print(f"\nR² (fit quality):")
    print(f"  Mean: {r2_stats['mean']:.6f}")
    print(f"  Std:  {r2_stats['std']:.6f}")
    print(f"  95% CI: [{r2_stats['ci_lower']:.6f}, {r2_stats['ci_upper']:.6f}]")

    # Hypothesis testing
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS TESTING")
    print(f"{'='*70}")

    hypothesis_result = hypothesis_test_mean(
        slopes,
        expected_value=theoretical_coeff,
        alternative='two-sided'
    )

    print(f"Null hypothesis: slope = {theoretical_coeff:.6f}")
    print(f"Test statistic: t = {hypothesis_result['t_statistic']:.4f}")
    print(f"P-value: {hypothesis_result['p_value']:.6f}")
    print(f"Effect size (Cohen's d): {hypothesis_result['effect_size']:.4f}")

    if hypothesis_result['reject_null']:
        print(f"Result: ✗ Reject null hypothesis (significant difference)")
        logger.log_warning(f"Slope differs significantly from theoretical value")
    else:
        print(f"Result: ✓ Cannot reject null hypothesis (consistent with theory)")
        logger.log_success(f"Slope consistent with theoretical prediction")

    # Success criteria evaluation
    print(f"\n{'='*70}")
    print(f"SUCCESS CRITERIA EVALUATION")
    print(f"{'='*70}")

    criteria_passed = {}

    # Criterion 1: R² > 0.99
    mean_r2 = r2_stats['mean']
    criteria_passed['r_squared'] = mean_r2 > 0.99
    status_r2 = "✓ PASS" if criteria_passed['r_squared'] else "✗ FAIL"
    print(f"1. R² > 0.99: {mean_r2:.6f} ... {status_r2}")

    # Criterion 2: |slope - theoretical| < 0.01
    mean_slope = slope_stats['mean']
    slope_error = abs(mean_slope - theoretical_coeff)
    criteria_passed['slope_accuracy'] = slope_error < 0.01
    status_slope = "✓ PASS" if criteria_passed['slope_accuracy'] else "✗ FAIL"
    print(f"2. |slope - {theoretical_coeff:.6f}| < 0.01: {slope_error:.6f} ... {status_slope}")

    # Criterion 3: p-value < 0.001 for regression
    mean_pval = results_df['p_value'].mean()
    criteria_passed['significance'] = mean_pval < 0.001
    status_pval = "✓ PASS" if criteria_passed['significance'] else "✗ FAIL"
    print(f"3. p-value < 0.001: {mean_pval:.2e} ... {status_pval}")

    # Overall
    all_passed = all(criteria_passed.values())
    print(f"\n{'='*70}")
    if all_passed:
        print(f"✓ ALL CRITERIA PASSED - AREA LAW VERIFIED")
        logger.log_success("All success criteria met")
    else:
        print(f"✗ SOME CRITERIA FAILED")
        logger.log_failure("Not all success criteria met")
    print(f"{'='*70}\n")

    # Visualization
    print(f"Generating visualizations...")

    # Plot 1: Area law fit for first run
    first_result = results[0]
    fit_params = {
        'slope': first_result['slope'],
        'intercept': first_result['intercept'],
        'r_squared': first_result['r_squared']
    }

    plot_path_1 = os.path.join(args.output_dir, "figures", "phase1_entropy_vs_size.pdf")
    plot_entanglement_entropy_vs_size(
        np.array(first_result['sizes']),
        np.array(first_result['entropies']),
        fit_params=fit_params,
        save_path=plot_path_1,
        show=False
    )

    # Plot 2: Slope convergence
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax1 = axes[0]
    ax1.scatter(range(len(slopes)), slopes, alpha=0.6, s=100)
    ax1.axhline(theoretical_coeff, color='red', linestyle='--', linewidth=2,
                label=f'Theory: {theoretical_coeff:.6f}')
    mean_slope_val = slope_stats['mean']
    ax1.axhline(mean_slope_val, color='green', linestyle='-', linewidth=2,
                label=f'Mean: {mean_slope_val:.6f}')
    ax1.fill_between(
        range(len(slopes)),
        slope_stats['ci_lower'],
        slope_stats['ci_upper'],
        alpha=0.2,
        color='green',
        label='95% CI'
    )
    ax1.set_xlabel('Run Number')
    ax1.set_ylabel('Fitted Slope (c/3)')
    ax1.set_title('Slope Consistency Across Runs')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.scatter(range(len(r_squared)), r_squared, alpha=0.6, s=100, color='orange')
    ax2.axhline(0.99, color='red', linestyle='--', linewidth=2, label='Target: 0.99')
    mean_r2_val = r2_stats['mean']
    ax2.axhline(mean_r2_val, color='blue', linestyle='-', linewidth=2,
                label=f'Mean: {mean_r2_val:.6f}')
    ax2.set_xlabel('Run Number')
    ax2.set_ylabel('R² Value')
    ax2.set_title('Fit Quality Across Runs')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0.95, 1.0])

    plt.tight_layout()
    plot_path_2 = os.path.join(args.output_dir, "figures", "phase1_consistency.pdf")
    Path(plot_path_2).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path_2, bbox_inches='tight', dpi=300)
    print(f"  Saved: {plot_path_2}")
    plt.close()

    # Generate report
    report_path = os.path.join(args.output_dir, "logs", "phase1_report.md")
    logger.generate_report(report_path)
    print(f"  Saved: {report_path}")

    # Finalize
    status = "completed" if all_passed else "failed"
    logger.finalize(status)

    print(f"\n{'='*70}")
    print(f"PHASE 1 COMPLETE")
    print(f"Status: {status.upper()}")
    print(f"Results saved to: {args.output_dir}")
    print(f"{'='*70}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
