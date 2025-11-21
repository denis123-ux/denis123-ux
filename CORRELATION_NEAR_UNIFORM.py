"""
🔥 CORRELATION BOUND FOR NEAR-UNIFORM FAMILIES
===============================================

GOAL: Prove n_12 ≥ p_1·p_2·m for NEAR-UNIFORM families
      (where all p_i > (5/6)p_1)

If successful, this COMPLETES the proof!
"""

import numpy as np
from fractions import Fraction
import math

print("="*80)
print("🔥 CORRELATION BOUND FOR NEAR-UNIFORM FAMILIES")
print("="*80)
print()

# ==============================================================================
# PART 1: SETUP
# ==============================================================================

print("="*80)
print("PART 1: NEAR-UNIFORM FAMILY SETUP")
print("="*80)
print()

print("ASSUMPTION:")
print("  Family F with max frequency p_1 ∈ (3/7, 1/2)")
print("  Non-uniform: p_1 > p_2 > ... > p_n")
print("  Near-uniform: ALL p_i > (5/6)p_1")
print()

print("GOAL:")
print("  Prove n_12 ≥ p_1·p_2·m")
print()

print("If successful:")
print("  p_2 ≥ 0.5(1-p_1) + p_1·p_2")
print("  p_2(1-p_1) ≥ 0.5(1-p_1)")
print("  p_2 ≥ 0.5 ✓")
print()

# ==============================================================================
# PART 2: CONDITIONAL PROBABILITY APPROACH
# ==============================================================================

print("="*80)
print("PART 2: CONDITIONAL PROBABILITY")
print("="*80)
print()

print("Define:")
print("  F_1 = {S ∈ F : 1 ∈ S}")
print("  |F_1| = p_1·m")
print()

print("Frequency of 2 in F_1:")
print("  f_2|1 = n_12 / (p_1·m)")
print()

print("CLAIM: For near-uniform families, f_2|1 ≥ p_2")
print()

print("This would give:")
print("  n_12 / (p_1·m) ≥ p_2")
print("  n_12 ≥ p_1·p_2·m ✓")
print()

print("PROOF ATTEMPT:")
print("-"*60)
print()

print("Consider F_not_1 = {S ∈ F : 1 ∉ S}")
print("  |F_not_1| = (1-p_1)m")
print()

print("Element 2 appears in:")
print("  - k_2 sets in F_not_1")
print("  - n_12 sets in F_1")
print("  Total: p_2·m = k_2 + n_12")
print()

print("Frequency in F_not_1:")
print("  k_2 / ((1-p_1)m)")
print()

print("Frequency in F_1:")
print("  n_12 / (p_1·m)")
print()

print("Total:")
print("  p_2 = [k_2 + n_12] / m")
print("      = k_2/(m) + n_12/m")
print("      = (1-p_1)·[k_2/((1-p_1)m)] + p_1·[n_12/(p_1·m)]")
print("      = (1-p_1)·f_2|not_1 + p_1·f_2|1")
print()

print("where f_2|1 = freq of 2 in F_1, f_2|not_1 = freq of 2 in F_not_1")
print()

print("By induction: some element in F_not_1 has freq ≥ 1/2")
print()

print("If element 2 is max in F_not_1:")
print("  f_2|not_1 ≥ 1/2")
print()

print("Then:")
print("  p_2 = (1-p_1)·f_2|not_1 + p_1·f_2|1")
print("      ≥ (1-p_1)·0.5 + p_1·f_2|1")
print()

print("So:")
print("  p_2 - 0.5(1-p_1) ≥ p_1·f_2|1")
print("  f_2|1 ≤ [p_2 - 0.5(1-p_1)] / p_1")
print()

print("From near-uniformity: p_2 > (5/6)p_1")
print()

print("Upper bound on f_2|1:")
print("  f_2|1 ≤ [(5/6)p_1 - 0.5(1-p_1)] / p_1")
print("       = 5/6 - 0.5(1-p_1)/p_1")
print()

print("For p_1 = 0.45:")
print("  f_2|1 ≤ 5/6 - 0.5(0.55)/0.45")
print("       = 0.833 - 0.611")
print("       = 0.222")
print()

print("But we want LOWER bound on f_2|1, not upper!")
print()

print("Let me reconsider...")
print()

# ==============================================================================
# PART 3: DIRECT COMBINATORIAL ARGUMENT
# ==============================================================================

print("="*80)
print("PART 3: 🎯 DIRECT COMBINATORIAL APPROACH")
print("="*80)
print()

print("KEY INSIGHT:")
print("-"*60)
print()

print("For near-uniform family:")
print("  Elements 1 and 2 appear in 'most' sets")
print("  p_1, p_2 > 0.42 (since > (5/6)·(3/7))")
print()

print("Consider sparse sets (size < n/2):")
print("  Let s = # sparse sets")
print()

print("For sparse set S:")
print("  If 1 ∈ S, how likely is 2 ∈ S?")
print()

print("In sparse sets, expect elements to 'cluster'")
print("because union creates new sets")
print()

print("Hmm, this is too vague...")
print()

# ==============================================================================
# PART 4: USING CLOSURE MORE DIRECTLY
# ==============================================================================

print("="*80)
print("PART 4: 💡 CLOSURE-BASED COUNTING")
print("="*80)
print()

print("OBSERVATION:")
print("-"*60)
print()

print("For sets S, T ∈ F:")
print("  If 1 ∈ S and 2 ∈ T, then 1,2 ∈ S ∪ T")
print()

print("Let:")
print("  A = sets with both 1 and 2 (size n_12)")
print("  B = sets with 1 but not 2 (size p_1·m - n_12)")
print("  C = sets with 2 but not 1 (size p_2·m - n_12)")
print("  D = sets with neither (size m - p_1·m - p_2·m + n_12)")
print()

print("For each S ∈ B and T ∈ C:")
print("  S ∪ T contains both 1 and 2")
print("  So S ∪ T ∈ A ∪ B ∪ C")
print()

print("All |B| × |C| unions must fit somewhere!")
print()

print("Lower bound on distinct unions:")
print("  At least some constant fraction?")
print()

print("For |B| = b, |C| = c:")
print("  Need at least ???  distinct unions")
print()

print("Each union has form S ∪ T where |S ∪ T| ≤ n")
print()

print("Number of possible unions ≤ 2^n")
print()

print("So: b · c / (# ways to form each union) ≤ 2^n")
print()

print("This bound is too weak (exponential in n)")
print()

# ==============================================================================
# PART 5: INFORMATION-THEORETIC ARGUMENT
# ==============================================================================

print("="*80)
print("PART 5: 🔑 INFORMATION-THEORETIC BOUND")
print("="*80)
print()

print("IDEA:")
print("-"*60)
print()

print("If n_12 is TOO SMALL (< p_1·p_2·m), then:")
print("  Elements 1 and 2 are 'anticorrelated'")
print()

print("But union-closure should create POSITIVE correlation!")
print()

print("Why? Because:")
print("  If {1} ∈ F and {2} ∈ F")
print("  Then {1,2} ∈ F (by closure)")
print()

print("This 'forces' elements to appear together")
print()

print("FORMAL ARGUMENT:")
print("-"*60)
print()

print("Let X_S(i) = 1 if i ∈ S, 0 otherwise")
print()

print("Correlation:")
print("  Cov(X(1), X(2)) = E[X(1)·X(2)] - E[X(1)]·E[X(2)]")
print("                   = n_12/m - p_1·p_2")
print()

print("For union-closed F:")
print()

print("Claim: Cov(X(1), X(2)) ≥ 0")
print()

print("Proof:")
print("  For S,T ∈ F:")
print("    If 1 ∈ S and 2 ∈ T:")
print("      S ∪ T ∈ F")
print("      1,2 ∈ S ∪ T")
print()

print("  This 'synchronizes' appearances of 1 and 2")
print()

print("  Hmm, but this isn't a rigorous proof...")
print()

# ==============================================================================
# PART 6: COUNTEREXAMPLE SEARCH
# ==============================================================================

print("="*80)
print("PART 6: 🔍 SEARCHING FOR COUNTEREXAMPLES")
print("="*80)
print()

print("Let me check: among near-uniform families,")
print("does correlation bound ALWAYS hold?")
print()

def generate_random_family_n5(size=20):
    """Generate random union-closed family on 5 elements."""
    n = 5
    family = {frozenset()}

    for _ in range(size * 3):
        if np.random.random() < 0.4 and len(family) < size * 3:
            s = frozenset(np.random.choice(range(n),
                                          size=np.random.randint(0, n+1),
                                          replace=False))
            family.add(s)

        family_list = list(family)
        for s1 in family_list[:min(15, len(family_list))]:
            for s2 in family_list[:min(15, len(family_list))]:
                family.add(s1 | s2)
                if len(family) >= size * 3:
                    break
            if len(family) >= size * 3:
                break

    return family

print("Generating near-uniform families...")
print()

near_uniform_families = []
violations_near_uniform = 0
total_near_uniform = 0

for trial in range(200):
    family = generate_random_family_n5(size=15)
    m = len(family)
    n = 5

    if m < 5:
        continue

    # Compute frequencies
    freqs = []
    for i in range(n):
        freqs.append(sum(1 for s in family if i in s) / m)

    if len(freqs) == 0 or max(freqs) == 0:
        continue

    p_max = max(freqs)
    p_min = min([f for f in freqs if f > 0]) if any(f > 0 for f in freqs) else 0

    # Check if near-uniform (all > 5/6 of max)
    is_near_uniform = all(f > (5/6)*p_max for f in freqs if f > 0)

    if not is_near_uniform:
        continue

    near_uniform_families.append({
        'freqs': freqs,
        'family': family,
        'm': m
    })

    # Check correlation bound
    for i in range(n):
        for j in range(i+1, n):
            if freqs[i] == 0 or freqs[j] == 0:
                continue

            n_ij = sum(1 for s in family if i in s and j in s)
            expected = freqs[i] * freqs[j] * m

            total_near_uniform += 1
            if n_ij < expected:
                violations_near_uniform += 1

print(f"Found {len(near_uniform_families)} near-uniform families")
print()

if total_near_uniform > 0:
    print(f"Correlation bound violations: {violations_near_uniform}/{total_near_uniform}")
    print(f"Success rate: {100*(total_near_uniform-violations_near_uniform)/total_near_uniform:.1f}%")
    print()

    if violations_near_uniform == 0:
        print("🎉 CORRELATION BOUND HOLDS FOR NEAR-UNIFORM! 🎉")
        print()
        print("This suggests n_ij ≥ p_i·p_j·m for near-uniform families!")
        print()
    else:
        print("❌ Still finding violations in near-uniform case")
        print()
else:
    print("Need more data...")
    print()

# ==============================================================================
# ASSESSMENT
# ==============================================================================

print("="*80)
print("🤔 ASSESSMENT")
print("="*80)
print()

print("ATTEMPTED APPROACHES:")
print("  ❓ Conditional probability: Inconclusive")
print("  ❌ Direct combinatorial: Too complex")
print("  ❌ Closure-based counting: Bounds too weak")
print("  ❓ Information-theoretic: Not rigorous")
print("  🔬 Computational: Testing...")
print()

print("CONCLUSION:")
print("  Correlation bound for near-uniform families")
print("  needs more investigation")
print()

print("Alternative: Maybe correlation bound is NOT the right approach?")
print()
