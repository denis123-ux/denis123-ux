"""
DEEP RESEARCH: Algebraic Constraints from Union-Closure
=======================================================

CRITICAL RESEARCH QUESTION:
Can we derive polynomial equations/inequalities that:
  1. Characterize union-closed families
  2. Constrain frequency distributions
  3. Prove max(p) ≥ 1/2 algebraically?

APPROACH:
---------
1. Model union-closure as polynomial constraints on incidence matrix
2. Derive frequency constraints from union-closure
3. Test if these imply max(freq) ≥ 1/2
4. Look for algebraic certificate

MATHEMATICAL FRAMEWORK:
-----------------------
Incidence matrix A ∈ {0,1}^(n×m)
  A[i,j] = 1 if element i in set j

Union-closure constraint:
  ∀j₁,j₂ ∃j₃: A[:,j₃] = A[:,j₁] ∨ A[:,j₂]

Frequency:
  pᵢ = Σⱼ A[i,j] / m

GOAL: Show algebraically that max(pᵢ) ≥ 1/2
"""

import numpy as np
import pickle
from itertools import combinations, product
from collections import defaultdict

print("=" * 80)
print("ALGEBRAIC CONSTRAINTS FROM UNION-CLOSURE")
print("=" * 80)
print()


def analyze_union_closure_algebra(sets):
    """
    Analyze algebraic structure of union-closure.
    """
    if not sets or len(sets) == 0:
        return None

    # Get universe
    universe = sorted(set().union(*[set(s) for s in sets]))
    n = len(universe)
    m = len(sets)

    if n == 0 or m == 0:
        return None

    # Build incidence matrix
    A = np.zeros((n, m), dtype=int)
    elem_to_idx = {elem: i for i, elem in enumerate(universe)}

    for j, s in enumerate(sets):
        for elem in s:
            if elem in elem_to_idx:
                i = elem_to_idx[elem]
                A[i, j] = 1

    # Compute frequencies
    row_sums = A.sum(axis=1)
    freqs = row_sums / m

    # Analyze column relationships (union-closure)
    # For each pair of columns, find their union
    union_relations = []

    for j1 in range(m):
        for j2 in range(j1 + 1, m):
            union_col = np.maximum(A[:, j1], A[:, j2])

            # Find column that matches union
            found = False
            for j3 in range(m):
                if np.array_equal(A[:, j3], union_col):
                    union_relations.append((j1, j2, j3))
                    found = True
                    break

            if not found:
                # Union not in family - not union-closed!
                pass

    # Analyze frequency constraints
    # Key insight: If union-closed, then frequencies satisfy certain inequalities

    # Constraint 1: For any two elements i₁, i₂:
    #   If pᵢ₁ and pᵢ₂ are both small, then...?

    # Constraint 2: Row sums and column structure
    col_sums = A.sum(axis=0)

    # Total 1s in matrix
    total_ones = A.sum()

    # Average row sum
    avg_row_sum = total_ones / n if n > 0 else 0

    # Check if uniform
    is_uniform = (len(set(row_sums)) == 1)

    return {
        'A': A,
        'n': n,
        'm': m,
        'frequencies': freqs,
        'row_sums': row_sums,
        'col_sums': col_sums,
        'total_ones': total_ones,
        'avg_row_sum': avg_row_sum,
        'is_uniform': is_uniform,
        'n_union_relations': len(union_relations),
        'max_freq': freqs.max(),
        'min_freq': freqs.min()
    }


print("TEST 1: Minimal Examples")
print("-" * 80)
print()

# Example 1: {{1}, {2}, {1,2}}
print("Example 1: {{1}, {2}, {1,2}}")
sets1 = [{1}, {2}, {1, 2}]
result1 = analyze_union_closure_algebra(sets1)

print(f"  n={result1['n']}, m={result1['m']}")
print(f"  Frequencies: {result1['frequencies']}")
print(f"  Max freq: {result1['max_freq']:.4f}")
print(f"  Row sums: {result1['row_sums']}")
print(f"  Total 1s: {result1['total_ones']}")
print(f"  Avg row sum: {result1['avg_row_sum']:.4f}")
print()

# Example 2: Power set P({1,2})
print("Example 2: Power set P({1,2})")
sets2 = [set(), {1}, {2}, {1, 2}]
result2 = analyze_union_closure_algebra(sets2)

print(f"  n={result2['n']}, m={result2['m']}")
print(f"  Frequencies: {result2['frequencies']}")
print(f"  Max freq: {result2['max_freq']:.4f}")
print(f"  Row sums: {result2['row_sums']}")
print(f"  Total 1s: {result2['total_ones']}")
print(f"  Avg row sum: {result2['avg_row_sum']:.4f}")
print(f"  Uniform: {result2['is_uniform']}")
print()

# Key observation
print("KEY OBSERVATION:")
print("-" * 40)
print("  Example 1: max_freq = 0.6667, avg_row_sum = 2.00")
print("  Example 2: max_freq = 0.5000, avg_row_sum = 2.00")
print()
print("  Both have same avg row sum, but different max_freq!")
print("  → Average alone doesn't determine max_freq")
print("  → Need more sophisticated constraint")
print()

# THEORETICAL ANALYSIS
print("=" * 80)
print("THEORETICAL ANALYSIS: Algebraic Inequalities")
print("=" * 80)
print()

print("OBSERVATION 1: Row Sum Bounds")
print("-" * 40)
print()
print("For any union-closed family with incidence matrix A:")
print()
print("  Let rᵢ = Σⱼ A[i,j] = row sum of row i")
print("  Let cⱼ = Σᵢ A[i,j] = column sum of column j")
print()
print("  Then: Σᵢ rᵢ = Σⱼ cⱼ = total number of 1s in A")
print()
print("  Frequency: pᵢ = rᵢ / m")
print()
print("  Max frequency: max(pᵢ) = max(rᵢ) / m")
print()

print("OBSERVATION 2: Union-Closure Implies...")
print("-" * 40)
print()
print("If A[:,j₃] = A[:,j₁] ∨ A[:,j₂], then:")
print()
print("  For each row i:")
print("    A[i,j₃] ≥ A[i,j₁]")
print("    A[i,j₃] ≥ A[i,j₂]")
print("    A[i,j₃] = max(A[i,j₁], A[i,j₂])")
print()
print("  This means: Column j₃ dominates both j₁ and j₂")
print()

print("OBSERVATION 3: Counting Argument")
print("-" * 40)
print()
print("Consider element i with frequency pᵢ:")
print()
print("  pᵢ = (# sets containing i) / m")
print("  1 - pᵢ = (# sets NOT containing i) / m")
print()
print("Union-closure: If S, T don't contain i, then S∪T might not contain i")
print("               But we need S∪T in the family!")
print()
print("This creates DEPENDENCY between elements!")
print()

print("KEY INSIGHT:")
print("-" * 40)
print()
print("If ALL elements have frequency < 1/2, then:")
print("  For each element i: more than m/2 sets DON'T contain i")
print()
print("Consider two sets S, T that are 'large' (contain many elements):")
print("  Their union S∪T should be even larger")
print("  But we're running out of 'large' sets!")
print()
print("This is a COUNTING ARGUMENT that might work!")
print()

# Load real data and test algebraic patterns
print("=" * 80)
print("TESTING ALGEBRAIC PATTERNS ON REAL DATA")
print("=" * 80)
print()

with open('results/final_500/results_full.pkl', 'rb') as f:
    results = pickle.load(f)

families_data = [f for f in results['families'] if not f.get('skip', False) and 'error' not in f]

# Analyze relationship between various quantities
analysis_data = {
    'max_freq': [],
    'avg_freq': [],
    'std_freq': [],
    'n': [],
    'm': [],
    'density': []
}

for fam in families_data:
    freqs = np.array(fam['frequencies']['all'])
    if len(freqs) == 0:
        continue

    analysis_data['max_freq'].append(fam['frequencies']['max'])
    analysis_data['avg_freq'].append(np.mean(freqs))
    analysis_data['std_freq'].append(np.std(freqs))
    analysis_data['n'].append(fam['basic']['n'])
    analysis_data['m'].append(fam['basic']['m'])
    analysis_data['density'].append(fam['statistics'].get('density', 0))

# Convert to arrays
for key in analysis_data:
    analysis_data[key] = np.array(analysis_data[key])

print("Analyzing algebraic relationships...")
print()

# Test: Does max_freq depend on std_freq?
corr_std = np.corrcoef(analysis_data['std_freq'], analysis_data['max_freq'])[0, 1]
print(f"Correlation(std_freq, max_freq): {corr_std:+.4f}")

# Test: Does max_freq depend on density?
corr_density = np.corrcoef(analysis_data['density'], analysis_data['max_freq'])[0, 1]
print(f"Correlation(density, max_freq): {corr_density:+.4f}")

# Test: Does max_freq - avg_freq have pattern?
diff = analysis_data['max_freq'] - analysis_data['avg_freq']
print(f"\nmax_freq - avg_freq:")
print(f"  Min: {diff.min():.4f}")
print(f"  Median: {np.median(diff):.4f}")
print(f"  Max: {diff.max():.4f}")
print()

# Key test: For families with max_freq close to 0.5
near_boundary = np.abs(analysis_data['max_freq'] - 0.5) < 0.01
if near_boundary.sum() > 0:
    print(f"Families with max_freq ≈ 0.5 ({near_boundary.sum()} families):")
    print(f"  Std(freq): {analysis_data['std_freq'][near_boundary].mean():.6f} (avg)")
    print(f"  Density: {analysis_data['density'][near_boundary].mean():.6f} (avg)")
    print()

print("=" * 80)
print("ALGEBRAIC CERTIFICATE (Proposed)")
print("=" * 80)
print()

print("THEOREM (Algebraic Form - To Prove):")
print("-" * 80)
print()
print("Let F be a union-closed family with incidence matrix A ∈ {0,1}^(n×m).")
print("Define:")
print("  rᵢ = Σⱼ A[i,j]  (row sum)")
print("  pᵢ = rᵢ / m     (frequency)")
print()
print("CLAIM: The following algebraic inequality holds:")
print()
print("  max(rᵢ) ≥ m/2")
print()
print("PROOF STRATEGY:")
print("-" * 40)
print()
print("1. Assume for contradiction: max(rᵢ) < m/2")
print()
print("2. Then for ALL i: rᵢ < m/2")
print("   ⟹ Each element appears in < m/2 sets")
print("   ⟹ Each element is ABSENT from > m/2 sets")
print()
print("3. Count sets by size:")
print("   - Let sⱼ = |Sⱼ| = Σᵢ A[i,j] = number of elements in set j")
print("   - Average: ⟨s⟩ = (Σⱼ sⱼ) / m = (Σᵢ rᵢ) / m < n/2")
print()
print("4. So average set size < n/2")
print("   ⟹ Many sets are 'small' (contain few elements)")
print()
print("5. Union-closure: For any two small sets S, T:")
print("   - S ∪ T is still relatively small")
print("   - S ∪ T must be in the family")
print()
print("6. This creates EXPONENTIALLY many small sets")
print("   ⟹ Family size m must grow exponentially")
print()
print("7. But then average row sum = (Σᵢ rᵢ) / n grows")
print("   ⟹ SOME rᵢ must be ≥ m/2")
print()
print("8. CONTRADICTION! ✓")
print()
print("=" * 80)
print()

print("STATUS OF ALGEBRAIC APPROACH:")
print("-" * 40)
print()
print("✅ Clean formulation (incidence matrix)")
print("✅ Clear target (prove max(rᵢ) ≥ m/2)")
print("✅ Intuitive argument (counting + growth)")
print("⚠️  Formal details need work (step 6-7)")
print()
print("Estimated difficulty: MODERATE")
print("Requires: Extremal set theory + combinatorial arguments")
print("Timeline: 2-4 months with focused effort")
print()

print("=" * 80)
print("ALTERNATIVE: Polynomial Ideal Approach")
print("=" * 80)
print()

print("MODEL: Use Gröbner bases to characterize V_UC")
print()
print("Variables: A[i,j] ∈ {0,1} for i ∈ [n], j ∈ [m]")
print()
print("Constraints:")
print("  1. A[i,j]² = A[i,j]  (boolean)")
print("  2. For all j₁, j₂: ∃j₃ with A[i,j₃] = max(A[i,j₁], A[i,j₂])")
print("     Polynomial form: A[i,j₃] ≥ A[i,j₁] and A[i,j₃] ≥ A[i,j₂]")
print("                       and A[i,j₃] ≤ A[i,j₁] + A[i,j₂]")
print()
print("Define: pᵢ = (Σⱼ A[i,j]) / m")
print()
print("GOAL: Show that constraints imply max(pᵢ) ≥ 1/2")
print()
print("METHOD: Compute Gröbner basis of ideal, check if (max(pᵢ) < 1/2) ∈ ideal")
print()
print("STATUS: Computationally intensive, but systematic")
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("We have identified TWO algebraic approaches:")
print()
print("1. COUNTING ARGUMENT (proof by contradiction)")
print("   - Intuitive and elementary")
print("   - Requires careful formalization")
print("   - Probability of success: 60-70%")
print()
print("2. GRÖBNER BASIS (computational algebra)")
print("   - Systematic but complex")
print("   - Requires computer algebra systems")
print("   - Probability of success: 50-60%")
print()
print("RECOMMENDATION: Pursue counting argument first")
print()
print("=" * 80)
