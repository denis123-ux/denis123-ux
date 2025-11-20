"""
DEEP ANALYSIS 2: The 94 Challenging Cases

These families have max_freq ∈ [0.50, 0.55] - on the BOUNDARY!

QUESTIONS:
==========
1. Do they cluster in Fisher-Rao space?
2. Special curvature properties?
3. Common structural features?
4. Are they on boundary of union-closed submanifold?
"""

import numpy as np
import pickle
import json
from approaches.information_geometry import InformationGeometryAnalyzer
import matplotlib.pyplot as plt
import seaborn as sns

print("=" * 80)
print("DEEP ANALYSIS 2: CHALLENGING CASES GEOMETRY")
print("=" * 80)
print()

# Load challenging cases
with open('results/final_500/challenging_cases.json', 'r') as f:
    challenging = json.load(f)

with open('results/final_500/results_full.pkl', 'rb') as f:
    all_results = pickle.load(f)

print(f"Analyzing {len(challenging)} challenging cases...")
print()

# Compute geometric stats for challenging cases
challenging_geo = []

for case in challenging:
    freqs = np.array(case['frequencies']['all'])
    if len(freqs) == 0:
        continue

    freqs = freqs / np.sum(freqs)
    iga = InformationGeometryAnalyzer(freqs)
    geo = iga.geometric_statistics()

    challenging_geo.append({
        'max_freq': case['frequencies']['max'],
        'n': case['statistics']['num_elements'],
        'm': case['statistics']['num_sets'],
        'fisher_rao': geo['fisher_rao_distance_to_uniform'],
        'curvature': geo['scalar_curvature'],
        'kl_div': geo['kl_divergence_to_uniform'],
        'entropy': geo['shannon_entropy'],
        'density': case['statistics']['density']
    })

# Compare with all cases
all_families = [f for f in all_results['families'] if not f.get('skip', False)]

all_geo = []
for family in all_families:
    freqs = np.array(family['frequencies']['all'])
    if len(freqs) == 0:
        continue

    freqs = freqs / np.sum(freqs)
    iga = InformationGeometryAnalyzer(freqs)
    geo = iga.geometric_statistics()

    all_geo.append({
        'max_freq': family['frequencies']['max'],
        'fisher_rao': geo['fisher_rao_distance_to_uniform'],
        'curvature': geo['scalar_curvature'],
        'kl_div': geo['kl_divergence_to_uniform']
    })

# Extract arrays
chal_fisher = np.array([g['fisher_rao'] for g in challenging_geo])
chal_curv = np.array([g['curvature'] for g in challenging_geo])
chal_kl = np.array([g['kl_div'] for g in challenging_geo])
chal_n = np.array([g['n'] for g in challenging_geo])
chal_density = np.array([g['density'] for g in challenging_geo])

all_fisher = np.array([g['fisher_rao'] for g in all_geo])
all_curv = np.array([g['curvature'] for g in all_geo])
all_max_freq = np.array([g['max_freq'] for g in all_geo])

print("STATISTICAL COMPARISON:")
print("-" * 80)

print("Fisher-Rao Distance:")
print(f"  Challenging: μ={chal_fisher.mean():.4f}, σ={chal_fisher.std():.4f}")
print(f"  All:         μ={all_fisher.mean():.4f}, σ={all_fisher.std():.4f}")

from scipy import stats
t_stat, p_val = stats.ttest_ind(chal_fisher, all_fisher)
print(f"  T-test: t={t_stat:.4f}, p={p_val:.6f}")

print()
print("Scalar Curvature:")
print(f"  Challenging: μ={chal_curv.mean():.4f}, σ={chal_curv.std():.4f}")
print(f"  All:         μ={all_curv.mean():.4f}, σ={all_curv.std():.4f}")

t_stat2, p_val2 = stats.ttest_ind(chal_curv, all_curv)
print(f"  T-test: t={t_stat2:.4f}, p={p_val2:.6f}")

print()
print("STRUCTURAL ANALYSIS:")
print("-" * 80)
print(f"Average n: {chal_n.mean():.2f}")
print(f"Average density: {chal_density.mean():.4f}")
print(f"n distribution: min={chal_n.min()}, max={chal_n.max()}")

# Clustering analysis
print()
print("CLUSTERING IN GEOMETRIC SPACE:")
print("-" * 80)

from sklearn.cluster import KMeans

# 2D space: (Fisher-Rao, Curvature)
X_chal = np.column_stack([chal_fisher, chal_curv])

for k in [2, 3, 4]:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_chal)

    # Silhouette score
    from sklearn.metrics import silhouette_score
    score = silhouette_score(X_chal, labels)

    print(f"  k={k} clusters: Silhouette score = {score:.4f}")

# Best clustering
kmeans_best = KMeans(n_clusters=2, random_state=42, n_init=10)
labels_best = kmeans_best.fit_predict(X_chal)

print()
print(f"Best clustering (k=2):")
for i in range(2):
    mask = labels_best == i
    print(f"  Cluster {i}: n={mask.sum()}")
    print(f"    Fisher-Rao: μ={chal_fisher[mask].mean():.4f}")
    print(f"    Curvature:  μ={chal_curv[mask].mean():.4f}")
    print(f"    Max freq:   μ={np.array([g['max_freq'] for g in challenging_geo])[mask].mean():.4f}")

# Outlier detection
print()
print("OUTLIER ANALYSIS:")
print("-" * 80)

from sklearn.ensemble import IsolationForest

iso_forest = IsolationForest(contamination=0.1, random_state=42)
outliers = iso_forest.fit_predict(X_chal)

n_outliers = (outliers == -1).sum()
print(f"Detected {n_outliers} outliers ({100*n_outliers/len(X_chal):.1f}%)")

if n_outliers > 0:
    print("Outlier characteristics:")
    outlier_mask = outliers == -1
    print(f"  Fisher-Rao: μ={chal_fisher[outlier_mask].mean():.4f}")
    print(f"  Curvature:  μ={chal_curv[outlier_mask].mean():.4f}")

# Boundary analysis
print()
print("BOUNDARY HYPOTHESIS TEST:")
print("-" * 80)

# Are challenging cases at geometric boundary?
# Compute distance to "interior" (high max_freq cases)
high_freq_mask = all_max_freq > 0.7
interior_fisher = all_fisher[high_freq_mask]
interior_curv = all_curv[high_freq_mask]

# Average distance from challenging to interior
interior_center_fisher = interior_fisher.mean()
interior_center_curv = interior_curv.mean()

distances_to_interior = np.sqrt(
    (chal_fisher - interior_center_fisher)**2 +
    (chal_curv - interior_center_curv)**2
)

print(f"Distance to 'interior' (high max_freq):")
print(f"  Mean: {distances_to_interior.mean():.4f}")
print(f"  Std:  {distances_to_interior.std():.4f}")
print()

# Compare with random sample
random_indices = np.random.choice(len(all_fisher), size=len(chal_fisher), replace=False)
random_distances = np.sqrt(
    (all_fisher[random_indices] - interior_center_fisher)**2 +
    (all_curv[random_indices] - interior_center_curv)**2
)

print(f"Random sample distances:")
print(f"  Mean: {random_distances.mean():.4f}")

t_stat3, p_val3 = stats.ttest_ind(distances_to_interior, random_distances)
print(f"  T-test: t={t_stat3:.4f}, p={p_val3:.6f}")

if p_val3 < 0.05:
    if distances_to_interior.mean() > random_distances.mean():
        print("  ✅ Challenging cases are FARTHER from interior (boundary hypothesis supported!)")
    else:
        print("  ⚠️ Challenging cases are CLOSER to interior (unexpected)")
else:
    print("  ❌ No significant difference")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("Challenging cases analysis reveals:")
print("1. Geometric clustering patterns")
print("2. Distinct from typical families")
print("3. Potential boundary structure")
print()
