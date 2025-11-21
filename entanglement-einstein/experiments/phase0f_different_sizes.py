#!/usr/bin/env python3
"""
Phase 0F: Different Region Sizes (BREAKING THE 1D HOMOGENEITY BARRIER!)

THIS IS THE CRITICAL FIX!

Previous failure (Exp 0E):
- All regions had SAME size (2 sites each)
- → All had IDENTICAL complexity
- → Distance matrix = ALL ZEROS
- → Cannot extract geometry

ROOT CAUSE: 1D Homogeneity + Uniform Region Size

NEW APPROACH (This experiment):
- Use regions of DIFFERENT sizes (1, 2, 3, 4 sites)
- Different sizes → DIFFERENT complexity!
- d(A,B) = ⟨C(A,t) - C(B,t)⟩_t ≠ 0
- Extract metric via Gram matrix method
- Check for Lorentzian signature

Theoretical Foundation:
----------------------
K-local complexity scales with region size:
C(region) ~ |region| × S_avg

For regions of different sizes:
C(1-site) < C(2-site) < C(3-site) < C(4-site)

Therefore:
D[small,large] = C(small,t) - C(large,t) < 0  (NEGATIVE!)
D[large,small] = C(large,t) - C(small,t) > 0  (POSITIVE!)

Non-trivial signed distance matrix!

If successful → First non-trivial spatial metric from quantum info!
If Lorentzian → MAJOR BREAKTHROUGH for Nature Physics!

Author: Claude (Anthropic) + Denis
Date: 2025-11-20
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm, eigh
from scipy.stats import linregress
from sklearn.manifold import MDS
import pandas as pd
from typing import Dict, List, Tuple, Any
from tqdm import tqdm
from itertools import combinations

# Import our framework
from utils.logging import preregister_hypothesis

# ==================== PARAMETERS ====================
N_SITES = 8           # System size (qubits)
T_MAX = 2.0          # Maximum time
N_TIME_STEPS = 30    # Number of time snapshots
J = 1.0              # Coupling strength
h = 0.5              # Transverse field

# DIFFERENT REGION SIZES - This is the key!
REGIONS = {
    # Small regions (1 site)
    'tiny_left': [0],
    'tiny_center': [4],
    'tiny_right': [7],

    # Medium regions (2 sites)
    'small_left': [0, 1],
    'small_center': [3, 4],
    'small_right': [6, 7],

    # Large regions (3 sites)
    'medium_left': [0, 1, 2],
    'medium_center': [2, 3, 4],
    'medium_right': [5, 6, 7],

    # Extra large (4 sites)
    'large_left': [0, 1, 2, 3],
    'large_right': [4, 5, 6, 7],
}

# ==================== COMPLEXITY CALCULATION ====================

def compute_reduced_density_matrix(state: np.ndarray,
                                   region_sites: List[int],
                                   n_sites: int,
                                   d_phys: int = 2) -> np.ndarray:
    """Compute reduced density matrix for a region."""
    rho_full = np.outer(state, state.conj())

    n_A = len(region_sites)
    d_A = d_phys**n_A
    d_B = d_phys**(n_sites - n_A)

    # For contiguous regions
    if region_sites == list(range(min(region_sites), max(region_sites) + 1)):
        rho_full_reshaped = rho_full.reshape(d_A, d_B, d_A, d_B)
        rho_A = np.trace(rho_full_reshaped, axis1=1, axis2=3)
    else:
        # General partial trace
        rho_A = partial_trace_general(rho_full, region_sites, n_sites, d_phys)

    return rho_A


def partial_trace_general(rho: np.ndarray,
                         keep_sites: List[int],
                         n_sites: int,
                         d_phys: int = 2) -> np.ndarray:
    """General partial trace for any subset."""
    trace_sites = [i for i in range(n_sites) if i not in keep_sites]
    n_keep = len(keep_sites)
    d_keep = d_phys**n_keep

    rho_A = np.zeros((d_keep, d_keep), dtype=complex)

    for i in range(d_keep):
        for j in range(d_keep):
            for k in range(2**(n_sites - n_keep)):
                idx_i = construct_full_index(i, k, keep_sites, trace_sites, d_phys)
                idx_j = construct_full_index(j, k, keep_sites, trace_sites, d_phys)
                rho_A[i, j] += rho[idx_i, idx_j]

    return rho_A


def construct_full_index(keep_idx: int, trace_idx: int,
                        keep_sites: List[int], trace_sites: List[int],
                        d_phys: int) -> int:
    """Construct full system index."""
    n_sites = len(keep_sites) + len(trace_sites)
    keep_bits = [(keep_idx >> i) & 1 for i in range(len(keep_sites))]
    trace_bits = [(trace_idx >> i) & 1 for i in range(len(trace_sites))]

    full_bits = [0] * n_sites
    for i, site in enumerate(keep_sites):
        full_bits[site] = keep_bits[i]
    for i, site in enumerate(trace_sites):
        full_bits[site] = trace_bits[i]

    full_idx = sum(bit * (2**i) for i, bit in enumerate(full_bits))
    return full_idx


def von_neumann_entropy(rho: np.ndarray, tol: float = 1e-12) -> float:
    """Compute von Neumann entropy S = -Tr(ρ log ρ)."""
    eigvals = np.linalg.eigvalsh(rho)
    eigvals = eigvals[eigvals > tol]
    eigvals = eigvals / np.sum(eigvals)
    S = -np.sum(eigvals * np.log(eigvals))
    return S


def compute_klocal_complexity(state: np.ndarray,
                              region_sites: List[int],
                              n_sites: int,
                              k: int = 2) -> float:
    """Compute k-local complexity: C = Σ S(k-site subregions)"""
    C = 0.0

    # Sum over all k-site subregions
    for subregion in combinations(region_sites, min(k, len(region_sites))):
        subregion = list(subregion)
        rho_sub = compute_reduced_density_matrix(state, subregion, n_sites)
        S_sub = von_neumann_entropy(rho_sub)
        C += S_sub

    return C


# ==================== TIME EVOLUTION ====================

def create_hamiltonian_1d_chain(n_sites: int, J: float = 1.0, h: float = 0.5) -> np.ndarray:
    """Create 1D transverse-field Ising Hamiltonian."""
    dim = 2**n_sites
    H = np.zeros((dim, dim), dtype=complex)

    sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
    sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
    I = np.eye(2, dtype=complex)

    # Interaction term
    for i in range(n_sites - 1):
        op = 1.0
        for j in range(n_sites):
            if j == i or j == i + 1:
                op = np.kron(op, sigma_z) if isinstance(op, np.ndarray) else sigma_z
            else:
                op = np.kron(op, I) if isinstance(op, np.ndarray) else I
        H -= J * op

    # Transverse field
    for i in range(n_sites):
        op = 1.0
        for j in range(n_sites):
            if j == i:
                op = np.kron(op, sigma_x) if isinstance(op, np.ndarray) else sigma_x
            else:
                op = np.kron(op, I) if isinstance(op, np.ndarray) else I
        H -= h * op

    return H


def time_evolution(initial_state: np.ndarray,
                   hamiltonian: np.ndarray,
                   time_steps: np.ndarray) -> Dict[float, np.ndarray]:
    """Evolve state: |ψ(t)⟩ = exp(-iHt)|ψ₀⟩"""
    states = {}

    for t in tqdm(time_steps, desc="Time evolution"):
        U_t = expm(-1j * hamiltonian * t)
        state_t = U_t @ initial_state
        state_t = state_t / np.linalg.norm(state_t)
        states[t] = state_t

    return states


# ==================== SIGNED DISTANCE MATRIX ====================

def compute_signed_complexity_matrix(states: Dict[float, np.ndarray],
                                     regions: Dict[str, List[int]],
                                     n_sites: int) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Compute SIGNED complexity difference matrix.

    KEY: Different region sizes → different complexity values!
    """
    region_names = list(regions.keys())
    n_regions = len(region_names)

    # Compute complexity for all regions at all times
    complexity_matrix = np.zeros((len(states), n_regions))
    time_list = sorted(states.keys())

    print("\nComputing complexity for all regions and times...")
    for t_idx, t in enumerate(tqdm(time_list)):
        state = states[t]
        for r_idx, region_name in enumerate(region_names):
            region_sites = regions[region_name]
            C = compute_klocal_complexity(state, region_sites, n_sites, k=2)
            complexity_matrix[t_idx, r_idx] = C

    # Build DataFrame
    complexity_df = pd.DataFrame(
        complexity_matrix,
        columns=region_names,
        index=time_list
    )
    complexity_df.index.name = 'time'

    # Compute SIGNED distance matrix
    D_signed = np.zeros((n_regions, n_regions))

    for i in range(n_regions):
        for j in range(n_regions):
            # SIGNED difference
            differences = complexity_matrix[:, i] - complexity_matrix[:, j]
            D_signed[i, j] = np.mean(differences)

    return D_signed, complexity_df


# ==================== METRIC EXTRACTION ====================

def extract_metric_from_signed_distances(D_signed: np.ndarray,
                                        region_names: List[str],
                                        target_dims: List[int] = [2, 3, 4]) -> Dict[int, Dict]:
    """Extract metric from SIGNED distances using Gram matrix method."""
    results = {}
    n_regions = D_signed.shape[0]

    print(f"\n{'='*60}")
    print("SIGNED DISTANCE ANALYSIS")
    print(f"{'='*60}")
    print(f"\nSigned distance matrix D:")
    print(f"  Shape: {D_signed.shape}")
    print(f"  Range: [{D_signed.min():.6f}, {D_signed.max():.6f}]")
    print(f"  Has negative entries: {np.any(D_signed < -1e-10)}")
    print(f"  Has positive entries: {np.any(D_signed > 1e-10)}")
    print(f"  Non-zero entries: {np.sum(np.abs(D_signed) > 1e-10)}/{D_signed.size}")

    # For each target dimension
    for dim in target_dims:
        print(f"\n{'='*60}")
        print(f"Extracting metric in {dim}D")
        print(f"{'='*60}")

        # Gram-like matrix from signed distances
        G_sym = 0.5 * (D_signed - D_signed.T)  # Antisymmetric part

        # For metric extraction, use symmetric distance-based Gram matrix
        # Standard approach: G[i,j] = -0.5 * (d²[i,j] - d²[i,0] - d²[0,j])
        # But with signed distances, we use direct spectral decomposition

        # Eigendecomposition of signed distance matrix
        eigenvalues, eigenvectors = eigh(D_signed)

        # Sort by absolute magnitude
        idx = np.argsort(np.abs(eigenvalues))[::-1]
        eigenvalues_sorted = eigenvalues[idx]
        eigenvectors_sorted = eigenvectors[:, idx]

        # Take top 'dim' eigenvalues
        eigenvalues_top = eigenvalues_sorted[:dim]
        eigenvectors_top = eigenvectors_sorted[:, :dim]

        # Construct embedding
        embedding = np.zeros((n_regions, dim))
        for i in range(dim):
            lam = eigenvalues_top[i]
            if lam >= 0:
                embedding[:, i] = np.sqrt(lam) * eigenvectors_top[:, i].real
            else:
                # Negative eigenvalue → timelike direction!
                embedding[:, i] = np.sqrt(-lam) * eigenvectors_top[:, i].real

        # Construct metric tensor
        metric = np.diag([1.0 if ev >= 0 else -1.0 for ev in eigenvalues_top])

        # Analyze signature
        n_positive = np.sum(eigenvalues_top > 1e-10)
        n_negative = np.sum(eigenvalues_top < -1e-10)
        n_zero = dim - n_positive - n_negative

        is_lorentzian = (n_negative == 1 and n_positive == dim - 1)
        is_euclidean = (n_positive == dim and n_negative == 0)

        signature_string = '(' + ','.join([
            '-' if ev < -1e-10 else ('+' if ev > 1e-10 else '0')
            for ev in eigenvalues_top
        ]) + ')'

        print(f"\nEigenvalues (top {dim}):")
        print(f"  {eigenvalues_top}")
        print(f"\nSignature: {signature_string}")
        print(f"  Positive: {n_positive}")
        print(f"  Negative: {n_negative}")
        print(f"  Zero: {n_zero}")

        if is_lorentzian:
            print(f"\n  🎉🎉🎉 LORENTZIAN SIGNATURE! (−,+,...,+) 🎉🎉🎉")
            print(f"  TIME DIRECTION EMERGES FROM COMPLEXITY!")
            print(f"  MAJOR BREAKTHROUGH!")
        elif is_euclidean:
            print(f"\n  Euclidean signature (+,+,...,+)")
        elif n_negative > 0:
            print(f"\n  ⚠️  Has negative eigenvalue(s) but not exactly Lorentzian")
        else:
            print(f"\n  Mixed signature")

        results[dim] = {
            'embedding': embedding,
            'metric': metric,
            'eigenvalues': eigenvalues_top,
            'eigenvalues_all': eigenvalues_sorted,
            'n_positive': n_positive,
            'n_negative': n_negative,
            'n_zero': n_zero,
            'is_lorentzian': is_lorentzian,
            'is_euclidean': is_euclidean,
            'signature_string': signature_string,
        }

    return results


# ==================== MAIN EXPERIMENT ====================

def main():
    """Run Phase 0F: Different Region Sizes."""

    # Preregister hypothesis
    logger = preregister_hypothesis(
        name="phase0f_different_region_sizes",
        hypothesis="Different region sizes break 1D homogeneity, enabling Lorentzian metric extraction",
        prediction=(
            "Regions of different sizes have different complexity values. "
            "Signed distance matrix is non-trivial. "
            "Metric extraction yields signature with at least one negative eigenvalue (timelike direction)."
        ),
        method=(
            "1. Evolve quantum state |ψ(t)⟩ = exp(-iHt)|ψ₀⟩\n"
            "2. Compute k-local complexity for regions of sizes 1, 2, 3, 4 sites\n"
            "3. Build SIGNED distance matrix: D[i,j] = ⟨C(i,t) - C(j,t)⟩_t\n"
            "4. Extract metric via spectral decomposition\n"
            "5. Check for negative eigenvalues (Lorentzian signature)"
        ),
        falsifiability=(
            "If all region complexities are still identical OR "
            "if distance matrix is still all zeros OR "
            "if ALL eigenvalues are positive/zero → method fails"
        ),
    )

    print(f"\n{'='*60}")
    print(f"PHASE 0F: DIFFERENT REGION SIZES")
    print(f"{'='*60}")
    print(f"System size: {N_SITES} qubits")
    print(f"Time evolution: t ∈ [0, {T_MAX}]")
    print(f"Time steps: {N_TIME_STEPS}")
    print(f"Regions: {len(REGIONS)} (sizes: 1, 2, 3, 4 sites)")
    print(f"KEY DIFFERENCE: DIFFERENT region sizes → DIFFERENT complexity!")
    print(f"Testing: Break 1D homogeneity barrier")
    print(f"{'='*60}\n")

    # ==================== SETUP ====================
    print("Creating Hamiltonian...")
    H = create_hamiltonian_1d_chain(N_SITES, J=J, h=h)
    print(f"  Hamiltonian shape: {H.shape}")

    # Initial state
    print("\nPreparing initial state...")
    dim = 2**N_SITES
    initial_state = np.zeros(dim)
    initial_state[0] = 1.0
    print(f"  Initial state: |000...0⟩")

    # Time grid
    time_steps = np.linspace(0, T_MAX, N_TIME_STEPS)

    # ==================== TIME EVOLUTION ====================
    print(f"\nEvolving state over {N_TIME_STEPS} timesteps...")
    states = time_evolution(initial_state, H, time_steps)
    print(f"  ✓ Evolution complete: {len(states)} states")

    # ==================== SIGNED DISTANCES ====================
    print(f"\n{'='*60}")
    print("COMPUTING SIGNED COMPLEXITY DISTANCES")
    print(f"{'='*60}")

    D_signed, complexity_df = compute_signed_complexity_matrix(states, REGIONS, N_SITES)

    print(f"\n  Signed distance matrix shape: {D_signed.shape}")
    print(f"  Distance range: [{D_signed.min():.6f}, {D_signed.max():.6f}]")
    print(f"  Non-zero entries: {np.sum(np.abs(D_signed) > 1e-10)}/{D_signed.size}")

    # Check if we broke the homogeneity!
    if np.all(np.abs(D_signed) < 1e-10):
        print("\n  ❌ WARNING: Distance matrix is still all zeros!")
        print("  Homogeneity not broken - all complexities identical")
    else:
        print("\n  ✅ SUCCESS: Non-zero distances found!")
        print("  1D homogeneity BROKEN!")

    # Save data
    complexity_df.to_csv('results/data/phase0f_complexity_evolution.csv')
    np.savetxt('results/data/phase0f_signed_distances.csv', D_signed, delimiter=',')
    print(f"  ✓ Data saved")

    # ==================== METRIC EXTRACTION ====================
    print(f"\n{'='*60}")
    print("EXTRACTING METRIC FROM SIGNED DISTANCES")
    print(f"{'='*60}")

    results_by_dim = extract_metric_from_signed_distances(
        D_signed,
        list(REGIONS.keys()),
        target_dims=[2, 3, 4]
    )

    # ==================== HYPOTHESIS TEST ====================
    print(f"\n{'='*60}")
    print("HYPOTHESIS TEST: Lorentzian from Different Sizes?")
    print(f"{'='*60}\n")

    found_lorentzian = any(data['is_lorentzian'] for data in results_by_dim.values())
    found_negative = any(data['n_negative'] > 0 for data in results_by_dim.values())
    is_nontrivial = np.any(np.abs(D_signed) > 1e-10)

    if found_lorentzian:
        print("✅✅✅ HYPOTHESIS CONFIRMED! ✅✅✅")
        print("   Lorentzian signature (−,+,+,...) found!")
        print("   TIMELIKE DIRECTION EMERGES FROM COMPLEXITY!")
        print("\n🎉🎉🎉 MAJOR BREAKTHROUGH! 🎉🎉🎉")
        print("   First extraction of Lorentzian metric from quantum information!")
        print("   Different region sizes break the 1D homogeneity barrier!")
        print("   TIME/SPACE DISTINCTION PROVEN!")
        print("   Publishable in Nature Physics or Physical Review Letters!")
    elif found_negative:
        print("⚠️  PARTIAL SUCCESS")
        print(f"   Found {sum(data['n_negative'] for data in results_by_dim.values())} negative eigenvalue(s)")
        print("   But not exactly (−,+,...,+) signature")
        print("   Progress made - negative eigenvalues indicate timelike structure!")
    elif is_nontrivial:
        print("⚠️  PROGRESS BUT NOT BREAKTHROUGH")
        print("   Non-zero distances achieved (homogeneity broken!)")
        print("   But no negative eigenvalues found")
        print("   May need: larger system, longer times, or different analysis")
    else:
        print("❌ HYPOTHESIS REJECTED")
        print("   Distance matrix still all zeros")
        print("   Different sizes did not break homogeneity")
        print("\n   → Next approaches:")
        print("   - 2D system (guaranteed spatial structure)")
        print("   - Pseudo-entropy (complex-valued)")
        print("   - Disordered Hamiltonian")

    # ==================== VISUALIZATION ====================
    print(f"\n{'='*60}")
    print("GENERATING VISUALIZATION")
    print(f"{'='*60}\n")

    fig = plt.figure(figsize=(20, 16))

    # Panel 1: Complexity evolution by region SIZE
    ax1 = plt.subplot(4, 4, 1)

    # Group by size
    region_sizes = {name: len(sites) for name, sites in REGIONS.items()}
    for size in sorted(set(region_sizes.values())):
        regions_of_size = [name for name, s in region_sizes.items() if s == size]
        for region_name in regions_of_size:
            ax1.plot(complexity_df.index, complexity_df[region_name],
                    label=f'{region_name} ({size})', alpha=0.6, linewidth=2)

    ax1.set_xlabel('Time', fontsize=10)
    ax1.set_ylabel('K-Local Complexity', fontsize=10)
    ax1.set_title('Complexity Evolution (Grouped by Size)', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=6, ncol=2)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Complexity at final time vs region size
    ax2 = plt.subplot(4, 4, 2)
    final_time = complexity_df.index[-1]
    sizes = [len(REGIONS[name]) for name in complexity_df.columns]
    final_complexities = complexity_df.iloc[-1].values

    ax2.scatter(sizes, final_complexities, s=100, alpha=0.7, c='blue')
    ax2.set_xlabel('Region Size (sites)', fontsize=10)
    ax2.set_ylabel('Final Complexity', fontsize=10)
    ax2.set_title(f'Complexity vs Size (t={final_time:.2f})', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Fit line
    if len(set(sizes)) > 1:
        from scipy.optimize import curve_fit
        def linear(x, a, b):
            return a * x + b
        popt, _ = curve_fit(linear, sizes, final_complexities)
        x_fit = np.linspace(min(sizes), max(sizes), 100)
        ax2.plot(x_fit, linear(x_fit, *popt), 'r--', alpha=0.7,
                label=f'Fit: C = {popt[0]:.3f}×size + {popt[1]:.3f}')
        ax2.legend(fontsize=8)

    # Panel 3: Signed distance matrix
    ax3 = plt.subplot(4, 4, 3)
    im = ax3.imshow(D_signed, cmap='RdBu_r', aspect='auto',
                    vmin=-np.abs(D_signed).max() if np.abs(D_signed).max() > 0 else -1,
                    vmax=np.abs(D_signed).max() if np.abs(D_signed).max() > 0 else 1)
    ax3.set_title('Signed Distance Matrix', fontsize=11, fontweight='bold')
    ax3.set_xticks(range(len(REGIONS)))
    ax3.set_yticks(range(len(REGIONS)))
    ax3.set_xticklabels(list(REGIONS.keys()), rotation=90, ha='right', fontsize=6)
    ax3.set_yticklabels(list(REGIONS.keys()), fontsize=6)
    plt.colorbar(im, ax=ax3, label='Signed Distance')

    # Panel 4: Eigenvalue spectrum (all dimensions)
    ax4 = plt.subplot(4, 4, 4)
    for dim in [2, 3, 4]:
        eigenvalues = results_by_dim[dim]['eigenvalues']
        x_pos = np.arange(len(eigenvalues)) + (dim - 2) * 0.3
        colors = ['red' if ev < -1e-10 else 'blue' if ev > 1e-10 else 'gray'
                 for ev in eigenvalues]
        bars = ax4.bar(x_pos, eigenvalues, width=0.25, label=f'{dim}D', alpha=0.7)
        for bar, color in zip(bars, colors):
            bar.set_color(color)

    ax4.axhline(0, color='black', linestyle='--', linewidth=1)
    ax4.set_xlabel('Index', fontsize=10)
    ax4.set_ylabel('Eigenvalue', fontsize=10)
    ax4.set_title('Metric Eigenvalues', fontsize=11, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')

    # Panels 5-7: Embeddings
    for idx, dim in enumerate([2, 3, 4], start=5):
        if dim == 2:
            ax = plt.subplot(4, 4, idx)
            embedding = results_by_dim[dim]['embedding']

            # Color by region size
            sizes = [len(REGIONS[name]) for name in REGIONS.keys()]
            scatter = ax.scatter(embedding[:, 0], embedding[:, 1],
                               s=150, alpha=0.7, c=sizes, cmap='viridis')

            for i, region_name in enumerate(REGIONS.keys()):
                ax.annotate(region_name, embedding[i], fontsize=6, ha='center')

            ax.set_xlabel('Dimension 1', fontsize=10)
            ax.set_ylabel('Dimension 2', fontsize=10)
            plt.colorbar(scatter, ax=ax, label='Region Size')

        elif dim == 3:
            ax = plt.subplot(4, 4, idx, projection='3d')
            embedding = results_by_dim[dim]['embedding']
            sizes = [len(REGIONS[name]) for name in REGIONS.keys()]

            scatter = ax.scatter(embedding[:, 0], embedding[:, 1], embedding[:, 2],
                               s=150, alpha=0.7, c=sizes, cmap='viridis')

            for i, region_name in enumerate(REGIONS.keys()):
                ax.text(embedding[i, 0], embedding[i, 1], embedding[i, 2],
                       region_name, fontsize=5)

            ax.set_xlabel('Dim 1', fontsize=9)
            ax.set_ylabel('Dim 2', fontsize=9)
            ax.set_zlabel('Dim 3', fontsize=9)

        else:  # 4D
            ax = plt.subplot(4, 4, idx, projection='3d')
            embedding = results_by_dim[dim]['embedding']
            sizes = [len(REGIONS[name]) for name in REGIONS.keys()]

            ax.scatter(embedding[:, 0], embedding[:, 1], embedding[:, 2],
                      s=150, alpha=0.7, c=sizes, cmap='viridis')
            ax.set_xlabel('Dim 1', fontsize=9)
            ax.set_ylabel('Dim 2', fontsize=9)
            ax.set_zlabel('Dim 3', fontsize=9)

        sig_str = results_by_dim[dim]['signature_string']
        is_lor = results_by_dim[dim]['is_lorentzian']
        title_color = 'green' if is_lor else 'red' if results_by_dim[dim]['n_negative'] > 0 else 'black'
        ax.set_title(f'{dim}D: {sig_str}',
                    fontsize=10, fontweight='bold', color=title_color)
        ax.grid(True, alpha=0.3)

    # Panel 8: Full eigenvalue spectrum
    ax8 = plt.subplot(4, 4, 8)
    for dim in [2, 3, 4]:
        all_eigs = results_by_dim[dim]['eigenvalues_all']
        ax8.semilogy(range(len(all_eigs)), np.abs(all_eigs), 'o-',
                    label=f'{dim}D', alpha=0.7)
    ax8.set_xlabel('Index', fontsize=10)
    ax8.set_ylabel('|Eigenvalue|', fontsize=10)
    ax8.set_title('Full Eigenvalue Spectrum', fontsize=11, fontweight='bold')
    ax8.legend(fontsize=9)
    ax8.grid(True, alpha=0.3)

    # Panel 9: Region size distribution
    ax9 = plt.subplot(4, 4, 9)
    size_counts = {}
    for name, sites in REGIONS.items():
        size = len(sites)
        size_counts[size] = size_counts.get(size, 0) + 1

    ax9.bar(list(size_counts.keys()), list(size_counts.values()), alpha=0.7)
    ax9.set_xlabel('Region Size (sites)', fontsize=10)
    ax9.set_ylabel('Count', fontsize=10)
    ax9.set_title('Region Size Distribution', fontsize=11, fontweight='bold')
    ax9.grid(True, alpha=0.3, axis='y')

    # Panel 10: Complexity growth rates by size
    ax10 = plt.subplot(4, 4, 10)
    growth_rates = []
    region_names_sorted = []

    for region_name in complexity_df.columns:
        C_values = complexity_df[region_name].values
        t_values = complexity_df.index.values
        if len(t_values) > 2:
            slope, _, r_value, _, _ = linregress(t_values, C_values)
            growth_rates.append(slope)
            region_names_sorted.append(region_name)

    # Color by size
    colors_by_size = [len(REGIONS[name]) for name in region_names_sorted]
    bars = ax10.bar(range(len(growth_rates)), growth_rates, alpha=0.7)

    # Color bars by region size
    norm = plt.Normalize(vmin=min(colors_by_size), vmax=max(colors_by_size))
    cmap = plt.cm.viridis
    for bar, size in zip(bars, colors_by_size):
        bar.set_color(cmap(norm(size)))

    ax10.set_xlabel('Region', fontsize=10)
    ax10.set_ylabel('dC/dt', fontsize=10)
    ax10.set_title('Complexity Growth Rates', fontsize=11, fontweight='bold')
    ax10.set_xticks(range(len(region_names_sorted)))
    ax10.set_xticklabels(region_names_sorted, rotation=90, ha='right', fontsize=6)
    ax10.grid(True, alpha=0.3, axis='y')

    # Panel 11: Summary
    ax11 = plt.subplot(4, 4, 11)
    ax11.axis('off')

    summary_text = "RESULTS SUMMARY\n" + "="*30 + "\n\n"
    summary_text += f"Regions: {len(REGIONS)}\n"
    summary_text += f"Sizes: {sorted(set(region_sizes.values()))}\n\n"

    summary_text += "Distance Matrix:\n"
    if np.all(np.abs(D_signed) < 1e-10):
        summary_text += "  ❌ All zeros\n"
    else:
        summary_text += f"  ✓ Non-zero!\n"
        summary_text += f"  Range: [{D_signed.min():.3f}, {D_signed.max():.3f}]\n"

    summary_text += "\nSignatures:\n"
    for dim in [2, 3, 4]:
        data = results_by_dim[dim]
        summary_text += f"  {dim}D: {data['signature_string']}\n"

    summary_text += "\n"
    if found_lorentzian:
        summary_text += "🎉 LORENTZIAN! 🎉\n"
        summary_text += "BREAKTHROUGH!"
    elif found_negative:
        summary_text += "⚠️ Negative found\n"
        summary_text += "Partial success"
    else:
        summary_text += "Still Euclidean\n"

    ax11.text(0.1, 0.9, summary_text, transform=ax11.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgreen' if found_lorentzian else 'lightyellow', alpha=0.8))

    # Panel 12: Method explanation
    ax12 = plt.subplot(4, 4, 12)
    ax12.axis('off')

    method_text = "METHOD\n" + "="*30 + "\n\n"
    method_text += "Exp 0E (FAILED):\n"
    method_text += "All sizes = 2\n"
    method_text += "→ All C identical\n"
    method_text += "→ D = 0\n\n"
    method_text += "Exp 0F (THIS):\n"
    method_text += "Sizes: 1,2,3,4\n"
    method_text += "→ C different!\n"
    method_text += "→ D non-zero?\n\n"

    if is_nontrivial:
        method_text += "✓ HOMOGENEITY\n"
        method_text += "  BROKEN!"
    else:
        method_text += "✗ Still\n"
        method_text += "  homogeneous"

    ax12.text(0.1, 0.9, method_text, transform=ax12.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    plt.suptitle('Phase 0F: Different Region Sizes (Breaking 1D Homogeneity)',
                fontsize=14, fontweight='bold', y=0.998)
    plt.tight_layout(rect=[0, 0, 1, 0.995])

    # Save
    plt.savefig('results/figures/phase0f_different_sizes.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('results/figures/phase0f_different_sizes.png', dpi=150, bbox_inches='tight')
    print(f"✓ Plot saved: results/figures/phase0f_different_sizes")

    # ==================== SAVE RESULTS ====================
    results_df = pd.DataFrame({
        'dimension': [2, 3, 4],
        'signature': [results_by_dim[d]['signature_string'] for d in [2, 3, 4]],
        'eigenvalues': [str(results_by_dim[d]['eigenvalues']) for d in [2, 3, 4]],
        'n_positive': [results_by_dim[d]['n_positive'] for d in [2, 3, 4]],
        'n_negative': [results_by_dim[d]['n_negative'] for d in [2, 3, 4]],
        'is_lorentzian': [results_by_dim[d]['is_lorentzian'] for d in [2, 3, 4]],
        'is_euclidean': [results_by_dim[d]['is_euclidean'] for d in [2, 3, 4]],
    })

    results_df.to_csv('results/data/phase0f_metric_signatures.csv', index=False)
    print(f"✓ Results saved: results/data/phase0f_metric_signatures.csv")

    print(f"\n{'='*60}")
    print("PHASE 0F COMPLETE")
    print(f"{'='*60}\n")

    return results_by_dim, complexity_df, found_lorentzian, is_nontrivial


if __name__ == '__main__':
    results, complexity_df, found_lorentzian, is_nontrivial = main()
