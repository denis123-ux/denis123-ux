"""
HILBERT-PÓLYA OPERATOR SEARCH
==============================

The ultimate goal: Find the Hermitian operator H whose eigenvalues are
exactly the imaginary parts of the non-trivial Riemann zeros.

If such H exists and is proven, RH is automatically true!

This module implements:
1. Candidate operators from literature (Berry-Keating, etc.)
2. Parameterized operator families
3. Eigenvalue computation
4. Matching with Riemann zeros
5. Machine learning-guided search in operator space

Key innovation: Use optimization to search in operator space, guided by
the actual Riemann zeros as targets!
"""

import numpy as np
from scipy import linalg
from scipy.optimize import minimize
from typing import List, Tuple, Optional, Dict, Callable
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# DISCRETIZATION AND NUMERICAL OPERATORS
# =============================================================================

def create_position_operator(n: int, x_min: float = 0.1, x_max: float = 10.0) -> np.ndarray:
    """
    Discretized position operator X on [x_min, x_max].
    """
    x = np.linspace(x_min, x_max, n)
    return np.diag(x)

def create_momentum_operator(n: int, x_min: float = 0.1, x_max: float = 10.0) -> np.ndarray:
    """
    Discretized momentum operator P = -i d/dx (using finite differences).
    """
    dx = (x_max - x_min) / (n - 1)

    # Central difference derivative (with periodic boundary)
    D = np.zeros((n, n))
    for i in range(n):
        D[i, (i+1) % n] = 1
        D[i, (i-1) % n] = -1
    D = D / (2 * dx)

    return -1j * D

def create_xp_operator(n: int, x_min: float = 0.1, x_max: float = 10.0,
                       symmetrized: bool = True) -> np.ndarray:
    """
    Berry-Keating Hamiltonian: H = xp (or symmetrized (xp + px)/2).

    This is the main candidate from Berry-Keating conjecture!
    """
    X = create_position_operator(n, x_min, x_max)
    P = create_momentum_operator(n, x_min, x_max)

    if symmetrized:
        # H = (XP + PX) / 2 to ensure Hermiticity
        H = (X @ P + P @ X) / 2
    else:
        H = X @ P

    # Make Hermitian (enforce symmetry)
    H = (H + H.conj().T) / 2

    return H

def create_harmonic_oscillator(n: int, omega: float = 1.0) -> np.ndarray:
    """
    Quantum harmonic oscillator: H = p²/2 + ω²x²/2
    """
    X = create_position_operator(n)
    P = create_momentum_operator(n)

    H = P @ P / 2 + omega**2 * X @ X / 2
    H = (H + H.conj().T) / 2  # Ensure Hermitian

    return H

# =============================================================================
# PARAMETERIZED OPERATOR FAMILIES
# =============================================================================

def create_generalized_xp(n: int, alpha: float = 1.0, beta: float = 1.0,
                          gamma: float = 0.0, potential: Optional[Callable] = None) -> np.ndarray:
    """
    Generalized Berry-Keating operator:

    H = α(xp + px)/2 + β(x² + p²)/2 + γV(x)

    Parameters:
    - alpha: xp coupling strength
    - beta: harmonic term strength
    - gamma: potential strength
    - potential: V(x) function
    """
    X = create_position_operator(n)
    P = create_momentum_operator(n)

    # Berry-Keating term
    H = alpha * (X @ P + P @ X) / 2

    # Harmonic term
    H = H + beta * (X @ X + P @ P) / 2

    # Custom potential
    if potential is not None and gamma != 0:
        x = np.diag(X)
        V = np.diag(potential(x))
        H = H + gamma * V

    H = (H + H.conj().T) / 2
    return H

def create_log_potential_operator(n: int, alpha: float = 1.0,
                                  beta: float = 0.0) -> np.ndarray:
    """
    Operator with logarithmic potential (related to prime counting function):

    H = (xp + px)/2 + α log(x) + β/x
    """
    x_min, x_max = 1.0, 100.0  # Avoid log(0)
    X = create_position_operator(n, x_min, x_max)
    P = create_momentum_operator(n, x_min, x_max)

    x = np.diag(X)

    H = (X @ P + P @ X) / 2
    H = H + alpha * np.diag(np.log(x))
    if beta != 0:
        H = H + beta * np.diag(1.0 / x)

    H = (H + H.conj().T) / 2
    return H

def create_prime_potential_operator(n: int, num_primes: int = 25) -> np.ndarray:
    """
    NOVEL: Operator with potential defined by prime numbers!

    V(x) = Σ δ(x - log(p_k))

    This directly encodes prime structure into the Hamiltonian.
    """
    # Generate primes
    def sieve_primes(limit):
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, int(limit**0.5) + 1):
            if sieve[i]:
                for j in range(i*i, limit + 1, i):
                    sieve[j] = False
        return [i for i in range(limit + 1) if sieve[i]]

    primes = sieve_primes(1000)[:num_primes]
    log_primes = np.log(primes)

    x_min, x_max = 0.1, max(log_primes) * 1.2

    X = create_position_operator(n, x_min, x_max)
    P = create_momentum_operator(n, x_min, x_max)

    x = np.diag(X)

    # Create "soft delta" potential at log(p)
    sigma = 0.1  # Width of Gaussians
    V = np.zeros(n)
    for log_p in log_primes:
        V += np.exp(-(x - log_p)**2 / (2 * sigma**2))

    H = (X @ P + P @ X) / 2 - np.diag(V)
    H = (H + H.conj().T) / 2

    return H

# =============================================================================
# EIGENVALUE COMPUTATION AND MATCHING
# =============================================================================

def compute_eigenvalues(H: np.ndarray, n_eigenvalues: int = None) -> np.ndarray:
    """
    Compute eigenvalues of operator H.

    For Hermitian H, eigenvalues are real.
    """
    eigenvalues = np.linalg.eigvalsh(H)
    eigenvalues = np.sort(eigenvalues)

    if n_eigenvalues is not None:
        eigenvalues = eigenvalues[:n_eigenvalues]

    return np.real(eigenvalues)

def match_eigenvalues_to_zeros(eigenvalues: np.ndarray,
                               zeros: np.ndarray,
                               method: str = 'shift_scale') -> Dict:
    """
    Try to match operator eigenvalues to Riemann zeros.

    Methods:
    - 'shift_scale': Find best linear transformation a*λ + b
    - 'nonlinear': Try nonlinear transformations
    """
    n = min(len(eigenvalues), len(zeros))
    eigs = eigenvalues[:n]
    zs = zeros[:n]

    if method == 'shift_scale':
        # Find a, b to minimize Σ(a*λ_i + b - z_i)²
        # This is linear regression
        from scipy.stats import linregress
        slope, intercept, r_value, p_value, std_err = linregress(eigs, zs)

        transformed = slope * eigs + intercept
        residuals = transformed - zs
        rmse = np.sqrt(np.mean(residuals**2))

        return {
            'method': 'shift_scale',
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'rmse': rmse,
            'max_error': np.max(np.abs(residuals)),
            'transformed': transformed,
            'residuals': residuals,
        }

    elif method == 'nonlinear':
        # Try: z = a * λ^b + c
        from scipy.optimize import curve_fit

        def model(x, a, b, c):
            return a * np.abs(x)**b + c

        try:
            # Initial guess
            p0 = [1.0, 1.0, zeros[0]]
            popt, pcov = curve_fit(model, eigs, zs, p0=p0, maxfev=5000)

            transformed = model(eigs, *popt)
            residuals = transformed - zs
            rmse = np.sqrt(np.mean(residuals**2))

            return {
                'method': 'nonlinear',
                'params': popt,
                'rmse': rmse,
                'max_error': np.max(np.abs(residuals)),
                'transformed': transformed,
                'residuals': residuals,
            }
        except:
            return {'method': 'nonlinear', 'error': 'Fitting failed'}

    else:
        raise ValueError(f"Unknown method: {method}")

# =============================================================================
# OPERATOR SPACE SEARCH
# =============================================================================

def operator_loss(params: np.ndarray, zeros: np.ndarray, n: int = 100) -> float:
    """
    Loss function for operator search.

    params = [alpha, beta, gamma, ...]
    """
    alpha, beta, gamma = params[:3]

    # Define potential
    def potential(x):
        return np.log(x + 1)

    try:
        H = create_generalized_xp(n, alpha, beta, gamma, potential)
        eigenvalues = compute_eigenvalues(H, n_eigenvalues=len(zeros))

        # Match to zeros
        match = match_eigenvalues_to_zeros(eigenvalues, zeros, method='shift_scale')

        if 'rmse' in match:
            return match['rmse']
        else:
            return 1e10
    except:
        return 1e10

def search_operator_space(zeros: np.ndarray,
                          n_iterations: int = 100,
                          verbose: bool = True) -> Dict:
    """
    Search for optimal operator parameters.
    """
    if verbose:
        print("Searching operator space...")

    best_loss = float('inf')
    best_params = None
    best_match = None

    # Initial random search
    for i in range(n_iterations):
        # Random parameters
        params = np.array([
            np.random.uniform(-2, 2),   # alpha
            np.random.uniform(-1, 1),   # beta
            np.random.uniform(-1, 1),   # gamma
        ])

        loss = operator_loss(params, zeros[:20], n=50)

        if loss < best_loss:
            best_loss = loss
            best_params = params.copy()

            if verbose and i % 20 == 0:
                print(f"  Iteration {i}: loss = {loss:.4f}")

    # Refine with optimization
    if best_params is not None:
        result = minimize(
            lambda p: operator_loss(p, zeros[:20], n=50),
            best_params,
            method='Nelder-Mead',
            options={'maxiter': 200}
        )
        if result.fun < best_loss:
            best_params = result.x
            best_loss = result.fun

    # Compute final match
    if best_params is not None:
        alpha, beta, gamma = best_params

        def potential(x):
            return np.log(x + 1)

        H = create_generalized_xp(100, alpha, beta, gamma, potential)
        eigenvalues = compute_eigenvalues(H, n_eigenvalues=len(zeros))
        best_match = match_eigenvalues_to_zeros(eigenvalues, zeros, method='shift_scale')

    return {
        'best_params': best_params,
        'best_loss': best_loss,
        'best_match': best_match,
    }

# =============================================================================
# CANDIDATE OPERATORS EVALUATION
# =============================================================================

def evaluate_candidate_operators(zeros: np.ndarray, n: int = 200,
                                 verbose: bool = True) -> Dict:
    """
    Evaluate all candidate operators against Riemann zeros.
    """
    results = {}

    candidates = {
        'Berry-Keating (xp)': lambda: create_xp_operator(n),
        'Harmonic Oscillator': lambda: create_harmonic_oscillator(n, omega=1.0),
        'Generalized (α=1,β=0.1)': lambda: create_generalized_xp(n, alpha=1.0, beta=0.1, gamma=0.0),
        'Log Potential': lambda: create_log_potential_operator(n, alpha=0.5, beta=0.0),
        'Prime Potential (NOVEL)': lambda: create_prime_potential_operator(n, num_primes=25),
    }

    for name, create_fn in candidates.items():
        if verbose:
            print(f"\nEvaluating: {name}")

        try:
            H = create_fn()
            eigenvalues = compute_eigenvalues(H, n_eigenvalues=len(zeros))

            # Match
            match = match_eigenvalues_to_zeros(eigenvalues, zeros)

            results[name] = {
                'eigenvalues': eigenvalues,
                'match': match,
            }

            if verbose:
                print(f"  R² = {match.get('r_squared', 0):.4f}")
                print(f"  RMSE = {match.get('rmse', float('inf')):.4f}")

        except Exception as e:
            results[name] = {'error': str(e)}
            if verbose:
                print(f"  Error: {e}")

    return results

# =============================================================================
# MAIN HILBERT-PÓLYA ANALYSIS
# =============================================================================

def full_hilbert_polya_analysis(zeros: np.ndarray, verbose: bool = True) -> Dict:
    """
    Complete Hilbert-Pólya operator search and analysis.
    """
    if verbose:
        print("=" * 60)
        print("HILBERT-PÓLYA OPERATOR SEARCH")
        print("=" * 60)

    results = {}

    # 1. Evaluate known candidates
    if verbose:
        print("\n1. Evaluating Known Candidate Operators...")

    candidates = evaluate_candidate_operators(zeros[:30], n=100, verbose=verbose)
    results['candidates'] = candidates

    # 2. Search operator space
    if verbose:
        print("\n2. Searching Operator Space...")

    search_result = search_operator_space(zeros[:30], n_iterations=50, verbose=verbose)
    results['search'] = search_result

    # 3. Best operator
    if verbose:
        print("\n" + "=" * 60)
        print("BEST OPERATORS FOUND")
        print("=" * 60)

        # Find best among candidates
        best_candidate = None
        best_r2 = -1

        for name, data in candidates.items():
            if 'match' in data and 'r_squared' in data['match']:
                r2 = data['match']['r_squared']
                if r2 > best_r2:
                    best_r2 = r2
                    best_candidate = name

        if best_candidate:
            print(f"\nBest candidate: {best_candidate}")
            print(f"  R² = {best_r2:.4f}")

        # Search result
        if search_result['best_match']:
            print(f"\nOptimized operator:")
            print(f"  Params: α={search_result['best_params'][0]:.3f}, β={search_result['best_params'][1]:.3f}, γ={search_result['best_params'][2]:.3f}")
            print(f"  RMSE = {search_result['best_loss']:.4f}")
            print(f"  R² = {search_result['best_match'].get('r_squared', 0):.4f}")

    results['best_candidate'] = best_candidate
    results['best_r2'] = best_r2

    return results


if __name__ == "__main__":
    from riemann_zeros import get_zeros

    zeros = get_zeros(50)
    results = full_hilbert_polya_analysis(zeros)
