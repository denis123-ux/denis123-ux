#!/usr/bin/env python3
"""
⚡ ENERGY-WEIGHTED CORRELATION LENGTH - THE FINAL BET
================================================================================
Sample points with Boltzmann weight: P(x) ~ exp(-β × L(x))

BREAKTHROUGH HYPOTHESIS:
- SAT: As β→∞, samples concentrate near solutions (L=0)
       → Correlation length DIVERGES (ξ → ∞)
- UNSAT: No solutions exist (L≥1 always)
         → Correlation length BOUNDED (ξ finite)

This would give DRAMATIC separation ξ_SAT >> ξ_UNSAT!

PHYSICAL INTERPRETATION:
- β = inverse temperature (β→∞ means T→0, "cooling")
- At high temperature (β→0): both look random
- At low temperature (β→∞): SAT crystallizes, UNSAT stays glassy

This is the PHASE TRANSITION view of P vs NP!
================================================================================
"""

import numpy as np
from typing import List, Tuple, Dict
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.optimize import curve_fit
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')


class EnergyWeightedCorrelation:
    """
    Energy-weighted correlation length discriminator.
    """

    def __init__(self, formula: SATFormula,
                 beta: float = 1.0,
                 n_samples: int = 5000,
                 max_distance: int = 20):
        """
        Args:
            formula: SAT formula
            beta: Inverse temperature (β = 1/T)
            n_samples: Number of samples for Monte Carlo
            max_distance: Max Hamming distance to probe
        """
        self.formula = formula
        self.n = formula.n_vars
        self.beta = beta
        self.n_samples = n_samples
        self.max_distance = max_distance

    def _count_violations(self, assignment: np.ndarray) -> int:
        """Count violated clauses."""
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
        """Compute discrete gradient."""
        L_x = self._count_violations(assignment)
        gradient = np.zeros(self.n)

        for i in range(self.n):
            assignment[i] = 1 - assignment[i]
            L_flip = self._count_violations(assignment)
            gradient[i] = L_flip - L_x
            assignment[i] = 1 - assignment[i]

        return gradient

    def _sample_boltzmann(self, n_samples: int, burn_in: int = 100) -> List[Tuple[np.ndarray, int]]:
        """
        Sample assignments from Boltzmann distribution using Metropolis MCMC.

        P(x) ~ exp(-β × L(x))

        Returns:
            List of (assignment, violations) tuples
        """
        samples = []

        # Start from random assignment
        x = np.random.randint(0, 2, size=self.n)
        L_x = self._count_violations(x)

        # Metropolis-Hastings MCMC
        for step in range(burn_in + n_samples):
            # Propose: flip random bit
            i = np.random.randint(self.n)
            x[i] = 1 - x[i]
            L_proposal = self._count_violations(x)

            # Accept/reject
            delta_L = L_proposal - L_x
            if delta_L <= 0:
                # Always accept improvement
                L_x = L_proposal
            else:
                # Accept with Boltzmann probability
                accept_prob = np.exp(-self.beta * delta_L)
                if np.random.rand() < accept_prob:
                    L_x = L_proposal
                else:
                    # Reject: flip back
                    x[i] = 1 - x[i]

            # Collect sample after burn-in
            if step >= burn_in:
                samples.append((x.copy(), L_x))

        return samples

    def compute_weighted_correlation(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute energy-weighted correlation function.

        C_weighted(d) = ⟨∇L(x) · ∇L(x')⟩_Boltzmann

        where samples are drawn from P(x) ~ exp(-βL(x))

        Returns:
            (distances, correlations)
        """
        # Sample from Boltzmann distribution
        print(f"  Sampling from Boltzmann distribution (β={self.beta:.2f})...")
        samples = self._sample_boltzmann(self.n_samples, burn_in=200)

        # Compute average energy
        avg_energy = np.mean([L for _, L in samples])
        print(f"  Average energy: {avg_energy:.2f}")

        distances = np.arange(1, min(self.max_distance + 1, self.n))
        correlations = []

        for d in distances:
            corrs_at_d = []

            # Sample pairs at distance d
            n_pairs = min(100, len(samples) // 2)
            for _ in range(n_pairs):
                # Pick random sample
                idx = np.random.randint(len(samples))
                x, _ = samples[idx]

                # Create x' at distance d
                x_prime = x.copy()
                flip_indices = np.random.choice(self.n, size=d, replace=False)
                x_prime[flip_indices] = 1 - x_prime[flip_indices]

                # Compute gradients
                grad_x = self._compute_gradient(x)
                grad_x_prime = self._compute_gradient(x_prime)

                # Normalized correlation
                norm_x = np.linalg.norm(grad_x)
                norm_x_prime = np.linalg.norm(grad_x_prime)

                if norm_x > 0 and norm_x_prime > 0:
                    corr = np.dot(grad_x, grad_x_prime) / (norm_x * norm_x_prime)
                    corrs_at_d.append(corr)

            if len(corrs_at_d) > 0:
                correlations.append(np.mean(corrs_at_d))
            else:
                correlations.append(0.0)

        return distances, np.array(correlations)

    def fit_correlation_length(self, distances: np.ndarray, correlations: np.ndarray) -> Dict:
        """Fit ξ from correlation function."""
        def exp_decay(d, xi, A):
            return A * np.exp(-d / xi)

        valid_mask = correlations > 0
        if np.sum(valid_mask) < 3:
            return {'xi': np.nan, 'fit_quality': 0.0}

        d_valid = distances[valid_mask]
        c_valid = correlations[valid_mask]

        try:
            popt, _ = curve_fit(exp_decay, d_valid, c_valid,
                               p0=[self.n / 5, c_valid[0]],
                               bounds=([0.1, 0], [self.n, 10]),
                               maxfev=5000)
            xi, A = popt

            # R² quality
            predictions = exp_decay(d_valid, xi, A)
            ss_res = np.sum((c_valid - predictions) ** 2)
            ss_tot = np.sum((c_valid - np.mean(c_valid)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {'xi': xi, 'A': A, 'fit_quality': r_squared}
        except:
            # Fallback
            if np.sum(c_valid) > 0:
                xi = np.sum(d_valid * c_valid) / np.sum(c_valid)
            else:
                xi = 1.0
            return {'xi': xi, 'A': c_valid[0] if len(c_valid) > 0 else 0, 'fit_quality': 0.3}

    def compute(self) -> Dict:
        """Full computation."""
        distances, correlations = self.compute_weighted_correlation()
        fit_results = self.fit_correlation_length(distances, correlations)

        return {
            'distances': distances,
            'correlations': correlations,
            **fit_results
        }


# ============================================================================
# MULTI-TEMPERATURE ANALYSIS
# ============================================================================

def analyze_multitemperature(formulas: List[SATFormula],
                             betas: List[float] = [0.5, 1.0, 2.0, 5.0]) -> Dict:
    """
    Analyze correlation length at multiple temperatures.

    HYPOTHESIS: ξ_SAT(β) grows with β, ξ_UNSAT(β) stays bounded.

    Args:
        formulas: List of formulas
        betas: List of inverse temperatures to test

    Returns:
        Results dictionary
    """
    print("="*80)
    print("⚡ MULTI-TEMPERATURE CORRELATION ANALYSIS")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print(f"Temperatures: β = {betas}")
    print()

    results = {beta: {'sat': [], 'unsat': []} for beta in betas}

    for i, formula in enumerate(formulas):
        for beta in betas:
            disc = EnergyWeightedCorrelation(formula, beta=beta, n_samples=2000, max_distance=15)
            result = disc.compute()

            key = 'sat' if formula.is_sat else 'unsat'
            results[beta][key].append(result['xi'])

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(formulas)}] {'SAT' if formula.is_sat else 'UNSAT'}")

    print()
    print("="*80)
    print("📊 RESULTS vs TEMPERATURE")
    print("="*80)

    for beta in betas:
        sat_xi = np.array([x for x in results[beta]['sat'] if not np.isnan(x)])
        unsat_xi = np.array([x for x in results[beta]['unsat'] if not np.isnan(x)])

        if len(sat_xi) >= 3 and len(unsat_xi) >= 3:
            d = compute_cohens_d(sat_xi, unsat_xi)
            t_stat, p_value = ttest_ind(sat_xi, unsat_xi)

            verdict = "🏆 BREAKTHROUGH" if abs(d) > 1.25 else \
                     "⚡ LARGE" if abs(d) > 0.8 else \
                     "📊 MEDIUM" if abs(d) > 0.5 else "❌ WEAK"

            print(f"\nβ = {beta:.1f}:")
            print(f"  SAT: ξ = {np.mean(sat_xi):.3f} ± {np.std(sat_xi):.3f}")
            print(f"  UNSAT: ξ = {np.mean(unsat_xi):.3f} ± {np.std(unsat_xi):.3f}")
            print(f"  Cohen's d: {d:.4f}  {verdict}")
            print(f"  p-value: {p_value:.2e}")

    print()
    print("="*80)

    return results


if __name__ == "__main__":
    print(__doc__)
