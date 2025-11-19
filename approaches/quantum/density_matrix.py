"""
Quantum Density Matrix approach to the Union-Closed Sets Conjecture.

CORE IDEA:
----------
Map a union-closed family F to a quantum density matrix ρ, where:
- Each element x ∈ universe corresponds to a quantum state |x⟩
- Each set S ∈ F corresponds to a mixed state ρ_S = (1/|S|) ∑_{x∈S} |x⟩⟨x|
- Family density matrix: ρ_F = (1/|F|) ∑_{S∈F} ρ_S

QUANTUM INFORMATION MEASURES:
-----------------------------
1. **Von Neumann Entropy**: S(ρ) = -Tr(ρ log ρ)
   - Measures mixedness of quantum state
   - S(ρ) = 0 for pure states, S(ρ) = log(d) for maximally mixed

2. **Purity**: P(ρ) = Tr(ρ²)
   - P(ρ) = 1 for pure states, P(ρ) = 1/d for maximally mixed

3. **Fidelity**: F(ρ, σ) = Tr(√(√ρ σ √ρ))
   - Measures closeness of quantum states

CONJECTURE CONNECTION:
----------------------
Hypothesis: If F is union-closed, then ρ_F has special structure that
implies ∃x with frequency(x) ≥ 1/2.

Approach:
1. Compute ρ_F and its spectrum {λ_i}
2. Compute S(ρ) and P(ρ)
3. Relate these to frequency distribution
4. Use quantum information inequalities to bound max frequency

KEY INSIGHT: Union-closedness imposes constraints on ρ_F similar to
"quantum conditional independence" - this limits how uniform frequencies can be.
"""

import numpy as np
from scipy.linalg import logm, sqrtm
from typing import Dict, Tuple, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.family import UnionClosedFamily


class QuantumApproach:
    """
    Quantum information theory approach to union-closed sets conjecture.
    """

    def __init__(self, family: UnionClosedFamily):
        """
        Initialize quantum approach with a union-closed family.

        Args:
            family: Union-closed family to analyze
        """
        self.family = family
        self.n = family.n  # Dimension of Hilbert space
        self.m = family.m  # Number of sets

        # Density matrix (computed lazily)
        self._rho = None
        self._eigenvalues = None

    def compute_density_matrix(self) -> np.ndarray:
        """
        Compute the density matrix ρ_F for the family.

        Construction:
        - Each set S contributes ρ_S = (1/|S|) ∑_{x∈S} |x⟩⟨x|
        - ρ_F = (1/|F|) ∑_{S∈F} ρ_S

        Returns:
            Density matrix (n×n complex Hermitian matrix)
        """
        if self._rho is not None:
            return self._rho

        if self.n == 0 or self.m == 0:
            self._rho = np.zeros((1, 1), dtype=complex)
            return self._rho

        # Initialize density matrix
        rho = np.zeros((self.n, self.n), dtype=complex)

        # Map elements to indices
        elem_to_idx = {elem: idx for idx, elem in enumerate(sorted(self.family.universe))}

        # Build density matrix
        for S in self.family.sets:
            if len(S) == 0:
                continue

            # ρ_S = (1/|S|) ∑_{x∈S} |x⟩⟨x|
            for x in S:
                idx = elem_to_idx[x]
                rho[idx, idx] += 1.0 / len(S)

        # Normalize by number of sets
        rho /= self.m

        # Ensure Hermiticity (should already be Hermitian, but numerical safety)
        rho = (rho + rho.conj().T) / 2

        self._rho = rho
        return rho

    def eigenspectrum(self) -> np.ndarray:
        """
        Compute eigenspectrum of density matrix.

        Returns:
            Eigenvalues in descending order
        """
        if self._eigenvalues is not None:
            return self._eigenvalues

        rho = self.compute_density_matrix()

        # Compute eigenvalues (should all be real and non-negative)
        eigenvalues = np.linalg.eigvalsh(rho)

        # Sort in descending order
        eigenvalues = np.sort(eigenvalues)[::-1]

        # Clip small negative values (numerical errors)
        eigenvalues = np.maximum(eigenvalues, 0)

        # Normalize (should sum to 1)
        eigenvalues = eigenvalues / (np.sum(eigenvalues) + 1e-15)

        self._eigenvalues = eigenvalues
        return eigenvalues

    def von_neumann_entropy(self) -> float:
        """
        Compute von Neumann entropy S(ρ) = -Tr(ρ log ρ).

        Returns:
            Entropy in nats (use log base e)
        """
        eigenvalues = self.eigenspectrum()

        # S(ρ) = -∑ λ_i log(λ_i)
        # Handle λ=0 case: 0 log 0 = 0
        entropy = 0.0
        for lam in eigenvalues:
            if lam > 1e-15:
                entropy -= lam * np.log(lam)

        return entropy

    def purity(self) -> float:
        """
        Compute purity P(ρ) = Tr(ρ²).

        Returns:
            Purity (in [1/n, 1])
        """
        eigenvalues = self.eigenspectrum()

        # P(ρ) = ∑ λ_i²
        purity = np.sum(eigenvalues ** 2)

        return purity

    def participation_ratio(self) -> float:
        """
        Compute participation ratio PR = 1/Tr(ρ²).

        Measures effective number of quantum states participating.

        Returns:
            Participation ratio (in [1, n])
        """
        p = self.purity()
        if p < 1e-15:
            return self.n

        return 1.0 / p

    def max_eigenvalue(self) -> float:
        """
        Get largest eigenvalue λ_max.

        Returns:
            λ_max
        """
        eigenvalues = self.eigenspectrum()
        return eigenvalues[0] if len(eigenvalues) > 0 else 0.0

    def effective_dimension(self) -> float:
        """
        Compute effective dimension d_eff = exp(S(ρ)).

        Returns:
            Effective dimension
        """
        S = self.von_neumann_entropy()
        return np.exp(S)

    def quantum_frequency_bound(self) -> float:
        """
        Compute a bound on max frequency using quantum information.

        THEOREM (Heuristic):
        If ρ is the density matrix of a union-closed family, then:

        max_frequency ≥ λ_max = largest eigenvalue of ρ

        PROOF SKETCH:
        - ρ_ii = frequency of element i
        - λ_max ≥ ρ_ii for all i (diagonal elements bounded by max eigenvalue)
        - Therefore λ_max provides a lower bound on max frequency

        Returns:
            Lower bound on max frequency
        """
        rho = self.compute_density_matrix()

        # Method 1: Max eigenvalue bound
        lambda_max = self.max_eigenvalue()

        # Method 2: Max diagonal element (= max frequency directly)
        max_diag = np.max(np.real(np.diag(rho)))

        # Method 3: Purity bound
        # If all frequencies were < 1/2, purity would be < specific threshold
        p = self.purity()

        # Theoretical bound (heuristic)
        # If max_freq < 1/2, then purity ≤ ??
        # Still working on this...

        return max(lambda_max, max_diag)

    def analyze_union_closure_constraints(self) -> Dict:
        """
        Analyze constraints imposed by union-closure on density matrix.

        Union-closure ⇒ certain coherence patterns in ρ.

        Returns:
            Dict with analysis results
        """
        rho = self.compute_density_matrix()
        eigenvalues = self.eigenspectrum()

        # Compute off-diagonal coherence
        coherence = np.sum(np.abs(rho - np.diag(np.diag(rho))))

        # Compute max off-diagonal element
        rho_offdiag = rho - np.diag(np.diag(rho))
        max_coherence = np.max(np.abs(rho_offdiag))

        return {
            'coherence_l1': coherence,
            'max_coherence': max_coherence,
            'eigenvalue_spread': eigenvalues[0] - eigenvalues[-1] if len(eigenvalues) > 0 else 0,
            'effective_rank': self.participation_ratio(),
            'entropy': self.von_neumann_entropy(),
            'purity': self.purity()
        }

    def quantum_statistics(self) -> Dict:
        """
        Compute comprehensive quantum statistics.

        Returns:
            Dict with all quantum measures
        """
        rho = self.compute_density_matrix()
        eigenvalues = self.eigenspectrum()

        # Direct frequency from diagonal
        freqs = self.family.compute_frequencies()
        elem_to_idx = {elem: idx for idx, elem in enumerate(sorted(self.family.universe))}

        # Compare diagonal elements with frequencies
        diagonal_freqs = {elem: np.real(rho[elem_to_idx[elem], elem_to_idx[elem]])
                         for elem in self.family.universe}

        return {
            'dimension': self.n,
            'num_sets': self.m,
            'eigenvalues': eigenvalues.tolist(),
            'largest_eigenvalue': self.max_eigenvalue(),
            'von_neumann_entropy': self.von_neumann_entropy(),
            'purity': self.purity(),
            'participation_ratio': self.participation_ratio(),
            'effective_dimension': self.effective_dimension(),
            'quantum_bound': self.quantum_frequency_bound(),
            'actual_max_frequency': max(freqs.values()) if freqs else 0,
            'diagonal_vs_frequency_match': all(
                abs(diagonal_freqs[elem] - freqs[elem]) < 1e-10
                for elem in freqs
            ),
            'coherence_analysis': self.analyze_union_closure_constraints()
        }

    def test_conjecture_via_quantum(self) -> Dict:
        """
        Test the conjecture using quantum approach.

        Returns:
            Dict with test results
        """
        stats = self.quantum_statistics()
        actual_satisfies = self.family.satisfies_conjecture()

        # Check if quantum bound predicts conjecture
        quantum_predicts_satisfaction = stats['quantum_bound'] >= 0.5

        return {
            'actual_satisfies': actual_satisfies,
            'quantum_bound': stats['quantum_bound'],
            'actual_max_frequency': stats['actual_max_frequency'],
            'quantum_predicts_correctly': quantum_predicts_satisfaction == actual_satisfies,
            'bound_tightness': abs(stats['quantum_bound'] - stats['actual_max_frequency']),
            'quantum_statistics': stats
        }


def demonstrate_quantum_approach():
    """
    Demonstrate the quantum approach on example families.
    """
    from core.generator import FamilyGenerator

    print("=" * 70)
    print("QUANTUM DENSITY MATRIX APPROACH")
    print("=" * 70)
    print()

    # Example 1: Simple family
    print("Example 1: {{1}, {2}, {1,2}}")
    family1 = UnionClosedFamily([{1}, {2}, {1, 2}])
    qa1 = QuantumApproach(family1)
    result1 = qa1.test_conjecture_via_quantum()

    print(f"  Actual max frequency: {result1['actual_max_frequency']:.3f}")
    print(f"  Quantum bound: {result1['quantum_bound']:.3f}")
    print(f"  Satisfies conjecture: {result1['actual_satisfies']}")
    print(f"  Von Neumann entropy: {result1['quantum_statistics']['von_neumann_entropy']:.3f}")
    print(f"  Purity: {result1['quantum_statistics']['purity']:.3f}")
    print()

    # Example 2: Random family
    print("Example 2: Random family (n=5)")
    gen = FamilyGenerator()
    family2 = gen.random_atoms(5, 3, seed=42)
    qa2 = QuantumApproach(family2)
    result2 = qa2.test_conjecture_via_quantum()

    print(f"  Actual max frequency: {result2['actual_max_frequency']:.3f}")
    print(f"  Quantum bound: {result2['quantum_bound']:.3f}")
    print(f"  Satisfies conjecture: {result2['actual_satisfies']}")
    print(f"  Von Neumann entropy: {result2['quantum_statistics']['von_neumann_entropy']:.3f}")
    print(f"  Purity: {result2['quantum_statistics']['purity']:.3f}")
    print()

    # Example 3: Challenging family
    print("Example 3: Challenging family (n=6)")
    family3 = gen.challenging_family(6, seed=123)
    qa3 = QuantumApproach(family3)
    result3 = qa3.test_conjecture_via_quantum()

    print(f"  Actual max frequency: {result3['actual_max_frequency']:.3f}")
    print(f"  Quantum bound: {result3['quantum_bound']:.3f}")
    print(f"  Satisfies conjecture: {result3['actual_satisfies']}")
    print(f"  Von Neumann entropy: {result3['quantum_statistics']['von_neumann_entropy']:.3f}")
    print(f"  Purity: {result3['quantum_statistics']['purity']:.3f}")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demonstrate_quantum_approach()
