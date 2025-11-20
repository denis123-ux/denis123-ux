#!/usr/bin/env python3
"""
🎯 DEFINITIVE TORSION TEST - Full SNF, No Shortcuts
================================================================================

After testing all fast methods (ALL FAILED with 0% detection):
- Fast SNF with limited iterations: FAILED
- GCD-based detection: FAILED
- Rank-based approximation: FAILED
- Parallel fast SNF: FAILED

This is the DEFINITIVE test using FULL Smith Normal Form.
Accepting computational cost (~30-60 sec per formula).

HYPOTHESIS:
1. ALL UNSAT formulas have 2-torsion (100%)
2. SOME SAT formulas are torsion-free (>0%)

Sample: 50 formulas (25 SAT + 25 UNSAT)
Expected runtime: ~25-50 minutes
================================================================================
"""

import numpy as np
from typing import List, Dict
from sat_tensor_framework import parse_cnf
from scipy.stats import ttest_ind
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))

from obstruction_advanced import AdvancedObstructionDiscriminator


def definitive_torsion_test(sat_files: List, unsat_files: List):
    """
    Definitive test with FULL SNF - no shortcuts, no optimizations.
    """
    print("="*80)
    print("🎯 DEFINITIVE TORSION TEST - FULL SNF")
    print("="*80)
    print(f"SAT formulas: {len(sat_files)}")
    print(f"UNSAT formulas: {len(unsat_files)}")
    print(f"Total: {len(sat_files) + len(unsat_files)}")
    print()
    print("METHOD: Complete Smith Normal Form (no optimizations)")
    print("Expected time: ~30-60 sec per formula")
    print()
    print("HYPOTHESIS:")
    print("  1. ALL UNSAT have 2-torsion (100%)")
    print("  2. SOME SAT are torsion-free (>0%)")
    print()
    print("="*80)
    print()

    results = {'sat': [], 'unsat': []}

    # Process SAT formulas
    print("🔵 Processing SAT formulas...")
    for i, f in enumerate(sat_files):
        start = time.time()
        formula = parse_cnf(f)
        discriminator = AdvancedObstructionDiscriminator(formula)
        result = discriminator.compute()
        elapsed = time.time() - start

        results['sat'].append(result)

        torsion_str = f"torsion={result['torsion_invariants']}" if result['has_torsion'] else "torsion-free"
        print(f"  [{i+1}/{len(sat_files)}] {f.name}: {torsion_str} ({elapsed:.1f}s)")

    print()
    print("🔴 Processing UNSAT formulas...")
    for i, f in enumerate(unsat_files):
        start = time.time()
        formula = parse_cnf(f)
        discriminator = AdvancedObstructionDiscriminator(formula)
        result = discriminator.compute()
        elapsed = time.time() - start

        results['unsat'].append(result)

        torsion_str = f"torsion={result['torsion_invariants']}" if result['has_torsion'] else "torsion-free"
        print(f"  [{i+1}/{len(unsat_files)}] {f.name}: {torsion_str} ({elapsed:.1f}s)")

    print()
    print("="*80)
    print("📊 DEFINITIVE RESULTS")
    print("="*80)
    print()

    # Binary analysis - HAS ANY TORSION
    sat_has_torsion = sum(r['has_torsion'] for r in results['sat'])
    unsat_has_torsion = sum(r['has_torsion'] for r in results['unsat'])

    n_sat = len(results['sat'])
    n_unsat = len(results['unsat'])

    print("HAS ANY TORSION:")
    print(f"  SAT:   {sat_has_torsion}/{n_sat} ({100*sat_has_torsion/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_has_torsion}/{n_unsat} ({100*unsat_has_torsion/n_unsat:.1f}%)")
    print()

    # Binary analysis - HAS 2-TORSION
    sat_has_2torsion = sum(r['has_2_torsion'] for r in results['sat'])
    unsat_has_2torsion = sum(r['has_2_torsion'] for r in results['unsat'])

    print("HAS 2-TORSION:")
    print(f"  SAT:   {sat_has_2torsion}/{n_sat} ({100*sat_has_2torsion/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_has_2torsion}/{n_unsat} ({100*unsat_has_2torsion/n_unsat:.1f}%)")
    print()

    # Torsion-free count
    sat_free = n_sat - sat_has_2torsion
    unsat_free = n_unsat - unsat_has_2torsion

    print("TORSION-FREE (no 2-torsion):")
    print(f"  SAT:   {sat_free}/{n_sat} ({100*sat_free/n_sat:.1f}%)")
    print(f"  UNSAT: {unsat_free}/{n_unsat} ({100*unsat_free/n_unsat:.1f}%)")
    print()

    # Count statistics
    sat_counts = np.array([r['num_torsion_elements'] for r in results['sat']])
    unsat_counts = np.array([r['num_torsion_elements'] for r in results['unsat']])

    print("NUMBER OF TORSION ELEMENTS:")
    print(f"  SAT:   {np.mean(sat_counts):.2f} ± {np.std(sat_counts):.2f}")
    print(f"  UNSAT: {np.mean(unsat_counts):.2f} ± {np.std(unsat_counts):.2f}")
    print()

    # Statistical tests
    from sat_tensor_framework import compute_cohens_d

    # Cohen's d on counts
    d_count = compute_cohens_d(sat_counts, unsat_counts)
    t_stat, p_value = ttest_ind(sat_counts, unsat_counts)

    print(f"Cohen's d (count): {d_count:.4f}")
    print(f"p-value (count): {p_value:.4f}")
    print()

    # Binary 2-torsion (as 0/1)
    sat_binary = np.array([1 if r['has_2_torsion'] else 0 for r in results['sat']])
    unsat_binary = np.array([1 if r['has_2_torsion'] else 0 for r in results['unsat']])

    d_binary = compute_cohens_d(sat_binary, unsat_binary)
    t_stat_bin, p_value_bin = ttest_ind(sat_binary, unsat_binary)

    print(f"Cohen's d (binary 2-torsion): {d_binary:.4f}")
    print(f"p-value (binary): {p_value_bin:.4f}")
    print()

    # Examples
    print("="*80)
    print("📝 EXAMPLES")
    print("="*80)
    print()

    print("SAT TORSION-FREE:")
    sat_free_examples = [r for r in results['sat'] if not r['has_2_torsion']]
    if sat_free_examples:
        for r in sat_free_examples[:5]:
            print(f"  β₁={r['beta_1']}, torsion=[] ✅")
    else:
        print("  NONE FOUND ❌")

    print()
    print("SAT WITH 2-TORSION:")
    sat_torsion_examples = [r for r in results['sat'] if r['has_2_torsion']]
    if sat_torsion_examples:
        for r in sat_torsion_examples[:5]:
            print(f"  β₁={r['beta_1']}, torsion={r['torsion_invariants']}")

    print()
    print("UNSAT TORSION-FREE:")
    unsat_free_examples = [r for r in results['unsat'] if not r['has_2_torsion']]
    if unsat_free_examples:
        for r in unsat_free_examples[:5]:
            print(f"  β₁={r['beta_1']}, torsion=[] ⚠️")
    else:
        print("  NONE FOUND! All UNSAT have 2-torsion ✅")

    print()
    print("UNSAT WITH 2-TORSION:")
    unsat_torsion_examples = [r for r in results['unsat'] if r['has_2_torsion']]
    if unsat_torsion_examples:
        for r in unsat_torsion_examples[:5]:
            print(f"  β₁={r['beta_1']}, torsion={r['torsion_invariants']}")

    print()
    print("="*80)
    print("🎯 HYPOTHESIS VERDICT")
    print("="*80)
    print()

    # Hypothesis 1: ALL UNSAT have 2-torsion
    if unsat_has_2torsion == n_unsat:
        print("✅ HYPOTHESIS 1 CONFIRMED: ALL UNSAT have 2-torsion (100%)")
    else:
        pct = 100*unsat_has_2torsion/n_unsat
        print(f"⚠️  HYPOTHESIS 1 PARTIAL: {pct:.1f}% UNSAT have 2-torsion")
        print(f"    {unsat_free}/{n_unsat} UNSAT are torsion-free (counterexamples)")

    print()

    # Hypothesis 2: SOME SAT are torsion-free
    if sat_free > 0:
        pct = 100*sat_free/n_sat
        print(f"✅ HYPOTHESIS 2 CONFIRMED: {sat_free}/{n_sat} SAT are torsion-free ({pct:.1f}%)")
    else:
        print("❌ HYPOTHESIS 2 REJECTED: NO SAT are torsion-free")
        print("    All SAT also have 2-torsion")

    print()

    # Implication
    if unsat_free == 0 and sat_free > 0:
        print("="*80)
        print("🏆 BREAKTHROUGH IMPLICATION")
        print("="*80)
        print()
        print("DISCOVERED:")
        print("  • Torsion-free → SAT (poly-time certificate!)")
        print("  • UNSAT → Has 2-torsion (necessary condition!)")
        print()
        print(f"  {sat_free}/{n_sat} SAT formulas ({100*sat_free/n_sat:.1f}%) have fast SAT certificate!")
        print()
        print("SIGNIFICANCE:")
        print("  • Binary discriminator: d={:.4f}".format(d_binary))
        print("  • If generalizes: torsion-free detection is poly-time SAT solver")
        print("    for this subclass!")
        print()
    elif unsat_free > 0:
        print("⚠️  HYPOTHESIS REJECTED:")
        print(f"    Found {unsat_free} UNSAT formulas that are torsion-free")
        print("    2-torsion is NOT necessary for UNSAT")

    print("="*80)
    print()

    return {
        'results': results,
        'sat_has_2torsion': sat_has_2torsion,
        'unsat_has_2torsion': unsat_has_2torsion,
        'sat_free': sat_free,
        'unsat_free': unsat_free,
        'cohens_d_count': d_count,
        'cohens_d_binary': d_binary,
        'p_value_count': p_value,
        'p_value_binary': p_value_bin
    }


if __name__ == "__main__":
    print(__doc__)
    print()

    benchmark_dir = Path(__file__).parent.parent / "benchmarks"

    print("Loading formula paths...")
    sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:25]
    unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:25]

    print(f"Loaded {len(sat_files)} SAT + {len(unsat_files)} UNSAT = {len(sat_files)+len(unsat_files)} total")
    print()

    start_time = time.time()

    # RUN DEFINITIVE TEST
    results = definitive_torsion_test(sat_files, unsat_files)

    elapsed = time.time() - start_time

    print()
    print(f"🎉 DEFINITIVE TEST COMPLETE in {elapsed/60:.1f} minutes!")
    print()
