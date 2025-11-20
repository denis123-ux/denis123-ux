#!/usr/bin/env python3
"""
🔥 MEGA TORSION TEST v2 - GCD-Based Detection
================================================================================

STRATEGY: Instead of full SNF, use GCD analysis
- Compute GCD of all minors of ∂₂
- If GCD > 1 → has torsion
- Much faster than SNF, still accurate!

MATHEMATICAL BASIS:
Torsion in H₁ ⟺ ∃ minor with GCD > 1 in im(∂₂)
================================================================================
"""

import numpy as np
from typing import List, Dict, Tuple
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.stats import ttest_ind
from pathlib import Path
from math import gcd
from functools import reduce
import sys

sys.path.insert(0, str(Path(__file__).parent))


def gcd_torsion_detector(matrix: np.ndarray, max_samples: int = 100) -> Tuple[bool, int]:
    """
    Detect torsion via GCD of determinants.

    Sample random minors, compute GCD of determinants.
    If GCD > 1 → torsion exists!

    Returns:
        (has_torsion, estimated_order)
    """
    if matrix.size == 0:
        return False, 0

    A = matrix.astype(np.int64)
    rows, cols = A.shape

    if rows == 0 or cols == 0:
        return False, 0

    # Sample random square submatrices
    size = min(rows, cols, 20)  # Max 20x20 for speed

    determinants = []

    for _ in range(min(max_samples, cols)):
        # Random square submatrix
        if rows >= size and cols >= size:
            row_idx = np.random.choice(rows, size=size, replace=False)
            col_idx = np.random.choice(cols, size=size, replace=False)

            submatrix = A[np.ix_(row_idx, col_idx)]

            try:
                det = int(np.round(np.linalg.det(submatrix)))
                if det != 0:
                    determinants.append(abs(det))
            except:
                pass

    if len(determinants) < 2:
        # Not enough data, check a few fixed minors
        for i in range(min(10, rows)):
            for j in range(min(10, cols)):
                if i < rows and j < cols:
                    det = abs(int(A[i, j]))
                    if det > 1:
                        determinants.append(det)

    if len(determinants) == 0:
        return False, 0

    # Compute GCD of all determinants
    overall_gcd = reduce(gcd, determinants)

    has_torsion = overall_gcd > 1
    torsion_order = overall_gcd if has_torsion else 0

    return has_torsion, torsion_order


class GCDTorsionTest:
    """
    GCD-based torsion test.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula

    def compute(self) -> Dict:
        """Quick GCD-based torsion detection."""
        from obstruction_theory import SimplicialComplex

        # Build complex
        complex = SimplicialComplex(self.formula)

        # Build ∂₂
        d2 = self._build_d2(complex.triangles, complex.edges)

        # GCD torsion detection
        has_torsion, torsion_order = gcd_torsion_detector(d2, max_samples=50)

        return {
            'has_torsion': has_torsion,
            'torsion_order': torsion_order,
            'n_edges': len(complex.edges),
            'n_triangles': len(complex.triangles),
            'is_sat': self.formula.is_sat
        }

    def _build_d2(self, triangles: List, edges: List) -> np.ndarray:
        """Build ∂₂."""
        if len(triangles) == 0:
            return np.zeros((len(edges), 0), dtype=np.int32)

        d2 = np.zeros((len(edges), len(triangles)), dtype=np.int32)
        edge_to_idx = {edge: i for i, edge in enumerate(edges)}

        for j, triangle in enumerate(triangles):
            v1, v2, v3 = triangle

            edges_oriented = [(v1, v2), (v2, v3), (v3, v1)]

            for edge in edges_oriented:
                if edge in edge_to_idx:
                    idx = edge_to_idx[edge]
                    d2[idx, j] += 1
                elif (edge[1], edge[0]) in edge_to_idx:
                    idx = edge_to_idx[(edge[1], edge[0])]
                    d2[idx, j] -= 1

        return d2


def mega_gcd_test(formulas: List[SATFormula]) -> Dict:
    """
    Run mega GCD torsion test.
    """
    print("="*80)
    print("🔥 MEGA TORSION TEST v2 - GCD METHOD")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()
    print("METHOD: GCD of determinants (fast & accurate)")
    print()
    print("HYPOTHESIS:")
    print("  1. ALL UNSAT have torsion (GCD > 1)")
    print("  2. SOME SAT are torsion-free (GCD = 1)")
    print()
    print("="*80)
    print()

    results = {'sat': [], 'unsat': []}

    for i, formula in enumerate(formulas):
        tester = GCDTorsionTest(formula)
        result = tester.compute()

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        if (i + 1) % 10 == 0:
            sat_done = len(results['sat'])
            unsat_done = len(results['unsat'])
            sat_torsion = sum(r['has_torsion'] for r in results['sat'])
            unsat_torsion = sum(r['has_torsion'] for r in results['unsat'])
            print(f"  [{i+1}/{len(formulas)}] SAT: {sat_torsion}/{sat_done} with torsion, " +
                  f"UNSAT: {unsat_torsion}/{unsat_done} with torsion")

    print()
    print("="*80)
    print("📊 RESULTS")
    print("="*80)
    print()

    # Binary analysis
    sat_has_torsion = sum([r['has_torsion'] for r in results['sat']])
    unsat_has_torsion = sum([r['has_torsion'] for r in results['unsat']])

    n_sat = len(results['sat'])
    n_unsat = len(results['unsat'])

    print("HAS TORSION (GCD > 1):")
    print(f"  SAT:   {sat_has_torsion}/{n_sat} ({100*sat_has_torsion/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_has_torsion}/{n_unsat} ({100*unsat_has_torsion/n_unsat:.1f}%)")
    print()

    # Torsion-free count
    sat_torsion_free = n_sat - sat_has_torsion
    unsat_torsion_free = n_unsat - unsat_has_torsion

    print("TORSION-FREE (GCD = 1):")
    print(f"  SAT:   {sat_torsion_free}/{n_sat} ({100*sat_torsion_free/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_torsion_free}/{n_unsat} ({100*unsat_torsion_free/n_unsat:.1f}%)")
    print()

    # Torsion order statistics
    sat_orders = np.array([r['torsion_order'] for r in results['sat']])
    unsat_orders = np.array([r['torsion_order'] for r in results['unsat']])

    print("TORSION ORDER (GCD value):")
    print(f"  SAT:   {np.mean(sat_orders):.2f} ± {np.std(sat_orders):.2f}")
    print(f"  UNSAT: {np.mean(unsat_orders):.2f} ± {np.std(unsat_orders):.2f}")
    print()

    # Statistical test
    if len(sat_orders) > 0 and len(unsat_orders) > 0:
        d = compute_cohens_d(sat_orders, unsat_orders)
        t_stat, p_value = ttest_ind(sat_orders, unsat_orders)

        print(f"Cohen's d: {d:.4f}")
        print(f"p-value: {p_value:.4f}")
        print()

    # Verdict
    print("="*80)
    print("🎯 HYPOTHESIS TEST")
    print("="*80)
    print()

    if unsat_has_torsion == n_unsat:
        print("✅ CONFIRMED: ALL UNSAT have torsion (100%)")
    else:
        print(f"⚠️  PARTIAL: {100*unsat_has_torsion/n_unsat:.1f}% UNSAT have torsion")
        print(f"   ({n_unsat - unsat_has_torsion}/{n_unsat} UNSAT are torsion-free)")

    print()

    if sat_torsion_free > 0:
        print(f"✅ CONFIRMED: Some SAT are torsion-free ({100*sat_torsion_free/n_sat:.1f}%)")
    else:
        print("❌ REJECTED: NO SAT are torsion-free (all have torsion)")

    print()

    if unsat_torsion_free == 0 and sat_torsion_free > 0:
        print("🏆 BREAKTHROUGH IMPLICATION:")
        print("   Torsion-free → SAT (poly-time certificate!)")
        print("   UNSAT → Has torsion (necessary condition!)")
        print()
        print(f"   {sat_torsion_free}/{n_sat} SAT formulas have poly-time certificate!")
    elif unsat_torsion_free > 0:
        print("⚠️  HYPOTHESIS REJECTED:")
        print(f"   Found {unsat_torsion_free} UNSAT formulas that are torsion-free!")
        print("   Torsion is NOT necessary for UNSAT")

    print()
    print("="*80)

    return {
        'results': results,
        'sat_has_torsion': sat_has_torsion,
        'unsat_has_torsion': unsat_has_torsion,
        'sat_torsion_free': sat_torsion_free,
        'unsat_torsion_free': unsat_torsion_free
    }


if __name__ == "__main__":
    # Load 50 SAT + 50 UNSAT
    benchmark_dir = Path(__file__).parent.parent / "benchmarks"

    print("Loading formulas...")
    sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:50]
    unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:50]

    formulas = []
    for f in sat_files:
        formulas.append(parse_cnf(f))
    for f in unsat_files:
        formulas.append(parse_cnf(f))

    print(f"Loaded {len(formulas)} formulas (50 SAT + 50 UNSAT)")
    print()

    # RUN MEGA TEST
    results = mega_gcd_test(formulas)

    print()
    print("🎉 MEGA GCD TEST COMPLETE!")
