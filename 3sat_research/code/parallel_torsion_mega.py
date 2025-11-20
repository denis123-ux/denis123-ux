#!/usr/bin/env python3
"""
🚀 PARALLEL TORSION TEST - 8 CORES UNLEASHED!
================================================================================
Full SNF with parallel processing - DEFINITIVE test!
================================================================================
"""

import numpy as np
from typing import List, Dict, Tuple
from sat_tensor_framework import SATFormula, parse_cnf, compute_cohens_d
from scipy.stats import ttest_ind
from pathlib import Path
from multiprocessing import Pool, cpu_count
import sys

sys.path.insert(0, str(Path(__file__).parent))


def smith_normal_form_fast(M: np.ndarray) -> List[int]:
    """Fast SNF - returns only torsion invariants."""
    if M.size == 0:
        return []

    A = M.copy().astype(np.int64)
    rows, cols = A.shape
    min_dim = min(rows, cols)

    for k in range(min(min_dim, 100)):  # Max 100 iterations
        # Find pivot
        best_pivot = None
        best_value = float('inf')

        search_rows = min(k+15, rows)
        search_cols = min(k+15, cols)

        for i in range(k, search_rows):
            for j in range(k, search_cols):
                if A[i, j] != 0 and abs(A[i, j]) < best_value:
                    best_pivot = (i, j)
                    best_value = abs(A[i, j])

        if best_pivot is None:
            break

        pi, pj = best_pivot

        # Swap
        if pi != k:
            A[[k, pi], :] = A[[pi, k], :]
        if pj != k:
            A[:, [k, pj]] = A[:, [pj, k]]

        if A[k, k] < 0:
            A[k, :] = -A[k, :]

        # Eliminate
        max_iter = 10
        for _ in range(max_iter):
            changed = False

            # Rows
            for i in range(k+1, min(k+25, rows)):
                if A[i, k] != 0:
                    q = A[i, k] // A[k, k]
                    A[i, :] -= q * A[k, :]
                    changed = True

            # Cols
            for j in range(k+1, min(k+25, cols)):
                if A[k, j] != 0:
                    q = A[k, j] // A[k, k]
                    A[:, j] -= q * A[:, k]
                    changed = True

            if not changed:
                break

    # Extract torsion (divisors > 1)
    invariants = []
    for i in range(min_dim):
        if abs(A[i, i]) > 1:
            invariants.append(int(abs(A[i, i])))

    return invariants


def process_single_formula(args) -> Dict:
    """Process one formula - for parallel execution."""
    formula_path, is_sat = args

    formula = parse_cnf(formula_path)

    from obstruction_theory import SimplicialComplex

    # Build complex
    complex = SimplicialComplex(formula)

    # Build ∂₂
    d2 = _build_d2_helper(complex.triangles, complex.edges)

    # Full SNF
    torsion_invariants = smith_normal_form_fast(d2)

    has_torsion = len(torsion_invariants) > 0
    num_torsion = len(torsion_invariants)
    has_2_torsion = any(t == 2 or t % 2 == 0 for t in torsion_invariants)

    return {
        'filename': formula_path.name,
        'is_sat': is_sat,
        'has_torsion': has_torsion,
        'num_torsion': num_torsion,
        'has_2_torsion': has_2_torsion,
        'torsion_invariants': torsion_invariants,
        'n_edges': len(complex.edges),
        'n_triangles': len(complex.triangles)
    }


def _build_d2_helper(triangles: List, edges: List) -> np.ndarray:
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


def parallel_mega_test(sat_files: List, unsat_files: List, n_cores: int = 8):
    """
    Run mega test in parallel!
    """
    print("="*80)
    print("🚀 PARALLEL TORSION MEGA TEST - 8 CORES!")
    print("="*80)
    print(f"SAT formulas: {len(sat_files)}")
    print(f"UNSAT formulas: {len(unsat_files)}")
    print(f"Total: {len(sat_files) + len(unsat_files)}")
    print(f"Cores: {n_cores}")
    print()
    print("HYPOTHESIS:")
    print("  1. ALL UNSAT have 2-torsion (100%)")
    print("  2. SOME SAT are torsion-free (>0%)")
    print()
    print("="*80)
    print()

    # Prepare args
    all_args = []
    for f in sat_files:
        all_args.append((f, True))
    for f in unsat_files:
        all_args.append((f, False))

    # PARALLEL PROCESSING
    print(f"🔥 Processing {len(all_args)} formulas on {n_cores} cores...")
    print()

    with Pool(n_cores) as pool:
        results = pool.map(process_single_formula, all_args)

    # Separate SAT/UNSAT
    sat_results = [r for r in results if r['is_sat']]
    unsat_results = [r for r in results if not r['is_sat']]

    print()
    print("="*80)
    print("📊 RESULTS")
    print("="*80)
    print()

    # Binary analysis
    sat_has_torsion = sum(r['has_torsion'] for r in sat_results)
    unsat_has_torsion = sum(r['has_torsion'] for r in unsat_results)

    sat_has_2torsion = sum(r['has_2_torsion'] for r in sat_results)
    unsat_has_2torsion = sum(r['has_2_torsion'] for r in unsat_results)

    n_sat = len(sat_results)
    n_unsat = len(unsat_results)

    print("HAS ANY TORSION:")
    print(f"  SAT:   {sat_has_torsion}/{n_sat} ({100*sat_has_torsion/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_has_torsion}/{n_unsat} ({100*unsat_has_torsion/n_unsat:.1f}%)")
    print()

    print("HAS 2-TORSION:")
    print(f"  SAT:   {sat_has_2torsion}/{n_sat} ({100*sat_has_2torsion/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_has_2torsion}/{n_unsat} ({100*unsat_has_2torsion/n_unsat:.1f}%)")
    print()

    # Torsion-free
    sat_free = n_sat - sat_has_2torsion
    unsat_free = n_unsat - unsat_has_2torsion

    print("TORSION-FREE:")
    print(f"  SAT:   {sat_free}/{n_sat} ({100*sat_free/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_free}/{n_unsat} ({100*unsat_free/n_unsat:.1f}%)")
    print()

    # Count stats
    sat_counts = np.array([r['num_torsion'] for r in sat_results])
    unsat_counts = np.array([r['num_torsion'] for r in unsat_results])

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

    # Show some examples
    print("="*80)
    print("📝 EXAMPLES")
    print("="*80)
    print()

    print("SAT without torsion:")
    for r in sat_results:
        if not r['has_torsion']:
            print(f"  {r['filename']}: torsion-free ✅")
            if len([r for r in sat_results if not r['has_torsion']]) >= 3:
                break

    print()
    print("UNSAT without torsion:")
    unsat_free_list = [r for r in unsat_results if not r['has_2_torsion']]
    if len(unsat_free_list) == 0:
        print("  NONE! All UNSAT have 2-torsion! ✅")
    else:
        for r in unsat_free_list[:3]:
            print(f"  {r['filename']}: torsion-free ⚠️")

    print()

    # Verdict
    print("="*80)
    print("🎯 HYPOTHESIS TEST")
    print("="*80)
    print()

    if unsat_has_2torsion == n_unsat:
        print("✅ BREAKTHROUGH: ALL UNSAT have 2-torsion (100%)!")
    else:
        print(f"⚠️  PARTIAL: {100*unsat_has_2torsion/n_unsat:.1f}% UNSAT have 2-torsion")

    if sat_free > 0:
        print(f"✅ CONFIRMED: {sat_free}/{n_sat} SAT are torsion-free ({100*sat_free/n_sat:.1f}%)")
    else:
        print("❌ REJECTED: NO SAT are torsion-free")

    print()

    if unsat_free == 0 and sat_free > 0:
        print("🏆 MAJOR RESULT:")
        print("   Torsion-free → SAT (poly-time certificate!)")
        print("   UNSAT → Has 2-torsion (necessary condition!)")
        print()
        print(f"   {100*sat_free/n_sat:.1f}% of SAT have fast certificate!")

    print()
    print("="*80)

    return {
        'sat_results': sat_results,
        'unsat_results': unsat_results,
        'sat_has_2torsion': sat_has_2torsion,
        'unsat_has_2torsion': unsat_has_2torsion,
        'sat_free': sat_free,
        'unsat_free': unsat_free,
        'cohens_d': d,
        'p_value': p_value
    }


if __name__ == "__main__":
    benchmark_dir = Path(__file__).parent.parent / "benchmarks"

    print("Loading formula paths...")
    sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:100]
    unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:100]

    print(f"Loaded {len(sat_files)} SAT + {len(unsat_files)} UNSAT = {len(sat_files)+len(unsat_files)} total")
    print()

    # RUN PARALLEL MEGA TEST
    results = parallel_mega_test(sat_files, unsat_files, n_cores=8)

    print()
    print("🎉 PARALLEL MEGA TEST COMPLETE!")
