#!/usr/bin/env python3
"""
🌀 RG FLOW V2 - ENERGY LANDSCAPE
================================================================================

V1 FAILED: All formulas converged to p*=1.0 (too simple!)

V2 IDEA: Use ENERGY as order parameter!

Order parameter: E(t) = fraction of UNSATISFIED clauses under greedy assignment

RG flow on ENERGY LANDSCAPE:
- SAT → Energy flows to E* = 0 (ground state exists!)
- UNSAT → Energy stuck at E* > 0 (frustrated, no ground state!)

This is the CORRECT physical analogy:
- SAT = material with ground state
- UNSAT = spin glass (frustration prevents ground state)

β-function: β(E) = dE/dt measures how energy evolves with scale!
================================================================================
"""

import numpy as np
from typing import List, Dict, Tuple
from sat_tensor_framework import SATFormula, parse_cnf
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))


class EnergyRGAnalyzer:
    """
    Energy-based RG flow analyzer.
    """

    def __init__(self, formula: SATFormula):
        self.formula = formula
        self.n_vars = formula.n_vars
        self.clauses = formula.clauses.copy()

    def greedy_energy(self, clauses: List, remaining_vars: set) -> float:
        """
        Compute energy = fraction of unsatisfied clauses under greedy assignment.

        Greedy: for each variable, choose value that satisfies most clauses.
        """
        if len(clauses) == 0:
            return 0.0

        # Try random assignment on remaining variables
        assignment = {}
        for var in remaining_vars:
            # Count how many clauses prefer True vs False
            true_benefit = 0
            false_benefit = 0

            for clause in clauses:
                has_true = var in [lit for lit in clause if lit > 0]
                has_false = -var in clause

                if has_true:
                    true_benefit += 1
                if has_false:
                    false_benefit += 1

            # Greedy choice
            assignment[var] = true_benefit >= false_benefit

        # Count unsatisfied clauses
        unsatisfied = 0
        for clause in clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                sign = lit > 0

                if var in assignment and assignment[var] == sign:
                    satisfied = True
                    break

            if not satisfied:
                unsatisfied += 1

        return unsatisfied / len(clauses)

    def decimate_variable(self, var: int, value: bool) -> List:
        """Decimate variable, return simplified clauses."""
        new_clauses = []

        for clause in self.clauses:
            satisfied = False
            new_clause = []

            for lit in clause:
                lit_var = abs(lit)
                lit_sign = lit > 0

                if lit_var == var:
                    if lit_sign == value:
                        satisfied = True
                        break
                else:
                    new_clause.append(lit)

            if not satisfied and len(new_clause) > 0:
                new_clauses.append(tuple(new_clause))

        return new_clauses

    def compute_energy_flow(self, n_steps: int = 30) -> Dict:
        """
        Compute RG flow on ENERGY landscape.
        """
        energy_trajectory = []
        scales = []

        current_clauses = self.clauses.copy()
        remaining_vars = set(range(1, self.n_vars + 1))

        for step in range(n_steps):
            if len(remaining_vars) == 0:
                break

            # Scale: fraction of remaining variables
            scale = len(remaining_vars) / self.n_vars

            # Energy: fraction unsatisfied under greedy
            energy = self.greedy_energy(current_clauses, remaining_vars)

            energy_trajectory.append(energy)
            scales.append(scale)

            # Choose variable to decimate (most frequent)
            var_counts = {}
            for clause in current_clauses:
                for lit in clause:
                    var = abs(lit)
                    if var in remaining_vars:
                        var_counts[var] = var_counts.get(var, 0) + 1

            if len(var_counts) == 0:
                break

            var_to_decimate = max(var_counts, key=var_counts.get)

            # Try both assignments, pick lower energy
            clauses_true = self.decimate_variable(var_to_decimate, True)
            clauses_false = self.decimate_variable(var_to_decimate, False)

            remaining_after = remaining_vars - {var_to_decimate}

            energy_true = self.greedy_energy(clauses_true, remaining_after)
            energy_false = self.greedy_energy(clauses_false, remaining_after)

            if energy_true <= energy_false:
                current_clauses = clauses_true
                self.clauses = clauses_true
            else:
                current_clauses = clauses_false
                self.clauses = clauses_false

            remaining_vars = remaining_after

        # β-function: dE/dt (t = log scale)
        beta_values = []
        for i in range(1, len(energy_trajectory)):
            if scales[i] > 0 and scales[i-1] > 0:
                dE = energy_trajectory[i] - energy_trajectory[i-1]
                dt = np.log(scales[i]) - np.log(scales[i-1])
                beta = dE / dt if dt != 0 else 0
                beta_values.append(beta)

        if len(beta_values) < len(energy_trajectory):
            beta_values.append(beta_values[-1] if beta_values else 0)

        # Fixed point = final energy
        fixed_point_energy = energy_trajectory[-1] if energy_trajectory else 1.0

        # Converged to ground state?
        ground_state = fixed_point_energy < 0.01

        return {
            'energy_trajectory': energy_trajectory,
            'scales': scales,
            'beta_function': beta_values,
            'fixed_point_energy': fixed_point_energy,
            'ground_state_reached': ground_state,
            'mean_beta': np.mean(beta_values) if beta_values else 0,
            'initial_energy': energy_trajectory[0] if energy_trajectory else 1.0,
            'energy_drop': energy_trajectory[0] - fixed_point_energy if energy_trajectory else 0
        }


def test_energy_rg(formulas: List[SATFormula]) -> Dict:
    """Test energy-based RG flow."""
    print("="*80)
    print("🌀 RG FLOW V2 - ENERGY LANDSCAPE")
    print("="*80)
    print(f"Formulas: {len(formulas)}")
    print()
    print("HYPOTHESIS:")
    print("  SAT → Energy flows to E* = 0 (ground state!)")
    print("  UNSAT → Energy stuck at E* > 0 (frustrated!)")
    print()
    print("="*80)
    print()

    results = {'sat': [], 'unsat': []}

    for i, formula in enumerate(formulas):
        analyzer = EnergyRGAnalyzer(formula)
        flow = analyzer.compute_energy_flow(n_steps=40)

        result = {**flow, 'is_sat': formula.is_sat}

        key = 'sat' if formula.is_sat else 'unsat'
        results[key].append(result)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(formulas)}] processed")

    print()
    print("="*80)
    print("📊 RESULTS")
    print("="*80)
    print()

    # Extract metrics
    sat_E = np.array([r['fixed_point_energy'] for r in results['sat']])
    unsat_E = np.array([r['fixed_point_energy'] for r in results['unsat']])

    sat_ground = sum([r['ground_state_reached'] for r in results['sat']])
    unsat_ground = sum([r['ground_state_reached'] for r in results['unsat']])

    sat_beta = np.array([r['mean_beta'] for r in results['sat']])
    unsat_beta = np.array([r['mean_beta'] for r in results['unsat']])

    print("FIXED POINT ENERGY (E*):")
    print(f"  SAT:   {np.mean(sat_E):.4f} ± {np.std(sat_E):.4f}")
    print(f"  UNSAT: {np.mean(unsat_E):.4f} ± {np.std(unsat_E):.4f}")
    print()

    print("GROUND STATE REACHED (E* < 0.01):")
    print(f"  SAT:   {sat_ground}/{len(results['sat'])} ({100*sat_ground/len(results['sat']):.1f}%)")
    print(f"  UNSAT: {unsat_ground}/{len(results['unsat'])} ({100*unsat_ground/len(results['unsat']):.1f}%)")
    print()

    print("MEAN β-FUNCTION:")
    print(f"  SAT:   {np.mean(sat_beta):.4f} ± {np.std(sat_beta):.4f}")
    print(f"  UNSAT: {np.mean(unsat_beta):.4f} ± {np.std(unsat_beta):.4f}")
    print()

    # Statistical tests
    from scipy.stats import ttest_ind
    from sat_tensor_framework import compute_cohens_d

    d_energy = compute_cohens_d(sat_E, unsat_E)
    t_energy, p_energy = ttest_ind(sat_E, unsat_E)

    d_beta = compute_cohens_d(sat_beta, unsat_beta)

    print("STATISTICAL TESTS:")
    print(f"  Energy E*: Cohen's d = {d_energy:.4f}, p = {p_energy:.4f}")
    print(f"  β-function: Cohen's d = {d_beta:.4f}")
    print()

    # Verdict
    print("="*80)
    print("🎯 VERDICT")
    print("="*80)
    print()

    if abs(d_energy) > 1.25:
        print(f"🏆 BREAKTHROUGH: Energy discriminates! (d={d_energy:.4f})")
    elif abs(d_energy) > 0.8:
        print(f"✅ LARGE EFFECT: Strong discrimination (d={d_energy:.4f})")
    elif abs(d_energy) > 0.5:
        print(f"⚡ MEDIUM EFFECT: Promising (d={d_energy:.4f})")
    else:
        print(f"❌ WEAK: Low discrimination (d={d_energy:.4f})")

    print()
    print("="*80)

    return {
        'results': results,
        'cohens_d_energy': d_energy,
        'cohens_d_beta': d_beta,
        'p_value': p_energy
    }


if __name__ == "__main__":
    print(__doc__)
    print()

    benchmark_dir = Path(__file__).parent.parent / "benchmarks"

    sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:25]
    unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:25]

    formulas = []
    for f in sat_files:
        formulas.append(parse_cnf(f))
    for f in unsat_files:
        formulas.append(parse_cnf(f))

    print(f"Loaded {len(formulas)} formulas")
    print()

    results = test_energy_rg(formulas)

    print()
    print("🎉 ENERGY RG TEST COMPLETE!")
