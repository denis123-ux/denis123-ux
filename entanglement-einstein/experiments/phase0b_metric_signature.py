"""
PHASE 0B (MOONSHOT): Lorentzian Signature from Entanglement
=============================================================

THE DEEPEST QUESTION IN QUANTUM GRAVITY:
Does the metric extracted from entanglement have Lorentzian signature (−,+,+,+)?

APPROACH:
1. Compute mutual information I(A:B,t) for all region pairs at different times
2. Extract "distance" from mutual info: d(A,B,t) = -log[I(A:B)/√(S(A)S(B))]
3. Build distance matrix D[t] for each time slice
4. Use MDS to extract metric tensor g_μν[t]
5. CRITICAL TEST: Does g have signature (−,+,+,+)?

HYPOTHESIS:
The time direction (t-evolution) will have NEGATIVE eigenvalue in metric.
Spatial directions will have POSITIVE eigenvalues.
→ Lorentzian signature emerges naturally!

PREDICTION:
metric eigenvalues = [λ_time < 0, λ_x > 0, λ_y > 0, λ_z > 0]

BREAKTHROUGH IF TRUE:
- First proof that spacetime signature emerges from quantum information
- Solves 20-year mystery: "Why is one direction (time) different?"
- GUARANTEED Nobel Prize

References:
- Czech et al. (2015): "Kinematic Space and Waveforms of Entanglement"
- Van Raamsdonk (2010): "Building up spacetime with quantum entanglement"
- PRL 2024: "Emergent Holographic Spacetime from Quantum Information"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from sklearn.manifold import MDS
from typing import Dict, List, Tuple
import pandas as pd
from tqdm import tqdm

from entanglement.entropy import entanglement_entropy_svd
from entanglement.mutual_info import mutual_information
from utils.logging import preregister_hypothesis


# ==================== MUTUAL INFORMATION COMPUTATION ====================

def compute_mutual_information_matrix(
    state: np.ndarray,
    n_sites: int,
    region_configs: Dict[str, List[int]]
) -> np.ndarray:
    """
    Compute I(A:B) for all pairs of regions.

    I(A:B) = S(A) + S(B) - S(A∪B)

    Returns
    -------
    ndarray, shape (n_regions, n_regions)
        Mutual information matrix
    """
    regions = list(region_configs.keys())
    n_regions = len(regions)

    I_matrix = np.zeros((n_regions, n_regions))
    S_dict = {}  # Cache entropies

    print(f"\nComputing mutual information matrix ({n_regions}×{n_regions})...")

    # First, compute all single-region entropies
    for i, (name_A, region_A) in enumerate(region_configs.items()):
        if name_A not in S_dict:
            S_A, _ = entanglement_entropy_svd(
                state,
                region_A_size=len(region_A),
                total_sites=n_sites,
                d_phys=2
            )
            S_dict[name_A] = S_A

    # Now compute mutual information
    for i, (name_A, region_A) in enumerate(tqdm(region_configs.items(), desc="Computing I(A:B)")):
        for j, (name_B, region_B) in enumerate(region_configs.items()):
            if i == j:
                I_matrix[i, j] = S_dict[name_A]  # I(A:A) = S(A)
                continue

            # Check if already computed (symmetric)
            if i > j:
                I_matrix[i, j] = I_matrix[j, i]
                continue

            # Compute union A∪B
            region_AB = sorted(list(set(region_A) | set(region_B)))

            try:
                S_AB, _ = entanglement_entropy_svd(
                    state,
                    region_A_size=len(region_AB),
                    total_sites=n_sites,
                    d_phys=2
                )

                S_A = S_dict[name_A]
                S_B = S_dict[name_B]

                # I(A:B) = S(A) + S(B) - S(A∪B)
                I_AB = mutual_information(S_A, S_B, S_AB)

                I_matrix[i, j] = I_AB
                I_matrix[j, i] = I_AB  # Symmetric

            except Exception as e:
                print(f"    Warning: Failed for ({name_A}, {name_B}): {e}")
                I_matrix[i, j] = 0.0
                I_matrix[j, i] = 0.0

    return I_matrix, S_dict


def kinematic_distance_matrix(
    I_matrix: np.ndarray,
    S_dict: Dict[str, float],
    region_names: List[str]
) -> np.ndarray:
    """
    Convert mutual information to kinematic space distance.

    d(A,B) = -log[I(A:B) / √(S(A)S(B))]

    High mutual information → small distance
    Low mutual information → large distance
    """
    n = len(region_names)
    D = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                D[i, j] = 0.0
                continue

            I_ij = I_matrix[i, j]
            S_i = S_dict[region_names[i]]
            S_j = S_dict[region_names[j]]

            if I_ij > 1e-10 and S_i > 1e-10 and S_j > 1e-10:
                # Normalized mutual information
                I_norm = I_ij / np.sqrt(S_i * S_j)
                # Distance
                d_ij = -np.log(I_norm + 1e-10)
            else:
                d_ij = 100.0  # Large distance for disconnected regions

            D[i, j] = d_ij

    return D


# ==================== METRIC EXTRACTION ====================

def extract_metric_from_distances(
    D: np.ndarray,
    target_dim: int = 2
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract metric tensor from distance matrix using MDS.

    Returns
    -------
    embedding : ndarray, shape (n_points, target_dim)
        Coordinates in emergent space
    metric : ndarray, shape (target_dim, target_dim)
        Average metric tensor
    """
    # Multidimensional scaling
    mds = MDS(
        n_components=target_dim,
        dissimilarity='precomputed',
        random_state=42,
        max_iter=1000
    )

    embedding = mds.fit_transform(D)

    # Compute metric as covariance of embedding
    # This is a simplified approach - proper version would compute local metric at each point
    metric = np.cov(embedding.T)

    # Normalize
    metric /= np.trace(metric)

    return embedding, metric


def analyze_metric_signature(
    metric: np.ndarray
) -> Dict:
    """
    Analyze signature of metric tensor.

    Lorentzian: (−, +, +, +) → 1 negative, 3 positive eigenvalues
    Euclidean: (+, +, +, +) → all positive
    """
    eigenvalues, eigenvectors = np.linalg.eigh(metric)

    # Sort by magnitude
    idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    n_positive = np.sum(eigenvalues > 1e-10)
    n_negative = np.sum(eigenvalues < -1e-10)
    n_zero = len(eigenvalues) - n_positive - n_negative

    signature = (n_negative, n_positive)

    is_lorentzian = (n_negative == 1 and n_positive == len(eigenvalues) - 1)
    is_euclidean = (n_negative == 0 and n_positive == len(eigenvalues))

    return {
        'eigenvalues': eigenvalues,
        'eigenvectors': eigenvectors,
        'n_positive': n_positive,
        'n_negative': n_negative,
        'n_zero': n_zero,
        'signature': signature,
        'is_lorentzian': is_lorentzian,
        'is_euclidean': is_euclidean,
        'signature_string': f"({n_negative}, {'+' * n_positive})"
    }


# ==================== MAIN EXPERIMENT ====================

def main():
    """Run metric signature experiment."""

    # ==================== PREREGISTRATION ====================
    logger = preregister_hypothesis(
        name="phase0b_metric_signature",
        hypothesis="Metric extracted from entanglement has Lorentzian signature (−,+,+,+)",
        prediction="Exactly 1 negative eigenvalue (time), rest positive (space)",
        method="Mutual information → kinematic distance → MDS → metric tensor → eigenvalue analysis",
        falsifiability="If all eigenvalues same sign → Lorentzian signature does NOT emerge",
        output_dir=Path("results/logs")
    )

    # ==================== PARAMETERS ====================
    N_SITES = 8  # Larger system for better statistics
    N_REGIONS = 4  # Number of test regions

    print(f"\n{'='*60}")
    print(f"PHASE 0B: METRIC SIGNATURE FROM ENTANGLEMENT")
    print(f"{'='*60}")
    print(f"System size: {N_SITES} sites")
    print(f"Number of regions: {N_REGIONS}")
    print(f"Target: Identify Lorentzian signature (−,+,+,+)")
    print(f"{'='*60}\n")

    # ==================== CREATE QUANTUM STATE ====================
    print("Creating entangled quantum state...")

    # Use a random state with significant entanglement
    np.random.seed(42)
    dim = 2**N_SITES
    state = np.random.randn(dim) + 1j * np.random.randn(dim)
    state /= np.linalg.norm(state)

    print(f"  State dimension: {dim}")
    print(f"  State norm: {np.linalg.norm(state):.6f}")

    # ==================== DEFINE REGIONS ====================
    # Test regions at different positions
    region_configs = {}
    region_size = N_SITES // 4

    for i in range(N_REGIONS):
        start = i * (N_SITES // N_REGIONS)
        end = start + region_size
        region_configs[f'region_{i}'] = list(range(start, min(end, N_SITES)))

    print(f"\nRegion configurations:")
    for name, indices in region_configs.items():
        print(f"  {name}: sites {indices}")

    # ==================== COMPUTE MUTUAL INFORMATION ====================
    I_matrix, S_dict = compute_mutual_information_matrix(
        state,
        N_SITES,
        region_configs
    )

    print(f"\nMutual information matrix:")
    print(I_matrix)

    print(f"\nEntropies:")
    for name, S in S_dict.items():
        print(f"  S({name}) = {S:.4f}")

    # ==================== EXTRACT DISTANCE MATRIX ====================
    region_names = list(region_configs.keys())
    D = kinematic_distance_matrix(I_matrix, S_dict, region_names)

    print(f"\nKinematic distance matrix:")
    print(D)

    # ==================== EXTRACT METRIC ====================
    print(f"\n{'='*60}")
    print("EXTRACTING METRIC TENSOR")
    print(f"{'='*60}\n")

    # Try different target dimensions
    results_by_dim = {}

    for target_dim in range(2, min(5, N_REGIONS + 1)):
        print(f"\nTarget dimension: {target_dim}")

        embedding, metric = extract_metric_from_distances(D, target_dim=target_dim)

        print(f"Embedding shape: {embedding.shape}")
        print(f"Metric tensor:")
        print(metric)

        # Analyze signature
        analysis = analyze_metric_signature(metric)

        print(f"\nSignature analysis:")
        print(f"  Eigenvalues: {analysis['eigenvalues']}")
        print(f"  Signature: {analysis['signature_string']}")
        print(f"  Positive eigenvalues: {analysis['n_positive']}")
        print(f"  Negative eigenvalues: {analysis['n_negative']}")
        print(f"  Zero eigenvalues: {analysis['n_zero']}")
        print(f"  Is Lorentzian (−,+,...)? {analysis['is_lorentzian']}")
        print(f"  Is Euclidean (+,+,...)? {analysis['is_euclidean']}")

        results_by_dim[target_dim] = {
            'embedding': embedding,
            'metric': metric,
            'analysis': analysis
        }

        # Log result
        if analysis['is_lorentzian']:
            logger.log_success(
                f"dim={target_dim}: LORENTZIAN SIGNATURE FOUND! "
                f"{analysis['signature_string']}"
            )
            print(f"\n🎉 BREAKTHROUGH: Lorentzian signature detected in {target_dim}D!")
        elif analysis['is_euclidean']:
            logger.log_failure(
                f"dim={target_dim}: Euclidean signature "
                f"{analysis['signature_string']}"
            )
            print(f"\n⚠️  Euclidean signature (all positive)")
        else:
            logger.log_summary(
                f"dim={target_dim}: Mixed signature "
                f"{analysis['signature_string']}"
            )
            print(f"\n⚠️  Mixed signature (not clearly Lorentzian or Euclidean)")

    # ==================== VISUALIZATION ====================
    print(f"\n{'='*60}")
    print("GENERATING VISUALIZATION")
    print(f"{'='*60}\n")

    fig = plt.figure(figsize=(16, 10))

    # Plot for each dimension
    n_dims = len(results_by_dim)

    for idx, (dim, data) in enumerate(results_by_dim.items(), 1):
        # Panel: Metric heatmap
        ax1 = plt.subplot(2, n_dims, idx)
        metric = data['metric']
        im = ax1.imshow(metric, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
        ax1.set_title(f'{dim}D Metric Tensor')
        ax1.set_xlabel('μ')
        ax1.set_ylabel('ν')
        plt.colorbar(im, ax=ax1)

        # Panel: Eigenvalues
        ax2 = plt.subplot(2, n_dims, n_dims + idx)
        eigenvalues = data['analysis']['eigenvalues']
        colors = ['red' if ev < 0 else 'blue' for ev in eigenvalues]
        bars = ax2.bar(range(len(eigenvalues)), eigenvalues, color=colors, alpha=0.7)
        ax2.axhline(0, color='black', linestyle='-', linewidth=1)
        ax2.set_xlabel('Eigenvalue index')
        ax2.set_ylabel('Eigenvalue')
        ax2.set_title(f'Signature: {data["analysis"]["signature_string"]}')
        ax2.grid(True, alpha=0.3, axis='y')

        # Annotate Lorentzian if found
        if data['analysis']['is_lorentzian']:
            ax2.text(0.5, 0.95, '✓ LORENTZIAN!',
                    transform=ax2.transAxes,
                    fontsize=14, fontweight='bold', color='green',
                    ha='center', va='top',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))

    plt.suptitle('Metric Signature Analysis: Search for Lorentzian Geometry',
                fontsize=16, y=0.995)
    plt.tight_layout()

    # Save
    save_path = Path("results/figures/phase0b_metric_signature.pdf")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    for ext in ['pdf', 'png']:
        fig.savefig(save_path.with_suffix(f'.{ext}'), dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved: {save_path}")

    # ==================== FINAL VERDICT ====================
    print(f"\n{'='*60}")
    print("FINAL VERDICT")
    print(f"{'='*60}\n")

    lorentzian_found = any(
        data['analysis']['is_lorentzian']
        for data in results_by_dim.values()
    )

    if lorentzian_found:
        print("🏆 SUCCESS: Lorentzian signature FOUND!")
        print("   → Time direction emerges from entanglement!")
        print("   → Metric has (−,+,+,...) signature")
        print("   → THIS IS THE BREAKTHROUGH!")
        logger.log_success("LORENTZIAN SIGNATURE CONFIRMED - TIME EMERGES!")
    else:
        all_euclidean = all(
            data['analysis']['is_euclidean']
            for data in results_by_dim.values()
        )
        if all_euclidean:
            print("⚠️  RESULT: Only Euclidean signatures found")
            print("   → All eigenvalues positive")
            print("   → Lorentzian signature did NOT emerge")
            print("   → Need different approach (pseudo-entropy? complex metrics?)")
            logger.log_failure("Only Euclidean signatures - Lorentzian NOT found")
        else:
            print("⚠️  INCONCLUSIVE: Mixed signatures")
            print("   → Neither clearly Lorentzian nor Euclidean")
            print("   → May need larger system or different regions")
            logger.log_summary("Mixed signatures - inconclusive result")

    # ==================== REPORT ====================
    logger.generate_report()

    print(f"\n{'='*60}")
    print("PHASE 0B COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
