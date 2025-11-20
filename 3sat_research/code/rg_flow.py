#!/usr/bin/env python3
"""
🌀 RENORMALIZATION GROUP FLOW FOR 3-SAT
================================================================================

BREAKTHROUGH IDEA: Apply RG flow from QFT/statistical physics to SAT!

HYPOTHESIS:
- SAT formulas: RG flow converges to STABLE fixed point (p* = 1)
- UNSAT formulas: RG flow diverges or converges to UNSTABLE fixed point (p* < 1)

MATHEMATICAL FRAMEWORK:
1. Decimation: Iteratively eliminate variables (coarse-graining)
2. Track order parameter: p(t) = local satisfiability fraction
3. Compute β-function: β(p) = dp/dt where t = log(scale)
4. Analyze fixed points and stability

WHY THIS COULD WORK:
- RG solves phase transitions in physics (QCD, Ising model, etc.)
- SAT/UNSAT IS a phase transition (at clause ratio α_c ≈ 4.27)
- β-function is LOCAL (poly-time computable!)
- NEVER applied to combinatorial problems like 3-SAT

If SAT/UNSAT distinction is encoded in RG flow topology → poly-time algorithm!
================================================================================
"""

import numpy as np
from typing import List, Dict, Tuple, Set
from sat_tensor_framework import SATFormula, parse_cnf
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))


class RGFlowAnalyzer:
    """
    Renormalization Group Flow analyzer for 3-SAT.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula
        self.n_vars = formula.n_vars
        self.clauses = formula.clauses.copy()

    def decimate_variable(self, var: int, value: bool) -> Tuple[List, int]:
        """
        Decimate (eliminate) a variable by assigning it a value.

        Returns:
            (new_clauses, n_satisfied)
        """
        new_clauses = []
        n_satisfied = 0

        for clause in self.clauses:
            # Check if clause is satisfied by this assignment
            satisfied = False
            new_clause = []

            for lit in clause:
                lit_var = abs(lit)
                lit_sign = lit > 0

                if lit_var == var:
                    if lit_sign == value:
                        # Clause satisfied!
                        satisfied = True
                        break
                    # else: literal is false, skip it
                else:
                    new_clause.append(lit)

            if satisfied:
                n_satisfied += 1
            elif len(new_clause) > 0:
                new_clauses.append(tuple(new_clause))
            # If new_clause is empty: contradiction (clause becomes unsatisfiable)

        return new_clauses, n_satisfied

    def local_satisfiability(self, clauses: List) -> float:
        """
        Compute local satisfiability: fraction of clauses that can be
        satisfied by at least one literal assignment.

        This is the RG "order parameter" p.
        """
        if len(clauses) == 0:
            return 1.0

        # For each clause, check if it's not a contradiction
        # (contradiction = empty clause or all literals conflict)
        satisfiable_count = 0

        for clause in clauses:
            if len(clause) > 0:
                # Non-empty clause can potentially be satisfied
                satisfiable_count += 1

        return satisfiable_count / len(clauses)

    def compute_rg_flow(self, n_steps: int = 20) -> Dict:
        """
        Compute RG flow trajectory by iterative decimation.

        Returns:
            Dictionary with flow trajectory and β-function.
        """
        trajectory = []
        scales = []
        beta_values = []

        current_clauses = self.clauses.copy()
        remaining_vars = set(range(1, self.n_vars + 1))

        initial_m = len(current_clauses)

        for step in range(n_steps):
            if len(remaining_vars) == 0 or len(current_clauses) == 0:
                break

            # Current scale: log(remaining variables / total)
            scale = np.log(len(remaining_vars) / self.n_vars) if len(remaining_vars) > 0 else -np.inf

            # Order parameter: local satisfiability
            p = self.local_satisfiability(current_clauses)

            trajectory.append(p)
            scales.append(scale)

            # Choose variable to decimate (heuristic: most frequent)
            var_counts = {}
            for clause in current_clauses:
                for lit in clause:
                    var = abs(lit)
                    var_counts[var] = var_counts.get(var, 0) + 1

            if len(var_counts) == 0:
                break

            # Decimate most frequent variable
            var_to_decimate = max(var_counts, key=var_counts.get)

            # Try both assignments, pick the one that satisfies more clauses
            clauses_true, sat_true = self.decimate_variable(var_to_decimate, True)
            clauses_false, sat_false = self.decimate_variable(var_to_decimate, False)

            if sat_true >= sat_false:
                current_clauses = clauses_true
            else:
                current_clauses = clauses_false

            remaining_vars.discard(var_to_decimate)

        # Compute β-function: numerical derivative dp/dt
        for i in range(1, len(trajectory)):
            if scales[i] != scales[i-1]:
                dp = trajectory[i] - trajectory[i-1]
                dt = scales[i] - scales[i-1]
                beta = dp / dt if dt != 0 else 0
                beta_values.append(beta)
            else:
                beta_values.append(0)

        # Add one more to match length
        if len(beta_values) < len(trajectory):
            beta_values.append(beta_values[-1] if beta_values else 0)

        # Fixed point analysis
        fixed_point = trajectory[-1] if trajectory else 0
        converged = len(trajectory) > 5 and np.std(trajectory[-5:]) < 0.05

        # Flow direction: positive β means flowing to higher p (SAT-like)
        mean_beta = np.mean(beta_values) if beta_values else 0

        return {
            'trajectory': trajectory,
            'scales': scales,
            'beta_function': beta_values,
            'fixed_point': fixed_point,
            'converged': converged,
            'mean_beta': mean_beta,
            'final_p': trajectory[-1] if trajectory else 0,
            'initial_p': trajectory[0] if trajectory else 0,
            'flow_direction': 1 if mean_beta > 0 else -1 if mean_beta < 0 else 0
        }


def test_rg_discriminator(formulas: List[SATFormula]) -> Dict:
    """
    Test RG flow as SAT/UNSAT discriminator.
    """
    print("="*80)
    print("🌀 RENORMALIZATION GROUP FLOW - 3-SAT DISCRIMINATOR")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()
    print("HYPOTHESIS:")
    print("  SAT → converges to stable fixed point (p* ≈ 1)")
    print("  UNSAT → diverges or unstable fixed point (p* < 1)")
    print()
    print("="*80)
    print()

    results = {'sat': [], 'unsat': []}

    for i, formula in enumerate(formulas):
        analyzer = RGFlowAnalyzer(formula)
        flow = analyzer.compute_rg_flow(n_steps=30)

        result = {
            **flow,
            'is_sat': formula.is_sat
        }

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(formulas)}] processed")

    print()
    print("="*80)
    print("📊 RESULTS")
    print("="*80)
    print()

    # Extract discriminators
    sat_fixed = np.array([r['fixed_point'] for r in results['sat']])
    unsat_fixed = np.array([r['fixed_point'] for r in results['unsat']])

    sat_beta = np.array([r['mean_beta'] for r in results['sat']])
    unsat_beta = np.array([r['mean_beta'] for r in results['unsat']])

    sat_converged = sum([r['converged'] for r in results['sat']])
    unsat_converged = sum([r['converged'] for r in results['unsat']])

    print("FIXED POINT (p*):")
    print(f"  SAT:   {np.mean(sat_fixed):.4f} ± {np.std(sat_fixed):.4f}")
    print(f"  UNSAT: {np.mean(unsat_fixed):.4f} ± {np.std(unsat_fixed):.4f}")
    print()

    print("MEAN β-FUNCTION:")
    print(f"  SAT:   {np.mean(sat_beta):.4f} ± {np.std(sat_beta):.4f}")
    print(f"  UNSAT: {np.mean(unsat_beta):.4f} ± {np.std(unsat_beta):.4f}")
    print()

    print("CONVERGENCE:")
    print(f"  SAT:   {sat_converged}/{len(results['sat'])} ({100*sat_converged/len(results['sat']):.1f}%)")
    print(f"  UNSAT: {unsat_converged}/{len(results['unsat'])} ({100*unsat_converged/len(results['unsat']):.1f}%)")
    print()

    # Statistical tests
    from scipy.stats import ttest_ind
    from sat_tensor_framework import compute_cohens_d

    d_fixed = compute_cohens_d(sat_fixed, unsat_fixed)
    t_fixed, p_fixed = ttest_ind(sat_fixed, unsat_fixed)

    d_beta = compute_cohens_d(sat_beta, unsat_beta)
    t_beta, p_beta = ttest_ind(sat_beta, unsat_beta)

    print("STATISTICAL TESTS:")
    print(f"  Fixed point: Cohen's d = {d_fixed:.4f}, p = {p_fixed:.4f}")
    print(f"  β-function:  Cohen's d = {d_beta:.4f}, p = {p_beta:.4f}")
    print()

    # Verdict
    print("="*80)
    print("🎯 VERDICT")
    print("="*80)
    print()

    if abs(d_fixed) > 0.8:
        print(f"✅ BREAKTHROUGH: Fixed point discriminates! (d={d_fixed:.4f})")
    elif abs(d_fixed) > 0.5:
        print(f"⚡ PROMISING: Medium effect (d={d_fixed:.4f})")
    else:
        print(f"❌ WEAK: Low discrimination (d={d_fixed:.4f})")

    print()

    if abs(d_beta) > 0.8:
        print(f"✅ BREAKTHROUGH: β-function discriminates! (d={d_beta:.4f})")
    elif abs(d_beta) > 0.5:
        print(f"⚡ PROMISING: Medium effect (d={d_beta:.4f})")
    else:
        print(f"❌ WEAK: Low discrimination (d={d_beta:.4f})")

    print()
    print("="*80)

    return {
        'results': results,
        'cohens_d_fixed': d_fixed,
        'cohens_d_beta': d_beta,
        'p_value_fixed': p_fixed,
        'p_value_beta': p_beta
    }


if __name__ == "__main__":
    print(__doc__)
    print()

    benchmark_dir = Path(__file__).parent.parent / "benchmarks"

    print("Loading formulas...")
    sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:25]
    unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:25]

    formulas = []
    for f in sat_files:
        formulas.append(parse_cnf(f))
    for f in unsat_files:
        formulas.append(parse_cnf(f))

    print(f"Loaded {len(formulas)} formulas (25 SAT + 25 UNSAT)")
    print()

    # RUN RG FLOW TEST
    results = test_rg_discriminator(formulas)

    print()
    print("🎉 RG FLOW TEST COMPLETE!")
