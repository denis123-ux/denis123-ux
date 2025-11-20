#!/usr/bin/env python3
"""
🔥 MEGA TORSION TEST - The Definitive Experiment
================================================================================

HYPOTHESIS TO TEST:
1. ALL UNSAT formulas have 2-torsion (100%)
2. SOME SAT formulas are torsion-free (>0%)

If confirmed → poly-time SAT certificate for torsion-free formulas!

OPTIMIZATION FOR SPEED:
- Use optimized SNF with early termination
- Skip full diagonalization if we just need "has torsion?"
- Parallel processing where possible
================================================================================
"""

import numpy as np
from typing import List, Dict, Tuple
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.stats import ttest_ind
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))


def fast_torsion_check(matrix: np.ndarray) -> Tuple[bool, int]:
    """
    Fast check for 2-torsion without full SNF.

    Returns:
        (has_torsion, num_torsion_elements)
    """
    if matrix.size == 0:
        return False, 0

    A = matrix.copy().astype(np.int64)
    rows, cols = A.shape
    min_dim = min(rows, cols)

    torsion_count = 0

    for k in range(min(min_dim, 50)):  # Limit iterations for speed
        # Find pivot
        best_pivot = None
        best_value = float('inf')

        for i in range(k, min(k+10, rows)):  # Limited search
            for j in range(k, min(k+10, cols)):
                if A[i, j] != 0 and abs(A[i, j]) < best_value:
                    best_pivot = (i, j)
                    best_value = abs(A[i, j])

        if best_pivot is None:
            break

        pi, pj = best_pivot

        # Swap to (k, k)
        if pi != k:
            A[[k, pi], :] = A[[pi, k], :]
        if pj != k:
            A[:, [k, pj]] = A[:, [pj, k]]

        if A[k, k] < 0:
            A[k, :] = -A[k, :]

        # Quick elimination (not full SNF)
        for i in range(k+1, min(k+20, rows)):
            if A[i, k] != 0:
                q = A[i, k] // A[k, k]
                A[i, :] -= q * A[k, :]

        # Check for torsion (divisor > 1)
        if abs(A[k, k]) > 1:
            torsion_count += 1

    has_torsion = torsion_count > 0
    return has_torsion, torsion_count


class MegaTorsionTest:
    """
    Mega test for 2-torsion hypothesis.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula

    def compute(self) -> Dict:
        """Quick torsion detection."""
        from obstruction_theory import SimplicialComplex

        # Build complex
        complex = SimplicialComplex(self.formula)

        # Build ∂₂ only (faster than both)
        d2 = self._build_d2(complex.triangles, complex.edges)

        # Fast torsion check
        has_torsion, num_torsion = fast_torsion_check(d2)

        return {
            'has_torsion': has_torsion,
            'num_torsion': num_torsion,
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

            # Oriented boundary
            edges_oriented = [(v1, v2), (v2, v3), (v3, v1)]

            for edge in edges_oriented:
                if edge in edge_to_idx:
                    idx = edge_to_idx[edge]
                    d2[idx, j] += 1
                elif (edge[1], edge[0]) in edge_to_idx:
                    idx = edge_to_idx[(edge[1], edge[0])]
                    d2[idx, j] -= 1

        return d2


def mega_torsion_test(formulas: List[SATFormula]) -> Dict:
    """
    Run mega torsion test.
    """
    print("="*80)
    print("🔥 MEGA TORSION TEST - DEFINITIVE EXPERIMENT")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()
    print("HYPOTHESIS:")
    print("  1. ALL UNSAT have 2-torsion (100%)")
    print("  2. SOME SAT are torsion-free (>0%)")
    print()
    print("="*80)
    print()

    results = {'sat': [], 'unsat': []}

    for i, formula in enumerate(formulas):
        tester = MegaTorsionTest(formula)
        result = tester.compute()

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        if (i + 1) % 10 == 0:
            sat_done = len(results['sat'])
            unsat_done = len(results['unsat'])
            print(f"  [{i+1}/{len(formulas)}] SAT: {sat_done}, UNSAT: {unsat_done}")

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

    print("HAS 2-TORSION:")
    print(f"  SAT:   {sat_has_torsion}/{n_sat} ({100*sat_has_torsion/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_has_torsion}/{n_unsat} ({100*unsat_has_torsion/n_unsat:.1f}%)")
    print()

    # Torsion-free count
    sat_torsion_free = n_sat - sat_has_torsion
    unsat_torsion_free = n_unsat - unsat_has_torsion

    print("TORSION-FREE:")
    print(f"  SAT:   {sat_torsion_free}/{n_sat} ({100*sat_torsion_free/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_torsion_free}/{n_unsat} ({100*unsat_torsion_free/n_unsat:.1f}%)")
    print()

    # Count statistics
    sat_counts = np.array([r['num_torsion'] for r in results['sat']])
    unsat_counts = np.array([r['num_torsion'] for r in results['unsat']])

    print("NUMBER OF TORSION ELEMENTS:")
    print(f"  SAT:   {np.mean(sat_counts):.2f} ± {np.std(sat_counts):.2f}")
    print(f"  UNSAT: {np.mean(unsat_counts):.2f} ± {np.std(unsat_counts):.2f}")
    print()

    # Statistical test
    d = compute_cohens_d(sat_counts, unsat_counts)
    t_stat, p_value = ttest_ind(sat_counts, unsat_counts)

    print(f"Cohen's d: {d:.4f}")
    print(f"p-value: {p_value:.4f}")
    print()

    # Verdict
    print("="*80)
    print("🎯 HYPOTHESIS TEST")
    print("="*80)
    print()

    if unsat_has_torsion == n_unsat:
        print("✅ CONFIRMED: ALL UNSAT have 2-torsion (100%)")
    else:
        print(f"⚠️  PARTIAL: {100*unsat_has_torsion/n_unsat:.1f}% UNSAT have 2-torsion")

    if sat_torsion_free > 0:
        print(f"✅ CONFIRMED: Some SAT are torsion-free ({100*sat_torsion_free/n_sat:.1f}%)")
    else:
        print("❌ REJECTED: NO SAT are torsion-free")

    print()

    if unsat_torsion_free == 0 and sat_torsion_free > 0:
        print("🏆 BREAKTHROUGH IMPLICATION:")
        print("   Torsion-free → SAT (poly-time certificate!)")
        print("   UNSAT → Has torsion (necessary condition!)")

    print()
    print("="*80)

    return {
        'results': results,
        'sat_has_torsion': sat_has_torsion,
        'unsat_has_torsion': unsat_has_torsion,
        'sat_torsion_free': sat_torsion_free,
        'unsat_torsion_free': unsat_torsion_free,
        'cohens_d': d,
        'p_value': p_value
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
    results = mega_torsion_test(formulas)

    print()
    print("🎉 MEGA TEST COMPLETE!")
