#!/usr/bin/env python3
"""
🔬 ADVANCED CORRELATION ANALYSIS
================================================================================
After discovering ξ_SAT ≈ ξ_UNSAT, we investigate REFINED discriminators:

1. Gradient Magnitude: ⟨|∇L|²⟩ (SAT: strong, UNSAT: weak?)
2. Un-normalized Correlation: C_raw(d) (includes magnitude info)
3. Anisotropy: variance of gradient directions (SAT: aligned, UNSAT: random?)
4. Effective scale: |∇L|² × ξ (combined discriminator)

HYPOTHESIS REFINEMENT:
- Both SAT and UNSAT have similar spatial correlation length ξ
- BUT: SAT has STRONG gradients pointing coherently toward solutions
- UNSAT has WEAK gradients that are uncorrelated noise
================================================================================
"""

import numpy as np
from typing import List, Tuple, Dict
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.optimize import curve_fit
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')


class AdvancedCorrelationDiscriminator:
    """
    Extended correlation analysis with multiple metrics.
    """

    def __init__(self, formula: SATFormula, n_samples: int = 3000, max_distance: int = 20):
        self.formula = formula
        self.n = formula.n_vars
        self.n_samples = n_samples
        self.max_distance = max_distance

    def _count_violations(self, assignment: np.ndarray) -> int:
        """Count number of violated clauses."""
        violations = 0
        for clause in self.formula.clauses:
            satisfied = False
            for lit in clause:
                var_idx = abs(lit) - 1
                var_value = assignment[var_idx]
                if (lit > 0 and var_value == 1) or (lit < 0 and var_value == 0):
                    satisfied = True
                    break
            if not satisfied:
                violations += 1
        return violations

    def _compute_gradient(self, assignment: np.ndarray) -> np.ndarray:
        """Compute discrete gradient ∇L(x)."""
        L_x = self._count_violations(assignment)
        gradient = np.zeros(self.n)

        for i in range(self.n):
            assignment[i] = 1 - assignment[i]
            L_flip = self._count_violations(assignment)
            gradient[i] = L_flip - L_x
            assignment[i] = 1 - assignment[i]

        return gradient

    def compute_gradient_statistics(self) -> Dict:
        """
        Compute statistics of gradient field.

        Returns:
            Dictionary with gradient metrics
        """
        grad_magnitudes = []
        grad_vectors = []

        # Sample random points
        for _ in range(min(self.n_samples, 1000)):
            x = np.random.randint(0, 2, size=self.n)
            grad = self._compute_gradient(x)

            mag = np.linalg.norm(grad)
            grad_magnitudes.append(mag)

            if mag > 0:
                grad_vectors.append(grad / mag)  # Normalized direction

        grad_magnitudes = np.array(grad_magnitudes)
        grad_vectors = np.array(grad_vectors)

        # Gradient magnitude statistics
        mean_mag = np.mean(grad_magnitudes)
        std_mag = np.std(grad_magnitudes)
        mean_mag_sq = np.mean(grad_magnitudes ** 2)

        # Anisotropy: variance of normalized gradients
        # High anisotropy = gradients point in similar directions (SAT?)
        # Low anisotropy = gradients random (UNSAT?)
        if len(grad_vectors) > 0:
            # Compute covariance matrix of normalized gradients
            cov = np.cov(grad_vectors.T)
            eigenvalues = np.linalg.eigvalsh(cov)
            # Anisotropy = ratio of largest to smallest eigenvalue
            anisotropy = eigenvalues[-1] / (eigenvalues[0] + 1e-10)
            # Alternative: effective dimensionality (Shannon entropy of eigenvalues)
            eigenvalues_norm = eigenvalues / (np.sum(eigenvalues) + 1e-10)
            eigenvalues_norm = eigenvalues_norm[eigenvalues_norm > 1e-10]
            if len(eigenvalues_norm) > 0:
                eff_dim = np.exp(-np.sum(eigenvalues_norm * np.log(eigenvalues_norm)))
            else:
                eff_dim = 1.0
        else:
            anisotropy = 1.0
            eff_dim = float(self.n)

        return {
            'mean_magnitude': mean_mag,
            'std_magnitude': std_mag,
            'mean_magnitude_squared': mean_mag_sq,
            'anisotropy': anisotropy,
            'effective_dimensionality': eff_dim
        }

    def compute_raw_correlation(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute UN-NORMALIZED correlation (includes magnitude info).

        C_raw(d) = ⟨∇L(x) · ∇L(x')⟩  (NOT normalized!)

        Returns:
            (distances, raw_correlations, normalized_correlations)
        """
        distances = np.arange(1, min(self.max_distance + 1, self.n))
        raw_corrs = []
        norm_corrs = []

        for d in distances:
            raw_dots = []
            norm_dots = []

            # Sample pairs at distance d
            n_pairs = min(50, self.n_samples // len(distances))
            for _ in range(n_pairs):
                x = np.random.randint(0, 2, size=self.n)
                x_prime = x.copy()
                flip_indices = np.random.choice(self.n, size=d, replace=False)
                x_prime[flip_indices] = 1 - x_prime[flip_indices]

                grad_x = self._compute_gradient(x)
                grad_x_prime = self._compute_gradient(x_prime)

                # Raw dot product
                raw_dot = np.dot(grad_x, grad_x_prime)
                raw_dots.append(raw_dot)

                # Normalized dot product
                mag_x = np.linalg.norm(grad_x)
                mag_x_prime = np.linalg.norm(grad_x_prime)
                if mag_x > 0 and mag_x_prime > 0:
                    norm_dot = raw_dot / (mag_x * mag_x_prime)
                    norm_dots.append(norm_dot)

            if len(raw_dots) > 0:
                raw_corrs.append(np.mean(raw_dots))
            else:
                raw_corrs.append(0.0)

            if len(norm_dots) > 0:
                norm_corrs.append(np.mean(norm_dots))
            else:
                norm_corrs.append(0.0)

        return distances, np.array(raw_corrs), np.array(norm_corrs)

    def fit_correlation_length(self, distances: np.ndarray, correlations: np.ndarray) -> float:
        """Fit and extract ξ."""
        def exp_decay(d, xi, A):
            return A * np.exp(-d / xi)

        valid_mask = correlations > 0
        if np.sum(valid_mask) < 3:
            return np.nan

        d_valid = distances[valid_mask]
        c_valid = correlations[valid_mask]

        try:
            popt, _ = curve_fit(exp_decay, d_valid, c_valid,
                               p0=[self.n / 5, c_valid[0]],
                               bounds=([0.1, 0], [self.n, np.max(c_valid) * 10]),
                               maxfev=5000)
            xi, _ = popt
            return xi
        except:
            # Fallback: weighted mean
            if np.sum(c_valid) > 0:
                return np.sum(d_valid * c_valid) / np.sum(c_valid)
            else:
                return 1.0

    def compute_all(self) -> Dict:
        """
        Compute ALL discriminators.

        Returns:
            Dictionary with all metrics
        """
        # Gradient statistics
        grad_stats = self.compute_gradient_statistics()

        # Correlation functions
        distances, raw_corrs, norm_corrs = self.compute_raw_correlation()

        # Fit correlation lengths
        xi_raw = self.fit_correlation_length(distances, raw_corrs)
        xi_norm = self.fit_correlation_length(distances, norm_corrs)

        # Combined discriminator: magnitude² × ξ
        combined = grad_stats['mean_magnitude_squared'] * xi_raw

        return {
            **grad_stats,
            'xi_raw': xi_raw,
            'xi_normalized': xi_norm,
            'combined_mag2_xi': combined,
            'distances': distances,
            'raw_correlations': raw_corrs,
            'norm_correlations': norm_corrs
        }


# ============================================================================
# BATCH ANALYSIS
# ============================================================================

def analyze_advanced_correlation(formulas: List[SATFormula]) -> Dict:
    """
    Full advanced analysis on list of formulas.
    """
    print("="*80)
    print("🔬 ADVANCED CORRELATION ANALYSIS")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()

    results = {
        'sat': [],
        'unsat': []
    }

    for i, formula in enumerate(formulas):
        disc = AdvancedCorrelationDiscriminator(formula, n_samples=2000, max_distance=15)
        result = disc.compute_all()

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(formulas)}] {key.upper()}: " +
                  f"⟨|∇L|²⟩={result['mean_magnitude_squared']:.2f}, " +
                  f"ξ_raw={result['xi_raw']:.2f}, " +
                  f"combined={result['combined_mag2_xi']:.2f}")

    print()
    print("="*80)
    print("📊 STATISTICAL COMPARISON")
    print("="*80)

    # Extract metrics
    metrics = [
        'mean_magnitude',
        'mean_magnitude_squared',
        'xi_raw',
        'xi_normalized',
        'anisotropy',
        'effective_dimensionality',
        'combined_mag2_xi'
    ]

    comparison = {}

    for metric in metrics:
        sat_vals = np.array([r[metric] for r in results['sat'] if not np.isnan(r[metric])])
        unsat_vals = np.array([r[metric] for r in results['unsat'] if not np.isnan(r[metric])])

        if len(sat_vals) >= 3 and len(unsat_vals) >= 3:
            d = compute_cohens_d(sat_vals, unsat_vals)
            t_stat, p_value = ttest_ind(sat_vals, unsat_vals)

            comparison[metric] = {
                'sat_mean': np.mean(sat_vals),
                'sat_std': np.std(sat_vals),
                'unsat_mean': np.mean(unsat_vals),
                'unsat_std': np.std(unsat_vals),
                'cohens_d': d,
                'p_value': p_value
            }

            verdict = "🏆 BREAKTHROUGH" if abs(d) > 1.25 else \
                     "⚡ LARGE" if abs(d) > 0.8 else \
                     "📊 MEDIUM" if abs(d) > 0.5 else "❌ WEAK"

            print(f"\n{metric}:")
            print(f"  SAT: {np.mean(sat_vals):.3f} ± {np.std(sat_vals):.3f}")
            print(f"  UNSAT: {np.mean(unsat_vals):.3f} ± {np.std(unsat_vals):.3f}")
            print(f"  Cohen's d: {d:.4f}  {verdict}")
            print(f"  p-value: {p_value:.2e}")

    print()
    print("="*80)
    print()

    return {
        'results': results,
        'comparison': comparison
    }


if __name__ == "__main__":
    print(__doc__)
