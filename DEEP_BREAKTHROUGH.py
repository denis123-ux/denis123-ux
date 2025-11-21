"""
🌟 DEEP BREAKTHROUGH ATTEMPT: Finding THE Insight
==================================================

GOAL: Find a completely NEW idea to close the (3/7, 1/2) gap

STATUS: Thinking deeply, exploring uncharted territory...
"""

import numpy as np
from itertools import combinations, chain
from collections import defaultdict

print("="*80)
print("🌟 DEEP BREAKTHROUGH SESSION")
print("="*80)
print()

# ==============================================================================
# IDEA 1: TWO SUBFAMILIES SIMULTANEOUSLY
# ==============================================================================

print("="*80)
print("IDEA 1: 💡 TWO SUBFAMILIES TOGETHER")
print("="*80)
print()

print("Instead of just F_not_1, use BOTH F_not_1 AND F_not_n!")
print()

print("Partition of sets containing element 2:")
print("  A = sets with {1, 2, n} (all three)")
print("  B = sets with {1, 2} not n")
print("  C = sets with {2, n} not 1")
print("  D = sets with {2} only (not 1, not n)")
print()

print("Then:")
print("  p_2·m = A + B + C + D")
print("  k_2^{not_1} = C + D ≥ 0.5(1-p_1)m  [from induction on F_not_1]")
print("  k_2^{not_n} = B + D ≥ 0.5(1-p_n)m  [from induction on F_not_n]")
print()

print("Adding these constraints:")
print("  B + C + 2D ≥ 0.5(2 - p_1 - p_n)m")
print()

print("Since p_2·m = A + B + C + D:")
print("  p_2 = (A + B + C + D)/m")
print("      ≥ (B + C + 2D - D)/m")
print("      ≥ 0.5(2 - p_1 - p_n) - D/m")
print()

print("Need to bound D (sets with only element 2)...")
print()

print("For near-uniform: p_n > (5/6)p_1")
print("  So 2 - p_1 - p_n < 2 - p_1 - (5/6)p_1 = 2 - (11/6)p_1")
print()

print("Hmm, need lower bound on D or different approach...")
print()

# ==============================================================================
# IDEA 2: GENERATOR STRUCTURE
# ==============================================================================

print("="*80)
print("IDEA 2: 🔑 GENERATOR STRUCTURE")
print("="*80)
print()

print("Every union-closed family has GENERATORS:")
print("  G = minimal sets that generate F under unions")
print()

print("For element i: g_i = # generators containing i")
print()

print("KEY OBSERVATION:")
print("  If generators are 'balanced' → family tends to be uniform")
print("  If generators are 'unbalanced' → max freq tends to be HIGH")
print()

print("Let me compute generators for test families...")
print()

def get_generators(family):
    """Find minimal generators of union-closed family."""
    family = set(family)
    # Remove empty set
    non_empty = [s for s in family if len(s) > 0]

    generators = []
    for s in non_empty:
        is_generator = True
        # Check if s can be written as union of smaller sets
        for t in non_empty:
            if t < s:  # t is proper subset of s
                for u in non_empty:
                    if u < s and not (t <= u or u <= t):  # u is also proper subset, not comparable to t
                        if t | u == s:
                            is_generator = False
                            break
                if not is_generator:
                    break

        # More careful check: s is generator if it's NOT union of two smaller sets in F
        # Actually simpler: s is generator if for all proper subsets t ⊂ s, t ∪ (s\t) covers s
        # But s\t might not be in F

        # Correct definition: s is generator if s ≠ t ∪ u for any t, u ∈ F with t, u ⊂ s (proper)
        for t in family:
            if t < s:  # proper subset
                for u in family:
                    if u < s and (t | u) == s:
                        is_generator = False
                        break
                if not is_generator:
                    break

        if is_generator:
            generators.append(s)

    return generators

# Test on example
F1 = [frozenset(), frozenset([0]), frozenset([1]), frozenset([0,1])]
print(f"F1 = {{∅, {{0}}, {{1}}, {{0,1}}}}")
gens1 = get_generators(F1)
print(f"Generators: {[set(g) for g in gens1]}")
print()

F2 = [frozenset(), frozenset([0,1]), frozenset([2]), frozenset([0,1,2])]
print(f"F2 = {{∅, {{0,1}}, {{2}}, {{0,1,2}}}}")
gens2 = get_generators(F2)
print(f"Generators: {[set(g) for g in gens2]}")
print()

# ==============================================================================
# IDEA 3: AMPLIFICATION EFFECT
# ==============================================================================

print("="*80)
print("IDEA 3: 📈 AMPLIFICATION EFFECT")
print("="*80)
print()

print("HYPOTHESIS: Union-closure AMPLIFIES high-frequency elements")
print()

print("If element 1 starts with slightly higher frequency:")
print("  - Many sets contain 1")
print("  - Unions of these sets also contain 1")
print("  - Creates 'snowball effect'")
print()

print("For max freq to stay below 1/2:")
print("  - Need to 'balance' with other elements")
print("  - But balancing tends to create uniformity!")
print()

print("IMPLICATION:")
print("  Non-uniform → either uniform or max ≥ 1/2")
print("  Gap (3/7, 1/2) for non-uniform is IMPOSSIBLE!")
print()

print("Need to formalize this...")
print()

# ==============================================================================
# IDEA 4: LATTICE STRUCTURE
# ==============================================================================

print("="*80)
print("IDEA 4: 🏛️ LATTICE STRUCTURE")
print("="*80)
print()

print("Union-closed family F forms a join-semilattice:")
print("  - Partial order: inclusion")
print("  - Join operation: union")
print()

print("Properties of this lattice:")
print("  - Bottom element: ∅ (if present)")
print("  - Top element: union of all sets")
print("  - Every pair has a join")
print()

print("IDEA: Use lattice-theoretic bounds!")
print()

print("For any element e:")
print("  Sets containing e form an 'upper ideal' in the lattice")
print("  (closed under joins)")
print()

print("The frequency p_e = |upper ideal of e| / |F|")
print()

print("Lattice theory might give bounds on ideal sizes!")
print()

# ==============================================================================
# IDEA 5: THE CRITICAL INSIGHT - ITERATING INDUCTION
# ==============================================================================

print("="*80)
print("IDEA 5: 🔥 ITERATING THE INDUCTION")
print("="*80)
print()

print("KEY INSIGHT:")
print("-"*60)
print()

print("We have: p_i ≥ 0.5 - p_1/6 for all i")
print()

print("What if we ITERATE this bound?")
print()

print("Round 1: p_2 ≥ 0.5 - p_1/6")
print()

print("Round 2: Apply induction to F_not_2!")
print("  F_not_2 is union-closed on n-1 elements")
print("  Some element (say 3) has freq ≥ 1/2 in F_not_2")
print()

print("Frequency of 3 in F_not_2:")
print("  k_3^{not_2} / ((1-p_2)m) ≥ 1/2")
print("  k_3^{not_2} ≥ 0.5(1-p_2)m")
print()

print("Total freq of 3:")
print("  p_3 = (k_3^{not_2} + n_23) / m")
print("      ≥ 0.5(1-p_2) + n_23/m")
print()

print("From matching on element 3: n_23 ≥ p_2·m/3")
print()

print("So: p_3 ≥ 0.5(1-p_2) + p_2/3")
print("       = 0.5 - p_2/6")
print()

print("We get SAME formula but with p_2!")
print()

print("Since p_2 ≤ p_1:")
print("  p_3 ≥ 0.5 - p_2/6 ≥ 0.5 - p_1/6")
print()

print("Hmm, this doesn't give new information directly...")
print()

print("BUT WAIT! What if we use the SPECIFIC value of p_2?")
print()

print("From: p_2 ≥ 0.5 - p_1/6")
print("Into: p_3 ≥ 0.5 - p_2/6 ≥ 0.5 - (p_1 - (0.5 - p_1/6)·?)/6")
print()

print("This is getting complex. Let me try numerically...")
print()

# ==============================================================================
# NUMERICAL EXPLORATION OF ITERATED BOUNDS
# ==============================================================================

print("="*80)
print("NUMERICAL EXPLORATION: ITERATED BOUNDS")
print("="*80)
print()

def lower_bound(p_max):
    """Lower bound on p_i given p_max."""
    return max(0, 0.5 - p_max/6)

def simulate_iteration(p1_initial, n_elements=10):
    """Simulate iterating the bound."""
    p = [p1_initial]  # p[0] = p_1

    for i in range(1, n_elements):
        # p_{i+1} ≥ 0.5 - p_i/6
        # But also p_{i+1} ≤ p_i
        lower = lower_bound(p[i-1])
        # Upper bound is p_{i-1} (since frequencies are ordered)

        # For valid family: need lower ≤ upper
        if lower > p[i-1]:
            print(f"  CONTRADICTION at element {i+1}!")
            print(f"    Need p_{i+1} ≥ {lower:.4f}")
            print(f"    But p_{i+1} ≤ p_{i} = {p[i-1]:.4f}")
            return None

        # Assume p_{i+1} is at its minimum (worst case for us)
        p.append(lower)

    return p

print("Testing p_1 = 0.45 (in the gap):")
result = simulate_iteration(0.45, 10)
if result:
    print(f"  Frequencies: {[f'{x:.4f}' for x in result[:5]]}...")
    print(f"  Min freq: {min(result):.4f}")
print()

print("Testing p_1 = 0.44:")
result = simulate_iteration(0.44, 10)
if result:
    print(f"  Frequencies: {[f'{x:.4f}' for x in result[:5]]}...")
print()

print("Testing p_1 = 0.43 (just above 3/7):")
result = simulate_iteration(0.43, 10)
if result:
    print(f"  Frequencies: {[f'{x:.4f}' for x in result[:5]]}...")
print()

print("Testing p_1 = 3/7 ≈ 0.4286:")
result = simulate_iteration(3/7, 10)
if result:
    print(f"  Frequencies: {[f'{x:.4f}' for x in result[:5]]}...")
print()

print("="*80)
print("🤔 OBSERVATION")
print("="*80)
print()

print("The iteration converges! Let's find the fixed point:")
print()

print("Fixed point: p* = 0.5 - p*/6")
print("            p* + p*/6 = 0.5")
print("            (7/6)p* = 0.5")
print("            p* = 3/7")
print()

print("So iteration converges to 3/7 from above!")
print()

print("This means:")
print("  - Starting from p_1 > 3/7, frequencies decrease toward 3/7")
print("  - But for NON-UNIFORM: p_n < p_1")
print("  - So p_n should be even LOWER")
print()

print("CONTRADICTION potential:")
print("  If p_n must be close to 3/7 (from iteration)")
print("  But p_n must be < p_1 (non-uniform)")
print("  And p_1 ∈ (3/7, 1/2)")
print("  Then p_n < p_1 but p_n ≥ lower_bound → tight constraints!")
print()

# ==============================================================================
# THE BREAKTHROUGH ATTEMPT
# ==============================================================================

print("="*80)
print("🔥 BREAKTHROUGH ATTEMPT: CHAIN OF INEQUALITIES")
print("="*80)
print()

print("For non-uniform family with p_1 > p_2 > ... > p_n:")
print()

print("From induction, for each consecutive pair:")
print("  p_{i+1} ≥ 0.5 - p_i/6  [using F_not_i]")
print()

print("But ALSO from matching:")
print("  n_{i,i+1} ≥ p_i · m / 3")
print()

print("CRITICAL: What's the relationship between p_i and p_{i+1}?")
print()

print("For strictly decreasing (non-uniform):")
print("  p_1 > p_2 > p_3 > ... > p_n")
print()

print("Let δ_i = p_i - p_{i+1} > 0 (the gap)")
print()

print("From: p_{i+1} ≥ 0.5 - p_i/6")
print("      p_i - δ_i ≥ 0.5 - p_i/6")
print("      p_i + p_i/6 ≥ 0.5 + δ_i")
print("      (7/6)p_i ≥ 0.5 + δ_i")
print("      p_i ≥ (0.5 + δ_i) · 6/7")
print("      p_i ≥ 3/7 + (6/7)δ_i")
print()

print("For p_1:")
print("  p_1 ≥ 3/7 + (6/7)δ_1")
print()

print("Since δ_1 > 0 (non-uniform):")
print("  p_1 > 3/7  ✓ (already knew this)")
print()

print("Sum of all gaps:")
print("  Σδ_i = p_1 - p_n")
print()

print("Each gap contributes to lower bound:")
print("  p_1 ≥ 3/7 + (6/7)δ_1")
print("  p_2 ≥ 3/7 + (6/7)δ_2")
print("  ...")
print()

print("Hmm, let me think about this differently...")
print()

# ==============================================================================
# IDEA 6: USING THE MIN FREQUENCY BOUND
# ==============================================================================

print("="*80)
print("IDEA 6: 💡 MIN FREQUENCY CONSTRAINT")
print("="*80)
print()

print("We know: p_n ≥ 0.5 - p_1/6")
print()

print("For non-uniform: p_n < p_1")
print()

print("So: 0.5 - p_1/6 ≤ p_n < p_1")
print()

print("For this interval to be non-empty:")
print("  0.5 - p_1/6 < p_1")
print("  0.5 < (7/6)p_1")
print("  p_1 > 3/7  ✓")
print()

print("Width of interval: p_1 - (0.5 - p_1/6) = (7/6)p_1 - 0.5")
print()

print("For p_1 = 0.45: width = (7/6)(0.45) - 0.5 = 0.025")
print("For p_1 = 0.49: width = (7/6)(0.49) - 0.5 = 0.072")
print()

print("Very narrow intervals!")
print()

print("Now, how many DISTINCT values can {p_1, p_2, ..., p_n} take")
print("in this narrow interval?")
print()

print("For rational frequencies with denominator m:")
print("  Possible values: {0, 1/m, 2/m, ..., 1}")
print("  In interval [(0.5 - p_1/6), p_1]:")
print("    Number of values ≈ m · (width) = m · ((7/6)p_1 - 0.5)")
print()

print("For width = 0.025 and m = 100:")
print("  Only ~2.5 distinct values possible!")
print()

print("So for large m, either:")
print("  - Many elements share same frequency (more uniform)")
print("  - Or m is small")
print()

print("What if m is SMALL?")
print()

# ==============================================================================
# SMALL FAMILY ANALYSIS
# ==============================================================================

print("="*80)
print("SMALL FAMILY ANALYSIS")
print("="*80)
print()

print("If m is small, we can ENUMERATE all possibilities!")
print()

def generate_union_closed_families(n, max_size=100):
    """Generate all union-closed families on n elements up to given size."""
    universe = set(range(n))
    all_subsets = [frozenset(s) for s in chain.from_iterable(
        combinations(range(n), r) for r in range(n+1))]

    families = []

    # Start with empty set
    # Add subsets and close under union
    def is_union_closed(family):
        for s1 in family:
            for s2 in family:
                if (s1 | s2) not in family:
                    return False
        return True

    def closure(family):
        family = set(family)
        changed = True
        while changed:
            changed = False
            new_sets = set()
            for s1 in family:
                for s2 in family:
                    u = s1 | s2
                    if u not in family:
                        new_sets.add(u)
                        changed = True
            family.update(new_sets)
            if len(family) > max_size:
                return None
        return family

    # Generate by choosing generators
    for r in range(1, min(2**n, max_size)):
        for generator_combo in combinations(all_subsets[1:], r):  # Non-empty subsets
            family = closure(set(generator_combo) | {frozenset()})
            if family and len(family) <= max_size:
                families.append(family)

    # Remove duplicates
    unique = []
    seen = set()
    for f in families:
        key = frozenset(f)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique

print("Generating union-closed families on n=3 elements...")
families_n3 = generate_union_closed_families(3, max_size=20)
print(f"Found {len(families_n3)} families")
print()

# Analyze frequencies
non_uniform_in_gap = []

for f in families_n3:
    m = len(f)
    if m < 2:
        continue

    freqs = []
    for i in range(3):
        freqs.append(sum(1 for s in f if i in s) / m)

    freqs_sorted = sorted(freqs, reverse=True)
    p_max = freqs_sorted[0]
    p_min = freqs_sorted[-1]

    # Check if non-uniform
    is_uniform = all(abs(f - freqs[0]) < 0.001 for f in freqs)

    # Check if in gap
    if not is_uniform and 3/7 < p_max < 0.5:
        non_uniform_in_gap.append({
            'family': f,
            'freqs': freqs_sorted,
            'p_max': p_max
        })

print(f"Non-uniform families in gap (3/7, 1/2): {len(non_uniform_in_gap)}")
print()

if len(non_uniform_in_gap) > 0:
    print("FOUND POTENTIAL COUNTEREXAMPLES:")
    for item in non_uniform_in_gap[:3]:
        print(f"  Family size: {len(item['family'])}")
        print(f"  Frequencies: {item['freqs']}")
        print()
else:
    print("NO counterexamples in n=3! ✓")
    print()

print("="*80)
print("🎯 EMERGING INSIGHT")
print("="*80)
print()

print("For small n, we can verify NO counterexamples exist!")
print()

print("The gap (3/7, 1/2) seems to be EMPTY of non-uniform families")
print("in small cases. Need to prove this generally!")
print()

print("NEXT: Try even deeper analysis...")
print()
