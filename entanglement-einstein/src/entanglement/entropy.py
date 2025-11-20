"""
Entanglement entropy calculations with multiple cross-validation methods.

Provides 3+ independent methods to compute S_EE(A) = -Tr(ρ_A log ρ_A):
1. SVD method: Most stable numerically
2. Eigenvalue method: Direct diagonalization
3. Replica trick: Physics-inspired approach

All methods MUST agree within tolerance for validation.
"""

import numpy as np
from scipy.linalg import svd, logm
from typing import Tuple, Dict, Any, Optional
import warnings


def compute_entropy_svd(state_vector: np.ndarray, region_A_dim: int) -> Tuple[float, Dict[str, Any]]:
    """
    Compute entanglement entropy via Schmidt decomposition (SVD).

    Most numerically stable method.

    Math:
        |ψ⟩ = Σ_i √λ_i |i⟩_A ⊗ |i⟩_B (Schmidt decomposition)
        S(A) = -Σ_i λ_i log λ_i

    Args:
        state_vector: Full quantum state |ψ⟩
        region_A_dim: Dimension of Hilbert space for region A

    Returns:
        (entropy, info_dict)
    """
    # Reshape state as matrix: |ψ⟩ → ψ_{AB}
    total_dim = len(state_vector)
    region_B_dim = total_dim // region_A_dim

    assert region_A_dim * region_B_dim == total_dim, "Incompatible dimensions"

    state_matrix = state_vector.reshape(region_A_dim, region_B_dim)

    # SVD: ψ = U Σ V†
    _, singular_values, _ = svd(state_matrix, full_matrices=False)

    # Schmidt coefficients: λ_i = s_i²
    schmidt_coefficients = singular_values ** 2

    # Remove numerical zeros
    schmidt_coefficients = schmidt_coefficients[schmidt_coefficients > 1e-15]

    # Normalize (should already be normalized, but ensure numerical stability)
    schmidt_coefficients = schmidt_coefficients / np.sum(schmidt_coefficients)

    # Entropy: S = -Σ λ log λ
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        entropy = -np.sum(schmidt_coefficients * np.log(schmidt_coefficients))

    # Check for NaN
    if np.isnan(entropy):
        entropy = 0.0

    info = {
        'method': 'svd',
        'schmidt_rank': len(schmidt_coefficients),
        'largest_schmidt_coeff': float(np.max(schmidt_coefficients)),
        'schmidt_spectrum': schmidt_coefficients
    }

    return float(entropy), info


def compute_entropy_eigenvalue(rho_A: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Compute entanglement entropy via direct eigenvalue decomposition.

    Args:
        rho_A: Reduced density matrix ρ_A

    Returns:
        (entropy, info_dict)
    """
    # Ensure Hermitian
    rho_A = (rho_A + rho_A.conj().T) / 2

    # Diagonalize
    eigenvalues = np.linalg.eigvalsh(rho_A)

    # Remove negative eigenvalues (numerical errors)
    eigenvalues = eigenvalues[eigenvalues > 1e-15]

    # Normalize
    eigenvalues = eigenvalues / np.sum(eigenvalues)

    # Entropy
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        entropy = -np.sum(eigenvalues * np.log(eigenvalues))

    if np.isnan(entropy):
        entropy = 0.0

    info = {
        'method': 'eigenvalue',
        'n_eigenvalues': len(eigenvalues),
        'largest_eigenvalue': float(np.max(eigenvalues)),
        'eigenspectrum': eigenvalues,
        'purity': float(np.sum(eigenvalues ** 2))
    }

    return float(entropy), info


def compute_entropy_replica_trick(
    rho_A: np.ndarray,
    n_values: Optional[np.ndarray] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute entanglement entropy via replica trick.

    Math:
        S = -∂/∂n Tr(ρ^n)|_{n→1}

    Approximate using finite differences with multiple n values.

    Args:
        rho_A: Reduced density matrix
        n_values: Array of n values for finite difference (default: [0.9, 1.0, 1.1])

    Returns:
        (entropy, info_dict)
    """
    if n_values is None:
        n_values = np.array([0.9, 0.95, 1.0, 1.05, 1.1])

    # Compute Tr(ρ^n) for each n
    traces = []
    for n in n_values:
        if abs(n - 1.0) < 1e-10:
            # n = 1: Tr(ρ) = 1
            trace_n = 1.0
        else:
            # Tr(ρ^n) via eigenvalue method
            eigenvalues = np.linalg.eigvalsh(rho_A)
            eigenvalues = eigenvalues[eigenvalues > 1e-15]
            trace_n = np.sum(eigenvalues ** n)

        traces.append(trace_n)

    traces = np.array(traces)

    # Numerical derivative at n=1
    # Use central difference
    idx_1 = np.argmin(np.abs(n_values - 1.0))

    if idx_1 > 0 and idx_1 < len(n_values) - 1:
        # Central difference
        dn = n_values[idx_1 + 1] - n_values[idx_1 - 1]
        dZ = traces[idx_1 + 1] - traces[idx_1 - 1]
        derivative = dZ / dn
    else:
        # Forward or backward difference
        dn = n_values[1] - n_values[0]
        dZ = traces[1] - traces[0]
        derivative = dZ / dn

    entropy = -derivative

    info = {
        'method': 'replica_trick',
        'n_values': n_values,
        'traces': traces,
        'derivative': derivative
    }

    return float(entropy), info


def compute_entropy_vonneumann_direct(rho_A: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Compute von Neumann entropy via direct matrix logarithm.

    Math:
        S = -Tr(ρ log ρ)

    Warning: Can be numerically unstable for nearly singular matrices.

    Args:
        rho_A: Reduced density matrix

    Returns:
        (entropy, info_dict)
    """
    # Ensure Hermitian
    rho_A = (rho_A + rho_A.conj().T) / 2

    # Regularize to avoid log(0)
    epsilon = 1e-15
    rho_A_reg = rho_A + epsilon * np.eye(rho_A.shape[0])

    try:
        # Matrix logarithm
        log_rho = logm(rho_A_reg)

        # S = -Tr(ρ log ρ)
        entropy = -np.trace(rho_A @ log_rho).real

    except np.linalg.LinAlgError:
        # Fallback to eigenvalue method
        warnings.warn("Matrix logarithm failed, using eigenvalue method")
        entropy, info = compute_entropy_eigenvalue(rho_A)
        return entropy, info

    info = {
        'method': 'vonneumann_direct',
        'used_regularization': epsilon
    }

    return float(entropy), info


def compute_renyi_entropy(rho_A: np.ndarray, alpha: float = 2.0) -> Tuple[float, Dict[str, Any]]:
    """
    Compute Rényi entropy.

    Math:
        S_α = (1/(1-α)) log Tr(ρ^α)

    For α=1: recovers von Neumann entropy (by limit)
    For α=2: "purity entropy"

    Args:
        rho_A: Reduced density matrix
        alpha: Rényi parameter (α > 0, α ≠ 1)

    Returns:
        (renyi_entropy, info_dict)
    """
    if abs(alpha - 1.0) < 1e-6:
        # α → 1 limit: von Neumann entropy
        return compute_entropy_eigenvalue(rho_A)

    # Compute Tr(ρ^α)
    eigenvalues = np.linalg.eigvalsh(rho_A)
    eigenvalues = eigenvalues[eigenvalues > 1e-15]

    trace_rho_alpha = np.sum(eigenvalues ** alpha)

    # S_α = (1/(1-α)) log Tr(ρ^α)
    renyi_entropy = (1 / (1 - alpha)) * np.log(trace_rho_alpha)

    info = {
        'method': f'renyi_alpha_{alpha}',
        'alpha': alpha,
        'trace_rho_alpha': float(trace_rho_alpha)
    }

    return float(renyi_entropy), info


def compute_entropy_all_methods(
    state_vector: Optional[np.ndarray] = None,
    rho_A: Optional[np.ndarray] = None,
    region_A_dim: Optional[int] = None,
    check_agreement: bool = True,
    tolerance: float = 0.01
) -> Dict[str, Any]:
    """
    Compute entanglement entropy using ALL methods for cross-validation.

    This is the main function to use for rigorous scientific computation.

    Args:
        state_vector: Full state |ψ⟩ (if available)
        rho_A: Reduced density matrix ρ_A (if available)
        region_A_dim: Dimension of region A (needed for SVD method)
        check_agreement: Whether to check methods agree
        tolerance: Agreement tolerance (relative error)

    Returns:
        Dictionary with results from all methods
    """
    results = {
        'methods': {},
        'agreement_check': {},
        'recommended_value': None
    }

    # Method 1: SVD (if state vector available)
    if state_vector is not None and region_A_dim is not None:
        S_svd, info_svd = compute_entropy_svd(state_vector, region_A_dim)
        results['methods']['svd'] = {'entropy': S_svd, 'info': info_svd}

    # Method 2: Eigenvalue (if density matrix available)
    if rho_A is not None:
        S_eigen, info_eigen = compute_entropy_eigenvalue(rho_A)
        results['methods']['eigenvalue'] = {'entropy': S_eigen, 'info': info_eigen}

        # Method 3: Replica trick
        S_replica, info_replica = compute_entropy_replica_trick(rho_A)
        results['methods']['replica'] = {'entropy': S_replica, 'info': info_replica}

        # Method 4: Direct von Neumann
        S_direct, info_direct = compute_entropy_vonneumann_direct(rho_A)
        results['methods']['direct'] = {'entropy': S_direct, 'info': info_direct}

    # Check agreement
    if check_agreement and len(results['methods']) >= 2:
        entropy_values = [r['entropy'] for r in results['methods'].values()]
        mean_entropy = np.mean(entropy_values)
        std_entropy = np.std(entropy_values)
        relative_std = std_entropy / (mean_entropy + 1e-10)

        results['agreement_check'] = {
            'mean': mean_entropy,
            'std': std_entropy,
            'relative_std': relative_std,
            'all_agree': relative_std < tolerance,
            'tolerance': tolerance
        }

        if relative_std >= tolerance:
            warnings.warn(
                f"Methods disagree! Relative std: {relative_std:.4f} >= {tolerance}\n"
                f"Values: {entropy_values}"
            )

        # Use SVD as recommended value (most stable)
        if 'svd' in results['methods']:
            results['recommended_value'] = results['methods']['svd']['entropy']
        else:
            results['recommended_value'] = mean_entropy

    return results


def compute_mutual_information(
    S_A: float,
    S_B: float,
    S_AB: float
) -> float:
    """
    Compute mutual information I(A:B) = S(A) + S(B) - S(AB).

    Args:
        S_A: Entropy of region A
        S_B: Entropy of region B
        S_AB: Entropy of combined region A∪B

    Returns:
        Mutual information I(A:B)
    """
    I_AB = S_A + S_B - S_AB
    return I_AB


def compute_conditional_entropy(S_A: float, S_AB: float) -> float:
    """
    Compute conditional entropy S(A|B) = S(AB) - S(B).

    Args:
        S_A: Entropy of region A
        S_AB: Entropy of combined region A∪B

    Returns:
        Conditional entropy S(A|B)
    """
    S_conditional = S_AB - S_A
    return S_conditional
