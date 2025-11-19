"""
Tensor Network (MPS/PEPS) approach to Union-Closed Sets Conjecture.

CORE IDEA:
----------
Represent union-closed family as a tensor network:
- Each set S = {x₁, ..., xₖ} ⊆ {1,...,n} → tensor T^{i₁...iₙ}
  where iⱼ ∈ {0,1} (0 = not in set, 1 = in set)
- Family F = collection of tensors
- Union operation → tensor contraction/addition

MATRIX PRODUCT STATE (MPS):
---------------------------
Decompose family tensor as:

T^{i₁...iₙ} = ∑_{α₁...αₙ₋₁} A¹[i₁]_{α₁} A²[i₂]_{α₁α₂} ... Aⁿ[iₙ]_{αₙ₋₁}

where:
- A^k[iₖ] are (χₖ₋₁ × χₖ) matrices
- χₖ = bond dimension at site k
- max χₖ = entanglement across bipartition

ENTANGLEMENT ENTROPY:
---------------------
For bipartition {1,...,k} | {k+1,...,n}:
S_k = -∑ᵢ λᵢ² log(λᵢ²)

where λᵢ are singular values of reshaped tensor.

CONJECTURE CONNECTION:
----------------------
Hypothesis: Union-closed families have bounded entanglement entropy.
High entanglement ⇒ complex correlations ⇒ frequencies can't be too uniform
⇒ max frequency ≥ 1/2

KEY QUANTITIES:
---------------
1. Bond dimension χ: Complexity of representation
2. Entanglement entropy S: Information across cuts
3. Schmidt rank: Number of significant singular values
4. Area law: S ~ boundary (for local Hamiltonians)

For union-closed families, we expect:
- Bounded bond dimension (families have structure)
- Sub-maximal entanglement (correlations constrained)
- This limits how "spread out" frequencies can be
"""

import numpy as np
from scipy.linalg import svd
from typing import List, Dict, Tuple
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.family import UnionClosedFamily


class TensorNetworkApproach:
    """
    Tensor network approach to union-closed sets conjecture.
    """

    def __init__(self, family: UnionClosedFamily):
        """
        Initialize tensor network approach.

        Args:
            family: Union-closed family
        """
        self.family = family
        self.n = family.n
        self.m = family.m

        # Build element ordering
        self.elem_order = sorted(list(family.universe))
        self.elem_to_idx = {elem: idx for idx, elem in enumerate(self.elem_order)}

        # Tensor representation
        self._family_tensor = None
        self._mps_decomposition = None

    def to_tensor(self) -> np.ndarray:
        """
        Convert family to tensor representation.

        Returns tensor T of shape (m, 2, 2, ..., 2) where:
        - First dimension indexes sets in family
        - Remaining n dimensions are binary (element in/out)

        Returns:
            Family tensor
        """
        if self._family_tensor is not None:
            return self._family_tensor

        if self.n == 0:
            return np.zeros((self.m, 1))

        # Shape: (m, 2^n) but represented as (m, 2, 2, ..., 2)
        shape = (self.m,) + (2,) * self.n
        tensor = np.zeros(shape)

        for set_idx, S in enumerate(sorted(self.family.sets, key=lambda x: (len(x), tuple(sorted(x))))):
            # Build index tuple
            indices = [set_idx]
            for elem in self.elem_order:
                indices.append(1 if elem in S else 0)

            tensor[tuple(indices)] = 1.0

        self._family_tensor = tensor
        return tensor

    def to_matrix_form(self) -> np.ndarray:
        """
        Convert family to matrix form (m × 2^n).

        Each row = one set, each column = one possible element configuration.

        Returns:
            Matrix of shape (m, 2^n)
        """
        tensor = self.to_tensor()

        # Reshape from (m, 2, 2, ..., 2) to (m, 2^n)
        matrix = tensor.reshape(self.m, 2 ** self.n)

        return matrix

    def compute_entanglement_entropy(self, cut_position: int) -> float:
        """
        Compute entanglement entropy across bipartition at position k.

        Bipartition: {1,...,k} | {k+1,...,n}

        Args:
            cut_position: Position k where to cut (1 ≤ k < n)

        Returns:
            Entanglement entropy S_k
        """
        if cut_position < 1 or cut_position >= self.n:
            return 0.0

        tensor = self.to_tensor()

        # Reshape into matrix for bipartition
        # Left: dimensions [0, 1, ..., cut_position]
        # Right: dimensions [cut_position+1, ..., n]

        left_dims = (self.m,) + (2,) * cut_position
        right_dims = (2,) * (self.n - cut_position)

        left_size = np.prod(left_dims)
        right_size = np.prod(right_dims)

        # Reshape tensor
        matrix = tensor.reshape(left_size, right_size)

        # Compute SVD
        U, s, Vt = svd(matrix, full_matrices=False)

        # Normalize singular values to get Schmidt coefficients
        s_normalized = s / (np.linalg.norm(s) + 1e-15)

        # Compute entanglement entropy
        entropy = 0.0
        for si in s_normalized:
            if si > 1e-15:
                entropy -= si**2 * np.log(si**2)

        return entropy

    def entanglement_profile(self) -> List[float]:
        """
        Compute entanglement entropy across all cuts.

        Returns:
            List of entropies [S_1, S_2, ..., S_{n-1}]
        """
        if self.n <= 1:
            return []

        profile = []
        for k in range(1, self.n):
            S_k = self.compute_entanglement_entropy(k)
            profile.append(S_k)

        return profile

    def bond_dimension(self, cut_position: int, threshold: float = 1e-10) -> int:
        """
        Compute bond dimension χ_k at cut position k.

        Bond dimension = number of significant singular values.

        Args:
            cut_position: Position k where to cut
            threshold: Threshold for "significant" singular value

        Returns:
            Bond dimension χ_k
        """
        if cut_position < 1 or cut_position >= self.n:
            return 1

        tensor = self.to_tensor()

        # Reshape for bipartition
        left_size = self.m * (2 ** cut_position)
        right_size = 2 ** (self.n - cut_position)

        matrix = tensor.reshape(left_size, right_size)

        # Compute singular values
        U, s, Vt = svd(matrix, full_matrices=False)

        # Count significant singular values
        chi = np.sum(s > threshold)

        return int(chi)

    def bond_dimensions(self, threshold: float = 1e-10) -> List[int]:
        """
        Compute bond dimensions across all cuts.

        Returns:
            List [χ_1, χ_2, ..., χ_{n-1}]
        """
        if self.n <= 1:
            return []

        dims = []
        for k in range(1, self.n):
            chi_k = self.bond_dimension(k, threshold)
            dims.append(chi_k)

        return dims

    def mps_decomposition(self, max_bond_dim: int = None) -> List[np.ndarray]:
        """
        Decompose family tensor into Matrix Product State form.

        Returns list of tensors [A¹, A², ..., Aⁿ] where
        A^k has shape (χ_{k-1}, 2, χ_k).

        Args:
            max_bond_dim: Maximum bond dimension (for compression)

        Returns:
            List of MPS tensors
        """
        if self._mps_decomposition is not None:
            return self._mps_decomposition

        if self.n == 0:
            return []

        tensor = self.to_tensor()

        # Sequential SVD decomposition (left-to-right)
        mps_tensors = []
        remaining = tensor.copy()

        for k in range(self.n):
            # Reshape for SVD
            if k == 0:
                shape = (self.m * 2, -1)
            else:
                current_shape = remaining.shape
                shape = (current_shape[0] * 2, -1)

            matrix = remaining.reshape(shape)

            # SVD
            U, s, Vt = svd(matrix, full_matrices=False)

            # Truncate if needed
            if max_bond_dim is not None:
                chi = min(max_bond_dim, len(s))
                U = U[:, :chi]
                s = s[:chi]
                Vt = Vt[:chi, :]

            # Store current tensor
            if k == 0:
                A_k = U.reshape(self.m, 2, -1)
            else:
                prev_chi = mps_tensors[-1].shape[2]
                A_k = U.reshape(prev_chi, 2, -1)

            mps_tensors.append(A_k)

            # Update remaining
            if k < self.n - 1:
                remaining = (np.diag(s) @ Vt).reshape(-1, *([2] * (self.n - k - 1)))

        self._mps_decomposition = mps_tensors
        return mps_tensors

    def tensor_rank(self) -> int:
        """
        Compute rank of family tensor (viewed as matrix).

        Returns:
            Tensor rank
        """
        matrix = self.to_matrix_form()
        rank = np.linalg.matrix_rank(matrix)
        return rank

    def correlation_function(self, i: int, j: int) -> float:
        """
        Compute correlation between positions i and j.

        C(i,j) = ⟨σⁱ σʲ⟩ - ⟨σⁱ⟩⟨σʲ⟩

        where σⁱ = indicator of element i being present.

        Args:
            i, j: Positions (0-indexed in elem_order)

        Returns:
            Correlation C(i,j)
        """
        if i >= self.n or j >= self.n:
            return 0.0

        tensor = self.to_tensor()

        # Compute marginals
        # P(σⁱ=1) = ∑_{other indices} T[..., i=1, ...]
        p_i = np.mean(np.sum(tensor, axis=tuple(range(1, self.n + 1)) if True else None))

        # This is getting complex, simplified version:
        # Use incidence matrix
        M = self.family.to_matrix()

        if M.size == 0:
            return 0.0

        # Marginals
        p_i = np.mean(M[:, i])
        p_j = np.mean(M[:, j])

        # Joint
        p_ij = np.mean(M[:, i] * M[:, j])

        # Correlation
        corr = p_ij - p_i * p_j

        return corr

    def correlation_matrix(self) -> np.ndarray:
        """
        Compute full correlation matrix C[i,j].

        Returns:
            Correlation matrix (n × n)
        """
        if self.n == 0:
            return np.array([[]])

        C = np.zeros((self.n, self.n))

        for i in range(self.n):
            for j in range(self.n):
                C[i, j] = self.correlation_function(i, j)

        return C

    def tensor_statistics(self) -> Dict:
        """
        Compute comprehensive tensor network statistics.

        Returns:
            Dict with statistics
        """
        ent_profile = self.entanglement_profile()
        bond_dims = self.bond_dimensions()
        corr_matrix = self.correlation_matrix()

        return {
            'dimension': self.n,
            'num_sets': self.m,
            'tensor_rank': self.tensor_rank(),
            'entanglement_profile': ent_profile,
            'avg_entanglement': np.mean(ent_profile) if ent_profile else 0,
            'max_entanglement': np.max(ent_profile) if ent_profile else 0,
            'bond_dimensions': bond_dims,
            'max_bond_dimension': np.max(bond_dims) if bond_dims else 1,
            'avg_bond_dimension': np.mean(bond_dims) if bond_dims else 1,
            'correlation_frobenius_norm': np.linalg.norm(corr_matrix, 'fro'),
            'max_correlation': np.max(np.abs(corr_matrix)) if corr_matrix.size > 0 else 0
        }

    def test_conjecture_via_tensor(self) -> Dict:
        """
        Test conjecture using tensor network approach.

        Returns:
            Test results
        """
        stats = self.tensor_statistics()
        actual_satisfies = self.family.satisfies_conjecture()

        # Heuristic: High entanglement suggests structured correlations
        # which should prevent uniform frequencies
        # ⇒ max frequency should be ≥ 0.5

        avg_ent = stats['avg_entanglement']
        max_bond = stats['max_bond_dimension']

        # Heuristic bound (to be refined)
        # If avg_ent > threshold or max_bond > threshold
        # then predict conjecture satisfied

        tensor_predicts_satisfaction = (avg_ent > 0.5) or (max_bond > 2)

        freqs = self.family.compute_frequencies()
        actual_max_freq = max(freqs.values()) if freqs else 0

        return {
            'actual_satisfies': actual_satisfies,
            'actual_max_frequency': actual_max_freq,
            'tensor_predicts_satisfaction': tensor_predicts_satisfaction,
            'avg_entanglement': avg_ent,
            'max_bond_dimension': max_bond,
            'tensor_rank': stats['tensor_rank'],
            'tensor_statistics': stats
        }


def demonstrate_tensor_approach():
    """
    Demonstrate tensor network approach on examples.
    """
    from core.generator import FamilyGenerator

    print("=" * 70)
    print("TENSOR NETWORK (MPS) APPROACH")
    print("=" * 70)
    print()

    # Example 1
    print("Example 1: {{1}, {2}, {1,2}}")
    family1 = UnionClosedFamily([{1}, {2}, {1, 2}])
    tna1 = TensorNetworkApproach(family1)
    result1 = tna1.test_conjecture_via_tensor()

    print(f"  Actual max frequency: {result1['actual_max_frequency']:.3f}")
    print(f"  Tensor rank: {result1['tensor_rank']}")
    print(f"  Avg entanglement: {result1['avg_entanglement']:.3f}")
    print(f"  Max bond dimension: {result1['max_bond_dimension']}")
    print()

    # Example 2
    print("Example 2: Random family (n=5)")
    gen = FamilyGenerator()
    family2 = gen.random_atoms(5, 3, seed=42)
    tna2 = TensorNetworkApproach(family2)
    result2 = tna2.test_conjecture_via_tensor()

    print(f"  Actual max frequency: {result2['actual_max_frequency']:.3f}")
    print(f"  Tensor rank: {result2['tensor_rank']}")
    print(f"  Avg entanglement: {result2['avg_entanglement']:.3f}")
    print(f"  Max bond dimension: {result2['max_bond_dimension']}")
    print()

    # Example 3
    print("Example 3: Challenging family (n=6)")
    family3 = gen.challenging_family(6, seed=123)
    tna3 = TensorNetworkApproach(family3)
    result3 = tna3.test_conjecture_via_tensor()

    print(f"  Actual max frequency: {result3['actual_max_frequency']:.3f}")
    print(f"  Tensor rank: {result3['tensor_rank']}")
    print(f"  Avg entanglement: {result3['avg_entanglement']:.3f}")
    print(f"  Max bond dimension: {result3['max_bond_dimension']}")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demonstrate_tensor_approach()
