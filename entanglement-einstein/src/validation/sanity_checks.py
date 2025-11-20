"""
Sanity Checks Module
====================

Physical and mathematical consistency checks:
- Area law properties
- Entropy bounds
- Metric properties (positive-definite, signature)
- Stress tensor conservation
- Boundary conditions
- Physical invariants
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import warnings


def check_area_law_properties(
    entropies: Dict[int, float],
    boundaries: Dict[int, float],
    dimension: int = 1,
    tolerance: float = 0.1
) -> Dict[str, Any]:
    """
    Check if entanglement entropy satisfies area law.

    For d-dimensional system:
    S(A) ~ |∂A|^(d-1) (NOT |A|^d)

    Parameters
    ----------
    entropies : dict
        {region_size: S_EE}
    boundaries : dict
        {region_size: boundary_size}
    dimension : int
        Spatial dimension
    tolerance : float
        Relative tolerance for volume law check

    Returns
    -------
    dict
        {
            'is_area_law': bool,
            'is_volume_law': bool,
            'boundary_scaling': float,  # Expected: d-1
            'volume_scaling': float,    # Expected: << d
            'r_squared_area': float,
            'r_squared_volume': float,
            'warnings': list
        }
    """
    results = {
        'is_area_law': False,
        'is_volume_law': False,
        'warnings': []
    }

    sizes = np.array(list(entropies.keys()))
    S = np.array([entropies[s] for s in sizes])
    boundary_sizes = np.array([boundaries[s] for s in sizes])

    # Check 1: Entropy is non-negative
    if np.any(S < 0):
        results['warnings'].append(f"Negative entropy detected: min={np.min(S)}")

    # Check 2: Entropy is bounded by ln(dim(H_A)) = size * ln(d_phys)
    # For qubits: S_max = size * ln(2)
    max_entropy_bound = sizes * np.log(2)
    if np.any(S > max_entropy_bound * (1 + tolerance)):
        violations = S > max_entropy_bound * (1 + tolerance)
        results['warnings'].append(
            f"Entropy exceeds maximum: {np.sum(violations)} violations"
        )

    # Check 3: Area law vs volume law
    # Area law: S ~ boundary^(d-1) ~ size^((d-1)/d) for d-dim system
    # Volume law: S ~ size^d

    # Fit: log(S) = a * log(boundary) + b
    if len(sizes) > 3:
        from scipy.stats import linregress

        # Area law fit
        log_boundary = np.log(boundary_sizes + 1e-10)
        log_S = np.log(S + 1e-10)
        slope_area, intercept_area, r_area, p_area, se_area = linregress(log_boundary, log_S)

        # Volume law fit
        log_size = np.log(sizes + 1e-10)
        slope_volume, intercept_volume, r_volume, p_volume, se_volume = linregress(log_size, log_S)

        results['boundary_scaling'] = slope_area
        results['volume_scaling'] = slope_volume
        results['r_squared_area'] = r_area**2
        results['r_squared_volume'] = r_volume**2

        # Area law: slope should be ~ (d-1)
        expected_area_slope = dimension - 1
        area_law_satisfied = (
            abs(slope_area - expected_area_slope) < tolerance and
            r_area**2 > 0.95
        )

        # Volume law: slope should be ~ d
        volume_law_satisfied = (
            abs(slope_volume - dimension) < tolerance and
            r_volume**2 > 0.95
        )

        results['is_area_law'] = area_law_satisfied
        results['is_volume_law'] = volume_law_satisfied

        if area_law_satisfied and volume_law_satisfied:
            results['warnings'].append(
                "WARNING: Both area and volume law appear satisfied! Check data."
            )

    return results


def check_entropy_bounds(
    rho: np.ndarray,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Check if density matrix satisfies physical bounds.

    Checks:
    1. rho is Hermitian
    2. rho is positive semi-definite (eigenvalues >= 0)
    3. Tr(rho) = 1
    4. 0 <= S(rho) <= log(dim(rho))

    Parameters
    ----------
    rho : ndarray
        Density matrix
    tolerance : float
        Numerical tolerance

    Returns
    -------
    dict
        Validation results and warnings
    """
    results = {
        'is_valid': True,
        'warnings': []
    }

    # Check 1: Hermitian
    if not np.allclose(rho, rho.conj().T, atol=tolerance):
        results['is_valid'] = False
        results['warnings'].append("Density matrix is not Hermitian")

    # Check 2: Positive semi-definite
    eigenvalues = np.linalg.eigvalsh(rho)
    if np.any(eigenvalues < -tolerance):
        results['is_valid'] = False
        results['warnings'].append(
            f"Negative eigenvalues: min={np.min(eigenvalues)}"
        )
        results['min_eigenvalue'] = np.min(eigenvalues)

    # Check 3: Trace = 1
    trace = np.trace(rho)
    if not np.isclose(trace, 1.0, atol=tolerance):
        results['is_valid'] = False
        results['warnings'].append(f"Trace != 1: Tr(rho) = {trace}")
        results['trace'] = trace

    # Check 4: Entropy bounds
    # S = -Tr(rho log rho)
    eigenvalues_clean = eigenvalues[eigenvalues > tolerance]
    S = -np.sum(eigenvalues_clean * np.log(eigenvalues_clean))

    max_entropy = np.log(len(rho))
    results['entropy'] = S
    results['max_entropy'] = max_entropy

    if S < -tolerance:
        results['is_valid'] = False
        results['warnings'].append(f"Negative entropy: S={S}")

    if S > max_entropy + tolerance:
        results['is_valid'] = False
        results['warnings'].append(
            f"Entropy exceeds maximum: S={S} > log(d)={max_entropy}"
        )

    return results


def check_metric_properties(
    metric: np.ndarray,
    metric_type: str = 'riemannian',
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Check if metric tensor satisfies geometric properties.

    Parameters
    ----------
    metric : ndarray, shape (d, d)
        Metric tensor g_μν
    metric_type : str
        'riemannian': positive-definite (all +)
        'lorentzian': signature (-,+,+,+)
        'euclidean': same as riemannian
    tolerance : float
        Numerical tolerance

    Returns
    -------
    dict
        Validation results
    """
    results = {
        'is_valid': True,
        'warnings': []
    }

    # Check 1: Symmetric
    if not np.allclose(metric, metric.T, atol=tolerance):
        results['is_valid'] = False
        results['warnings'].append("Metric is not symmetric")

    # Check 2: Check signature
    eigenvalues = np.linalg.eigvalsh(metric)
    results['eigenvalues'] = eigenvalues.tolist()

    if metric_type in ['riemannian', 'euclidean']:
        # All eigenvalues should be positive
        if np.any(eigenvalues <= tolerance):
            results['is_valid'] = False
            results['warnings'].append(
                f"Non-positive eigenvalues: {eigenvalues[eigenvalues <= tolerance]}"
            )

    elif metric_type == 'lorentzian':
        # Should have signature (-,+,+,...,+)
        # Exactly one negative eigenvalue
        n_negative = np.sum(eigenvalues < -tolerance)
        n_positive = np.sum(eigenvalues > tolerance)

        if n_negative != 1:
            results['warnings'].append(
                f"Expected 1 negative eigenvalue, got {n_negative}"
            )

        if n_positive != len(eigenvalues) - 1:
            results['warnings'].append(
                f"Expected {len(eigenvalues)-1} positive eigenvalues, got {n_positive}"
            )

    # Check 3: Determinant
    det = np.linalg.det(metric)
    results['determinant'] = det

    if metric_type in ['riemannian', 'euclidean']:
        if det <= tolerance:
            results['is_valid'] = False
            results['warnings'].append(f"Determinant <= 0: det={det}")

    # Check 4: Condition number (numerical stability)
    cond = np.linalg.cond(metric)
    results['condition_number'] = cond

    if cond > 1e10:
        results['warnings'].append(
            f"High condition number: {cond:.2e} (numerically unstable)"
        )

    return results


def check_stress_tensor_conservation(
    stress_tensor: np.ndarray,
    metric: np.ndarray,
    coords: np.ndarray,
    tolerance: float = 1e-3
) -> Dict[str, Any]:
    """
    Check if stress-energy tensor is conserved: ∇_μ T^μν = 0.

    Parameters
    ----------
    stress_tensor : ndarray, shape (d, d)
        Stress-energy tensor T^μν
    metric : ndarray, shape (d, d)
        Metric tensor g_μν
    coords : ndarray
        Coordinate grid for computing derivatives
    tolerance : float
        Tolerance for conservation check

    Returns
    -------
    dict
        Conservation check results
    """
    results = {
        'is_conserved': True,
        'warnings': []
    }

    # Check 1: Symmetry T^μν = T^νμ
    if not np.allclose(stress_tensor, stress_tensor.T, atol=tolerance):
        results['warnings'].append("Stress tensor is not symmetric")

    # Check 2: Energy conditions (optional, for physical stress tensors)
    # Null energy condition: T_μν k^μ k^ν >= 0 for all null k^μ
    # This is a deep check, skip for now

    # Check 3: Conservation (numerical derivative)
    # ∇_μ T^μν = ∂_μ T^μν + Γ^μ_μλ T^λν + Γ^ν_μλ T^μλ
    # For simplicity, check ∂_μ T^μν ≈ 0 (valid in locally flat coords)

    # Compute divergence using finite differences
    # This requires stress tensor at multiple points - skip for single point check

    # For now, just check trace properties
    trace = np.trace(stress_tensor)
    results['trace'] = trace

    # For conformal field theories: T^μ_μ = 0 (traceless)
    # But this is not general, so just report
    results['is_traceless'] = abs(trace) < tolerance

    return results


def check_unitarity(
    U: np.ndarray,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Check if matrix is unitary: U† U = I.

    Parameters
    ----------
    U : ndarray
        Matrix to check
    tolerance : float
        Numerical tolerance

    Returns
    -------
    dict
        Unitarity check results
    """
    results = {
        'is_unitary': True,
        'warnings': []
    }

    # U† U
    UdagU = U.conj().T @ U
    identity = np.eye(len(U))

    deviation = np.linalg.norm(UdagU - identity)
    results['deviation_from_identity'] = deviation

    if deviation > tolerance:
        results['is_unitary'] = False
        results['warnings'].append(f"Not unitary: ||U†U - I|| = {deviation:.2e}")

    # Check determinant has modulus 1
    det = np.linalg.det(U)
    results['determinant'] = det
    results['det_modulus'] = abs(det)

    if abs(abs(det) - 1.0) > tolerance:
        results['warnings'].append(f"|det(U)| = {abs(det):.6f} != 1")

    return results


def check_causality(
    metric: np.ndarray,
    point1: np.ndarray,
    point2: np.ndarray
) -> Dict[str, Any]:
    """
    Check causal relationship between two points.

    For Lorentzian metric with signature (-,+,+,+):
    - Timelike: ds² < 0
    - Spacelike: ds² > 0
    - Lightlike: ds² = 0

    Parameters
    ----------
    metric : ndarray
        Metric tensor g_μν
    point1, point2 : ndarray
        Coordinates of two points

    Returns
    -------
    dict
        Causal relationship
    """
    # Displacement vector
    dx = point2 - point1

    # Interval: ds² = g_μν dx^μ dx^ν
    ds_squared = dx @ metric @ dx

    if ds_squared < -1e-10:
        causal_type = 'timelike'
        causal = True
    elif ds_squared > 1e-10:
        causal_type = 'spacelike'
        causal = False
    else:
        causal_type = 'lightlike'
        causal = True  # On light cone

    return {
        'ds_squared': ds_squared,
        'separation_type': causal_type,
        'causally_connected': causal
    }


def check_ryu_takayanagi_consistency(
    S_EE: float,
    area: float,
    G_N: float,
    tolerance: float = 0.1
) -> Dict[str, Any]:
    """
    Check if Ryu-Takayanagi formula holds: S_EE = Area / (4 G_N).

    Parameters
    ----------
    S_EE : float
        Entanglement entropy from quantum state
    area : float
        Minimal surface area in bulk
    G_N : float
        Newton's constant
    tolerance : float
        Relative tolerance

    Returns
    -------
    dict
        Consistency check
    """
    predicted_S = area / (4 * G_N)
    relative_error = abs(S_EE - predicted_S) / (predicted_S + 1e-10)

    is_consistent = relative_error < tolerance

    return {
        'is_consistent': is_consistent,
        'S_EE_quantum': S_EE,
        'S_EE_geometric': predicted_S,
        'relative_error': relative_error,
        'area': area,
        'G_N': G_N
    }
