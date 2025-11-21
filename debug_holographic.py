"""
Debug script to understand why holographic solutions fail verification
"""

import sys
sys.path.insert(0, '/home/user/denis123-ux')

from holographic_sat import (
    CNFFormula, Clause, Literal,
    holographic_sat_solve, generate_random_3sat, generate_simple_sat,
    verify_solution
)

def debug_holographic():
    """Debug the holographic solver"""
    print("="*80)
    print("DEBUGGING HOLOGRAPHIC SOLVER")
    print("="*80)

    # Test 1: Simple SAT
    print("\n--- Test 1: Simple SAT ---")
    formula = generate_simple_sat(3)
    print(f"Formula: {formula}")

    result = holographic_sat_solve(formula, verbose=True)

    print(f"\nResult: {result}")
    print(f"Solution type: {type(result.get('solution'))}")
    print(f"Solution value: {result.get('solution')}")

    if result.get('solution'):
        sol = result['solution']
        print(f"\nManual verification:")

        for clause in formula.clauses:
            satisfied = False
            print(f"  Clause {clause}:")
            for lit in clause.literals:
                print(f"    Literal: {lit}, var={lit.var}, negated={lit.negated}")
                if isinstance(sol, dict):
                    val = sol.get(lit.var, None)
                elif isinstance(sol, list):
                    val = sol[lit.var - 1] if lit.var <= len(sol) else None
                else:
                    val = None
                print(f"    Value in solution: {val}")

                if val is not None:
                    if (val == 1 and not lit.negated) or (val == 0 and lit.negated):
                        print(f"    -> SATISFIES clause")
                        satisfied = True
                        break

            if not satisfied:
                print(f"    -> CLAUSE NOT SATISFIED!")

        # Test verify_solution
        print(f"\nverify_solution result: {verify_solution(formula, sol)}")

    # Test 2: Check solution format
    print("\n" + "="*80)
    print("--- Test 2: Solution format analysis ---")

    # Generate a small random instance
    formula2 = generate_random_3sat(5, 10, seed=42)
    result2 = holographic_sat_solve(formula2, verbose=False)

    print(f"Formula: {formula2.n_vars} vars, {len(formula2.clauses)} clauses")
    print(f"Solution: {result2.get('solution')}")
    print(f"Solution type: {type(result2.get('solution'))}")

    if result2.get('solution'):
        sol = result2['solution']
        if isinstance(sol, dict):
            print(f"Dict keys: {list(sol.keys())}")
            print(f"Dict values: {list(sol.values())}")
        elif isinstance(sol, list):
            print(f"List length: {len(sol)}")
            print(f"List indices: 0 to {len(sol)-1}")

    # Test 3: Check the reconstruction
    print("\n" + "="*80)
    print("--- Test 3: Check clause-by-clause ---")

    formula3 = generate_simple_sat(3)
    result3 = holographic_sat_solve(formula3, verbose=False)
    sol3 = result3.get('solution')

    print(f"Formula clauses:")
    for i, clause in enumerate(formula3.clauses):
        print(f"  {i}: {clause}")
        print(f"      literals: {list(clause.literals)}")

    print(f"\nSolution: {sol3}")

    if isinstance(sol3, dict):
        print("\nChecking each variable:")
        for var in sorted(sol3.keys()):
            print(f"  x{var} = {sol3[var]}")

    # Test 4: Trace through verify_solution
    print("\n" + "="*80)
    print("--- Test 4: Detailed verify_solution trace ---")

    def verify_detailed(formula, solution):
        print(f"Verifying solution: {solution}")
        for i, clause in enumerate(formula.clauses):
            print(f"\n  Clause {i}: {clause}")
            satisfied = False
            for lit in clause.literals:
                print(f"    Checking literal {lit} (var={lit.var}, neg={lit.negated})")

                if isinstance(solution, dict):
                    if lit.var in solution:
                        val = solution[lit.var]
                        print(f"      Found in solution: {val}")
                        if (val == 1 and not lit.negated) or (val == 0 and lit.negated):
                            print(f"      -> Literal satisfied!")
                            satisfied = True
                            break
                        else:
                            print(f"      -> Literal NOT satisfied")
                    else:
                        print(f"      Variable not in solution!")
                elif isinstance(solution, list):
                    if lit.var <= len(solution):
                        val = solution[lit.var - 1]
                        print(f"      Found in solution: {val}")
                        if (val == 1 and not lit.negated) or (val == 0 and lit.negated):
                            print(f"      -> Literal satisfied!")
                            satisfied = True
                            break
                        else:
                            print(f"      -> Literal NOT satisfied")
                    else:
                        print(f"      Variable out of range!")

            if not satisfied:
                print(f"  CLAUSE NOT SATISFIED - returning False")
                return False

        print("\n  All clauses satisfied!")
        return True

    verify_detailed(formula3, sol3)

    # Test 5: What if we manually construct a correct solution?
    print("\n" + "="*80)
    print("--- Test 5: Manual solution test ---")

    # (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3)
    # x1=1, x2=0, x3=1 works:
    # (1 ∨ 0) = 1 ✓
    # (0 ∨ 1) = 1 ✓
    # (1 ∨ 0) = 1 ✓

    manual_dict = {1: 1, 2: 0, 3: 1}
    manual_list = [1, 0, 1]

    print(f"Testing manual solutions on simple_sat:")
    print(f"  Dict solution {manual_dict}: {verify_solution(formula3, manual_dict)}")

    # Check if verify_solution handles lists
    print(f"\nExpected behavior with list: trying...")
    try:
        print(f"  List solution {manual_list}: {verify_solution(formula3, manual_list)}")
    except Exception as e:
        print(f"  List solution failed: {e}")


if __name__ == "__main__":
    debug_holographic()
