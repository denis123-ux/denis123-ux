#!/usr/bin/env python3
"""
🚀 FULL ANALYSIS: 2000 3-SAT INSTANCES
================================================================================
Run ALL discriminators on 1000 SAT + 1000 UNSAT instances.
Goal: Find discriminator with Cohen's d > 1.25 (beat lm_mean_depth baseline)
================================================================================
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict
import time
import json
from sat_tensor_framework import (
    parse_cnf, SATFormula, TensorNetworkDiscriminator,
    FractionalDerivativeDiscriminator, HolonomicGradientDiscriminator,
    compute_cohens_d
)
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# LOCAL MINIMA DEPTH DISCRIMINATOR (BASELINE d=1.25)
# ============================================================================

def compute_lm_mean_depth(formula: SATFormula, n_descents: int = 25) -> float:
    """
    Compute mean depth of local minima (BASELINE from mega-doc).

    Algorithm:
    1. Random start
    2. Greedy descent (1-flip steepest improvement)
    3. Record depth = violations at local minimum
    4. Repeat n_descents times
    5. Return mean depth

    SAT: shallow minima (depth ≈ 4)
    UNSAT: deep minima (depth ≈ 9)

    Returns:
        Mean depth across all descents
    """
    depths = []

    for trial in range(n_descents):
        # Random start
        state = np.random.randint(0, 2, size=formula.n_vars)
        current_violations = count_violations(formula, state)

        # Greedy descent
        max_iterations = 200
        for iteration in range(max_iterations):
            improved = False

            for var in range(formula.n_vars):
                # Flip variable
                state[var] = 1 - state[var]
                new_violations = count_violations(formula, state)

                if new_violations < current_violations:
                    current_violations = new_violations
                    improved = True
                    break

                # Undo flip
                state[var] = 1 - state[var]

            if not improved or current_violations == 0:
                break

        depths.append(current_violations)

    return float(np.mean(depths))


def count_violations(formula: SATFormula, assignment: np.ndarray) -> int:
    """Count violated clauses."""
    violations = 0
    for clause in formula.clauses:
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


# ============================================================================
# FULL PIPELINE
# ============================================================================

def analyze_single_formula(formula: SATFormula, idx: int, total: int) -> Dict:
    """
    Analyze single formula with ALL discriminators.

    Returns:
        Dictionary with all metrics
    """
    print(f"[{idx+1}/{total}] {formula.filename} (n={formula.n_vars}, m={formula.n_clauses})", end=' ')

    result = {
        'filename': formula.filename,
        'n_vars': formula.n_vars,
        'n_clauses': formula.n_clauses,
        'is_sat': formula.is_sat
    }

    # 1. BASELINE: lm_mean_depth (d=1.25 from mega-doc)
    start = time.time()
    try:
        depth = compute_lm_mean_depth(formula, n_descents=25)
        result['lm_mean_depth'] = depth
        result['lm_time'] = time.time() - start
        print(f"depth={depth:.2f}", end=' ')
    except Exception as e:
        result['lm_mean_depth'] = np.nan
        result['lm_time'] = time.time() - start
        print(f"depth=ERR", end=' ')

    # 2. FRACTIONAL DERIVATIVE (quick)
    start = time.time()
    try:
        fd = FractionalDerivativeDiscriminator(formula)
        # Fast version: test only α=1.5 (midpoint between gradient and Hessian)
        frac_val = fd.compute_fractional_derivative(alpha=1.5)
        result['fractional_derivative_1.5'] = frac_val
        result['frac_time'] = time.time() - start
        print(f"frac={frac_val:.3f}", end=' ')
    except Exception as e:
        result['fractional_derivative_1.5'] = np.nan
        result['frac_time'] = time.time() - start
        print(f"frac=ERR", end=' ')

    # 3. HOLONOMIC GRADIENT (medium speed)
    start = time.time()
    try:
        hg = HolonomicGradientDiscriminator(formula)
        holonomy = hg.compute_holonomy(n_loops=3)  # Reduce loops for speed
        result['holonomy'] = holonomy
        result['holonomy_time'] = time.time() - start
        print(f"hol={holonomy:.3f}", end=' ')
    except Exception as e:
        result['holonomy'] = np.nan
        result['holonomy_time'] = time.time() - start
        print(f"hol=ERR", end=' ')

    # 4. TENSOR NETWORK (skip for now - too expensive and not discriminating)
    # result['bond_dimension'] = np.nan
    # result['tensor_time'] = 0.0

    print(f"✓ ({sum([result.get(k, 0) for k in ['lm_time', 'frac_time', 'holonomy_time']]):.1f}s)")

    return result


def run_full_analysis(benchmark_dir: Path, max_instances: int = None):
    """
    Run analysis on all SAT and UNSAT instances.

    Args:
        benchmark_dir: Path to benchmarks
        max_instances: Max instances per class (None = all)
    """
    # Collect files
    sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))
    unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))

    if max_instances:
        sat_files = sat_files[:max_instances]
        unsat_files = unsat_files[:max_instances]

    all_files = sat_files + unsat_files
    total = len(all_files)

    print(f"="*80)
    print(f"🚀 FULL ANALYSIS: {len(sat_files)} SAT + {len(unsat_files)} UNSAT = {total} total")
    print(f"="*80)

    results = []
    start_time = time.time()

    for idx, filepath in enumerate(all_files):
        try:
            formula = parse_cnf(filepath)
            result = analyze_single_formula(formula, idx, total)
            results.append(result)

            # Checkpoint every 100
            if (idx + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (idx + 1) / elapsed
                remaining = (total - idx - 1) / rate
                print(f"\n⏱️  Progress: {idx+1}/{total} ({100*(idx+1)/total:.1f}%) | "
                      f"Rate: {rate:.1f} inst/s | ETA: {remaining/60:.1f} min\n")

                # Save checkpoint
                df = pd.DataFrame(results)
                df.to_csv(benchmark_dir.parent / "results" / "checkpoint.csv", index=False)

        except Exception as e:
            print(f"\n❌ ERROR on {filepath.name}: {e}\n")
            continue

    # Final save
    elapsed = time.time() - start_time
    df = pd.DataFrame(results)
    output_file = benchmark_dir.parent / "results" / "full_analysis.csv"
    df.to_csv(output_file, index=False)

    print(f"\n{'='*80}")
    print(f"✅ Analysis complete!")
    print(f"⏱️  Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    print(f"📊 Rate: {total/elapsed:.2f} instances/second")
    print(f"💾 Results saved to: {output_file}")
    print(f"{'='*80}\n")

    return df


def compute_statistics(df: pd.DataFrame):
    """
    Compute Cohen's d and statistical tests for all discriminators.
    """
    print(f"\n{'='*80}")
    print(f"📊 STATISTICAL ANALYSIS")
    print(f"{'='*80}\n")

    sat_df = df[df['is_sat'] == True]
    unsat_df = df[df['is_sat'] == False]

    discriminators = [
        'lm_mean_depth',
        'fractional_derivative_1.5',
        'holonomy'
    ]

    results = []

    for disc in discriminators:
        sat_vals = sat_df[disc].dropna().values
        unsat_vals = unsat_df[disc].dropna().values

        if len(sat_vals) < 10 or len(unsat_vals) < 10:
            print(f"{disc}: INSUFFICIENT DATA\n")
            continue

        # Compute statistics
        mean_sat = np.mean(sat_vals)
        mean_unsat = np.mean(unsat_vals)
        std_sat = np.std(sat_vals, ddof=1)
        std_unsat = np.std(unsat_vals, ddof=1)

        cohens_d = compute_cohens_d(sat_vals, unsat_vals)
        t_stat, p_value = ttest_ind(sat_vals, unsat_vals)

        # Determine verdict
        if abs(cohens_d) < 0.2:
            verdict = "FAIL (negligible)"
        elif abs(cohens_d) < 0.5:
            verdict = "WEAK"
        elif abs(cohens_d) < 0.8:
            verdict = "MEDIUM"
        elif abs(cohens_d) < 1.0:
            verdict = "LARGE"
        elif abs(cohens_d) < 1.25:
            verdict = "VERY LARGE"
        else:
            verdict = "🏆 BREAKTHROUGH (d > 1.25)!"

        results.append({
            'discriminator': disc,
            'mean_sat': mean_sat,
            'mean_unsat': mean_unsat,
            'std_sat': std_sat,
            'std_unsat': std_unsat,
            'cohens_d': cohens_d,
            'p_value': p_value,
            'verdict': verdict
        })

        print(f"{disc}:")
        print(f"  SAT:    {mean_sat:.4f} ± {std_sat:.4f}")
        print(f"  UNSAT:  {mean_unsat:.4f} ± {std_unsat:.4f}")
        print(f"  Cohen's d: {cohens_d:.4f}")
        print(f"  p-value: {p_value:.2e}")
        print(f"  VERDICT: {verdict}\n")

    # Save statistics
    stats_df = pd.DataFrame(results)
    stats_file = df.attrs.get('output_dir', Path('.')) / "statistics.json"
    stats_df.to_json(stats_file, orient='records', indent=2)

    print(f"{'='*80}\n")

    return stats_df


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    benchmark_dir = Path("/home/user/denis123-ux/3sat_research/benchmarks")
    results_dir = benchmark_dir.parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Parse args
    if len(sys.argv) > 1:
        max_instances = int(sys.argv[1])
        print(f"🔧 Running in TEST MODE: {max_instances} instances per class\n")
    else:
        max_instances = None
        print(f"🚀 Running in FULL MODE: ALL instances\n")

    # Run analysis
    df = run_full_analysis(benchmark_dir, max_instances=max_instances)
    df.attrs['output_dir'] = results_dir

    # Compute statistics
    stats = compute_statistics(df)

    print(f"✅ DONE! Check {results_dir} for results.")
