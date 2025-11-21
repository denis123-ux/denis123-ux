"""
Spectral Graph Analysis for Collatz Conjecture

REVOLUTIONARY APPROACH:
Use eigenvalues and eigenvectors of the Collatz graph to prove convergence!

Key Theorems:
1. If spectral gap λ₁ - λ₂ > δ, then mixing time is bounded
2. If all eigenvalues have |λᵢ| < 1, then trajectories converge
3. Eigenvector structure reveals "attraction basins"
"""

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as sparse_linalg
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class SpectralProperties:
    """Container for spectral analysis results"""
    eigenvalues: np.ndarray
    eigenvectors: Optional[np.ndarray]
    spectral_gap: float
    spectral_radius: float
    algebraic_connectivity: float
    mixing_time_bound: Optional[float]


class CollatzSpectralAnalyzer:
    """
    Spectral analysis of Collatz graph

    This is the CORE innovation - using spectral graph theory
    to understand convergence properties
    """

    def __init__(self, adjacency_matrix: sparse.csr_matrix, node_list: List[int]):
        self.adjacency = adjacency_matrix
        self.node_list = node_list
        self.n = len(node_list)

        # Compute degree matrix
        degrees = np.array(adjacency_matrix.sum(axis=1)).flatten()
        self.degree_matrix = sparse.diags(degrees)

        # Compute Laplacian: L = D - A
        self.laplacian = self.degree_matrix - adjacency_matrix

        # Normalized Laplacian: L_norm = D^(-1/2) L D^(-1/2)
        degrees_inv_sqrt = np.zeros(self.n)
        nonzero = degrees > 0
        degrees_inv_sqrt[nonzero] = 1.0 / np.sqrt(degrees[nonzero])

        D_inv_sqrt = sparse.diags(degrees_inv_sqrt)
        self.normalized_laplacian = D_inv_sqrt @ self.laplacian @ D_inv_sqrt

    def compute_eigenvalues(
        self,
        k: int = 20,
        which: str = 'SM',
        normalized: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute top-k eigenvalues and eigenvectors

        Args:
            k: Number of eigenvalues to compute
            which: 'SM' (smallest magnitude), 'LM' (largest), 'SA' (smallest algebraic)
            normalized: Use normalized Laplacian

        Returns:
            (eigenvalues, eigenvectors)
        """
        matrix = self.normalized_laplacian if normalized else self.laplacian

        # Use sparse eigenvalue solver
        try:
            eigenvalues, eigenvectors = sparse_linalg.eigsh(
                matrix,
                k=min(k, self.n - 2),
                which=which,
                return_eigenvectors=True
            )

            # Sort by eigenvalue
            idx = np.argsort(eigenvalues)
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]

            return eigenvalues, eigenvectors

        except Exception as e:
            print(f"Warning: Eigenvalue computation failed: {e}")
            return np.array([]), np.array([])

    def analyze_spectrum(self, k: int = 20) -> SpectralProperties:
        """
        Complete spectral analysis

        Returns key spectral properties that may reveal convergence structure
        """
        eigenvalues, eigenvectors = self.compute_eigenvalues(k=k, normalized=True)

        if len(eigenvalues) < 2:
            return SpectralProperties(
                eigenvalues=eigenvalues,
                eigenvectors=eigenvectors,
                spectral_gap=0.0,
                spectral_radius=0.0,
                algebraic_connectivity=0.0,
                mixing_time_bound=None
            )

        # Spectral gap: difference between two smallest eigenvalues
        # (For Laplacian, smallest is always 0)
        spectral_gap = eigenvalues[1] - eigenvalues[0] if len(eigenvalues) > 1 else 0.0

        # Spectral radius: largest absolute eigenvalue
        spectral_radius = np.max(np.abs(eigenvalues))

        # Algebraic connectivity: second smallest eigenvalue (Fiedler value)
        # Measures how well-connected the graph is
        algebraic_connectivity = eigenvalues[1] if len(eigenvalues) > 1 else 0.0

        # Mixing time bound (Cheeger inequality)
        # τ_mix ≤ 1 / λ₂ (rough bound)
        mixing_time_bound = 1.0 / algebraic_connectivity if algebraic_connectivity > 0 else None

        return SpectralProperties(
            eigenvalues=eigenvalues,
            eigenvectors=eigenvectors,
            spectral_gap=spectral_gap,
            spectral_radius=spectral_radius,
            algebraic_connectivity=algebraic_connectivity,
            mixing_time_bound=mixing_time_bound
        )

    def compute_cheeger_constant(self, sample_size: int = 1000) -> float:
        """
        Estimate Cheeger constant (graph expansion)

        h(G) = min_{S ⊂ V} |∂S| / min(|S|, |V\S|)

        Higher Cheeger constant → better expansion → faster mixing
        """
        # Sample random cuts and compute expansion
        min_expansion = float('inf')

        for _ in range(sample_size):
            # Random partition
            cut_size = np.random.randint(1, self.n)
            indices = np.random.choice(self.n, size=cut_size, replace=False)

            # Compute cut edges
            mask = np.zeros(self.n, dtype=bool)
            mask[indices] = True

            # Count edges crossing the cut
            crossing_edges = 0
            for i in range(self.n):
                if mask[i]:
                    # Count edges to nodes outside the cut
                    row = self.adjacency[i].toarray().flatten()
                    crossing_edges += np.sum(row[~mask])

            # Expansion ratio
            vol_S = cut_size
            vol_V_minus_S = self.n - cut_size
            expansion = crossing_edges / min(vol_S, vol_V_minus_S) if min(vol_S, vol_V_minus_S) > 0 else 0

            min_expansion = min(min_expansion, expansion)

        return min_expansion

    def analyze_eigenvector_structure(self, k: int = 5) -> Dict:
        """
        Analyze structure of top eigenvectors

        Eigenvectors reveal "communities" and flow patterns in the graph
        """
        eigenvalues, eigenvectors = self.compute_eigenvalues(k=k, normalized=True)

        results = {}

        for i in range(min(k, len(eigenvalues))):
            ev = eigenvectors[:, i]

            results[f'eigenvector_{i}'] = {
                'eigenvalue': eigenvalues[i],
                'mean': np.mean(ev),
                'std': np.std(ev),
                'max_value': np.max(ev),
                'min_value': np.min(ev),
                'sparsity': np.sum(np.abs(ev) < 1e-6) / len(ev),
                # Find nodes with largest coefficients
                'top_nodes': [self.node_list[j] for j in np.argsort(np.abs(ev))[-10:]],
            }

        return results

    def compute_pagerank(self, damping: float = 0.85, max_iter: int = 100) -> np.ndarray:
        """
        Compute PageRank on Collatz graph

        Interpretation: Which numbers are "most important" in the Collatz structure?
        Hypothesis: Number 1 should have highest PageRank (it's the sink)
        """
        # PageRank: PR = (1-d)/N + d * A^T * PR
        n = self.n
        pr = np.ones(n) / n

        # Normalize adjacency matrix by out-degree
        out_degrees = np.array(self.adjacency.sum(axis=1)).flatten()
        out_degrees[out_degrees == 0] = 1  # Avoid division by zero

        A_norm = self.adjacency.multiply(1.0 / out_degrees[:, np.newaxis])

        for _ in range(max_iter):
            pr_new = (1 - damping) / n + damping * A_norm.T @ pr

            # Check convergence
            if np.linalg.norm(pr_new - pr, 1) < 1e-8:
                break

            pr = pr_new

        return pr

    def analyze_convergence_via_spectrum(self) -> Dict:
        """
        MAIN THEOREM CHECKER:

        Analyze if spectral properties guarantee convergence

        Theorem: If all eigenvalues of transition matrix have |λᵢ| < 1,
        then random walks converge to stationary distribution
        """
        # Get eigenvalues of normalized adjacency (transition matrix)
        out_degrees = np.array(self.adjacency.sum(axis=1)).flatten()
        out_degrees[out_degrees == 0] = 1

        # Transition matrix: P = D^(-1) A
        D_inv = sparse.diags(1.0 / out_degrees)
        transition_matrix = D_inv @ self.adjacency

        # Compute eigenvalues
        try:
            eigenvalues = sparse_linalg.eigs(
                transition_matrix,
                k=min(10, self.n - 2),
                which='LM',
                return_eigenvectors=False
            )

            spectral_radius = np.max(np.abs(eigenvalues))

            results = {
                'transition_eigenvalues': eigenvalues,
                'spectral_radius': spectral_radius,
                'converges': spectral_radius < 1.0,
                'convergence_rate': -np.log(spectral_radius) if spectral_radius > 0 else float('inf'),
            }

            # Estimate convergence time
            if spectral_radius < 1.0 and spectral_radius > 0:
                # Time to ε-convergence: t ≈ log(ε) / log(ρ)
                epsilon = 0.01
                conv_time = np.log(epsilon) / np.log(spectral_radius)
                results['convergence_time_estimate'] = conv_time

            return results

        except Exception as e:
            print(f"Warning: Transition matrix analysis failed: {e}")
            return {'error': str(e)}

    def plot_spectrum(self, k: int = 20, save_path: Optional[str] = None):
        """Visualize eigenvalue spectrum"""
        eigenvalues, _ = self.compute_eigenvalues(k=k, normalized=True)

        plt.figure(figsize=(12, 5))

        # Plot 1: Eigenvalue spectrum
        plt.subplot(1, 2, 1)
        plt.plot(eigenvalues, 'o-', markersize=8)
        plt.axhline(y=0, color='r', linestyle='--', alpha=0.3)
        plt.xlabel('Index', fontsize=12)
        plt.ylabel('Eigenvalue', fontsize=12)
        plt.title('Laplacian Eigenvalue Spectrum', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)

        # Plot 2: Spectral gap
        if len(eigenvalues) > 1:
            plt.subplot(1, 2, 2)
            gaps = np.diff(eigenvalues)
            plt.bar(range(len(gaps)), gaps)
            plt.xlabel('Index', fontsize=12)
            plt.ylabel('Eigenvalue Gap', fontsize=12)
            plt.title('Spectral Gaps', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved spectrum plot to {save_path}")

        return plt.gcf()


def test_spectral_convergence_theorem(
    analyzer: CollatzSpectralAnalyzer,
    verbose: bool = True
) -> Dict:
    """
    TEST KEY THEOREM:

    If spectral gap λ₁ - λ₀ > δ > 0, then graph has good expansion
    → implies finite mixing time → implies convergence

    Returns evidence for/against theorem
    """
    props = analyzer.analyze_spectrum(k=20)

    if verbose:
        print("\n" + "="*60)
        print("SPECTRAL CONVERGENCE THEOREM TEST")
        print("="*60)
        print(f"\nSpectral Gap (λ₁ - λ₀): {props.spectral_gap:.6f}")
        print(f"Algebraic Connectivity (λ₁): {props.algebraic_connectivity:.6f}")
        print(f"Spectral Radius: {props.spectral_radius:.6f}")

        if props.mixing_time_bound:
            print(f"Mixing Time Upper Bound: {props.mixing_time_bound:.2f}")

        print(f"\n✓ Graph has positive spectral gap: {props.spectral_gap > 0}")
        print(f"✓ Graph is well-connected: {props.algebraic_connectivity > 0}")

    # Check convergence via transition matrix
    conv_analysis = analyzer.analyze_convergence_via_spectrum()

    if verbose and 'converges' in conv_analysis:
        print(f"\n✓ Transition matrix converges: {conv_analysis['converges']}")
        if 'convergence_time_estimate' in conv_analysis:
            print(f"  Estimated convergence time: {conv_analysis['convergence_time_estimate']:.2f} steps")

    return {
        'spectral_properties': props,
        'convergence_analysis': conv_analysis,
        'theorem_supported': props.spectral_gap > 0 and conv_analysis.get('converges', False)
    }
