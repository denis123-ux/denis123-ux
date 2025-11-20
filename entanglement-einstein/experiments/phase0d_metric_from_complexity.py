#!/usr/bin/env python3
"""
Phase 0D: Extract Metric from Quantum Complexity (Not Mutual Information!)

This is the CRITICAL test:
- Exp 0B showed MI-based distances give ONLY Euclidean metrics (+,+,+,+)
- Exp 0C showed complexity grows linearly with TIME
- NOW: Extract metric from COMPLEXITY to break Euclidean barrier

Hypothesis: Metric from complexity has Lorentzian signature (−,+,+,+)

Theoretical Foundation:
----------------------
Standard approach (Exp 0B):
    d(A,B) = -log[I(A:B) / √(S(A)S(B))]
    Problem: I(A:B) ≥ 0 always → real distances → Euclidean metric

New approach (this experiment):
    d(A,B,t) = |C(A,t) - C(B,t)|
    where C(A,t) = k-local complexity of region A at time t

Why this could work:
- Complexity has TIME DIRECTION (grows with t)
- Spatial directions don't have preferred growth
- This BREAKS time/space symmetry!
- May yield one timelike direction (−) and spatial directions (+)

If successful → MAJOR BREAKTHROUGH in emergent spacetime!

Author: Claude (Anthropic) + Denis
Date: 2025-11-20
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from scipy.stats import linregress
from sklearn.manifold import MDS
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
N_TIME_STEPS = 20    # Number of time snapshots
J = 1.0              # Coupling strength
h = 0.5              # Transverse field

# Region definitions (different spatial slices)
REGIONS = {
    'region_1': [0, 1],           # Sites 0-1
    'region_2': [2, 3],           # Sites 2-3
    'region_3': [4, 5],           # Sites 4-5
    'region_4': [6, 7],           # Sites 6-7
    'region_12': [0, 1, 2, 3],    # Sites 0-3
    'region_23': [2, 3, 4, 5],    # Sites 2-5
    'region_34': [4, 5, 6, 7],    # Sites 4-7
}

# ==================== COMPLEXITY CALCULATION ====================

def compute_reduced_density_matrix(state: np.ndarray,
                                   region_sites: List[int],
                                   n_sites: int,
                                   d_phys: int = 2) -> np.ndarray:
    """
    Compute reduced density matrix for a region.

    Parameters
    ----------
    state : ndarray
        Full quantum state vector (length 2^n_sites)
    region_sites : list
        List of site indices in region
    n_sites : int
        Total number of sites
    d_phys : int
        Physical dimension per site (2 for qubits)

    Returns
    -------
    rho_A : ndarray
        Reduced density matrix for region
    """
    # Convert state to density matrix
    rho_full = np.outer(state, state.conj())

    # Get dimensions
    n_A = len(region_sites)
    n_B = n_sites - n_A
    d_A = d_phys**n_A
    d_B = d_phys**n_B

    # Create index mapping
    # This is simplified - assumes region is contiguous for efficiency
    # For general case, would need tensor reshaping

    if region_sites == list(range(min(region_sites), max(region_sites) + 1)):
        # Contiguous region - can use simple reshape
        rho_full_reshaped = rho_full.reshape(d_A, d_B, d_A, d_B)
        rho_A = np.trace(rho_full_reshaped, axis1=1, axis2=3)
    else:
        # Non-contiguous - need full partial trace (slower)
        rho_A = partial_trace_general(rho_full, region_sites, n_sites, d_phys)

    return rho_A


def partial_trace_general(rho: np.ndarray,
                         keep_sites: List[int],
                         n_sites: int,
                         d_phys: int = 2) -> np.ndarray:
    """General partial trace (works for any subset of sites)."""
    trace_sites = [i for i in range(n_sites) if i not in keep_sites]

    n_keep = len(keep_sites)
    d_keep = d_phys**n_keep

    rho_A = np.zeros((d_keep, d_keep), dtype=complex)

    # Iterate over basis states
    for i in range(d_keep):
        for j in range(d_keep):
            # Sum over traced-out subspace
            for k in range(2**(n_sites - n_keep)):
                # Construct full basis indices
                idx_i = construct_full_index(i, k, keep_sites, trace_sites, d_phys)
                idx_j = construct_full_index(j, k, keep_sites, trace_sites, d_phys)
                rho_A[i, j] += rho[idx_i, idx_j]

    return rho_A


def construct_full_index(keep_idx: int, trace_idx: int,
                        keep_sites: List[int], trace_sites: List[int],
                        d_phys: int) -> int:
    """Construct full system index from keep and trace indices."""
    n_sites = len(keep_sites) + len(trace_sites)

    # Convert indices to bit strings
    keep_bits = [(keep_idx >> i) & 1 for i in range(len(keep_sites))]
    trace_bits = [(trace_idx >> i) & 1 for i in range(len(trace_sites))]

    # Construct full bit string
    full_bits = [0] * n_sites
    for i, site in enumerate(keep_sites):
        full_bits[site] = keep_bits[i]
    for i, site in enumerate(trace_sites):
        full_bits[site] = trace_bits[i]

    # Convert to index
    full_idx = sum(bit * (2**i) for i, bit in enumerate(full_bits))
    return full_idx


def von_neumann_entropy(rho: np.ndarray, tol: float = 1e-12) -> float:
    """
    Compute von Neumann entropy S = -Tr(ρ log ρ).

    Parameters
    ----------
    rho : ndarray
        Density matrix
    tol : float
        Tolerance for zero eigenvalues

    Returns
    -------
    S : float
        Von Neumann entropy
    """
    # Get eigenvalues
    eigvals = np.linalg.eigvalsh(rho)

    # Filter out numerical zeros
    eigvals = eigvals[eigvals > tol]

    # Normalize (in case of numerical errors)
    eigvals = eigvals / np.sum(eigvals)

    # Compute entropy
    S = -np.sum(eigvals * np.log(eigvals))

    return S


def compute_klocal_complexity(state: np.ndarray,
                              region_sites: List[int],
                              n_sites: int,
                              k: int = 2) -> float:
    """
    Compute k-local complexity for a region.

    C_klocal = Σ_{all k-site subregions in region} S(subregion)

    This measures total entanglement within the region.

    Parameters
    ----------
    state : ndarray
        Full quantum state
    region_sites : list
        Sites in the region
    n_sites : int
        Total system size
    k : int
        Locality (2 = pairs, 3 = triples, etc.)

    Returns
    -------
    C : float
        K-local complexity
    """
    from itertools import combinations

    C = 0.0

    # Sum over all k-site subregions
    for subregion in combinations(region_sites, min(k, len(region_sites))):
        subregion = list(subregion)

        # Compute reduced density matrix
        rho_sub = compute_reduced_density_matrix(state, subregion, n_sites)

        # Add entropy
        S_sub = von_neumann_entropy(rho_sub)
        C += S_sub

    return C


# ==================== TIME EVOLUTION ====================

def create_hamiltonian_1d_chain(n_sites: int, J: float = 1.0, h: float = 0.5) -> np.ndarray:
    """
    Create 1D transverse-field Ising Hamiltonian.

    H = -J Σ_i σ^z_i σ^z_{i+1} - h Σ_i σ^x_i
    """
    dim = 2**n_sites
    H = np.zeros((dim, dim), dtype=complex)

    # Pauli matrices
    sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
    sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
    I = np.eye(2, dtype=complex)

    # Interaction term: -J Σ σ^z_i σ^z_{i+1}
    for i in range(n_sites - 1):
        # Build σ^z_i ⊗ σ^z_{i+1}
        op = 1.0
        for j in range(n_sites):
            if j == i or j == i + 1:
                op = np.kron(op, sigma_z) if isinstance(op, np.ndarray) else sigma_z
            else:
                op = np.kron(op, I) if isinstance(op, np.ndarray) else I

        H -= J * op

    # Transverse field: -h Σ σ^x_i
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
    """
    Evolve state under Hamiltonian: |ψ(t)⟩ = exp(-iHt)|ψ₀⟩

    Returns dict: {t: state_at_t}
    """
    states = {}

    for t in tqdm(time_steps, desc="Time evolution"):
        # Compute U(t) = exp(-iHt)
        U_t = expm(-1j * hamiltonian * t)

        # Evolve state
        state_t = U_t @ initial_state

        # Normalize (in case of numerical errors)
        state_t = state_t / np.linalg.norm(state_t)

        states[t] = state_t

    return states


# ==================== METRIC EXTRACTION ====================

def compute_complexity_distance_matrix(states: Dict[float, np.ndarray],
                                      regions: Dict[str, List[int]],
                                      n_sites: int) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Compute distance matrix based on complexity differences.

    d(A,B,t) = |C(A,t) - C(B,t)|

    We average over time to get stable metric.

    Returns
    -------
    D : ndarray
        Distance matrix (n_regions × n_regions)
    complexity_df : DataFrame
        Complexity values for all regions and times
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

    # Compute distance matrix (average over time)
    D = np.zeros((n_regions, n_regions))

    for i in range(n_regions):
        for j in range(i + 1, n_regions):
            # Distance = average |C(A,t) - C(B,t)| over all times
            distances = np.abs(complexity_matrix[:, i] - complexity_matrix[:, j])
            D[i, j] = np.mean(distances)
            D[j, i] = D[i, j]  # Symmetric

    return D, complexity_df


def extract_metric_from_distances(D: np.ndarray,
                                  target_dims: List[int] = [2, 3, 4]) -> Dict[int, Dict]:
    """
    Extract metric tensor from distance matrix using MDS.

    Returns dict: {dimension: {'embedding': coords, 'metric': g_μν, 'analysis': ...}}
    """
    results = {}

    for dim in target_dims:
        print(f"\nExtracting metric in {dim}D...")

        # MDS embedding
        mds = MDS(n_components=dim, dissimilarity='precomputed', random_state=42)
        embedding = mds.fit_transform(D)

        # Compute metric tensor at origin (approximate)
        # g_μν ≈ (1/N) Σ_i (x^μ_i x^ν_i)
        metric = (embedding.T @ embedding) / len(embedding)

        # Analyze signature
        eigenvalues = np.linalg.eigvalsh(metric)
        eigenvalues_sorted = np.sort(eigenvalues)[::-1]  # Largest first

        n_positive = np.sum(eigenvalues > 1e-10)
        n_negative = np.sum(eigenvalues < -1e-10)
        n_zero = dim - n_positive - n_negative

        is_lorentzian = (n_negative == 1 and n_positive == dim - 1)
        is_euclidean = (n_positive == dim and n_negative == 0)

        signature_string = '(' + ','.join([
            '-' if ev < -1e-10 else ('+' if ev > 1e-10 else '0')
            for ev in eigenvalues_sorted
        ]) + ')'

        results[dim] = {
            'embedding': embedding,
            'metric': metric,
            'eigenvalues': eigenvalues_sorted,
            'n_positive': n_positive,
            'n_negative': n_negative,
            'n_zero': n_zero,
            'is_lorentzian': is_lorentzian,
            'is_euclidean': is_euclidean,
            'signature_string': signature_string,
            'stress': mds.stress_,
        }

    return results


# ==================== MAIN EXPERIMENT ====================

def main():
    """Run Phase 0D: Metric from Complexity."""

    # Preregister hypothesis
    logger = preregister_hypothesis(
        name="phase0d_metric_from_complexity",
        hypothesis="Metric extracted from complexity distances has Lorentzian signature (−,+,+,+)",
        prediction=(
            "At least one dimension will show signature (−,+,+,...) or (−,+,+,+). "
            "Negative eigenvalue corresponds to timelike direction."
        ),
        method=(
            "1. Evolve quantum state |ψ(t)⟩ = exp(-iHt)|ψ₀⟩\n"
            "2. Compute k-local complexity C(region, t) for all regions\n"
            "3. Build distance matrix: d(A,B) = ⟨|C(A,t) - C(B,t)|⟩_t\n"
            "4. Extract metric via MDS\n"
            "5. Analyze eigenvalues for signature"
        ),
        falsifiability=(
            "If ALL dimensions show only positive eigenvalues (Euclidean) "
            "AND no negative eigenvalues found → complexity method also fails"
        ),
    )

    print(f"\n{'='*60}")
    print(f"PHASE 0D: METRIC FROM COMPLEXITY (NOT MI!)")
    print(f"{'='*60}")
    print(f"System size: {N_SITES} qubits")
    print(f"Time evolution: t ∈ [0, {T_MAX}]")
    print(f"Time steps: {N_TIME_STEPS}")
    print(f"Regions: {len(REGIONS)}")
    print(f"Testing: Lorentzian signature from complexity")
    print(f"{'='*60}\n")

    # ==================== SETUP ====================
    print("Creating Hamiltonian...")
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from phase0_time_emergence import create_hamiltonian_1d_chain as create_H
    H = create_H(N_SITES, J=J, h=h)
    print(f"  Hamiltonian shape: {H.shape}")

    # Initial state: product state |000...0⟩
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

    # ==================== COMPLEXITY DISTANCES ====================
    print(f"\n{'='*60}")
    print("COMPUTING COMPLEXITY-BASED DISTANCES")
    print(f"{'='*60}")

    D, complexity_df = compute_complexity_distance_matrix(states, REGIONS, N_SITES)

    print(f"\n  Distance matrix shape: {D.shape}")
    print(f"  Distance range: [{D[D > 0].min():.4f}, {D.max():.4f}]")

    # Save complexity data
    complexity_df.to_csv('results/data/phase0d_complexity_evolution.csv')
    print(f"  ✓ Complexity data saved")

    # ==================== METRIC EXTRACTION ====================
    print(f"\n{'='*60}")
    print("EXTRACTING METRIC FROM COMPLEXITY")
    print(f"{'='*60}")

    results_by_dim = extract_metric_from_distances(D, target_dims=[2, 3, 4])

    # ==================== SIGNATURE ANALYSIS ====================
    print(f"\n{'='*60}")
    print("METRIC SIGNATURE ANALYSIS")
    print(f"{'='*60}\n")

    found_lorentzian = False

    for dim, data in results_by_dim.items():
        analysis = data
        eigenvalues = analysis['eigenvalues']

        print(f"\n{dim}D Embedding:")
        print(f"  Eigenvalues: {eigenvalues}")
        print(f"  Signature: {analysis['signature_string']}")
        print(f"  Positive: {analysis['n_positive']}, Negative: {analysis['n_negative']}, Zero: {analysis['n_zero']}")
        print(f"  MDS Stress: {analysis['stress']:.6f}")

        if analysis['is_lorentzian']:
            print(f"  🎯 LORENTZIAN SIGNATURE FOUND! (−,+,...,+)")
            found_lorentzian = True
        elif analysis['is_euclidean']:
            print(f"  Euclidean signature (+,+,...,+)")
        else:
            print(f"  Mixed signature")

    # ==================== HYPOTHESIS TEST ====================
    print(f"\n{'='*60}")
    print("HYPOTHESIS TEST: Lorentzian from Complexity?")
    print(f"{'='*60}\n")

    if found_lorentzian:
        print("✅ HYPOTHESIS CONFIRMED!")
        print("   Lorentzian signature (−,+,+,...) found!")
        print("   TIME DIRECTION EMERGES FROM COMPLEXITY!")
        print("\n🎉 MAJOR BREAKTHROUGH!")
        print("   First proof of emergent Lorentzian spacetime from quantum complexity")
        print("   Publishable in Nature or Science")
    else:
        all_euclidean = all(data['is_euclidean'] for data in results_by_dim.values())
        if all_euclidean:
            print("❌ HYPOTHESIS REJECTED")
            print("   All signatures are Euclidean (+,+,+,...)")
            print("   Complexity method also gives Euclidean geometry")
            print("\n   → Need alternative approach:")
            print("   - Pseudo-entropy (complex-valued)")
            print("   - Timelike entanglement entropy")
            print("   - Different distance measure")
        else:
            print("⚠️  INCONCLUSIVE")
            print("   Mixed signatures found (neither clearly Lorentzian nor Euclidean)")
            print("   May need larger system or different analysis")

    # ==================== VISUALIZATION ====================
    print(f"\n{'='*60}")
    print("GENERATING VISUALIZATION")
    print(f"{'='*60}\n")

    fig = plt.figure(figsize=(18, 12))

    # Panel 1: Complexity evolution for all regions
    ax1 = plt.subplot(3, 3, 1)
    for region_name in complexity_df.columns:
        ax1.plot(complexity_df.index, complexity_df[region_name],
                label=region_name, marker='o', markersize=3)
    ax1.set_xlabel('Time', fontsize=10)
    ax1.set_ylabel('K-Local Complexity', fontsize=10)
    ax1.set_title('Complexity Evolution (All Regions)', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=6, ncol=2)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Distance matrix heatmap
    ax2 = plt.subplot(3, 3, 2)
    im = ax2.imshow(D, cmap='viridis', aspect='auto')
    ax2.set_title('Complexity Distance Matrix', fontsize=11, fontweight='bold')
    ax2.set_xticks(range(len(REGIONS)))
    ax2.set_yticks(range(len(REGIONS)))
    ax2.set_xticklabels(list(REGIONS.keys()), rotation=45, ha='right', fontsize=7)
    ax2.set_yticklabels(list(REGIONS.keys()), fontsize=7)
    plt.colorbar(im, ax=ax2, label='Distance')

    # Panel 3: Eigenvalue comparison
    ax3 = plt.subplot(3, 3, 3)
    dims = sorted(results_by_dim.keys())
    for dim in dims:
        eigenvalues = results_by_dim[dim]['eigenvalues']
        x_pos = np.arange(len(eigenvalues)) + (dim - 2) * 0.25
        colors = ['red' if ev < -1e-10 else 'blue' for ev in eigenvalues]
        ax3.bar(x_pos, eigenvalues, width=0.2, label=f'{dim}D', alpha=0.7)
    ax3.axhline(0, color='black', linestyle='--', linewidth=1)
    ax3.set_xlabel('Eigenvalue Index', fontsize=10)
    ax3.set_ylabel('Eigenvalue', fontsize=10)
    ax3.set_title('Metric Eigenvalues (By Dimension)', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)

    # Panels 4-6: Embeddings for each dimension
    for idx, dim in enumerate([2, 3, 4], start=4):
        ax = plt.subplot(3, 3, idx)
        embedding = results_by_dim[dim]['embedding']

        if dim == 2:
            ax.scatter(embedding[:, 0], embedding[:, 1], s=100, alpha=0.7)
            for i, region_name in enumerate(REGIONS.keys()):
                ax.annotate(region_name, embedding[i], fontsize=7, ha='center')
            ax.set_xlabel('Dimension 1', fontsize=10)
            ax.set_ylabel('Dimension 2', fontsize=10)
        elif dim == 3:
            from mpl_toolkits.mplot3d import Axes3D
            ax.remove()
            ax = fig.add_subplot(3, 3, idx, projection='3d')
            ax.scatter(embedding[:, 0], embedding[:, 1], embedding[:, 2],
                      s=100, alpha=0.7)
            for i, region_name in enumerate(REGIONS.keys()):
                ax.text(embedding[i, 0], embedding[i, 1], embedding[i, 2],
                       region_name, fontsize=6)
            ax.set_xlabel('Dim 1', fontsize=9)
            ax.set_ylabel('Dim 2', fontsize=9)
            ax.set_zlabel('Dim 3', fontsize=9)
        else:  # 4D - show first 3 dimensions
            from mpl_toolkits.mplot3d import Axes3D
            ax.remove()
            ax = fig.add_subplot(3, 3, idx, projection='3d')
            ax.scatter(embedding[:, 0], embedding[:, 1], embedding[:, 2],
                      s=100, alpha=0.7)
            ax.set_xlabel('Dim 1', fontsize=9)
            ax.set_ylabel('Dim 2', fontsize=9)
            ax.set_zlabel('Dim 3', fontsize=9)
            ax.set_title(f'4D Embedding (first 3 dims)', fontsize=10, fontweight='bold')

        sig_str = results_by_dim[dim]['signature_string']
        is_lor = results_by_dim[dim]['is_lorentzian']
        title_color = 'green' if is_lor else 'black'
        ax.set_title(f'{dim}D: {sig_str}', fontsize=10, fontweight='bold', color=title_color)
        ax.grid(True, alpha=0.3)

    # Panel 7: Complexity growth rates
    ax7 = plt.subplot(3, 3, 7)
    for region_name in complexity_df.columns:
        C_values = complexity_df[region_name].values
        t_values = complexity_df.index.values
        if len(t_values) > 2:
            slope, intercept, r_value, p_value, std_err = linregress(t_values, C_values)
            ax7.bar(region_name, slope, alpha=0.7)
    ax7.set_xlabel('Region', fontsize=10)
    ax7.set_ylabel('dC/dt', fontsize=10)
    ax7.set_title('Complexity Growth Rates', fontsize=11, fontweight='bold')
    ax7.tick_params(axis='x', rotation=45, labelsize=7)
    ax7.grid(True, alpha=0.3, axis='y')

    # Panel 8: Signature summary
    ax8 = plt.subplot(3, 3, 8)
    ax8.axis('off')

    summary_text = "SIGNATURE ANALYSIS\n" + "="*30 + "\n\n"
    for dim in [2, 3, 4]:
        data = results_by_dim[dim]
        summary_text += f"{dim}D: {data['signature_string']}\n"
        summary_text += f"   λ = {data['eigenvalues']}\n"
        if data['is_lorentzian']:
            summary_text += "   ✓ LORENTZIAN!\n"
        elif data['is_euclidean']:
            summary_text += "   Euclidean\n"
        else:
            summary_text += "   Mixed\n"
        summary_text += "\n"

    if found_lorentzian:
        summary_text += "\n🎉 BREAKTHROUGH! 🎉\n"
        summary_text += "Lorentzian signature found!\n"
        summary_text += "Time emerges from complexity!"
    else:
        summary_text += "\nNo Lorentzian signature\n"
        summary_text += "Complexity → Euclidean"

    ax8.text(0.1, 0.9, summary_text, transform=ax8.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Panel 9: Comparison with MI-based (Exp 0B)
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')

    comparison_text = "COMPLEXITY vs MI\n" + "="*30 + "\n\n"
    comparison_text += "Exp 0B (MI-based):\n"
    comparison_text += "  2D: (+,+)\n"
    comparison_text += "  3D: (+,+,+)\n"
    comparison_text += "  4D: (+,+,+,+)\n"
    comparison_text += "  ALL EUCLIDEAN\n\n"
    comparison_text += "Exp 0D (Complexity):\n"
    for dim in [2, 3, 4]:
        data = results_by_dim[dim]
        comparison_text += f"  {dim}D: {data['signature_string']}\n"

    if found_lorentzian:
        comparison_text += "\n→ COMPLEXITY BREAKS\n"
        comparison_text += "  EUCLIDEAN BARRIER!"
    else:
        comparison_text += "\n→ Both give Euclidean\n"
        comparison_text += "  Need new approach"

    ax9.text(0.1, 0.9, comparison_text, transform=ax9.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    plt.suptitle('Phase 0D: Metric from Complexity', fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    # Save
    plt.savefig('results/figures/phase0d_metric_from_complexity.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('results/figures/phase0d_metric_from_complexity.png', dpi=150, bbox_inches='tight')
    print(f"✓ Plot saved: results/figures/phase0d_metric_from_complexity")

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

    results_df.to_csv('results/data/phase0d_metric_signatures.csv', index=False)
    print(f"✓ Results saved: results/data/phase0d_metric_signatures.csv")

    print(f"\n{'='*60}")
    print("PHASE 0D COMPLETE")
    print(f"{'='*60}\n")

    return results_by_dim, complexity_df, found_lorentzian


if __name__ == '__main__':
    results, complexity_df, found_lorentzian = main()
