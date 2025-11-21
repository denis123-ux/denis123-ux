"""
===============================================================================
                    EXTENDED STRESS TEST
                    ====================

    Testing at LARGER scales to find where things break.
    Also testing Information Geometry approach.
===============================================================================
"""

import numpy as np
import random
import time
import sys

sys.path.insert(0, '/home/user/denis123-ux')

from symplectic_sat_solver import (
    SATFormula, Clause as SymplecticClause,
    SymplecticSATSolver
)

from holographic_sat import (
    CNFFormula, Clause as HoloClause, Literal,
    holographic_sat_solve
)


def convert_to_symplectic(n: int, clause_list) -> SATFormula:
    clauses = [SymplecticClause(c) for c in clause_list]
    return SATFormula(n, clauses)


def generate_definitely_sat(n: int, m: int, seed: int = None):
    """Generate SAT formula with known solution"""
    if seed:
        random.seed(seed)

    solution = [random.choice([0, 1]) for _ in range(n)]
    clauses = []

    for _ in range(m):
        vars = random.sample(range(n), 3)
        lits = []

        for v in vars:
            if random.random() > 0.3:
                if solution[v] == 1:
                    lits.append(v + 1)
                else:
                    lits.append(-(v + 1))
            else:
                lits.append((v + 1) if random.random() > 0.5 else -(v + 1))

        satisfied = False
        for lit in lits:
            idx = abs(lit) - 1
            if (lit > 0 and solution[idx] == 1) or (lit < 0 and solution[idx] == 0):
                satisfied = True
                break

        if not satisfied:
            idx = random.choice(vars)
            if solution[idx] == 1:
                lits[vars.index(idx)] = idx + 1
            else:
                lits[vars.index(idx)] = -(idx + 1)

        clauses.append(lits)

    return clauses, solution


def generate_hard_3sat(n: int, ratio: float = 4.27, seed: int = None):
    if seed:
        random.seed(seed)

    m = int(n * ratio)
    clauses = []

    for _ in range(m):
        vars = random.sample(range(1, n+1), 3)
        lits = [v if random.random() > 0.5 else -v for v in vars]
        clauses.append(lits)

    return clauses


# ============================================================================
# TEST 1: SYMPLECTIC LARGE SCALE
# ============================================================================

def test_symplectic_large_scale():
    """Test symplectic at larger scales"""
    print("\n" + "="*80)
    print("TEST 1: SYMPLECTIC LARGE SCALE TEST")
    print("="*80)

    sizes = [10, 15, 20, 25, 30]
    results = []

    for n in sizes:
        print(f"\n--- n = {n} ---")

        m = int(3 * n)
        times = []
        successes = 0
        n_trials = 3

        for trial in range(n_trials):
            clauses, known_sol = generate_definitely_sat(n, m, seed=100*n + trial)
            formula = convert_to_symplectic(n, clauses)

            solver = SymplecticSATSolver(formula, embedding_degree=2)

            start = time.time()
            solution = solver.solve(
                n_attempts=5,
                T=100.0,
                dt=0.01,
                gamma=0.5,
                verbose=False
            )
            elapsed = time.time() - start
            times.append(elapsed)

            if solution is not None and formula.verify_boolean(solution):
                successes += 1

        avg_time = np.mean(times)
        success_rate = successes / n_trials

        results.append({
            'n': n,
            'avg_time': avg_time,
            'success_rate': success_rate
        })

        print(f"  Avg time: {avg_time:.2f}s")
        print(f"  Success rate: {success_rate*100:.1f}%")

    # Scaling analysis
    print("\n" + "-"*60)
    print("SCALING ANALYSIS:")

    ns = np.array([r['n'] for r in results])
    ts = np.array([r['avg_time'] for r in results])

    if len(ns) >= 2 and all(t > 0 for t in ts):
        log_ns = np.log(ns)
        log_ts = np.log(ts + 1e-10)
        coeffs = np.polyfit(log_ns, log_ts, 1)
        k = coeffs[0]

        print(f"  Time scaling exponent: k = {k:.2f}")
        print(f"  Expected time at n=100: ~{np.exp(coeffs[1]) * (100**k):.0f}s")

        if k < 3:
            print("  VERDICT: Polynomial time (potential P=NP evidence!)")
        elif k < 5:
            print("  VERDICT: High polynomial (concerning)")
        else:
            print("  VERDICT: Likely super-polynomial")

    return results


# ============================================================================
# TEST 2: SYMPLECTIC HARD PHASE TRANSITION
# ============================================================================

def test_symplectic_phase_transition():
    """Test at phase transition for various sizes"""
    print("\n" + "="*80)
    print("TEST 2: SYMPLECTIC PHASE TRANSITION TEST (ratio=4.27)")
    print("="*80)

    sizes = [5, 8, 10, 12, 15, 18, 20]
    results = []

    for n in sizes:
        print(f"\n--- n = {n}, m = {int(4.27*n)} ---")

        successes = 0
        n_trials = 5

        for trial in range(n_trials):
            clauses = generate_hard_3sat(n, ratio=4.27, seed=200*n + trial)
            formula = convert_to_symplectic(n, clauses)

            solver = SymplecticSATSolver(formula, embedding_degree=2)
            solution = solver.solve(
                n_attempts=10,
                T=150,
                dt=0.01,
                gamma=0.3,
                verbose=False
            )

            if solution is not None and formula.verify_boolean(solution):
                successes += 1

        success_rate = successes / n_trials
        results.append({'n': n, 'success_rate': success_rate})
        print(f"  Success rate: {success_rate*100:.1f}%")

    print("\n" + "-"*60)
    print("SUCCESS RATE TREND:")

    for r in results:
        bar = "#" * int(r['success_rate'] * 20)
        print(f"  n={r['n']:2d}: {bar:20s} {r['success_rate']*100:.0f}%")

    # Critical analysis
    rates = [r['success_rate'] for r in results]
    if rates[-1] < 0.3:
        print("\n  CRITICAL: Success rate drops below 30% at large n")
        print("  This suggests EXPONENTIAL basin shrinkage!")
    elif rates[-1] > 0.7:
        print("\n  PROMISING: Success rate stays above 70%")
        print("  This is consistent with polynomial algorithm!")

    return results


# ============================================================================
# TEST 3: INFORMATION GEOMETRY
# ============================================================================

def test_information_geometry():
    """Test information geometry approach"""
    print("\n" + "="*80)
    print("TEST 3: INFORMATION GEOMETRY TEST")
    print("="*80)

    try:
        from approaches.information_geometry import InformationGeometryAnalyzer
    except Exception as e:
        print(f"  Could not import Information Geometry module: {e}")
        print("  Skipping this test...")
        return None

    # Test on synthetic frequency distributions
    print("\n--- Testing Fisher metric properties ---")

    # Generate random frequency distributions
    for n in [5, 10, 20]:
        # Random normalized frequencies
        freqs = np.random.rand(n)
        freqs = freqs / np.sum(freqs)

        analyzer = InformationGeometryAnalyzer(freqs)

        print(f"\n  n = {n}:")
        print(f"    Max frequency: {np.max(freqs):.4f}")
        print(f"    Scalar curvature: {analyzer.ricci_curvature_scalar():.4f}")
        print(f"    Mean sectional curvature: {analyzer.mean_curvature():.4f}")
        print(f"    Shannon entropy: {analyzer.entropy_connection():.4f}")

    # Test curvature-frequency correlation
    print("\n--- Curvature-Frequency Correlation Test ---")

    curvatures = []
    max_freqs = []

    for trial in range(100):
        n = random.randint(5, 20)
        freqs = np.random.rand(n)
        freqs = freqs / np.sum(freqs)

        analyzer = InformationGeometryAnalyzer(freqs)
        curvatures.append(analyzer.ricci_curvature_scalar())
        max_freqs.append(np.max(freqs))

    correlation = np.corrcoef(curvatures, max_freqs)[0, 1]
    print(f"  Correlation (curvature, max_freq): {correlation:.4f}")

    if abs(correlation) > 0.3:
        print("  SIGNIFICANT correlation found!")
        print("  This supports the information-geometric hypothesis")
    else:
        print("  Weak correlation - theory needs refinement")

    return {'correlation': correlation}


# ============================================================================
# TEST 4: COMPARISON AT FIXED SIZE
# ============================================================================

def comparison_test():
    """Side-by-side comparison at fixed size"""
    print("\n" + "="*80)
    print("TEST 4: DIRECT COMPARISON (n=12)")
    print("="*80)

    n = 12
    n_tests = 20

    sym_solved = 0
    sym_correct = 0
    sym_times = []

    print("\nRunning tests...")

    for test_id in range(n_tests):
        clauses, known_sol = generate_definitely_sat(n, int(3*n), seed=300 + test_id)

        # Symplectic
        formula_sym = convert_to_symplectic(n, clauses)
        solver = SymplecticSATSolver(formula_sym, embedding_degree=2)

        start = time.time()
        sol = solver.solve(n_attempts=3, T=50, verbose=False)
        elapsed = time.time() - start
        sym_times.append(elapsed)

        if sol is not None:
            sym_solved += 1
            if formula_sym.verify_boolean(sol):
                sym_correct += 1

        print(f"  Test {test_id+1}/{n_tests}: Sym solved={sol is not None}, correct={formula_sym.verify_boolean(sol) if sol is not None else 'N/A'}")

    print("\n" + "-"*60)
    print("RESULTS:")
    print(f"  SYMPLECTIC:")
    print(f"    Solved: {sym_solved}/{n_tests} ({sym_solved/n_tests*100:.1f}%)")
    print(f"    Correct: {sym_correct}/{n_tests} ({sym_correct/n_tests*100:.1f}%)")
    print(f"    Avg time: {np.mean(sym_times):.3f}s")


# ============================================================================
# TEST 5: WORST CASE SEARCH
# ============================================================================

def find_worst_case():
    """Search for worst-case instances"""
    print("\n" + "="*80)
    print("TEST 5: WORST CASE SEARCH")
    print("="*80)

    worst_n = 0
    worst_time = 0
    worst_seed = 0

    for n in [10, 12, 15]:
        print(f"\n--- Searching at n={n} ---")

        for seed in range(50):
            clauses = generate_hard_3sat(n, ratio=4.27, seed=400 + n*100 + seed)
            formula = convert_to_symplectic(n, clauses)

            solver = SymplecticSATSolver(formula, embedding_degree=2)

            start = time.time()
            solution = solver.solve(n_attempts=5, T=100, verbose=False)
            elapsed = time.time() - start

            if elapsed > worst_time:
                worst_time = elapsed
                worst_n = n
                worst_seed = seed
                success = solution is not None and formula.verify_boolean(solution)
                print(f"  New worst: n={n}, seed={seed}, time={elapsed:.2f}s, solved={success}")

    print("\n" + "-"*60)
    print(f"WORST CASE FOUND:")
    print(f"  n={worst_n}, seed={worst_seed}")
    print(f"  Time: {worst_time:.2f}s")

    return {'n': worst_n, 'seed': worst_seed, 'time': worst_time}


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║                    EXTENDED STRESS TEST SUITE                            ║
    ║                                                                          ║
    ║  Testing limits of P=NP approaches at larger scales                      ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)

    results = {}

    # Run tests
    results['large_scale'] = test_symplectic_large_scale()
    results['phase_transition'] = test_symplectic_phase_transition()
    results['info_geo'] = test_information_geometry()
    results['comparison'] = comparison_test()
    results['worst_case'] = find_worst_case()

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                         EXTENDED TEST RESULTS                            ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)

    if results.get('large_scale'):
        last = results['large_scale'][-1]
        print(f"  Large Scale (n={last['n']}): {last['success_rate']*100:.0f}% success, {last['avg_time']:.1f}s avg")

    if results.get('phase_transition'):
        last = results['phase_transition'][-1]
        print(f"  Phase Transition (n={last['n']}): {last['success_rate']*100:.0f}% success")

    if results.get('worst_case'):
        wc = results['worst_case']
        print(f"  Worst Case: n={wc['n']}, time={wc['time']:.1f}s")

    return results


if __name__ == "__main__":
    main()
