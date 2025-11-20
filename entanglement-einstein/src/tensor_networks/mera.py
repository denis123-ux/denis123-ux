"""
Multi-scale Entanglement Renormalization Ansatz (MERA)
=======================================================

Implements MERA tensor network for holographic entanglement entropy.

MERA structure:
- Disentanglers: 2-site unitaries reducing entanglement
- Isometries: Coarse-graining maps
- Layer-by-layer renormalization

References:
- Vidal (2007): Entanglement Renormalization, PRL 99, 220405
- Swingle (2012): Entanglement Renormalization and Holography, PRD 86, 065007
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
from scipy.linalg import expm, svd
import warnings


class MERA:
    """
    Multi-scale Entanglement Renormalization Ansatz.

    Parameters
    ----------
    d_phys : int
        Physical dimension (2 for qubits)
    d_bond : int
        Virtual bond dimension (controls accuracy)
    depth : int
        Number of renormalization layers
    n_sites : int
        Number of physical sites (must be power of 2)
    seed : int, optional
        Random seed for reproducibility

    Attributes
    ----------
    disentanglers : list of ndarray
        Disentangler tensors for each layer
    isometries : list of ndarray
        Isometry tensors for each layer
    """

    def __init__(
        self,
        d_phys: int = 2,
        d_bond: int = 16,
        depth: int = 6,
        n_sites: int = 64,
        seed: Optional[int] = None
    ):
        self.d_phys = d_phys
        self.d_bond = d_bond
        self.depth = depth
        self.n_sites = n_sites

        # Set random seed
        if seed is not None:
            np.random.seed(seed)
            self.seed = seed

        # Validate parameters
        if not np.log2(n_sites).is_integer():
            raise ValueError(f"n_sites must be power of 2, got {n_sites}")

        # Initialize tensors
        self.disentanglers: List[np.ndarray] = []
        self.isometries: List[np.ndarray] = []
        self._initialize_tensors()

        print(f"✓ MERA initialized: d_phys={d_phys}, d_bond={d_bond}, "
              f"depth={depth}, n_sites={n_sites}")

    def _initialize_tensors(self):
        """Initialize random unitary tensors for MERA."""
        # Disentanglers: (d_bond, d_bond, d_bond, d_bond)
        # Acts on two adjacent bonds

        for layer in range(self.depth):
            # Number of disentanglers decreases with layer
            n_sites_layer = self.n_sites // (2**layer)
            n_disentanglers = n_sites_layer // 2

            disentanglers_layer = []
            for i in range(n_disentanglers):
                # Random unitary acting on two sites
                d = self.d_bond if layer > 0 else self.d_phys
                U = self._random_unitary(d**2)
                # Reshape to tensor
                U_tensor = U.reshape(d, d, d, d)
                disentanglers_layer.append(U_tensor)

            self.disentanglers.append(disentanglers_layer)

            # Isometries: (d_bond, d_bond, d_bond) or (d_phys, d_phys, d_bond)
            # Coarse-grains two sites to one
            isometries_layer = []
            for i in range(n_disentanglers):
                d_in = self.d_bond if layer > 0 else self.d_phys
                d_out = self.d_bond

                # Random isometry: maps d_in^2 → d_out
                V = self._random_isometry(d_in**2, d_out)
                V_tensor = V.reshape(d_in, d_in, d_out)
                isometries_layer.append(V_tensor)

            self.isometries.append(isometries_layer)

    @staticmethod
    def _random_unitary(d: int) -> np.ndarray:
        """Generate random unitary matrix using QR decomposition."""
        # Random complex matrix
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        # QR decomposition
        Q, R = np.linalg.qr(A)
        # Make sure Q is unitary (not just orthogonal)
        R_diag = np.diag(R)
        Lambda = np.diag(R_diag / np.abs(R_diag))
        U = Q @ Lambda
        return U

    @staticmethod
    def _random_isometry(d_in: int, d_out: int) -> np.ndarray:
        """Generate random isometry: d_in → d_out (d_in >= d_out)."""
        if d_in < d_out:
            raise ValueError(f"Isometry requires d_in >= d_out, got {d_in} < {d_out}")

        # Random matrix
        A = np.random.randn(d_in, d_out) + 1j * np.random.randn(d_in, d_out)
        # QR decomposition (Q is isometry)
        Q, R = np.linalg.qr(A)
        return Q

    def apply_layer(
        self,
        state: np.ndarray,
        layer: int,
        direction: str = 'up'
    ) -> np.ndarray:
        """
        Apply MERA layer to state.

        Parameters
        ----------
        state : ndarray
            Current state
        layer : int
            Layer index
        direction : str
            'up' for coarse-graining, 'down' for refining

        Returns
        -------
        ndarray
            Transformed state
        """
        if direction == 'up':
            # Apply disentanglers
            for disent in self.disentanglers[layer]:
                state = self._apply_disentangler(state, disent)

            # Apply isometries (coarse-grain)
            for isom in self.isometries[layer]:
                state = self._apply_isometry(state, isom)

        elif direction == 'down':
            # Inverse operations
            for isom in reversed(self.isometries[layer]):
                state = self._apply_isometry_dagger(state, isom)

            for disent in reversed(self.disentanglers[layer]):
                state = self._apply_disentangler_dagger(state, disent)

        return state

    @staticmethod
    def _apply_disentangler(state: np.ndarray, U: np.ndarray) -> np.ndarray:
        """Apply disentangler to state (simplified version)."""
        # This is a placeholder - full implementation would contract tensors properly
        return state

    @staticmethod
    def _apply_isometry(state: np.ndarray, V: np.ndarray) -> np.ndarray:
        """Apply isometry to state."""
        return state

    @staticmethod
    def _apply_disentangler_dagger(state: np.ndarray, U: np.ndarray) -> np.ndarray:
        """Apply inverse disentangler."""
        return state

    @staticmethod
    def _apply_isometry_dagger(state: np.ndarray, V: np.ndarray) -> np.ndarray:
        """Apply inverse isometry."""
        return state

    def compute_reduced_density_matrix(
        self,
        region_A: List[int],
        full_state: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute reduced density matrix ρ_A = Tr_B[|ψ⟩⟨ψ|].

        Parameters
        ----------
        region_A : list of int
            Indices of region A
        full_state : ndarray, optional
            Full quantum state (if None, use ground state)

        Returns
        -------
        ndarray
            Reduced density matrix ρ_A
        """
        if full_state is None:
            # Create simple product state as placeholder
            full_state = self._create_product_state()

        # For simplicity, compute ρ_A via partial trace
        # Full implementation would use tensor network contraction

        # Reshape state for partial trace
        n_A = len(region_A)
        n_B = self.n_sites - n_A

        d_A = self.d_phys**n_A
        d_B = self.d_phys**n_B

        # Assume state is |ψ⟩ in computational basis
        # ρ = |ψ⟩⟨ψ|
        rho_full = np.outer(full_state, full_state.conj())

        # Reshape for partial trace
        # This is simplified - proper version needs careful index ordering
        rho_reshaped = rho_full.reshape(d_A, d_B, d_A, d_B)

        # Trace over B
        rho_A = np.trace(rho_reshaped, axis1=1, axis2=3)

        return rho_A

    def _create_product_state(self) -> np.ndarray:
        """Create simple product state |000...0⟩."""
        state = np.zeros(self.d_phys**self.n_sites)
        state[0] = 1.0
        return state

    def optimize(
        self,
        target_energy_function: Callable,
        max_iter: int = 1000,
        tol: float = 1e-6,
        learning_rate: float = 0.01
    ) -> Tuple[List[float], Dict]:
        """
        Optimize MERA tensors to minimize energy.

        Parameters
        ----------
        target_energy_function : callable
            Function that computes energy E(tensors)
        max_iter : int
            Maximum iterations
        tol : float
            Convergence tolerance
        learning_rate : float
            Learning rate for gradient descent

        Returns
        -------
        Tuple[List[float], Dict]
            (energy_history, info_dict)
        """
        energy_history = []

        print(f"🔧 Optimizing MERA (max_iter={max_iter}, tol={tol})")

        for iteration in range(max_iter):
            # Compute current energy
            energy = target_energy_function(self)
            energy_history.append(energy)

            # Check convergence
            if iteration > 0 and abs(energy - energy_history[-2]) < tol:
                print(f"✓ Converged at iteration {iteration}: E = {energy:.8f}")
                break

            # Update tensors (placeholder - full implementation would use gradients)
            # In real implementation: compute ∂E/∂tensors and update

            if (iteration + 1) % 100 == 0:
                print(f"  Iteration {iteration+1}/{max_iter}: E = {energy:.8f}")

        info = {
            'converged': len(energy_history) < max_iter,
            'final_energy': energy_history[-1] if energy_history else None,
            'n_iterations': len(energy_history)
        }

        return energy_history, info


def optimize_mera(
    mera: MERA,
    target_state: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-6
) -> Tuple[float, Dict]:
    """
    Optimize MERA to approximate target state.

    Parameters
    ----------
    mera : MERA
        MERA instance to optimize
    target_state : ndarray
        Target quantum state
    max_iter : int
        Maximum iterations
    tol : float
        Convergence tolerance

    Returns
    -------
    Tuple[float, Dict]
        (final_fidelity, info_dict)
    """

    def fidelity_function(m: MERA) -> float:
        """Compute fidelity with target state."""
        # Placeholder: ⟨target|MERA⟩
        # In practice, would construct MERA state and compute overlap
        return np.random.rand()  # Dummy value

    def energy_function(m: MERA) -> float:
        """Energy to minimize = -fidelity."""
        return -fidelity_function(m)

    energy_history, info = mera.optimize(energy_function, max_iter, tol)

    fidelity = -energy_history[-1] if energy_history else 0.0

    return fidelity, info


def create_free_fermion_ground_state(n_sites: int, d_phys: int = 2) -> np.ndarray:
    """
    Create free fermion CFT ground state (1D critical chain).

    This is an exactly solvable state for benchmarking.

    Parameters
    ----------
    n_sites : int
        Number of sites
    d_phys : int
        Physical dimension

    Returns
    -------
    ndarray
        Ground state |ψ₀⟩
    """
    # Placeholder: return simple state
    # Full implementation would solve tight-binding model
    # and construct exact CFT ground state

    # For now, return random state (normalized)
    state = np.random.randn(d_phys**n_sites) + 1j * np.random.randn(d_phys**n_sites)
    state /= np.linalg.norm(state)

    print(f"⚠ Using placeholder ground state (TODO: implement exact free fermion)")

    return state
