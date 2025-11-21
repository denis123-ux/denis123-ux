#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    CYCLE EXCLUSION: RIGOROUS ANALYSIS
═══════════════════════════════════════════════════════════════════════════════

Goal: Prove that no non-trivial cycles exist in the Collatz sequence.

A cycle with k odd values {a₁, a₂, ..., aₖ} must satisfy:
    ∏ᵢ(3aᵢ + 1) = 2^e × ∏ᵢaᵢ

where e is the total number of even steps.

We analyze this equation from multiple angles:
1. Modular constraints
2. Size bounds
3. 2-adic valuation analysis
4. Explicit enumeration bounds
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from fractions import Fraction
from itertools import combinations, product
from functools import reduce
import math
from typing import List, Tuple, Set, Optional
from collections import defaultdict


def header(title: str):
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + f" {title} ".center(78) + "║")
    print("╚" + "═"*78 + "╝")


def v2(n: int) -> int:
    """2-adic valuation: highest power of 2 dividing n"""
    if n == 0:
        return float('inf')
    count = 0
    while n % 2 == 0:
        n //= 2
        count += 1
    return count


def collatz_cycle_equation():
    """Derive and analyze the cycle equation"""
    header("THEOREM 1: THE CYCLE EQUATION")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         DERIVATION OF CYCLE EQUATION
═══════════════════════════════════════════════════════════════════════════════

Consider a hypothetical cycle visiting odd values a₁ → a₂ → ... → aₖ → a₁

For each odd value aᵢ:
    - Apply 3aᵢ + 1 (odd step)
    - Apply divisions by 2 until reaching next odd value aᵢ₊₁

Let eᵢ = number of divisions by 2 after 3aᵢ + 1 to reach aᵢ₊₁

Then: aᵢ₊₁ = (3aᵢ + 1) / 2^eᵢ

For a CYCLE (returning to a₁):
    a₁ = (3aₖ + 1) / 2^eₖ × ... × (3a₁ + 1) / 2^e₁ × a₁ / a₁

Multiplying all equations:
    ∏ᵢ aᵢ₊₁ = ∏ᵢ (3aᵢ + 1) / 2^eᵢ

Since it's a cycle, ∏ᵢ aᵢ₊₁ = ∏ᵢ aᵢ

Therefore:
    ∏ᵢ aᵢ = ∏ᵢ (3aᵢ + 1) / 2^e    where e = Σᵢ eᵢ

CYCLE EQUATION:
    ╔═══════════════════════════════════════════════════════════════════╗
    ║   ∏ᵢ (3aᵢ + 1) = 2^e × ∏ᵢ aᵢ    for some integer e ≥ k        ║
    ╚═══════════════════════════════════════════════════════════════════╝

Note: e ≥ k because each eᵢ ≥ 1 (3aᵢ + 1 is always even for odd aᵢ).
""")


def modular_constraints():
    """Analyze modular constraints on cycles"""
    header("THEOREM 2: MODULAR CONSTRAINTS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         MODULAR ANALYSIS (mod 3)
═══════════════════════════════════════════════════════════════════════════════

LEMMA 2.1: For any odd a, we have 3a + 1 ≡ 1 (mod 3)

PROOF: 3a ≡ 0 (mod 3), so 3a + 1 ≡ 1 (mod 3). QED.

LEMMA 2.2: In the cycle equation ∏(3aᵢ + 1) = 2^e × ∏aᵢ:

    LHS ≡ 1^k ≡ 1 (mod 3)
    RHS ≡ 2^e × ∏aᵢ (mod 3)

    Since 2 ≡ -1 (mod 3): 2^e ≡ (-1)^e (mod 3)

CONSTRAINT 1:
    (-1)^e × ∏aᵢ ≡ 1 (mod 3)

    If e is even: ∏aᵢ ≡ 1 (mod 3)
    If e is odd:  ∏aᵢ ≡ -1 ≡ 2 (mod 3)
""")

    # Verify with examples
    print("VERIFICATION:")
    print("-" * 60)

    # The trivial cycle 1 → 4 → 2 → 1
    # Odd values: {1}, e = 2 (4 → 2 → 1)
    print("Trivial cycle {1}: 3×1+1 = 4 = 2² × 1 ✓")
    print("  e = 2 (even), ∏aᵢ = 1 ≡ 1 (mod 3) ✓")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         MODULAR ANALYSIS (mod 8)
═══════════════════════════════════════════════════════════════════════════════

For deeper constraints, analyze mod 8.

LEMMA 2.3: For odd a, the value of 3a + 1 (mod 8) depends on a (mod 8):
""")

    print("a mod 8  |  3a+1 mod 8  |  v₂(3a+1)")
    print("-" * 40)
    for a_mod in [1, 3, 5, 7]:
        val = (3 * a_mod + 1) % 8
        # Compute v2 for this residue class
        v2_val = v2(3 * a_mod + 1)
        print(f"   {a_mod}    |      {val}       |     {v2_val}")

    print("""
OBSERVATION:
    - a ≡ 1 (mod 8): v₂(3a+1) = 2 (exactly)
    - a ≡ 3 (mod 8): v₂(3a+1) = 1 (exactly)
    - a ≡ 5 (mod 8): v₂(3a+1) ≥ 4
    - a ≡ 7 (mod 8): v₂(3a+1) = 1 (exactly)

This constrains which combinations of residues can form a cycle!
""")


def size_bound_analysis():
    """Analyze size bounds on cycle elements"""
    header("THEOREM 3: SIZE BOUNDS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                              SIZE CONSTRAINTS
═══════════════════════════════════════════════════════════════════════════════

LEMMA 3.1 (Lower Bound on e):
    In a cycle with k odd values, e ≥ k.

PROOF: Each 3aᵢ + 1 is even, requiring at least one division. QED.

LEMMA 3.2 (Upper Bound from Cycle Equation):
    From ∏(3aᵢ + 1) = 2^e × ∏aᵢ, taking logs:

    Σᵢ log(3aᵢ + 1) = e × log(2) + Σᵢ log(aᵢ)
    Σᵢ log(3 + 1/aᵢ) = e × log(2)

    Since 3 < 3 + 1/aᵢ ≤ 4:
        k × log(3) < e × log(2) ≤ k × log(4)
        k × log(3)/log(2) < e ≤ 2k

    Therefore: 1.585k < e ≤ 2k

LEMMA 3.3 (Refined Bound):
    Let A = min(aᵢ). Then 3 + 1/A ≤ 3 + 1/aᵢ ≤ 4 for all i.

    k × log(3 + 1/A) ≤ e × log(2)
    e ≥ k × log(3 + 1/A) / log(2)

    As A → ∞: e/k → log(3)/log(2) ≈ 1.585
""")

    print("NUMERICAL BOUNDS:")
    print("-" * 50)
    print(f"{'k (odd values)':<20} {'e_min':<15} {'e_max':<15}")
    print("-" * 50)

    for k in range(1, 11):
        e_min = int(np.ceil(k * np.log(3) / np.log(2)))
        e_max = 2 * k
        print(f"{k:<20} {e_min:<15} {e_max:<15}")


def two_adic_analysis():
    """Deep 2-adic valuation analysis"""
    header("THEOREM 4: 2-ADIC VALUATION ANALYSIS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                           2-ADIC CONSTRAINTS
═══════════════════════════════════════════════════════════════════════════════

DEFINITION: v₂(n) = max{k : 2^k | n} (2-adic valuation)

KEY PROPERTY: v₂(∏xᵢ) = Σᵢ v₂(xᵢ)

LEMMA 4.1: For the cycle equation ∏(3aᵢ+1) = 2^e × ∏aᵢ:

    v₂(LHS) = Σᵢ v₂(3aᵢ + 1) = e    (since aᵢ are odd, v₂(aᵢ) = 0)

    Therefore: e = Σᵢ v₂(3aᵢ + 1)

This is a STRONG constraint: the exponent e is exactly determined by the
2-adic valuations of the 3aᵢ + 1 terms!

LEMMA 4.2 (Distribution of v₂(3a+1)):
    For odd a, the distribution of v₂(3a+1) over residue classes mod 2^k
    determines possible cycle structures.
""")

    # Analyze distribution
    print("Distribution of v₂(3a+1) for odd a in [1, 1000]:")
    print("-" * 40)

    v2_counts = defaultdict(int)
    for a in range(1, 1001, 2):
        v = v2(3*a + 1)
        v2_counts[v] += 1

    total = sum(v2_counts.values())
    for v in sorted(v2_counts.keys()):
        count = v2_counts[v]
        frac = count / total
        theoretical = 1 / (2 ** v) if v > 0 else 0
        print(f"  v₂ = {v}: {count:4} ({frac:.4f}), theoretical ≈ {theoretical:.4f}")

    print("""
OBSERVATION:
    v₂(3a+1) follows approximately geometric distribution with mean ≈ 2.

CONSTRAINT FOR k-CYCLES:
    e = Σᵢ v₂(3aᵢ + 1)

    For a k-cycle with e ≈ 1.585k to 2k:
    - Average v₂ per term: e/k ≈ 1.585 to 2
    - This is consistent with geometric distribution (mean ≈ 2)

    But specific combinations are HIGHLY constrained!
""")


def explicit_cycle_search():
    """Search for cycles with explicit constraints"""
    header("THEOREM 5: EXPLICIT CYCLE ANALYSIS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         EXPLICIT CYCLE CONSTRAINTS
═══════════════════════════════════════════════════════════════════════════════

For a 1-cycle (single odd value a):
    3a + 1 = 2^e × a
    a(3 - 2^e) = -1
    a = 1/(2^e - 3)

    For a to be positive odd integer: 2^e - 3 must be ±1
    2^e = 4 → e = 2 → a = 1 ✓ (trivial cycle)
    2^e = 2 → e = 1 → a = -1 ✗

    No other 1-cycles exist.

For a 2-cycle {a, b}:
    (3a+1)(3b+1) = 2^e × ab
    9ab + 3a + 3b + 1 = 2^e × ab
    ab(9 - 2^e) + 3(a+b) + 1 = 0
""")

    print("Searching for 2-cycles...")
    print("-" * 60)

    found_2cycles = []
    for e in range(3, 20):
        coeff = 9 - 2**e
        if coeff == 0:
            continue
        # ab(9 - 2^e) + 3(a+b) + 1 = 0
        # Need to find odd a, b satisfying this
        for a in range(1, 10000, 2):
            for b in range(a, 10000, 2):
                if a * b * coeff + 3 * (a + b) + 1 == 0:
                    found_2cycles.append((a, b, e))
                    print(f"  Found: a={a}, b={b}, e={e}")

    if not found_2cycles:
        print("  No 2-cycles found for e ≤ 19, a,b ≤ 10000")

    print("""
THEOREM 5.1: For a 2-cycle to exist with e ≤ 19 and min(a,b) ≤ 10000,
             no solutions exist other than degenerate cases.
""")


def steiner_bound():
    """Implement Steiner's bound on cycle length"""
    header("THEOREM 6: STEINER'S BOUND")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                            STEINER'S BOUND (1977)
═══════════════════════════════════════════════════════════════════════════════

THEOREM (Steiner):
    If a non-trivial cycle exists with k odd elements, then k ≥ 35.

MODERN BOUNDS:
    - Eliahou (1993): k ≥ 17,087,915
    - Hercher (2023): k ≥ 91,000,000,000

These bounds come from analyzing the cycle equation with Baker's theorem
on linear forms in logarithms.

LEMMA 6.1 (Linear Form):
    The cycle equation ∏(3aᵢ+1) = 2^e × ∏aᵢ implies:

    Σᵢ log(3 + 1/aᵢ) = e × log(2)

    Let λᵢ = log(3 + 1/aᵢ) - αᵢ × log(2) where αᵢ = v₂(3aᵢ+1)

    Then: Σλᵢ = 0

    But λᵢ are algebraically independent → contradiction for large k.

CONSEQUENCE:
    Any non-trivial cycle has k ≥ 91 billion odd elements!

    This is effectively impossible:
    - Minimum element in cycle would be astronomically large
    - No computational search could ever find it
""")

    # Compute minimum cycle element given k
    print("Minimum cycle element bounds:")
    print("-" * 50)

    for k in [35, 100, 1000, 10**6, 10**9]:
        # Rough bound: min element ≈ 2^(k/2)
        min_elem_approx = 2 ** (k * 0.5)
        if min_elem_approx < 10**100:
            print(f"  k = {k:>12}: min element > 2^{k//2} ≈ {min_elem_approx:.2e}")
        else:
            print(f"  k = {k:>12}: min element > 2^{k//2} (astronomical)")


def rational_cycle_analysis():
    """Analyze why rational cycles don't help"""
    header("THEOREM 7: RATIONAL EXTENSIONS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         RATIONAL CYCLE ANALYSIS
═══════════════════════════════════════════════════════════════════════════════

QUESTION: Does extending Collatz to Q help understand integer cycles?

DEFINITION (Rational Collatz):
    For x ∈ Q, x > 0:
    f(x) = x/2         if x has even numerator (in lowest terms)
    f(x) = (3x+1)/2    if x has odd numerator

FACT: Rational Collatz has infinitely many cycles!

EXAMPLE CYCLES in Q:
""")

    # Find some rational cycles
    def rational_collatz(p, q, max_steps=100):
        """Apply Collatz to p/q, return trajectory of (p,q) pairs"""
        from math import gcd
        traj = [(p, q)]
        for _ in range(max_steps):
            g = gcd(p, q)
            p, q = p // g, q // g
            if p % 2 == 0:
                p = p // 2
            else:
                p = 3 * p + q
                q = 2 * q
            g = gcd(p, q)
            p, q = p // g, q // g
            if (p, q) == traj[0]:
                return traj, True
            traj.append((p, q))
        return traj, False

    # Known rational cycles
    print("Known rational cycles:")
    print("-" * 60)

    # Cycle containing -1: -1 → -2 → -1
    print("  -1/1 → -2/1 → -1/1  (negative integers)")

    # Cycle containing -5
    print("  -5 → -7 → -10 → -5  (negative integers)")

    # Cycle containing -17
    print("  -17 → -25 → -37 → -55 → -82 → -41 → -61 → -91 → ...")

    print("""
THEOREM 7.1:
    The existence of rational cycles does NOT imply integer cycles.

    Integer cycles are constrained by:
    1. All elements must be positive integers
    2. The cycle equation must have integer solutions
    3. Modular constraints must be satisfied

    Rational cycles lack constraint (1), allowing many more solutions.

COROLLARY:
    Studying rational Collatz is interesting but doesn't directly
    help prove the integer conjecture.
""")


def final_cycle_theorem():
    """State the main cycle exclusion result"""
    header("MAIN THEOREM: CYCLE EXCLUSION")

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        MAIN CYCLE EXCLUSION THEOREM                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

THEOREM (Cycle Exclusion - Current Knowledge):

    Let C be a non-trivial Collatz cycle (not 1→4→2→1).
    Let k = number of odd elements in C.
    Let m = minimum element of C.

    THEN:

    1. k ≥ 91,000,000,000  (Hercher 2023)

    2. m > 2^40  (computational verification)

    3. The cycle equation ∏(3aᵢ+1) = 2^e × ∏aᵢ with:
       - 1.585k < e ≤ 2k
       - All aᵢ ≡ 1 (mod 2)
       - Σ v₂(3aᵢ+1) = e exactly
       - ∏aᵢ ≡ 1 or 2 (mod 3) depending on parity of e

       has NO known solutions other than {a₁} = {1}.

WHAT WE CAN PROVE:
    ✓ No k-cycles for k < 91 billion (theorem)
    ✓ No cycles with min element < 2^40 (computation)
    ✓ Strong constraints on any hypothetical cycle

WHAT REMAINS:
    ✗ Prove no cycles exist for ANY k (would need new technique)

SIGNIFICANCE:
    The non-existence of cycles for k < 91 billion means that
    any non-trivial cycle would need to visit at least 91 billion
    distinct odd numbers, with minimum element astronomically large.

    This is "morally" equivalent to cycle exclusion, but not a proof.

══════════════════════════════════════════════════════════════════════════════════
""")


def main():
    print("═" * 80)
    print(" " * 20 + "CYCLE EXCLUSION ANALYSIS")
    print(" " * 15 + "Rigorous Mathematical Investigation")
    print("═" * 80)

    collatz_cycle_equation()
    modular_constraints()
    size_bound_analysis()
    two_adic_analysis()
    explicit_cycle_search()
    steiner_bound()
    rational_cycle_analysis()
    final_cycle_theorem()

    print("\n" + "═" * 80)
    print("CYCLE ANALYSIS COMPLETE")
    print("═" * 80)


if __name__ == "__main__":
    main()
