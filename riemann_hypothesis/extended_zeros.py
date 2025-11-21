#!/usr/bin/env python3
"""
================================================================================
    EXTENDED RIEMANN ZEROS - Computing and Downloading More Data
================================================================================

This module:
1. Computes Riemann zeros using mpmath (high precision)
2. Provides utilities for working with large zero datasets
3. Validates zeros against known values

================================================================================
"""

import numpy as np
from typing import List, Optional
import time

# =============================================================================
# COMPUTE ZEROS WITH MPMATH
# =============================================================================

def compute_zeros_mpmath(n: int, verbose: bool = True) -> np.ndarray:
    """
    Compute first n Riemann zeros using mpmath.

    mpmath.zetazero(k) returns the k-th zero on the critical line.
    """
    try:
        from mpmath import zetazero, mp

        # Set precision
        mp.dps = 30  # 30 decimal places

        zeros = []
        start_time = time.time()

        for k in range(1, n + 1):
            zero = zetazero(k)
            zeros.append(float(zero.imag))

            if verbose and k % 100 == 0:
                elapsed = time.time() - start_time
                rate = k / elapsed
                eta = (n - k) / rate
                print(f"  Computed {k}/{n} zeros ({rate:.1f}/s, ETA: {eta:.0f}s)")

        if verbose:
            print(f"  Total time: {time.time() - start_time:.1f}s")

        return np.array(zeros)

    except ImportError:
        print("mpmath not available. Using pre-computed zeros.")
        from riemann_zeros import RIEMANN_ZEROS_100
        return RIEMANN_ZEROS_100[:min(n, 100)]

# =============================================================================
# EXTENDED ZEROS (Pre-computed for speed)
# =============================================================================

# First 500 zeros (imaginary parts) - computed with high precision
RIEMANN_ZEROS_500 = None  # Will be populated

def get_extended_zeros(n: int = 500, force_compute: bool = False) -> np.ndarray:
    """
    Get extended Riemann zeros, computing if necessary.
    """
    global RIEMANN_ZEROS_500

    if RIEMANN_ZEROS_500 is None or len(RIEMANN_ZEROS_500) < n or force_compute:
        print(f"Computing {n} Riemann zeros...")
        RIEMANN_ZEROS_500 = compute_zeros_mpmath(n)

    return RIEMANN_ZEROS_500[:n]

# =============================================================================
# VALIDATION
# =============================================================================

def validate_zeros(computed: np.ndarray, reference: np.ndarray,
                   tolerance: float = 1e-6) -> dict:
    """
    Validate computed zeros against reference values.
    """
    n = min(len(computed), len(reference))

    errors = np.abs(computed[:n] - reference[:n])

    return {
        'n_compared': n,
        'max_error': np.max(errors),
        'mean_error': np.mean(errors),
        'all_within_tolerance': np.all(errors < tolerance),
        'n_errors': np.sum(errors >= tolerance),
    }

# =============================================================================
# ZERO STATISTICS
# =============================================================================

def zero_statistics(zeros: np.ndarray) -> dict:
    """
    Compute comprehensive statistics of Riemann zeros.
    """
    n = len(zeros)
    spacings = np.diff(zeros)

    # Normalize spacings
    # According to theory, mean spacing ~ 2π/log(t/2π)
    # For simplicity, just divide by mean
    norm_spacings = spacings / np.mean(spacings)

    stats = {
        'n_zeros': n,
        'first_zero': zeros[0],
        'last_zero': zeros[-1],
        'range': zeros[-1] - zeros[0],

        'mean_spacing': np.mean(spacings),
        'std_spacing': np.std(spacings),
        'min_spacing': np.min(spacings),
        'max_spacing': np.max(spacings),

        'norm_mean': np.mean(norm_spacings),
        'norm_std': np.std(norm_spacings),

        # GUE-like statistics
        'spacing_ratio': np.std(spacings) / np.mean(spacings),  # Should be ~0.52 for GUE
    }

    return stats

# =============================================================================
# DENSITY OF ZEROS
# =============================================================================

def zero_counting_function(t: float, zeros: np.ndarray = None) -> int:
    """
    N(t) = number of zeros with 0 < γ ≤ t
    """
    if zeros is None:
        zeros = get_extended_zeros(500)
    return np.sum(zeros <= t)

def theoretical_zero_density(t: float) -> float:
    """
    Theoretical density: N(t) ≈ (t/2π) log(t/2π) - t/2π + O(log t)

    This is the Riemann-von Mangoldt formula.
    """
    if t <= 0:
        return 0
    return (t / (2 * np.pi)) * np.log(t / (2 * np.pi)) - t / (2 * np.pi) + 7/8

def verify_zero_density(zeros: np.ndarray) -> dict:
    """
    Verify that computed zeros follow the theoretical density.
    """
    results = []

    for i, t in enumerate(zeros):
        actual_count = i + 1  # Number of zeros up to and including this one
        theoretical_count = theoretical_zero_density(t)
        error = abs(actual_count - theoretical_count)
        results.append({
            't': t,
            'actual': actual_count,
            'theoretical': theoretical_count,
            'error': error,
        })

    errors = [r['error'] for r in results]

    return {
        'max_error': max(errors),
        'mean_error': np.mean(errors),
        'results': results,
    }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║   EXTENDED RIEMANN ZEROS - Computing More Data                    ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Compute 500 zeros
    print("Computing 500 Riemann zeros with mpmath...")
    zeros = compute_zeros_mpmath(500, verbose=True)

    # Statistics
    print("\n" + "=" * 60)
    print("ZERO STATISTICS")
    print("=" * 60)
    stats = zero_statistics(zeros)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.6f}")
        else:
            print(f"  {key}: {value}")

    # Verify density
    print("\n" + "=" * 60)
    print("DENSITY VERIFICATION (Riemann-von Mangoldt)")
    print("=" * 60)
    density = verify_zero_density(zeros)
    print(f"  Max error from theoretical: {density['max_error']:.4f}")
    print(f"  Mean error: {density['mean_error']:.4f}")

    # Save zeros
    np.save('/home/user/denis123-ux/riemann_hypothesis/zeros_500.npy', zeros)
    print(f"\n  Saved {len(zeros)} zeros to zeros_500.npy")
