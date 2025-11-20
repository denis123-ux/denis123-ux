"""
Unit tests for entanglement entropy calculations.
"""

import numpy as np
import pytest
from src.entanglement.entropy import (
    compute_entropy_svd,
    compute_entropy_eigenvalue,
    compute_entropy_replica_trick,
    compute_entropy_all_methods,
    compute_mutual_information
)


class TestEntropyCalculations:
    """Test suite for entropy calculation methods."""

    def test_entropy_pure_state(self):
        """Test that pure state has zero entropy."""
        # Pure product state |0⟩⊗|0⟩
        state = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)

        S, info = compute_entropy_svd(state, region_A_dim=2)

        assert np.abs(S) < 1e-10, f"Pure state should have zero entropy, got {S}"

    def test_entropy_maximally_entangled(self):
        """Test maximally entangled Bell state."""
        # |ψ⟩ = (|00⟩ + |11⟩)/√2
        state = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)

        S, info = compute_entropy_svd(state, region_A_dim=2)

        # Should be log(2)
        expected = np.log(2)
        assert np.abs(S - expected) < 1e-6, f"Expected {expected}, got {S}"

    def test_entropy_non_negative(self):
        """Test that entropy is always non-negative."""
        np.random.seed(42)

        for _ in range(10):
            # Random state
            state = np.random.randn(16) + 1j * np.random.randn(16)
            state = state / np.linalg.norm(state)

            S, info = compute_entropy_svd(state, region_A_dim=4)

            assert S >= -1e-10, f"Entropy must be non-negative, got {S}"

    def test_entropy_upper_bound(self):
        """Test that entropy satisfies upper bound S ≤ log(dim)."""
        np.random.seed(42)

        dim_A = 4
        dim_B = 4
        max_entropy = np.log(dim_A)

        for _ in range(10):
            state = np.random.randn(dim_A * dim_B) + 1j * np.random.randn(dim_A * dim_B)
            state = state / np.linalg.norm(state)

            S, info = compute_entropy_svd(state, region_A_dim=dim_A)

            assert S <= max_entropy + 1e-6, f"Entropy {S} exceeds maximum {max_entropy}"

    def test_methods_agree(self):
        """Test that different methods give consistent results."""
        np.random.seed(42)

        # Random entangled state
        state = np.random.randn(16) + 1j * np.random.randn(16)
        state = state / np.linalg.norm(state)

        # Compute with different methods
        S_svd, _ = compute_entropy_svd(state, region_A_dim=4)

        # Density matrix
        state_matrix = state.reshape(4, 4)
        rho_A = state_matrix @ state_matrix.conj().T

        S_eigen, _ = compute_entropy_eigenvalue(rho_A)
        S_replica, _ = compute_entropy_replica_trick(rho_A)

        # Check agreement (within 5%)
        tolerance = 0.05
        relative_diff_1 = abs(S_svd - S_eigen) / (S_svd + 1e-10)
        relative_diff_2 = abs(S_svd - S_replica) / (S_svd + 1e-10)

        assert relative_diff_1 < tolerance, f"SVD vs Eigen: {relative_diff_1:.3f} > {tolerance}"
        assert relative_diff_2 < tolerance, f"SVD vs Replica: {relative_diff_2:.3f} > {tolerance}"

    def test_mutual_information_positive(self):
        """Test that mutual information is non-negative."""
        # For pure states: I(A:B) = 2*S(A)
        # Create entangled state
        state = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)

        S_A, _ = compute_entropy_svd(state, region_A_dim=2)
        S_B = S_A  # By symmetry
        S_AB = 0.0  # Pure state

        I_AB = compute_mutual_information(S_A, S_B, S_AB)

        assert I_AB >= -1e-10, f"Mutual information should be non-negative, got {I_AB}"
        assert np.abs(I_AB - 2 * S_A) < 1e-6, f"Expected I(A:B) = 2*S(A) = {2*S_A}, got {I_AB}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
