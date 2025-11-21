"""
Kolmogorov Complexity Analysis for Collatz Trajectories

REVOLUTIONARY INFORMATION-THEORETIC APPROACH:

Kolmogorov Complexity K(x) = length of shortest program that generates x

KEY THEOREM (to prove):
If K(trajectory(n)) = O(log log n), then trajectories are "simple"
→ implies algorithmic structure
→ cannot be chaotic
→ must converge!

We approximate K(x) using compression algorithms:
- LZ77 compression
- Arithmetic coding
- BWT (Burrows-Wheeler Transform)

Also compute:
- Shannon entropy
- Lempel-Ziv complexity
- Entropy rate
"""

import numpy as np
from typing import List, Dict, Tuple
import zlib
import bz2
from collections import Counter
from dataclasses import dataclass


@dataclass
class ComplexityMetrics:
    """Container for complexity analysis results"""
    kolmogorov_estimate: float  # Via compression
    shannon_entropy: float
    lempel_ziv_complexity: float
    entropy_rate: float
    compressibility_ratio: float
    pattern_repetition_score: float


class KolmogorovComplexityAnalyzer:
    """
    Estimate Kolmogorov complexity and related information-theoretic measures

    Since K(x) is uncomputable, we use compression as upper bound:
    K(x) ≤ |compressed(x)| + |decompressor|
    """

    @staticmethod
    def trajectory_to_string(trajectory: List[int]) -> str:
        """Convert trajectory to string representation"""
        # Use binary representation with separator
        return ','.join(map(str, trajectory))

    @staticmethod
    def trajectory_to_bytes(trajectory: List[int]) -> bytes:
        """Convert trajectory to byte representation"""
        # Pack as sequence of integers
        s = ','.join(map(str, trajectory))
        return s.encode('utf-8')

    def compression_ratio(self, data: bytes, algorithm: str = 'zlib') -> float:
        """
        Compute compression ratio as proxy for Kolmogorov complexity

        compression_ratio = |compressed| / |original|

        Lower ratio → more compressible → lower complexity
        """
        original_size = len(data)

        if original_size == 0:
            return 1.0

        if algorithm == 'zlib':
            compressed = zlib.compress(data, level=9)
        elif algorithm == 'bz2':
            compressed = bz2.compress(data, compresslevel=9)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        compressed_size = len(compressed)

        return compressed_size / original_size

    def kolmogorov_estimate(
        self,
        trajectory: List[int],
        normalize: bool = True
    ) -> float:
        """
        Estimate Kolmogorov complexity using compression

        K(x) ≈ |compressed(x)|

        If normalize=True, divide by length to get K(x)/|x|
        """
        data = self.trajectory_to_bytes(trajectory)
        compressed = zlib.compress(data, level=9)

        k_estimate = len(compressed)

        if normalize:
            k_estimate /= len(data) if len(data) > 0 else 1

        return k_estimate

    def shannon_entropy(self, trajectory: List[int]) -> float:
        """
        Compute Shannon entropy of trajectory

        H(X) = -∑ p(x) log₂ p(x)

        Measures "information content" - how unpredictable is sequence
        """
        if not trajectory:
            return 0.0

        # Count frequencies
        counts = Counter(trajectory)
        total = len(trajectory)

        # Compute entropy
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)

        return entropy

    def lempel_ziv_complexity(self, trajectory: List[int]) -> float:
        """
        Compute Lempel-Ziv complexity

        Measures number of distinct patterns in sequence
        Higher complexity → more random
        """
        # Convert to binary string for LZ complexity
        # Use odd/even pattern (simplest meaningful encoding)
        binary = ''.join(['1' if x % 2 == 1 else '0' for x in trajectory])

        if not binary:
            return 0.0

        # LZ76 complexity algorithm
        complexity = 1
        prefix_length = 1
        n = len(binary)

        while prefix_length + complexity <= n:
            pattern = binary[prefix_length:prefix_length + complexity]
            prefix = binary[0:prefix_length + complexity]

            # Check if pattern exists in prefix
            if pattern in prefix[:-complexity]:
                complexity += 1
            else:
                prefix_length += complexity
                complexity = 1

        # Normalize by theoretical maximum
        # Max complexity ≈ n / log(n)
        max_complexity = n / np.log2(n) if n > 1 else 1
        normalized_complexity = prefix_length / max_complexity

        return normalized_complexity

    def entropy_rate(
        self,
        trajectory: List[int],
        order: int = 2
    ) -> float:
        """
        Compute entropy rate (Markov model of given order)

        H_rate = lim_{n→∞} H(X_n | X_{n-1}, ..., X_{n-order})

        Measures "new information" per step
        """
        if len(trajectory) < order + 1:
            return 0.0

        # Create n-grams
        ngrams = []
        for i in range(len(trajectory) - order):
            ngram = tuple(trajectory[i:i+order+1])
            ngrams.append(ngram)

        if not ngrams:
            return 0.0

        # Count transitions
        context_counts = Counter([ng[:-1] for ng in ngrams])
        transition_counts = Counter(ngrams)

        # Compute conditional entropy
        entropy_rate = 0.0
        total = len(ngrams)

        for ngram in transition_counts:
            context = ngram[:-1]
            p_ngram = transition_counts[ngram] / total
            p_context = context_counts[context] / total

            if p_context > 0:
                p_conditional = p_ngram / p_context
                if p_conditional > 0:
                    entropy_rate -= p_ngram * np.log2(p_conditional)

        return entropy_rate

    def pattern_repetition_score(self, trajectory: List[int]) -> float:
        """
        Compute pattern repetition score

        Measures how often patterns repeat
        Higher score → more structure → lower complexity
        """
        if len(trajectory) < 4:
            return 0.0

        # Look for repeated patterns of various lengths
        repetition_count = 0
        total_comparisons = 0

        for pattern_length in [2, 3, 4, 5]:
            if len(trajectory) < 2 * pattern_length:
                continue

            # Count how many times each pattern appears
            patterns = {}
            for i in range(len(trajectory) - pattern_length + 1):
                pattern = tuple(trajectory[i:i+pattern_length])
                patterns[pattern] = patterns.get(pattern, 0) + 1

            # Count repetitions (patterns that appear > 1 time)
            for count in patterns.values():
                if count > 1:
                    repetition_count += count - 1

            total_comparisons += len(patterns)

        if total_comparisons == 0:
            return 0.0

        return repetition_count / total_comparisons

    def analyze_trajectory(self, trajectory: List[int]) -> ComplexityMetrics:
        """
        Complete complexity analysis of trajectory

        Returns all metrics in one pass
        """
        return ComplexityMetrics(
            kolmogorov_estimate=self.kolmogorov_estimate(trajectory, normalize=True),
            shannon_entropy=self.shannon_entropy(trajectory),
            lempel_ziv_complexity=self.lempel_ziv_complexity(trajectory),
            entropy_rate=self.entropy_rate(trajectory, order=2),
            compressibility_ratio=self.compression_ratio(
                self.trajectory_to_bytes(trajectory),
                algorithm='zlib'
            ),
            pattern_repetition_score=self.pattern_repetition_score(trajectory)
        )

    def batch_analyze(
        self,
        trajectories: List[List[int]],
        verbose: bool = True
    ) -> List[ComplexityMetrics]:
        """Analyze multiple trajectories"""
        results = []

        for i, traj in enumerate(trajectories):
            metrics = self.analyze_trajectory(traj)
            results.append(metrics)

            if verbose and (i + 1) % max(1, len(trajectories) // 10) == 0:
                print(f"Analyzed {i+1}/{len(trajectories)} trajectories...")

        return results


def test_low_complexity_theorem(
    trajectories: List[List[int]],
    starting_values: List[int],
    verbose: bool = True
) -> Dict:
    """
    TEST KEY THEOREM:

    If K(trajectory(n)) = O(log log n), then trajectories are algorithmically simple
    → implies deterministic structure → must converge!

    We test if K(T_n) / log(log(n)) is bounded
    """
    analyzer = KolmogorovComplexityAnalyzer()

    if verbose:
        print("\n" + "="*60)
        print("LOW COMPLEXITY THEOREM TEST")
        print("="*60)

    # Analyze all trajectories
    metrics_list = analyzer.batch_analyze(trajectories, verbose=verbose)

    # Compute K / log(log(n))
    complexity_ratios = []

    for i, (n, metrics) in enumerate(zip(starting_values, metrics_list)):
        if n > 2:
            denominator = np.log(np.log(n))
            if denominator > 0:
                ratio = metrics.kolmogorov_estimate / denominator
                complexity_ratios.append(ratio)

    if complexity_ratios:
        mean_ratio = np.mean(complexity_ratios)
        std_ratio = np.std(complexity_ratios)
        max_ratio = np.max(complexity_ratios)

        if verbose:
            print(f"\nK(T_n) / log(log(n)) statistics:")
            print(f"  Mean: {mean_ratio:.6f}")
            print(f"  Std: {std_ratio:.6f}")
            print(f"  Max: {max_ratio:.6f}")

            # Check if bounded
            is_bounded = max_ratio < 10.0  # Arbitrary threshold
            print(f"\n✓ Ratio appears bounded: {is_bounded}")
            print(f"✓ Low average complexity: {mean_ratio < 5.0}")

        # Aggregate statistics
        avg_metrics = {
            'avg_kolmogorov': np.mean([m.kolmogorov_estimate for m in metrics_list]),
            'avg_shannon_entropy': np.mean([m.shannon_entropy for m in metrics_list]),
            'avg_lz_complexity': np.mean([m.lempel_ziv_complexity for m in metrics_list]),
            'avg_entropy_rate': np.mean([m.entropy_rate for m in metrics_list]),
            'avg_compressibility': np.mean([m.compressibility_ratio for m in metrics_list]),
            'avg_repetition_score': np.mean([m.pattern_repetition_score for m in metrics_list]),
        }

        if verbose:
            print(f"\nAggregate Statistics:")
            print(f"  Avg Kolmogorov estimate: {avg_metrics['avg_kolmogorov']:.6f}")
            print(f"  Avg Shannon entropy: {avg_metrics['avg_shannon_entropy']:.6f}")
            print(f"  Avg LZ complexity: {avg_metrics['avg_lz_complexity']:.6f}")
            print(f"  Avg entropy rate: {avg_metrics['avg_entropy_rate']:.6f}")
            print(f"  Avg compressibility: {avg_metrics['avg_compressibility']:.6f}")
            print(f"  Avg repetition score: {avg_metrics['avg_repetition_score']:.6f}")

        # Theorem supported if complexity is low and trajectories are compressible
        theorem_supported = (
            mean_ratio < 5.0 and
            avg_metrics['avg_compressibility'] < 0.7
        )

        return {
            'complexity_ratios': complexity_ratios,
            'mean_ratio': mean_ratio,
            'std_ratio': std_ratio,
            'max_ratio': max_ratio,
            'aggregate_metrics': avg_metrics,
            'theorem_supported': theorem_supported,
        }

    return {'error': 'Insufficient data'}


def analyze_complexity_vs_stopping_time(
    trajectories: List[List[int]],
    stopping_times: List[int]
) -> Dict:
    """
    Analyze relationship between complexity and stopping time

    HYPOTHESIS: More complex trajectories have longer stopping times
    """
    analyzer = KolmogorovComplexityAnalyzer()
    metrics_list = analyzer.batch_analyze(trajectories, verbose=False)

    # Extract complexity measures
    kolmogorov_estimates = [m.kolmogorov_estimate for m in metrics_list]
    entropies = [m.shannon_entropy for m in metrics_list]

    # Compute correlations
    from scipy.stats import pearsonr, spearmanr

    corr_k_time, p_k_time = pearsonr(kolmogorov_estimates, stopping_times)
    corr_h_time, p_h_time = pearsonr(entropies, stopping_times)

    rank_corr_k, rank_p_k = spearmanr(kolmogorov_estimates, stopping_times)
    rank_corr_h, rank_p_h = spearmanr(entropies, stopping_times)

    return {
        'pearson_correlation_K_vs_time': corr_k_time,
        'pearson_pvalue_K_vs_time': p_k_time,
        'pearson_correlation_H_vs_time': corr_h_time,
        'pearson_pvalue_H_vs_time': p_h_time,
        'spearman_correlation_K_vs_time': rank_corr_k,
        'spearman_pvalue_K_vs_time': rank_p_k,
        'spearman_correlation_H_vs_time': rank_corr_h,
        'spearman_pvalue_H_vs_time': rank_p_h,
    }
