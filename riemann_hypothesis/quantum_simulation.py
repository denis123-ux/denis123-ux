#!/usr/bin/env python3
"""
================================================================================
    QUANTUM SIMULATION OF RIEMANN HYPOTHESIS
================================================================================

Based on: "The Riemann Hypothesis Emerges in Dynamical Quantum Phase Transitions"
          arXiv:2511.11199 (November 2025)

KEY INSIGHT: The Riemann Hypothesis can be viewed as the emergence of
Dynamical Quantum Phase Transitions (DQPTs) at a specific temperature β = 1/2.

This module implements:
1. Logarithmic Hamiltonian H₀ = Σ log(n)|n⟩⟨n|
2. Accumulated Phase Factor encoding ζ(s)
3. Loschmidt Amplitude and Hardy Z-function
4. Detection of DQPTs at Riemann zeros

================================================================================
"""

import numpy as np
from scipy import linalg
from scipy.special import gamma as gamma_func
from typing import Tuple, List, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# =============================================================================
# RIEMANN-SIEGEL THETA FUNCTION
# =============================================================================

def riemann_siegel_theta(t: float) -> float:
    """
    Riemann-Siegel theta function:

    θ(t) = arg(Γ(1/4 + it/2)) - (t/2)log(π)

    This is the phase that makes Z(t) real.
    """
    from scipy.special import loggamma

    # θ(t) = Im(log Γ(1/4 + it/2)) - t/2 * log(π)
    s = 0.25 + 0.5j * t
    log_gamma = loggamma(s)
    theta = log_gamma.imag - (t / 2) * np.log(np.pi)

    return theta

def theta_derivative(t: float, dt: float = 1e-6) -> float:
    """
    Numerical derivative of theta function: θ'(t)
    """
    return (riemann_siegel_theta(t + dt) - riemann_siegel_theta(t - dt)) / (2 * dt)

# =============================================================================
# LOGARITHMIC HAMILTONIAN
# =============================================================================

def create_log_hamiltonian(N: int) -> np.ndarray:
    """
    Create the logarithmic Hamiltonian from the 2025 paper:

    H₀ = Σₙ₌₁ᴺ log(n)|n⟩⟨n|

    This has energy levels Eₙ = log(n).
    """
    energies = np.log(np.arange(1, N + 1))
    return np.diag(energies)

def thermal_state(H: np.ndarray, beta: float) -> np.ndarray:
    """
    Create thermal state:

    ρ = e^(-βH) / Z(β)

    where Z(β) = Tr(e^(-βH)) is the partition function.
    """
    eigenvalues = np.diag(H)
    boltzmann = np.exp(-beta * eigenvalues)
    Z = np.sum(boltzmann)
    rho = np.diag(boltzmann / Z)
    return rho

def partition_function(N: int, beta: float) -> float:
    """
    Partition function for logarithmic Hamiltonian:

    Z(β, H₀) = Σₙ₌₁ᴺ n^(-β)

    NOTE: This IS the (truncated) Riemann zeta function ζ(β)!
    """
    return np.sum(np.arange(1, N + 1) ** (-beta))

# =============================================================================
# ACCUMULATED PHASE FACTOR
# =============================================================================

def accumulated_phase_factor(N: int, beta: float, t: float) -> complex:
    """
    Accumulated phase factor from the 2025 paper:

    L(β, t) = -Σₙ₌₁ᴺ (-1)^(n+1) n^(-β-it) / Z(β)

    In the thermodynamic limit:
    Z(β) * L(β, t) → (2^(1-s) - 1) ζ(s)   where s = β + it

    When β = 1/2 (critical line), the zeros of |L| correspond to Riemann zeros!
    """
    Z = partition_function(N, beta)

    L = 0.0
    for n in range(1, N + 1):
        sign = (-1) ** (n + 1)
        L += sign * (n ** (-beta - 1j * t))

    return -L / Z

def find_phase_zeros(N: int, beta: float, t_range: Tuple[float, float],
                     resolution: int = 1000) -> List[float]:
    """
    Find zeros of |L(β, t)| in a given range.

    These should correspond to Riemann zeros when β = 1/2!
    """
    t_values = np.linspace(t_range[0], t_range[1], resolution)

    # Compute |L| at each point
    L_values = np.array([np.abs(accumulated_phase_factor(N, beta, t)) for t in t_values])

    # Find local minima
    zeros = []
    for i in range(1, len(L_values) - 1):
        if L_values[i] < L_values[i-1] and L_values[i] < L_values[i+1]:
            if L_values[i] < 0.1:  # Threshold for "zero"
                zeros.append(t_values[i])

    return zeros

# =============================================================================
# HARDY Z-FUNCTION
# =============================================================================

def hardy_z_function(t: float, N: int = 1000) -> float:
    """
    Hardy Z-function (real-valued on the critical line):

    Z(t) = e^(iθ(t)) ζ(1/2 + it)

    Zeros of Z(t) are the imaginary parts of Riemann zeros!
    """
    theta = riemann_siegel_theta(t)

    # Compute ζ(1/2 + it) using Dirichlet series (truncated)
    s = 0.5 + 1j * t
    zeta_approx = np.sum(np.arange(1, N + 1) ** (-s))

    Z = np.exp(1j * theta) * zeta_approx

    return Z.real

def find_hardy_zeros(t_range: Tuple[float, float], resolution: int = 1000,
                    N: int = 1000) -> List[float]:
    """
    Find zeros of Hardy Z-function (= Riemann zeros).
    """
    t_values = np.linspace(t_range[0], t_range[1], resolution)

    Z_values = np.array([hardy_z_function(t, N) for t in t_values])

    # Find sign changes
    zeros = []
    for i in range(len(Z_values) - 1):
        if Z_values[i] * Z_values[i+1] < 0:
            # Interpolate to find more precise zero
            t_zero = t_values[i] - Z_values[i] * (t_values[i+1] - t_values[i]) / (Z_values[i+1] - Z_values[i])
            zeros.append(t_zero)

    return zeros

# =============================================================================
# LOSCHMIDT AMPLITUDE
# =============================================================================

def loschmidt_amplitude(N: int, t: float) -> complex:
    """
    Generalized Loschmidt amplitude related to Hardy Z-function.

    This connects to:
    G(t) = ⟨ψ₀|e^(-iHt)|ψ₀⟩

    for appropriate initial state.
    """
    # Using the connection from the paper
    theta = riemann_siegel_theta(t)
    s = 0.5 + 1j * t

    # Dirichlet series (truncated)
    zeta_sum = np.sum(np.arange(1, N + 1) ** (-s))

    return np.exp(1j * theta) * zeta_sum

def loschmidt_rate(N: int, t_values: np.ndarray) -> np.ndarray:
    """
    Loschmidt rate function (free energy density):

    λ(t) = -lim(N→∞) (1/log N) ln|G(t)|

    Non-analyticities indicate DQPTs!
    """
    rates = []
    log_N = np.log(N)

    for t in t_values:
        G = loschmidt_amplitude(N, t)
        rate = -np.log(np.abs(G) + 1e-15) / log_N
        rates.append(rate)

    return np.array(rates)

# =============================================================================
# DYNAMICAL QUANTUM PHASE TRANSITIONS
# =============================================================================

def detect_dqpts(N: int, t_range: Tuple[float, float],
                resolution: int = 500) -> dict:
    """
    Detect Dynamical Quantum Phase Transitions.

    DQPTs occur when the Loschmidt amplitude vanishes, which happens
    at the Riemann zeros!
    """
    t_values = np.linspace(t_range[0], t_range[1], resolution)

    # Compute Loschmidt amplitude
    G_values = np.array([loschmidt_amplitude(N, t) for t in t_values])
    G_abs = np.abs(G_values)

    # Compute rate function
    rates = loschmidt_rate(N, t_values)

    # Detect DQPTs (peaks in rate function = zeros of |G|)
    dqpt_times = []
    for i in range(1, len(rates) - 1):
        if rates[i] > rates[i-1] and rates[i] > rates[i+1]:
            if rates[i] > np.mean(rates) + 2 * np.std(rates):
                dqpt_times.append(t_values[i])

    return {
        't_values': t_values,
        'G_abs': G_abs,
        'rates': rates,
        'dqpt_times': dqpt_times,
    }

# =============================================================================
# COMPARISON WITH RIEMANN ZEROS
# =============================================================================

def compare_dqpt_with_zeros(riemann_zeros: np.ndarray, N: int = 500) -> dict:
    """
    Compare DQPT times with actual Riemann zeros.

    This is the KEY TEST of the quantum simulation approach!
    """
    # Get range from zeros
    t_min = riemann_zeros[0] - 2
    t_max = riemann_zeros[-1] + 2

    # Detect DQPTs
    dqpt_result = detect_dqpts(N, (t_min, t_max), resolution=2000)
    dqpt_times = np.array(dqpt_result['dqpt_times'])

    # Compare
    matched_zeros = []
    matched_dqpts = []
    errors = []

    for zero in riemann_zeros:
        if len(dqpt_times) > 0:
            # Find closest DQPT
            idx = np.argmin(np.abs(dqpt_times - zero))
            closest_dqpt = dqpt_times[idx]
            error = abs(closest_dqpt - zero)

            if error < 1.0:  # Tolerance
                matched_zeros.append(zero)
                matched_dqpts.append(closest_dqpt)
                errors.append(error)

    return {
        'riemann_zeros': riemann_zeros,
        'dqpt_times': dqpt_times,
        'matched_zeros': np.array(matched_zeros),
        'matched_dqpts': np.array(matched_dqpts),
        'errors': np.array(errors),
        'match_rate': len(matched_zeros) / len(riemann_zeros) if len(riemann_zeros) > 0 else 0,
        'mean_error': np.mean(errors) if errors else float('inf'),
    }

# =============================================================================
# VISUALIZATION
# =============================================================================

def visualize_quantum_simulation(riemann_zeros: np.ndarray, N: int = 500):
    """
    Create comprehensive visualization of quantum simulation approach.
    """
    t_min = riemann_zeros[0] - 5
    t_max = min(riemann_zeros[-1] + 5, 100)
    t_values = np.linspace(t_min, t_max, 1000)

    fig, axes = plt.subplots(3, 2, figsize=(15, 12))

    # 1. Hardy Z-function
    ax1 = axes[0, 0]
    Z_values = [hardy_z_function(t, N) for t in t_values]
    ax1.plot(t_values, Z_values, 'b-', linewidth=1)
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    for zero in riemann_zeros:
        if t_min < zero < t_max:
            ax1.axvline(zero, color='r', alpha=0.3, linestyle=':')
    ax1.set_xlabel('t')
    ax1.set_ylabel('Z(t)')
    ax1.set_title('Hardy Z-function (zeros = Riemann zeros)')
    ax1.grid(True, alpha=0.3)

    # 2. Accumulated Phase Factor |L(1/2, t)|
    ax2 = axes[0, 1]
    L_values = [np.abs(accumulated_phase_factor(N, 0.5, t)) for t in t_values]
    ax2.plot(t_values, L_values, 'g-', linewidth=1)
    for zero in riemann_zeros:
        if t_min < zero < t_max:
            ax2.axvline(zero, color='r', alpha=0.3, linestyle=':')
    ax2.set_xlabel('t')
    ax2.set_ylabel('|L(1/2, t)|')
    ax2.set_title('Accumulated Phase Factor at β = 1/2 (critical line)')
    ax2.grid(True, alpha=0.3)

    # 3. Loschmidt Amplitude
    ax3 = axes[1, 0]
    G_values = [np.abs(loschmidt_amplitude(N, t)) for t in t_values]
    ax3.semilogy(t_values, G_values, 'purple', linewidth=1)
    for zero in riemann_zeros:
        if t_min < zero < t_max:
            ax3.axvline(zero, color='r', alpha=0.3, linestyle=':')
    ax3.set_xlabel('t')
    ax3.set_ylabel('|G(t)| (log scale)')
    ax3.set_title('Loschmidt Amplitude (minima = DQPTs = zeros)')
    ax3.grid(True, alpha=0.3)

    # 4. Loschmidt Rate (Free Energy)
    ax4 = axes[1, 1]
    rates = loschmidt_rate(N, t_values)
    ax4.plot(t_values, rates, 'orange', linewidth=1)
    for zero in riemann_zeros:
        if t_min < zero < t_max:
            ax4.axvline(zero, color='r', alpha=0.3, linestyle=':')
    ax4.set_xlabel('t')
    ax4.set_ylabel('λ(t)')
    ax4.set_title('Loschmidt Rate Function (peaks = DQPTs)')
    ax4.grid(True, alpha=0.3)

    # 5. Theta function
    ax5 = axes[2, 0]
    theta_values = [riemann_siegel_theta(t) for t in t_values]
    ax5.plot(t_values, theta_values, 'cyan', linewidth=2)
    ax5.set_xlabel('t')
    ax5.set_ylabel('θ(t)')
    ax5.set_title('Riemann-Siegel Theta Function')
    ax5.grid(True, alpha=0.3)

    # 6. Comparison: DQPT times vs Riemann zeros
    ax6 = axes[2, 1]
    comparison = compare_dqpt_with_zeros(riemann_zeros[:20], N)
    if len(comparison['matched_zeros']) > 0:
        ax6.scatter(comparison['matched_zeros'], comparison['matched_dqpts'],
                   c='blue', s=50, alpha=0.7)
        # Perfect line
        max_val = max(comparison['matched_zeros'].max(), comparison['matched_dqpts'].max())
        min_val = min(comparison['matched_zeros'].min(), comparison['matched_dqpts'].min())
        ax6.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect match')
    ax6.set_xlabel('Riemann zeros γₙ')
    ax6.set_ylabel('DQPT times')
    ax6.set_title(f'DQPT vs Zeros (Match rate: {comparison["match_rate"]:.1%})')
    ax6.legend()
    ax6.grid(True, alpha=0.3)

    plt.suptitle('QUANTUM SIMULATION OF RIEMANN HYPOTHESIS (2025 DQPT Approach)',
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/home/user/denis123-ux/riemann_hypothesis/quantum_simulation.png', dpi=150)
    plt.close()

    print("Visualization saved to quantum_simulation.png")

    return comparison

# =============================================================================
# FULL ANALYSIS
# =============================================================================

def full_quantum_analysis(riemann_zeros: np.ndarray, N: int = 500,
                         verbose: bool = True) -> dict:
    """
    Complete quantum simulation analysis.
    """
    if verbose:
        print("=" * 70)
        print("QUANTUM SIMULATION ANALYSIS (2025 DQPT APPROACH)")
        print("=" * 70)

    results = {}

    # 1. Verify zeta connection
    if verbose:
        print("\n1. Verifying Partition Function = ζ(β)...")

    for beta in [2.0, 3.0, 4.0]:
        Z_computed = partition_function(10000, beta)
        from scipy.special import zeta as scipy_zeta
        Z_actual = scipy_zeta(beta)
        error = abs(Z_computed - Z_actual) / Z_actual
        if verbose:
            print(f"   Z({beta}) = {Z_computed:.6f}, ζ({beta}) = {Z_actual:.6f}, error = {error:.2e}")

    # 2. Find zeros via Hardy Z-function
    if verbose:
        print("\n2. Finding zeros via Hardy Z-function...")

    hardy_zeros = find_hardy_zeros((10, 50), resolution=2000, N=N)
    results['hardy_zeros'] = hardy_zeros

    if verbose:
        print(f"   Found {len(hardy_zeros)} zeros in range [10, 50]")
        print(f"   First few: {hardy_zeros[:5]}")

    # 3. Compare with actual Riemann zeros
    if verbose:
        print("\n3. Comparing with actual Riemann zeros...")

    # Filter to same range
    actual_in_range = riemann_zeros[(riemann_zeros >= 10) & (riemann_zeros <= 50)]

    if len(hardy_zeros) > 0 and len(actual_in_range) > 0:
        errors = []
        for actual in actual_in_range:
            idx = np.argmin(np.abs(np.array(hardy_zeros) - actual))
            errors.append(abs(hardy_zeros[idx] - actual))

        results['zero_comparison'] = {
            'actual': actual_in_range,
            'computed': hardy_zeros,
            'mean_error': np.mean(errors),
            'max_error': np.max(errors),
        }

        if verbose:
            print(f"   Mean error: {np.mean(errors):.4f}")
            print(f"   Max error: {np.max(errors):.4f}")

    # 4. DQPT analysis
    if verbose:
        print("\n4. Detecting DQPTs...")

    comparison = compare_dqpt_with_zeros(riemann_zeros[:30], N)
    results['dqpt_comparison'] = comparison

    if verbose:
        print(f"   DQPT match rate: {comparison['match_rate']:.1%}")
        print(f"   Mean DQPT error: {comparison['mean_error']:.4f}")

    # 5. Visualization
    if verbose:
        print("\n5. Generating visualization...")

    visualize_quantum_simulation(riemann_zeros[:30], N)

    # 6. Verdict
    if verbose:
        print("\n" + "=" * 70)
        print("QUANTUM SIMULATION VERDICT")
        print("=" * 70)

        if comparison['match_rate'] > 0.8:
            print("✓ STRONG correspondence between DQPTs and Riemann zeros!")
            print("→ This supports the 2025 paper's claim that RH = emergence of DQPTs")
        elif comparison['match_rate'] > 0.5:
            print("△ MODERATE correspondence - need more precision")
        else:
            print("✗ Weak correspondence - check parameters")

    return results

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║   QUANTUM SIMULATION OF RIEMANN HYPOTHESIS                            ║
    ║   Based on: arXiv:2511.11199 (November 2025)                          ║
    ║                                                                       ║
    ║   "RH = Emergence of Dynamical Quantum Phase Transitions at β=1/2"   ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)

    from riemann_zeros import get_zeros
    zeros = get_zeros(100)

    results = full_quantum_analysis(zeros, N=500, verbose=True)
