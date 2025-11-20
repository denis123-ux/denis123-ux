"""
Sanity checks for quantum gravity computations.

These are basic physical and mathematical constraints that MUST hold.
Any violation indicates a bug or numerical instability.

Categories:
- Quantum information constraints (entropy bounds, subadditivity, etc.)
- Geometric constraints (metric signature, positive det, etc.)
- Numerical stability checks
"""

import numpy as np
from typing import Dict, Any, Optional, List
import warnings


class SanityCheckError(Exception):
    """Raised when a critical sanity check fails."""
    pass


def check_entanglement_entropy_bounds(
    S: float,
    dim_hilbert: int,
    region_name: str = "A",
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Check entanglement entropy satisfies basic bounds.

    Physical constraints:
    1. S ≥ 0 (non-negative)
    2. S ≤ log(dim) (maximal entropy bound)

    Args:
        S: Entanglement entropy value
        dim_hilbert: Dimension of Hilbert space for region
        region_name: Name of region for error messages
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results

    Raises:
        SanityCheckError: If critical bounds violated
    """
    results = {
        'region': region_name,
        'entropy': S,
        'dim_hilbert': dim_hilbert,
        'passed': True,
        'violations': []
    }

    # Check 1: Non-negativity
    if S < -tolerance:
        results['passed'] = False
        results['violations'].append(f"Negative entropy: S = {S:.6f} < 0")
        raise SanityCheckError(f"Negative entropy for region {region_name}: S = {S}")

    # Check 2: Upper bound
    max_entropy = np.log(dim_hilbert)
    if S > max_entropy + tolerance:
        results['passed'] = False
        results['violations'].append(
            f"Entropy exceeds maximum: S = {S:.6f} > log(dim) = {max_entropy:.6f}"
        )
        warnings.warn(f"Entropy exceeds maximum for region {region_name}")

    # Check 3: Pure state check (for total system)
    if region_name == "total_system" and S > tolerance:
        results['violations'].append(
            f"Total system not pure: S_total = {S:.6f} > 0"
        )
        warnings.warn("Total system entropy should be zero for pure states")

    return results


def check_strong_subadditivity(
    S_A: float,
    S_B: float,
    S_C: float,
    S_AB: float,
    S_BC: float,
    S_AC: float,
    S_ABC: float,
    tolerance: float = 1e-5
) -> Dict[str, Any]:
    """
    Check strong subadditivity of entanglement entropy.

    Strong subadditivity (SSA):
    S(ABC) + S(B) ≤ S(AB) + S(BC)

    This is a fundamental property of quantum entanglement.

    Args:
        S_A, S_B, S_C: Individual entropies
        S_AB, S_BC, S_AC: Pairwise entropies
        S_ABC: Triple entropy
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results
    """
    # SSA inequality
    lhs = S_ABC + S_B
    rhs = S_AB + S_BC
    violation = lhs - rhs

    # Subadditivity: S(AB) ≤ S(A) + S(B)
    subadditivity_checks = {
        'S(AB) <= S(A) + S(B)': S_AB <= S_A + S_B + tolerance,
        'S(BC) <= S(B) + S(C)': S_BC <= S_B + S_C + tolerance,
        'S(AC) <= S(A) + S(C)': S_AC <= S_A + S_C + tolerance,
    }

    results = {
        'strong_subadditivity': {
            'lhs': lhs,
            'rhs': rhs,
            'violation': violation,
            'passed': violation <= tolerance
        },
        'subadditivity': subadditivity_checks,
        'all_passed': all(subadditivity_checks.values()) and (violation <= tolerance)
    }

    if violation > tolerance:
        warnings.warn(f"Strong subadditivity violated by {violation:.6e}")

    return results


def check_area_law_properties(
    entropies: Dict[int, float],
    boundary_lengths: Dict[int, int],
    system_dimension: int = 1,
    tolerance: float = 0.1
) -> Dict[str, Any]:
    """
    Check area law properties for entanglement entropy.

    For ground states of local Hamiltonians:
    S(A) ~ |∂A|^(d-1) (area law)
    NOT ~ |A|^d (volume law)

    Args:
        entropies: Dictionary mapping region size to entropy
        boundary_lengths: Dictionary mapping region size to boundary length
        system_dimension: Spatial dimension
        tolerance: Tolerance for area law violation

    Returns:
        Dictionary with check results
    """
    sizes = np.array(sorted(entropies.keys()))
    S_values = np.array([entropies[s] for s in sizes])
    boundary_values = np.array([boundary_lengths[s] for s in sizes])

    # Check if entropy grows with area (not volume)
    # For 1D: area = boundary points (constant = 2)
    # For 2D: area = perimeter ~ L
    # For 3D: area ~ L^2

    # Fit: S ~ boundary^α
    # Area law: α ~ 1
    # Volume law: α ~ d/(d-1)

    log_boundary = np.log(boundary_values + 1e-10)
    log_S = np.log(S_values + 1e-10)

    # Only fit where we have variation
    if len(np.unique(boundary_values)) > 1:
        slope, intercept = np.polyfit(log_boundary, log_S, 1)
        expected_slope = 1.0  # Area law
        volume_slope = system_dimension  # Volume law

        deviation_from_area = abs(slope - expected_slope)
        deviation_from_volume = abs(slope - volume_slope)

        is_area_law = deviation_from_area < deviation_from_volume

        results = {
            'slope': slope,
            'expected_area_law_slope': expected_slope,
            'expected_volume_law_slope': volume_slope,
            'is_area_law': is_area_law,
            'passed': is_area_law,
            'message': 'Area law satisfied' if is_area_law else 'Possible volume law violation'
        }
    else:
        results = {
            'message': 'Insufficient data for area law check',
            'passed': None
        }

    return results


def check_density_matrix_valid(
    rho: np.ndarray,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Check density matrix satisfies all required properties.

    Properties:
    1. Hermitian: ρ = ρ†
    2. Positive semi-definite: all eigenvalues ≥ 0
    3. Unit trace: Tr(ρ) = 1

    Args:
        rho: Density matrix
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results
    """
    results = {
        'passed': True,
        'violations': []
    }

    # Check 1: Hermitian
    if not np.allclose(rho, rho.conj().T, atol=tolerance):
        results['passed'] = False
        results['violations'].append('Not Hermitian')
        hermiticity_error = np.max(np.abs(rho - rho.conj().T))
        results['hermiticity_error'] = hermiticity_error

    # Check 2: Positive semi-definite
    eigenvalues = np.linalg.eigvalsh(rho)
    min_eigenvalue = np.min(eigenvalues)

    if min_eigenvalue < -tolerance:
        results['passed'] = False
        results['violations'].append(f'Negative eigenvalue: {min_eigenvalue:.6e}')

    results['min_eigenvalue'] = min_eigenvalue
    results['max_eigenvalue'] = np.max(eigenvalues)

    # Check 3: Unit trace
    trace = np.trace(rho)
    if not np.isclose(trace, 1.0, atol=tolerance):
        results['passed'] = False
        results['violations'].append(f'Trace not unity: Tr(ρ) = {trace:.6f}')

    results['trace'] = trace

    if not results['passed']:
        warnings.warn(f"Invalid density matrix: {results['violations']}")

    return results


def check_metric_properties(
    metric: np.ndarray,
    expected_signature: Optional[str] = None,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Check metric tensor properties.

    Properties:
    1. Symmetric: g_μν = g_νμ
    2. Non-degenerate: det(g) ≠ 0
    3. Correct signature (Lorentzian: (-,+,+,+) or Euclidean: (+,+,+,+))

    Args:
        metric: Metric tensor
        expected_signature: 'lorentzian' or 'euclidean'
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results
    """
    results = {
        'passed': True,
        'violations': []
    }

    # Check 1: Symmetric
    if not np.allclose(metric, metric.T, atol=tolerance):
        results['passed'] = False
        results['violations'].append('Not symmetric')

    # Check 2: Non-degenerate
    det = np.linalg.det(metric)
    results['determinant'] = det

    if abs(det) < tolerance:
        results['passed'] = False
        results['violations'].append(f'Nearly degenerate: det(g) = {det:.6e}')

    # Check 3: Signature
    eigenvalues = np.linalg.eigvalsh(metric)
    n_positive = np.sum(eigenvalues > tolerance)
    n_negative = np.sum(eigenvalues < -tolerance)
    n_zero = len(eigenvalues) - n_positive - n_negative

    results['eigenvalues'] = eigenvalues
    results['signature'] = f"({n_negative}, {n_positive}, {n_zero})"

    if expected_signature == 'lorentzian':
        # Should be (-,+,+,...,+) → (1 negative, d positive)
        if n_negative != 1 or n_zero != 0:
            results['violations'].append(
                f"Expected Lorentzian signature (1 negative), got {results['signature']}"
            )
    elif expected_signature == 'euclidean':
        # Should be (+,+,...,+) → (0 negative, d+1 positive)
        if n_negative != 0 or n_zero != 0:
            results['violations'].append(
                f"Expected Euclidean signature (all positive), got {results['signature']}"
            )

    if results['violations']:
        results['passed'] = False

    return results


def check_numerical_stability(
    value: float,
    name: str = "value",
    max_value: Optional[float] = 1e10,
    min_value: Optional[float] = -1e10
) -> Dict[str, Any]:
    """
    Check for numerical instabilities (inf, nan, overflow).

    Args:
        value: Value to check
        name: Name for error messages
        max_value: Maximum allowed value
        min_value: Minimum allowed value

    Returns:
        Dictionary with check results
    """
    results = {
        'value': value,
        'passed': True,
        'issues': []
    }

    # Check for nan
    if np.isnan(value):
        results['passed'] = False
        results['issues'].append('NaN detected')
        raise SanityCheckError(f"NaN detected in {name}")

    # Check for inf
    if np.isinf(value):
        results['passed'] = False
        results['issues'].append('Inf detected')
        raise SanityCheckError(f"Inf detected in {name}")

    # Check bounds
    if max_value is not None and value > max_value:
        results['passed'] = False
        results['issues'].append(f'Value {value:.3e} exceeds maximum {max_value:.3e}')
        warnings.warn(f"Possible overflow in {name}")

    if min_value is not None and value < min_value:
        results['passed'] = False
        results['issues'].append(f'Value {value:.3e} below minimum {min_value:.3e}')
        warnings.warn(f"Possible underflow in {name}")

    return results


def check_conservation_law(
    values: List[float],
    expected_sum: float = 0.0,
    tolerance: float = 1e-5,
    law_name: str = "Conservation"
) -> Dict[str, Any]:
    """
    Check conservation law (e.g., stress tensor conservation ∇·T = 0).

    Args:
        values: List of values that should sum to expected_sum
        expected_sum: Expected sum (usually 0)
        tolerance: Tolerance for violation
        law_name: Name of conservation law

    Returns:
        Dictionary with check results
    """
    actual_sum = np.sum(values)
    violation = abs(actual_sum - expected_sum)

    results = {
        'law': law_name,
        'expected_sum': expected_sum,
        'actual_sum': actual_sum,
        'violation': violation,
        'passed': violation < tolerance
    }

    if not results['passed']:
        warnings.warn(f"{law_name} violated by {violation:.6e}")

    return results


def comprehensive_validation_report(
    all_checks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate comprehensive validation report from multiple checks.

    Args:
        all_checks: List of check result dictionaries

    Returns:
        Summary report
    """
    total_checks = len(all_checks)
    passed_checks = sum(1 for check in all_checks if check.get('passed', False))
    failed_checks = total_checks - passed_checks

    report = {
        'total_checks': total_checks,
        'passed': passed_checks,
        'failed': failed_checks,
        'pass_rate': passed_checks / total_checks if total_checks > 0 else 0,
        'all_passed': failed_checks == 0,
        'failed_checks_details': [
            check for check in all_checks if not check.get('passed', False)
        ]
    }

    return report
