"""
RANDOM MATRIX THEORY ANALYSIS
=============================

The Montgomery-Odlyzko Law states that the statistical properties of
Riemann zeros match those of eigenvalues of random Hermitian matrices
from the Gaussian Unitary Ensemble (GUE).

This module:
1. Generates GUE random matrices
2. Computes their eigenvalue statistics
3. Compares with Riemann zero statistics
4. Quantifies the "distance" between the two distributions

Key insight: If we can understand WHY this correspondence holds,
we may be able to construct the Hilbert-Pólya operator.
"""

import numpy as np
from scipy import stats
from scipy.special import gamma as gamma_func
from typing import Tuple, List, Optional
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# GUE RANDOM MATRIX GENERATION
# =============================================================================

def generate_gue_matrix(n: int) -> np.ndarray:
    """
    Generate an n x n matrix from the Gaussian Unitary Ensemble (GUE).

    GUE matrices are Hermitian with:
    - Diagonal elements: N(0, 1)
    - Off-diagonal elements: (N(0, 1/2) + i*N(0, 1/2))
    """
    # Real and imaginary parts
    real_part = np.random.randn(n, n) / np.sqrt(2)
    imag_part = np.random.randn(n, n) / np.sqrt(2)

    # Construct Hermitian matrix
    A = real_part + 1j * imag_part
    H = (A + A.conj().T) / np.sqrt(2)

    return H

def gue_eigenvalues(n: int, normalize: bool = True) -> np.ndarray:
    """
    Get eigenvalues of a GUE matrix.

    If normalize=True, scale so mean spacing is 1.
    """
    H = generate_gue_matrix(n)
    eigenvalues = np.linalg.eigvalsh(H)  # Real eigenvalues (Hermitian)
    eigenvalues = np.sort(eigenvalues)

    if normalize:
        # Normalize to unit mean spacing
        spacings = np.diff(eigenvalues)
        mean_spacing = np.mean(spacings)
        if mean_spacing > 0:
            eigenvalues = eigenvalues / mean_spacing

    return eigenvalues

def gue_spacings(n: int, num_samples: int = 1000) -> np.ndarray:
    """
    Generate many GUE matrices and collect all normalized spacings.
    """
    all_spacings = []
    for _ in range(num_samples):
        eigenvalues = gue_eigenvalues(n, normalize=False)
        spacings = np.diff(eigenvalues)
        # Normalize each set of spacings
        mean_spacing = np.mean(spacings)
        if mean_spacing > 0:
            norm_spacings = spacings / mean_spacing
            all_spacings.extend(norm_spacings)

    return np.array(all_spacings)

# =============================================================================
# THEORETICAL GUE DISTRIBUTIONS
# =============================================================================

def wigner_surmise(s: np.ndarray) -> np.ndarray:
    """
    Wigner's surmise for GUE spacing distribution.

    P(s) = (32/π²) * s² * exp(-4s²/π)

    This is an excellent approximation to the true GUE spacing distribution.
    """
    return (32 / np.pi**2) * s**2 * np.exp(-4 * s**2 / np.pi)

def poisson_spacing(s: np.ndarray) -> np.ndarray:
    """
    Poisson (uncorrelated) spacing distribution.

    P(s) = exp(-s)

    This is what we'd expect if zeros were randomly distributed.
    """
    return np.exp(-s)

def goe_surmise(s: np.ndarray) -> np.ndarray:
    """
    Wigner's surmise for GOE (Gaussian Orthogonal Ensemble).

    P(s) = (π/2) * s * exp(-πs²/4)
    """
    return (np.pi / 2) * s * np.exp(-np.pi * s**2 / 4)

# =============================================================================
# PAIR CORRELATION FUNCTION
# =============================================================================

def pair_correlation_gue(r: np.ndarray) -> np.ndarray:
    """
    Theoretical pair correlation function for GUE.

    g(r) = 1 - (sin(πr)/(πr))²

    This is the Montgomery conjecture for Riemann zeros!
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        result = 1 - (np.sin(np.pi * r) / (np.pi * r))**2
        # Handle r=0 case
        result = np.where(np.abs(r) < 1e-10, 0, result)
    return result

def compute_pair_correlation(values: np.ndarray, r_max: float = 5.0,
                             num_bins: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute empirical pair correlation function from a sequence of values.

    For Riemann zeros, this should match pair_correlation_gue!
    """
    n = len(values)

    # Normalize to unit mean spacing
    spacings = np.diff(values)
    mean_spacing = np.mean(spacings)
    normalized = values / mean_spacing

    # Compute all pairwise differences
    differences = []
    for i in range(n):
        for j in range(i+1, n):
            diff = abs(normalized[j] - normalized[i])
            if diff < r_max * n:
                differences.append(diff / n)  # Unfolding

    differences = np.array(differences)

    # Bin the differences
    r_bins = np.linspace(0, r_max, num_bins + 1)
    r_centers = (r_bins[:-1] + r_bins[1:]) / 2

    hist, _ = np.histogram(differences, bins=r_bins, density=True)

    return r_centers, hist

# =============================================================================
# COMPARISON METRICS
# =============================================================================

def kolmogorov_smirnov_test(riemann_spacings: np.ndarray,
                           gue_spacings: np.ndarray) -> Tuple[float, float]:
    """
    Kolmogorov-Smirnov test comparing Riemann spacings to GUE.

    Returns (statistic, p-value).
    Low statistic and high p-value = good match!
    """
    return stats.ks_2samp(riemann_spacings, gue_spacings)

def wasserstein_distance(riemann_spacings: np.ndarray,
                        gue_spacings: np.ndarray) -> float:
    """
    Wasserstein (Earth Mover's) distance between distributions.

    This measures how much "work" is needed to transform one distribution
    into another. Lower = more similar.
    """
    return stats.wasserstein_distance(riemann_spacings, gue_spacings)

def spacing_distribution_comparison(riemann_spacings: np.ndarray,
                                   num_gue_samples: int = 10000) -> dict:
    """
    Comprehensive comparison of Riemann spacing distribution with GUE.
    """
    # Generate theoretical GUE spacings
    # Using Wigner surmise for simplicity
    s_vals = np.linspace(0.01, 4, 1000)
    gue_pdf = wigner_surmise(s_vals)

    # Empirical Riemann statistics
    riemann_mean = np.mean(riemann_spacings)
    riemann_std = np.std(riemann_spacings)
    riemann_skew = stats.skew(riemann_spacings)
    riemann_kurtosis = stats.kurtosis(riemann_spacings)

    # Theoretical GUE statistics (from Wigner surmise)
    # E[s] ≈ 1, Var[s] ≈ 0.178 for normalized GUE spacings
    gue_mean_theory = 1.0
    gue_var_theory = 4/np.pi - 1  # ≈ 0.273

    # Generate GUE samples for comparison
    gue_samples = np.random.choice(s_vals, size=num_gue_samples,
                                   p=gue_pdf/np.sum(gue_pdf))

    # KS test against Wigner surmise
    def wigner_cdf(s):
        # CDF of Wigner surmise
        return 1 - np.exp(-4 * s**2 / np.pi)

    ks_stat, ks_pval = stats.kstest(riemann_spacings, wigner_cdf)

    return {
        'riemann_mean': riemann_mean,
        'riemann_std': riemann_std,
        'riemann_skew': riemann_skew,
        'riemann_kurtosis': riemann_kurtosis,
        'gue_mean_theory': gue_mean_theory,
        'gue_std_theory': np.sqrt(gue_var_theory),
        'ks_statistic': ks_stat,
        'ks_pvalue': ks_pval,
        'wasserstein': wasserstein_distance(riemann_spacings, gue_samples),
    }

# =============================================================================
# LEVEL REPULSION ANALYSIS
# =============================================================================

def analyze_level_repulsion(spacings: np.ndarray) -> dict:
    """
    Analyze level repulsion in the spacing distribution.

    Key insight: GUE shows quadratic level repulsion (P(s) ~ s² for small s),
    while Poisson shows no repulsion (P(s) ~ const for small s).

    If Riemann zeros show GUE-like repulsion, this is strong evidence
    for an underlying Hermitian operator!
    """
    # Fit power law to small spacings
    small_spacings = spacings[spacings < 0.5]  # Small spacing regime

    if len(small_spacings) < 10:
        return {'repulsion_exponent': None, 'message': 'Not enough small spacings'}

    # Log-log fit: log(P(s)) = β*log(s) + const
    # β = 0: Poisson (no repulsion)
    # β = 1: GOE (linear repulsion)
    # β = 2: GUE (quadratic repulsion)

    # Create histogram of small spacings
    hist, bin_edges = np.histogram(small_spacings, bins=20, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Filter out zeros
    mask = (hist > 0) & (bin_centers > 0.01)
    if np.sum(mask) < 3:
        return {'repulsion_exponent': None, 'message': 'Cannot fit power law'}

    log_s = np.log(bin_centers[mask])
    log_p = np.log(hist[mask])

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_s, log_p)

    classification = "Unknown"
    if slope < 0.5:
        classification = "Poisson-like (no repulsion)"
    elif slope < 1.5:
        classification = "GOE-like (linear repulsion)"
    elif slope < 2.5:
        classification = "GUE-like (quadratic repulsion)"
    else:
        classification = "Super-GUE (strong repulsion)"

    return {
        'repulsion_exponent': slope,
        'exponent_std_err': std_err,
        'r_squared': r_value**2,
        'classification': classification,
        'gue_expected': 2.0,
    }

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def full_rmt_analysis(riemann_spacings: np.ndarray, verbose: bool = True) -> dict:
    """
    Complete Random Matrix Theory analysis of Riemann zero spacings.
    """
    results = {}

    # 1. Basic comparison
    if verbose:
        print("=" * 60)
        print("RANDOM MATRIX THEORY ANALYSIS")
        print("=" * 60)

    comparison = spacing_distribution_comparison(riemann_spacings)
    results['comparison'] = comparison

    if verbose:
        print(f"\nSpacing Statistics:")
        print(f"  Riemann mean: {comparison['riemann_mean']:.4f} (GUE theory: {comparison['gue_mean_theory']:.4f})")
        print(f"  Riemann std:  {comparison['riemann_std']:.4f} (GUE theory: {comparison['gue_std_theory']:.4f})")
        print(f"\nKolmogorov-Smirnov Test vs Wigner Surmise:")
        print(f"  Statistic: {comparison['ks_statistic']:.4f}")
        print(f"  P-value:   {comparison['ks_pvalue']:.4f}")
        print(f"\nWasserstein Distance: {comparison['wasserstein']:.4f}")

    # 2. Level repulsion
    repulsion = analyze_level_repulsion(riemann_spacings)
    results['repulsion'] = repulsion

    if verbose:
        print(f"\nLevel Repulsion Analysis:")
        if repulsion['repulsion_exponent'] is not None:
            print(f"  Exponent β: {repulsion['repulsion_exponent']:.2f} ± {repulsion['exponent_std_err']:.2f}")
            print(f"  Expected (GUE): {repulsion['gue_expected']:.2f}")
            print(f"  Classification: {repulsion['classification']}")
            print(f"  R²: {repulsion['r_squared']:.4f}")

    # 3. Verdict
    if verbose:
        print("\n" + "=" * 60)
        print("VERDICT")
        print("=" * 60)

        gue_match_score = 0

        # Check mean
        if abs(comparison['riemann_mean'] - 1.0) < 0.1:
            gue_match_score += 1

        # Check KS test
        if comparison['ks_pvalue'] > 0.05:
            gue_match_score += 1

        # Check repulsion
        if repulsion['repulsion_exponent'] is not None:
            if 1.5 < repulsion['repulsion_exponent'] < 2.5:
                gue_match_score += 1

        print(f"GUE Match Score: {gue_match_score}/3")
        if gue_match_score >= 2:
            print("✓ Strong evidence for GUE correspondence!")
            print("→ This supports the Hilbert-Pólya conjecture.")
        else:
            print("△ Weak GUE correspondence (may need more data).")

    results['gue_match_score'] = gue_match_score
    return results


if __name__ == "__main__":
    from riemann_zeros import get_normalized_spacings

    # Get Riemann zeros spacings
    riemann_spacings = get_normalized_spacings()

    # Run full analysis
    results = full_rmt_analysis(riemann_spacings)
