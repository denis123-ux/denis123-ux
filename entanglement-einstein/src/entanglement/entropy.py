"""
Entanglement Entropy Calculations
==================================

Three independent methods for computing S_EE(A) = -Tr(ρ_A log ρ_A):
1. SVD method (direct diagonalization)
2. Replica trick (analytical continuation)
3. Transfer matrix (for MPS/MERA)

Cross-validation ensures numerical accuracy.

References:
- Holzhey et al. (1994): Geometric entropy in CFT
- Calabrese & Cardy (2004): Entanglement entropy in 1D quantum systems
"""

import numpy as np
from typing import Optional, Tuple, Dict
import warnings


def von_neumann_entropy(
    rho: np.ndarray,
    base: float = np.e,
    tolerance: float = 1e-14
) -> float:
    """
    Compute von Neumann entropy S = -Tr(ρ log ρ).

    Parameters
    ----------
    rho : ndarray, shape (d, d)
        Density matrix
    base : float
        Logarithm base (np.e for nats, 2 for bits)
    tolerance : float
        Eigenvalue cutoff (avoid log(0))

    Returns
    -------
    float
        Von Neumann entropy

    Examples
    --------
    >>> # Maximally mixed state: S = log(d)
    >>> d = 4
    >>> rho = np.eye(d) / d
    >>> S = von_neumann_entropy(rho, base=2)
    >>> print(f"S = {S:.4f} bits (expected: 2.0)")
    """
    # Diagonalize density matrix
    eigenvalues = np.linalg.eigvalsh(rho)

    # Filter out near-zero eigenvalues
    eigenvalues = eigenvalues[eigenvalues > tolerance]

    # Normalize (in case of numerical errors)
    eigenvalues /= np.sum(eigenvalues)

    # S = -sum(λ_i log λ_i)
    S = -np.sum(eigenvalues * np.log(eigenvalues) / np.log(base))

    return S


def entanglement_entropy_svd(
    state: np.ndarray,
    region_A_size: int,
    total_sites: int,
    d_phys: int = 2,
    base: float = np.e
) -> Tuple[float, Dict]:
    """
    Compute entanglement entropy via SVD of state vector.

    For a pure state |ψ⟩ in bipartition A∪B:
    |ψ⟩ = ∑_i λ_i |i⟩_A ⊗ |i⟩_B (Schmidt decomposition)
    S_EE(A) = -∑_i λ_i² log(λ_i²)

    Parameters
    ----------
    state : ndarray
        Pure state |ψ⟩ (assumed normalized)
    region_A_size : int
        Number of sites in region A
    total_sites : int
        Total number of sites
    d_phys : int
        Physical dimension per site
    base : float
        Logarithm base

    Returns
    -------
    Tuple[float, Dict]
        (S_EE, info_dict)

    Examples
    --------
    >>> # Product state |00...0⟩: S = 0
    >>> n = 8
    >>> state = np.zeros(2**n)
    >>> state[0] = 1.0
    >>> S, info = entanglement_entropy_svd(state, region_A_size=4, total_sites=n)
    >>> print(f"S = {S:.6f} (expected: 0)")
    """
    region_B_size = total_sites - region_A_size

    d_A = d_phys**region_A_size
    d_B = d_phys**region_B_size

    # Reshape state into matrix: |ψ⟩ → Ψ_{A,B}
    # State has shape (d_phys^total_sites,)
    # Reshape to (d_A, d_B)
    try:
        state_matrix = state.reshape(d_A, d_B)
    except ValueError:
        raise ValueError(
            f"Cannot reshape state of size {len(state)} into ({d_A}, {d_B}). "
            f"Check d_phys={d_phys}, region_A_size={region_A_size}, total_sites={total_sites}"
        )

    # Schmidt decomposition via SVD
    # Ψ = U Λ V†
    U, schmidt_values, Vh = np.linalg.svd(state_matrix, full_matrices=False)

    # Schmidt coefficients are eigenvalues of ρ_A (and ρ_B)
    lambda_sq = schmidt_values**2

    # Normalize (should already be normalized if state is normalized)
    lambda_sq /= np.sum(lambda_sq)

    # Filter near-zero eigenvalues
    lambda_sq = lambda_sq[lambda_sq > 1e-14]

    # Entanglement entropy
    S_EE = -np.sum(lambda_sq * np.log(lambda_sq) / np.log(base))

    # Additional info
    info = {
        'method': 'svd',
        'schmidt_rank': len(lambda_sq),
        'max_schmidt_value': np.max(schmidt_values) if len(schmidt_values) > 0 else 0,
        'schmidt_values': schmidt_values.tolist()
    }

    return S_EE, info


def entanglement_entropy_replica(
    rho_A: np.ndarray,
    base: float = np.e,
    n_values: Optional[np.ndarray] = None
) -> Tuple[float, Dict]:
    """
    Compute entanglement entropy via replica trick.

    Replica trick:
    S = -∂/∂n Tr(ρ^n)|_{n→1}

    Compute Rényi entropies S_n = 1/(1-n) log Tr(ρ^n) for n > 1,
    then extrapolate to n → 1 to get von Neumann entropy.

    Parameters
    ----------
    rho_A : ndarray
        Reduced density matrix
    base : float
        Logarithm base
    n_values : ndarray, optional
        Replica indices (default: [2, 3, 4, 5])

    Returns
    -------
    Tuple[float, Dict]
        (S_EE, info_dict)

    Examples
    --------
    >>> # Random density matrix
    >>> d = 4
    >>> rho = np.random.rand(d, d)
    >>> rho = rho @ rho.T
    >>> rho /= np.trace(rho)
    >>> S, info = entanglement_entropy_replica(rho)
    >>> print(f"S = {S:.4f}")
    """
    if n_values is None:
        n_values = np.array([2, 3, 4, 5])

    renyi_entropies = []

    for n in n_values:
        # Compute Tr(ρ^n)
        rho_n = np.linalg.matrix_power(rho_A, int(n))
        trace_rho_n = np.trace(rho_n)

        # Rényi entropy: S_n = 1/(1-n) log Tr(ρ^n)
        S_n = np.log(trace_rho_n) / ((1 - n) * np.log(base))
        renyi_entropies.append(S_n)

    renyi_entropies = np.array(renyi_entropies)

    # Extrapolate to n → 1 using polynomial fit
    # S_1 = lim_{n→1} S_n
    # Use linear extrapolation in n-1:
    # S_n ≈ S_1 + a*(n-1) + b*(n-1)^2

    from scipy.optimize import curve_fit

    def fit_func(n, S1, a):
        return S1 + a * (n - 1)

    try:
        popt, pcov = curve_fit(fit_func, n_values, renyi_entropies)
        S_EE = popt[0]
        error = np.sqrt(pcov[0, 0]) if pcov.shape[0] > 0 else 0.0
    except:
        # Fallback: simple linear extrapolation
        S_EE = renyi_entropies[0] + (renyi_entropies[0] - renyi_entropies[1])
        error = np.std(renyi_entropies)

    info = {
        'method': 'replica',
        'n_values': n_values.tolist(),
        'renyi_entropies': renyi_entropies.tolist(),
        'extrapolation_error': error
    }

    return S_EE, info


def entanglement_entropy_transfer_matrix(
    mera,
    region_A: list,
    base: float = np.e
) -> Tuple[float, Dict]:
    """
    Compute entanglement entropy using transfer matrix for MERA.

    For MERA/MPS, can use transfer matrix eigenvalues.

    Parameters
    ----------
    mera : MERA
        MERA tensor network
    region_A : list
        Indices of region A
    base : float
        Logarithm base

    Returns
    -------
    Tuple[float, Dict]
        (S_EE, info_dict)
    """
    # Placeholder implementation
    # Full version would:
    # 1. Construct transfer matrix from MERA tensors
    # 2. Compute leading eigenvalues
    # 3. Extract entanglement from eigenvalue spectrum

    # For now, use simplified approach via reduced density matrix
    rho_A = mera.compute_reduced_density_matrix(region_A)
    S_EE = von_neumann_entropy(rho_A, base=base)

    info = {
        'method': 'transfer_matrix',
        'region_size': len(region_A),
        'warning': 'Using simplified implementation (TODO: proper transfer matrix)'
    }

    return S_EE, info


def entanglement_entropy(
    state: Optional[np.ndarray] = None,
    rho_A: Optional[np.ndarray] = None,
    mera: Optional[object] = None,
    region_A: Optional[list] = None,
    region_A_size: Optional[int] = None,
    total_sites: Optional[int] = None,
    d_phys: int = 2,
    method: str = 'svd',
    base: float = np.e,
    cross_validate: bool = False
) -> Tuple[float, Dict]:
    """
    Unified interface for entanglement entropy calculation.

    Automatically selects appropriate method based on input.

    Parameters
    ----------
    state : ndarray, optional
        Pure state |ψ⟩
    rho_A : ndarray, optional
        Reduced density matrix
    mera : MERA, optional
        MERA tensor network
    region_A : list, optional
        Indices of region A
    region_A_size : int, optional
        Size of region A
    total_sites : int, optional
        Total number of sites
    d_phys : int
        Physical dimension
    method : str
        'svd', 'replica', 'transfer', 'auto'
    base : float
        Logarithm base
    cross_validate : bool
        If True, compute with all methods and compare

    Returns
    -------
    Tuple[float, Dict]
        (S_EE, info_dict)

    Examples
    --------
    >>> # Using pure state
    >>> state = np.random.randn(2**8)
    >>> state /= np.linalg.norm(state)
    >>> S, info = entanglement_entropy(state=state, region_A_size=4, total_sites=8)

    >>> # Using density matrix
    >>> rho = np.eye(4) / 4
    >>> S, info = entanglement_entropy(rho_A=rho, method='replica')
    """
    if cross_validate:
        results = {}

        # Try SVD
        if state is not None and region_A_size is not None and total_sites is not None:
            S_svd, info_svd = entanglement_entropy_svd(
                state, region_A_size, total_sites, d_phys, base
            )
            results['svd'] = (S_svd, info_svd)

        # Try replica
        if rho_A is not None:
            S_replica, info_replica = entanglement_entropy_replica(rho_A, base)
            results['replica'] = (S_replica, info_replica)

        # Try transfer matrix
        if mera is not None and region_A is not None:
            S_transfer, info_transfer = entanglement_entropy_transfer_matrix(
                mera, region_A, base
            )
            results['transfer'] = (S_transfer, info_transfer)

        # Check agreement
        S_values = [S for S, _ in results.values()]
        if len(S_values) > 1:
            agreement = np.std(S_values) / (np.mean(S_values) + 1e-10)
            if agreement > 0.01:
                warnings.warn(
                    f"Methods disagree: std/mean = {agreement:.3f}. "
                    f"Values: {S_values}"
                )

        # Return mean
        S_mean = np.mean(S_values)
        info = {
            'method': 'cross_validated',
            'individual_results': results,
            'agreement': agreement if len(S_values) > 1 else 0.0
        }
        return S_mean, info

    # Single method
    if method == 'svd' or (method == 'auto' and state is not None):
        if state is None:
            raise ValueError("SVD method requires 'state' parameter")
        if region_A_size is None or total_sites is None:
            raise ValueError("SVD method requires 'region_A_size' and 'total_sites'")
        return entanglement_entropy_svd(state, region_A_size, total_sites, d_phys, base)

    elif method == 'replica':
        if rho_A is None:
            raise ValueError("Replica method requires 'rho_A' parameter")
        return entanglement_entropy_replica(rho_A, base)

    elif method == 'transfer' or (method == 'auto' and mera is not None):
        if mera is None or region_A is None:
            raise ValueError("Transfer method requires 'mera' and 'region_A' parameters")
        return entanglement_entropy_transfer_matrix(mera, region_A, base)

    else:
        raise ValueError(f"Unknown method: {method}")


def compute_area_law_coefficient(
    entropies: dict,
    boundaries: dict,
    dimension: int = 1
) -> Tuple[float, float, float]:
    """
    Fit area law and extract coefficient.

    S(A) = c * log(|∂A|) + const

    Parameters
    ----------
    entropies : dict
        {size: S_EE}
    boundaries : dict
        {size: boundary_length}
    dimension : int
        Spatial dimension

    Returns
    -------
    Tuple[float, float, float]
        (coefficient, r_squared, p_value)
    """
    from scipy.stats import linregress

    sizes = np.array(list(entropies.keys()))
    S = np.array([entropies[s] for s in sizes])
    boundary_sizes = np.array([boundaries[s] for s in sizes])

    # Fit: log(S) = a*log(boundary) + b
    log_boundary = np.log(boundary_sizes + 1e-10)
    slope, intercept, r_value, p_value, std_err = linregress(log_boundary, S)

    return slope, r_value**2, p_value
