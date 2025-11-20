"""
Sanity checks for physical and mathematical validity.

These checks ensure that computed quantities satisfy basic physical
requirements and mathematical constraints.
"""

import numpy as np
from typing import Dict, Any, List, Optional


def check_entropy_properties(
    entropy: float,
    system_size: int,
    d_phys: int = 2
) -> Dict[str, Any]:
    """
    Check if entanglement entropy satisfies basic properties.

    Properties:
    1. S >= 0 (non-negative)
    2. S <= log(d^N) where d = physical dimension, N = system size
    3. S is finite

    Args:
        entropy: Computed entanglement entropy
        system_size: Size of subsystem
        d_phys: Physical dimension per site

    Returns:
        Dictionary with check results
    """
    checks = {}

    # Non-negative
    checks['non_negative'] = {
        'passed': entropy >= 0,
        'value': entropy,
        'message': 'Entropy must be non-negative'
    }

    # Upper bound
    max_entropy = system_size * np.log(d_phys)
    checks['upper_bound'] = {
        'passed': entropy <= max_entropy + 1e-10,  # Small tolerance
        'value': entropy,
        'max_value': max_entropy,
        'message': f'Entropy must be <= log(d^N) = {max_entropy:.4f}'
    }

    # Finite
    checks['finite'] = {
        'passed': np.isfinite(entropy),
        'value': entropy,
        'message': 'Entropy must be finite'
    }

    # Overall
    all_passed = all(check['passed'] for check in checks.values())

    return {
        'all_passed': all_passed,
        'checks': checks
    }


def check_area_law_scaling(
    entropies: Dict[int, float],
    tolerance: float = 0.2
) -> Dict[str, Any]:
    """
    Check if entropies satisfy area law scaling.

    For 1D systems, area law means S ~ log(L) not S ~ L.

    Args:
        entropies: Dictionary mapping subsystem size to entropy
        tolerance: Tolerance for scaling exponent

    Returns:
        Dictionary with check results
    """
    sizes = np.array(list(entropies.keys()))
    S_values = np.array(list(entropies.values()))

    # Fit to power law: S ~ L^α
    log_sizes = np.log(sizes)
    log_S = np.log(S_values + 1e-10)  # Avoid log(0)

    # Linear regression
    from scipy.stats import linregress
    result = linregress(log_sizes, log_S)
    exponent = result.slope

    # Area law in 1D means α < 1 (ideally α ~ 0 for log scaling)
    area_law_satisfied = exponent < 1.0 + tolerance

    return {
        'area_law_satisfied': area_law_satisfied,
        'exponent': exponent,
        'expected_range': (0, 1),
        'message': f'Area law: S ~ L^α with α = {exponent:.4f} (should be < 1)'
    }


def check_mutual_information_properties(
    I_AB: float,
    S_A: float,
    S_B: float,
    S_AB: float,
    tolerance: float = 1e-8
) -> Dict[str, Any]:
    """
    Check mutual information satisfies required properties.

    Properties:
    1. I(A:B) >= 0 (non-negative)
    2. I(A:B) = S(A) + S(B) - S(AB)
    3. I(A:B) <= min(S(A), S(B))
    4. Strong subadditivity: I(A:B) <= S(A) and I(A:B) <= S(B)

    Args:
        I_AB: Computed mutual information
        S_A, S_B, S_AB: Individual entanglement entropies
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results
    """
    checks = {}

    # Non-negative
    checks['non_negative'] = {
        'passed': I_AB >= -tolerance,
        'value': I_AB,
        'message': 'Mutual information must be non-negative'
    }

    # Definition check
    I_computed = S_A + S_B - S_AB
    checks['definition'] = {
        'passed': abs(I_AB - I_computed) < tolerance,
        'value': I_AB,
        'expected': I_computed,
        'difference': abs(I_AB - I_computed),
        'message': 'I(A:B) = S(A) + S(B) - S(AB)'
    }

    # Upper bound
    min_entropy = min(S_A, S_B)
    checks['upper_bound'] = {
        'passed': I_AB <= min_entropy + tolerance,
        'value': I_AB,
        'max_value': min_entropy,
        'message': 'I(A:B) <= min(S(A), S(B))'
    }

    # Finite
    checks['finite'] = {
        'passed': np.isfinite(I_AB),
        'value': I_AB,
        'message': 'Mutual information must be finite'
    }

    all_passed = all(check['passed'] for check in checks.values())

    return {
        'all_passed': all_passed,
        'checks': checks
    }


def check_density_matrix_properties(
    rho: np.ndarray,
    tolerance: float = 1e-8
) -> Dict[str, Any]:
    """
    Check if density matrix is valid.

    Properties:
    1. Hermitian: ρ = ρ†
    2. Positive semi-definite: eigenvalues >= 0
    3. Trace one: Tr(ρ) = 1
    4. ρ² <= ρ (idempotent for pure states)

    Args:
        rho: Density matrix
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results
    """
    checks = {}

    # Hermitian
    hermitian_error = np.linalg.norm(rho - rho.conj().T)
    checks['hermitian'] = {
        'passed': hermitian_error < tolerance,
        'error': hermitian_error,
        'message': 'Density matrix must be Hermitian'
    }

    # Positive semi-definite
    eigenvalues = np.linalg.eigvalsh(rho)
    min_eigenvalue = np.min(eigenvalues)
    checks['positive_semidefinite'] = {
        'passed': min_eigenvalue >= -tolerance,
        'min_eigenvalue': min_eigenvalue,
        'message': 'All eigenvalues must be >= 0'
    }

    # Trace one
    trace = np.trace(rho)
    checks['trace_one'] = {
        'passed': abs(trace - 1.0) < tolerance,
        'trace': trace,
        'error': abs(trace - 1.0),
        'message': 'Trace must equal 1'
    }

    # Valid probability distribution
    if checks['positive_semidefinite']['passed']:
        checks['valid_probabilities'] = {
            'passed': np.all(eigenvalues <= 1.0 + tolerance),
            'max_eigenvalue': np.max(eigenvalues),
            'message': 'All eigenvalues must be <= 1'
        }

    all_passed = all(check['passed'] for check in checks.values())

    return {
        'all_passed': all_passed,
        'checks': checks,
        'eigenvalues': eigenvalues
    }


def check_tensor_properties(
    tensor: np.ndarray,
    should_be_unitary: bool = False,
    should_be_normalized: bool = True,
    tolerance: float = 1e-8
) -> Dict[str, Any]:
    """
    Check tensor network properties.

    Args:
        tensor: Tensor to check
        should_be_unitary: Whether tensor should be unitary
        should_be_normalized: Whether tensor should be normalized
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results
    """
    checks = {}

    # Finite
    checks['finite'] = {
        'passed': np.all(np.isfinite(tensor)),
        'message': 'All tensor elements must be finite'
    }

    # Normalized
    if should_be_normalized:
        norm = np.linalg.norm(tensor)
        checks['normalized'] = {
            'passed': abs(norm - 1.0) < tolerance,
            'norm': norm,
            'message': 'Tensor should be normalized'
        }

    # Unitary (for square matrices)
    if should_be_unitary and tensor.ndim == 2 and tensor.shape[0] == tensor.shape[1]:
        identity = np.eye(tensor.shape[0])
        product = tensor @ tensor.conj().T
        unitary_error = np.linalg.norm(product - identity)
        checks['unitary'] = {
            'passed': unitary_error < tolerance,
            'error': unitary_error,
            'message': 'Tensor should be unitary'
        }

    all_passed = all(check['passed'] for check in checks.values())

    return {
        'all_passed': all_passed,
        'checks': checks
    }


def check_metric_properties(
    metric: np.ndarray,
    tolerance: float = 1e-8
) -> Dict[str, Any]:
    """
    Check if metric tensor satisfies required properties.

    Properties:
    1. Symmetric: g_μν = g_νμ
    2. Non-degenerate: det(g) != 0
    3. Signature: Has correct number of +/- eigenvalues

    Args:
        metric: Metric tensor
        tolerance: Numerical tolerance

    Returns:
        Dictionary with check results
    """
    checks = {}

    # Symmetric
    symmetry_error = np.linalg.norm(metric - metric.T)
    checks['symmetric'] = {
        'passed': symmetry_error < tolerance,
        'error': symmetry_error,
        'message': 'Metric must be symmetric'
    }

    # Non-degenerate
    det = np.linalg.det(metric)
    checks['non_degenerate'] = {
        'passed': abs(det) > tolerance,
        'determinant': det,
        'message': 'Metric must be non-degenerate'
    }

    # Eigenvalues for signature
    eigenvalues = np.linalg.eigvalsh(metric)
    n_positive = np.sum(eigenvalues > tolerance)
    n_negative = np.sum(eigenvalues < -tolerance)
    n_zero = len(eigenvalues) - n_positive - n_negative

    checks['signature'] = {
        'n_positive': n_positive,
        'n_negative': n_negative,
        'n_zero': n_zero,
        'eigenvalues': eigenvalues,
        'message': f'Signature: ({n_positive}, {n_negative}, {n_zero})'
    }

    all_passed = all(check['passed'] for check in checks.values() if 'passed' in check)

    return {
        'all_passed': all_passed,
        'checks': checks
    }


def check_einstein_equation_residual(
    G_tensor: np.ndarray,
    T_tensor: np.ndarray,
    G_N: float = 1.0,
    tolerance: float = 1e-3
) -> Dict[str, Any]:
    """
    Check residual of Einstein equations: G_μν = 8πG_N T_μν

    Args:
        G_tensor: Einstein tensor
        T_tensor: Stress-energy tensor
        G_N: Newton's constant
        tolerance: Acceptable relative error

    Returns:
        Dictionary with check results
    """
    # Compute residual
    expected = 8 * np.pi * G_N * T_tensor
    residual = G_tensor - expected

    # Relative error
    G_norm = np.linalg.norm(G_tensor)
    residual_norm = np.linalg.norm(residual)

    if G_norm > 1e-10:
        relative_error = residual_norm / G_norm
    else:
        relative_error = residual_norm

    satisfied = relative_error < tolerance

    return {
        'satisfied': satisfied,
        'relative_error': relative_error,
        'absolute_error': residual_norm,
        'tolerance': tolerance,
        'residual': residual,
        'message': f'Einstein equations: relative error = {relative_error:.6f}'
    }


def run_all_sanity_checks(
    data: Dict[str, Any],
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run all applicable sanity checks on provided data.

    Args:
        data: Dictionary containing quantities to check
        verbose: Print results

    Returns:
        Dictionary with all check results
    """
    results = {}

    # Check entanglement entropy if provided
    if 'entropy' in data:
        results['entropy'] = check_entropy_properties(
            data['entropy'],
            data.get('system_size', 1),
            data.get('d_phys', 2)
        )

    # Check density matrix if provided
    if 'density_matrix' in data:
        results['density_matrix'] = check_density_matrix_properties(
            data['density_matrix']
        )

    # Check area law if entropies dict provided
    if 'entropies' in data:
        results['area_law'] = check_area_law_scaling(data['entropies'])

    # Check mutual information if provided
    if all(k in data for k in ['I_AB', 'S_A', 'S_B', 'S_AB']):
        results['mutual_information'] = check_mutual_information_properties(
            data['I_AB'], data['S_A'], data['S_B'], data['S_AB']
        )

    # Check metric if provided
    if 'metric' in data:
        results['metric'] = check_metric_properties(data['metric'])

    # Check Einstein equations if provided
    if 'G_tensor' in data and 'T_tensor' in data:
        results['einstein_equations'] = check_einstein_equation_residual(
            data['G_tensor'],
            data['T_tensor'],
            data.get('G_N', 1.0)
        )

    # Overall status
    all_passed = all(
        result.get('all_passed', result.get('satisfied', True))
        for result in results.values()
    )

    if verbose:
        print("\n" + "="*60)
        print("SANITY CHECKS SUMMARY")
        print("="*60)

        for check_name, check_result in results.items():
            status = "✓ PASS" if check_result.get('all_passed', check_result.get('satisfied', False)) else "✗ FAIL"
            print(f"{check_name:30s} {status}")

        print("="*60)
        print(f"Overall: {'✓ ALL PASSED' if all_passed else '✗ SOME FAILED'}")
        print("="*60 + "\n")

    return {
        'all_passed': all_passed,
        'individual_checks': results
    }
