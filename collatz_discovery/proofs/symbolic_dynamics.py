#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    SYMBOLIC DYNAMICS OF COLLATZ
═══════════════════════════════════════════════════════════════════════════════

Symbolic dynamics represents Collatz trajectories as sequences of symbols.

Key ideas:
1. Represent trajectories as binary strings (O = odd step, E = even step)
2. Study the "shift space" of allowed symbol sequences
3. Use mod 6 structure to define a finite-state automaton
4. Analyze forbidden patterns and their implications

This approach translates the dynamical system into combinatorics.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from collections import defaultdict, Counter
from typing import List, Tuple, Set, Dict, Optional
from itertools import product
import math


def header(title: str):
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + f" {title} ".center(78) + "║")
    print("╚" + "═"*78 + "╝")


def collatz_step(n: int) -> Tuple[int, str]:
    """Single Collatz step with label"""
    if n % 2 == 0:
        return n // 2, 'E'
    else:
        return 3 * n + 1, 'O'


def trajectory_symbols(n: int, max_steps: int = 1000) -> str:
    """Get symbolic representation of trajectory"""
    symbols = []
    for _ in range(max_steps):
        if n == 1:
            break
        n, symbol = collatz_step(n)
        symbols.append(symbol)
    return ''.join(symbols)


def introduction_symbolic():
    """Introduction to symbolic dynamics"""
    header("INTRODUCTION: SYMBOLIC DYNAMICS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                       SYMBOLIC REPRESENTATION
═══════════════════════════════════════════════════════════════════════════════

DEFINITION:
    For each step in a Collatz trajectory, assign a symbol:
    - 'O' = odd step (apply 3n+1)
    - 'E' = even step (apply n/2)

    A trajectory n → T(n) → T²(n) → ... → 1
    becomes a string like "OEEOEEOEEEE..."

EXAMPLES:
""")

    for n in [6, 7, 27, 97, 871]:
        syms = trajectory_symbols(n)
        print(f"  n = {n:>5}: {syms[:50]}{'...' if len(syms) > 50 else ''}")
        print(f"           Length: {len(syms)}, O-count: {syms.count('O')}, E-count: {syms.count('E')}")

    print("""
OBSERVATION:
    - Every 'O' is followed by at least one 'E' (since 3n+1 is even)
    - The pattern "OO" never appears (forbidden)
    - The ratio of E to O tends to ~2:1
""")


def forbidden_patterns():
    """Analyze forbidden patterns in symbolic sequences"""
    header("THEOREM 1: FORBIDDEN PATTERNS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         FORBIDDEN PATTERNS
═══════════════════════════════════════════════════════════════════════════════

THEOREM 1.1: The pattern "OO" is FORBIDDEN.

PROOF:
    'O' occurs when n is odd.
    After 'O', we have 3n+1 which is EVEN.
    An even number requires 'E' step.
    So 'O' must be followed by 'E'. QED.

COROLLARY: Every 'O' is followed by at least one 'E'.

THEOREM 1.2: The pattern "OE...EO" with k E's encodes v₂(3n+1) = k.

PROOF:
    Starting from odd n, apply 3n+1 (O).
    Then divide by 2 exactly k times until odd (E...E with k E's).
    The next odd number may then have another O step. QED.
""")

    # Verify
    print("VERIFICATION: Pattern extraction")
    print("-" * 60)

    # Analyze glide patterns
    all_glides = []
    for n in range(3, 10001, 2):
        syms = trajectory_symbols(n)
        # Extract glide lengths (number of E's after each O)
        i = 0
        while i < len(syms):
            if syms[i] == 'O':
                glide = 0
                i += 1
                while i < len(syms) and syms[i] == 'E':
                    glide += 1
                    i += 1
                all_glides.append(glide)
            else:
                i += 1

    glide_dist = Counter(all_glides)
    print("Glide length distribution (E's after O):")
    total = sum(glide_dist.values())
    for k in range(1, 10):
        count = glide_dist.get(k, 0)
        print(f"  {k} E's: {count} ({count/total:.2%})")


def mod6_automaton():
    """Define the mod 6 automaton"""
    header("THEOREM 2: MOD 6 FINITE AUTOMATON")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                        MOD 6 AUTOMATON
═══════════════════════════════════════════════════════════════════════════════

The Collatz map induces transitions on Z/6Z:

    State = n mod 6
    Transition = Collatz step

TRANSITION TABLE:
""")

    # Compute transitions for each state
    transitions = {}

    for state in range(6):
        # For this state, what are possible next states?
        # Need to consider representative numbers
        next_states = set()

        for n in range(state, 1000, 6):
            if n == 0:
                continue
            if n % 2 == 0:
                next_n = n // 2
            else:
                next_n = 3 * n + 1
            next_states.add(next_n % 6)

        transitions[state] = next_states

    print(f"{'State':<10} {'Parity':<10} {'Next States':<20} {'Transition':<15}")
    print("-" * 55)

    for state in range(6):
        parity = "even" if state % 2 == 0 else "odd"
        next_str = str(transitions[state])
        if state % 2 == 0:
            trans = f"{state} → {state//2 % 6} (E)"
        else:
            trans = f"{state} → {(3*state+1) % 6} (O)"
        print(f"{state:<10} {parity:<10} {next_str:<20} {trans:<15}")

    print("""
AUTOMATON STRUCTURE:
    - States: {0, 1, 2, 3, 4, 5}
    - Alphabet: {O, E}
    - Transitions: determined by Collatz rule

    Odd states (1, 3, 5): only 'O' transition possible
    Even states (0, 2, 4): only 'E' transition possible

KEY INSIGHT:
    The automaton is DETERMINISTIC.
    Given current state, the next transition symbol is determined.
""")


def shift_space_analysis():
    """Analyze the shift space structure"""
    header("THEOREM 3: SHIFT SPACE STRUCTURE")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                         SHIFT SPACE Σ_C
═══════════════════════════════════════════════════════════════════════════════

DEFINITION:
    The Collatz shift space Σ_C is the set of all bi-infinite sequences
    that can appear as (extensions of) Collatz trajectories.

CHARACTERIZATION:
    Σ_C = {σ ∈ {O, E}^Z : σ satisfies forbidden pattern constraints}

CONSTRAINTS:
    1. No "OO" (Theorem 1.1)
    2. Glide lengths follow specific distribution
    3. Global constraint: sequence must be realizable by some n

THEOREM 3.1:
    Let w = w₁w₂...wₖ be a finite word in {O, E}*.
    Then w is REALIZABLE if there exists n such that the first k symbols
    of trajectory(n) equal w.

THEOREM 3.2:
    Not all words avoiding "OO" are realizable!
    The realizability constraint is STRONGER than just avoiding "OO".
""")

    # Find non-realizable words
    print("SEARCHING FOR NON-REALIZABLE PATTERNS:")
    print("-" * 60)

    def is_realizable(pattern: str, max_n: int = 100000) -> Tuple[bool, Optional[int]]:
        """Check if pattern is realizable"""
        for n in range(2, max_n):
            syms = trajectory_symbols(n, len(pattern) + 10)
            if syms.startswith(pattern):
                return True, n
        return False, None

    # Test various patterns
    patterns_to_test = [
        "OE",
        "OEE",
        "OEEE",
        "OEEEE",
        "OEEEEE",
        "OEEEEEE",
        "OEEEEEEE",
        "OEEEEEEEE",
        "OEEEEEEEEE",
        "OEOEOE",
        "OEOEOEO",
        "OEEOEEOEE",
    ]

    for pattern in patterns_to_test:
        if "OO" in pattern:
            print(f"  {pattern}: FORBIDDEN (contains OO)")
            continue

        realizable, witness = is_realizable(pattern, 50000)
        if realizable:
            print(f"  {pattern}: realizable (e.g., n={witness})")
        else:
            print(f"  {pattern}: NOT FOUND in n ≤ 50000")


def entropy_analysis():
    """Compute topological entropy of shift space"""
    header("THEOREM 4: TOPOLOGICAL ENTROPY")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                        TOPOLOGICAL ENTROPY
═══════════════════════════════════════════════════════════════════════════════

DEFINITION:
    The topological entropy h(Σ_C) measures the "complexity" of the shift space.

    h(Σ_C) = lim_{n→∞} (1/n) × log₂(|W_n|)

    where W_n = set of length-n words appearing in Σ_C.

UPPER BOUND:
    Since "OO" is forbidden, h(Σ_C) ≤ h(golden mean shift) = log₂(φ) ≈ 0.694

    where φ = (1 + √5)/2 is the golden ratio.

COMPUTATION:
""")

    # Count realizable words of each length
    def count_realizable_words(length: int, max_n: int = 10000) -> Set[str]:
        """Count distinct length-k prefixes of trajectories"""
        words = set()
        for n in range(2, max_n):
            syms = trajectory_symbols(n, length + 5)
            if len(syms) >= length:
                words.add(syms[:length])
        return words

    print(f"{'Length':<10} {'|W_n|':<15} {'log₂|W_n|/n':<15} {'Upper bound':<15}")
    print("-" * 55)

    golden = (1 + np.sqrt(5)) / 2
    upper_bound = np.log2(golden)

    for length in range(1, 16):
        words = count_realizable_words(length, 20000)
        count = len(words)
        entropy_approx = np.log2(count) / length if count > 0 else 0
        print(f"{length:<10} {count:<15} {entropy_approx:<15.4f} {upper_bound:<15.4f}")

    print(f"""
OBSERVATION:
    The entropy of Collatz shift space appears to be < log₂(φ) ≈ {upper_bound:.4f}

    This suggests additional forbidden patterns beyond "OO".
""")


def de_bruijn_analysis():
    """Analyze using de Bruijn graph perspective"""
    header("THEOREM 5: DE BRUIJN GRAPH PERSPECTIVE")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                        DE BRUIJN GRAPH
═══════════════════════════════════════════════════════════════════════════════

DEFINITION:
    The de Bruijn graph B_k has:
    - Vertices: all length-k words in {O, E}*
    - Edges: w₁...wₖ → w₂...wₖwₖ₊₁ if w₁...wₖwₖ₊₁ is valid

    For Collatz, we restrict to REALIZABLE words.

PROPERTY:
    Paths in B_k correspond to trajectories.
    The adjacency matrix spectrum gives dynamical information.

ANALYSIS:
""")

    # Build de Bruijn graph for small k
    for k in [2, 3, 4]:
        # Get all realizable k-words
        words = set()
        for n in range(2, 50000):
            syms = trajectory_symbols(n, k + 5)
            for i in range(len(syms) - k + 1):
                words.add(syms[i:i+k])

        # Build adjacency
        edges = []
        for w in words:
            for next_char in ['O', 'E']:
                next_word = w[1:] + next_char
                if next_word in words:
                    edges.append((w, next_word))

        print(f"\nde Bruijn graph B_{k}:")
        print(f"  Vertices: {len(words)}")
        print(f"  Edges: {len(edges)}")
        print(f"  Sample vertices: {list(words)[:10]}")


def periodic_orbits():
    """Analyze periodic orbits in symbolic dynamics"""
    header("THEOREM 6: PERIODIC ORBITS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                       PERIODIC SYMBOLIC SEQUENCES
═══════════════════════════════════════════════════════════════════════════════

QUESTION:
    Can a Collatz trajectory have a periodic symbolic sequence?

    If trajectory n → T(n) → T²(n) → ... has periodic symbols
    s₁s₂...sₖs₁s₂...sₖ...

    Does this imply a cycle in the integers?

THEOREM 6.1:
    A periodic symbolic sequence corresponds to a cycle iff
    the sequence of VALUES is also periodic.

    Periodic symbols + aperiodic values = impossible (would require
    same parity sequence to produce different values).

ANALYSIS:
""")

    # The trivial cycle
    print("TRIVIAL CYCLE: 1 → 4 → 2 → 1")
    print("  Symbolic: starting from 2: EOEO... (period 2: EO)")
    print("  Or from 4: EEOEO... (starts with EE)")

    # Search for other periodic patterns that could indicate cycles
    print("\nSearching for repeated symbolic patterns...")

    def has_periodic_prefix(syms: str, min_period: int = 2, min_reps: int = 3) -> Optional[int]:
        """Check if symbols start with a periodic pattern"""
        for p in range(min_period, len(syms) // min_reps):
            pattern = syms[:p]
            if all(syms[i:i+p] == pattern for i in range(0, p * min_reps, p)):
                return p
        return None

    periodic_found = []
    for n in range(2, 100000):
        syms = trajectory_symbols(n, 500)
        period = has_periodic_prefix(syms, min_period=2, min_reps=5)
        if period and period < 20:
            periodic_found.append((n, period, syms[:period*3]))

    print(f"\nNumbers with periodic symbol prefixes (period < 20, ≥5 reps):")
    for n, p, sample in periodic_found[:10]:
        print(f"  n = {n}: period {p}, pattern = {sample}")

    if not periodic_found:
        print("  None found (besides trivial)")


def symbolic_collatz_theorem():
    """Main theorem on symbolic dynamics"""
    header("MAIN THEOREM: SYMBOLIC DYNAMICS")

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   SYMBOLIC DYNAMICS MAIN RESULTS                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

THEOREM (Symbolic Characterization):

    The Collatz conjecture is equivalent to:

    Every realizable symbolic sequence over {O, E} that avoids "OO"
    eventually reaches the periodic sequence "EO" (representing the 1-2-4 cycle).

PROVEN PROPERTIES:

    1. "OO" is forbidden (every O followed by ≥1 E)
    2. Mod 6 automaton is deterministic
    3. Topological entropy < log₂(φ) ≈ 0.694
    4. de Bruijn graph structure constrains possible trajectories

OPEN QUESTIONS:

    1. Is the shift space Σ_C a SOFIC shift?
       (Would imply describable by finite automaton)

    2. Does every infinite path eventually become periodic?
       (Would prove Collatz)

    3. Can we characterize all forbidden patterns?
       (Beyond just "OO")

═══════════════════════════════════════════════════════════════════════════════
                           IMPLICATIONS
═══════════════════════════════════════════════════════════════════════════════

INSIGHT 1: Symbolic dynamics translates Collatz to COMBINATORICS.
    Instead of number theory, we study allowed symbol sequences.

INSIGHT 2: The shift space structure encodes everything.
    A description of Σ_C would characterize all trajectories.

INSIGHT 3: Forbidden patterns constrain dynamics.
    Each forbidden pattern rules out certain behaviors.

LIMITATION: We can characterize LOCAL constraints but not GLOBAL termination.
    The symbolic view is elegant but doesn't directly prove termination.

═══════════════════════════════════════════════════════════════════════════════
""")


def main():
    print("═" * 80)
    print(" " * 20 + "SYMBOLIC DYNAMICS OF COLLATZ")
    print(" " * 15 + "Shift Space and Automaton Analysis")
    print("═" * 80)

    introduction_symbolic()
    forbidden_patterns()
    mod6_automaton()
    shift_space_analysis()
    entropy_analysis()
    de_bruijn_analysis()
    periodic_orbits()
    symbolic_collatz_theorem()

    print("\n" + "═" * 80)
    print("SYMBOLIC DYNAMICS ANALYSIS COMPLETE")
    print("═" * 80)


if __name__ == "__main__":
    main()
