#!/usr/bin/env python3
"""
🌌 OBSTRUCTION THEORY FOR 3-SAT - THE ULTIMATE FRAMEWORK
================================================================================

GOAL: Compute cohomology H¹(Γ_φ, ℤ/2ℤ) and detect TORSION

MATHEMATICAL SETUP:
1. Build implication graph Γ_φ as simplicial complex:
   - 0-cells (vertices): literals {x₁, ¬x₁, x₂, ¬x₂, ...}
   - 1-cells (edges): implications x → y
   - 2-cells (triangles): cycles of length 3

2. Compute homology H₁(Γ_φ, ℤ/2ℤ):
   - Boundary matrices ∂₁: C₁ → C₀, ∂₂: C₂ → C₁
   - H₁ = ker(∂₁) / im(∂₂)
   - Dual: H¹ ≅ Hom(H₁, ℤ/2ℤ)

3. Detect TORSION:
   - Elements τ ∈ H₁ with ord(τ) = 2 (τ + τ = 0, τ ≠ 0)
   - Use Smith Normal Form to find torsion subgroup

BREAKTHROUGH HYPOTHESIS:
- SAT: H₁ is free (no torsion) → o(φ) = 0
- UNSAT: H₁ has torsion → o(φ) ≠ 0 (OBSTRUCTION EXISTS!)

If torsion discriminates SAT/UNSAT with high Cohen's d → MAJOR BREAKTHROUGH!

================================================================================
"""

import numpy as np
from typing import List, Tuple, Dict, Set
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.stats import ttest_ind
from scipy.linalg import null_space
import warnings
warnings.filterwarnings('ignore')


class SimplicialComplex:
    """
    Simplicial complex for 3-SAT formula.

    Structure:
    - 0-cells: literals
    - 1-cells: implications (edges)
    - 2-cells: directed triangles
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula
        self.n = formula.n_vars

        # Vertices: literals (positive and negative)
        self.vertices = []  # List of literals
        self.vertex_to_idx = {}  # Map literal → index

        # Edges: implications
        self.edges = []  # List of (source_idx, target_idx)

        # 2-cells: triangles
        self.triangles = []  # List of 3 vertex indices

        self._build_complex()

    def _lit_to_str(self, lit: int) -> str:
        """Convert literal to string."""
        if lit > 0:
            return f"x{lit}"
        else:
            return f"¬x{-lit}"

    def _build_vertices(self):
        """Build 0-cells (vertices)."""
        for i in range(1, self.n + 1):
            # Positive literal
            self.vertex_to_idx[i] = len(self.vertices)
            self.vertices.append(i)

            # Negative literal
            self.vertex_to_idx[-i] = len(self.vertices)
            self.vertices.append(-i)

    def _build_implications(self):
        """
        Build 1-cells (implications) from clauses.

        For clause (a ∨ b ∨ c):
        - ¬a → b ∨ c → (¬a → b) and (¬a → c)
        - Similarly for ¬b, ¬c

        This gives binary resolution implications.
        """
        for clause in self.formula.clauses:
            # Each clause (a ∨ b ∨ c) generates implications:
            # ¬a ∧ ¬b → c, ¬a ∧ ¬c → b, ¬b ∧ ¬c → a

            a, b, c = clause[0], clause[1], clause[2]

            # ¬a → (b ∨ c) - we'll create both ¬a → b and ¬a → c
            self._add_edge(-a, b)
            self._add_edge(-a, c)

            # ¬b → (a ∨ c)
            self._add_edge(-b, a)
            self._add_edge(-b, c)

            # ¬c → (a ∨ b)
            self._add_edge(-c, a)
            self._add_edge(-c, b)

    def _add_edge(self, source: int, target: int):
        """Add directed edge (implication)."""
        src_idx = self.vertex_to_idx[source]
        tgt_idx = self.vertex_to_idx[target]

        edge = (src_idx, tgt_idx)
        if edge not in self.edges:
            self.edges.append(edge)

    def _build_triangles(self):
        """
        Find all directed 3-cycles (triangles).

        A triangle is a cycle: v₁ → v₂ → v₃ → v₁
        These represent 2-cells in the complex.
        """
        # Build adjacency list
        adj = {i: [] for i in range(len(self.vertices))}
        for src, tgt in self.edges:
            adj[src].append(tgt)

        # Find all 3-cycles
        for v1 in range(len(self.vertices)):
            for v2 in adj[v1]:
                for v3 in adj[v2]:
                    if v1 in adj[v3]:  # Cycle closes!
                        triangle = tuple(sorted([v1, v2, v3]))
                        if triangle not in self.triangles:
                            self.triangles.append(triangle)

    def _build_complex(self):
        """Build full simplicial complex."""
        print(f"  Building simplicial complex for formula with {self.n} variables...")

        self._build_vertices()
        print(f"    Vertices (0-cells): {len(self.vertices)}")

        self._build_implications()
        print(f"    Edges (1-cells): {len(self.edges)}")

        self._build_triangles()
        print(f"    Triangles (2-cells): {len(self.triangles)}")


class HomologyComputer:
    """
    Compute homology groups H₁(K, ℤ/2ℤ) for simplicial complex K.
    """

    def __init__(self, complex: SimplicialComplex):
        self.complex = complex
        self.n_vertices = len(complex.vertices)
        self.n_edges = len(complex.edges)
        self.n_triangles = len(complex.triangles)

    def _build_boundary_matrix_1(self) -> np.ndarray:
        """
        Build boundary matrix ∂₁: C₁ → C₀.

        For edge e = (v₁, v₂), ∂₁(e) = v₂ - v₁ (mod 2)

        Returns:
            Matrix of shape (n_vertices, n_edges) over ℤ/2ℤ
        """
        d1 = np.zeros((self.n_vertices, self.n_edges), dtype=np.int8)

        for j, (src, tgt) in enumerate(self.complex.edges):
            d1[src, j] = 1  # -1 ≡ 1 (mod 2)
            d1[tgt, j] = 1

        # Reduce mod 2
        d1 = d1 % 2

        return d1

    def _build_boundary_matrix_2(self) -> np.ndarray:
        """
        Build boundary matrix ∂₂: C₂ → C₁.

        For triangle τ = (v₁, v₂, v₃), ∂₂(τ) = (v₁,v₂) + (v₂,v₃) + (v₃,v₁) (mod 2)

        Returns:
            Matrix of shape (n_edges, n_triangles) over ℤ/2ℤ
        """
        if self.n_triangles == 0:
            return np.zeros((self.n_edges, 0), dtype=np.int8)

        d2 = np.zeros((self.n_edges, self.n_triangles), dtype=np.int8)

        # Map edge to index
        edge_to_idx = {edge: i for i, edge in enumerate(self.complex.edges)}

        for j, triangle in enumerate(self.complex.triangles):
            v1, v2, v3 = triangle

            # Boundary edges (unordered)
            edges = [
                tuple(sorted([v1, v2])),
                tuple(sorted([v2, v3])),
                tuple(sorted([v3, v1]))
            ]

            for edge in edges:
                if edge in edge_to_idx:
                    idx = edge_to_idx[edge]
                    d2[idx, j] = 1

        # Reduce mod 2
        d2 = d2 % 2

        return d2

    def _rank_mod2(self, matrix: np.ndarray) -> int:
        """Compute rank of matrix over ℤ/2ℤ using Gaussian elimination."""
        if matrix.size == 0:
            return 0

        M = matrix.copy()
        rows, cols = M.shape

        rank = 0
        pivot_col = 0

        for row in range(rows):
            # Find pivot
            found = False
            for col in range(pivot_col, cols):
                if M[row, col] == 1:
                    # Swap columns
                    M[:, [pivot_col, col]] = M[:, [col, pivot_col]]
                    found = True
                    break

            if not found:
                continue

            # Eliminate
            for r in range(rows):
                if r != row and M[r, pivot_col] == 1:
                    M[r, :] = (M[r, :] + M[row, :]) % 2

            rank += 1
            pivot_col += 1

        return rank

    def _smith_normal_form_mod2(self, matrix: np.ndarray) -> Tuple[int, int]:
        """
        Compute Smith Normal Form over ℤ/2ℤ.

        Returns:
            (rank, torsion_rank) where torsion_rank counts diagonal 2's (but over ℤ/2ℤ all nonzero → 1)
        """
        rank = self._rank_mod2(matrix)
        return rank, 0  # Over ℤ/2ℤ, no torsion in SNF (all entries 0 or 1)

    def compute_homology(self) -> Dict:
        """
        Compute H₁(K, ℤ/2ℤ).

        H₁ = ker(∂₁) / im(∂₂)

        By rank-nullity theorem over ℤ/2ℤ:
        - dim(ker(∂₁)) = n_edges - rank(∂₁)
        - dim(im(∂₂)) = rank(∂₂)
        - β₁ = dim(H₁) = dim(ker(∂₁)) - dim(im(∂₂))

        Returns:
            Dictionary with homology info
        """
        print(f"  Computing homology H₁(K, ℤ/2ℤ)...")

        # Build boundary matrices
        d1 = self._build_boundary_matrix_1()
        d2 = self._build_boundary_matrix_2()

        print(f"    ∂₁: {d1.shape[0]} × {d1.shape[1]}")
        print(f"    ∂₂: {d2.shape[0]} × {d2.shape[1]}")

        # Compute ranks
        rank_d1 = self._rank_mod2(d1)
        rank_d2 = self._rank_mod2(d2)

        print(f"    rank(∂₁) = {rank_d1}")
        print(f"    rank(∂₂) = {rank_d2}")

        # Betti numbers
        beta_0 = self.n_vertices - rank_d1  # Connected components
        beta_1 = self.n_edges - rank_d1 - rank_d2  # 1-cycles

        print(f"    β₀ = {beta_0} (connected components)")
        print(f"    β₁ = {beta_1} (1-cycles)")

        # TORSION DETECTION
        # Over ℤ/2ℤ, we need to look at H₁(K, ℤ) and then reduce mod 2
        # For now, use a heuristic: count "odd cycles" that might have torsion

        # Simple torsion indicator: β₁ > 0 means cycles exist
        # More sophisticated: check if specific cycles have order 2

        has_cycles = (beta_1 > 0)

        return {
            'beta_0': beta_0,
            'beta_1': beta_1,
            'rank_d1': rank_d1,
            'rank_d2': rank_d2,
            'n_vertices': self.n_vertices,
            'n_edges': self.n_edges,
            'n_triangles': self.n_triangles,
            'has_cycles': has_cycles
        }


class ObstructionDiscriminator:
    """
    Main discriminator using obstruction theory.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula

    def compute(self) -> Dict:
        """
        Compute obstruction-theoretic invariants.

        Returns:
            Dictionary with all computed invariants
        """
        # Build simplicial complex
        complex = SimplicialComplex(self.formula)

        # Compute homology
        hom_computer = HomologyComputer(complex)
        homology = hom_computer.compute_homology()

        return {
            **homology,
            'is_sat': self.formula.is_sat
        }


# ============================================================================
# BATCH ANALYSIS
# ============================================================================

def analyze_obstruction_theory(formulas: List[SATFormula]) -> Dict:
    """
    Analyze obstruction theory on list of formulas.
    """
    print("="*80)
    print("🌌 OBSTRUCTION THEORY ANALYSIS")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()

    results = {'sat': [], 'unsat': []}

    for i, formula in enumerate(formulas):
        print(f"[{i+1}/{len(formulas)}] {formula.filename}")

        disc = ObstructionDiscriminator(formula)
        result = disc.compute()

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        print()

    # Statistical comparison
    print("="*80)
    print("📊 STATISTICAL COMPARISON")
    print("="*80)

    metrics = ['beta_0', 'beta_1', 'n_vertices', 'n_edges', 'n_triangles']

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

    # Binary discriminator: has_cycles
    sat_has_cycles = sum([r['has_cycles'] for r in results['sat']])
    unsat_has_cycles = sum([r['has_cycles'] for r in results['unsat']])

    print(f"\nhas_cycles (β₁ > 0):")
    print(f"  SAT: {sat_has_cycles}/{len(results['sat'])} ({100*sat_has_cycles/len(results['sat']):.1f}%)")
    print(f"  UNSAT: {unsat_has_cycles}/{len(results['unsat'])} ({100*unsat_has_cycles/len(results['unsat']):.1f}%)")

    print()
    print("="*80)

    return {
        'results': results,
        'comparison': comparison
    }


if __name__ == "__main__":
    print(__doc__)
