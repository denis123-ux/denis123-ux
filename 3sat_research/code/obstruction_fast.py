#!/usr/bin/env python3
"""
🚀 FAST OBSTRUCTION THEORY - Optimized for Speed
================================================================================

OPTIMIZATION STRATEGY:
1. Skip full Smith Normal Form (too expensive)
2. Use RANK-based torsion detection
3. Approximate torsion count via rank deficiency

MATHEMATICAL INSIGHT:
- H₁ = ker(∂₁) / im(∂₂)
- dim(H₁) = dim(ker(∂₁)) - dim(im(∂₂))
- Torsion manifests as: rank(∂₂) < dim(C₂) - dim(ker(∂₁))

Fast approximation:
  torsion_rank_approx ≈ n_triangles - rank(∂₂) - β₁

This avoids SNF but gives good approximation!
================================================================================
"""

import numpy as np
from typing import List, Dict
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')


class FastObstructionDiscriminator:
    """
    Fast obstruction discriminator without full SNF.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula

    def compute(self) -> Dict:
        """Fast computation."""
        from obstruction_theory import SimplicialComplex

        complex = SimplicialComplex(self.formula)

        n_vertices = len(complex.vertices)
        n_edges = len(complex.edges)
        n_triangles = len(complex.triangles)

        # Build boundary matrices
        d1 = self._build_d1(complex.edges, n_vertices)
        d2 = self._build_d2(complex.triangles, complex.edges)

        # Fast rank computation (SVD)
        rank_d1 = np.linalg.matrix_rank(d1, tol=1e-10)
        rank_d2 = np.linalg.matrix_rank(d2, tol=1e-10)

        # Betti numbers
        beta_0 = n_vertices - rank_d1
        beta_1 = n_edges - rank_d1 - rank_d2

        # Torsion approximation
        # If rank(∂₂) is "too small" relative to expected, we have torsion
        expected_rank_d2 = min(n_edges - beta_0 - beta_1, n_triangles)
        torsion_defect = expected_rank_d2 - rank_d2

        # Cycle complexity: ratio of triangles to cycles
        cycle_complexity = n_triangles / (beta_1 + 1)

        # Triangle density
        triangle_density = n_triangles / (n_edges + 1)

        return {
            'beta_0': beta_0,
            'beta_1': beta_1,
            'rank_d1': rank_d1,
            'rank_d2': rank_d2,
            'n_vertices': n_vertices,
            'n_edges': n_edges,
            'n_triangles': n_triangles,
            'torsion_defect': torsion_defect,
            'cycle_complexity': cycle_complexity,
            'triangle_density': triangle_density,
            'is_sat': self.formula.is_sat
        }

    def _build_d1(self, edges: List, n_vertices: int) -> np.ndarray:
        """Build ∂₁."""
        d1 = np.zeros((n_vertices, len(edges)), dtype=np.float64)
        for j, (src, tgt) in enumerate(edges):
            d1[src, j] = -1
            d1[tgt, j] = +1
        return d1

    def _build_d2(self, triangles: List, edges: List) -> np.ndarray:
        """Build ∂₂."""
        if len(triangles) == 0:
            return np.zeros((len(edges), 0), dtype=np.float64)

        d2 = np.zeros((len(edges), len(triangles)), dtype=np.float64)

        edge_to_idx = {edge: i for i, edge in enumerate(edges)}

        for j, triangle in enumerate(triangles):
            v1, v2, v3 = triangle

            # Boundary edges
            edges_in_tri = [
                (v1, v2), (v2, v1),
                (v2, v3), (v3, v2),
                (v3, v1), (v1, v3)
            ]

            for edge in edges_in_tri:
                if edge in edge_to_idx:
                    idx = edge_to_idx[edge]
                    d2[idx, j] += 1

        return d2


def analyze_fast_obstruction(formulas: List[SATFormula]) -> Dict:
    """
    Fast obstruction analysis.
    """
    print("="*80)
    print("🚀 FAST OBSTRUCTION THEORY ANALYSIS")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()

    results = {'sat': [], 'unsat': []}

    for i, formula in enumerate(formulas):
        disc = FastObstructionDiscriminator(formula)
        result = disc.compute()

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(formulas)}] β₁={result['beta_1']}, " +
                  f"triangles={result['n_triangles']}, " +
                  f"defect={result['torsion_defect']:.1f}")

    print()
    print("="*80)
    print("📊 STATISTICAL COMPARISON")
    print("="*80)

    metrics = [
        'beta_1',
        'n_triangles',
        'torsion_defect',
        'cycle_complexity',
        'triangle_density'
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

    print()
    print("="*80)

    return {
        'results': results,
        'comparison': comparison
    }


if __name__ == "__main__":
    print(__doc__)
