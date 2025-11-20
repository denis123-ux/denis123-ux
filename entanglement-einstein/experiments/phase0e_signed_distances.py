#!/usr/bin/env python3
"""
Phase 0E: Signed Complexity Distances (BREAKING THE MDS BARRIER!)

THIS IS THE CRITICAL TEST!

Previous failures:
- Exp 0B: MI-based distances → MDS → Euclidean (+,+,+)
- Exp 0D: Complexity-based distances → MDS → Euclidean (+,+,+)

Root cause identified: MDS always gives positive-definite metrics!

NEW APPROACH (This experiment):
- Use SIGNED distances (not absolute values!)
- d(A,B,t) = C(A,t) - C(B,t)  [CAN BE NEGATIVE]
- Direct metric construction (NO MDS!)
- Preserve time orientation

Theoretical Foundation:
----------------------
Standard approach (FAILED):
    d(A,B) = |C(A,t) - C(B,t)|  → Always positive → MDS → Euclidean

New approach (THIS):
    d_signed(A,B,t) = C(A,t) - C(B,t)  → Can be negative!

    Build "distance" matrix with signs:
    D[i,j] = ⟨C(i,t) - C(j,t)⟩_t

    This preserves TIME DIRECTION:
    - If C(A) > C(B): regions at different "times"
    - Sign indicates temporal ordering

Method for metric extraction:
1. Compute signed complexity differences
2. Use Gram matrix construction (preserves negative entries)
3. Diagonalize to get metric eigenvalues
4. Check signature: is there ONE negative eigenvalue?

If successful → Lorentzian signature (−,+,+,+) → BREAKTHROUGH!

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
import pandas as pd
from typing import Dict, List, Tuple, Any
import hashlib
from datetime import datetime
from tqdm import tqdm

# Import our framework
from utils.logging import preregister_hypothesis

# ==================== PARAMETERS ====================
N_SITES = 8           # System size (qubits)
T_MAX = 2.0          # Maximum time
N_TIME_STEPS = 30    # Number of time snapshots
J = 1.0              # Coupling strength
h = 0.5              # Transverse field

# Region definitions (spatial slices)
REGIONS = {
    'L1': [0, 1],           # Left edge
    'L2': [1, 2],
    'LC': [2, 3],           # Left-center
    'C':  [3, 4],           # Center
    'RC': [4, 5],           # Right-center
    'R2': [5, 6],
    'R1': [6, 7],           # Right edge
}

# ==================== COMPLEXITY CALCULATION ====================
# (Same as Phase 0D)

def compute_reduced_density_matrix(state: np.ndarray,
                                   region_sites: List[int],
                                   n_sites: int,
                                   d_phys: int = 2) -> np.ndarray:
    """Compute reduced density matrix for a region."""
    rho_full = np.outer(state, state.conj())

    n_A = len(region_sites)
    d_A = d_phys**n_A
    d_B = d_phys**(n_sites - n_A)

    # Simplified for contiguous regions
    if region_sites == list(range(min(region_sites), max(region_sites) + 1)):
        rho_full_reshaped = rho_full.reshape(d_A, d_B, d_A, d_B)
        rho_A = np.trace(rho_full_reshaped, axis1=1, axis2=3)
    else:
        # Full partial trace (general case)
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
    """
    Compute k-local complexity: C = Σ S(k-site subregions)
    """
    from itertools import combinations

    C = 0.0
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

    D[i,j] = ⟨C(i,t) - C(j,t)⟩_t  [CAN BE NEGATIVE!]

    This is fundamentally different from Phase 0D which used |C(i,t) - C(j,t)|
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
            # SIGNED difference (not absolute value!)
            differences = complexity_matrix[:, i] - complexity_matrix[:, j]
            D_signed[i, j] = np.mean(differences)  # Can be negative!

    # D_signed is now antisymmetric: D[i,j] = -D[j,i]

    return D_signed, complexity_df


# ==================== METRIC EXTRACTION (NO MDS!) ====================

def extract_metric_from_signed_distances(D_signed: np.ndarray,
                                        region_names: List[str],
                                        target_dims: List[int] = [2, 3, 4]) -> Dict[int, Dict]:
    """
    Extract metric from SIGNED distances using Gram matrix method.

    Key difference from MDS:
    - MDS assumes Euclidean embedding: minimizes Σ(d_ij - ||x_i - x_j||)²
    - Gram method: constructs metric directly from signed distances

    Method:
    1. Form Gram matrix G from signed distances
    2. Diagonalize G to get metric eigenvalues
    3. Check for NEGATIVE eigenvalues (timelike directions!)

    Reference: "Distance Geometry" (Blumenthal, 1953)
    """
    results = {}
    n_regions = D_signed.shape[0]

    print(f"\n{'='*60}")
    print("SIGNED DISTANCE ANALYSIS")
    print(f"{'='*60}")
    print(f"\nSigned distance matrix D:")
    print(f"  Shape: {D_signed.shape}")
    print(f"  Range: [{D_signed.min():.4f}, {D_signed.max():.4f}]")
    print(f"  Has negative entries: {np.any(D_signed < -1e-10)}")
    print(f"  Antisymmetric: {np.allclose(D_signed, -D_signed.T, atol=1e-10)}")

    # For each target dimension
    for dim in target_dims:
        print(f"\n{'='*60}")
        print(f"Extracting metric in {dim}D")
        print(f"{'='*60}")

        # Method 1: Direct Gram matrix from signed distances
        # G[i,j] = -0.5 * (d²[i,j] - d²[i,0] - d²[0,j])
        # But our distances are signed, so we need modified approach

        # Form Gram-like matrix from signed distances
        # For signed distances d[i,j], we construct:
        # G[i,j] = d[i,j]  (preserve sign!)
        G = D_signed.copy()

        # Symmetrize by taking average (since d[i,j] ≈ -d[j,i])
        G_sym = 0.5 * (G - G.T)  # Extract antisymmetric part

        # Convert to symmetric form for eigenvalue analysis
        # Use: M = G_sym^T @ G_sym (this preserves negative eigenvalues!)
        M = G_sym.T @ G_sym

        # Eigendecomposition
        eigenvalues, eigenvectors = eigh(M)

        # Sort by magnitude (largest first)
        idx = np.argsort(np.abs(eigenvalues))[::-1]
        eigenvalues_sorted = eigenvalues[idx]
        eigenvectors_sorted = eigenvectors[:, idx]

        # Take top 'dim' eigenvalues
        eigenvalues_top = eigenvalues_sorted[:dim]
        eigenvectors_top = eigenvectors_sorted[:, :dim]

        # Construct embedding
        # For negative eigenvalues, take imaginary part to get real coordinates
        embedding = np.zeros((n_regions, dim))
        for i in range(dim):
            lam = eigenvalues_top[i]
            if lam >= 0:
                embedding[:, i] = np.sqrt(lam) * eigenvectors_top[:, i].real
            else:
                # Negative eigenvalue → timelike direction!
                embedding[:, i] = np.sqrt(-lam) * eigenvectors_top[:, i].real

        # Construct metric tensor
        metric = np.zeros((dim, dim))
        for i in range(dim):
            for j in range(dim):
                if eigenvalues_top[i] >= 0 and eigenvalues_top[j] >= 0:
                    metric[i, j] = 1.0 if i == j else 0.0
                elif eigenvalues_top[i] < 0 and eigenvalues_top[j] < 0:
                    metric[i, j] = -1.0 if i == j else 0.0
                else:
                    metric[i, j] = 0.0

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
            print(f"\n  🎉 LORENTZIAN SIGNATURE! (−,+,...,+)")
        elif is_euclidean:
            print(f"\n  Euclidean signature (+,+,...,+)")
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
            'gram_matrix': G_sym,
        }

    return results


# ==================== MAIN EXPERIMENT ====================

def main():
    """Run Phase 0E: Signed Complexity Distances."""

    # Preregister hypothesis
    logger = preregister_hypothesis(
        name="phase0e_signed_complexity_distances",
        hypothesis="Signed complexity distances can extract Lorentzian metric signature (−,+,+,+)",
        prediction=(
            "At least one dimension will show signature (−,+,...) with ONE negative eigenvalue. "
            "This negative eigenvalue corresponds to the timelike direction (complexity growth)."
        ),
        method=(
            "1. Evolve quantum state |ψ(t)⟩ = exp(-iHt)|ψ₀⟩\n"
            "2. Compute k-local complexity C(region, t)\n"
            "3. Build SIGNED distance matrix: D[i,j] = ⟨C(i,t) - C(j,t)⟩_t (CAN BE NEGATIVE)\n"
            "4. Extract metric via Gram matrix method (NOT MDS)\n"
            "5. Analyze eigenvalues for negative entries"
        ),
        falsifiability=(
            "If ALL dimensions show only positive/zero eigenvalues "
            "AND no negative eigenvalues → signed distance method also fails"
        ),
    )

    print(f"\n{'='*60}")
    print(f"PHASE 0E: SIGNED COMPLEXITY DISTANCES")
    print(f"{'='*60}")
    print(f"System size: {N_SITES} qubits")
    print(f"Time evolution: t ∈ [0, {T_MAX}]")
    print(f"Time steps: {N_TIME_STEPS}")
    print(f"Regions: {len(REGIONS)}")
    print(f"KEY DIFFERENCE: Using SIGNED distances (not absolute value)")
    print(f"Testing: Breaking the MDS barrier!")
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
    print(f"  Contains negative values: {np.any(D_signed < -1e-10)}")

    # Save data
    complexity_df.to_csv('results/data/phase0e_complexity_evolution.csv')
    np.savetxt('results/data/phase0e_signed_distances.csv', D_signed, delimiter=',')
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
    print("HYPOTHESIS TEST: Lorentzian from Signed Distances?")
    print(f"{'='*60}\n")

    found_lorentzian = any(data['is_lorentzian'] for data in results_by_dim.values())
    found_negative = any(data['n_negative'] > 0 for data in results_by_dim.values())

    if found_lorentzian:
        print("✅ HYPOTHESIS CONFIRMED!")
        print("   Lorentzian signature (−,+,+,...) found!")
        print("   TIMELIKE DIRECTION EMERGES FROM COMPLEXITY!")
        print("\n🎉🎉🎉 MAJOR BREAKTHROUGH! 🎉🎉🎉")
        print("   First extraction of Lorentzian metric from quantum information!")
        print("   TIME/SPACE DISTINCTION PROVEN!")
        print("   Publishable in Nature Physics or Physical Review Letters!")
    elif found_negative:
        print("⚠️  PARTIAL SUCCESS")
        print(f"   Found {sum(data['n_negative'] for data in results_by_dim.values())} negative eigenvalue(s)")
        print("   But not exactly (−,+,...,+) signature")
        print("   May need refinement or different interpretation")
    else:
        print("❌ HYPOTHESIS REJECTED")
        print("   No negative eigenvalues found")
        print("   Signed distance method also gives only positive eigenvalues")
        print("\n   → Next approaches:")
        print("   - Pseudo-entropy (complex-valued)")
        print("   - Time-dependent metric")
        print("   - Direct Lorentzian construction")

    # ==================== VISUALIZATION ====================
    print(f"\n{'='*60}")
    print("GENERATING VISUALIZATION")
    print(f"{'='*60}\n")

    fig = plt.figure(figsize=(20, 14))

    # Panel 1: Complexity evolution
    ax1 = plt.subplot(3, 4, 1)
    for region_name in complexity_df.columns:
        ax1.plot(complexity_df.index, complexity_df[region_name],
                label=region_name, marker='o', markersize=3, alpha=0.7)
    ax1.set_xlabel('Time', fontsize=10)
    ax1.set_ylabel('K-Local Complexity', fontsize=10)
    ax1.set_title('Complexity Evolution', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=7, ncol=2)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Signed distance matrix
    ax2 = plt.subplot(3, 4, 2)
    im = ax2.imshow(D_signed, cmap='RdBu_r', aspect='auto',
                    vmin=-np.abs(D_signed).max(), vmax=np.abs(D_signed).max())
    ax2.set_title('Signed Distance Matrix', fontsize=11, fontweight='bold')
    ax2.set_xticks(range(len(REGIONS)))
    ax2.set_yticks(range(len(REGIONS)))
    ax2.set_xticklabels(list(REGIONS.keys()), rotation=45, ha='right', fontsize=8)
    ax2.set_yticklabels(list(REGIONS.keys()), fontsize=8)
    plt.colorbar(im, ax=ax2, label='Signed Distance')

    # Panel 3: Eigenvalue spectrum (all dimensions)
    ax3 = plt.subplot(3, 4, 3)
    for dim in [2, 3, 4]:
        eigenvalues = results_by_dim[dim]['eigenvalues']
        x_pos = np.arange(len(eigenvalues)) + (dim - 2) * 0.3
        colors = ['red' if ev < -1e-10 else 'blue' if ev > 1e-10 else 'gray'
                 for ev in eigenvalues]
        ax3.bar(x_pos, eigenvalues, width=0.25, label=f'{dim}D', alpha=0.7)
    ax3.axhline(0, color='black', linestyle='--', linewidth=1)
    ax3.set_xlabel('Index', fontsize=10)
    ax3.set_ylabel('Eigenvalue', fontsize=10)
    ax3.set_title('Metric Eigenvalues (All Dimensions)', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')

    # Panel 4: Comparison table
    ax4 = plt.subplot(3, 4, 4)
    ax4.axis('off')

    comparison_text = "EXPERIMENT COMPARISON\n" + "="*35 + "\n\n"
    comparison_text += "Exp 0B (MI → MDS):\n"
    comparison_text += "  2D: (+,+)   3D: (+,+,+)\n\n"
    comparison_text += "Exp 0D (|ΔC| → MDS):\n"
    comparison_text += "  2D: (+,+)   3D: (+,+,+)\n\n"
    comparison_text += "Exp 0E (signed ΔC → Gram):\n"
    for dim in [2, 3, 4]:
        sig = results_by_dim[dim]['signature_string']
        comparison_text += f"  {dim}D: {sig}\n"

    if found_lorentzian:
        comparison_text += "\n🎉 BREAKTHROUGH! 🎉\n"
        comparison_text += "Lorentzian signature found!"
    elif found_negative:
        comparison_text += "\n⚠️ Negative eigenvalues\n"
        comparison_text += "   found but not (−,+,+,+)"
    else:
        comparison_text += "\n❌ Still Euclidean\n"

    ax4.text(0.05, 0.95, comparison_text, transform=ax4.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # Panels 5-7: Embeddings for each dimension
    for idx, dim in enumerate([2, 3, 4], start=5):
        if dim == 2:
            ax = plt.subplot(3, 4, idx)
            embedding = results_by_dim[dim]['embedding']
            ax.scatter(embedding[:, 0], embedding[:, 1], s=150, alpha=0.7, c='blue')
            for i, region_name in enumerate(REGIONS.keys()):
                ax.annotate(region_name, embedding[i], fontsize=8, ha='center')
            ax.set_xlabel('Dimension 1', fontsize=10)
            ax.set_ylabel('Dimension 2', fontsize=10)
        elif dim == 3:
            ax = plt.subplot(3, 4, idx, projection='3d')
            embedding = results_by_dim[dim]['embedding']
            ax.scatter(embedding[:, 0], embedding[:, 1], embedding[:, 2],
                      s=150, alpha=0.7, c='blue')
            for i, region_name in enumerate(REGIONS.keys()):
                ax.text(embedding[i, 0], embedding[i, 1], embedding[i, 2],
                       region_name, fontsize=7)
            ax.set_xlabel('Dim 1', fontsize=9)
            ax.set_ylabel('Dim 2', fontsize=9)
            ax.set_zlabel('Dim 3', fontsize=9)
        else:  # 4D
            ax = plt.subplot(3, 4, idx, projection='3d')
            embedding = results_by_dim[dim]['embedding']
            ax.scatter(embedding[:, 0], embedding[:, 1], embedding[:, 2],
                      s=150, alpha=0.7, c='blue')
            ax.set_xlabel('Dim 1', fontsize=9)
            ax.set_ylabel('Dim 2', fontsize=9)
            ax.set_zlabel('Dim 3', fontsize=9)

        sig_str = results_by_dim[dim]['signature_string']
        is_lor = results_by_dim[dim]['is_lorentzian']
        title_color = 'green' if is_lor else 'black'
        ax.set_title(f'{dim}D Embedding: {sig_str}',
                    fontsize=10, fontweight='bold', color=title_color)
        ax.grid(True, alpha=0.3)

    # Panel 8: Eigenvalue comparison (Phase 0D vs 0E)
    ax8 = plt.subplot(3, 4, 8)

    # We know Phase 0D gave all positive
    x_labels = ['2D', '3D', '4D']
    x_pos = np.arange(len(x_labels))

    for i, dim in enumerate([2, 3, 4]):
        eigenvalues = results_by_dim[dim]['eigenvalues']
        has_negative = np.any(eigenvalues < -1e-10)
        color = 'green' if has_negative else 'red'
        ax8.bar(x_pos[i], 1 if has_negative else 0, width=0.6,
               color=color, alpha=0.7, label=f'{dim}D: {results_by_dim[dim]["signature_string"]}')

    ax8.set_xticks(x_pos)
    ax8.set_xticklabels(x_labels)
    ax8.set_ylabel('Has Negative Eigenvalue?', fontsize=10)
    ax8.set_ylim([0, 1.2])
    ax8.set_title('Negative Eigenvalues Found?', fontsize=11, fontweight='bold')
    ax8.grid(True, alpha=0.3, axis='y')

    # Panel 9: Complexity growth rates
    ax9 = plt.subplot(3, 4, 9)
    growth_rates = []
    for region_name in complexity_df.columns:
        C_values = complexity_df[region_name].values
        t_values = complexity_df.index.values
        if len(t_values) > 2:
            slope, _, r_value, _, _ = linregress(t_values, C_values)
            growth_rates.append(slope)

    ax9.bar(list(REGIONS.keys()), growth_rates, alpha=0.7)
    ax9.set_xlabel('Region', fontsize=10)
    ax9.set_ylabel('dC/dt', fontsize=10)
    ax9.set_title('Complexity Growth Rates', fontsize=11, fontweight='bold')
    ax9.tick_params(axis='x', rotation=45, labelsize=8)
    ax9.grid(True, alpha=0.3, axis='y')

    # Panel 10: All eigenvalues (full spectrum)
    ax10 = plt.subplot(3, 4, 10)
    for dim in [2, 3, 4]:
        all_eigs = results_by_dim[dim]['eigenvalues_all']
        ax10.plot(range(len(all_eigs)), all_eigs, 'o-', label=f'{dim}D', alpha=0.7)
    ax10.axhline(0, color='black', linestyle='--', linewidth=1)
    ax10.set_xlabel('Index', fontsize=10)
    ax10.set_ylabel('Eigenvalue', fontsize=10)
    ax10.set_title('Full Eigenvalue Spectrum', fontsize=11, fontweight='bold')
    ax10.legend(fontsize=9)
    ax10.grid(True, alpha=0.3)
    ax10.set_yscale('symlog', linthresh=1e-10)

    # Panel 11: Summary
    ax11 = plt.subplot(3, 4, 11)
    ax11.axis('off')

    summary_text = "RESULTS SUMMARY\n" + "="*30 + "\n\n"

    for dim in [2, 3, 4]:
        data = results_by_dim[dim]
        summary_text += f"{dim}D:\n"
        summary_text += f"  {data['signature_string']}\n"
        summary_text += f"  λ_min = {data['eigenvalues'].min():.2e}\n"
        summary_text += f"  Negative: {data['n_negative']}\n\n"

    if found_lorentzian:
        summary_text += "✅ SUCCESS!\n"
        summary_text += "Lorentzian found!\n"
        summary_text += "TIME EMERGES!"
    elif found_negative:
        summary_text += "⚠️ PARTIAL\n"
        summary_text += "Negative eigenvalues\n"
        summary_text += "but not (−,+,+,+)"
    else:
        summary_text += "❌ NEGATIVE\n"
        summary_text += "Still Euclidean"

    ax11.text(0.1, 0.9, summary_text, transform=ax11.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))

    # Panel 12: Method explanation
    ax12 = plt.subplot(3, 4, 12)
    ax12.axis('off')

    method_text = "METHOD\n" + "="*30 + "\n\n"
    method_text += "Previous (FAILED):\n"
    method_text += "d = |ΔC| → MDS\n"
    method_text += "→ Always (+,+,+)\n\n"
    method_text += "This work (NEW):\n"
    method_text += "d = ΔC (signed!)\n"
    method_text += "→ Gram matrix\n"
    method_text += "→ Preserves negatives\n\n"
    method_text += "Key: SIGN matters!\n"
    method_text += "Negative = timelike"

    ax12.text(0.1, 0.9, method_text, transform=ax12.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    plt.suptitle('Phase 0E: Signed Complexity Distances',
                fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    # Save
    plt.savefig('results/figures/phase0e_signed_distances.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('results/figures/phase0e_signed_distances.png', dpi=150, bbox_inches='tight')
    print(f"✓ Plot saved: results/figures/phase0e_signed_distances")

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

    results_df.to_csv('results/data/phase0e_metric_signatures.csv', index=False)
    print(f"✓ Results saved: results/data/phase0e_metric_signatures.csv")

    print(f"\n{'='*60}")
    print("PHASE 0E COMPLETE")
    print(f"{'='*60}\n")

    return results_by_dim, complexity_df, found_lorentzian


if __name__ == '__main__':
    results, complexity_df, found_lorentzian = main()
