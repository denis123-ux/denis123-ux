"""Tests for entanglement entropy calculations."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
import pytest
from entanglement.entropy import (
    von_neumann_entropy,
    entanglement_entropy_svd,
    entanglement_entropy_replica
)


class TestVonNeumannEntropy:
    """Test von Neumann entropy calculation."""

    def test_pure_state_zero_entropy(self):
        """Pure state should have zero entropy."""
        # Pure state: ρ = |0⟩⟨0|
        rho = np.array([[1, 0], [0, 0]])
        S = von_neumann_entropy(rho)
        assert np.abs(S) < 1e-10, f"Pure state entropy {S} != 0"

    def test_maximally_mixed_state(self):
        """Maximally mixed state should have maximum entropy."""
        d = 4
        rho = np.eye(d) / d
        S = von_neumann_entropy(rho, base=2)
        expected = np.log2(d)  # 2 bits for d=4
        assert np.abs(S - expected) < 1e-10, f"S={S} != {expected}"

    def test_entropy_bounds(self):
        """Entropy should satisfy 0 ≤ S ≤ log(d)."""
        # Random density matrix
        d = 3
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        rho = A @ A.conj().T
        rho /= np.trace(rho)

        S = von_neumann_entropy(rho)
        assert S >= 0, f"Negative entropy: {S}"
        assert S <= np.log(d) + 1e-10, f"S={S} > log(d)={np.log(d)}"


class TestEntanglementEntropySVD:
    """Test SVD method for entanglement entropy."""

    def test_product_state_zero_entropy(self):
        """Product state |00...0⟩ should have zero entanglement."""
        n_sites = 6
        state = np.zeros(2**n_sites)
        state[0] = 1.0

        S, info = entanglement_entropy_svd(
            state,
            region_A_size=3,
            total_sites=n_sites
        )

        assert np.abs(S) < 1e-10, f"Product state entropy {S} != 0"
        assert info['schmidt_rank'] == 1, "Product state should have Schmidt rank 1"

    def test_maximally_entangled_pair(self):
        """Bell state should have entropy log(2)."""
        # Bell state: (|00⟩ + |11⟩)/√2 for 2 qubits
        state = np.zeros(4)
        state[0] = 1/np.sqrt(2)  # |00⟩
        state[3] = 1/np.sqrt(2)  # |11⟩

        S, info = entanglement_entropy_svd(
            state,
            region_A_size=1,
            total_sites=2
        )

        expected = np.log(2)
        assert np.abs(S - expected) < 1e-10, f"Bell state S={S} != log(2)={expected}"

    def test_normalization_invariance(self):
        """Entropy should not change if state is renormalized."""
        n_sites = 4
        state = np.random.randn(2**n_sites)
        state /= np.linalg.norm(state)

        S1, _ = entanglement_entropy_svd(state, 2, n_sites)

        # Renormalize
        state *= 2.0
        state /= np.linalg.norm(state)

        S2, _ = entanglement_entropy_svd(state, 2, n_sites)

        assert np.abs(S1 - S2) < 1e-10, f"Entropy changed: {S1} → {S2}"


class TestEntanglementEntropyReplica:
    """Test replica trick method."""

    def test_agrees_with_direct_calculation(self):
        """Replica method should agree with direct diagonalization."""
        # Random density matrix
        d = 4
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        rho = A @ A.conj().T
        rho /= np.trace(rho)

        # Direct calculation
        S_direct = von_neumann_entropy(rho)

        # Replica trick
        S_replica, _ = entanglement_entropy_replica(rho)

        # Should agree within a few percent (replica is approximate)
        relative_error = abs(S_direct - S_replica) / (S_direct + 1e-10)
        assert relative_error < 0.05, f"Methods disagree: {S_direct} vs {S_replica}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
