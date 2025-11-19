"""
UnionClosedFamily: Core class for representing and manipulating union-closed families.
"""

from typing import Set, FrozenSet, List, Dict, Tuple
import numpy as np
from collections import Counter


class UnionClosedFamily:
    """
    Represents a union-closed family of sets.

    A family F is union-closed if for any A, B in F, A ∪ B is also in F.
    """

    def __init__(self, sets: List[Set[int]] = None):
        """
        Initialize a union-closed family.

        Args:
            sets: List of sets (will be converted to frozensets internally)
        """
        if sets is None:
            sets = [set()]

        # Store as frozensets for hashability
        self.sets: Set[FrozenSet[int]] = {frozenset(s) for s in sets}

        # Compute universe (all elements appearing)
        self.universe: Set[int] = set()
        for s in self.sets:
            self.universe.update(s)

        self.n = len(self.universe)  # Number of elements in universe
        self.m = len(self.sets)      # Number of sets in family

        # Cache for frequently computed properties
        self._frequencies = None
        self._is_union_closed = None
        self._adjacency_matrix = None

    def __repr__(self):
        return f"UnionClosedFamily(n={self.n}, m={self.m})"

    def __len__(self):
        return self.m

    def add_set(self, s: Set[int]):
        """Add a set to the family (invalidates caches)."""
        fs = frozenset(s)
        if fs not in self.sets:
            self.sets.add(fs)
            self.universe.update(s)
            self.n = len(self.universe)
            self.m = len(self.sets)
            self._invalidate_cache()

    def _invalidate_cache(self):
        """Invalidate cached computations."""
        self._frequencies = None
        self._is_union_closed = None
        self._adjacency_matrix = None

    def is_union_closed(self) -> bool:
        """
        Check if the family is union-closed.

        Returns:
            True if ∀A,B ∈ F: A ∪ B ∈ F
        """
        if self._is_union_closed is not None:
            return self._is_union_closed

        sets_list = list(self.sets)
        for i, A in enumerate(sets_list):
            for j in range(i, len(sets_list)):
                B = sets_list[j]
                union = A | B
                if union not in self.sets:
                    self._is_union_closed = False
                    return False

        self._is_union_closed = True
        return True

    def compute_frequencies(self) -> Dict[int, float]:
        """
        Compute frequency of each element (proportion of sets containing it).

        Returns:
            Dict mapping element -> frequency (in [0,1])
        """
        if self._frequencies is not None:
            return self._frequencies

        if self.m == 0:
            self._frequencies = {}
            return self._frequencies

        counts = Counter()
        for s in self.sets:
            for elem in s:
                counts[elem] += 1

        self._frequencies = {
            elem: count / self.m
            for elem, count in counts.items()
        }

        return self._frequencies

    def min_frequency(self) -> Tuple[int, float]:
        """
        Find the element with minimum frequency.

        Returns:
            (element, frequency) tuple
        """
        freqs = self.compute_frequencies()
        if not freqs:
            return (None, 0.0)

        min_elem = min(freqs.items(), key=lambda x: x[1])
        return min_elem

    def max_frequency(self) -> Tuple[int, float]:
        """
        Find the element with maximum frequency.

        Returns:
            (element, frequency) tuple
        """
        freqs = self.compute_frequencies()
        if not freqs:
            return (None, 0.0)

        max_elem = max(freqs.items(), key=lambda x: x[1])
        return max_elem

    def satisfies_conjecture(self) -> bool:
        """
        Check if the family satisfies the union-closed conjecture.

        Returns:
            True if ∃ element with frequency ≥ 0.5
        """
        if self.m <= 1:  # Trivial cases
            return True

        _, min_freq = self.min_frequency()
        _, max_freq = self.max_frequency()

        # Conjecture: max_freq >= 0.5
        return max_freq >= 0.5

    def to_matrix(self) -> np.ndarray:
        """
        Convert family to binary incidence matrix.

        Returns:
            Binary matrix M where M[i,j] = 1 if element j is in set i
            Shape: (m, n)
        """
        if not self.universe:
            return np.zeros((self.m, 0))

        # Create mapping from elements to indices
        elem_to_idx = {elem: idx for idx, elem in enumerate(sorted(self.universe))}

        # Build matrix
        matrix = np.zeros((self.m, self.n), dtype=int)
        for i, s in enumerate(sorted(self.sets, key=lambda x: (len(x), sorted(x)))):
            for elem in s:
                matrix[i, elem_to_idx[elem]] = 1

        return matrix

    def to_adjacency_matrix(self) -> np.ndarray:
        """
        Build adjacency matrix for the "union graph".

        Returns:
            Matrix A where A[i,j] = index of set_i ∪ set_j in family
            Shape: (m, m)
        """
        if self._adjacency_matrix is not None:
            return self._adjacency_matrix

        sets_list = list(self.sets)
        set_to_idx = {s: idx for idx, s in enumerate(sets_list)}

        adj = np.zeros((self.m, self.m), dtype=int)
        for i, A in enumerate(sets_list):
            for j, B in enumerate(sets_list):
                union = A | B
                if union in self.sets:
                    adj[i, j] = set_to_idx[union]

        self._adjacency_matrix = adj
        return adj

    def spectral_properties(self) -> Dict[str, float]:
        """
        Compute spectral properties of the incidence matrix.

        Returns:
            Dict with eigenvalues, singular values, etc.
        """
        M = self.to_matrix()

        if M.size == 0:
            return {
                'largest_eigenvalue': 0,
                'spectral_gap': 0,
                'largest_singular_value': 0,
                'trace': 0,
                'frobenius_norm': 0
            }

        # Compute eigenvalues of M^T M (symmetric, positive semidefinite)
        MTM = M.T @ M
        eigenvalues = np.linalg.eigvalsh(MTM)
        eigenvalues = np.sort(eigenvalues)[::-1]  # Descending order

        # Singular values
        singular_values = np.sqrt(np.maximum(eigenvalues, 0))

        return {
            'largest_eigenvalue': float(eigenvalues[0]) if len(eigenvalues) > 0 else 0,
            'spectral_gap': float(eigenvalues[0] - eigenvalues[1]) if len(eigenvalues) > 1 else 0,
            'largest_singular_value': float(singular_values[0]) if len(singular_values) > 0 else 0,
            'trace': float(np.trace(MTM)),
            'frobenius_norm': float(np.linalg.norm(M, 'fro'))
        }

    def statistics(self) -> Dict[str, float]:
        """
        Compute comprehensive statistics of the family.

        Returns:
            Dict with various statistics
        """
        if self.m == 0:
            return {
                'num_sets': 0,
                'num_elements': 0,
                'avg_set_size': 0,
                'min_set_size': 0,
                'max_set_size': 0,
                'density': 0,
                'min_frequency': 0,
                'max_frequency': 0,
                'avg_frequency': 0
            }

        set_sizes = [len(s) for s in self.sets]
        freqs = self.compute_frequencies()
        freq_values = list(freqs.values()) if freqs else [0]

        return {
            'num_sets': self.m,
            'num_elements': self.n,
            'avg_set_size': np.mean(set_sizes),
            'min_set_size': min(set_sizes),
            'max_set_size': max(set_sizes),
            'density': np.mean(set_sizes) / max(self.n, 1),
            'min_frequency': min(freq_values),
            'max_frequency': max(freq_values),
            'avg_frequency': np.mean(freq_values)
        }

    def to_dict(self) -> Dict:
        """Export family to dictionary format."""
        return {
            'sets': [sorted(list(s)) for s in self.sets],
            'universe': sorted(list(self.universe)),
            'is_union_closed': self.is_union_closed(),
            'satisfies_conjecture': self.satisfies_conjecture(),
            'statistics': self.statistics()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'UnionClosedFamily':
        """Create family from dictionary format."""
        return cls([set(s) for s in data['sets']])
