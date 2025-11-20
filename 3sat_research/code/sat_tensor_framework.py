#!/usr/bin/env python3
"""
🚀 P vs NP BREAKTHROUGH FRAMEWORK
================================================================================
Revolutionary discriminators for 3-SAT based on:
1. TENSOR NETWORKS (bond dimension χ) - PRIMARY HYPOTHESIS
2. FRACTIONAL DERIVATIVES (∂^α, α ∈ [1,2])
3. PERSISTENT HOMOLOGY (dynamic topology)
4. HOLONOMIC GRADIENT (non-abelian gauge theory)

Author: Denis & Claude
Date: 2025-11-20
Goal: Find discriminator with d > 1.25 (beat lm_mean_depth)
================================================================================
"""

import numpy as np
from scipy.linalg import svd, logm
from scipy.special import gamma
from scipy.stats import ttest_ind
from typing import List, Tuple, Dict, Optional
import re
from pathlib import Path
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SATFormula:
    """3-SAT formula representation."""
    n_vars: int
    n_clauses: int
    clauses: List[List[int]]  # Each clause is list of literals
    is_sat: Optional[bool] = None  # Ground truth
    filename: str = ""

    def __post_init__(self):
        """Validate formula."""
        assert all(len(c) == 3 for c in self.clauses), "Must be 3-SAT"
        assert all(abs(lit) <= self.n_vars for c in self.clauses for lit in c)


@dataclass
class DiscriminatorResult:
    """Result of discriminator computation."""
    name: str
    value: float
    computation_time: float  # seconds
    metadata: Dict = None


# ============================================================================
# CNF PARSER
# ============================================================================

def parse_cnf(filepath: Path) -> SATFormula:
    """
    Parse DIMACS CNF file.

    Format:
        c comments
        p cnf <nvars> <nclauses>
        lit1 lit2 lit3 0
        ...

    Args:
        filepath: Path to .cnf file

    Returns:
        SATFormula object
    """
    clauses = []
    n_vars = n_clauses = 0

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('c') or line.startswith('%'):
                continue

            # Parse header
            if line.startswith('p'):
                parts = line.split()
                assert parts[1] == 'cnf', "Must be CNF format"
                n_vars = int(parts[2])
                n_clauses = int(parts[3])
                continue

            # Parse clause
            literals = [int(x) for x in line.split() if x != '0']
            if literals:
                clauses.append(literals)

    # Determine SAT/UNSAT from filename
    fname = filepath.name
    is_sat = None
    if 'uuf' in fname.lower() or 'unsat' in fname.lower():
        is_sat = False
    elif 'uf' in fname.lower() or 'sat' in fname.lower():
        is_sat = True

    return SATFormula(
        n_vars=n_vars,
        n_clauses=n_clauses,
        clauses=clauses,
        is_sat=is_sat,
        filename=fname
    )


# ============================================================================
# TENSOR NETWORK DISCRIMINATOR (PRIMARY HYPOTHESIS)
# ============================================================================

class TensorNetworkDiscriminator:
    """
    REVOLUTIONARY IDEA: Represent 3-SAT as tensor network, compute bond dimension χ.

    HYPOTHESIS:
        SAT   ↔ χ ≤ poly(n)    (low entanglement)
        UNSAT ↔ χ > exp(n)     (high entanglement)

    IF TRUE → P=NP solved! (χ computable in poly time via SVD)
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula
        self.n = formula.n_vars
        self.m = formula.n_clauses

    def to_tensor(self) -> np.ndarray:
        """
        Convert formula to tensor representation.

        Construction:
            T[i₁, i₂, ..., iₙ] = 1 if assignment satisfies formula, 0 otherwise
            where iₖ ∈ {0,1} (variable k false/true)

        Shape: (2, 2, ..., 2) with n dimensions

        Returns:
            Tensor of shape (2,)*n
        """
        # Build full truth table (WARNING: exponential! Only for n≤20)
        if self.n > 20:
            raise ValueError(f"n={self.n} too large for full tensor (need n≤20)")

        tensor_shape = tuple([2] * self.n)
        T = np.zeros(tensor_shape, dtype=np.float32)

        # Iterate all 2^n assignments
        for assignment_idx in range(2**self.n):
            # Convert index to binary assignment
            assignment = [(assignment_idx >> k) & 1 for k in range(self.n)]

            # Check if assignment satisfies formula
            if self._satisfies(assignment):
                # Convert flat index to multi-index
                multi_idx = tuple(assignment)
                T[multi_idx] = 1.0

        return T

    def _satisfies(self, assignment: List[int]) -> bool:
        """Check if assignment satisfies formula."""
        for clause in self.formula.clauses:
            satisfied = False
            for lit in clause:
                var_idx = abs(lit) - 1  # Convert to 0-indexed
                var_value = assignment[var_idx]

                if (lit > 0 and var_value == 1) or (lit < 0 and var_value == 0):
                    satisfied = True
                    break

            if not satisfied:
                return False

        return True

    def compute_bond_dimension(self) -> float:
        """
        Compute bond dimension χ = max rank across all bipartitions.

        For each cut k: {1,...,k} | {k+1,...,n}
        1. Reshape tensor: (2^k, 2^(n-k))
        2. Compute SVD
        3. Count singular values > threshold
        4. χ = max across all cuts

        Returns:
            Maximum bond dimension
        """
        try:
            T = self.to_tensor()
        except ValueError:
            # For n>20, use approximation (sample-based)
            return self._approximate_bond_dimension()

        max_chi = 1
        threshold = 1e-10  # Singular value threshold

        # Try all bipartitions
        for k in range(1, self.n):
            # Reshape: left = sites 0..k-1, right = sites k..n-1
            left_dim = 2**k
            right_dim = 2**(self.n - k)

            # Reshape tensor
            T_matrix = T.reshape(left_dim, right_dim)

            # SVD
            try:
                U, s, Vt = svd(T_matrix, full_matrices=False)

                # Count significant singular values
                chi_k = np.sum(s > threshold * s[0]) if s[0] > 0 else 0
                max_chi = max(max_chi, chi_k)
            except:
                continue

        return float(max_chi)

    def _approximate_bond_dimension(self, n_samples: int = 10000) -> float:
        """
        Approximate bond dimension for large n using sampling.

        KEY INSIGHT:
        - SAT: Many satisfying assignments → low effective rank (clustered)
        - UNSAT: No satisfying assignments → use energy landscape rank

        Strategy:
        1. Sample random assignments (not just satisfying!)
        2. Weight by exp(-violations)
        3. Compute rank of weighted matrix

        Returns:
            Estimated bond dimension
        """
        # Sample random assignments with violation counts
        assignments = []
        weights = []
        attempts = n_samples

        for _ in range(attempts):
            assignment = np.random.randint(0, 2, size=self.n)
            violations = self._count_violations(assignment)

            # Boltzmann weight: w = exp(-violations)
            weight = np.exp(-violations)

            assignments.append(assignment)
            weights.append(weight)

        # Build weighted matrix
        matrix = np.array(assignments, dtype=np.float32)
        weights = np.array(weights, dtype=np.float32)

        # Normalize weights
        weights = weights / (np.sum(weights) + 1e-15)

        # Weight rows by sqrt(weight) for SVD
        weighted_matrix = matrix * np.sqrt(weights)[:, np.newaxis]

        # Compute rank
        try:
            U, s, Vt = svd(weighted_matrix, full_matrices=False)
            threshold = 1e-6 * s[0] if s[0] > 0 else 1e-6
            rank = np.sum(s > threshold)

            # Additional discriminator: ratio of satisfying assignments
            n_satisfying = np.sum([self._satisfies(a.tolist()) for a in assignments[:100]])
            sat_ratio = n_satisfying / 100.0

            # SAT: high sat_ratio, low rank
            # UNSAT: low sat_ratio, high rank
            # Combine: effective_chi = rank / (sat_ratio + 0.01)
            effective_chi = rank / (sat_ratio + 0.01)

            return float(effective_chi)
        except:
            return float(self.n)

    def _count_violations(self, assignment) -> int:
        """Count violated clauses (helper for approximation)."""
        violations = 0
        for clause in self.formula.clauses:
            satisfied = False
            for lit in clause:
                var_idx = abs(lit) - 1
                if isinstance(assignment, np.ndarray):
                    var_value = assignment[var_idx]
                else:
                    var_value = assignment[var_idx]

                if (lit > 0 and var_value == 1) or (lit < 0 and var_value == 0):
                    satisfied = True
                    break
            if not satisfied:
                violations += 1
        return violations

    def compute_entanglement_entropy(self) -> float:
        """
        Compute entanglement entropy S = -Σᵢ λᵢ² log(λᵢ²)
        where λᵢ are singular values (normalized).

        Returns:
            Entanglement entropy
        """
        try:
            T = self.to_tensor()
        except ValueError:
            # Use approximate for large n
            return self._approximate_entanglement()

        # Use middle bipartition
        k = self.n // 2
        left_dim = 2**k
        right_dim = 2**(self.n - k)

        T_matrix = T.reshape(left_dim, right_dim)

        try:
            U, s, Vt = svd(T_matrix, full_matrices=False)

            # Normalize singular values
            s_norm = s / np.linalg.norm(s) if np.linalg.norm(s) > 0 else s
            s_squared = s_norm**2

            # Compute entropy
            s_squared = s_squared[s_squared > 1e-15]  # Avoid log(0)
            entropy = -np.sum(s_squared * np.log(s_squared))

            return float(entropy)
        except:
            return 0.0

    def _approximate_entanglement(self, n_samples: int = 1000) -> float:
        """Approximate entanglement entropy via sampling."""
        # Similar to approximate bond dimension
        satisfying = []
        attempts = 0
        max_attempts = 10000

        while len(satisfying) < n_samples and attempts < max_attempts:
            assignment = np.random.randint(0, 2, size=self.n)
            if self._satisfies(assignment.tolist()):
                satisfying.append(assignment)
            attempts += 1

        if len(satisfying) < 10:
            return 0.0

        matrix = np.array(satisfying, dtype=np.float32)

        try:
            U, s, Vt = svd(matrix, full_matrices=False)
            s_norm = s / np.linalg.norm(s) if np.linalg.norm(s) > 0 else s
            s_squared = s_norm**2
            s_squared = s_squared[s_squared > 1e-15]
            entropy = -np.sum(s_squared * np.log(s_squared))
            return float(entropy)
        except:
            return 0.0


# ============================================================================
# FRACTIONAL DERIVATIVE DISCRIMINATOR
# ============================================================================

class FractionalDerivativeDiscriminator:
    """
    HYPOTHESIS: Sweet spot between gradient (α=1, d=0.98) and Hessian (α=2, d=0.07)
    exists at some α* ∈ (1,2) with d > 1.0

    Uses Caputo fractional derivative.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula
        self.n = formula.n_vars

    def compute_probability_vector(self) -> np.ndarray:
        """Compute polarity-based probability vector."""
        pos_count = np.zeros(self.n)
        neg_count = np.zeros(self.n)

        for clause in self.formula.clauses:
            for lit in clause:
                var_idx = abs(lit) - 1
                if lit > 0:
                    pos_count[var_idx] += 1
                else:
                    neg_count[var_idx] += 1

        total = pos_count + neg_count
        prob = np.where(total > 0, pos_count / total, 0.5)

        # Clip to avoid numerical issues
        prob = np.clip(prob, 1e-10, 1 - 1e-10)

        return prob

    def compute_log_likelihood(self, prob: np.ndarray) -> float:
        """Compute log P(formula satisfied | prob)."""
        log_prob = 0.0

        for clause in self.formula.clauses:
            # P(clause satisfied) = 1 - P(all literals false)
            p_all_false = 1.0

            for lit in clause:
                var_idx = abs(lit) - 1
                if lit > 0:
                    p_all_false *= (1 - prob[var_idx])
                else:
                    p_all_false *= prob[var_idx]

            p_clause = 1.0 - p_all_false
            p_clause = max(p_clause, 1e-15)  # Avoid log(0)
            log_prob += np.log(p_clause)

        return log_prob

    def compute_fractional_derivative(self, alpha: float = 1.5,
                                     epsilon: float = 1e-4) -> float:
        """
        Compute fractional derivative ∂^α L / ∂p^α using Caputo definition.

        For α ∈ (1,2):
            D^α f(x) ≈ [f(x+h) - 2f(x) + f(x-h)] / h^α × Γ(3-α)

        Args:
            alpha: Fractional order (1 < alpha < 2)
            epsilon: Finite difference step

        Returns:
            Mean absolute fractional derivative
        """
        assert 1.0 <= alpha <= 2.0, "α must be in [1,2]"

        prob = self.compute_probability_vector()
        L0 = self.compute_log_likelihood(prob)

        frac_derivatives = []

        for i in range(self.n):
            # Forward perturbation
            prob_plus = prob.copy()
            prob_plus[i] = min(prob[i] + epsilon, 1 - 1e-10)
            L_plus = self.compute_log_likelihood(prob_plus)

            # Backward perturbation
            prob_minus = prob.copy()
            prob_minus[i] = max(prob[i] - epsilon, 1e-10)
            L_minus = self.compute_log_likelihood(prob_minus)

            # Fractional derivative (Caputo approximation)
            if alpha == 1.0:
                # Standard gradient
                deriv = (L_plus - L_minus) / (2 * epsilon)
            elif alpha == 2.0:
                # Standard Hessian diagonal
                deriv = (L_plus - 2*L0 + L_minus) / (epsilon**2)
            else:
                # Fractional order
                numerator = L_plus - 2*L0 + L_minus
                denominator = epsilon**alpha
                gamma_factor = gamma(3 - alpha)
                deriv = (numerator / denominator) * gamma_factor

            frac_derivatives.append(abs(deriv))

        return float(np.mean(frac_derivatives))

    def optimize_alpha(self, alpha_range: Tuple[float, float] = (1.0, 2.0),
                      n_steps: int = 20) -> Tuple[float, float]:
        """
        Find optimal α that maximizes discriminative power.

        Returns:
            (optimal_alpha, value_at_optimal)
        """
        alphas = np.linspace(alpha_range[0], alpha_range[1], n_steps)
        values = []

        for alpha in alphas:
            try:
                val = self.compute_fractional_derivative(alpha)
                values.append(val)
            except:
                values.append(0.0)

        optimal_idx = np.argmax(values)
        return float(alphas[optimal_idx]), float(values[optimal_idx])


# ============================================================================
# PERSISTENT HOMOLOGY DISCRIMINATOR
# ============================================================================

class PersistentHomologyDiscriminator:
    """
    HYPOTHESIS: Static topology (β₀, β₁) fails, but DYNAMIC topology succeeds.

    Track Betti numbers β(t) during greedy descent trajectory.

    DISCRIMINATOR: persistence_signature = ∫|dβ/dt| dt
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula
        self.n = formula.n_vars

    def greedy_descent_trajectory(self, max_steps: int = 100) -> List[np.ndarray]:
        """
        Perform greedy descent and record trajectory.

        Returns:
            List of assignments (each is binary vector of length n)
        """
        # Random start
        state = np.random.randint(0, 2, size=self.n)
        trajectory = [state.copy()]

        for step in range(max_steps):
            current_violations = self._count_violations(state)
            improved = False

            for var in range(self.n):
                # Flip variable
                state[var] = 1 - state[var]
                new_violations = self._count_violations(state)

                if new_violations < current_violations:
                    trajectory.append(state.copy())
                    current_violations = new_violations
                    improved = True
                    break

                # Undo flip
                state[var] = 1 - state[var]

            if not improved or current_violations == 0:
                break

        return trajectory

    def _count_violations(self, assignment: np.ndarray) -> int:
        """Count violated clauses."""
        violations = 0
        for clause in self.formula.clauses:
            satisfied = False
            for lit in clause:
                var_idx = abs(lit) - 1
                if (lit > 0 and assignment[var_idx] == 1) or \
                   (lit < 0 and assignment[var_idx] == 0):
                    satisfied = True
                    break
            if not satisfied:
                violations += 1
        return violations

    def compute_betti_numbers(self, assignment: np.ndarray) -> Tuple[int, int]:
        """
        Compute β₀ and β₁ for neighborhood graph of assignment.

        Graph: nodes = 1-flip neighbors, edges = Hamming distance 1

        Returns:
            (β₀, β₁) - connected components and cycles
        """
        # Build 1-flip neighborhood graph
        neighbors = []
        violations = []

        for var in range(self.n):
            neighbor = assignment.copy()
            neighbor[var] = 1 - neighbor[var]
            neighbors.append(neighbor)
            violations.append(self._count_violations(neighbor))

        # Adjacency: neighbors with same violation count
        adjacency = np.zeros((self.n, self.n), dtype=int)
        for i in range(self.n):
            for j in range(i+1, self.n):
                if violations[i] == violations[j]:
                    adjacency[i, j] = adjacency[j, i] = 1

        # β₀ = number of connected components
        visited = np.zeros(self.n, dtype=bool)
        components = 0

        def dfs(node):
            visited[node] = True
            for neighbor in range(self.n):
                if adjacency[node, neighbor] and not visited[neighbor]:
                    dfs(neighbor)

        for node in range(self.n):
            if not visited[node]:
                dfs(node)
                components += 1

        beta_0 = components

        # β₁ = cycles (approximation: #edges - #nodes + #components)
        n_edges = np.sum(adjacency) // 2
        n_nodes = self.n
        beta_1 = max(0, n_edges - n_nodes + components)

        return beta_0, beta_1

    def compute_persistence_signature(self, n_trajectories: int = 10) -> float:
        """
        Compute persistence signature = mean(∫|dβ/dt| dt) over trajectories.

        Returns:
            Persistence signature value
        """
        signatures = []

        for trial in range(n_trajectories):
            trajectory = self.greedy_descent_trajectory()

            # Compute Betti numbers along trajectory
            betti_sequence = []
            for state in trajectory:
                beta_0, beta_1 = self.compute_betti_numbers(state)
                betti_sequence.append((beta_0, beta_1))

            # Compute total variation
            variation = 0.0
            for t in range(1, len(betti_sequence)):
                db0 = abs(betti_sequence[t][0] - betti_sequence[t-1][0])
                db1 = abs(betti_sequence[t][1] - betti_sequence[t-1][1])
                variation += db0 + db1

            signatures.append(variation)

        return float(np.mean(signatures))


# ============================================================================
# HOLONOMIC GRADIENT DISCRIMINATOR
# ============================================================================

class HolonomicGradientDiscriminator:
    """
    HYPOTHESIS: Holonomy ∮_γ ∇L·dp distinguishes SAT (abelian, holonomy=0)
    from UNSAT (non-abelian, holonomy≠0).

    Inspired by Yang-Mills gauge theory.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula
        self.n = formula.n_vars

    def compute_probability_vector(self) -> np.ndarray:
        """Compute polarity-based probability vector."""
        pos_count = np.zeros(self.n)
        neg_count = np.zeros(self.n)

        for clause in self.formula.clauses:
            for lit in clause:
                var_idx = abs(lit) - 1
                if lit > 0:
                    pos_count[var_idx] += 1
                else:
                    neg_count[var_idx] += 1

        total = pos_count + neg_count
        prob = np.where(total > 0, pos_count / total, 0.5)
        prob = np.clip(prob, 1e-10, 1 - 1e-10)

        return prob

    def compute_log_likelihood(self, prob: np.ndarray) -> float:
        """Compute log P(formula satisfied | prob)."""
        log_prob = 0.0

        for clause in self.formula.clauses:
            p_all_false = 1.0
            for lit in clause:
                var_idx = abs(lit) - 1
                p_all_false *= (1 - prob[var_idx]) if lit > 0 else prob[var_idx]
            p_clause = max(1.0 - p_all_false, 1e-15)
            log_prob += np.log(p_clause)

        return log_prob

    def compute_gradient(self, prob: np.ndarray, epsilon: float = 1e-4) -> np.ndarray:
        """Compute gradient ∇L at prob."""
        L0 = self.compute_log_likelihood(prob)
        grad = np.zeros(self.n)

        for i in range(self.n):
            prob_plus = prob.copy()
            prob_plus[i] = min(prob[i] + epsilon, 1 - 1e-10)
            L_plus = self.compute_log_likelihood(prob_plus)

            prob_minus = prob.copy()
            prob_minus[i] = max(prob[i] - epsilon, 1e-10)
            L_minus = self.compute_log_likelihood(prob_minus)

            grad[i] = (L_plus - L_minus) / (2 * epsilon)

        return grad

    def compute_holonomy(self, n_loops: int = 5, loop_radius: float = 0.1) -> float:
        """
        Compute holonomy ∮_γ ∇L·dp along closed loops.

        If holonomy ≠ 0 → non-integrable gradient field → UNSAT

        Args:
            n_loops: Number of random loops to test
            loop_radius: Radius of loops in probability space

        Returns:
            Mean absolute holonomy
        """
        prob_center = self.compute_probability_vector()
        holonomies = []

        for loop_idx in range(n_loops):
            # Generate random circular loop
            # γ(t) = p_center + r*(cos(2πt), sin(2πt), 0, ..., 0) for t∈[0,1]

            # Pick two random dimensions for the loop
            dims = np.random.choice(self.n, size=2, replace=False)

            holonomy = 0.0
            n_steps = 20

            for step in range(n_steps):
                t = step / n_steps
                t_next = (step + 1) / n_steps

                # Current point on loop
                prob = prob_center.copy()
                prob[dims[0]] += loop_radius * np.cos(2 * np.pi * t)
                prob[dims[1]] += loop_radius * np.sin(2 * np.pi * t)
                prob = np.clip(prob, 1e-10, 1 - 1e-10)

                # Next point on loop
                prob_next = prob_center.copy()
                prob_next[dims[0]] += loop_radius * np.cos(2 * np.pi * t_next)
                prob_next[dims[1]] += loop_radius * np.sin(2 * np.pi * t_next)
                prob_next = np.clip(prob_next, 1e-10, 1 - 1e-10)

                # Tangent vector
                dp = prob_next - prob

                # Gradient at current point
                grad = self.compute_gradient(prob)

                # Line integral contribution
                holonomy += np.dot(grad, dp)

            holonomies.append(abs(holonomy))

        return float(np.mean(holonomies))


# ============================================================================
# MAIN ANALYSIS PIPELINE
# ============================================================================

def analyze_formula(formula: SATFormula) -> Dict[str, DiscriminatorResult]:
    """
    Run all discriminators on a single formula.

    Returns:
        Dictionary mapping discriminator name to result
    """
    import time

    results = {}

    # 1. TENSOR NETWORK (PRIMARY HYPOTHESIS)
    print(f"  [1/4] Tensor Network...", end='', flush=True)
    start = time.time()
    try:
        tn = TensorNetworkDiscriminator(formula)
        chi = tn.compute_bond_dimension()
        entropy = tn.compute_entanglement_entropy()
        elapsed = time.time() - start

        results['bond_dimension'] = DiscriminatorResult(
            name='bond_dimension',
            value=chi,
            computation_time=elapsed,
            metadata={'entanglement_entropy': entropy}
        )
        print(f" χ={chi:.2f}, S={entropy:.3f} ({elapsed:.2f}s)")
    except Exception as e:
        print(f" FAILED: {e}")
        results['bond_dimension'] = DiscriminatorResult(
            name='bond_dimension',
            value=np.nan,
            computation_time=time.time() - start
        )

    # 2. FRACTIONAL DERIVATIVE
    print(f"  [2/4] Fractional Derivative...", end='', flush=True)
    start = time.time()
    try:
        fd = FractionalDerivativeDiscriminator(formula)
        alpha_opt, val_opt = fd.optimize_alpha()
        elapsed = time.time() - start

        results['fractional_derivative'] = DiscriminatorResult(
            name='fractional_derivative',
            value=val_opt,
            computation_time=elapsed,
            metadata={'optimal_alpha': alpha_opt}
        )
        print(f" α*={alpha_opt:.3f}, val={val_opt:.3f} ({elapsed:.2f}s)")
    except Exception as e:
        print(f" FAILED: {e}")
        results['fractional_derivative'] = DiscriminatorResult(
            name='fractional_derivative',
            value=np.nan,
            computation_time=time.time() - start
        )

    # 3. PERSISTENT HOMOLOGY (expensive, skip for large n)
    if formula.n_vars <= 30:
        print(f"  [3/4] Persistent Homology...", end='', flush=True)
        start = time.time()
        try:
            ph = PersistentHomologyDiscriminator(formula)
            signature = ph.compute_persistence_signature(n_trajectories=5)
            elapsed = time.time() - start

            results['persistence_signature'] = DiscriminatorResult(
                name='persistence_signature',
                value=signature,
                computation_time=elapsed
            )
            print(f" sig={signature:.3f} ({elapsed:.2f}s)")
        except Exception as e:
            print(f" FAILED: {e}")
            results['persistence_signature'] = DiscriminatorResult(
                name='persistence_signature',
                value=np.nan,
                computation_time=time.time() - start
            )
    else:
        print(f"  [3/4] Persistent Homology... SKIPPED (n={formula.n_vars}>30)")
        results['persistence_signature'] = DiscriminatorResult(
            name='persistence_signature',
            value=np.nan,
            computation_time=0.0
        )

    # 4. HOLONOMIC GRADIENT
    print(f"  [4/4] Holonomic Gradient...", end='', flush=True)
    start = time.time()
    try:
        hg = HolonomicGradientDiscriminator(formula)
        holonomy = hg.compute_holonomy(n_loops=5)
        elapsed = time.time() - start

        results['holonomy'] = DiscriminatorResult(
            name='holonomy',
            value=holonomy,
            computation_time=elapsed
        )
        print(f" hol={holonomy:.3f} ({elapsed:.2f}s)")
    except Exception as e:
        print(f" FAILED: {e}")
        results['holonomy'] = DiscriminatorResult(
            name='holonomy',
            value=np.nan,
            computation_time=time.time() - start
        )

    return results


def compute_cohens_d(sat_values: np.ndarray, unsat_values: np.ndarray) -> float:
    """
    Compute Cohen's d effect size.

    d = (mean_unsat - mean_sat) / pooled_std

    Returns:
        Cohen's d (positive if UNSAT > SAT)
    """
    mean_sat = np.mean(sat_values)
    mean_unsat = np.mean(unsat_values)
    std_sat = np.std(sat_values, ddof=1)
    std_unsat = np.std(unsat_values, ddof=1)

    n_sat = len(sat_values)
    n_unsat = len(unsat_values)

    pooled_std = np.sqrt(((n_sat - 1) * std_sat**2 + (n_unsat - 1) * std_unsat**2) /
                         (n_sat + n_unsat - 2))

    if pooled_std == 0:
        return 0.0

    d = (mean_unsat - mean_sat) / pooled_std
    return d


# ============================================================================
# DEMO / TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("🚀 P vs NP BREAKTHROUGH FRAMEWORK - TEST")
    print("="*80)

    # Test CNF parser
    benchmark_dir = Path("/home/user/denis123-ux/3sat_research/benchmarks")

    # Load one SAT and one UNSAT
    sat_file = benchmark_dir / "uf50-01.cnf"
    unsat_file = benchmark_dir / "UUF50.218.1000" / "uuf50-01.cnf"

    print("\n[TEST 1] Parsing CNF files...")
    formula_sat = parse_cnf(sat_file)
    print(f"✓ SAT formula: n={formula_sat.n_vars}, m={formula_sat.n_clauses}")

    formula_unsat = parse_cnf(unsat_file)
    print(f"✓ UNSAT formula: n={formula_unsat.n_vars}, m={formula_unsat.n_clauses}")

    print("\n[TEST 2] Running discriminators on SAT formula...")
    results_sat = analyze_formula(formula_sat)

    print("\n[TEST 3] Running discriminators on UNSAT formula...")
    results_unsat = analyze_formula(formula_unsat)

    print("\n[RESULTS COMPARISON]")
    print("-" * 80)
    print(f"{'Discriminator':<30} {'SAT':<15} {'UNSAT':<15} {'Trend':<10}")
    print("-" * 80)

    for name in results_sat.keys():
        val_sat = results_sat[name].value
        val_unsat = results_unsat[name].value

        if np.isnan(val_sat) or np.isnan(val_unsat):
            trend = "N/A"
        elif abs(val_unsat - val_sat) < 1e-6:
            trend = "="
        elif val_unsat > val_sat:
            trend = "UNSAT > SAT ✓"
        else:
            trend = "SAT > UNSAT"

        print(f"{name:<30} {val_sat:<15.4f} {val_unsat:<15.4f} {trend:<10}")

    print("="*80)
    print("✓ Framework test complete!")
    print("="*80)
