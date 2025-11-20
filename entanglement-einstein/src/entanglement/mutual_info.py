"""
Mutual Information and Multipartite Entanglement
=================================================

Computes:
- I(A:B) = S(A) + S(B) - S(A∪B)  (mutual information)
- I₃(A:B:C) = tripartite information
- Entanglement negativity
"""

import numpy as np
from typing import Tuple, Dict
from .entropy import von_neumann_entropy, entanglement_entropy


def mutual_information(
    S_A: float,
    S_B: float,
    S_AB: float
) -> float:
    """
    Compute mutual information I(A:B) = S(A) + S(B) - S(A∪B).

    Measures total correlation between A and B.

    Parameters
    ----------
    S_A : float
        Entropy of region A
    S_B : float
        Entropy of region B
    S_AB : float
        Entropy of A∪B

    Returns
    -------
    float
        Mutual information I(A:B) >= 0

    Examples
    --------
    >>> # Independent regions: I = 0
    >>> S_A, S_B, S_AB = 1.0, 1.0, 2.0
    >>> I = mutual_information(S_A, S_B, S_AB)
    >>> print(f"I(A:B) = {I:.4f} (expected: 0)")
    """
    I = S_A + S_B - S_AB

    # Check validity (I >= 0 by strong subadditivity)
    if I < -1e-10:
        raise ValueError(
            f"Negative mutual information: I = {I:.6f}. "
            f"This violates strong subadditivity. Check entropy calculations."
        )

    return max(0, I)  # Clamp to 0 to handle numerical errors


def tripartite_information(
    S_A: float,
    S_B: float,
    S_C: float,
    S_AB: float,
    S_AC: float,
    S_BC: float,
    S_ABC: float
) -> float:
    """
    Compute tripartite information I₃(A:B:C).

    I₃ = I(A:B) + I(A:C) - I(A:BC)
       = S(A) + S(B) + S(C) - S(AB) - S(AC) - S(BC) + S(ABC)

    Positive I₃ indicates multipartite entanglement.

    Parameters
    ----------
    S_A, S_B, S_C : float
        Individual entropies
    S_AB, S_AC, S_BC : float
        Pairwise entropies
    S_ABC : float
        Total entropy

    Returns
    -------
    float
        Tripartite information
    """
    I3 = S_A + S_B + S_C - S_AB - S_AC - S_BC + S_ABC
    return I3


def conditional_mutual_information(
    S_A: float,
    S_B: float,
    S_C: float,
    S_AC: float,
    S_BC: float,
    S_ABC: float
) -> float:
    """
    Compute conditional mutual information I(A:B|C).

    I(A:B|C) = S(AC) + S(BC) - S(C) - S(ABC)

    Measures correlation between A and B given C.

    Parameters
    ----------
    S_A, S_B, S_C : float
        Individual entropies
    S_AC, S_BC : float
        Joint entropies
    S_ABC : float
        Total entropy

    Returns
    -------
    float
        I(A:B|C)
    """
    I_cond = S_AC + S_BC - S_C - S_ABC

    # Should be >= 0 by strong subadditivity
    if I_cond < -1e-10:
        raise ValueError(f"Negative CMI: {I_cond:.6f}")

    return max(0, I_cond)


def entanglement_negativity(
    rho_AB: np.ndarray,
    dim_A: int,
    dim_B: int
) -> Tuple[float, Dict]:
    """
    Compute entanglement negativity (measure of entanglement).

    Negativity: N = ||ρ^{T_B}|| - 1
    where T_B is partial transpose over subsystem B.

    Parameters
    ----------
    rho_AB : ndarray, shape (dim_A*dim_B, dim_A*dim_B)
        Density matrix of A∪B
    dim_A, dim_B : int
        Dimensions of subsystems

    Returns
    -------
    Tuple[float, Dict]
        (negativity, info_dict)
    """
    # Partial transpose over B
    rho_TB = partial_transpose(rho_AB, dim_A, dim_B, subsystem='B')

    # Negativity = ||ρ^{T_B}||_1 - 1
    eigenvalues = np.linalg.eigvalsh(rho_TB)
    trace_norm = np.sum(np.abs(eigenvalues))
    negativity = (trace_norm - 1) / 2

    # Logarithmic negativity
    log_negativity = np.log2(trace_norm)

    info = {
        'negativity': negativity,
        'log_negativity': log_negativity,
        'min_eigenvalue': np.min(eigenvalues),
        'is_entangled': negativity > 1e-10
    }

    return negativity, info


def partial_transpose(
    rho: np.ndarray,
    dim_A: int,
    dim_B: int,
    subsystem: str = 'B'
) -> np.ndarray:
    """
    Compute partial transpose of density matrix.

    Parameters
    ----------
    rho : ndarray, shape (dim_A*dim_B, dim_A*dim_B)
        Density matrix
    dim_A, dim_B : int
        Dimensions of subsystems
    subsystem : str
        'A' or 'B' - which subsystem to transpose

    Returns
    -------
    ndarray
        Partially transposed density matrix
    """
    # Reshape to (dim_A, dim_B, dim_A, dim_B)
    rho_reshaped = rho.reshape(dim_A, dim_B, dim_A, dim_B)

    if subsystem == 'B':
        # Transpose B: (i,j,k,l) → (i,l,k,j)
        rho_TB = np.transpose(rho_reshaped, (0, 3, 2, 1))
    elif subsystem == 'A':
        # Transpose A: (i,j,k,l) → (k,j,i,l)
        rho_TB = np.transpose(rho_reshaped, (2, 1, 0, 3))
    else:
        raise ValueError(f"subsystem must be 'A' or 'B', got {subsystem}")

    # Reshape back
    rho_TB = rho_TB.reshape(dim_A * dim_B, dim_A * dim_B)

    return rho_TB


def kinematic_space_distance(
    I_AB: float,
    S_A: float,
    S_B: float
) -> float:
    """
    Compute kinematic space distance from mutual information.

    d(A,B) = -log[I(A:B) / sqrt(S(A)*S(B))]

    High mutual information → small distance.

    Parameters
    ----------
    I_AB : float
        Mutual information
    S_A, S_B : float
        Entropies

    Returns
    -------
    float
        Distance in kinematic space
    """
    if I_AB <= 0 or S_A <= 0 or S_B <= 0:
        return np.inf

    # Normalized mutual information
    I_normalized = I_AB / np.sqrt(S_A * S_B)

    # Distance
    d = -np.log(I_normalized + 1e-10)

    return d
