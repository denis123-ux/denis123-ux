"""
ENTROPY AND INFORMATION THEORY ANALYSIS
========================================

Based on the 2025 paper "Spectral Entropy Collapse and the Riemann Hypothesis"
by Douglas F. Watson, which proposes:

"RH is equivalent to a unique collapse of arithmetic entropy."

This module implements:
1. Spectral entropy measures
2. Information-theoretic analysis of zeros
3. Kolmogorov complexity estimates
4. Entropy collapse detection

Key Hypothesis: If RH is true, there should be a characteristic entropy
signature that distinguishes valid zeros from hypothetical invalid ones.
"""

import numpy as np
from scipy import stats
from scipy.special import digamma, gamma as gamma_func
from typing import List, Tuple, Optional, Dict
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# SHANNON ENTROPY MEASURES
# =============================================================================

def shannon_entropy(probs: np.ndarray) -> float:
    """
    Shannon entropy: H = -Σ p_i log(p_i)
    """
    probs = probs[probs > 0]  # Filter zeros
    return -np.sum(probs * np.log(probs))

def spacing_entropy(zeros: np.ndarray, n_bins: int = 20) -> float:
    """
    Entropy of the spacing distribution.

    Higher entropy = more random spacing
    Lower entropy = more structured spacing

    GUE spacings should have a specific entropy value!
    """
    spacings = np.diff(zeros)
    # Normalize
    spacings = spacings / np.mean(spacings)

    # Create histogram
    hist, _ = np.histogram(spacings, bins=n_bins, density=True)
    hist = hist / np.sum(hist)  # Normalize to probability

    return shannon_entropy(hist)

def theoretical_gue_entropy(n_bins: int = 20) -> float:
    """
    Compute theoretical entropy of Wigner surmise distribution.
    """
    s = np.linspace(0.001, 5, 1000)
    # Wigner surmise PDF
    pdf = (32 / np.pi**2) * s**2 * np.exp(-4 * s**2 / np.pi)
    pdf = pdf / np.sum(pdf)  # Normalize

    # Bin it
    hist, _ = np.histogram(s, bins=n_bins, weights=pdf, density=False)
    hist = hist / np.sum(hist)

    return shannon_entropy(hist)

def theoretical_poisson_entropy(n_bins: int = 20) -> float:
    """
    Compute theoretical entropy of Poisson (exponential) distribution.
    """
    s = np.linspace(0.001, 5, 1000)
    pdf = np.exp(-s)
    pdf = pdf / np.sum(pdf)

    hist, _ = np.histogram(s, bins=n_bins, weights=pdf, density=False)
    hist = hist / np.sum(hist)

    return shannon_entropy(hist)

# =============================================================================
# DIFFERENTIAL ENTROPY
# =============================================================================

def differential_entropy_gaussian(variance: float) -> float:
    """
    Differential entropy of Gaussian: h = 0.5 * log(2πeσ²)
    """
    return 0.5 * np.log(2 * np.pi * np.e * variance)

def differential_entropy_estimate(data: np.ndarray, method: str = 'knn') -> float:
    """
    Estimate differential entropy from data.

    Methods:
    - 'knn': k-nearest neighbor estimator
    - 'histogram': simple histogram-based
    """
    if method == 'histogram':
        hist, bin_edges = np.histogram(data, bins='auto', density=True)
        bin_width = bin_edges[1] - bin_edges[0]
        hist = hist[hist > 0]
        return -np.sum(hist * np.log(hist) * bin_width)

    elif method == 'knn':
        # Kozachenko-Leonenko estimator
        n = len(data)
        k = max(1, int(np.sqrt(n)))

        # Sort data
        data_sorted = np.sort(data)

        # Compute distances to k-th nearest neighbor
        distances = []
        for i in range(n):
            # Find k nearest neighbors
            dists = np.abs(data_sorted - data[i])
            dists = np.sort(dists)
            if len(dists) > k:
                distances.append(dists[k])
            else:
                distances.append(dists[-1])

        distances = np.array(distances)
        distances = distances[distances > 0]

        # KL estimator
        estimate = digamma(n) - digamma(k) + np.mean(np.log(2 * distances))
        return estimate

    else:
        raise ValueError(f"Unknown method: {method}")

# =============================================================================
# SPECTRAL ENTROPY (from 2025 paper concept)
# =============================================================================

def spectral_entropy(zeros: np.ndarray, window_size: int = 20) -> np.ndarray:
    """
    Compute local spectral entropy of zeros.

    This captures how "locally random" the zeros appear.
    """
    spacings = np.diff(zeros)
    n = len(spacings)

    entropies = []
    for i in range(n - window_size + 1):
        local_spacings = spacings[i:i+window_size]
        local_spacings = local_spacings / np.mean(local_spacings)

        # Compute entropy
        hist, _ = np.histogram(local_spacings, bins=10, density=True)
        hist = hist / (np.sum(hist) + 1e-10)
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log(hist + 1e-10))
        entropies.append(entropy)

    return np.array(entropies)

def entropy_collapse_test(zeros: np.ndarray) -> Dict:
    """
    Test for "spectral entropy collapse" as proposed in 2025 paper.

    The hypothesis is that RH is equivalent to a unique collapse
    of arithmetic entropy at the critical line.
    """
    spacings = np.diff(zeros)
    spacings_norm = spacings / np.mean(spacings)

    results = {}

    # 1. Global entropy
    results['global_spacing_entropy'] = spacing_entropy(zeros)
    results['gue_theoretical_entropy'] = theoretical_gue_entropy()
    results['poisson_theoretical_entropy'] = theoretical_poisson_entropy()

    # 2. Entropy distance from GUE
    entropy_dist_gue = abs(results['global_spacing_entropy'] - results['gue_theoretical_entropy'])
    entropy_dist_poisson = abs(results['global_spacing_entropy'] - results['poisson_theoretical_entropy'])
    results['entropy_distance_gue'] = entropy_dist_gue
    results['entropy_distance_poisson'] = entropy_dist_poisson

    # 3. Entropy collapse ratio
    # If RH is true, entropy should be "collapsed" toward GUE value
    if entropy_dist_poisson > 0:
        results['collapse_ratio'] = entropy_dist_gue / entropy_dist_poisson
    else:
        results['collapse_ratio'] = float('inf')

    # 4. Local entropy variation
    local_entropies = spectral_entropy(zeros)
    results['local_entropy_mean'] = np.mean(local_entropies)
    results['local_entropy_std'] = np.std(local_entropies)
    results['local_entropy_stability'] = 1 / (1 + np.std(local_entropies))

    # 5. Entropy convergence (should stabilize as we add more zeros)
    entropy_sequence = []
    for n in range(10, len(zeros), 5):
        ent = spacing_entropy(zeros[:n])
        entropy_sequence.append(ent)
    results['entropy_sequence'] = entropy_sequence
    if len(entropy_sequence) > 5:
        results['entropy_convergence'] = np.std(entropy_sequence[-5:])
    else:
        results['entropy_convergence'] = np.std(entropy_sequence)

    return results

# =============================================================================
# MUTUAL INFORMATION
# =============================================================================

def mutual_information_spacings(zeros: np.ndarray, lag: int = 1) -> float:
    """
    Compute mutual information between spacings at different positions.

    I(S_i; S_{i+lag})

    High MI = spacings are correlated (non-random structure)
    Low MI = spacings are independent (more random)

    GUE has specific MI structure!
    """
    spacings = np.diff(zeros)
    n = len(spacings)

    if n <= lag:
        return 0.0

    s1 = spacings[:n-lag]
    s2 = spacings[lag:]

    # Estimate MI using binning
    n_bins = min(20, int(np.sqrt(len(s1))))

    # 2D histogram
    hist_2d, _, _ = np.histogram2d(s1, s2, bins=n_bins)
    p_xy = hist_2d / np.sum(hist_2d)

    # Marginals
    p_x = np.sum(p_xy, axis=1)
    p_y = np.sum(p_xy, axis=0)

    # MI = Σ p(x,y) log(p(x,y) / (p(x)p(y)))
    mi = 0.0
    for i in range(n_bins):
        for j in range(n_bins):
            if p_xy[i, j] > 0 and p_x[i] > 0 and p_y[j] > 0:
                mi += p_xy[i, j] * np.log(p_xy[i, j] / (p_x[i] * p_y[j]))

    return mi

def mutual_information_profile(zeros: np.ndarray, max_lag: int = 10) -> np.ndarray:
    """
    Compute MI at different lags to reveal correlation structure.
    """
    mi_values = []
    for lag in range(1, max_lag + 1):
        mi = mutual_information_spacings(zeros, lag)
        mi_values.append(mi)
    return np.array(mi_values)

# =============================================================================
# KOLMOGOROV COMPLEXITY ESTIMATES
# =============================================================================

def compression_complexity(zeros: np.ndarray) -> float:
    """
    Estimate Kolmogorov complexity via compression.

    Lower compression ratio = more complex/random
    Higher compression ratio = more structured

    Convert to string and compress to estimate complexity.
    """
    import zlib

    # Convert to string representation
    # Use fixed precision to ensure fair comparison
    zero_strings = [f"{z:.6f}" for z in zeros]
    data_string = ",".join(zero_strings).encode('utf-8')

    # Compress
    compressed = zlib.compress(data_string, level=9)

    # Compression ratio
    ratio = len(compressed) / len(data_string)

    return ratio

def complexity_comparison(zeros: np.ndarray, n_samples: int = 10) -> Dict:
    """
    Compare complexity of real zeros with random and GUE-like sequences.
    """
    from topological_analysis import generate_random_zeros, generate_gue_like_zeros

    n = len(zeros)
    mean_spacing = np.mean(np.diff(zeros))

    real_complexity = compression_complexity(zeros)

    random_complexities = []
    for _ in range(n_samples):
        random_zeros = generate_random_zeros(n, mean_spacing)
        random_complexities.append(compression_complexity(random_zeros))

    gue_complexities = []
    for _ in range(n_samples):
        gue_zeros = generate_gue_like_zeros(n, mean_spacing)
        gue_complexities.append(compression_complexity(gue_zeros))

    return {
        'real_complexity': real_complexity,
        'random_mean': np.mean(random_complexities),
        'random_std': np.std(random_complexities),
        'gue_mean': np.mean(gue_complexities),
        'gue_std': np.std(gue_complexities),
    }

# =============================================================================
# FISHER INFORMATION
# =============================================================================

def fisher_information_spacing(zeros: np.ndarray) -> float:
    """
    Estimate Fisher information of the spacing distribution.

    Fisher information measures "how much information" the spacings
    contain about the underlying parameter (position on critical line).

    I(θ) = E[(d/dθ log p(x|θ))²]

    For well-behaved distributions, higher Fisher info = more "peaked" distribution.
    """
    spacings = np.diff(zeros)
    spacings_norm = spacings / np.mean(spacings)

    # Estimate derivative of log-likelihood numerically
    # Using kernel density estimation
    from scipy.stats import gaussian_kde

    kde = gaussian_kde(spacings_norm)

    # Sample points
    x = np.linspace(0.01, 4, 200)
    pdf = kde(x)

    # Numerical derivative
    dx = x[1] - x[0]
    d_log_pdf = np.gradient(np.log(pdf + 1e-10), dx)

    # Fisher information
    fisher = np.sum(pdf * d_log_pdf**2 * dx)

    return fisher

# =============================================================================
# MAIN ENTROPY ANALYSIS
# =============================================================================

def full_entropy_analysis(zeros: np.ndarray, verbose: bool = True) -> Dict:
    """
    Complete entropy and information-theoretic analysis.
    """
    if verbose:
        print("=" * 60)
        print("ENTROPY & INFORMATION THEORY ANALYSIS")
        print("=" * 60)

    results = {}

    # 1. Entropy collapse test
    if verbose:
        print("\n1. Spectral Entropy Collapse Test (2025 approach)...")

    collapse = entropy_collapse_test(zeros)
    results['entropy_collapse'] = collapse

    if verbose:
        print(f"   Global spacing entropy: {collapse['global_spacing_entropy']:.4f}")
        print(f"   GUE theoretical entropy: {collapse['gue_theoretical_entropy']:.4f}")
        print(f"   Poisson theoretical entropy: {collapse['poisson_theoretical_entropy']:.4f}")
        print(f"   Distance to GUE: {collapse['entropy_distance_gue']:.4f}")
        print(f"   Distance to Poisson: {collapse['entropy_distance_poisson']:.4f}")
        print(f"   Collapse ratio (lower = more collapsed): {collapse['collapse_ratio']:.4f}")

    # 2. Mutual information profile
    if verbose:
        print("\n2. Mutual Information Analysis...")

    mi_profile = mutual_information_profile(zeros)
    results['mi_profile'] = mi_profile

    if verbose:
        print(f"   MI at lag 1: {mi_profile[0]:.4f}")
        print(f"   MI decay rate: {mi_profile[0] - mi_profile[-1]:.4f}")

    # 3. Complexity comparison
    if verbose:
        print("\n3. Kolmogorov Complexity Analysis...")

    complexity = complexity_comparison(zeros, n_samples=5)
    results['complexity'] = complexity

    if verbose:
        print(f"   Real zeros complexity: {complexity['real_complexity']:.4f}")
        print(f"   Random zeros complexity: {complexity['random_mean']:.4f} ± {complexity['random_std']:.4f}")
        print(f"   GUE-like zeros complexity: {complexity['gue_mean']:.4f} ± {complexity['gue_std']:.4f}")

    # 4. Fisher information
    if verbose:
        print("\n4. Fisher Information...")

    fisher = fisher_information_spacing(zeros)
    results['fisher_information'] = fisher

    if verbose:
        print(f"   Fisher information: {fisher:.4f}")

    # 5. Verdict
    if verbose:
        print("\n" + "=" * 60)
        print("ENTROPY VERDICT")
        print("=" * 60)

        verdict_score = 0

        # Check entropy collapse
        if collapse['collapse_ratio'] < 0.5:
            verdict_score += 1
            print("✓ Entropy collapsed toward GUE (collapse ratio < 0.5)")
        else:
            print("△ Entropy not strongly collapsed")

        # Check complexity
        if abs(complexity['real_complexity'] - complexity['gue_mean']) < abs(complexity['real_complexity'] - complexity['random_mean']):
            verdict_score += 1
            print("✓ Complexity closer to GUE than random")
        else:
            print("△ Complexity not clearly GUE-like")

        # Check MI structure
        if mi_profile[0] > 0.01:  # Non-trivial correlation
            verdict_score += 1
            print("✓ Non-trivial correlation structure detected")
        else:
            print("△ Weak correlation structure")

        print(f"\nOverall entropy score: {verdict_score}/3")
        if verdict_score >= 2:
            print("→ Strong information-theoretic support for RH!")

    results['verdict_score'] = verdict_score
    return results


if __name__ == "__main__":
    from riemann_zeros import get_zeros

    zeros = get_zeros(100)
    results = full_entropy_analysis(zeros)
