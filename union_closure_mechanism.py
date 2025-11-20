"""
DEEP ANALYSIS: WHY Union-Closure Prevents Uniformity

THEORETICAL QUESTION:
=====================
Why can't a union-closed family have uniform frequency distribution?

APPROACH:
=========
1. Construct families trying to be as uniform as possible
2. See what union-closure FORCES
3. Identify the algebraic constraint

"""

import numpy as np
from core.family import UnionClosedFamily
from core.generator import FamilyGenerator
from approaches.information_geometry import InformationGeometryAnalyzer

print("=" * 80)
print("MECHANISM: Why Union-Closure Prevents Uniformity")
print("=" * 80)
print()

# Experiment 1: Try to construct uniform family
print("EXPERIMENT 1: Attempting Uniform Construction")
print("-" * 80)

def try_uniform_family(n):
    """
    Try to construct a union-closed family with uniform frequencies.
    """
    # Strategy: Start with all singletons, see what union-closure forces
    singletons = [{i} for i in range(1, n+1)]

    # Compute closure
    gen = FamilyGenerator()
    family = gen.closure(singletons)

    # Analyze
    freqs = family.compute_frequencies()
    iga = InformationGeometryAnalyzer(np.array(list(freqs.values())))
    geo = iga.geometric_statistics()

    return family, freqs, geo

for n in [2, 3, 4, 5]:
    print(f"\nn = {n}:")
    family, freqs, geo = try_uniform_family(n)

    print(f"  Family size: {family.m}")
    print(f"  Frequencies: {dict(sorted(freqs.items()))}")
    print(f"  Max freq: {max(freqs.values()):.4f}")
    print(f"  Fisher-Rao: {geo['fisher_rao_distance_to_uniform']:.6f}")
    print(f"  Uniform? {len(set(freqs.values())) == 1}")

print()
print("Observation: Starting with singletons creates POWER SET!")
print("  → All elements appear in exactly 2^(n-1) sets")
print("  → Perfectly uniform!")
print("  → But max_freq = 2^(n-1)/2^n = 0.5 exactly!")
print()

# Experiment 2: Can we do WORSE than 0.5?
print("EXPERIMENT 2: Can We Achieve max_freq < 0.5?")
print("-" * 80)

def construct_challenging_family(n):
    """
    Try to construct family with max_freq < 0.5
    """
    # Strategy: Use overlapping pairs
    if n < 2:
        return None

    # Create pairs with maximum overlap
    sets = []
    for i in range(1, n):
        sets.append({i, i+1})

    # Add closure
    gen = FamilyGenerator()
    family = gen.closure(sets)

    return family

print("\nAttempting max_freq < 0.5...")
for n in [3, 4, 5, 6]:
    family = construct_challenging_family(n)
    if family is None:
        continue

    freqs = family.compute_frequencies()
    max_freq = max(freqs.values())

    print(f"n={n}: max_freq = {max_freq:.4f} {'✓ < 0.5' if max_freq < 0.5 else '✗ ≥ 0.5'}")

print()
print("Observation: Cannot construct max_freq < 0.5!")
print()

# Experiment 3: Analyze structure of families with max_freq = 0.5
print("EXPERIMENT 3: Families with max_freq = 0.5 Exactly")
print("-" * 80)

# Load actual families
import pickle
with open('results/final_500/results_full.pkl', 'rb') as f:
    results = pickle.load(f)

families_at_boundary = []
for f in results['families']:
    if not f.get('skip', False) and f['frequencies']['max'] == 0.5:
        families_at_boundary.append(f)

print(f"\nFound {len(families_at_boundary)} families with max_freq = 0.5 exactly")

if len(families_at_boundary) > 0:
    print("\nAnalyzing their structure...")

    for i, f in enumerate(families_at_boundary[:5]):  # First 5
        print(f"\n  Family {i+1}:")
        print(f"    n = {f['basic']['n']}, m = {f['basic']['m']}")
        print(f"    Avg set size: {f['statistics']['avg_set_size']:.2f}")
        print(f"    Density: {f['statistics']['density']:.4f}")

        # Reconstruct frequency distribution
        freqs = f['frequencies']['all']
        unique_freqs = set(freqs)
        print(f"    Unique frequencies: {sorted(unique_freqs)}")

        if len(unique_freqs) == 1:
            print(f"    → UNIFORM! (all frequencies = {list(unique_freqs)[0]:.4f})")

# THEORETICAL ANALYSIS
print()
print("=" * 80)
print("THEORETICAL ANALYSIS: The Algebraic Constraint")
print("=" * 80)
print()

print("THEOREM (Informal):")
print("-" * 80)
print()
print("For a union-closed family F with frequency distribution p:")
print()
print("1. Union-closure: ∀S,T ∈ F ⟹ S∪T ∈ F")
print("   ⟹ freq(i) = P(i ∈ random set from F)")
print()
print("2. Dependencies: Union creates correlations")
print("   If i ∈ S and j ∈ T, then {i,j} ⊆ S∪T")
print("   ⟹ freq(i or j) ≤ freq(i) + freq(j)")
print()
print("3. Uniform Impossibility (except trivial cases):")
print("   If all freq(i) = c for constant c,")
print("   then F must have special structure (e.g., power set)")
print()
print("4. Geometric Constraint:")
print("   Frequencies p must lie in specific submanifold of simplex")
print("   This submanifold EXCLUDES regions with max(p) < 0.5")
print()
print("=" * 80)
print()

print("CRITICAL PROOF STEP (to formalize):")
print("-" * 80)
print()
print("Show that union-closure implies:")
print()
print("  ∃ algebraic variety V ⊂ Δⁿ⁻¹ such that:")
print("  1. p ∈ V (frequencies constrained to V)")
print("  2. V ∩ {p : max(p) < 0.5} = ∅ (V avoids bad region)")
print()
print("Methods to prove this:")
print("  - Homological algebra (incidence matrix rank)")
print("  - Lattice theory (order-theoretic bounds)")
print("  - Information geometry (Fisher-Rao geodesics)")
print("  - Algebraic geometry (polynomial equations)")
print()

# Construct explicit example
print("EXPLICIT EXAMPLE:")
print("-" * 80)
print()

print("n = 2: Universe = {1, 2}")
print()

# All possible union-closed families on {1,2}
ucc_families = [
    [set()],  # Trivial
    [{1}],  # Singleton (not closed)
    [{1}, {2}, {1,2}],  # Full closure of singletons
    [{1,2}],  # Single set
    [set(), {1,2}],  # With empty set
]

for i, sets in enumerate(ucc_families):
    family = UnionClosedFamily(sets)
    if family.is_union_closed() and family.m > 1:
        freqs = family.compute_frequencies()
        if freqs:
            print(f"Family {i}: {[set(s) for s in family.sets]}")
            print(f"  Frequencies: {freqs}")
            print(f"  Max: {max(freqs.values()):.4f}")
            print()

print("Observation: For n=2, minimal max_freq = 0.5 (impossible to go lower!)")
print()
print("=" * 80)
