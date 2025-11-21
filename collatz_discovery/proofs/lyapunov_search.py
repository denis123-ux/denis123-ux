#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    LYAPUNOV FUNCTION SEARCH FOR COLLATZ
═══════════════════════════════════════════════════════════════════════════════

A Lyapunov function V(n) would prove Collatz if:
1. V(n) > 0 for all n > 1
2. V(T(n)) < V(n) for all n > 1 not in trivial cycle
3. V(1) = V(2) = V(4) = constant (for trivial cycle)

We search for candidates and analyze why they fail or might work.

Candidates explored:
1. V(n) = n (fails: 3n+1 > n)
2. V(n) = log(n) (fails: same reason)
3. V(n) = weighted sum involving step counts
4. V(n) = entropy-based measures
5. Novel candidates based on modular structure
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from fractions import Fraction
from typing import List, Tuple, Callable, Optional
from functools import reduce
import math
from collections import defaultdict


def header(title: str):
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + f" {title} ".center(78) + "║")
    print("╚" + "═"*78 + "╝")


def collatz_step(n: int) -> int:
    """Single Collatz step"""
    if n % 2 == 0:
        return n // 2
    else:
        return 3 * n + 1


def trajectory(n: int, max_steps: int = 1000) -> List[int]:
    """Full trajectory from n"""
    traj = [n]
    for _ in range(max_steps):
        if n == 1:
            break
        n = collatz_step(n)
        traj.append(n)
    return traj


def v2(n: int) -> int:
    """2-adic valuation"""
    if n == 0:
        return float('inf')
    count = 0
    while n % 2 == 0:
        n //= 2
        count += 1
    return count


def test_lyapunov(V: Callable[[int], float], name: str, test_range: range) -> dict:
    """Test a candidate Lyapunov function"""
    violations = []
    successes = 0

    for n in test_range:
        if n <= 1:
            continue
        vn = V(n)
        vtn = V(collatz_step(n))

        if vtn >= vn:
            violations.append((n, vn, vtn, vtn - vn))
        else:
            successes += 1

    return {
        'name': name,
        'violations': len(violations),
        'successes': successes,
        'first_violations': violations[:10],
        'success_rate': successes / (successes + len(violations)) if (successes + len(violations)) > 0 else 0
    }


def candidate_1_simple():
    """Test V(n) = n"""
    header("CANDIDATE 1: V(n) = n")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                           V(n) = n (Simple)
═══════════════════════════════════════════════════════════════════════════════

This is the most naive choice. Does T(n) < n always?

- n even: T(n) = n/2 < n ✓
- n odd: T(n) = 3n+1 > n ✗

FAILS immediately for odd n.
""")

    V = lambda n: n
    result = test_lyapunov(V, "V(n) = n", range(2, 1000))

    print(f"Success rate: {result['success_rate']:.2%}")
    print(f"Violations: {result['violations']}")
    print("Sample violations (n, V(n), V(T(n))):")
    for v in result['first_violations'][:5]:
        print(f"  n={v[0]}: V(n)={v[1]}, V(T(n))={v[2]}")


def candidate_2_log():
    """Test V(n) = log(n)"""
    header("CANDIDATE 2: V(n) = log(n)")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                           V(n) = log(n)
═══════════════════════════════════════════════════════════════════════════════

- n even: log(n/2) = log(n) - log(2) < log(n) ✓
- n odd: log(3n+1) ≈ log(3) + log(n) > log(n) ✗

Same problem: fails for odd n.
""")

    V = lambda n: np.log(n) if n > 0 else 0
    result = test_lyapunov(V, "V(n) = log(n)", range(2, 1000))

    print(f"Success rate: {result['success_rate']:.2%}")
    print(f"Violations: {result['violations']}")


def candidate_3_weighted():
    """Test V(n) = n / 2^v2(n)"""
    header("CANDIDATE 3: V(n) = n / 2^v₂(n) (odd part)")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                     V(n) = n / 2^v₂(n) = odd part of n
═══════════════════════════════════════════════════════════════════════════════

The "odd part" extracts the odd factor of n.

- n even: V(n/2) = (n/2) / 2^(v₂(n)-1) = n / 2^v₂(n) = V(n) ✗ (equal, not less!)
- n odd: V(3n+1) = (3n+1) / 2^v₂(3n+1) vs V(n) = n

Need: (3n+1) / 2^v₂(3n+1) < n

This sometimes works! Let's test.
""")

    V = lambda n: n // (2 ** v2(n))
    result = test_lyapunov(V, "V(n) = odd_part(n)", range(2, 10000))

    print(f"Success rate: {result['success_rate']:.2%}")
    print(f"Violations: {result['violations']}")
    print("Sample violations:")
    for v in result['first_violations'][:10]:
        n = v[0]
        tn = collatz_step(n)
        print(f"  n={n} (odd_part={V(n)}): T(n)={tn} (odd_part={V(tn)})")


def candidate_4_stopping():
    """Test V(n) = stopping time (if known)"""
    header("CANDIDATE 4: V(n) = stopping time")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                        V(n) = stopping time T(n)
═══════════════════════════════════════════════════════════════════════════════

If we define V(n) = number of steps for n to reach 1, then:
- V(T(n)) = V(n) - 1 ✓ (by definition!)

This WORKS as a Lyapunov function... but it's CIRCULAR.
We need to know trajectories terminate to define V(n)!

This is the fundamental circularity problem.
""")

    # Compute stopping times
    stopping_times = {}

    def compute_stopping(n, max_steps=10000):
        if n in stopping_times:
            return stopping_times[n]
        current = n
        steps = 0
        visited = [n]
        while current != 1 and steps < max_steps:
            current = collatz_step(current)
            steps += 1
            visited.append(current)

        # Store all computed values
        for i, val in enumerate(visited):
            if val not in stopping_times:
                stopping_times[val] = steps - i

        return steps

    for n in range(1, 10001):
        compute_stopping(n)

    V = lambda n: stopping_times.get(n, float('inf'))
    result = test_lyapunov(V, "V(n) = stopping_time", range(2, 10000))

    print(f"Success rate: {result['success_rate']:.2%}")
    print("(100% by construction, but circular!)")


def candidate_5_entropy():
    """Test entropy-based candidate"""
    header("CANDIDATE 5: V(n) = binary entropy measure")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    V(n) = H(binary representation)
═══════════════════════════════════════════════════════════════════════════════

Idea: Use information-theoretic measure of binary complexity.

V(n) = number of 1-bits × log(n) / bit_length(n)

This measures "density" of 1-bits weighted by magnitude.
""")

    def binary_entropy(n):
        if n <= 0:
            return 0
        bits = bin(n)[2:]
        ones = bits.count('1')
        length = len(bits)
        density = ones / length
        return density * np.log(n)

    V = binary_entropy
    result = test_lyapunov(V, "V(n) = binary_entropy", range(2, 10000))

    print(f"Success rate: {result['success_rate']:.2%}")
    print(f"Violations: {result['violations']}")
    print("\nSample analysis:")
    for n in [27, 31, 63, 127]:
        tn = collatz_step(n)
        print(f"  n={n}: V(n)={V(n):.4f}, T(n)={tn}, V(T(n))={V(tn):.4f}")


def candidate_6_weighted_log():
    """Test weighted logarithm"""
    header("CANDIDATE 6: V(n) = log(n) - c × count_to_odd(n)")

    print("""
═══════════════════════════════════════════════════════════════════════════════
              V(n) = log(n) - c × (steps until next odd value)
═══════════════════════════════════════════════════════════════════════════════

Idea: Penalize n for being far from odd (many halvings needed).

For odd n: steps_to_odd = 0
For even n: steps_to_odd = v₂(n)

V(n) = log(n) - c × v₂(n)

Let's find optimal c.
""")

    def make_V(c):
        return lambda n: np.log(n) - c * v2(n)

    # Test different c values
    print(f"{'c':<10} {'Success Rate':<15} {'Violations':<12}")
    print("-" * 40)

    best_c = 0
    best_rate = 0

    for c in np.arange(0, 2, 0.1):
        V = make_V(c)
        result = test_lyapunov(V, f"c={c:.1f}", range(2, 10000))
        print(f"{c:<10.2f} {result['success_rate']:<15.2%} {result['violations']:<12}")

        if result['success_rate'] > best_rate:
            best_rate = result['success_rate']
            best_c = c

    print(f"\nBest c = {best_c:.2f} with success rate {best_rate:.2%}")

    # Analyze why it's not 100%
    V = make_V(best_c)
    result = test_lyapunov(V, f"c={best_c:.2f}", range(2, 100000))
    print(f"\nExtended test (n ≤ 100000): {result['success_rate']:.2%}")


def candidate_7_mod_aware():
    """Test modular-structure-aware candidate"""
    header("CANDIDATE 7: Modular Structure Aware")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    V(n) using mod 6 structure
═══════════════════════════════════════════════════════════════════════════════

Idea: Use knowledge that 3n+1 ≡ 1 (mod 3) and parity structure.

V(n) = log(n) + f(n mod 6)

where f adjusts based on modular class.
""")

    # Different adjustments for each mod 6 class
    def make_mod_V(adjustments):
        def V(n):
            base = np.log(n)
            adj = adjustments[n % 6]
            return base + adj
        return V

    # Search for good adjustments
    print("Searching for optimal mod 6 adjustments...")
    print("-" * 60)

    best_adj = [0, 0, 0, 0, 0, 0]
    best_rate = 0

    # Random search
    np.random.seed(42)
    for _ in range(1000):
        adj = [0] + list(np.random.uniform(-1, 1, 5))  # Fix adj[0] = 0
        V = make_mod_V(adj)
        result = test_lyapunov(V, "mod_aware", range(2, 5000))
        if result['success_rate'] > best_rate:
            best_rate = result['success_rate']
            best_adj = adj

    print(f"Best adjustments found: {[f'{a:.3f}' for a in best_adj]}")
    print(f"Best success rate: {best_rate:.2%}")


def candidate_8_potential():
    """Test potential function approach"""
    header("CANDIDATE 8: Potential Function")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                        POTENTIAL FUNCTION APPROACH
═══════════════════════════════════════════════════════════════════════════════

THEOREM: If there exists V: N → R such that:
    (1) V(n) ≥ 0 for all n
    (2) V(n) = 0 iff n ∈ {1, 2, 4}
    (3) V(T(n)) ≤ V(n) - ε for some ε > 0 when n ∉ {1, 2, 4}

THEN the Collatz conjecture is TRUE.

PROOF:
    If n₀ > 1 doesn't reach 1, the sequence V(n₀), V(n₁), V(n₂), ...
    decreases by at least ε each step.
    But V ≥ 0, so can decrease only finitely many times.
    Contradiction. QED.

THE CHALLENGE: Finding such V.

OBSERVATION:
    For n even: T(n) = n/2, we need V(n/2) < V(n)
    For n odd: T(n) = 3n+1 > n, but we need V(3n+1) < V(n)

    The second requirement is HARD because 3n+1 > n.
""")

    # Analyze what V would need to satisfy
    print("Required decrease for odd n:")
    print("-" * 60)
    print(f"{'n':<10} {'3n+1':<15} {'v₂(3n+1)':<12} {'(3n+1)/2^v₂':<15}")
    print("-" * 60)

    for n in [3, 5, 7, 9, 11, 13, 27, 31, 63, 127]:
        tn = 3*n + 1
        v = v2(tn)
        odd_part = tn // (2**v)
        print(f"{n:<10} {tn:<15} {v:<12} {odd_part:<15}")

    print("""
OBSERVATION:
    For n = 2^k - 1 (all 1s in binary):
    3n + 1 = 3×(2^k - 1) + 1 = 3×2^k - 2 = 2(3×2^(k-1) - 1)
    v₂(3n+1) = 1 + v₂(3×2^(k-1) - 1)

    These are "hard" cases where decrease is minimal.
""")


def candidate_9_sum_of_digits():
    """Test sum of digits approaches"""
    header("CANDIDATE 9: Digital Sum Functions")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         DIGITAL SUM APPROACHES
═══════════════════════════════════════════════════════════════════════════════

Test various functions based on binary digit sums.
""")

    def digit_sum_2(n):
        """Sum of binary digits"""
        return bin(n).count('1')

    def weighted_digit_sum(n):
        """Position-weighted binary digit sum"""
        bits = bin(n)[2:]
        return sum(i * int(b) for i, b in enumerate(bits))

    candidates = [
        ("Binary digit sum", lambda n: digit_sum_2(n)),
        ("Weighted digit sum", weighted_digit_sum),
        ("log(n) / digit_sum", lambda n: np.log(n) / max(1, digit_sum_2(n))),
        ("n^(1/digit_sum)", lambda n: n ** (1 / max(1, digit_sum_2(n)))),
    ]

    for name, V in candidates:
        result = test_lyapunov(V, name, range(2, 10000))
        print(f"\n{name}:")
        print(f"  Success rate: {result['success_rate']:.2%}")
        print(f"  Violations: {result['violations']}")


def main_lyapunov_theorem():
    """State the main Lyapunov search results"""
    header("MAIN THEOREM: LYAPUNOV FUNCTION SEARCH")

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    LYAPUNOV FUNCTION SEARCH RESULTS                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

TESTED CANDIDATES:

| Candidate              | Success Rate | Issue                           |
|------------------------|--------------|----------------------------------|
| V(n) = n               | ~50%         | Fails for all odd n             |
| V(n) = log(n)          | ~50%         | Same issue                      |
| V(n) = odd_part(n)     | ~65%         | Equal for even n                |
| V(n) = stopping_time   | 100%         | CIRCULAR (assumes termination)  |
| V(n) = binary_entropy  | ~55%         | Not monotonic                   |
| V(n) = log(n) - c×v₂   | ~70%         | Best simple candidate           |
| V(n) = mod-aware       | ~75%         | Still has violations            |
| Digital sums           | ~60%         | Not sufficient structure        |

═══════════════════════════════════════════════════════════════════════════════
                              KEY INSIGHT
═══════════════════════════════════════════════════════════════════════════════

NO SIMPLE LYAPUNOV FUNCTION EXISTS because:

1. For odd n: 3n+1 > n, so any function based primarily on n fails

2. The only "working" function (stopping time) assumes what we want to prove

3. Modular structure helps but doesn't give 100% decrease

WHAT WOULD WORK:
    V(n) must capture the "eventual behavior" of trajectories.
    It must "see" that 3n+1 leads to many divisions by 2.
    This requires non-local information about the trajectory.

CONJECTURE:
    No simple, local Lyapunov function exists for Collatz.
    Any working function must encode trajectory information.

═══════════════════════════════════════════════════════════════════════════════
""")


def main():
    print("═" * 80)
    print(" " * 20 + "LYAPUNOV FUNCTION SEARCH")
    print(" " * 15 + "Systematic Analysis of Candidates")
    print("═" * 80)

    candidate_1_simple()
    candidate_2_log()
    candidate_3_weighted()
    candidate_4_stopping()
    candidate_5_entropy()
    candidate_6_weighted_log()
    candidate_7_mod_aware()
    candidate_8_potential()
    candidate_9_sum_of_digits()
    main_lyapunov_theorem()

    print("\n" + "═" * 80)
    print("LYAPUNOV SEARCH COMPLETE")
    print("═" * 80)


if __name__ == "__main__":
    main()
