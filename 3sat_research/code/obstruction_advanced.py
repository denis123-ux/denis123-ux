#!/usr/bin/env python3
"""
🔬 ADVANCED OBSTRUCTION THEORY - INTEGER HOMOLOGY + TORSION
================================================================================

UPGRADE FROM BASIC VERSION:
1. Compute H₁(K, ℤ) over INTEGERS (not ℤ/2ℤ)
2. Use Smith Normal Form to detect TORSION subgroup
3. Elements of order 2 (τ: 2τ=0, τ≠0) are TRUE obstructions!

MATHEMATICAL REFINEMENT:

H₁(K, ℤ) ≅ ℤ^β₁ ⊕ Tors(H₁)

where Tors(H₁) is torsion subgroup.

Over ℤ, Smith Normal Form gives:
  D = diag(d₁, d₂, ..., d_r, 0, 0, ...)

where d_i | d_{i+1} (divisibility).

Torsion subgroup: ⨁ ℤ/d_i ℤ for d_i > 1

BREAKTHROUGH HYPOTHESIS:
- SAT: Torsion-free (all d_i = 1) → o(φ) = 0
- UNSAT: Has 2-torsion (some d_i = 2) → o(φ) ≠ 0

This would be DEFINITIVE if it works!

================================================================================
"""

import numpy as np
from typing import List, Tuple, Dict
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')


def smith_normal_form(M: np.ndarray) -> Tuple[np.ndarray, List[int]]:
    """
    Compute Smith Normal Form of integer matrix M.

    Returns:
        (D, invariant_factors)
        where D is diagonal matrix and invariant_factors are nonzero diagonal elements
    """
    if M.size == 0:
        return M, []

    A = M.copy().astype(np.int64)
    rows, cols = A.shape

    min_dim = min(rows, cols)
    rank = 0

    for k in range(min_dim):
        # Find pivot (smallest nonzero absolute value)
        best_pivot = None
        best_value = float('inf')

        for i in range(k, rows):
            for j in range(k, cols):
                if A[i, j] != 0 and abs(A[i, j]) < best_value:
                    best_pivot = (i, j)
                    best_value = abs(A[i, j])

        if best_pivot is None:
            break  # Rest is zero

        pi, pj = best_pivot

        # Swap rows and columns to bring pivot to (k, k)
        if pi != k:
            A[[k, pi], :] = A[[pi, k], :]
        if pj != k:
            A[:, [k, pj]] = A[:, [pj, k]]

        # Make pivot positive
        if A[k, k] < 0:
            A[k, :] = -A[k, :]

        # Eliminate column k below pivot
        changed = True
        while changed:
            changed = False

            for i in range(k+1, rows):
                if A[i, k] != 0:
                    q = A[i, k] // A[k, k]
                    A[i, :] -= q * A[k, :]
                    changed = True

            # Eliminate row k to the right of pivot
            for j in range(k+1, cols):
                if A[k, j] != 0:
                    q = A[k, j] // A[k, k]
                    A[:, j] -= q * A[:, k]
                    changed = True

            # Check if any off-diagonal element is smaller
            for i in range(k+1, rows):
                if A[i, k] != 0 and abs(A[i, k]) < abs(A[k, k]):
                    A[[k, i], :] = A[[i, k], :]
                    if A[k, k] < 0:
                        A[k, :] = -A[k, :]
                    changed = True
                    break

            if not changed:
                for j in range(k+1, cols):
                    if A[k, j] != 0 and abs(A[k, j]) < abs(A[k, k]):
                        A[:, [k, j]] = A[:, [j, k]]
                        if A[k, k] < 0:
                            A[k, :] = -A[k, :]
                        changed = True
                        break

        rank += 1

    # Extract invariant factors (nonzero diagonal elements)
    invariants = []
    for i in range(min_dim):
        if A[i, i] > 1:  # Torsion!
            invariants.append(int(A[i, i]))

    return A, invariants


class IntegerHomologyComputer:
    """
    Compute homology over ℤ (integers).
    """

    def __init__(self, vertices: List, edges: List, triangles: List):
        self.vertices = vertices
        self.edges = edges
        self.triangles = triangles

        self.n_vertices = len(vertices)
        self.n_edges = len(edges)
        self.n_triangles = len(triangles)

    def _build_boundary_matrix_1(self) -> np.ndarray:
        """
        Boundary matrix ∂₁: C₁ → C₀ over ℤ.

        For directed edge (v₁ → v₂), ∂₁(e) = v₂ - v₁
        """
        d1 = np.zeros((self.n_vertices, self.n_edges), dtype=np.int32)

        for j, (src, tgt) in enumerate(self.edges):
            d1[src, j] = -1
            d1[tgt, j] = +1

        return d1

    def _build_boundary_matrix_2(self) -> np.ndarray:
        """
        Boundary matrix ∂₂: C₂ → C₁ over ℤ.

        For triangle (v₁, v₂, v₃), ∂₂(τ) = e₁₂ + e₂₃ + e₃₁ (with signs)
        """
        if self.n_triangles == 0:
            return np.zeros((self.n_edges, 0), dtype=np.int32)

        d2 = np.zeros((self.n_edges, self.n_triangles), dtype=np.int32)

        # Map edge to index
        edge_to_idx = {}
        for i, edge in enumerate(self.edges):
            # Store both directions
            edge_to_idx[edge] = i
            edge_to_idx[(edge[1], edge[0])] = i  # Reverse

        for j, triangle in enumerate(self.triangles):
            v1, v2, v3 = triangle

            # Oriented boundary: (v1,v2) + (v2,v3) + (v3,v1)
            edges_oriented = [
                (v1, v2),
                (v2, v3),
                (v3, v1)
            ]

            for edge in edges_oriented:
                if edge in edge_to_idx:
                    idx = edge_to_idx[edge]
                    d2[idx, j] += 1
                elif (edge[1], edge[0]) in edge_to_idx:
                    idx = edge_to_idx[(edge[1], edge[0])]
                    d2[idx, j] -= 1  # Opposite orientation

        return d2

    def compute_homology(self) -> Dict:
        """
        Compute H₁(K, ℤ) with torsion.

        Returns:
            Dictionary with Betti numbers and torsion info
        """
        print(f"  Computing H₁(K, ℤ) with torsion detection...")

        d1 = self._build_boundary_matrix_1()
        d2 = self._build_boundary_matrix_2()

        print(f"    ∂₁: {d1.shape[0]} × {d1.shape[1]}")
        print(f"    ∂₂: {d2.shape[0]} × {d2.shape[1]}")

        # Compute Smith Normal Form of ∂₁
        print(f"    Computing SNF(∂₁)...")
        _, invariants_d1 = smith_normal_form(d1)
        rank_d1 = np.linalg.matrix_rank(d1)

        # Compute Smith Normal Form of ∂₂
        print(f"    Computing SNF(∂₂)...")
        _, invariants_d2 = smith_normal_form(d2)
        rank_d2 = np.linalg.matrix_rank(d2)

        # Betti numbers
        beta_0 = self.n_vertices - rank_d1
        beta_1 = self.n_edges - rank_d1 - rank_d2

        print(f"    β₀ = {beta_0}")
        print(f"    β₁ = {beta_1} (free part)")

        # Torsion subgroup
        # H₁ = ker(∂₁) / im(∂₂)
        # Torsion comes from invariants of im(∂₂) that divide into ker(∂₁)

        # Simplified: count invariant factors > 1
        torsion_invariants = [d for d in invariants_d2 if d > 1]

        has_torsion = len(torsion_invariants) > 0
        has_2_torsion = any(d == 2 or d % 2 == 0 for d in torsion_invariants)

        print(f"    Torsion invariants: {torsion_invariants if has_torsion else 'none'}")
        print(f"    Has 2-torsion: {has_2_torsion}")

        return {
            'beta_0': beta_0,
            'beta_1': beta_1,
            'rank_d1': rank_d1,
            'rank_d2': rank_d2,
            'torsion_invariants': torsion_invariants,
            'num_torsion_elements': len(torsion_invariants),
            'has_torsion': has_torsion,
            'has_2_torsion': has_2_torsion,
            'max_torsion_order': max(torsion_invariants) if torsion_invariants else 0
        }


class AdvancedObstructionDiscriminator:
    """
    Advanced obstruction discriminator with integer homology.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula

    def compute(self) -> Dict:
        """Compute advanced obstruction invariants."""
        # Import from basic version
        from obstruction_theory import SimplicialComplex

        complex = SimplicialComplex(self.formula)

        # Compute integer homology
        hom_computer = IntegerHomologyComputer(
            complex.vertices,
            complex.edges,
            complex.triangles
        )

        homology = hom_computer.compute_homology()

        return {
            **homology,
            'is_sat': self.formula.is_sat,
            'n_vertices': len(complex.vertices),
            'n_edges': len(complex.edges),
            'n_triangles': len(complex.triangles)
        }


# ============================================================================
# BATCH ANALYSIS
# ============================================================================

def analyze_advanced_obstruction(formulas: List[SATFormula]) -> Dict:
    """
    Advanced obstruction theory analysis.
    """
    print("="*80)
    print("🔬 ADVANCED OBSTRUCTION THEORY - INTEGER HOMOLOGY")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()

    results = {'sat': [], 'unsat': []}

    for i, formula in enumerate(formulas):
        print(f"[{i+1}/{len(formulas)}] {formula.filename}")

        disc = AdvancedObstructionDiscriminator(formula)
        result = disc.compute()

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        print()

    # Statistical comparison
    print("="*80)
    print("📊 STATISTICAL COMPARISON")
    print("="*80)

    metrics = [
        'beta_1',
        'num_torsion_elements',
        'max_torsion_order',
        'n_triangles'
    ]

    comparison = {}

    for metric in metrics:
        sat_vals = np.array([r[metric] for r in results['sat']])
        unsat_vals = np.array([r[metric] for r in results['unsat']])

        if len(sat_vals) >= 3 and len(unsat_vals) >= 3:
            d = compute_cohens_d(sat_vals, unsat_vals)
            t_stat, p_value = ttest_ind(sat_vals, unsat_vals)

            comparison[metric] = {
                'sat_mean': np.mean(sat_vals),
                'sat_std': np.std(sat_vals),
                'unsat_mean': np.mean(unsat_vals),
                'unsat_std': np.std(unsat_vals),
                'cohens_d': d,
                'p_value': p_value
            }

            verdict = "🏆 BREAKTHROUGH" if abs(d) > 1.25 else \
                     "⚡ LARGE" if abs(d) > 0.8 else \
                     "📊 MEDIUM" if abs(d) > 0.5 else "❌ WEAK"

            print(f"\n{metric}:")
            print(f"  SAT: {np.mean(sat_vals):.2f} ± {np.std(sat_vals):.2f}")
            print(f"  UNSAT: {np.mean(unsat_vals):.2f} ± {np.std(unsat_vals):.2f}")
            print(f"  Cohen's d: {d:.4f}  {verdict}")
            print(f"  p-value: {p_value:.2e}")

    # Binary discriminators
    sat_has_torsion = sum([r['has_torsion'] for r in results['sat']])
    unsat_has_torsion = sum([r['has_torsion'] for r in results['unsat']])

    sat_has_2torsion = sum([r['has_2_torsion'] for r in results['sat']])
    unsat_has_2torsion = sum([r['has_2_torsion'] for r in results['unsat']])

    print(f"\nhas_torsion:")
    print(f"  SAT: {sat_has_torsion}/{len(results['sat'])} ({100*sat_has_torsion/len(results['sat']):.1f}%)")
    print(f"  UNSAT: {unsat_has_torsion}/{len(results['unsat'])} ({100*unsat_has_torsion/len(results['unsat']):.1f}%)")

    print(f"\nhas_2_torsion:")
    print(f"  SAT: {sat_has_2torsion}/{len(results['sat'])} ({100*sat_has_2torsion/len(results['sat']):.1f}%)")
    print(f"  UNSAT: {unsat_has_2torsion}/{len(results['unsat'])} ({100*unsat_has_2torsion/len(results['unsat']):.1f}%)")

    print()
    print("="*80)

    return {
        'results': results,
        'comparison': comparison
    }


if __name__ == "__main__":
    print(__doc__)
