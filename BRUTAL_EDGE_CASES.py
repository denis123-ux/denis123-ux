"""
===============================================================================
                    BRUTAL EDGE CASE TESTING
                    =========================

    Testing the HARDEST known cases:
    - Pigeonhole formulas (exponential for resolution)
    - Randomized unsatisfiable formulas
    - Planted solution instances
    - Cryptographic-style formulas
===============================================================================
"""

import numpy as np
import random
import time
import sys
from typing import List, Tuple, Optional

sys.path.insert(0, '/home/user/denis123-ux')

from symplectic_sat_solver import (
    SATFormula, Clause as SymplecticClause,
    SymplecticSATSolver
)


def convert_to_symplectic(n: int, clause_list) -> SATFormula:
    clauses = [SymplecticClause(c) for c in clause_list]
    return SATFormula(n, clauses)


# ============================================================================
# PIGEONHOLE FORMULAS (EXPONENTIAL FOR RESOLUTION!)
# ============================================================================

def generate_pigeonhole(n: int) -> Tuple[int, List[List[int]]]:
    """
    Generate Pigeonhole formula: n+1 pigeons, n holes

    PHP_n:
    - Variables: x_{i,j} means "pigeon i is in hole j"
    - (n+1)*n variables total
    - Clauses:
      1. At least one hole per pigeon: OR_j x_{i,j} for each i
      2. At most one pigeon per hole: NOT(x_{i,j} AND x_{k,j}) for i != k

    This formula is UNSATISFIABLE but requires exponential resolution steps.
    """
    n_vars = (n + 1) * n
    clauses = []

    def var(pigeon, hole):
        """Variable number for pigeon i in hole j (1-indexed)"""
        return pigeon * n + hole + 1

    # At least one hole per pigeon
    for i in range(n + 1):  # pigeons
        clause = [var(i, j) for j in range(n)]
        clauses.append(clause)

    # At most one pigeon per hole
    for j in range(n):  # holes
        for i1 in range(n + 1):
            for i2 in range(i1 + 1, n + 1):
                # NOT(x_{i1,j} AND x_{i2,j}) = NOT x_{i1,j} OR NOT x_{i2,j}
                clauses.append([-var(i1, j), -var(i2, j)])

    return n_vars, clauses


def test_pigeonhole():
    """Test symplectic approach on pigeonhole formulas"""
    print("="*80)
    print("TEST: PIGEONHOLE FORMULAS (Known exponential for resolution)")
    print("="*80)

    print("""
    PHP_n formula:
    - n+1 pigeons, n holes
    - UNSATISFIABLE (can't fit n+1 pigeons in n holes)
    - Resolution requires 2^(n/20) steps (Haken 1985)

    If symplectic approach says "SAT", it's WRONG!
    If it says "UNSAT" fast, it beat exponential barrier!
    """)

    results = []

    for n in [2, 3, 4, 5]:
        print(f"\n--- PHP_{n}: {n+1} pigeons, {n} holes ---")

        n_vars, clauses = generate_pigeonhole(n)
        formula = convert_to_symplectic(n_vars, clauses)

        print(f"  Variables: {n_vars}")
        print(f"  Clauses: {len(clauses)}")

        solver = SymplecticSATSolver(formula, embedding_degree=2)

        start = time.time()
        solution = solver.solve(
            n_attempts=10,
            T=200,
            dt=0.01,
            gamma=0.3,
            verbose=False
        )
        elapsed = time.time() - start

        if solution is not None:
            valid = formula.verify_boolean(solution)
            if valid:
                print(f"  CRITICAL ERROR: Found 'valid' solution to UNSAT formula!")
                print(f"  Solution: {solution}")
                results.append({'n': n, 'result': 'FALSE_POSITIVE', 'time': elapsed})
            else:
                print(f"  Found solution but invalid (expected for UNSAT)")
                results.append({'n': n, 'result': 'INVALID_SOL', 'time': elapsed})
        else:
            print(f"  No solution found (correct for UNSAT)")
            results.append({'n': n, 'result': 'CORRECT_UNSAT', 'time': elapsed})

        print(f"  Time: {elapsed:.2f}s")

    print("\n" + "-"*60)
    print("ANALYSIS:")

    correct = sum(1 for r in results if r['result'] == 'CORRECT_UNSAT')
    print(f"  Correctly identified UNSAT: {correct}/{len(results)}")

    false_positives = sum(1 for r in results if r['result'] == 'FALSE_POSITIVE')
    if false_positives > 0:
        print(f"  CRITICAL: {false_positives} false positives (claimed SAT for UNSAT)!")

    return results


# ============================================================================
# GRAPH COLORING (KNOWN HARD)
# ============================================================================

def generate_graph_coloring(n_vertices: int, n_colors: int, edges: List[Tuple[int,int]]) -> Tuple[int, List[List[int]]]:
    """
    Graph k-coloring as SAT:
    - Variables: x_{v,c} means "vertex v has color c"
    - Clauses:
      1. Each vertex has at least one color
      2. Each vertex has at most one color
      3. Adjacent vertices have different colors
    """
    n_vars = n_vertices * n_colors
    clauses = []

    def var(vertex, color):
        return vertex * n_colors + color + 1

    # At least one color per vertex
    for v in range(n_vertices):
        clause = [var(v, c) for c in range(n_colors)]
        clauses.append(clause)

    # At most one color per vertex
    for v in range(n_vertices):
        for c1 in range(n_colors):
            for c2 in range(c1 + 1, n_colors):
                clauses.append([-var(v, c1), -var(v, c2)])

    # Adjacent vertices different colors
    for (v1, v2) in edges:
        for c in range(n_colors):
            clauses.append([-var(v1, c), -var(v2, c)])

    return n_vars, clauses


def generate_complete_graph(n: int) -> List[Tuple[int,int]]:
    """Complete graph K_n (all vertices connected)"""
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((i, j))
    return edges


def test_graph_coloring():
    """Test graph coloring instances"""
    print("\n" + "="*80)
    print("TEST: GRAPH COLORING")
    print("="*80)

    print("""
    K_n (complete graph) requires n colors.
    - (n-1)-coloring is UNSAT
    - n-coloring is SAT
    """)

    results = []

    for n in [4, 5, 6]:
        edges = generate_complete_graph(n)

        # Test n-1 coloring (UNSAT)
        print(f"\n--- K_{n} with {n-1} colors (UNSAT) ---")
        n_vars, clauses = generate_graph_coloring(n, n-1, edges)
        formula = convert_to_symplectic(n_vars, clauses)

        solver = SymplecticSATSolver(formula, embedding_degree=2)
        start = time.time()
        solution = solver.solve(n_attempts=5, T=100, verbose=False)
        elapsed = time.time() - start

        if solution is not None and formula.verify_boolean(solution):
            print(f"  ERROR: Found solution to UNSAT!")
        else:
            print(f"  Correct: No valid solution (UNSAT)")

        results.append({'n': n, 'k': n-1, 'sat': False, 'found': solution is not None, 'time': elapsed})

        # Test n coloring (SAT)
        print(f"\n--- K_{n} with {n} colors (SAT) ---")
        n_vars, clauses = generate_graph_coloring(n, n, edges)
        formula = convert_to_symplectic(n_vars, clauses)

        solver = SymplecticSATSolver(formula, embedding_degree=2)
        start = time.time()
        solution = solver.solve(n_attempts=5, T=100, verbose=False)
        elapsed = time.time() - start

        if solution is not None and formula.verify_boolean(solution):
            print(f"  Correct: Found valid solution")
        else:
            print(f"  Failed to find solution to SAT formula")

        results.append({'n': n, 'k': n, 'sat': True, 'found': solution is not None, 'time': elapsed})

    return results


# ============================================================================
# XOR-SAT (HARD FOR CONTINUOUS METHODS)
# ============================================================================

def generate_xor_sat(n: int, seed: int = None) -> Tuple[List[List[int]], bool]:
    """
    Generate random XOR-SAT (parity constraints).

    XOR-SAT is solvable in polynomial time by Gaussian elimination,
    but CONTINUOUS relaxations struggle because XOR creates
    symmetric energy landscapes.

    Returns: (clauses, is_satisfiable)
    """
    if seed:
        random.seed(seed)

    # Generate random XOR constraints
    # Each constraint: x_i XOR x_j XOR x_k = b

    # We'll encode XOR as CNF (exponential blow-up but small for testing)
    # x XOR y = (x OR y) AND (NOT x OR NOT y)
    # x XOR y XOR z = (x XOR y) XOR z

    # For simplicity, generate 3-XOR constraints
    clauses = []
    m = int(n * 0.9)  # Below threshold

    for _ in range(m):
        vars = random.sample(range(1, n+1), 3)
        parity = random.choice([0, 1])

        # x1 XOR x2 XOR x3 = parity
        # Encode as CNF (8 clauses for each XOR-3)
        a, b, c = vars

        if parity == 0:  # x1 XOR x2 XOR x3 = 0 (even parity)
            clauses.append([a, b, c])
            clauses.append([a, -b, -c])
            clauses.append([-a, b, -c])
            clauses.append([-a, -b, c])
        else:  # x1 XOR x2 XOR x3 = 1 (odd parity)
            clauses.append([-a, -b, -c])
            clauses.append([-a, b, c])
            clauses.append([a, -b, c])
            clauses.append([a, b, -c])

    # XOR-SAT is easy to determine satisfiability via Gaussian elimination
    # but we'll just test empirically
    return clauses, True  # Likely SAT at this ratio


def test_xor_sat():
    """Test XOR-SAT instances"""
    print("\n" + "="*80)
    print("TEST: XOR-SAT (HARD FOR CONTINUOUS METHODS)")
    print("="*80)

    print("""
    XOR-SAT creates symmetric energy landscapes where
    continuous relaxations tend to get stuck at x = 0.5.

    This is a known weakness of gradient-based SAT solvers.
    """)

    results = []

    for n in [5, 8, 10, 12]:
        print(f"\n--- XOR-SAT n={n} ---")

        successes = 0
        n_trials = 5

        for trial in range(n_trials):
            clauses, _ = generate_xor_sat(n, seed=500+n*10+trial)
            formula = convert_to_symplectic(n, clauses)

            solver = SymplecticSATSolver(formula, embedding_degree=2)
            solution = solver.solve(n_attempts=5, T=100, verbose=False)

            if solution is not None and formula.verify_boolean(solution):
                successes += 1

        success_rate = successes / n_trials
        results.append({'n': n, 'success_rate': success_rate})
        print(f"  Success rate: {success_rate*100:.0f}%")

    print("\n" + "-"*60)
    print("ANALYSIS:")

    rates = [r['success_rate'] for r in results]
    if all(r > 0.8 for r in rates):
        print("  XOR-SAT handled well!")
    elif all(r < 0.3 for r in rates):
        print("  CRITICAL: XOR-SAT completely fails (expected weakness)")
    else:
        print("  Mixed performance on XOR-SAT")

    return results


# ============================================================================
# HIDDEN CLIQUE (PLANTED SOLUTION)
# ============================================================================

def generate_hidden_clique(n: int, k: int, seed: int = None) -> Tuple[int, List[List[int]], List[int]]:
    """
    Hidden clique problem:
    - Random graph G(n, 0.5)
    - Plant a clique of size k
    - SAT: Does graph have k-clique?

    Known to be hard for many algorithms when k < sqrt(n).
    """
    if seed:
        random.seed(seed)
        np.random.seed(seed)

    # Generate random adjacency matrix
    adj = np.random.randint(0, 2, (n, n))
    adj = np.triu(adj, 1)
    adj = adj + adj.T  # Symmetric

    # Plant clique
    clique_vertices = random.sample(range(n), k)
    for i in clique_vertices:
        for j in clique_vertices:
            if i != j:
                adj[i, j] = 1

    # Encode k-clique as SAT
    # Variables: x_i means "vertex i is in clique"
    clauses = []

    # At least k vertices in clique (hard to encode exactly)
    # We'll use a simpler formulation: select exactly k vertices

    # For simplicity, just check if clique exists
    # Constraint: if x_i and x_j, then (i,j) must be edge
    for i in range(n):
        for j in range(i+1, n):
            if adj[i, j] == 0:  # No edge
                # NOT(x_i AND x_j) = NOT x_i OR NOT x_j
                clauses.append([-(i+1), -(j+1)])

    # At least k variables true (at-least-k constraint)
    # This is complex, so we'll skip for now and just test edge constraints

    return n, clauses, clique_vertices


def test_hidden_clique():
    """Test hidden clique instances"""
    print("\n" + "="*80)
    print("TEST: HIDDEN CLIQUE PROBLEM")
    print("="*80)

    print("""
    Plant a clique of size k in random graph G(n, 0.5).
    Hard when k < sqrt(n) for most algorithms.
    """)

    results = []

    for n in [10, 15, 20]:
        k = int(np.sqrt(n)) + 1  # Just above sqrt(n)
        print(f"\n--- n={n}, k={k} (hidden clique) ---")

        n_vars, clauses, planted = generate_hidden_clique(n, k, seed=600+n)

        # Add clauses to force selection of k vertices
        # (simplified: just test without cardinality constraint)

        formula = convert_to_symplectic(n_vars, clauses)

        solver = SymplecticSATSolver(formula, embedding_degree=2)
        start = time.time()
        solution = solver.solve(n_attempts=5, T=100, verbose=False)
        elapsed = time.time() - start

        if solution is not None:
            # Check if found planted clique
            found_vertices = [i for i in range(n) if solution[i] == 1]
            is_planted = set(found_vertices) == set(planted)
            print(f"  Found: {found_vertices}")
            print(f"  Planted: {planted}")
            print(f"  Match: {is_planted}")
        else:
            print(f"  No solution found")

        results.append({'n': n, 'k': k, 'found': solution is not None, 'time': elapsed})

    return results


# ============================================================================
# FACTORING AS SAT (CRYPTOGRAPHIC HARDNESS)
# ============================================================================

def generate_multiplication_circuit(a_bits: int, b_bits: int) -> Tuple[int, List[List[int]], int, int]:
    """
    Generate SAT formula for multiplication circuit.
    Finding satisfying assignment = factoring the product!

    This is believed to be HARD (basis of RSA security).
    """
    # For simplicity, generate a small multiplication problem
    # a * b = c where c is given, find a and b

    # Variables:
    # a_i for bits of a (i=0..a_bits-1)
    # b_j for bits of b (j=0..b_bits-1)
    # Intermediate variables for carry bits

    # This gets complex, so we'll generate a simple test
    # Testing n-bit multiplication

    n = a_bits  # Assume square

    # Generate a random product
    a_val = random.randint(2**(n-1), 2**n - 1)
    b_val = random.randint(2**(n-1), 2**n - 1)
    c_val = a_val * b_val

    # For testing, we'll create a simpler version
    # Just test if the approach can "guess" factors

    print(f"    (Test: {a_val} * {b_val} = {c_val})")

    # Simplified: return empty formula (placeholder)
    return n, [], a_val, b_val


def test_factoring():
    """Test factoring-like problems"""
    print("\n" + "="*80)
    print("TEST: FACTORING-STYLE PROBLEMS")
    print("="*80)

    print("""
    Factoring is believed hard (RSA security depends on this).
    If symplectic approach solves factoring easily, it would
    break cryptography!

    (Note: Full encoding is complex, this is a simplified test)
    """)

    print("\n  [Factoring test requires complex circuit encoding]")
    print("  [Skipping full implementation - would need proper circuit SAT]")

    return []


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║                    BRUTAL EDGE CASE TESTING                              ║
    ║                                                                          ║
    ║  Testing on HARDEST known instances                                      ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)

    all_results = {}

    all_results['pigeonhole'] = test_pigeonhole()
    all_results['graph_coloring'] = test_graph_coloring()
    all_results['xor_sat'] = test_xor_sat()
    all_results['hidden_clique'] = test_hidden_clique()
    all_results['factoring'] = test_factoring()

    # Final summary
    print("\n" + "="*80)
    print("BRUTAL EDGE CASE SUMMARY")
    print("="*80)

    print("""
    Results:

    PIGEONHOLE (UNSAT):
      - Tests if approach correctly identifies unsatisfiable formulas
      - False positives = CRITICAL BUG

    GRAPH COLORING:
      - K_n with n-1 colors is UNSAT, n colors is SAT
      - Tests both SAT and UNSAT detection

    XOR-SAT:
      - Known weakness for continuous methods
      - Energy landscape has symmetric local minima

    HIDDEN CLIQUE:
      - Planted solution problems
      - Hard for most polynomial algorithms

    FACTORING:
      - Would break cryptography if easy
      - (Not fully implemented - complex encoding needed)
    """)

    # Count issues
    pigeonhole_issues = sum(1 for r in all_results.get('pigeonhole', [])
                           if r.get('result') == 'FALSE_POSITIVE')

    if pigeonhole_issues > 0:
        print(f"\n  CRITICAL: {pigeonhole_issues} false positives on UNSAT formulas!")

    return all_results


if __name__ == "__main__":
    main()
