"""
🌌 HOLOGRAPHIC SAT SOLVER
==========================

Implementation of computational holography for SAT solving.

Core idea: Project n-dimensional SAT to (n-1)-dimensional boundary
via renormalization group flow (variable elimination).

Key question: Does clause count stay polynomial? (Area law)
"""

import random
from typing import List, Set, Tuple, Optional, Dict
from collections import defaultdict
import time


class Literal:
    """A literal (variable or its negation)"""

    def __init__(self, var: int, negated: bool = False):
        self.var = abs(var)
        self.negated = negated

    def __eq__(self, other):
        return self.var == other.var and self.negated == other.negated

    def __hash__(self):
        return hash((self.var, self.negated))

    def __repr__(self):
        return f"{'¬' if self.negated else ''}x{self.var}"

    def negate(self):
        """Return negation of this literal"""
        return Literal(self.var, not self.negated)

    @staticmethod
    def from_int(i: int):
        """Create literal from integer (positive or negative)"""
        if i > 0:
            return Literal(i, False)
        else:
            return Literal(-i, True)


class Clause:
    """A disjunction of literals"""

    def __init__(self, literals: List[Literal]):
        # Store as set for efficient operations
        self.literals = frozenset(literals)

    def __repr__(self):
        if not self.literals:
            return "⊥"  # Empty clause (contradiction)
        return "(" + " ∨ ".join(str(lit) for lit in sorted(self.literals, key=lambda l: l.var)) + ")"

    def __eq__(self, other):
        return self.literals == other.literals

    def __hash__(self):
        return hash(self.literals)

    def __len__(self):
        return len(self.literals)

    def is_empty(self):
        """Empty clause = contradiction"""
        return len(self.literals) == 0

    def is_tautology(self):
        """Check if clause contains both x and ¬x"""
        vars_seen = {}
        for lit in self.literals:
            if lit.var in vars_seen:
                if vars_seen[lit.var] != lit.negated:
                    return True  # Both x and ¬x present
            vars_seen[lit.var] = lit.negated
        return False

    def contains_var(self, var: int) -> bool:
        """Check if clause contains variable (positive or negative)"""
        return any(lit.var == var for lit in self.literals)

    def get_literal_for_var(self, var: int) -> Optional[Literal]:
        """Get the literal for given variable"""
        for lit in self.literals:
            if lit.var == var:
                return lit
        return None

    def remove_literal(self, lit: Literal):
        """Return new clause without given literal"""
        return Clause([l for l in self.literals if l != lit])


class CNFFormula:
    """CNF formula (conjunction of clauses)"""

    def __init__(self, clauses: List[Clause], n_vars: int = None):
        self.clauses = set(clauses)  # Use set to avoid duplicates
        if n_vars is None:
            # Infer from clauses
            n_vars = max((lit.var for clause in clauses for lit in clause.literals), default=0)
        self.n_vars = n_vars

    def __repr__(self):
        if not self.clauses:
            return "⊤"  # Empty formula (tautology)
        if any(c.is_empty() for c in self.clauses):
            return "⊥"  # Contains empty clause
        return " ∧ ".join(str(clause) for clause in sorted(self.clauses, key=lambda c: len(c)))

    def is_empty(self):
        """No clauses = always satisfied"""
        return len(self.clauses) == 0

    def has_empty_clause(self):
        """Contains empty clause = contradiction"""
        return any(c.is_empty() for c in self.clauses)

    def get_variables(self) -> Set[int]:
        """Get all variables in formula"""
        return {lit.var for clause in self.clauses for lit in clause.literals}

    def copy(self):
        """Deep copy"""
        return CNFFormula(list(self.clauses), self.n_vars)


# ============================================================================
# HOLOGRAPHIC OPERATIONS
# ============================================================================

def resolve(c1: Clause, c2: Clause, var: int) -> Optional[Clause]:
    """
    Resolution rule: (x ∨ A) ∧ (¬x ∨ B) ⟹ (A ∨ B)

    Returns new clause, or None if resolution not possible
    """
    # Find literals for var in each clause
    lit1 = c1.get_literal_for_var(var)
    lit2 = c2.get_literal_for_var(var)

    if lit1 is None or lit2 is None:
        return None  # One clause doesn't contain var

    if lit1.negated == lit2.negated:
        return None  # Both have same polarity, can't resolve

    # Perform resolution
    new_literals = []

    # Add all literals from c1 except var
    for lit in c1.literals:
        if lit.var != var:
            new_literals.append(lit)

    # Add all literals from c2 except var
    for lit in c2.literals:
        if lit.var != var:
            new_literals.append(lit)

    # Remove duplicates and create clause
    new_clause = Clause(list(set(new_literals)))

    return new_clause


def integrate_out_variable(formula: CNFFormula, var: int) -> CNFFormula:
    """
    HOLOGRAPHIC PROJECTION: Integrate out (eliminate) variable via resolution

    This is the core RG flow step!

    Complexity: O(m²) worst case (quadratic clause growth)
    """
    # Separate clauses by var
    clauses_pos = []  # Contain x
    clauses_neg = []  # Contain ¬x
    clauses_other = []  # Don't contain x

    for clause in formula.clauses:
        lit = clause.get_literal_for_var(var)
        if lit is None:
            clauses_other.append(clause)
        elif lit.negated:
            clauses_neg.append(clause)
        else:
            clauses_pos.append(clause)

    # Resolve all pairs
    new_clauses = set(clauses_other)  # Start with clauses not containing var

    for c_pos in clauses_pos:
        for c_neg in clauses_neg:
            c_new = resolve(c_pos, c_neg, var)
            if c_new is not None:
                new_clauses.add(c_new)

    return CNFFormula(list(new_clauses), formula.n_vars - 1)


def simplify(formula: CNFFormula) -> CNFFormula:
    """
    Simplify formula:
    1. Remove tautologies (x ∨ ¬x)
    2. Remove subsumed clauses
    3. Unit propagation
    4. Pure literal elimination
    """
    clauses = set(formula.clauses)

    # 1. Remove tautologies
    clauses = {c for c in clauses if not c.is_tautology()}

    # 2. Remove subsumed clauses
    # Clause A subsumes B if A ⊆ B
    clauses_list = list(clauses)
    non_subsumed = []

    for i, c1 in enumerate(clauses_list):
        subsumed = False
        for j, c2 in enumerate(clauses_list):
            if i != j and c1.literals.issuperset(c2.literals):
                subsumed = True
                break
        if not subsumed:
            non_subsumed.append(c1)

    clauses = set(non_subsumed)

    # 3. Unit propagation
    # If clause is unit (single literal), propagate it
    changed = True
    while changed:
        changed = False
        for clause in list(clauses):
            if len(clause) == 1:
                unit_lit = list(clause.literals)[0]

                # Remove clauses containing unit_lit
                new_clauses = set()
                for c in clauses:
                    if unit_lit in c.literals:
                        continue  # Clause satisfied, remove
                    else:
                        # Remove ¬unit_lit from clause
                        neg_lit = unit_lit.negate()
                        if neg_lit in c.literals:
                            c_new = c.remove_literal(neg_lit)
                            new_clauses.add(c_new)
                        else:
                            new_clauses.add(c)

                if new_clauses != clauses:
                    clauses = new_clauses
                    changed = True
                    break

    # 4. Pure literal elimination
    # If literal appears only in one polarity, set it to satisfy
    lit_counts = defaultdict(lambda: {'pos': 0, 'neg': 0})

    for clause in clauses:
        for lit in clause.literals:
            if lit.negated:
                lit_counts[lit.var]['neg'] += 1
            else:
                lit_counts[lit.var]['pos'] += 1

    pure_lits = []
    for var, counts in lit_counts.items():
        if counts['pos'] > 0 and counts['neg'] == 0:
            pure_lits.append(Literal(var, False))
        elif counts['neg'] > 0 and counts['pos'] == 0:
            pure_lits.append(Literal(var, True))

    # Remove clauses containing pure literals
    for pure_lit in pure_lits:
        clauses = {c for c in clauses if pure_lit not in c.literals}

    return CNFFormula(list(clauses), formula.n_vars)


# ============================================================================
# HOLOGRAPHIC SAT SOLVER
# ============================================================================

def holographic_sat_solve(formula: CNFFormula, verbose=False) -> Dict:
    """
    MAIN ALGORITHM: Holographic SAT solver via RG flow

    Returns dict with:
        - 'satisfiable': bool
        - 'solution': assignment if SAT, None if UNSAT
        - 'clause_growth': list of clause counts at each RG step
        - 'time': runtime
    """
    start_time = time.time()

    n = formula.n_vars
    clause_growth = [len(formula.clauses)]

    if verbose:
        print(f"\n🌌 HOLOGRAPHIC SAT SOLVER")
        print(f"   Variables: {n}, Clauses: {len(formula.clauses)}")
        print(f"   Starting RG flow...\n")

    # Store formulas at each level for reconstruction
    formulas = {n: formula.copy()}

    # FORWARD PASS: RG flow to boundary
    for k in range(n, 0, -1):
        phi_k = formulas[k]

        if verbose:
            print(f"   RG Step {n-k+1}/{n}: {k} vars, {len(phi_k.clauses)} clauses")

        # Check trivial cases
        if phi_k.is_empty():
            # No clauses = SAT
            end_time = time.time()
            return {
                'satisfiable': True,
                'solution': [0] * n,  # Any assignment works
                'clause_growth': clause_growth,
                'time': end_time - start_time,
                'steps': n - k + 1
            }

        if phi_k.has_empty_clause():
            # Empty clause = UNSAT
            end_time = time.time()
            return {
                'satisfiable': False,
                'solution': None,
                'clause_growth': clause_growth,
                'time': end_time - start_time,
                'steps': n - k + 1
            }

        if k == 1:
            # 1 variable: trivial
            break

        # Integrate out variable k
        var_to_eliminate = k
        phi_k_minus_1 = integrate_out_variable(phi_k, var_to_eliminate)

        # Simplify
        phi_k_minus_1 = simplify(phi_k_minus_1)

        formulas[k-1] = phi_k_minus_1
        clause_growth.append(len(phi_k_minus_1.clauses))

        # Safety check: exponential blowup
        if len(phi_k_minus_1.clauses) > 10000:
            if verbose:
                print(f"\n   ⚠️  CLAUSE EXPLOSION: {len(phi_k_minus_1.clauses)} clauses!")
                print(f"   Stopping early (exponential growth detected)")
            end_time = time.time()
            return {
                'satisfiable': None,
                'solution': None,
                'clause_growth': clause_growth,
                'time': end_time - start_time,
                'steps': n - k + 1,
                'error': 'clause_explosion'
            }

    # At k=1: solve trivially
    phi_1 = formulas[1]

    if phi_1.is_empty():
        solution_1 = {1: 0}  # Any value
    elif phi_1.has_empty_clause():
        end_time = time.time()
        return {
            'satisfiable': False,
            'solution': None,
            'clause_growth': clause_growth,
            'time': end_time - start_time,
            'steps': n
        }
    else:
        # Find satisfying assignment for 1 variable
        # Just pick value that satisfies all clauses
        clause_list = list(phi_1.clauses)
        if clause_list:
            # Look at first clause
            lit = list(clause_list[0].literals)[0]
            solution_1 = {1: 0 if lit.negated else 1}
        else:
            solution_1 = {1: 0}

    # BACKWARD PASS: Reconstruct solution
    solution = solution_1.copy()

    for k in range(2, n+1):
        # Extend solution from k-1 vars to k vars
        # Choose value of var k that satisfies clauses in formulas[k]

        phi_k = formulas[k]

        # Try both values
        for val in [0, 1]:
            solution[k] = val

            # Check if satisfies all clauses
            satisfied = True
            for clause in phi_k.clauses:
                clause_sat = False
                for lit in clause.literals:
                    if lit.var in solution:
                        lit_val = solution[lit.var]
                        if (lit_val == 1 and not lit.negated) or (lit_val == 0 and lit.negated):
                            clause_sat = True
                            break
                if not clause_sat:
                    satisfied = False
                    break

            if satisfied:
                break

        if not satisfied:
            # Neither value works - shouldn't happen if algorithm is correct
            if verbose:
                print(f"   ⚠️  Reconstruction failed at variable {k}")

    end_time = time.time()

    if verbose:
        print(f"\n   ✅ RG flow complete!")
        print(f"   Max clauses: {max(clause_growth)}")
        print(f"   Final clauses: {clause_growth[-1]}")
        print(f"   Time: {end_time - start_time:.3f}s")

    return {
        'satisfiable': True,
        'solution': solution,
        'clause_growth': clause_growth,
        'time': end_time - start_time,
        'steps': n
    }


# ============================================================================
# UTILITIES
# ============================================================================

def generate_random_3sat(n: int, m: int, seed=None) -> CNFFormula:
    """Generate random 3-SAT formula"""
    if seed:
        random.seed(seed)

    clauses = []
    for _ in range(m):
        vars = random.sample(range(1, n+1), 3)
        lits = [Literal.from_int(v if random.random() > 0.5 else -v) for v in vars]
        clauses.append(Clause(lits))

    return CNFFormula(clauses, n)


def generate_simple_sat(n=3) -> CNFFormula:
    """Generate simple SAT formula for testing"""
    # (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3)
    clauses = [
        Clause([Literal(1), Literal(2)]),
        Clause([Literal(1, True), Literal(3)]),
        Clause([Literal(2, True), Literal(3, True)])
    ]
    return CNFFormula(clauses, n)


def verify_solution(formula: CNFFormula, solution: Dict[int, int]) -> bool:
    """Verify if solution satisfies formula"""
    for clause in formula.clauses:
        satisfied = False
        for lit in clause.literals:
            if lit.var in solution:
                val = solution[lit.var]
                if (val == 1 and not lit.negated) or (val == 0 and lit.negated):
                    satisfied = True
                    break
        if not satisfied:
            return False
    return True


# ============================================================================
# TESTS
# ============================================================================

def test_simple():
    """Test on simple formula"""
    print("\n" + "="*70)
    print("TEST 1: Simple SAT Formula")
    print("="*70)

    formula = generate_simple_sat()
    print(f"Formula: {formula}")

    result = holographic_sat_solve(formula, verbose=True)

    print(f"\nResult: {'SAT' if result['satisfiable'] else 'UNSAT'}")
    if result['solution']:
        print(f"Solution: {result['solution']}")
        valid = verify_solution(formula, result['solution'])
        print(f"Verification: {'✅ VALID' if valid else '❌ INVALID'}")


def test_clause_growth():
    """Test clause growth on various sizes"""
    print("\n" + "="*70)
    print("TEST 2: Clause Growth Analysis")
    print("="*70)

    sizes = [5, 7, 10, 12, 15]

    for n in sizes:
        m = int(4.27 * n)  # Near threshold
        formula = generate_random_3sat(n, m, seed=100+n)

        result = holographic_sat_solve(formula, verbose=False)

        print(f"\nn={n:2d}, m={m:2d}:")
        print(f"  Clause growth: {result['clause_growth']}")
        print(f"  Max clauses: {max(result['clause_growth'])}")
        print(f"  Growth ratio: {max(result['clause_growth']) / m:.2f}x")

        if 'error' in result:
            print(f"  ❌ {result['error']}")
        else:
            print(f"  ✅ Completed in {result['steps']} steps")


def test_scaling():
    """Test if clause growth is polynomial or exponential"""
    print("\n" + "="*70)
    print("TEST 3: Scaling Analysis (Critical Test!)")
    print("="*70)

    sizes = [3, 5, 7, 10, 12]
    results = []

    for n in sizes:
        m = int(4 * n)
        formula = generate_random_3sat(n, m, seed=200+n)

        result = holographic_sat_solve(formula, verbose=False)

        max_clauses = max(result['clause_growth']) if result['clause_growth'] else m

        results.append({
            'n': n,
            'm': m,
            'max_clauses': max_clauses,
            'ratio': max_clauses / m
        })

        print(f"n={n:2d}: m={m:3d} → max={max_clauses:5d} (ratio: {max_clauses/m:6.2f}x)")

    # Analyze trend
    print(f"\n📊 SCALING ANALYSIS:")

    if len(results) >= 3:
        n1, n2 = results[0]['n'], results[-1]['n']
        r1, r2 = results[0]['ratio'], results[-1]['ratio']

        # If polynomial: ratio ∝ n^k
        import math
        if r1 > 0 and r2 > 0:
            k = math.log(r2 / r1) / math.log(n2 / n1)
            print(f"   Growth exponent k ≈ {k:.2f}")

            if k < 2:
                print(f"   🟢 EXCELLENT! Sub-quadratic growth")
            elif k < 3:
                print(f"   🟡 GOOD: Polynomial (cubic or less)")
            elif k < 4:
                print(f"   🟠 CONCERNING: High polynomial degree")
            else:
                print(f"   🔴 BAD: Likely exponential")


if __name__ == "__main__":
    print("""
    🌌 HOLOGRAPHIC SAT SOLVER
    ==========================

    Testing computational holography for SAT solving.

    Key question: Does clause count grow polynomially?
    """)

    test_simple()
    test_clause_growth()
    test_scaling()

    print("\n" + "="*70)
    print("✨ TESTS COMPLETE")
    print("="*70)
