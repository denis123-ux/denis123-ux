"""
ConjectureVerifier: Verify the union-closed sets conjecture on families.
"""

from typing import List, Dict, Tuple
import numpy as np
from .family import UnionClosedFamily


class ConjectureVerifier:
    """
    Verify the union-closed sets conjecture and collect statistics.
    """

    @staticmethod
    def verify_single(family: UnionClosedFamily) -> Dict:
        """
        Verify conjecture on a single family.

        Args:
            family: Union-closed family to verify

        Returns:
            Dict with verification results
        """
        # Basic checks
        is_union_closed = family.is_union_closed()
        satisfies = family.satisfies_conjecture()

        elem, min_freq = family.min_frequency()
        _, max_freq = family.max_frequency()

        stats = family.statistics()

        return {
            'is_union_closed': is_union_closed,
            'satisfies_conjecture': satisfies,
            'min_frequency': min_freq,
            'max_frequency': max_freq,
            'min_frequency_element': elem,
            'statistics': stats,
            'spectral': family.spectral_properties()
        }

    @staticmethod
    def verify_batch(families: List[UnionClosedFamily]) -> Dict:
        """
        Verify conjecture on a batch of families.

        Args:
            families: List of families to verify

        Returns:
            Aggregated results
        """
        results = {
            'total_families': len(families),
            'union_closed_count': 0,
            'satisfies_count': 0,
            'counterexample_count': 0,
            'counterexamples': [],
            'min_frequencies': [],
            'max_frequencies': [],
            'avg_statistics': {},
            'hardest_cases': []  # Families with lowest max frequency
        }

        for i, family in enumerate(families):
            result = ConjectureVerifier.verify_single(family)

            if result['is_union_closed']:
                results['union_closed_count'] += 1

                if result['satisfies_conjecture']:
                    results['satisfies_count'] += 1
                else:
                    # Potential counterexample!
                    results['counterexample_count'] += 1
                    results['counterexamples'].append({
                        'index': i,
                        'family': family.to_dict(),
                        'result': result
                    })

                results['min_frequencies'].append(result['min_frequency'])
                results['max_frequencies'].append(result['max_frequency'])

                # Track hardest cases (lowest max frequency but still > 0.5)
                if result['max_frequency'] < 0.55 and result['satisfies_conjecture']:
                    results['hardest_cases'].append({
                        'index': i,
                        'max_frequency': result['max_frequency'],
                        'family': family.to_dict()
                    })

        # Compute average statistics
        if results['min_frequencies']:
            results['avg_min_frequency'] = np.mean(results['min_frequencies'])
            results['avg_max_frequency'] = np.mean(results['max_frequencies'])
            results['std_max_frequency'] = np.std(results['max_frequencies'])

            # Sort hardest cases by max frequency
            results['hardest_cases'] = sorted(
                results['hardest_cases'],
                key=lambda x: x['max_frequency']
            )[:10]  # Keep top 10

        return results

    @staticmethod
    def exhaustive_search(max_n: int, max_size: int = None) -> Dict:
        """
        Exhaustively search for counterexamples up to size n.

        WARNING: Exponential complexity! Only feasible for small n.

        Args:
            max_n: Maximum universe size
            max_size: Maximum family size (None = no limit)

        Returns:
            Search results
        """
        from .generator import FamilyGenerator
        import itertools

        results = {
            'max_n': max_n,
            'total_checked': 0,
            'counterexamples': []
        }

        for n in range(2, max_n + 1):
            # Generate all possible families of subsets
            universe = set(range(1, n + 1))
            all_subsets = list(itertools.chain.from_iterable(
                itertools.combinations(universe, r) for r in range(n + 1)
            ))
            all_subsets = [set(s) for s in all_subsets]

            # Try all possible families
            max_family_size = len(all_subsets) if max_size is None else min(max_size, len(all_subsets))

            for family_size in range(2, max_family_size + 1):
                for sets_tuple in itertools.combinations(all_subsets, family_size):
                    sets = list(sets_tuple)

                    # Check if union-closed
                    family = UnionClosedFamily(sets)
                    if family.is_union_closed():
                        results['total_checked'] += 1

                        # Check conjecture
                        if not family.satisfies_conjecture():
                            results['counterexamples'].append(family.to_dict())

        return results

    @staticmethod
    def analyze_hardness(family: UnionClosedFamily) -> Dict:
        """
        Analyze what makes a family hard for the conjecture.

        Args:
            family: Union-closed family

        Returns:
            Hardness analysis
        """
        stats = family.statistics()
        spectral = family.spectral_properties()
        freqs = family.compute_frequencies()

        # Compute frequency distribution metrics
        freq_values = list(freqs.values())
        freq_entropy = -sum(f * np.log2(f + 1e-10) for f in freq_values if f > 0)

        # Frequency uniformity (lower = more uniform)
        freq_std = np.std(freq_values)

        return {
            'avg_set_size': stats['avg_set_size'],
            'density': stats['density'],
            'max_frequency': stats['max_frequency'],
            'min_frequency': stats['min_frequency'],
            'frequency_std': freq_std,
            'frequency_entropy': freq_entropy,
            'spectral_gap': spectral['spectral_gap'],
            'num_sets': stats['num_sets'],
            'num_elements': stats['num_elements'],
            'hardness_score': freq_std / (stats['max_frequency'] + 1e-10)  # Lower max_freq, higher uniformity = harder
        }
