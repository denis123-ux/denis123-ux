#!/usr/bin/env python3
"""
Analyze partial torsion results from advanced test.

From the log, we have:
- 15 SAT formulas
- 8 UNSAT formulas (complete before timeout)
"""

import numpy as np
from scipy.stats import ttest_ind

# Manually extracted from log
sat_torsion = [
    False,  # uf50-01
    True,   # uf50-010 [2,2]
    True,   # uf50-0100 [2,2,2,2]
    True,   # uf50-01000 [2,2]
    True,   # uf50-0101 [2,2]
    False,  # uf50-0102
    True,   # uf50-0103 [2,2,2,2,2,2]
    False,  # uf50-0104
    True,   # uf50-0105 [2,2]
    True,   # uf50-0106 [2,2]
    True,   # uf50-0107 [2,2,2,2,2,2]
    False,  # uf50-0108
    True,   # uf50-0109 [2,2]
    True,   # uf50-011 [2,2,2,2,2,2,2,2]
    True,   # uf50-0110 [2,2,2,2]
]

unsat_torsion = [
    True,   # uuf50-01 [2,2]
    True,   # uuf50-010 [2,2,2,2]
    True,   # uuf50-0100 [2,2,2,2,2,2]
    True,   # uuf50-01000 [2,2]
    True,   # uuf50-0101 [2,2,2,2]
    True,   # uuf50-0102 [2,2,2,2,2]
    True,   # uuf50-0103 [2,2]
    True,   # uuf50-0104 [2,2]
]

sat_num_torsion = [
    0,  # uf50-01
    2,  # uf50-010
    4,  # uf50-0100
    2,  # uf50-01000
    2,  # uf50-0101
    0,  # uf50-0102
    6,  # uf50-0103
    0,  # uf50-0104
    2,  # uf50-0105
    2,  # uf50-0106
    6,  # uf50-0107
    0,  # uf50-0108
    2,  # uf50-0109
    8,  # uf50-011
    4,  # uf50-0110
]

unsat_num_torsion = [
    2,  # uuf50-01
    4,  # uuf50-010
    6,  # uuf50-0100
    2,  # uuf50-01000
    4,  # uuf50-0101
    5,  # uuf50-0102
    2,  # uuf50-0103
    2,  # uuf50-0104
]

print("="*80)
print("🔬 PARTIAL TORSION ANALYSIS")
print("="*80)
print()

# Binary analysis
sat_has_torsion = sum(sat_torsion)
unsat_has_torsion = sum(unsat_torsion)

print("HAS 2-TORSION (binary):")
print(f"  SAT: {sat_has_torsion}/{len(sat_torsion)} ({100*sat_has_torsion/len(sat_torsion):.1f}%)")
print(f"  UNSAT: {unsat_has_torsion}/{len(unsat_torsion)} ({100*unsat_has_torsion/len(unsat_torsion):.1f}%)")
print()

# Count analysis
sat_counts = np.array(sat_num_torsion)
unsat_counts = np.array(unsat_num_torsion)

print("NUMBER OF 2-TORSION ELEMENTS:")
print(f"  SAT: {np.mean(sat_counts):.2f} ± {np.std(sat_counts):.2f}")
print(f"  UNSAT: {np.mean(unsat_counts):.2f} ± {np.std(unsat_counts):.2f}")
print()

# Cohen's d
def cohens_d(x, y):
    nx, ny = len(x), len(y)
    dof = nx + ny - 2
    pooled_std = np.sqrt(((nx-1)*np.std(x, ddof=1)**2 + (ny-1)*np.std(y, ddof=1)**2) / dof)
    return (np.mean(x) - np.mean(y)) / pooled_std

d = cohens_d(sat_counts, unsat_counts)
t_stat, p_value = ttest_ind(sat_counts, unsat_counts)

print(f"Cohen's d: {d:.4f}")
print(f"t-test: t={t_stat:.3f}, p={p_value:.4f}")
print()

if abs(d) > 1.25:
    print("🏆 BREAKTHROUGH! d > 1.25")
elif abs(d) > 0.8:
    print("⚡ LARGE EFFECT! d > 0.8")
elif abs(d) > 0.5:
    print("📊 MEDIUM EFFECT")
else:
    print("❌ WEAK EFFECT")

print()
print("="*80)
print("🎯 INTERPRETATION")
print("="*80)
print()

if unsat_has_torsion == len(unsat_torsion):
    print("✅ ALL UNSAT instances have 2-torsion (100%)")
else:
    print(f"⚠️  Most UNSAT instances have 2-torsion ({100*unsat_has_torsion/len(unsat_torsion):.1f}%)")

if sat_has_torsion < len(sat_torsion):
    print(f"✅ SAT instances: {100*sat_has_torsion/len(sat_torsion):.1f}% have 2-torsion")
else:
    print("⚠️  ALL SAT instances also have 2-torsion")

print()
print("KEY FINDING:")
if d > 0:
    print(f"  UNSAT has MORE 2-torsion elements than SAT (d={d:.4f})")
    print(f"  Difference: {np.mean(unsat_counts) - np.mean(sat_counts):.2f} elements")
else:
    print(f"  SAT has MORE 2-torsion elements than UNSAT (d={d:.4f})")

print()
print("NEXT STEPS:")
print("1. Run on LARGER dataset (100+ formulas) with optimized SNF")
print("2. Check if torsion count correlates with problem difficulty")
print("3. Test if 2-torsion is NECESSARY for UNSAT (universal property)")
print()
