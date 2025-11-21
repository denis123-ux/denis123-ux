"""
🔥 IMPROVED MATCHING BOUND FOR NEAR-UNIFORM FAMILIES
=====================================================

KEY INSIGHT: For near-uniform families (all p_i > (5/6)p_1),
the matching bound n_12 ≥ p_1·m/3 can be IMPROVED!

GOAL: Prove tighter bound on n_12 for near-uniform case
"""

import numpy as np
from fractions import Fraction
import math

print("="*80)
print("🔥 IMPROVED MATCHING FOR NEAR-UNIFORM FAMILIES")
print("="*80)
print()

# ==============================================================================
# PART 1: RECAP OF MATCHING ARGUMENT
# ==============================================================================

print("="*80)
print("PART 1: STANDARD MATCHING BOUND")
print("="*80)
print()

print("Standard argument:")
print("  Bipartite graph:")
print("    Left: Sparse sets (size < n/2)")
print("    Right: Dense sets (size ≥ n/2)")
print("    Edge: (S,D) if S ⊂ D and D\\S contains only element 1")
print()

print("Matching gives:")
print("  # edges ≤ min(s, d)")
print("  But also: # edges = Σ_{S sparse} (# dense D with D\\S = {1})")
print()

print("For element 1 with freq p_1:")
print("  Total edges ≥ ...")
print("  Leads to: n_12 ≥ p_1·m/3")
print()

print("This is GENERAL bound, not using near-uniformity!")
print()

# ==============================================================================
# PART 2: NEAR-UNIFORM SPECIFIC BOUND
# ==============================================================================

print("="*80)
print("PART 2: 🎯 EXPLOITING NEAR-UNIFORMITY")
print("="*80)
print()

print("For near-uniform family:")
print("  ALL p_i > (5/6)p_1")
print()

print("This means element 2 appears in > (5/6)p_1·m sets")
print()

print("Partition F into:")
print("  A: Sets containing both 1 and 2 (size n_12)")
print("  B: Sets with 1 but not 2 (size p_1·m - n_12)")
print("  C: Sets with 2 but not 1 (size p_2·m - n_12)")
print("  D: Sets with neither (size m - p_1·m - p_2·m + n_12)")
print()

print("Total: A + B + C + D = m ✓")
print()

print("CLOSURE CONSTRAINT:")
print("-"*60)
print()

print("For any S ∈ B and T ∈ C:")
print("  S ∪ T ∈ F (by closure)")
print("  S ∪ T contains both 1 and 2")
print("  So S ∪ T ∈ A ∪ B ∪ C (not D)")
print()

print("Key observation: How many DISTINCT unions?")
print()

print("If all unions were distinct:")
print("  |B| · |C| ≤ |F| = m")
print("  (p_1·m - n_12)(p_2·m - n_12) ≤ m²")
print()

print("But unions might overlap!")
print()

print("Better: Count unions that land in EACH category")
print()

print("For S ∈ B, T ∈ C:")
print("  S ∪ T ∈ A if S ∪ T = some set in A")
print("  S ∪ T ∈ B if 2 ∈ T but somehow not in S ∪ T (impossible!)")
print("  S ∪ T ∈ C if 1 ∈ S but somehow not in S ∪ T (impossible!)")
print()

print("So S ∪ T ∈ A always!")
print()

print("So all |B| × |C| unions land in A (possibly with repetition)")
print()

print("BETTER CONSTRAINT:")
print("-"*60)
print()

print("Each set in A can be formed as S ∪ T in AT MOST certain ways")
print()

print("For set Z ∈ A (contains both 1 and 2):")
print("  How many ways to write Z = S ∪ T with S ∈ B, T ∈ C?")
print()

print("  S ⊂ Z must contain 1 but not 2")
print("  T ⊂ Z must contain 2 but not 1")
print("  S ∪ T = Z")
print()

print("Let Z = {1, 2, a_1, a_2, ..., a_k} where a_i ∉ {1,2}")
print()

print("Elements of Z \\ {1,2} can be distributed:")
print("  - Some go to S")
print("  - Some go to T")
print("  - Each element must go to at least one")
print()

print("By inclusion-exclusion:")
print("  # ways = 3^k (each element: in S only, in T only, or in both)")
print()

print("For |Z| = r:")
print("  k = r - 2")
print("  # ways ≤ 3^(r-2)")
print()

print("CONSTRAINT:")
print("  |B| · |C| ≤ Σ_{Z ∈ A} 3^(|Z|-2)")
print()

print("Hmm, this depends on size distribution of A...")
print()

# ==============================================================================
# PART 3: SIMPLER APPROACH - USING NEAR-UNIFORMITY DIRECTLY
# ==============================================================================

print("="*80)
print("PART 3: 💡 DIRECT APPROACH WITH NEAR-UNIFORMITY")
print("="*80)
print()

print("KEY REALIZATION:")
print("-"*60)
print()

print("We have TWO constraints on p_2:")
print()

print("  (1) From near-uniformity: p_2 > (5/6)p_1")
print("  (2) From induction: p_2 ≥ 0.5(1-p_1) + n_12/m")
print()

print("These give:")
print("  (5/6)p_1 < 0.5(1-p_1) + n_12/m")
print("  (5/6)p_1 < 0.5 - 0.5p_1 + n_12/m")
print("  (5/6)p_1 + 0.5p_1 < 0.5 + n_12/m")
print("  (4/3)p_1 < 0.5 + n_12/m")
print("  n_12/m > (4/3)p_1 - 0.5")
print()

print("So: n_12 > ((4/3)p_1 - 0.5)m")
print()

print("For p_1 > 3/8 = 0.375:")
print("  (4/3)p_1 - 0.5 > 0")
print("  So n_12 > 0 (trivial)")
print()

print("For p_1 = 0.45:")
print("  n_12 > ((4/3)·0.45 - 0.5)m = (0.6 - 0.5)m = 0.1m")
print()

print("Compare to matching bound:")
print("  n_12 ≥ p_1·m/3 = 0.45m/3 = 0.15m")
print()

print("Matching bound is STRONGER!")
print()

print("So near-uniformity alone doesn't improve n_12 bound directly...")
print()

# ==============================================================================
# PART 4: USING MULTIPLE ELEMENTS
# ==============================================================================

print("="*80)
print("PART 4: 🎯 USING ELEMENT 3")
print("="*80)
print()

print("We have:")
print("  p_1 > p_2 > p_3")
print("  All > (5/6)p_1")
print()

print("Apply induction argument to element 3:")
print("  p_3 ≥ 0.5(1-p_1) + n_13/m")
print()

print("where n_13 = # sets with both 1 and 3")
print()

print("From matching: n_13 ≥ p_1·m/3")
print()

print("So: p_3 ≥ 0.5(1-p_1) + p_1/3 = 0.5 - p_1/6")
print()

print("But also: p_3 > (5/6)p_1")
print()

print("Same inequality as for p_2!")
print()

print("In fact, for ALL elements i:")
print("  p_i ≥ 0.5 - p_1/6")
print("  p_i > (5/6)p_1")
print()

print("Both constraints must hold!")
print()

print("For which p_1 are both satisfied?")
print()

print("Need:")
print("  0.5 - p_1/6 ≤ (5/6)p_1  (lower bound doesn't exceed constraint)")
print("  0.5 ≤ (5/6)p_1 + p_1/6")
print("  0.5 ≤ p_1((5/6) + (1/6))")
print("  0.5 ≤ p_1")
print()

print("🎉🎉🎉 CONTRADICTION! 🎉🎉🎉")
print()

print("We need p_1 ≥ 0.5, but we assumed p_1 < 0.5!")
print()

print("WAIT - let me verify this carefully...")
print()

# ==============================================================================
# PART 5: CAREFUL VERIFICATION
# ==============================================================================

print("="*80)
print("PART 5: 🔍 CAREFUL VERIFICATION")
print("="*80)
print()

print("We have for element i:")
print()

print("  Lower bound from induction:")
print("    p_i ≥ 0.5(1-p_1) + n_1i/m ≥ 0.5(1-p_1) + p_1/3")
print("    p_i ≥ 0.5 - p_1/6")
print()

print("  Lower bound from near-uniformity:")
print("    p_i > (5/6)p_1")
print()

print("For BOTH to hold, need:")
print("  max(0.5 - p_1/6, (5/6)p_1) ≤ p_i")
print()

print("When is 0.5 - p_1/6 > (5/6)p_1?")
print("  0.5 - p_1/6 > (5/6)p_1")
print("  0.5 > (5/6)p_1 + p_1/6")
print("  0.5 > p_1")
print()

print("So for p_1 < 0.5:")
print("  0.5 - p_1/6 > (5/6)p_1")
print()

print("Therefore, the BINDING constraint is:")
print("  p_i ≥ 0.5 - p_1/6")
print()

print("But we derived p_i > (5/6)p_1 from p_i ≥ 0.5 - p_1/6!")
print()

print("Let me retrace:")
print()

print("From p_2 ≥ 0.5 - p_1/6 and p_2 < p_1 (non-uniform):")
print("  0.5 - p_1/6 < p_1")
print("  0.5 < p_1 + p_1/6")
print("  0.5 < (7/6)p_1")
print("  p_1 > 3/7")
print()

print("From p_1 > p_2 and p_2 ≥ 0.5 - p_1/6:")
print("  We get p_2 ∈ (0.5 - p_1/6, p_1)")
print()

print("For p_1 slightly above 3/7:")
print("  0.5 - p_1/6 ≈ 0.5 - 0.43/6 ≈ 0.428")
print("  So p_2 ∈ (0.428, 0.43)")
print()

print("This is IMPOSSIBLE! 0.428 > 0.43 is false...")
print()

print("Wait, I made an error. Let me recalculate:")
print()

print("For p_1 = 3/7 ≈ 0.4286:")
print("  0.5 - p_1/6 = 0.5 - 0.4286/6 = 0.5 - 0.0714 = 0.4286")
print()

print("So at p_1 = 3/7:")
print("  p_2 ≥ 0.4286 = p_1")
print()

print("For non-uniform: p_2 < p_1")
print()

print("So p_2 < 0.4286")
print("But p_2 ≥ 0.4286")
print()

print("🎉🎉🎉 CONTRADICTION!!! 🎉🎉🎉")
print()

print("This means: Cannot have non-uniform family with p_1 = 3/7!")
print()

print("For p_1 > 3/7:")
print("  0.5 - p_1/6 > 3/7")
print("  NO! Let's check:")
print("  0.5 - (3/7)/6 = 0.5 - 1/14 = 7/14 - 1/14 = 6/14 = 3/7")
print()

print("So 0.5 - p_1/6 is EXACTLY 3/7 when p_1 = 3/7")
print()

print("For p_1 slightly larger than 3/7:")
print("  0.5 - p_1/6 < p_1 (since (7/6)p_1 > 0.5)")
print()

print("  So we need: 0.5 - p_1/6 < p_2 < p_1")
print()

print("Gap size: p_1 - (0.5 - p_1/6) = p_1 + p_1/6 - 0.5")
print("                               = (7/6)p_1 - 0.5")
print()

print("For p_1 = 0.44:")
print("  Gap = (7/6)·0.44 - 0.5 = 0.513 - 0.5 = 0.013")
print("  So p_2 ∈ (0.427, 0.44)")
print("  This is POSSIBLE! ✓")
print()

print("Hmm, so there's a small region where non-uniform is possible...")
print()

print("Let me reconsider what p_i > (5/6)p_1 actually means...")
print()

# ==============================================================================
# PART 6: RECONSIDERING THE (5/6) BOUND
# ==============================================================================

print("="*80)
print("PART 6: 🤔 RECONSIDERING THE (5/6) BOUND")
print("="*80)
print()

print("I derived: For p_1 < 0.5, need p_2/p_1 > 5/6")
print()

print("Let me verify this:")
print()

print("From: p_1 ≥ 0.5/(r + 1/6) where r = p_2/p_1")
print()

print("For p_1 < 0.5:")
print("  0.5 > 0.5/(r + 1/6)")
print("  r + 1/6 > 1")
print("  r > 5/6")
print()

print("This is correct! ✓")
print()

print("But then I said ALL p_i > (5/6)p_1")
print("Let me verify this for p_3...")
print()

print("For p_3:")
print("  r_3 = p_3/p_1")
print("  p_3 ≥ 0.5(1-p_1) + n_13/m ≥ 0.5 - p_1/6")
print("  r_3 ≥ (0.5 - p_1/6)/p_1 = 0.5/p_1 - 1/6")
print()

print("Since p_1 < 0.5:")
print("  0.5/p_1 > 1")
print()

print("For p_1 = 0.45:")
print("  r_3 ≥ 0.5/0.45 - 1/6 = 1.111 - 0.167 = 0.944")
print()

print("For p_1 = 0.49:")
print("  r_3 ≥ 0.5/0.49 - 1/6 = 1.020 - 0.167 = 0.853")
print()

print("So p_3/p_1 ≥ 0.853 for p_1 = 0.49")
print()

print("This is STRONGER than 5/6 ≈ 0.833! ✓")
print()

print("As p_1 decreases toward 3/7, the bound gets even STRONGER!")
print()

print("For p_1 = 3/7 ≈ 0.4286:")
print("  r_3 ≥ 0.5/0.4286 - 1/6 = 1.167 - 0.167 = 1.000")
print()

print("At p_1 = 3/7: ALL p_i ≥ p_1! (UNIFORM!)")
print()

print("🎉🎉🎉 BREAKTHROUGH!!! 🎉🎉🎉")
print("="*60)
print()

print("For non-uniform family with p_1 = 3/7:")
print("  ALL elements satisfy p_i ≥ p_1")
print("  But p_1 is MAX, so all p_i = p_1")
print("  This means UNIFORM!")
print()

print("CONTRADICTION with non-uniform assumption!")
print()

print("Therefore: Non-uniform families must have p_1 > 3/7")
print()

print("And as p_1 increases from 3/7, eventually must reach 1/2!")
print()

print("FINAL QUESTION: Can non-uniform family exist with p_1 ∈ (3/7, 1/2)?")
print()

print("="*80)
print("🎯 LET ME VERIFY THIS RIGOROUSLY")
print("="*80)
print()
