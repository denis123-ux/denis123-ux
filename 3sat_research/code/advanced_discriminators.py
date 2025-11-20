#!/usr/bin/env python3
"""
🔥 ADVANCED DISCRIMINATORS - BREAKTHROUGH STRATEGIES
================================================================================
Hybrid combinations and optimized approaches to BEAT d=1.25 baseline!
================================================================================
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict
from sat_tensor_framework import (
    parse_cnf, SATFormula, FractionalDerivativeDiscriminator,
    compute_cohens_d
)
from scipy.stats import ttest_ind
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# HYBRID DISCRIMINATOR (THE KILLER APP!)
# ============================================================================

class HybridDiscriminator:
    """
    Weighted combination of multiple discriminators.

    STRATEGY: Combine strengths of different approaches
    - lm_mean_depth: Strong baseline (d=1.25)
    - fractional_derivative: Novel gradient-based
    - holonomy: Gauge theory (weak, but orthogonal)

    Optimize weights to MAXIMIZE Cohen's d!
    """

    def __init__(self, df: pd.DataFrame, discriminators: List[str]):
        """
        Initialize with results dataframe.

        Args:
            df: Results with columns for each discriminator
            discriminators: List of column names to combine
        """
        self.df = df
        self.discriminators = discriminators
        self.optimal_weights = None
        self.optimal_d = None

    def compute_hybrid_score(self, weights: np.ndarray) -> np.ndarray:
        """
        Compute weighted combination score.

        Args:
            weights: Array of weights for each discriminator

        Returns:
            Combined score for each instance
        """
        # Normalize weights
        weights = np.abs(weights)
        weights = weights / (np.sum(weights) + 1e-15)

        # Standardize each discriminator (z-score)
        scores = np.zeros(len(self.df))

        for i, disc in enumerate(self.discriminators):
            values = self.df[disc].values
            # Remove NaNs
            valid_mask = ~np.isnan(values)
            if np.sum(valid_mask) < 10:
                continue

            # Standardize
            mean = np.nanmean(values)
            std = np.nanstd(values)
            if std > 0:
                z_scores = (values - mean) / std
                z_scores = np.nan_to_num(z_scores, nan=0.0)
                scores += weights[i] * z_scores

        return scores

    def objective(self, weights: np.ndarray) -> float:
        """
        Objective function: NEGATIVE Cohen's d (minimize = maximize d).

        Args:
            weights: Candidate weights

        Returns:
            Negative Cohen's d (for minimization)
        """
        scores = self.compute_hybrid_score(weights)

        sat_scores = scores[self.df['is_sat'] == True]
        unsat_scores = scores[self.df['is_sat'] == False]

        if len(sat_scores) < 10 or len(unsat_scores) < 10:
            return 1000.0  # Penalty for invalid

        # Compute Cohen's d
        d = compute_cohens_d(sat_scores, unsat_scores)

        # Return negative (minimize = maximize d)
        return -abs(d)

    def optimize_weights(self, method: str = 'Nelder-Mead') -> Tuple[np.ndarray, float]:
        """
        Find optimal weights via optimization.

        Args:
            method: Scipy optimization method

        Returns:
            (optimal_weights, optimal_d)
        """
        n_disc = len(self.discriminators)

        # Initial guess: equal weights
        x0 = np.ones(n_disc) / n_disc

        # Optimize
        result = minimize(
            self.objective,
            x0,
            method=method,
            options={'maxiter': 1000, 'disp': False}
        )

        optimal_weights = np.abs(result.x)
        optimal_weights = optimal_weights / np.sum(optimal_weights)

        optimal_d = -result.fun  # Negate back

        self.optimal_weights = optimal_weights
        self.optimal_d = optimal_d

        return optimal_weights, optimal_d

    def get_optimal_scores(self) -> np.ndarray:
        """Get hybrid scores with optimal weights."""
        if self.optimal_weights is None:
            raise ValueError("Must call optimize_weights() first!")
        return self.compute_hybrid_score(self.optimal_weights)

    def print_results(self):
        """Print optimization results."""
        if self.optimal_weights is None:
            raise ValueError("Must call optimize_weights() first!")

        print("="*80)
        print("🔥 HYBRID DISCRIMINATOR RESULTS")
        print("="*80)
        print()
        print("Optimal Weights:")
        for disc, weight in zip(self.discriminators, self.optimal_weights):
            print(f"  {disc:<30} {weight:>8.4f}")
        print()
        print(f"Optimal Cohen's d: {self.optimal_d:.4f}")
        print()

        # Compare to individual discriminators
        print("Comparison to Individual Discriminators:")
        print("-"*80)

        for disc in self.discriminators:
            sat_vals = self.df[self.df['is_sat'] == True][disc].dropna().values
            unsat_vals = self.df[self.df['is_sat'] == False][disc].dropna().values

            if len(sat_vals) < 10 or len(unsat_vals) < 10:
                continue

            d_individual = compute_cohens_d(sat_vals, unsat_vals)
            improvement = ((self.optimal_d - d_individual) / d_individual) * 100

            print(f"  {disc:<30} d={d_individual:.4f}  (Δ={improvement:+.1f}%)")

        print("="*80)
        print()


# ============================================================================
# ALPHA GRID SEARCH (FIND OPTIMAL FRACTIONAL ORDER)
# ============================================================================

class AlphaOptimizer:
    """
    Grid search to find optimal α for fractional derivative.

    Tests α ∈ [1.0, 2.0] with fine resolution.
    Goal: Find α* that maximizes Cohen's d.
    """

    def __init__(self, formulas: List[SATFormula]):
        """
        Initialize with list of formulas.

        Args:
            formulas: List of SATFormula objects (subset for speed)
        """
        self.formulas = formulas
        self.alpha_range = (1.0, 2.0)
        self.results = []

    def evaluate_alpha(self, alpha: float, n_samples: int = 100) -> float:
        """
        Evaluate fractional derivative at given α on sample.

        Args:
            alpha: Fractional order
            n_samples: Number of formulas to test (for speed)

        Returns:
            Cohen's d at this α
        """
        # Sample formulas
        if n_samples < len(self.formulas):
            sample_idx = np.random.choice(len(self.formulas), n_samples, replace=False)
            sample = [self.formulas[i] for i in sample_idx]
        else:
            sample = self.formulas

        sat_values = []
        unsat_values = []

        for formula in sample:
            try:
                fd = FractionalDerivativeDiscriminator(formula)
                value = fd.compute_fractional_derivative(alpha=alpha)

                if formula.is_sat:
                    sat_values.append(value)
                else:
                    unsat_values.append(value)
            except:
                continue

        if len(sat_values) < 5 or len(unsat_values) < 5:
            return 0.0

        d = compute_cohens_d(np.array(sat_values), np.array(unsat_values))
        return abs(d)

    def grid_search(self, n_points: int = 20, n_samples: int = 100) -> Tuple[float, float]:
        """
        Grid search over α range.

        Args:
            n_points: Number of α values to test
            n_samples: Formulas per α (for speed)

        Returns:
            (optimal_alpha, optimal_d)
        """
        print("="*80)
        print("⚡ ALPHA GRID SEARCH")
        print("="*80)
        print(f"Range: α ∈ [{self.alpha_range[0]}, {self.alpha_range[1]}]")
        print(f"Points: {n_points}")
        print(f"Samples per point: {n_samples}")
        print()

        alphas = np.linspace(self.alpha_range[0], self.alpha_range[1], n_points)

        for i, alpha in enumerate(alphas):
            d = self.evaluate_alpha(alpha, n_samples)
            self.results.append({'alpha': alpha, 'cohens_d': d})

            # Progress
            if (i + 1) % 5 == 0:
                print(f"  [{i+1}/{n_points}] α={alpha:.3f} → d={d:.4f}")

        # Find optimal
        results_df = pd.DataFrame(self.results)
        optimal_idx = results_df['cohens_d'].idxmax()
        optimal_alpha = results_df.loc[optimal_idx, 'alpha']
        optimal_d = results_df.loc[optimal_idx, 'cohens_d']

        print()
        print(f"🎯 OPTIMAL: α*={optimal_alpha:.4f} with d={optimal_d:.4f}")
        print("="*80)
        print()

        return optimal_alpha, optimal_d

    def plot_results(self, save_path: Path):
        """Generate α vs d plot."""
        import matplotlib.pyplot as plt

        df = pd.DataFrame(self.results)

        plt.figure(figsize=(10, 6))
        plt.plot(df['alpha'], df['cohens_d'], 'o-', linewidth=2, markersize=8)
        plt.axhline(y=1.0, color='r', linestyle='--', label='Breakthrough threshold (d=1.0)')
        plt.axhline(y=1.25, color='g', linestyle='--', label='Baseline (d=1.25)')

        plt.xlabel('Fractional Order α', fontsize=14, fontweight='bold')
        plt.ylabel("Cohen's d", fontsize=14, fontweight='bold')
        plt.title('Fractional Derivative: Optimal α Search', fontsize=16, fontweight='bold')
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)

        # Annotate optimal
        optimal_idx = df['cohens_d'].idxmax()
        optimal_alpha = df.loc[optimal_idx, 'alpha']
        optimal_d = df.loc[optimal_idx, 'cohens_d']

        plt.scatter([optimal_alpha], [optimal_d], color='red', s=200, zorder=5,
                   marker='*', edgecolors='black', linewidths=2)
        plt.annotate(f'α*={optimal_alpha:.3f}\nd={optimal_d:.3f}',
                    xy=(optimal_alpha, optimal_d),
                    xytext=(optimal_alpha + 0.1, optimal_d - 0.1),
                    fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', lw=2))

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Plot saved: {save_path}")


# ============================================================================
# BOOTSTRAP CONFIDENCE INTERVALS
# ============================================================================

def bootstrap_cohen_d(sat_values: np.ndarray, unsat_values: np.ndarray,
                     n_bootstrap: int = 1000, confidence: float = 0.95) -> Dict:
    """
    Compute bootstrap confidence intervals for Cohen's d.

    Args:
        sat_values: SAT discriminator values
        unsat_values: UNSAT discriminator values
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level (e.g., 0.95 for 95% CI)

    Returns:
        Dictionary with d, CI_lower, CI_upper, std_error
    """
    n_sat = len(sat_values)
    n_unsat = len(unsat_values)

    bootstrap_ds = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        sat_boot = np.random.choice(sat_values, size=n_sat, replace=True)
        unsat_boot = np.random.choice(unsat_values, size=n_unsat, replace=True)

        # Compute d
        d_boot = compute_cohens_d(sat_boot, unsat_boot)
        bootstrap_ds.append(d_boot)

    bootstrap_ds = np.array(bootstrap_ds)

    # Compute percentiles
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    ci_lower = np.percentile(bootstrap_ds, lower_percentile)
    ci_upper = np.percentile(bootstrap_ds, upper_percentile)

    d_mean = np.mean(bootstrap_ds)
    d_std = np.std(bootstrap_ds)

    return {
        'd': d_mean,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'std_error': d_std,
        'confidence': confidence
    }


# ============================================================================
# MAIN DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("🔥 ADVANCED DISCRIMINATORS - DEMO")
    print("="*80)
    print()
    print("This module provides:")
    print("1. HybridDiscriminator: Optimal weighted combination")
    print("2. AlphaOptimizer: Find best α for fractional derivatives")
    print("3. Bootstrap CI: Robust confidence intervals")
    print()
    print("Usage:")
    print()
    print("  # After full analysis completes:")
    print("  df = pd.read_csv('../results/full_analysis.csv')")
    print()
    print("  # Hybrid discriminator")
    print("  hybrid = HybridDiscriminator(df, ['lm_mean_depth', 'fractional_derivative_1.5'])")
    print("  weights, d = hybrid.optimize_weights()")
    print("  hybrid.print_results()")
    print()
    print("  # Alpha optimization")
    print("  formulas = [parse_cnf(f) for f in formula_files[:100]]")
    print("  optimizer = AlphaOptimizer(formulas)")
    print("  alpha_opt, d_opt = optimizer.grid_search(n_points=20)")
    print()
    print("="*80)
