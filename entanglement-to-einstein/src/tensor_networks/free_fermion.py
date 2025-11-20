"""
Free fermion CFT implementation with exact entanglement entropy.

For free fermions in 1D, the entanglement entropy can be computed exactly
using the correlation matrix method.
"""

import numpy as np
from typing import List, Tuple, Optional
import warnings


def create_free_fermion_ground_state_correlation_matrix(
    n_sites: int,
    boundary: str = 'open'
) -> np.ndarray:
    """
    Create correlation matrix for free fermion ground state.

    For the critical free fermion (CFT limit), we use the tight-binding
    Hamiltonian: H = -Σ_i (c†_i c_{i+1} + h.c.)

    Args:
        n_sites: Number of lattice sites
        boundary: 'open' or 'periodic'

    Returns:
        Correlation matrix C_ij = ⟨c†_i c_j⟩
    """
    # Build hopping matrix
    H = np.zeros((n_sites, n_sites))

    for i in range(n_sites - 1):
        H[i, i + 1] = -1.0
        H[i + 1, i] = -1.0

    if boundary == 'periodic':
        H[0, n_sites - 1] = -1.0
        H[n_sites - 1, 0] = -1.0

    # Diagonalize
    eigenvalues, eigenvectors = np.linalg.eigh(H)

    # Fill half the states (half filling)
    n_filled = n_sites // 2

    # Correlation matrix from filled states
    filled_states = eigenvectors[:, :n_filled]
    C = filled_states @ filled_states.T

    return C


def compute_entanglement_entropy_free_fermion(
    C: np.ndarray,
    subsystem: List[int]
) -> float:
    """
    Compute entanglement entropy for free fermions.

    For free fermions, the entanglement entropy is:
    S = -Tr[C_A log(C_A) + (1 - C_A) log(1 - C_A)]

    where C_A is the correlation matrix restricted to subsystem A.

    Args:
        C: Full correlation matrix
        subsystem: List of site indices in subsystem A

    Returns:
        Entanglement entropy
    """
    # Extract submatrix
    C_A = C[np.ix_(subsystem, subsystem)]

    # Compute eigenvalues
    try:
        eigenvalues = np.linalg.eigvalsh(C_A)
    except np.linalg.LinAlgError:
        warnings.warn("Failed to compute eigenvalues")
        return 0.0

    # Clip to (0, 1) to avoid log(0)
    eigenvalues = np.clip(eigenvalues, 1e-14, 1 - 1e-14)

    # Entropy formula
    entropy = -np.sum(
        eigenvalues * np.log(eigenvalues) +
        (1 - eigenvalues) * np.log(1 - eigenvalues)
    )

    return entropy


def compute_area_law_coefficient_free_fermion(
    n_sites: int,
    max_subsystem_size: Optional[int] = None,
    boundary: str = 'open'
) -> Tuple[List[int], List[float], float]:
    """
    Compute entanglement entropy for various subsystem sizes
    and extract area law coefficient.

    For 1D free fermion CFT, the theoretical result is:
    S(L) = (c/3) * log(L) + const
    where c = 1/2 for a single Majorana fermion.

    Args:
        n_sites: Total number of sites
        max_subsystem_size: Maximum subsystem size to check
        boundary: Boundary conditions

    Returns:
        (subsystem_sizes, entropies, fitted_coefficient)
    """
    if max_subsystem_size is None:
        max_subsystem_size = n_sites // 2

    # Create correlation matrix
    C = create_free_fermion_ground_state_correlation_matrix(n_sites, boundary)

    sizes = []
    entropies = []

    # Compute for various contiguous subsystems
    for L in range(2, min(max_subsystem_size, n_sites // 2) + 1):
        subsystem = list(range(L))
        S = compute_entanglement_entropy_free_fermion(C, subsystem)

        sizes.append(L)
        entropies.append(S)

    # Fit to c/3 * log(L)
    sizes_array = np.array(sizes)
    entropies_array = np.array(entropies)

    log_sizes = np.log(sizes_array)

    # Linear regression
    from scipy.stats import linregress
    result = linregress(log_sizes, entropies_array)

    fitted_coefficient = result.slope

    return sizes, entropies, fitted_coefficient


def theoretical_area_law_coefficient() -> float:
    """
    Return theoretical c/3 value for free fermion.

    For a single Dirac fermion (or equivalently, a single
    real fermion = Majorana fermion), c = 1/2.

    Therefore c/3 = 1/6 ≈ 0.167

    Returns:
        Theoretical coefficient
    """
    c = 0.5  # Central charge for free fermion
    return c / 3.0


def create_free_boson_correlation_matrix(
    n_sites: int,
    boundary: str = 'open'
) -> np.ndarray:
    """
    Create correlation matrix for free boson CFT.

    For free boson, c = 1, so c/3 = 1/3 ≈ 0.333

    Args:
        n_sites: Number of sites
        boundary: Boundary conditions

    Returns:
        Correlation matrix
    """
    # Build hopping matrix (harmonic oscillator chain)
    H = np.zeros((n_sites, n_sites))

    # Hopping + on-site potential
    for i in range(n_sites):
        H[i, i] = 2.0  # On-site

    for i in range(n_sites - 1):
        H[i, i + 1] = -1.0
        H[i + 1, i] = -1.0

    if boundary == 'periodic':
        H[0, n_sites - 1] = -1.0
        H[n_sites - 1, 0] = -1.0

    # For bosons, correlation matrix construction is different
    # This is simplified; full implementation would include proper boson coherent state

    # Diagonalize
    eigenvalues, eigenvectors = np.linalg.eigh(H)

    # Correlation matrix (thermal state approximation)
    # C_ij = ⟨a†_i a_j⟩
    beta = 1.0  # Inverse temperature (0 = infinite temperature, ∞ = ground state)

    # Simplified: use similar structure to fermions
    n_filled = n_sites // 2
    filled_states = eigenvectors[:, :n_filled]
    C = filled_states @ filled_states.T

    return C


class FreeFermionCFT:
    """
    Free fermion conformal field theory in 1D.

    Provides exact ground state and entanglement properties.
    """

    def __init__(
        self,
        n_sites: int,
        boundary: str = 'open',
        central_charge: float = 0.5
    ):
        """
        Initialize free fermion CFT.

        Args:
            n_sites: Number of lattice sites
            boundary: Boundary conditions ('open' or 'periodic')
            central_charge: Central charge (0.5 for Majorana)
        """
        self.n_sites = n_sites
        self.boundary = boundary
        self.central_charge = central_charge

        # Compute correlation matrix
        self.C = create_free_fermion_ground_state_correlation_matrix(
            n_sites, boundary
        )

    def entanglement_entropy(self, subsystem: List[int]) -> float:
        """
        Compute entanglement entropy for subsystem.

        Args:
            subsystem: List of site indices

        Returns:
            Entanglement entropy S(A)
        """
        return compute_entanglement_entropy_free_fermion(self.C, subsystem)

    def area_law_fit(
        self,
        max_size: Optional[int] = None
    ) -> dict:
        """
        Fit area law and return results.

        Returns:
            Dictionary with fit results
        """
        sizes, entropies, coefficient = compute_area_law_coefficient_free_fermion(
            self.n_sites,
            max_size,
            self.boundary
        )

        theoretical = self.central_charge / 3.0

        return {
            'sizes': sizes,
            'entropies': entropies,
            'fitted_coefficient': coefficient,
            'theoretical_coefficient': theoretical,
            'relative_error': abs(coefficient - theoretical) / theoretical
        }

    def mutual_information(
        self,
        subsystem_A: List[int],
        subsystem_B: List[int]
    ) -> float:
        """
        Compute mutual information I(A:B).

        Args:
            subsystem_A: First subsystem
            subsystem_B: Second subsystem

        Returns:
            Mutual information
        """
        S_A = self.entanglement_entropy(subsystem_A)
        S_B = self.entanglement_entropy(subsystem_B)

        # Combined subsystem
        subsystem_AB = list(set(subsystem_A + subsystem_B))
        S_AB = self.entanglement_entropy(subsystem_AB)

        I_AB = S_A + S_B - S_AB

        return max(0, I_AB)  # Enforce non-negativity


def verify_area_law_analytically(
    n_sites: int = 128,
    boundary: str = 'open'
) -> dict:
    """
    Verify area law using exact free fermion solution.

    This serves as a benchmark for MERA implementation.

    Args:
        n_sites: Number of sites
        boundary: Boundary conditions

    Returns:
        Dictionary with verification results
    """
    cft = FreeFermionCFT(n_sites, boundary)
    results = cft.area_law_fit()

    # Check if within 5% of theoretical
    is_valid = results['relative_error'] < 0.05

    print(f"{'='*60}")
    print(f"Free Fermion Area Law Verification")
    print(f"{'='*60}")
    print(f"Sites: {n_sites}")
    print(f"Boundary: {boundary}")
    print(f"Central charge: {cft.central_charge}")
    print(f"Theoretical c/3: {results['theoretical_coefficient']:.6f}")
    print(f"Fitted c/3: {results['fitted_coefficient']:.6f}")
    print(f"Relative error: {results['relative_error']*100:.2f}%")
    print(f"Status: {'✓ PASS' if is_valid else '✗ FAIL'}")
    print(f"{'='*60}\n")

    return results
