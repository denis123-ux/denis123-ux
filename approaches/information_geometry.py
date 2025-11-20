"""
Information Geometry Approach to Union-Closed Sets Conjecture.

REVOLUTIONARY IDEA:
===================
Frequency distributions form a STATISTICAL MANIFOLD with Fisher metric.
Union-closure imposes geometric constraints → Curvature bounds → Frequency bounds!

Mathematical Framework:
-----------------------
1. Frequency distribution: p = (p₁,...,pₙ) where pᵢ = freq(element i)
2. Fisher Information Matrix: g_ij = E[∂log p/∂θᵢ · ∂log p/∂θⱼ]
3. Riemannian curvature from Fisher metric
4. α-connections (Amari): Interpolate exponential ↔ mixture families

Key Hypothesis:
---------------
Union-closed families → Positive curvature bound → max(p) ≥ 1/2

References:
-----------
- Amari (2016): Information Geometry and Its Applications
- Nielsen (2020): Elementary Introduction to Information Geometry
- Nakajima et al. (2022): Information Geometry on Graphs and Hypergraphs
"""

import numpy as np
from scipy.special import digamma, polygamma
from scipy.linalg import logm, expm
import matplotlib.pyplot as plt
from typing import Dict, Tuple, List
import pickle


class InformationGeometryAnalyzer:
    """
    Analyze union-closed families using information geometry.
    """

    def __init__(self, frequency_distribution: np.ndarray):
        """
        Initialize with frequency distribution.

        Args:
            frequency_distribution: Array of frequencies [p₁,...,pₙ] with Σpᵢ=1
        """
        # Normalize
        self.p = frequency_distribution / np.sum(frequency_distribution)
        self.n = len(self.p)

        # Add small epsilon for numerical stability
        self.eps = 1e-10
        self.p_safe = np.maximum(self.p, self.eps)

    def fisher_information_matrix(self) -> np.ndarray:
        """
        Compute Fisher Information Matrix for multinomial distribution.

        For multinomial: g_ij = δ_ij/p_i (diagonal)

        Returns:
            Fisher metric tensor (n×n matrix)
        """
        # For multinomial, Fisher matrix is diagonal
        g = np.diag(1.0 / self.p_safe)
        return g

    def fisher_rao_distance(self, other_dist: np.ndarray) -> float:
        """
        Compute Fisher-Rao (geodesic) distance to another distribution.

        For multinomial: d(p,q) = 2 arccos(Σ √(pᵢqᵢ))

        Args:
            other_dist: Target distribution

        Returns:
            Fisher-Rao distance
        """
        q = other_dist / np.sum(other_dist)
        q_safe = np.maximum(q, self.eps)

        # Bhattacharyya coefficient
        bc = np.sum(np.sqrt(self.p_safe * q_safe))

        # Fisher-Rao distance
        distance = 2.0 * np.arccos(np.clip(bc, 0, 1))

        return distance

    def ricci_curvature_scalar(self) -> float:
        """
        Compute scalar curvature of statistical manifold.

        For multinomial distribution on simplex:
        K = -(n-1)/2 · H(p) where H = harmonic mean

        Returns:
            Scalar curvature
        """
        # Harmonic mean: H = n / Σ(1/pᵢ)
        harmonic_mean = self.n / np.sum(1.0 / self.p_safe)

        # Scalar curvature (negative for probability simplex)
        K = -(self.n - 1) / 2.0 * harmonic_mean

        return K

    def sectional_curvature(self, i: int, j: int) -> float:
        """
        Compute sectional curvature in plane spanned by eᵢ, eⱼ.

        For multinomial: K(i,j) = -1/(4√(pᵢpⱼ))

        Args:
            i, j: Indices of basis vectors

        Returns:
            Sectional curvature K(eᵢ ∧ eⱼ)
        """
        if i == j:
            return 0.0

        K_ij = -1.0 / (4.0 * np.sqrt(self.p_safe[i] * self.p_safe[j]))

        return K_ij

    def alpha_divergence(self, other_dist: np.ndarray, alpha: float = 1.0) -> float:
        """
        Compute α-divergence (generalized KL divergence).

        D_α(p||q) = (4/(1-α²)) [1 - Σ pᵢ^((1+α)/2) qᵢ^((1-α)/2)]

        Special cases:
        - α=1: KL divergence
        - α=-1: Reverse KL
        - α=0: Hellinger distance

        Args:
            other_dist: Target distribution
            alpha: α parameter

        Returns:
            α-divergence
        """
        q = other_dist / np.sum(other_dist)
        q_safe = np.maximum(q, self.eps)

        if abs(alpha - 1.0) < 1e-6:
            # KL divergence (limit as α→1)
            return np.sum(self.p_safe * np.log(self.p_safe / q_safe))

        elif abs(alpha + 1.0) < 1e-6:
            # Reverse KL (limit as α→-1)
            return np.sum(q_safe * np.log(q_safe / self.p_safe))

        elif abs(alpha) < 1e-6:
            # Hellinger distance (α=0)
            return 2.0 * np.sum((np.sqrt(self.p_safe) - np.sqrt(q_safe))**2)

        else:
            # General α-divergence
            exp_p = (1.0 + alpha) / 2.0
            exp_q = (1.0 - alpha) / 2.0

            integral = np.sum(self.p_safe**exp_p * q_safe**exp_q)
            D_alpha = (4.0 / (1.0 - alpha**2)) * (1.0 - integral)

            return D_alpha

    def entropy_connection(self) -> float:
        """
        Shannon entropy (related to potential function of Fisher metric).

        H(p) = -Σ pᵢ log pᵢ

        Returns:
            Shannon entropy
        """
        return -np.sum(self.p_safe * np.log(self.p_safe))

    def riemannian_volume_element(self) -> float:
        """
        Volume element √det(g) of Fisher metric.

        For multinomial: √det(g) = 1/√(∏pᵢ)

        Returns:
            Volume element
        """
        det_g = np.prod(1.0 / self.p_safe)
        return np.sqrt(det_g)

    def mean_curvature(self) -> float:
        """
        Mean of sectional curvatures (proxy for scalar curvature).

        Returns:
            Mean sectional curvature
        """
        curvatures = []
        for i in range(self.n):
            for j in range(i+1, self.n):
                K_ij = self.sectional_curvature(i, j)
                curvatures.append(K_ij)

        return np.mean(curvatures) if curvatures else 0.0

    def information_radius(self, other_dist: np.ndarray) -> float:
        """
        Information radius: Jensen-Shannon divergence.

        IR(p,q) = (D_KL(p||m) + D_KL(q||m))/2 where m=(p+q)/2

        Args:
            other_dist: Target distribution

        Returns:
            Information radius
        """
        q = other_dist / np.sum(other_dist)
        m = (self.p + q) / 2.0

        D_p_m = np.sum(self.p_safe * np.log(self.p_safe / np.maximum(m, self.eps)))
        D_q_m = np.sum(q * np.log(q / np.maximum(m, self.eps)))

        return (D_p_m + D_q_m) / 2.0

    def geometric_statistics(self) -> Dict:
        """
        Compute all geometric statistics.

        Returns:
            Dict with all information-geometric quantities
        """
        # Distance to uniform distribution
        uniform = np.ones(self.n) / self.n
        fisher_rao_dist = self.fisher_rao_distance(uniform)

        # Divergences
        kl_div = self.alpha_divergence(uniform, alpha=1.0)
        reverse_kl = self.alpha_divergence(uniform, alpha=-1.0)
        hellinger = self.alpha_divergence(uniform, alpha=0.0)

        return {
            'scalar_curvature': self.ricci_curvature_scalar(),
            'mean_sectional_curvature': self.mean_curvature(),
            'shannon_entropy': self.entropy_connection(),
            'fisher_rao_distance_to_uniform': fisher_rao_dist,
            'kl_divergence_to_uniform': kl_div,
            'reverse_kl_to_uniform': reverse_kl,
            'hellinger_distance_to_uniform': hellinger,
            'volume_element': self.riemannian_volume_element()
        }


def test_information_geometry_hypothesis(results_path: str = 'results/final_500/results_full.pkl'):
    """
    Test hypothesis: Curvature bounds → max_frequency bounds.

    Returns:
        Analysis results
    """
    print("=" * 80)
    print("INFORMATION GEOMETRY ANALYSIS")
    print("Union-Closed Sets as Statistical Manifolds")
    print("=" * 80)
    print()

    # Load results
    with open(results_path, 'rb') as f:
        results = pickle.load(f)

    families = [f for f in results['families'] if not f.get('skip', False) and 'error' not in f]

    # Analyze each family
    geometric_data = []

    for family in families:
        # Get frequency distribution
        freqs = family['frequencies']['all']
        if len(freqs) == 0:
            continue

        freqs = np.array(freqs)
        freqs = freqs / np.sum(freqs)  # Normalize

        # Information geometry analysis
        iga = InformationGeometryAnalyzer(freqs)
        geo_stats = iga.geometric_statistics()

        # Add to data
        geo_stats['max_frequency'] = family['frequencies']['max']
        geo_stats['min_frequency'] = family['frequencies']['min']
        geo_stats['n_elements'] = family['basic']['n']
        geo_stats['n_sets'] = family['basic']['m']

        geometric_data.append(geo_stats)

    # Convert to arrays for analysis
    curvatures = np.array([d['scalar_curvature'] for d in geometric_data])
    mean_sect_curvatures = np.array([d['mean_sectional_curvature'] for d in geometric_data])
    max_freqs = np.array([d['max_frequency'] for d in geometric_data])
    fisher_rao_dists = np.array([d['fisher_rao_distance_to_uniform'] for d in geometric_data])
    kl_divs = np.array([d['kl_divergence_to_uniform'] for d in geometric_data])
    entropies = np.array([d['shannon_entropy'] for d in geometric_data])

    # Test correlations
    print("CORRELATION ANALYSIS:")
    print("-" * 80)

    correlations = {
        'Scalar Curvature ↔ Max Freq': np.corrcoef(curvatures, max_freqs)[0, 1],
        'Mean Sectional Curvature ↔ Max Freq': np.corrcoef(mean_sect_curvatures, max_freqs)[0, 1],
        'Fisher-Rao Distance ↔ Max Freq': np.corrcoef(fisher_rao_dists, max_freqs)[0, 1],
        'KL Divergence ↔ Max Freq': np.corrcoef(kl_divs, max_freqs)[0, 1],
        'Shannon Entropy ↔ Max Freq': np.corrcoef(entropies, max_freqs)[0, 1]
    }

    for name, corr in correlations.items():
        print(f"  {name}: {corr:+.4f}")

    print()
    print("STATISTICS:")
    print("-" * 80)
    print(f"Scalar Curvature:  μ={np.mean(curvatures):.4f}, σ={np.std(curvatures):.4f}")
    print(f"Sectional Curvature: μ={np.mean(mean_sect_curvatures):.4f}, σ={np.std(mean_sect_curvatures):.4f}")
    print(f"Fisher-Rao Dist:   μ={np.mean(fisher_rao_dists):.4f}, σ={np.std(fisher_rao_dists):.4f}")
    print(f"KL Divergence:     μ={np.mean(kl_divs):.4f}, σ={np.std(kl_divs):.4f}")
    print()

    # Quartile analysis
    print("MAX FREQUENCY BY CURVATURE QUARTILES:")
    print("-" * 80)

    curvature_quartiles = np.percentile(curvatures, [0, 25, 50, 75, 100])

    for i in range(len(curvature_quartiles) - 1):
        mask = (curvatures >= curvature_quartiles[i]) & (curvatures < curvature_quartiles[i+1])
        if mask.sum() > 0:
            print(f"  K ∈ [{curvature_quartiles[i]:.4f}, {curvature_quartiles[i+1]:.4f}]: "
                  f"max_freq = {max_freqs[mask].mean():.4f} ± {max_freqs[mask].std():.4f}")

    print()

    # Test critical hypothesis
    print("CRITICAL HYPOTHESIS TEST:")
    print("-" * 80)
    print("H₀: High curvature (less negative) → High max_frequency")
    print()

    # Split by median curvature
    median_K = np.median(curvatures)
    high_curvature = curvatures > median_K
    low_curvature = curvatures <= median_K

    print(f"High curvature (K > {median_K:.4f}):")
    print(f"  Mean max_freq: {max_freqs[high_curvature].mean():.4f}")
    print(f"  Min max_freq:  {max_freqs[high_curvature].min():.4f}")
    print()
    print(f"Low curvature (K ≤ {median_K:.4f}):")
    print(f"  Mean max_freq: {max_freqs[low_curvature].mean():.4f}")
    print(f"  Min max_freq:  {max_freqs[low_curvature].min():.4f}")
    print()

    # T-test
    from scipy import stats as scipy_stats
    t_stat, p_value = scipy_stats.ttest_ind(max_freqs[high_curvature], max_freqs[low_curvature])

    print(f"T-test: t={t_stat:.4f}, p={p_value:.6f}")
    if p_value < 0.05:
        print("  ✅ SIGNIFICANT difference!")
    else:
        print("  ❌ Not significant")

    print()

    # Save results
    output = {
        'geometric_data': geometric_data,
        'correlations': correlations,
        'statistics': {
            'curvature_mean': float(np.mean(curvatures)),
            'curvature_std': float(np.std(curvatures)),
            'fisher_rao_mean': float(np.mean(fisher_rao_dists)),
            'kl_div_mean': float(np.mean(kl_divs))
        }
    }

    return output


if __name__ == "__main__":
    results = test_information_geometry_hypothesis()

    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("Information geometry provides a NEW LENS for union-closed sets!")
    print()
    print("Next steps:")
    print("1. Formalize curvature bound → frequency bound theorem")
    print("2. Study union-closure constraints on statistical manifold")
    print("3. Apply Amari α-connections")
    print("4. Explore geodesics in frequency space")
    print()
    print("=" * 80)
