"""
Metric Extraction from Entanglement
====================================

Extract geometric metric tensor from entanglement entropy structure.

Methods:
1. Kinematic space (from mutual information)
2. Modular Hamiltonian perturbations
3. Multidimensional scaling (MDS)

References:
- Van Raamsdonk (2010): Building up spacetime with QE
- Czech et al. (2015): Kinematic space
"""

import numpy as np
from typing import Dict, Tuple, Optional, Callable
from scipy.optimize import minimize
from sklearn.manifold import MDS


def kinematic_metric(
    mutual_info_matrix: np.ndarray,
    entropies: np.ndarray,
    method: str = 'logarithmic'
) -> np.ndarray:
    """
    Extract metric from mutual information.

    d(A,B) = -log[I(A:B) / sqrt(S(A)*S(B))]

    Parameters
    ----------
    mutual_info_matrix : ndarray, shape (N, N)
        I(i:j) for all pairs
    entropies : ndarray, shape (N,)
        S(i) for all regions
    method : str
        'logarithmic' or 'linear'

    Returns
    -------
    ndarray, shape (N, N)
        Distance matrix
    """
    N = len(entropies)
    distance_matrix = np.zeros((N, N))

    for i in range(N):
        for j in range(i+1, N):
            I_ij = mutual_info_matrix[i, j]
            S_i = entropies[i]
            S_j = entropies[j]

            if method == 'logarithmic':
                # Normalized mutual information
                if I_ij > 0 and S_i > 0 and S_j > 0:
                    I_norm = I_ij / np.sqrt(S_i * S_j)
                    d_ij = -np.log(I_norm + 1e-10)
                else:
                    d_ij = np.inf

            elif method == 'linear':
                # Simple: d ~ 1/I
                if I_ij > 0:
                    d_ij = 1.0 / I_ij
                else:
                    d_ij = np.inf

            else:
                raise ValueError(f"Unknown method: {method}")

            distance_matrix[i, j] = d_ij
            distance_matrix[j, i] = d_ij

    return distance_matrix


def extract_metric(
    distance_matrix: np.ndarray,
    target_dimension: int = 3,
    method: str = 'mds'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract metric tensor from distance matrix.

    Uses multidimensional scaling (MDS) to embed points in target dimension,
    then computes local metric tensor.

    Parameters
    ----------
    distance_matrix : ndarray, shape (N, N)
        Pairwise distances
    target_dimension : int
        Dimension of target space (e.g., 3 for AdS3)
    method : str
        'mds', 'isomap', 'lle'

    Returns
    -------
    Tuple[ndarray, ndarray]
        (embedding, metric_tensors)
        embedding: shape (N, d) - coordinates
        metric_tensors: shape (N, d, d) - local metrics

    Examples
    --------
    >>> # Random distance matrix
    >>> N = 10
    >>> D = np.random.rand(N, N)
    >>> D = (D + D.T) / 2  # Symmetrize
    >>> np.fill_diagonal(D, 0)
    >>> embedding, metrics = extract_metric(D, target_dimension=2)
    """
    if method == 'mds':
        # Classical multidimensional scaling
        mds = MDS(
            n_components=target_dimension,
            dissimilarity='precomputed',
            random_state=42
        )
        embedding = mds.fit_transform(distance_matrix)

    else:
        raise NotImplementedError(f"Method {method} not implemented yet")

    # Compute local metric tensors at each point
    N, d = embedding.shape
    metric_tensors = np.zeros((N, d, d))

    for i in range(N):
        # Find nearest neighbors
        distances = distance_matrix[i]
        k = min(2 * d + 1, N - 1)  # Need at least d+1 neighbors
        neighbor_indices = np.argsort(distances)[1:k+1]  # Exclude self

        # Fit local quadratic form
        metric_tensors[i] = fit_local_metric(
            embedding[i],
            embedding[neighbor_indices],
            distance_matrix[i, neighbor_indices]
        )

    return embedding, metric_tensors


def fit_local_metric(
    center: np.ndarray,
    neighbors: np.ndarray,
    distances: np.ndarray
) -> np.ndarray:
    """
    Fit local metric tensor at a point.

    Fit quadratic form: d² ≈ (x - x₀)ᵀ g (x - x₀)

    Parameters
    ----------
    center : ndarray, shape (d,)
        Center point
    neighbors : ndarray, shape (k, d)
        Neighbor coordinates
    distances : ndarray, shape (k,)
        Distances to neighbors

    Returns
    -------
    ndarray, shape (d, d)
        Local metric tensor g_μν
    """
    d = len(center)

    # Displacement vectors
    dx = neighbors - center  # shape (k, d)

    # We want to fit: d² = dx^T g dx
    # This is a quadratic form, solve for g

    # For simplicity, assume Euclidean metric initially
    # TODO: Proper least-squares fit for g_μν

    # Compute empirical covariance-like metric
    metric = np.eye(d)

    if len(neighbors) >= d:
        # Use weighted covariance
        weights = 1.0 / (distances**2 + 1e-6)
        weights /= np.sum(weights)

        metric = np.zeros((d, d))
        for i in range(len(neighbors)):
            dx_i = dx[i]
            d_i = distances[i]
            # Approximate: g ~ (d²/||dx||²) * I
            if np.linalg.norm(dx_i) > 1e-10:
                scale = d_i**2 / np.dot(dx_i, dx_i)
                metric += weights[i] * scale * np.eye(d)

    return metric


def extract_ads_metric(
    embedding: np.ndarray,
    boundary_indices: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, float]:
    """
    Extract AdS metric from embedding.

    For AdS_d+1, metric should be:
    ds² = L²/z² (-dt² + dx² + dz²)

    Parameters
    ----------
    embedding : ndarray, shape (N, d+1)
        Embedding coordinates
    boundary_indices : ndarray, optional
        Indices of boundary points

    Returns
    -------
    Tuple[ndarray, float]
        (metric_tensor, AdS_radius_L)
    """
    # Placeholder: extract from hyperbolic structure
    d = embedding.shape[1]
    metric = np.diag([1.0] * d)  # Simplified

    # Fit AdS radius
    L = 1.0  # Placeholder

    return metric, L


def compute_modular_hamiltonian(
    rho_A: np.ndarray
) -> np.ndarray:
    """
    Compute modular Hamiltonian K_A = -log ρ_A.

    Parameters
    ----------
    rho_A : ndarray
        Reduced density matrix

    Returns
    -------
    ndarray
        Modular Hamiltonian
    """
    # Diagonalize ρ_A
    eigenvalues, eigenvectors = np.linalg.eigh(rho_A)

    # K = -log ρ = V (-log Λ) V†
    log_eigenvalues = np.zeros_like(eigenvalues)
    nonzero = eigenvalues > 1e-14
    log_eigenvalues[nonzero] = -np.log(eigenvalues[nonzero])

    K = eigenvectors @ np.diag(log_eigenvalues) @ eigenvectors.T.conj()

    return K
