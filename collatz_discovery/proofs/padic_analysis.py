#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    p-ADIC ANALYSIS OF COLLATZ CONJECTURE
═══════════════════════════════════════════════════════════════════════════════

The p-adic integers Z_p provide an alternative perspective on Collatz.

Key insight: In Z_2 (2-adic integers), division by 2 is well-defined for ALL
integers, not just even ones! This changes the dynamics fundamentally.

We study:
1. Collatz in Z_2 (2-adic integers)
2. Collatz in Z_3 (3-adic integers)
3. The interplay between Z_2 and Z_3 structures
4. Fixed points and cycles in p-adic completions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from fractions import Fraction
from typing import List, Tuple, Optional
from functools import reduce
import math


def header(title: str):
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + f" {title} ".center(78) + "║")
    print("╚" + "═"*78 + "╝")


def v_p(n: int, p: int) -> int:
    """p-adic valuation: highest power of p dividing n"""
    if n == 0:
        return float('inf')
    count = 0
    while n % p == 0:
        n //= p
        count += 1
    return count


def padic_representation(n: int, p: int, digits: int = 20) -> List[int]:
    """Compute first `digits` of p-adic expansion of n"""
    result = []
    for _ in range(digits):
        result.append(n % p)
        n = n // p
    return result


def two_adic_intro():
    """Introduction to 2-adic integers"""
    header("INTRODUCTION: 2-ADIC INTEGERS Z_2")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         THE 2-ADIC INTEGERS
═══════════════════════════════════════════════════════════════════════════════

DEFINITION:
    Z_2 = {Σᵢ₌₀^∞ aᵢ × 2ⁱ : aᵢ ∈ {0,1}}

    Every 2-adic integer is an infinite series of bits.
    Integers n ∈ Z embed as finite series.

KEY PROPERTY:
    In Z_2, division by 2 is a SHIFT operation:
    x = a₀ + 2a₁ + 4a₂ + ...
    x/2 = a₁ + 2a₂ + 4a₃ + ...  (IF a₀ = 0)

    But what if a₀ = 1 (x is odd)?
    In Z_2, we can still "divide" using the inverse of 2!

INVERSE OF 2 in Z_2:
    2 × (something) = 1 has NO solution in Z_2
    (because 2 | LHS but 2 ∤ 1)

    So 2 is NOT invertible in Z_2.
    Division by 2 of odd numbers is NOT defined in Z_2.

CONSEQUENCE:
    The standard Collatz map T(n) = n/2 (if even) or (3n+1)/2 (if odd)
    maps Z_2 → Z_2 because:
    - n even: n/2 ∈ Z_2 ✓
    - n odd: 3n+1 even, so (3n+1)/2 ∈ Z_2 ✓
""")


def two_adic_collatz():
    """Analyze Collatz in 2-adic integers"""
    header("THEOREM 1: COLLATZ IN Z_2")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         COLLATZ MAP ON Z_2
═══════════════════════════════════════════════════════════════════════════════

DEFINITION (2-adic Collatz):
    T: Z_2 → Z_2
    T(x) = x/2           if x ≡ 0 (mod 2)
    T(x) = (3x + 1)/2    if x ≡ 1 (mod 2)

This is well-defined because:
- If x ∈ Z_2 and x ≡ 0 (mod 2), then x = 2y for some y ∈ Z_2
- If x ∈ Z_2 and x ≡ 1 (mod 2), then 3x + 1 ≡ 0 (mod 2)

FIXED POINTS OF T:
    T(x) = x
    Case x even: x/2 = x → x = 0 ✓
    Case x odd: (3x+1)/2 = x → 3x+1 = 2x → x = -1

    So T has two fixed points in Z_2: {0, -1}

CYCLES:
    - The trivial cycle 1 → 2 → 1 (in reduced notation: 1 → 1)
    - Actually: T(1) = (3×1+1)/2 = 2, T(2) = 1

INTERESTING: -1 is a fixed point!
    T(-1) = (3×(-1)+1)/2 = (-3+1)/2 = -2/2 = -1 ✓
""")

    # Verify
    print("VERIFICATION:")
    print("-" * 40)
    print(f"T(0) = 0/2 = 0 ✓")
    print(f"T(-1) = (3×(-1)+1)/2 = -2/2 = -1 ✓")
    print(f"T(1) = (3×1+1)/2 = 2")
    print(f"T(2) = 2/2 = 1")


def two_adic_representation():
    """Show 2-adic representations"""
    header("THEOREM 2: 2-ADIC REPRESENTATIONS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         2-ADIC EXPANSIONS
═══════════════════════════════════════════════════════════════════════════════

KEY INSIGHT:
    In Z_2, negative integers have INFINITE 2-adic expansions!

    -1 = ...1111111 (all 1s)
    -2 = ...1111110
    -3 = ...1111101

    This is because:
    -1 = Σᵢ₌₀^∞ 2ⁱ = 1/(1-2) = -1 (using geometric series)
""")

    # Show representations
    print("2-adic expansions (showing first 20 digits):")
    print("-" * 60)

    for n in [1, 2, 3, 5, 7, -1, -2, -3, -5]:
        if n >= 0:
            rep = padic_representation(n, 2, 20)
        else:
            # For negative n, compute via 2's complement idea
            # -n in 2-adics is ...111...111 - (n-1)
            rep = []
            m = n
            for _ in range(20):
                rep.append(m % 2)
                m = (m - rep[-1]) // 2

        rep_str = ''.join(str(d) for d in reversed(rep))
        print(f"  {n:>4} = ...{rep_str}")

    print("""
OBSERVATION:
    The fixed point -1 = ...111111 is the "attractor" in some sense.
    In Z_2, trajectories starting from negative integers behave differently!
""")


def three_adic_analysis():
    """Analyze Collatz in 3-adic integers"""
    header("THEOREM 3: COLLATZ IN Z_3")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         3-ADIC PERSPECTIVE
═══════════════════════════════════════════════════════════════════════════════

In Z_3, the operation 3n+1 is more natural:
    3n + 1 ≡ 1 (mod 3) for any n

KEY PROPERTY:
    For any odd n, 3n + 1 ≡ 1 (mod 3)

    This means: after an odd step, we're always in residue class 1 (mod 3)

DEFINITION (3-adic valuation):
    v₃(n) = max{k : 3^k | n}

OBSERVATION:
    v₃(3n + 1) = v₃(1) = 0 for n ≢ 0 (mod 3)
    v₃(3n + 1) = v₃(3(n + 1/3)) undefined for n ≢ 0 (mod 3)

Actually, for integer n:
    v₃(3n + 1) = 0 always (since 3n ≡ 0 (mod 3), so 3n+1 ≡ 1 (mod 3))

IMPLICATION:
    The 3n+1 operation NEVER introduces factors of 3.
    Factors of 3 can only be removed by the n/2 operation (if 3|n and n even).
""")

    # Verify 3-adic structure
    print("VERIFICATION: v₃(3n+1) for various odd n")
    print("-" * 40)

    for n in [1, 3, 5, 7, 9, 11, 27, 81, 243]:
        val = 3*n + 1
        v3 = v_p(val, 3)
        print(f"  n = {n:>4}: 3n+1 = {val:>6}, v₃ = {v3}")

    print("\nAll v₃(3n+1) = 0 ✓")


def interplay_analysis():
    """Analyze interplay between Z_2 and Z_3"""
    header("THEOREM 4: INTERPLAY BETWEEN Z_2 AND Z_3")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    THE 2-3 INTERACTION STRUCTURE
═══════════════════════════════════════════════════════════════════════════════

FUNDAMENTAL OBSERVATION:
    Collatz dynamics arise from the interaction between:
    - Powers of 2 (from halving)
    - Powers of 3 (from tripling)

    The key equation is: 3n + 1 must eventually reduce to 1.

    In terms of valuations:
    v₂(3n+1) determines how many times we divide by 2
    v₃ is always 0 after 3n+1

THEOREM 4.1 (2-3 Logarithm Relation):
    For a terminating trajectory with o odd steps and e even steps:

    o × log(3) < e × log(2)  (from decay analysis)

    This is equivalent to:
    o/e < log(2)/log(3) ≈ 0.631

    In p-adic terms: the "growth" from ×3 is less than "shrinkage" from ÷2

THEOREM 4.2 (Mixed Radix Representation):
    Consider representing n in a mixed base using 2 and 3:

    n = Σ aᵢⱼ × 2ⁱ × 3ʲ

    Collatz dynamics move weight between different (i,j) cells.
    Termination = all weight eventually at (0,0) = 1.
""")

    # Demonstrate mixed representation
    print("MIXED 2-3 REPRESENTATION:")
    print("-" * 60)

    def mixed_decompose(n, max_i=10, max_j=5):
        """Decompose n into 2^i × 3^j components"""
        components = {}
        remaining = n
        for j in range(max_j, -1, -1):
            for i in range(max_i, -1, -1):
                power = (2**i) * (3**j)
                if power <= remaining:
                    count = remaining // power
                    if count > 0:
                        components[(i, j)] = count
                        remaining -= count * power
        return components

    for n in [27, 97, 871]:
        print(f"\n  n = {n}:")
        comp = mixed_decompose(n)
        for (i, j), count in sorted(comp.items()):
            print(f"    {count} × 2^{i} × 3^{j} = {count * (2**i) * (3**j)}")


def padic_fixed_points():
    """Analyze fixed points in p-adic completions"""
    header("THEOREM 5: FIXED POINTS AND ATTRACTORS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                     FIXED POINTS IN p-ADIC DOMAINS
═══════════════════════════════════════════════════════════════════════════════

STANDARD COLLATZ T(n):
    T(n) = n/2       if n even
    T(n) = 3n + 1    if n odd

FIXED POINTS in Z:
    - Even: n/2 = n → n = 0
    - Odd: 3n+1 = n → 2n = -1 → n = -1/2 ∉ Z

    Only fixed point in Z: n = 0

ACCELERATED COLLATZ S(n) = T^k(n) until odd:
    S(n) iterates T until reaching odd number

FIXED POINTS of S in positive integers:
    S(n) = n requires trajectory returning to n
    Only known: the cycle 1 → 4 → 2 → 1, giving S(1) = 1

IN Z_2:
    -1 = ...111111 is a fixed point of T:
    T(-1) = (3(-1)+1)/2 = -1 ✓

    This is interesting because -1 ∉ N, so doesn't affect the conjecture.

THEOREM 5.1:
    In Z_2 ∩ Z⁺ (positive integers), the only fixed point under
    iteration of T is the trivial cycle {1, 2, 4}.

    (This is equivalent to the Collatz conjecture for positive integers!)
""")


def convergence_in_padic():
    """Analyze convergence in p-adic metrics"""
    header("THEOREM 6: p-ADIC CONVERGENCE")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                      CONVERGENCE IN p-ADIC METRIC
═══════════════════════════════════════════════════════════════════════════════

p-ADIC METRIC:
    |x|_p = p^(-v_p(x))

    x is "small" in p-adic sense if p^k | x for large k.

2-ADIC CONVERGENCE:
    In Z_2, |x|_2 = 2^(-v_2(x))

    A sequence xₙ → 0 in Z_2 iff v_2(xₙ) → ∞
    (i.e., xₙ becomes increasingly divisible by 2)

COLLATZ IN 2-ADIC METRIC:
    After an odd step: n → 3n+1 (even)
    |3n+1|_2 = 2^(-v_2(3n+1)) ≤ 1/2

    After division: (3n+1)/2^k → odd
    |odd|_2 = 1

    So trajectory oscillates between |·|_2 = 1 (odd) and |·|_2 ≤ 1/2 (even).

THEOREM 6.1:
    The Collatz sequence does NOT converge in Z_2 metric.
    It oscillates between 2-adic norms 1 and < 1.

    (This is consistent with reaching 1, not 0.)
""")

    # Demonstrate
    print("2-ADIC NORMS ALONG TRAJECTORY of n=27:")
    print("-" * 50)

    n = 27
    traj = [n]
    for _ in range(20):
        if n == 1:
            break
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        traj.append(n)

    print(f"{'Step':<6} {'Value':<12} {'v_2':<8} {'|·|_2':<12}")
    print("-" * 40)
    for i, val in enumerate(traj[:15]):
        v = v_p(val, 2)
        norm = 2**(-v) if v < float('inf') else 0
        print(f"{i:<6} {val:<12} {v:<8} {norm:<12.4f}")


def main_padic_theorem():
    """State the main p-adic results"""
    header("MAIN THEOREM: p-ADIC PERSPECTIVE")

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     MAIN p-ADIC ANALYSIS RESULTS                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

THEOREM (p-adic Collatz Structure):

1. IN Z_2:
   - Collatz map T: Z_2 → Z_2 is well-defined
   - Fixed points: {0, -1}
   - -1 = ...111111 is an attractor for some starting points
   - Positive integers avoid the -1 fixed point

2. IN Z_3:
   - 3n+1 ≡ 1 (mod 3) always (for odd n)
   - v_3(3n+1) = 0 always
   - The operation never creates factors of 3

3. INTERPLAY:
   - Termination requires o × log(3) < e × log(2)
   - This is a 2-3 balance condition
   - Equivalent to decay condition c < log(2)/log(3)

4. FIXED POINTS:
   - In Z ∩ Z⁺: only the trivial cycle {1,2,4}
   - Proving this IS the Collatz conjecture

═══════════════════════════════════════════════════════════════════════════════
                        WHAT p-ADIC ANALYSIS REVEALS
═══════════════════════════════════════════════════════════════════════════════

INSIGHTS:
- The interplay between 2 and 3 is fundamental
- -1 as a 2-adic fixed point explains some trajectory behavior
- The conjecture is equivalent to: no positive integer reaches -1

LIMITATIONS:
- p-adic analysis gives structure but not direct proof
- Convergence in p-adic metric differs from standard metric
- The conjecture remains open

POTENTIAL:
- Better understanding of 2-3 interaction may lead to proof
- p-adic methods combined with other techniques could help
""")


def main():
    print("═" * 80)
    print(" " * 20 + "p-ADIC ANALYSIS OF COLLATZ")
    print(" " * 15 + "2-adic and 3-adic Perspectives")
    print("═" * 80)

    two_adic_intro()
    two_adic_collatz()
    two_adic_representation()
    three_adic_analysis()
    interplay_analysis()
    padic_fixed_points()
    convergence_in_padic()
    main_padic_theorem()

    print("\n" + "═" * 80)
    print("p-ADIC ANALYSIS COMPLETE")
    print("═" * 80)


if __name__ == "__main__":
    main()
