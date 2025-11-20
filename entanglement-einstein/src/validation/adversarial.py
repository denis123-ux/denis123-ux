"""
Adversarial testing for quantum gravity computations.

Purpose: Stress-test functions with edge cases, extreme values, and adversarial inputs
to ensure robustness and catch bugs before they affect results.
"""

import numpy as np
from typing import Callable, List, Dict, Any, Optional


def test_with_noise(
    func: Callable,
    input_data: np.ndarray,
    noise_levels: List[float] = [0.01, 0.1, 0.5],
    n_trials: int = 10
) -> Dict[str, Any]:
    """
    Test function with noisy inputs.

    Args:
        func: Function to test
        input_data: Clean input data
        noise_levels: List of noise standard deviations
        n_trials: Number of trials per noise level

    Returns:
        Dictionary with robustness results
    """
    results = {
        'noise_levels': noise_levels,
        'results': [],
        'stable': True
    }

    baseline = func(input_data)

    for noise_level in noise_levels:
        level_results = []
        for _ in range(n_trials):
            noisy_input = input_data + np.random.normal(0, noise_level, input_data.shape)
            try:
                output = func(noisy_input)
                relative_error = np.abs(output - baseline) / (np.abs(baseline) + 1e-10)
                level_results.append(relative_error)
            except Exception as e:
                results['stable'] = False
                level_results.append(float('inf'))

        results['results'].append({
            'noise_level': noise_level,
            'mean_error': np.mean(level_results),
            'max_error': np.max(level_results),
            'failures': sum(np.isinf(level_results))
        })

    return results


def test_edge_cases(
    func: Callable,
    edge_cases: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Test function with edge case inputs.

    Args:
        func: Function to test
        edge_cases: Dictionary of edge case names to inputs

    Returns:
        Dictionary with edge case results
    """
    results = {}

    for case_name, input_value in edge_cases.items():
        try:
            output = func(input_value)
            results[case_name] = {
                'passed': True,
                'output': output,
                'error': None
            }
        except Exception as e:
            results[case_name] = {
                'passed': False,
                'output': None,
                'error': str(e)
            }

    return results


def test_boundary_conditions(
    func: Callable,
    param_ranges: Dict[str, tuple],
    n_samples: int = 10
) -> Dict[str, Any]:
    """
    Test function at parameter boundaries.

    Args:
        func: Function to test
        param_ranges: Dictionary of parameter names to (min, max) ranges
        n_samples: Number of samples at each boundary

    Returns:
        Dictionary with boundary test results
    """
    results = {
        'passed': True,
        'boundary_tests': []
    }

    for param_name, (min_val, max_val) in param_ranges.items():
        # Test at minimum
        try:
            output_min = func(min_val)
            min_test = {'value': min_val, 'passed': True, 'output': output_min}
        except Exception as e:
            min_test = {'value': min_val, 'passed': False, 'error': str(e)}
            results['passed'] = False

        # Test at maximum
        try:
            output_max = func(max_val)
            max_test = {'value': max_val, 'passed': True, 'output': output_max}
        except Exception as e:
            max_test = {'value': max_val, 'passed': False, 'error': str(e)}
            results['passed'] = False

        results['boundary_tests'].append({
            'parameter': param_name,
            'min_test': min_test,
            'max_test': max_test
        })

    return results


def test_symmetries(
    func: Callable,
    input_data: np.ndarray,
    symmetry_transforms: Dict[str, Callable]
) -> Dict[str, Any]:
    """
    Test if function respects expected symmetries.

    Args:
        func: Function to test
        input_data: Input data
        symmetry_transforms: Dictionary of symmetry names to transform functions

    Returns:
        Dictionary with symmetry test results
    """
    baseline = func(input_data)
    results = {}

    for sym_name, transform in symmetry_transforms.items():
        transformed_input = transform(input_data)
        transformed_output = func(transformed_input)

        # Check if output is invariant
        deviation = np.max(np.abs(transformed_output - baseline))
        passed = deviation < 1e-6

        results[sym_name] = {
            'deviation': deviation,
            'passed': passed
        }

    return results


def stress_test_convergence(
    optimization_func: Callable,
    max_iter_values: List[int] = [10, 100, 1000, 10000],
    target_tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Stress test optimization convergence.

    Args:
        optimization_func: Optimization function returning (final_value, converged)
        max_iter_values: List of max iteration values to test
        target_tolerance: Target tolerance

    Returns:
        Dictionary with convergence results
    """
    results = []

    for max_iter in max_iter_values:
        final_value, converged, actual_iters = optimization_func(
            max_iter=max_iter,
            tolerance=target_tolerance
        )

        results.append({
            'max_iter': max_iter,
            'converged': converged,
            'actual_iters': actual_iters,
            'final_value': final_value
        })

    return {
        'convergence_tests': results,
        'all_converged': all(r['converged'] for r in results)
    }


def fuzz_testing(
    func: Callable,
    input_shape: tuple,
    n_tests: int = 100,
    value_range: tuple = (-10, 10)
) -> Dict[str, Any]:
    """
    Fuzz testing with random inputs.

    Args:
        func: Function to test
        input_shape: Shape of input array
        n_tests: Number of random tests
        value_range: Range of random values

    Returns:
        Dictionary with fuzz test results
    """
    failures = []
    successes = 0

    for i in range(n_tests):
        random_input = np.random.uniform(
            value_range[0],
            value_range[1],
            input_shape
        )

        try:
            output = func(random_input)

            # Check output validity
            if np.any(np.isnan(output)) or np.any(np.isinf(output)):
                failures.append({
                    'test': i,
                    'input': random_input,
                    'error': 'NaN or Inf in output'
                })
            else:
                successes += 1

        except Exception as e:
            failures.append({
                'test': i,
                'input': random_input,
                'error': str(e)
            })

    return {
        'n_tests': n_tests,
        'successes': successes,
        'failures': len(failures),
        'success_rate': successes / n_tests,
        'failure_details': failures[:10]  # Only first 10
    }
