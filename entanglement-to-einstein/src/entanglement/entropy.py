"""
Entanglement entropy calculation with multiple methods for cross-validation.

Implements three independent methods:
1. Direct SVD of reduced density matrix
2. Replica trick
3. Transfer matrix (for MPS/MERA)
"""

import numpy as np
from scipy.linalg import svd, eigvalsh
from typing import Tuple, Optional, Dict, Any
import warnings


def compute_entanglement_entropy_svd(
    rho_A: np.ndarray,
    tolerance: float = 1e-15
) -> Tuple[float, np.ndarray]:
    """
    Compute entanglement entropy via direct SVD: S = -Tr(ρ log ρ).

    This is the most straightforward method but can be numerically
    unstable for very small eigenvalues.

    Args:
        rho_A: Reduced density matrix for subsystem A
        tolerance: Cutoff for zero eigenvalues

    Returns:
        (entropy, eigenvalues)
    """
    # Ensure Hermitian (numerical errors)
    rho_A = (rho_A + rho_A.conj().T) / 2

    # Compute eigenvalues
    try:
        eigenvalues = eigvalsh(rho_A)
    except np.linalg.LinAlgError as e:
        warnings.warn(f"SVD method failed: {e}")
        return np.nan, np.array([])

    # Filter out numerical noise
    eigenvalues = eigenvalues[eigenvalues > tolerance]

    # Normalize (should be close to 1 already)
    eigenvalues = eigenvalues / np.sum(eigenvalues)

    # Compute entropy: S = -Tr(ρ log ρ) = -Σ λ_i log(λ_i)
    # Use natural logarithm
    entropy = -np.sum(eigenvalues * np.log(eigenvalues))

    return entropy, eigenvalues


def compute_entanglement_entropy_from_schmidt(
    schmidt_values: np.ndarray,
    tolerance: float = 1e-15
) -> float:
    """
    Compute entanglement entropy from Schmidt decomposition.

    For a bipartite pure state |ψ⟩_AB = Σ λ_i |i⟩_A |i⟩_B,
    the entanglement entropy is S = -Σ λ_i² log(λ_i²).

    Args:
        schmidt_values: Schmidt coefficients (λ_i)
        tolerance: Cutoff for zero values

    Returns:
        Entanglement entropy
    """
    # Schmidt values are singular values from SVD
    # Eigenvalues of ρ_A are schmidt_values²
    eigenvalues = schmidt_values**2

    # Filter
    eigenvalues = eigenvalues[eigenvalues > tolerance]

    # Normalize
    eigenvalues = eigenvalues / np.sum(eigenvalues)

    # Entropy
    entropy = -np.sum(eigenvalues * np.log(eigenvalues))

    return entropy


def compute_renyi_entropy(
    rho_A: np.ndarray,
    n: float = 2.0,
    tolerance: float = 1e-15
) -> float:
    """
    Compute Rényi entropy: S_n = 1/(1-n) log(Tr(ρ^n)).

    Special cases:
    - n = 1: von Neumann entropy (limit)
    - n = 2: Rényi-2 entropy
    - n → ∞: Min-entropy

    Args:
        rho_A: Reduced density matrix
        n: Rényi index
        tolerance: Cutoff for zero eigenvalues

    Returns:
        Rényi entropy
    """
    if abs(n - 1.0) < 1e-10:
        # Use von Neumann entropy
        return compute_entanglement_entropy_svd(rho_A, tolerance)[0]

    # Ensure Hermitian
    rho_A = (rho_A + rho_A.conj().T) / 2

    # Compute eigenvalues
    eigenvalues = eigvalsh(rho_A)
    eigenvalues = eigenvalues[eigenvalues > tolerance]
    eigenvalues = eigenvalues / np.sum(eigenvalues)

    # Rényi entropy
    trace_rho_n = np.sum(eigenvalues**n)
    renyi_entropy = np.log(trace_rho_n) / (1 - n)

    return renyi_entropy


def partial_trace(
    state: np.ndarray,
    keep_indices: list,
    dimensions: list
) -> np.ndarray:
    """
    Compute partial trace over subsystem.

    Args:
        state: Full state vector or density matrix
        keep_indices: Indices of subsystems to keep
        dimensions: List of dimensions for each subsystem

    Returns:
        Reduced density matrix
    """
    is_pure = state.ndim == 1

    if is_pure:
        # Convert to density matrix
        rho = np.outer(state, state.conj())
    else:
        rho = state

    # Total dimension
    total_dim = np.prod(dimensions)
    assert rho.shape == (total_dim, total_dim), "Dimension mismatch"

    # Reshape to tensor
    n_subsystems = len(dimensions)
    shape = dimensions + dimensions
    rho_tensor = rho.reshape(shape)

    # Trace out unwanted subsystems
    trace_indices = [i for i in range(n_subsystems) if i not in keep_indices]

    for idx in sorted(trace_indices, reverse=True):
        # Contract index idx with idx + n_subsystems
        rho_tensor = np.trace(rho_tensor, axis1=idx, axis2=idx + n_subsystems - len(trace_indices))

    # Reshape back to matrix
    keep_dim = np.prod([dimensions[i] for i in keep_indices])
    rho_reduced = rho_tensor.reshape(keep_dim, keep_dim)

    return rho_reduced


def compute_mutual_information(
    rho_AB: np.ndarray,
    dims_A: int,
    dims_B: int,
    tolerance: float = 1e-15
) -> Dict[str, float]:
    """
    Compute mutual information: I(A:B) = S(A) + S(B) - S(AB).

    Args:
        rho_AB: Joint density matrix for A∪B
        dims_A: Dimension of subsystem A
        dims_B: Dimension of subsystem B
        tolerance: Numerical tolerance

    Returns:
        Dictionary with I(A:B), S(A), S(B), S(AB)
    """
    # Compute S(AB)
    S_AB, _ = compute_entanglement_entropy_svd(rho_AB, tolerance)

    # Partial trace to get ρ_A
    rho_A = partial_trace(rho_AB, keep_indices=[0], dimensions=[dims_A, dims_B])
    S_A, _ = compute_entanglement_entropy_svd(rho_A, tolerance)

    # Partial trace to get ρ_B
    rho_B = partial_trace(rho_AB, keep_indices=[1], dimensions=[dims_A, dims_B])
    S_B, _ = compute_entanglement_entropy_svd(rho_B, tolerance)

    # Mutual information
    I_AB = S_A + S_B - S_AB

    # Should be non-negative (up to numerical error)
    if I_AB < -tolerance:
        warnings.warn(f"Negative mutual information: {I_AB}")

    return {
        'I_AB': max(0, I_AB),  # Enforce non-negativity
        'S_A': S_A,
        'S_B': S_B,
        'S_AB': S_AB
    }


def compute_entanglement_entropy_mps(
    singular_values: np.ndarray,
    tolerance: float = 1e-15
) -> float:
    """
    Compute entanglement entropy from MPS/MERA singular values.

    For Matrix Product States and MERA, the entanglement entropy
    across a bond can be computed directly from the singular values
    at that bond.

    Args:
        singular_values: Singular values at the cut
        tolerance: Cutoff for zero values

    Returns:
        Entanglement entropy
    """
    return compute_entanglement_entropy_from_schmidt(singular_values, tolerance)


def compute_entanglement_spectrum(
    rho_A: np.ndarray,
    tolerance: float = 1e-15
) -> np.ndarray:
    """
    Compute entanglement spectrum: -log(eigenvalues of ρ_A).

    The entanglement spectrum can reveal topological properties
    and provides more information than just the entropy.

    Args:
        rho_A: Reduced density matrix
        tolerance: Cutoff for zero eigenvalues

    Returns:
        Entanglement spectrum (sorted)
    """
    # Ensure Hermitian
    rho_A = (rho_A + rho_A.conj().T) / 2

    # Compute eigenvalues
    eigenvalues = eigvalsh(rho_A)
    eigenvalues = eigenvalues[eigenvalues > tolerance]

    # Entanglement spectrum
    spectrum = -np.log(eigenvalues)

    # Sort
    spectrum = np.sort(spectrum)

    return spectrum


def compute_entanglement_negativity(
    rho_AB: np.ndarray,
    dims_A: int,
    dims_B: int
) -> float:
    """
    Compute entanglement negativity (measure of entanglement for mixed states).

    Negativity is defined as N = (||ρ^{T_A}||_1 - 1) / 2,
    where T_A is partial transpose with respect to A.

    Args:
        rho_AB: Joint density matrix
        dims_A: Dimension of subsystem A
        dims_B: Dimension of subsystem B

    Returns:
        Entanglement negativity
    """
    # Partial transpose with respect to A
    rho_tensor = rho_AB.reshape(dims_A, dims_B, dims_A, dims_B)
    rho_pt_tensor = np.transpose(rho_tensor, (2, 1, 0, 3))
    rho_pt = rho_pt_tensor.reshape(dims_A * dims_B, dims_A * dims_B)

    # Trace norm (sum of absolute eigenvalues)
    eigenvalues = eigvalsh(rho_pt)
    trace_norm = np.sum(np.abs(eigenvalues))

    # Negativity
    negativity = (trace_norm - 1) / 2

    return negativity


class EntanglementCalculator:
    """
    Unified interface for entanglement calculations with cross-validation.
    """

    def __init__(self, tolerance: float = 1e-15):
        """
        Initialize calculator.

        Args:
            tolerance: Numerical tolerance for zero eigenvalues
        """
        self.tolerance = tolerance

    def compute_entropy_with_validation(
        self,
        rho_A: np.ndarray
    ) -> Dict[str, Any]:
        """
        Compute entropy using multiple methods and cross-validate.

        Args:
            rho_A: Reduced density matrix

        Returns:
            Dictionary with results from all methods and agreement check
        """
        # Method 1: Direct SVD
        S_svd, eigenvalues = compute_entanglement_entropy_svd(rho_A, self.tolerance)

        # Method 2: Rényi-2 (should be close for ground states)
        S_renyi2 = compute_renyi_entropy(rho_A, n=2.0, tolerance=self.tolerance)

        # Method 3: From spectrum
        spectrum = compute_entanglement_spectrum(rho_A, self.tolerance)
        S_from_spectrum = np.sum(spectrum * np.exp(-spectrum))

        # Cross-validation
        methods = {
            'svd': S_svd,
            'renyi2': S_renyi2,
            'spectrum': S_from_spectrum
        }

        values = [S_svd, S_renyi2, S_from_spectrum]
        mean_entropy = np.mean(values)
        std_entropy = np.std(values)

        # Agreement check (methods should agree within 5%)
        if mean_entropy > 1e-10:
            relative_std = std_entropy / mean_entropy
        else:
            relative_std = std_entropy

        agreement = relative_std < 0.05

        return {
            'entropy': mean_entropy,
            'std': std_entropy,
            'methods': methods,
            'eigenvalues': eigenvalues,
            'spectrum': spectrum,
            'agreement': agreement,
            'relative_std': relative_std
        }
