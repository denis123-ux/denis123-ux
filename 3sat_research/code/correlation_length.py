#!/usr/bin/env python3
"""
🌊 CORRELATION LENGTH DISCRIMINATOR
================================================================================
Measures the spatial scale over which gradient information persists.

CORE HYPOTHESIS:
- SAT: ξ_SAT ~ O(n) - gradients point coherently toward distant solutions
- UNSAT: ξ_UNSAT ~ O(1) or O(log n) - gradients are locally confused

This represents the FUNDAMENTAL SCALE of the P vs NP barrier!
================================================================================
"""

import numpy as np
from typing import List, Tuple, Dict
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.optimize import curve_fit
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')


class CorrelationLengthDiscriminator:
    """
    Measures correlation length ξ of gradient field in discrete space.

    For each formula, computes:
        C(d) = ⟨∇L(x) · ∇L(x')⟩  where Hamming(x,x') = d

    Then fits C(d) ~ exp(-d/ξ) to extract correlation length ξ.
    """

    def __init__(self, formula: SATFormula, n_samples: int = 5000, max_distance: int = 20):
        """
        Initialize discriminator.

        Args:
            formula: SAT formula
            n_samples: Number of random points to sample
            max_distance: Maximum Hamming distance to probe
        """
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
        """
        Compute discrete gradient ∇L(x).

        ∇L(x)_i = L(x^{flip_i}) - L(x)

        where x^{flip_i} is x with bit i flipped.

        Returns:
            Gradient vector (n dimensions)
        """
        L_x = self._count_violations(assignment)
        gradient = np.zeros(self.n)

        for i in range(self.n):
            # Flip bit i
            assignment[i] = 1 - assignment[i]
            L_flip = self._count_violations(assignment)
            gradient[i] = L_flip - L_x
            # Flip back
            assignment[i] = 1 - assignment[i]

        return gradient

    def _sample_pairs_at_distance(self, d: int, n_pairs: int = 100) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Sample pairs of assignments at Hamming distance d.

        Args:
            d: Target Hamming distance
            n_pairs: Number of pairs to sample

        Returns:
            List of (x, x') pairs with Hamming(x, x') = d
        """
        pairs = []

        for _ in range(n_pairs):
            # Sample random x
            x = np.random.randint(0, 2, size=self.n)

            # Create x' by flipping exactly d random bits
            x_prime = x.copy()
            flip_indices = np.random.choice(self.n, size=d, replace=False)
            x_prime[flip_indices] = 1 - x_prime[flip_indices]

            pairs.append((x, x_prime))

        return pairs

    def compute_correlation_function(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute C(d) for d = 1, 2, ..., max_distance.

        C(d) = ⟨∇L(x) · ∇L(x')⟩_{Hamming(x,x')=d}

        Returns:
            (distances, correlations)
        """
        distances = np.arange(1, min(self.max_distance + 1, self.n))
        correlations = []

        for d in distances:
            # Sample pairs at distance d
            pairs = self._sample_pairs_at_distance(d, n_pairs=min(100, self.n_samples // len(distances)))

            # Compute gradient correlations
            dot_products = []
            for x, x_prime in pairs:
                grad_x = self._compute_gradient(x)
                grad_x_prime = self._compute_gradient(x_prime)

                # Normalized dot product
                norm_x = np.linalg.norm(grad_x)
                norm_x_prime = np.linalg.norm(grad_x_prime)

                if norm_x > 0 and norm_x_prime > 0:
                    dot = np.dot(grad_x, grad_x_prime) / (norm_x * norm_x_prime)
                    dot_products.append(dot)

            if len(dot_products) > 0:
                correlations.append(np.mean(dot_products))
            else:
                correlations.append(0.0)

        return distances, np.array(correlations)

    def fit_correlation_length(self, distances: np.ndarray, correlations: np.ndarray) -> Dict:
        """
        Fit C(d) ~ exp(-d/ξ) to extract correlation length ξ.

        Args:
            distances: Array of distances
            correlations: Array of C(d) values

        Returns:
            Dictionary with fit results
        """
        # Exponential decay model
        def exp_decay(d, xi, A):
            return A * np.exp(-d / xi)

        # Filter positive correlations for fitting
        valid_mask = correlations > 0
        if np.sum(valid_mask) < 3:
            # Not enough points for fit
            return {
                'xi': np.nan,
                'A': np.nan,
                'fit_quality': 0.0,
                'method': 'insufficient_data'
            }

        d_valid = distances[valid_mask]
        c_valid = correlations[valid_mask]

        try:
            # Fit exponential decay
            popt, pcov = curve_fit(exp_decay, d_valid, c_valid,
                                  p0=[self.n / 5, 1.0],
                                  bounds=([0.1, 0], [self.n, 10]),
                                  maxfev=5000)
            xi, A = popt

            # Compute R² as fit quality
            predictions = exp_decay(d_valid, xi, A)
            ss_res = np.sum((c_valid - predictions) ** 2)
            ss_tot = np.sum((c_valid - np.mean(c_valid)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {
                'xi': xi,
                'A': A,
                'fit_quality': r_squared,
                'method': 'exponential_fit'
            }
        except:
            # Fit failed, use decay rate estimate
            # Estimate as d where C(d) ≈ C(1)/e
            target = c_valid[0] / np.e if len(c_valid) > 0 else 0

            if len(c_valid) > 1:
                # Find crossover
                for i, c in enumerate(c_valid):
                    if c < target:
                        xi_estimate = d_valid[i]
                        return {
                            'xi': xi_estimate,
                            'A': c_valid[0],
                            'fit_quality': 0.5,
                            'method': 'crossover'
                        }

            # Default: use mean distance weighted by correlation
            if np.sum(c_valid) > 0:
                xi_estimate = np.sum(d_valid * c_valid) / np.sum(c_valid)
            else:
                xi_estimate = 1.0

            return {
                'xi': xi_estimate,
                'A': c_valid[0] if len(c_valid) > 0 else 0,
                'fit_quality': 0.3,
                'method': 'weighted_mean'
            }

    def compute(self) -> Dict:
        """
        Main computation: compute correlation function and fit ξ.

        Returns:
            Dictionary with all results
        """
        distances, correlations = self.compute_correlation_function()
        fit_results = self.fit_correlation_length(distances, correlations)

        return {
            'distances': distances,
            'correlations': correlations,
            **fit_results
        }


# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_correlation_length(formulas: List[SATFormula],
                               n_samples: int = 3000,
                               max_distance: int = 20) -> Dict:
    """
    Analyze correlation length for a list of formulas.

    Args:
        formulas: List of SAT formulas
        n_samples: Samples per formula
        max_distance: Max Hamming distance

    Returns:
        Analysis results with Cohen's d
    """
    print("="*80)
    print("🌊 CORRELATION LENGTH ANALYSIS")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print(f"Samples per formula: {n_samples}")
    print(f"Max distance: {max_distance}")
    print()

    sat_xi = []
    unsat_xi = []

    for i, formula in enumerate(formulas):
        disc = CorrelationLengthDiscriminator(formula, n_samples=n_samples, max_distance=max_distance)
        result = disc.compute()

        xi = result['xi']

        if not np.isnan(xi):
            if formula.is_sat:
                sat_xi.append(xi)
            else:
                unsat_xi.append(xi)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(formulas)}] ξ={xi:.2f} ({'SAT' if formula.is_sat else 'UNSAT'})")

    print()
    print("="*80)
    print("📊 RESULTS")
    print("="*80)

    sat_xi = np.array(sat_xi)
    unsat_xi = np.array(unsat_xi)

    print(f"SAT: n={len(sat_xi)}, ξ_mean={np.mean(sat_xi):.3f} ± {np.std(sat_xi):.3f}")
    print(f"UNSAT: n={len(unsat_xi)}, ξ_mean={np.mean(unsat_xi):.3f} ± {np.std(unsat_xi):.3f}")
    print()

    if len(sat_xi) >= 5 and len(unsat_xi) >= 5:
        d = compute_cohens_d(sat_xi, unsat_xi)
        t_stat, p_value = ttest_ind(sat_xi, unsat_xi)

        print(f"Cohen's d: {d:.4f}")
        print(f"t-test: t={t_stat:.3f}, p={p_value:.2e}")
        print()

        if abs(d) > 1.25:
            print("🏆 BREAKTHROUGH! d > 1.25")
        elif abs(d) > 0.8:
            print("⚡ LARGE EFFECT! d > 0.8")
        elif abs(d) > 0.5:
            print("📊 MEDIUM EFFECT")
        else:
            print("❌ WEAK EFFECT")
    else:
        d = np.nan
        p_value = np.nan
        print("⚠️  Insufficient data for statistics")

    print("="*80)
    print()

    return {
        'sat_xi': sat_xi,
        'unsat_xi': unsat_xi,
        'cohens_d': d,
        'p_value': p_value
    }


if __name__ == "__main__":
    print(__doc__)
    print("\nThis module provides CorrelationLengthDiscriminator.")
    print("Import and use in analysis scripts.")
