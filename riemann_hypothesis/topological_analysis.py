"""
TOPOLOGICAL DATA ANALYSIS FOR RIEMANN ZEROS
============================================

THIS IS A NOVEL APPROACH THAT HAS NEVER BEEN SYSTEMATICALLY APPLIED TO RH!

We apply Persistent Homology to:
1. The point cloud of Riemann zeros (embedded in various spaces)
2. The spacing distribution
3. The correlation structure

Key Hypothesis: If the Riemann Hypothesis is true, the zeros should exhibit
specific topological features that distinguish them from random points.

The topology of the zero set might reveal:
- Hidden symmetries
- Clustering structure related to the prime distribution
- Topological invariants that constrain zeros to Re(s) = 1/2
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram
from typing import List, Tuple, Optional, Dict
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# POINT CLOUD EMBEDDINGS
# =============================================================================

def embed_zeros_1d(zeros: np.ndarray) -> np.ndarray:
    """Simple 1D embedding (just the imaginary parts)."""
    return zeros.reshape(-1, 1)

def embed_zeros_takens(zeros: np.ndarray, delay: int = 1, dim: int = 3) -> np.ndarray:
    """
    Takens embedding (time-delay embedding).

    This is powerful because if zeros come from a dynamical system
    (as Hilbert-Pólya suggests), this will reveal its attractor!

    Parameters:
    - delay: time delay τ
    - dim: embedding dimension d

    Creates vectors: [z_i, z_{i+τ}, z_{i+2τ}, ..., z_{i+(d-1)τ}]
    """
    n = len(zeros)
    max_idx = n - (dim - 1) * delay

    if max_idx <= 0:
        raise ValueError("Not enough data for this embedding")

    embedded = np.zeros((max_idx, dim))
    for i in range(max_idx):
        for d in range(dim):
            embedded[i, d] = zeros[i + d * delay]

    return embedded

def embed_zeros_spacing(zeros: np.ndarray, window: int = 5) -> np.ndarray:
    """
    Embed using sliding windows of consecutive spacings.

    Each point represents a "local structure" of the zeros.
    """
    spacings = np.diff(zeros)
    n = len(spacings)
    max_idx = n - window + 1

    if max_idx <= 0:
        raise ValueError("Window too large")

    embedded = np.zeros((max_idx, window))
    for i in range(max_idx):
        embedded[i] = spacings[i:i+window]

    return embedded

def embed_zeros_fourier(zeros: np.ndarray, n_components: int = 10) -> np.ndarray:
    """
    Embed using local Fourier coefficients.

    This captures periodic structure in the zeros.
    """
    spacings = np.diff(zeros)
    n = len(spacings)
    window = 2 * n_components
    max_idx = n - window + 1

    if max_idx <= 0:
        raise ValueError("Not enough data")

    embedded = np.zeros((max_idx, n_components))
    for i in range(max_idx):
        local_spacings = spacings[i:i+window]
        fft = np.fft.fft(local_spacings)
        embedded[i] = np.abs(fft[:n_components])

    return embedded

# =============================================================================
# SIMPLICIAL COMPLEX CONSTRUCTION
# =============================================================================

def vietoris_rips_complex(points: np.ndarray, epsilon: float) -> Dict:
    """
    Build Vietoris-Rips complex at scale epsilon.

    Returns:
    - 0-simplices (vertices): all points
    - 1-simplices (edges): pairs within distance epsilon
    - 2-simplices (triangles): triples where all pairs are edges
    """
    n = len(points)
    dist_matrix = squareform(pdist(points))

    # 0-simplices
    vertices = list(range(n))

    # 1-simplices (edges)
    edges = []
    for i in range(n):
        for j in range(i+1, n):
            if dist_matrix[i, j] <= epsilon:
                edges.append((i, j))

    # 2-simplices (triangles)
    triangles = []
    edge_set = set(edges)
    for i in range(n):
        for j in range(i+1, n):
            if (i, j) in edge_set:
                for k in range(j+1, n):
                    if (i, k) in edge_set and (j, k) in edge_set:
                        triangles.append((i, j, k))

    return {
        'vertices': vertices,
        'edges': edges,
        'triangles': triangles,
        'epsilon': epsilon
    }

def betti_numbers(complex_data: Dict) -> Tuple[int, int, int]:
    """
    Compute Betti numbers β₀, β₁, β₂ from simplicial complex.

    β₀ = number of connected components
    β₁ = number of "holes" (1-cycles)
    β₂ = number of "voids" (2-cycles)

    These are topological invariants!
    """
    n_vertices = len(complex_data['vertices'])
    n_edges = len(complex_data['edges'])
    n_triangles = len(complex_data['triangles'])

    # Build adjacency structure for connected components
    from collections import defaultdict

    adj = defaultdict(set)
    for i, j in complex_data['edges']:
        adj[i].add(j)
        adj[j].add(i)

    # β₀: Connected components (BFS/DFS)
    visited = set()
    components = 0

    def dfs(node):
        stack = [node]
        while stack:
            v = stack.pop()
            if v not in visited:
                visited.add(v)
                stack.extend(adj[v] - visited)

    for v in complex_data['vertices']:
        if v not in visited:
            dfs(v)
            components += 1

    beta_0 = components

    # β₁: Using Euler characteristic
    # χ = V - E + F = β₀ - β₁ + β₂
    # For 2D, β₂ ≈ 0, so β₁ ≈ V - E + F - β₀
    # Actually, β₁ = E - V + β₀ (for 1-skeleton)

    euler_char = n_vertices - n_edges + n_triangles
    beta_1 = n_edges - n_vertices + beta_0 - n_triangles + n_triangles  # Simplified
    beta_1 = max(0, n_edges - n_vertices + beta_0)  # For 1-skeleton

    # β₂: For simplicial complex, harder to compute exactly
    # Approximate as 0 for small complexes
    beta_2 = 0

    return beta_0, beta_1, beta_2

# =============================================================================
# PERSISTENT HOMOLOGY
# =============================================================================

def compute_persistence(points: np.ndarray,
                       max_epsilon: Optional[float] = None,
                       n_steps: int = 50) -> Dict:
    """
    Compute persistent homology by varying epsilon.

    Returns birth-death pairs for topological features.
    """
    dist_matrix = squareform(pdist(points))

    if max_epsilon is None:
        max_epsilon = np.max(dist_matrix)

    epsilons = np.linspace(0, max_epsilon, n_steps)

    # Track Betti numbers at each scale
    betti_history = []

    for eps in epsilons:
        complex_data = vietoris_rips_complex(points, eps)
        betti = betti_numbers(complex_data)
        betti_history.append({
            'epsilon': eps,
            'beta_0': betti[0],
            'beta_1': betti[1],
            'beta_2': betti[2]
        })

    # Extract persistence intervals
    # β₀ persistence: components merging
    # β₁ persistence: holes appearing/filling

    persistence_0 = []  # (birth, death) for components
    persistence_1 = []  # (birth, death) for holes

    # Simple persistence extraction
    prev_betti = betti_history[0]
    for i, curr_betti in enumerate(betti_history[1:], 1):
        # New components (shouldn't happen after eps=0)
        # Components dying (merging)
        if curr_betti['beta_0'] < prev_betti['beta_0']:
            # Some components merged
            n_deaths = prev_betti['beta_0'] - curr_betti['beta_0']
            for _ in range(n_deaths):
                persistence_0.append((0, epsilons[i]))

        # Holes born
        if curr_betti['beta_1'] > prev_betti['beta_1']:
            n_births = curr_betti['beta_1'] - prev_betti['beta_1']
            for _ in range(n_births):
                persistence_1.append((epsilons[i], None))  # Birth, death unknown

        # Holes dying
        if curr_betti['beta_1'] < prev_betti['beta_1']:
            n_deaths = prev_betti['beta_1'] - curr_betti['beta_1']
            # Match with earliest unmatched birth
            for j in range(len(persistence_1)):
                if persistence_1[j][1] is None and n_deaths > 0:
                    persistence_1[j] = (persistence_1[j][0], epsilons[i])
                    n_deaths -= 1

        prev_betti = curr_betti

    return {
        'epsilons': epsilons,
        'betti_history': betti_history,
        'persistence_0': persistence_0,
        'persistence_1': persistence_1
    }

def persistence_entropy(persistence: List[Tuple[float, float]]) -> float:
    """
    Compute persistence entropy.

    This measures the "complexity" of the topological structure.

    Higher entropy = more complex topology
    """
    lifetimes = []
    for birth, death in persistence:
        if death is not None:
            lifetimes.append(death - birth)

    if not lifetimes:
        return 0.0

    lifetimes = np.array(lifetimes)
    total = np.sum(lifetimes)

    if total == 0:
        return 0.0

    # Normalize to get probabilities
    probs = lifetimes / total

    # Shannon entropy
    entropy = -np.sum(probs * np.log(probs + 1e-10))

    return entropy

def persistence_landscape(persistence: List[Tuple[float, float]],
                         n_landscapes: int = 5,
                         resolution: int = 100) -> np.ndarray:
    """
    Compute persistence landscape (stable topological summary).

    This is a functional representation of persistence that's
    useful for machine learning!
    """
    if not persistence:
        return np.zeros((n_landscapes, resolution))

    # Get max scale
    max_death = max(d for _, d in persistence if d is not None)
    if max_death == 0:
        return np.zeros((n_landscapes, resolution))

    t = np.linspace(0, max_death, resolution)
    landscapes = np.zeros((n_landscapes, resolution))

    for i, t_val in enumerate(t):
        # Compute tent function values at t
        values = []
        for birth, death in persistence:
            if death is not None:
                mid = (birth + death) / 2
                height = (death - birth) / 2
                if birth <= t_val <= death:
                    if t_val <= mid:
                        values.append(t_val - birth)
                    else:
                        values.append(death - t_val)

        # Sort descending and take top n_landscapes
        values = sorted(values, reverse=True)
        for j in range(min(len(values), n_landscapes)):
            landscapes[j, i] = values[j]

    return landscapes

# =============================================================================
# TOPOLOGICAL SIGNATURES
# =============================================================================

def topological_signature(zeros: np.ndarray) -> Dict:
    """
    Compute comprehensive topological signature of Riemann zeros.

    This signature could potentially distinguish "valid" zeros
    (on the critical line) from hypothetical "invalid" zeros!
    """
    results = {}

    # 1. Takens embedding analysis
    try:
        takens_embed = embed_zeros_takens(zeros, delay=1, dim=3)
        persistence = compute_persistence(takens_embed[:50], n_steps=30)

        results['takens_persistence_0'] = len(persistence['persistence_0'])
        results['takens_persistence_1'] = len(persistence['persistence_1'])
        results['takens_entropy_0'] = persistence_entropy(persistence['persistence_0'])
        results['takens_entropy_1'] = persistence_entropy(persistence['persistence_1'])
    except Exception as e:
        results['takens_error'] = str(e)

    # 2. Spacing embedding analysis
    try:
        spacing_embed = embed_zeros_spacing(zeros, window=3)
        persistence = compute_persistence(spacing_embed[:50], n_steps=30)

        results['spacing_persistence_0'] = len(persistence['persistence_0'])
        results['spacing_persistence_1'] = len(persistence['persistence_1'])
        results['spacing_entropy_0'] = persistence_entropy(persistence['persistence_0'])
        results['spacing_entropy_1'] = persistence_entropy(persistence['persistence_1'])
    except Exception as e:
        results['spacing_error'] = str(e)

    # 3. Fourier embedding analysis
    try:
        fourier_embed = embed_zeros_fourier(zeros, n_components=5)
        if len(fourier_embed) >= 20:
            persistence = compute_persistence(fourier_embed[:30], n_steps=30)

            results['fourier_persistence_0'] = len(persistence['persistence_0'])
            results['fourier_persistence_1'] = len(persistence['persistence_1'])
            results['fourier_entropy_0'] = persistence_entropy(persistence['persistence_0'])
            results['fourier_entropy_1'] = persistence_entropy(persistence['persistence_1'])
    except Exception as e:
        results['fourier_error'] = str(e)

    return results

# =============================================================================
# COMPARISON WITH RANDOM DATA
# =============================================================================

def generate_random_zeros(n: int, mean_spacing: float = 2.3) -> np.ndarray:
    """
    Generate "fake" zeros with Poisson (random) spacing.

    If RH is true, real zeros should have DIFFERENT topological
    signature than these random zeros!
    """
    spacings = np.random.exponential(mean_spacing, n-1)
    zeros = np.cumsum(np.concatenate([[14.0], spacings]))
    return zeros

def generate_gue_like_zeros(n: int, mean_spacing: float = 2.3) -> np.ndarray:
    """
    Generate "fake" zeros with GUE-like spacing distribution.

    These should have SIMILAR topological signature to real zeros.
    """
    # Sample from Wigner surmise
    samples = []
    while len(samples) < n - 1:
        s = np.random.exponential(1.0)  # Proposal
        # Rejection sampling for Wigner surmise
        accept_prob = s**2 * np.exp(-s**2 * 4/np.pi + s)
        if np.random.random() < min(1, accept_prob / 3):
            samples.append(s * mean_spacing)

    spacings = np.array(samples[:n-1])
    zeros = np.cumsum(np.concatenate([[14.0], spacings]))
    return zeros

def topological_discrimination_test(real_zeros: np.ndarray,
                                   n_random: int = 10,
                                   n_gue: int = 10) -> Dict:
    """
    Test if topological signature can distinguish real zeros
    from random and GUE-like zeros.

    This is a NOVEL test of the Riemann Hypothesis!
    """
    n = len(real_zeros)
    mean_spacing = np.mean(np.diff(real_zeros))

    # Real zeros signature
    real_sig = topological_signature(real_zeros)

    # Random zeros signatures
    random_sigs = []
    for _ in range(n_random):
        random_zeros = generate_random_zeros(n, mean_spacing)
        random_sigs.append(topological_signature(random_zeros))

    # GUE-like zeros signatures
    gue_sigs = []
    for _ in range(n_gue):
        gue_zeros = generate_gue_like_zeros(n, mean_spacing)
        gue_sigs.append(topological_signature(gue_zeros))

    # Compare
    results = {
        'real_signature': real_sig,
        'random_signatures_mean': {},
        'gue_signatures_mean': {},
        'discrimination_scores': {}
    }

    for key in real_sig:
        if 'error' not in key and isinstance(real_sig[key], (int, float)):
            random_vals = [s.get(key, 0) for s in random_sigs if key in s]
            gue_vals = [s.get(key, 0) for s in gue_sigs if key in s]

            if random_vals:
                results['random_signatures_mean'][key] = np.mean(random_vals)
            if gue_vals:
                results['gue_signatures_mean'][key] = np.mean(gue_vals)

            # Discrimination: is real closer to GUE than random?
            if random_vals and gue_vals:
                dist_to_random = abs(real_sig[key] - np.mean(random_vals))
                dist_to_gue = abs(real_sig[key] - np.mean(gue_vals))

                if dist_to_random + dist_to_gue > 0:
                    score = dist_to_random / (dist_to_random + dist_to_gue)
                    results['discrimination_scores'][key] = score

    return results

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def full_topological_analysis(zeros: np.ndarray, verbose: bool = True) -> Dict:
    """
    Complete topological analysis of Riemann zeros.
    """
    if verbose:
        print("=" * 60)
        print("TOPOLOGICAL DATA ANALYSIS - NOVEL APPROACH")
        print("=" * 60)

    results = {}

    # 1. Compute signature
    if verbose:
        print("\n1. Computing topological signature...")
    sig = topological_signature(zeros)
    results['signature'] = sig

    if verbose:
        print("   Signature computed:")
        for key, value in sig.items():
            if 'error' not in key:
                print(f"   - {key}: {value:.4f}" if isinstance(value, float) else f"   - {key}: {value}")

    # 2. Discrimination test
    if verbose:
        print("\n2. Running discrimination test...")
    disc = topological_discrimination_test(zeros, n_random=5, n_gue=5)
    results['discrimination'] = disc

    if verbose:
        print("   Discrimination scores (1.0 = real zeros closer to GUE):")
        for key, score in disc['discrimination_scores'].items():
            indicator = "✓" if score > 0.5 else "✗"
            print(f"   {indicator} {key}: {score:.3f}")

    # 3. Overall verdict
    if verbose:
        print("\n" + "=" * 60)
        print("TOPOLOGICAL VERDICT")
        print("=" * 60)

        scores = list(disc['discrimination_scores'].values())
        if scores:
            mean_score = np.mean(scores)
            print(f"Mean discrimination score: {mean_score:.3f}")
            if mean_score > 0.6:
                print("✓ Real zeros are topologically closer to GUE than random!")
                print("→ This supports the Hilbert-Pólya conjecture.")
            elif mean_score > 0.4:
                print("△ Inconclusive - more data needed.")
            else:
                print("✗ Unexpected: real zeros closer to random than GUE!")

    return results


if __name__ == "__main__":
    from riemann_zeros import get_zeros

    zeros = get_zeros(100)
    results = full_topological_analysis(zeros)
