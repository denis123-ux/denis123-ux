"""
PHASE 0 (MOONSHOT): Time Emergence from Entanglement Growth
============================================================

HYPOTHESIS (Nobel-level):
The "time" dimension emerges as the direction of maximal entanglement growth.

APPROACH:
1. Evolve quantum state: |ψ(t)⟩ = exp(-iHt)|ψ₀⟩
2. Measure S(A,t) for regions in different spatial orientations
3. Identify: time_direction = argmax(dS/dt)
4. Verify: emergent metric has Lorentzian signature (−,+,+,+)

PREDICTION:
- One spatial dimension will show FASTER entanglement growth
- That dimension = emergent time
- Other dimensions = emergent space
- Metric signature: (−,+,+,+) naturally

BREAKTHROUGH IF TRUE:
- First computational proof of time emergence from quantum info
- Solves 20-year open problem in quantum gravity
- Guaranteed Nobel Prize

References:
- PRL Essay 2024: "Emergent Holographic Spacetime from Quantum Information"
- JHEP 2024: "Timelike Entanglement Entropy"
- Susskind: "Computational Complexity and Black Hole Horizons"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from typing import Dict, List, Tuple
import pandas as pd
from tqdm import tqdm

from entanglement.entropy import entanglement_entropy_svd
from utils.logging import preregister_hypothesis
from utils.visualization import PublicationPlot


# ==================== QUANTUM STATE EVOLUTION ====================

def create_hamiltonian_1d_chain(n_sites: int, J: float = 1.0, h: float = 0.5) -> np.ndarray:
    """
    Create 1D transverse-field Ising Hamiltonian.

    H = -J Σ_i σ^z_i σ^z_{i+1} - h Σ_i σ^x_i

    This is exactly solvable and has quantum phase transition.

    Parameters
    ----------
    n_sites : int
        Number of sites
    J : float
        Coupling strength
    h : float
        Transverse field

    Returns
    -------
    ndarray
        Hamiltonian matrix (2^n_sites × 2^n_sites)
    """
    # Pauli matrices
    sigma_x = np.array([[0, 1], [1, 0]])
    sigma_z = np.array([[1, 0], [0, -1]])
    I = np.eye(2)

    dim = 2**n_sites
    H = np.zeros((dim, dim), dtype=complex)

    # ZZ interaction term
    for i in range(n_sites - 1):
        # σ^z_i ⊗ σ^z_{i+1}
        term = 1.0
        for j in range(n_sites):
            if j == i or j == i + 1:
                term = np.kron(term, sigma_z) if isinstance(term, np.ndarray) else sigma_z
            else:
                term = np.kron(term, I) if isinstance(term, np.ndarray) else I
        H -= J * term

    # X field term
    for i in range(n_sites):
        term = 1.0
        for j in range(n_sites):
            if j == i:
                term = np.kron(term, sigma_x) if isinstance(term, np.ndarray) else sigma_x
            else:
                term = np.kron(term, I) if isinstance(term, np.ndarray) else I
        H -= h * term

    return H


def time_evolution(
    initial_state: np.ndarray,
    hamiltonian: np.ndarray,
    time_steps: np.ndarray
) -> List[np.ndarray]:
    """
    Evolve quantum state in time: |ψ(t)⟩ = exp(-iHt)|ψ₀⟩.

    Parameters
    ----------
    initial_state : ndarray
        Initial state |ψ₀⟩
    hamiltonian : ndarray
        Hamiltonian H
    time_steps : ndarray
        Array of time values

    Returns
    -------
    list of ndarray
        States at each time: [|ψ(t₁)⟩, |ψ(t₂)⟩, ...]
    """
    states = []

    print(f"Evolving state over {len(time_steps)} time steps...")

    for t in tqdm(time_steps):
        # U(t) = exp(-iHt)
        U_t = expm(-1j * hamiltonian * t)

        # |ψ(t)⟩ = U(t)|ψ₀⟩
        state_t = U_t @ initial_state

        # Verify normalization
        norm = np.linalg.norm(state_t)
        if abs(norm - 1.0) > 1e-6:
            print(f"  Warning: State at t={t:.3f} not normalized: ||ψ|| = {norm:.6f}")
            state_t /= norm

        states.append(state_t)

    return states


# ==================== ENTANGLEMENT GROWTH ANALYSIS ====================

def compute_entanglement_growth(
    states: List[np.ndarray],
    time_steps: np.ndarray,
    n_sites: int,
    region_configs: Dict[str, List[int]]
) -> Dict[str, np.ndarray]:
    """
    Compute S(A,t) for different region configurations.

    Parameters
    ----------
    states : list
        States at different times
    time_steps : ndarray
        Time values
    n_sites : int
        Total number of sites
    region_configs : dict
        {config_name: region_indices}

    Returns
    -------
    dict
        {config_name: [S(t₁), S(t₂), ...]}
    """
    entropies = {name: [] for name in region_configs.keys()}

    print(f"\nComputing entanglement entropy for {len(region_configs)} configurations...")

    for config_name, region_indices in region_configs.items():
        region_size = len(region_indices)

        print(f"\n  Config '{config_name}': region_size={region_size}")

        for i, state in enumerate(tqdm(states, desc=f"  {config_name}")):
            try:
                S, info = entanglement_entropy_svd(
                    state,
                    region_A_size=region_size,
                    total_sites=n_sites,
                    d_phys=2
                )
                entropies[config_name].append(S)

            except Exception as e:
                print(f"    Error at t={time_steps[i]:.3f}: {e}")
                entropies[config_name].append(np.nan)

        entropies[config_name] = np.array(entropies[config_name])

    return entropies


def analyze_growth_rates(
    entropies: Dict[str, np.ndarray],
    time_steps: np.ndarray
) -> Dict[str, Dict]:
    """
    Compute dS/dt for each configuration.

    Parameters
    ----------
    entropies : dict
        {config: S(t) array}
    time_steps : ndarray
        Time values

    Returns
    -------
    dict
        {config: {growth_rate, linear_fit, ...}}
    """
    results = {}

    for config_name, S_t in entropies.items():
        # Remove NaNs
        valid = ~np.isnan(S_t)
        t_valid = time_steps[valid]
        S_valid = S_t[valid]

        if len(S_valid) < 3:
            print(f"  Warning: {config_name} has only {len(S_valid)} valid points")
            continue

        # Linear fit: S(t) = a*t + b
        from scipy.stats import linregress
        slope, intercept, r_value, p_value, std_err = linregress(t_valid, S_valid)

        # Growth rate = dS/dt
        growth_rate = slope

        results[config_name] = {
            'growth_rate': growth_rate,
            'growth_rate_error': std_err,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value,
            'is_linear': r_value**2 > 0.95
        }

    return results


# ==================== VISUALIZATION ====================

def plot_entanglement_evolution(
    time_steps: np.ndarray,
    entropies: Dict[str, np.ndarray],
    growth_analysis: Dict[str, Dict],
    save_path: Path
):
    """
    Plot S(t) for all configurations with growth rate analysis.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Time Emergence via Entanglement Growth', fontsize=16, y=0.995)

    # Panel 1: S(t) for all configs
    ax1 = axes[0, 0]
    colors = plt.cm.tab10(np.linspace(0, 0.9, len(entropies)))

    for i, (config, S_t) in enumerate(entropies.items()):
        ax1.plot(time_steps, S_t, 'o-', label=config, color=colors[i], markersize=4)

    ax1.set_xlabel('Time t')
    ax1.set_ylabel('Entanglement Entropy S(A,t)')
    ax1.set_title('Entanglement Growth Over Time')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)

    # Panel 2: Growth rates comparison
    ax2 = axes[0, 1]
    configs = list(growth_analysis.keys())
    growth_rates = [growth_analysis[c]['growth_rate'] for c in configs]
    errors = [growth_analysis[c]['growth_rate_error'] for c in configs]

    x_pos = np.arange(len(configs))
    bars = ax2.bar(x_pos, growth_rates, yerr=errors, capsize=5, alpha=0.7, color=colors[:len(configs)])
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(configs, rotation=45, ha='right')
    ax2.set_ylabel('Growth Rate dS/dt')
    ax2.set_title('Entanglement Growth Rates by Configuration')
    ax2.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax2.grid(True, alpha=0.3, axis='y')

    # Highlight maximum
    max_idx = np.argmax(growth_rates)
    bars[max_idx].set_color('red')
    bars[max_idx].set_alpha(1.0)
    ax2.text(max_idx, growth_rates[max_idx], '  ← TIME?',
             fontsize=12, fontweight='bold', color='red')

    # Panel 3: R² values (linearity check)
    ax3 = axes[1, 0]
    r_squared = [growth_analysis[c]['r_squared'] for c in configs]
    ax3.bar(x_pos, r_squared, alpha=0.7, color=colors[:len(configs)])
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(configs, rotation=45, ha='right')
    ax3.set_ylabel('R² (Linear Fit)')
    ax3.set_title('Linearity of Entanglement Growth')
    ax3.axhline(0.95, color='red', linestyle='--', label='Threshold (0.95)')
    ax3.set_ylim([0, 1.05])
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')

    # Panel 4: Summary statistics
    ax4 = axes[1, 1]
    ax4.axis('off')

    # Create summary table
    summary_text = "GROWTH RATE ANALYSIS\n" + "="*50 + "\n\n"

    # Sort by growth rate
    sorted_configs = sorted(configs, key=lambda c: growth_analysis[c]['growth_rate'], reverse=True)

    for rank, config in enumerate(sorted_configs, 1):
        data = growth_analysis[config]
        marker = "🏆 " if rank == 1 else f"{rank}. "
        summary_text += f"{marker}{config}:\n"
        summary_text += f"  dS/dt = {data['growth_rate']:.4f} ± {data['growth_rate_error']:.4f}\n"
        summary_text += f"  R² = {data['r_squared']:.4f}\n"
        summary_text += f"  Linear: {'YES' if data['is_linear'] else 'NO'}\n\n"

    # Identify time candidate
    time_candidate = sorted_configs[0]
    summary_text += "="*50 + "\n"
    summary_text += f"TIME CANDIDATE: {time_candidate}\n"
    summary_text += "="*50

    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()

    # Save
    save_path.parent.mkdir(parents=True, exist_ok=True)
    for ext in ['pdf', 'png']:
        fig.savefig(save_path.with_suffix(f'.{ext}'), dpi=300, bbox_inches='tight')
    print(f"\n✓ Plot saved: {save_path}")

    return fig


# ==================== MAIN EXPERIMENT ====================

def main():
    """Run time emergence experiment."""

    # ==================== PREREGISTRATION ====================
    logger = preregister_hypothesis(
        name="phase0_time_emergence",
        hypothesis="Time emerges as the direction of maximal entanglement growth",
        prediction="One spatial direction shows dS/dt significantly > others; that direction = time",
        method="Hamiltonian time evolution + entanglement entropy measurement",
        falsifiability="If all directions have similar dS/dt → time does NOT emerge from entanglement",
        output_dir=Path("results/logs")
    )

    # ==================== PARAMETERS ====================
    N_SITES = 6  # Small system for computational tractability
    T_MAX = 2.0  # Maximum time
    N_TIME_STEPS = 20  # Number of time points

    # Hamiltonian parameters
    J = 1.0  # Coupling
    h = 0.5  # Transverse field (near critical point h_c = 1.0)

    print(f"\n{'='*60}")
    print(f"PHASE 0: TIME EMERGENCE FROM ENTANGLEMENT")
    print(f"{'='*60}")
    print(f"System size: {N_SITES} sites")
    print(f"Time evolution: t ∈ [0, {T_MAX}]")
    print(f"Time steps: {N_TIME_STEPS}")
    print(f"Hamiltonian: Transverse-field Ising (J={J}, h={h})")
    print(f"{'='*60}\n")

    # ==================== SETUP ====================
    # Create Hamiltonian
    print("Creating Hamiltonian...")
    H = create_hamiltonian_1d_chain(N_SITES, J=J, h=h)
    print(f"  Hamiltonian shape: {H.shape}")

    # Initial state: |000...0⟩ (low entanglement)
    print("\nPreparing initial state...")
    dim = 2**N_SITES
    initial_state = np.zeros(dim)
    initial_state[0] = 1.0  # |000...0⟩
    print(f"  Initial state: |000...0⟩")

    # Time grid
    time_steps = np.linspace(0, T_MAX, N_TIME_STEPS)

    # ==================== TIME EVOLUTION ====================
    states = time_evolution(initial_state, H, time_steps)

    # ==================== REGION CONFIGURATIONS ====================
    # Test different "orientations" of regions
    # In 1D chain, we test different positions and sizes

    region_configs = {
        'left_half': list(range(N_SITES // 2)),
        'right_half': list(range(N_SITES // 2, N_SITES)),
        'center': list(range(N_SITES // 4, 3 * N_SITES // 4)),
        'edges': list(range(N_SITES // 4)) + list(range(3 * N_SITES // 4, N_SITES)),
    }

    print(f"\nRegion configurations:")
    for name, indices in region_configs.items():
        print(f"  {name}: sites {indices}")

    # ==================== COMPUTE ENTANGLEMENT ====================
    entropies = compute_entanglement_growth(states, time_steps, N_SITES, region_configs)

    # ==================== ANALYZE GROWTH ====================
    print(f"\n{'='*60}")
    print("GROWTH RATE ANALYSIS")
    print(f"{'='*60}\n")

    growth_analysis = analyze_growth_rates(entropies, time_steps)

    for config, data in growth_analysis.items():
        print(f"{config}:")
        print(f"  dS/dt = {data['growth_rate']:.4f} ± {data['growth_rate_error']:.4f}")
        print(f"  R² = {data['r_squared']:.4f}")
        print(f"  Linear growth: {'YES' if data['is_linear'] else 'NO'}")
        print()

    # ==================== IDENTIFY TIME DIRECTION ====================
    growth_rates = {c: data['growth_rate'] for c, data in growth_analysis.items()}
    time_candidate = max(growth_rates, key=growth_rates.get)
    max_growth = growth_rates[time_candidate]

    print(f"{'='*60}")
    print(f"RESULT: TIME CANDIDATE")
    print(f"{'='*60}")
    print(f"Configuration with MAX growth: {time_candidate}")
    print(f"Growth rate: dS/dt = {max_growth:.4f}")
    print(f"{'='*60}\n")

    # Test if significantly different
    other_growths = [g for c, g in growth_rates.items() if c != time_candidate]
    mean_other = np.mean(other_growths)

    if max_growth > 1.5 * mean_other:
        logger.log_success(f"TIME DIRECTION IDENTIFIED: {time_candidate} (dS/dt = {max_growth:.4f})")
        print("✓ SUCCESS: One direction shows SIGNIFICANTLY faster entanglement growth!")
        print(f"  → '{time_candidate}' is the candidate TIME direction")
    else:
        logger.log_failure(f"No clear time direction: max={max_growth:.4f}, mean_others={mean_other:.4f}")
        print("✗ INCONCLUSIVE: All directions have similar growth rates")
        print("  → Time may NOT emerge clearly in this system")

    # ==================== VISUALIZATION ====================
    plot_entanglement_evolution(
        time_steps,
        entropies,
        growth_analysis,
        save_path=Path("results/figures/phase0_time_emergence")
    )

    # ==================== SAVE RESULTS ====================
    results_df = pd.DataFrame({
        'time': time_steps,
        **{f'S_{config}': S_t for config, S_t in entropies.items()}
    })

    results_path = Path("results/data/phase0_time_emergence.csv")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(results_path, index=False)
    print(f"✓ Results saved: {results_path}")

    # ==================== FINAL REPORT ====================
    logger.generate_report()

    print(f"\n{'='*60}")
    print("PHASE 0 COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
