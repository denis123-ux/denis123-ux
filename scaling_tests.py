"""
🔬 SCALING TESTS: La Verità su Polynomial vs Exponential

Test rigorosi per determinare se l'approccio scala davvero.
"""

import random
import math
import time


# ============================================================================
# IMPORT FROM SIMPLE DEMO
# ============================================================================

class Clause:
    def __init__(self, literals):
        self.literals = literals

    def evaluate_continuous(self, x):
        product = 1.0
        for lit in self.literals:
            if lit > 0:
                val = x[abs(lit) - 1]
            else:
                val = 1.0 - x[abs(lit) - 1]
            product *= (1.0 - val)
        return 1.0 - product

    def penalty(self, x):
        satisfaction = self.evaluate_continuous(x)
        return (1.0 - satisfaction) ** 2

    def verify_boolean(self, x_bool):
        for lit in self.literals:
            idx = abs(lit) - 1
            if lit > 0 and x_bool[idx] == 1:
                return True
            if lit < 0 and x_bool[idx] == 0:
                return True
        return False


class SATFormula:
    def __init__(self, n_vars, clauses):
        self.n_vars = n_vars
        self.clauses = clauses

    def energy(self, x):
        return sum(clause.penalty(x) for clause in self.clauses)

    def gradient_numerical(self, x, eps=1e-7):
        E_x = self.energy(x)
        grad = []
        for i in range(self.n_vars):
            x_plus = x[:]
            x_plus[i] += eps
            E_plus = self.energy(x_plus)
            grad.append((E_plus - E_x) / eps)
        return grad

    def verify_boolean(self, x_bool):
        return all(clause.verify_boolean(x_bool) for clause in self.clauses)


def clip(x, min_val=0.0, max_val=1.0):
    return max(min_val, min(max_val, x))


def vector_norm(v):
    return math.sqrt(sum(x**2 for x in v))


# ============================================================================
# FORMULA GENERATORS
# ============================================================================

def generate_random_3sat(n, m, seed=None):
    """
    Genera random 3-SAT formula

    Args:
        n: numero variabili
        m: numero clausole
        seed: random seed for reproducibility

    Returns:
        SATFormula
    """
    if seed is not None:
        random.seed(seed)

    clauses = []
    for _ in range(m):
        # Scegli 3 variabili random (no duplicates)
        vars_chosen = random.sample(range(1, n+1), 3)
        # Randomizza segni
        literals = []
        for v in vars_chosen:
            if random.random() > 0.5:
                literals.append(v)
            else:
                literals.append(-v)
        clauses.append(Clause(literals))

    return SATFormula(n, clauses)


def generate_2sat(n, m, seed=None):
    """Genera random 2-SAT (sempre SAT se m/n < 1)"""
    if seed is not None:
        random.seed(seed)

    clauses = []
    for _ in range(m):
        vars_chosen = random.sample(range(1, n+1), 2)
        literals = []
        for v in vars_chosen:
            if random.random() > 0.5:
                literals.append(v)
            else:
                literals.append(-v)
        clauses.append(Clause(literals))

    return SATFormula(n, clauses)


def generate_planted_sat(n, m, seed=None):
    """
    Genera SAT con soluzione planted

    Garantisce SAT (conosciamo soluzione)
    """
    if seed is not None:
        random.seed(seed)

    # Genera soluzione random
    solution = [random.randint(0, 1) for _ in range(n)]

    clauses = []
    for _ in range(m):
        # Scegli 3 variabili
        vars_chosen = random.sample(range(1, n+1), 3)

        # Assicura che almeno un letterale sia soddisfatto da solution
        literals = []
        for v in vars_chosen:
            # Con prob 0.7 usa segno che soddisfa solution
            if random.random() < 0.7:
                if solution[v-1] == 1:
                    literals.append(v)
                else:
                    literals.append(-v)
            else:
                if random.random() > 0.5:
                    literals.append(v)
                else:
                    literals.append(-v)

        clauses.append(Clause(literals))

    return SATFormula(n, clauses), solution


def generate_unsat_formula(n):
    """
    Genera formula UNSAT semplice

    Example: x ∧ ¬x (impossibile)
    """
    clauses = [
        Clause([1]),   # x₁
        Clause([-1])   # ¬x₁
    ]
    return SATFormula(n, clauses)


# ============================================================================
# ENHANCED SOLVER CON METRICS
# ============================================================================

def symplectic_solve_with_metrics(
    formula,
    T=100.0,
    dt=0.01,
    gamma=0.5,
    verbose=False,
    max_steps=None
):
    """
    Solve con tracking dettagliato di metrics

    Returns:
        {
            'success': bool,
            'x_final': list,
            'energy_final': float,
            'iterations': int,
            'time_seconds': float,
            'energy_history': list,
            'converged_to_zero': bool
        }
    """
    n = formula.n_vars

    # Initialize
    x = [random.random() for _ in range(n)]
    y = [0.0 for _ in range(n)]

    energy_history = []
    n_steps = int(T / dt)
    if max_steps:
        n_steps = min(n_steps, max_steps)

    start_time = time.time()

    for step in range(n_steps):
        # Gradient
        grad = formula.gradient_numerical(x)

        # Update
        for i in range(n):
            y[i] = y[i] - dt * grad[i] - gamma * dt * y[i]
            x[i] = x[i] + dt * y[i]
            x[i] = clip(x[i], 0.0, 1.0)

        # Energy
        E = formula.energy(x)
        energy_history.append(E)

        # Early stopping
        if E < 1e-6:
            break

    end_time = time.time()

    final_energy = energy_history[-1] if energy_history else float('inf')

    return {
        'success': final_energy < 1e-4,
        'x_final': x,
        'energy_final': final_energy,
        'iterations': step + 1,
        'time_seconds': end_time - start_time,
        'energy_history': energy_history,
        'converged_to_zero': final_energy < 1e-6
    }


# ============================================================================
# SCALING ANALYSIS
# ============================================================================

def test_scaling(sizes=[3, 5, 10, 15, 20], attempts_per_size=5):
    """
    Test scaling con diverse dimensioni

    Critical question: iterations ∝ n^k o ∝ 2^n?
    """
    print("\n" + "="*70)
    print("🔬 SCALING TEST: Polynomial vs Exponential")
    print("="*70)

    results = {}

    for n in sizes:
        print(f"\n{'─'*70}")
        print(f"📊 Testing n = {n} variables")
        print(f"{'─'*70}")

        # Clausole: ratio 4.27 (near critical threshold for 3-SAT)
        m = int(4.27 * n)

        iteration_counts = []
        success_counts = 0
        times = []

        for attempt in range(attempts_per_size):
            # Generate formula
            formula = generate_random_3sat(n, m, seed=100*n + attempt)

            # Solve
            result = symplectic_solve_with_metrics(
                formula,
                T=200.0,
                dt=0.01,
                gamma=0.5,
                verbose=False,
                max_steps=20000  # safety limit
            )

            iteration_counts.append(result['iterations'])
            times.append(result['time_seconds'])
            if result['success']:
                success_counts += 1

            print(f"  Attempt {attempt+1}: {result['iterations']:5d} iters, "
                  f"E={result['energy_final']:.2e}, "
                  f"{'✓' if result['success'] else '✗'}")

        # Statistics
        avg_iters = sum(iteration_counts) / len(iteration_counts)
        avg_time = sum(times) / len(times)
        success_rate = success_counts / attempts_per_size

        results[n] = {
            'avg_iterations': avg_iters,
            'avg_time': avg_time,
            'success_rate': success_rate,
            'all_iterations': iteration_counts
        }

        print(f"\n  📈 Statistics:")
        print(f"     Average iterations: {avg_iters:.1f}")
        print(f"     Average time: {avg_time:.3f}s")
        print(f"     Success rate: {success_rate:.1%}")

    # Analyze scaling
    print("\n" + "="*70)
    print("📊 SCALING ANALYSIS")
    print("="*70)

    print("\n  Size | Avg Iters | Time (s) | Success")
    print("  " + "─"*45)
    for n in sizes:
        r = results[n]
        print(f"  {n:4d} | {r['avg_iterations']:9.1f} | {r['avg_time']:8.3f} | {r['success_rate']:6.1%}")

    # Fit polynomial vs exponential
    print("\n  🔍 Scaling Pattern Analysis:")

    if len(sizes) >= 3:
        # Check if iterations ∝ n^k
        n1, n2 = sizes[0], sizes[-1]
        i1, i2 = results[n1]['avg_iterations'], results[n2]['avg_iterations']

        # If polynomial: i2/i1 ≈ (n2/n1)^k
        # Solve for k: k = log(i2/i1) / log(n2/n1)
        if i1 > 0:
            k_poly = math.log(i2 / i1) / math.log(n2 / n1)
            print(f"     If polynomial O(n^k): k ≈ {k_poly:.2f}")

        # If exponential: i2/i1 ≈ c^(n2-n1)
        # Solve for c: c = (i2/i1)^(1/(n2-n1))
        if i1 > 0 and n2 > n1:
            c_exp = (i2 / i1) ** (1.0 / (n2 - n1))
            print(f"     If exponential O(c^n): c ≈ {c_exp:.3f}")

            # Predictions
            print(f"\n     📈 Predictions for n=100:")
            pred_poly = i1 * (100.0 / n1) ** k_poly
            pred_exp = i1 * (c_exp ** (100 - n1))
            print(f"        Polynomial model: {pred_poly:,.0f} iterations")
            print(f"        Exponential model: {pred_exp:.2e} iterations")

            # Verdict
            print(f"\n     ⚖️  VERDICT:")
            if k_poly < 3.0:
                print(f"        🟢 PROMISING! Scaling looks polynomial (k={k_poly:.2f})")
            elif k_poly < 5.0:
                print(f"        🟡 MAYBE. Scaling is polynomial but high degree (k={k_poly:.2f})")
            else:
                print(f"        🔴 CONCERNING. Scaling might be too steep (k={k_poly:.2f})")

            if c_exp < 1.1:
                print(f"        🟢 GOOD! No strong exponential trend (c={c_exp:.3f})")
            elif c_exp < 1.3:
                print(f"        🟡 CAUTION. Possible exponential component (c={c_exp:.3f})")
            else:
                print(f"        🔴 BAD! Clear exponential scaling (c={c_exp:.3f})")

    return results


# ============================================================================
# ROUNDING GAP TEST
# ============================================================================

def test_rounding_gap():
    """
    Test se continuous solutions round correttamente
    """
    print("\n" + "="*70)
    print("🔍 ROUNDING GAP TEST")
    print("="*70)

    n_tests = 20
    rounding_failures = 0
    partial_convergence = 0

    for i in range(n_tests):
        # Generate small formula
        n = 5
        m = 10
        formula = generate_random_3sat(n, m, seed=200+i)

        # Solve
        result = symplectic_solve_with_metrics(formula, T=50, verbose=False)

        if result['energy_final'] < 0.01:  # "converged"
            x_continuous = result['x_final']
            x_boolean = [1 if x >= 0.5 else 0 for x in x_continuous]

            # Check if rounded solution is valid
            if formula.verify_boolean(x_boolean):
                # Success!
                pass
            else:
                # Rounding failed!
                rounding_failures += 1
                print(f"\n  ⚠️  Test {i+1}: ROUNDING FAILURE")
                print(f"     Continuous: {[f'{x:.2f}' for x in x_continuous]}")
                print(f"     Rounded:    {x_boolean}")
                print(f"     Energy (continuous): {result['energy_final']:.6f}")
                print(f"     Energy (rounded): {formula.energy([float(b) for b in x_boolean]):.6f}")

        elif result['energy_final'] < 0.1:
            partial_convergence += 1

    print(f"\n  📊 Results:")
    print(f"     Total tests: {n_tests}")
    print(f"     Rounding failures: {rounding_failures}")
    print(f"     Partial convergence: {partial_convergence}")

    if rounding_failures > 0:
        print(f"\n  🔴 WARNING: Rounding gap exists in {rounding_failures}/{n_tests} cases!")
    else:
        print(f"\n  🟢 GOOD: No rounding failures detected")


# ============================================================================
# UNSAT DETECTION TEST
# ============================================================================

def test_unsat_detection():
    """
    Test behavior on UNSAT formulas
    """
    print("\n" + "="*70)
    print("🔍 UNSAT DETECTION TEST")
    print("="*70)

    # Test 1: Simple contradiction
    print("\n  Test 1: Simple contradiction (x ∧ ¬x)")
    formula = generate_unsat_formula(1)

    result = symplectic_solve_with_metrics(formula, T=50, verbose=False)

    print(f"     Final energy: {result['energy_final']:.6f}")
    print(f"     Converged to E=0? {result['converged_to_zero']}")
    print(f"     Iterations: {result['iterations']}")

    if result['energy_final'] > 0.1:
        print(f"     ✓ Correctly did NOT converge to 0 (UNSAT detected)")
    else:
        print(f"     ✗ WARNING: Converged to near-0 on UNSAT formula!")

    # Test 2: More complex UNSAT
    print("\n  Test 2: Over-constrained formula")
    # Create formula with contradictory clauses
    clauses = [
        Clause([1, 2]),
        Clause([-1, 2]),
        Clause([1, -2]),
        Clause([-1, -2])  # All 4 combinations of 2 vars - UNSAT!
    ]
    formula = SATFormula(2, clauses)

    result = symplectic_solve_with_metrics(formula, T=100, verbose=False)

    print(f"     Final energy: {result['energy_final']:.6f}")
    print(f"     Converged to E=0? {result['converged_to_zero']}")

    if result['energy_final'] > 0.1:
        print(f"     ✓ Correctly identified as UNSAT")
    else:
        print(f"     ✗ WARNING: False convergence!")


# ============================================================================
# PLANTED SOLUTION TEST
# ============================================================================

def test_planted_solution():
    """
    Test on formulas with known solutions
    """
    print("\n" + "="*70)
    print("🔍 PLANTED SOLUTION TEST")
    print("="*70)

    sizes = [5, 10, 15]
    for n in sizes:
        m = int(4 * n)  # Many clauses
        formula, true_solution = generate_planted_sat(n, m, seed=300)

        print(f"\n  Testing n={n}, m={m}")
        print(f"  True solution: {true_solution}")

        result = symplectic_solve_with_metrics(formula, T=100, verbose=False)

        x_bool = [1 if x >= 0.5 else 0 for x in result['x_final']]

        print(f"  Found solution: {x_bool}")
        print(f"  Energy: {result['energy_final']:.6f}")
        print(f"  Iterations: {result['iterations']}")

        if formula.verify_boolean(x_bool):
            print(f"  ✓ Valid solution found")
            if x_bool == true_solution:
                print(f"  ✓✓ Matches planted solution exactly!")
        else:
            print(f"  ✗ Invalid solution")


# ============================================================================
# MAIN TEST SUITE
# ============================================================================

def run_all_tests():
    """Run comprehensive test suite"""

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║     🔬 COMPREHENSIVE SCALING & VALIDATION TESTS 🔬        ║
    ║                                                            ║
    ║  Testing if symplectic approach truly scales polynomial   ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # TEST 1: Scaling
    scaling_results = test_scaling(
        sizes=[3, 5, 8, 10, 12],
        attempts_per_size=5
    )

    # TEST 2: Rounding gap
    test_rounding_gap()

    # TEST 3: UNSAT detection
    test_unsat_detection()

    # TEST 4: Planted solutions
    test_planted_solution()

    # FINAL VERDICT
    print("\n" + "="*70)
    print("🎯 FINAL VERDICT")
    print("="*70)

    print("""
    Based on these tests:

    1. SCALING: Check if k < 3 in polynomial fit
    2. ROUNDING: Check if no failures
    3. UNSAT: Check if correctly doesn't converge
    4. PLANTED: Check if finds solutions

    If all pass → Approach is VERY promising!
    If some fail → Need modifications but still interesting
    If most fail → Back to drawing board
    """)


if __name__ == "__main__":
    run_all_tests()
