"""
CRITICAL ANALYSIS: What are we MISSING?

Current Status:
- Fisher-Rao correlation: 0.394 (good but not amazing)
- Linear fit: R² = 0.15 (explains only 15%!)
- T-test significant but effect size moderate

CRITICAL QUESTIONS:
===================

Q1: Is the relationship LINEAR?
   - Maybe it's exponential, logarithmic, or power law?
   - R² = 0.15 suggests linear is NOT the best fit!

Q2: Are there SUBGROUPS?
   - Maybe different families behave differently
   - Sparse vs dense families?
   - Small vs large n?

Q3: What about the 94 CHALLENGING cases?
   - Do they have special geometric structure?
   - Are they on the boundary of the manifold?
   - Do they cluster geometrically?

Q4: Is Fisher-Rao the BEST metric?
   - What about other divergences? (Hellinger, JS, etc.)
   - What about α-connections with different α?
   - Information radius? Jeffreys divergence?

Q5: What's the CAUSAL mechanism?
   - Union-closure → Geometric constraint → How exactly?
   - Can we identify specific forbidden regions?
   - Homological algebra constraints?

Q6: Curvature - WHICH curvature?
   - Scalar (R² low)
   - Sectional (R² very low)
   - Ricci? Gauss? What about dual curvature (α-connections)?

Q7: Are we looking at the RIGHT distribution?
   - Frequency distribution: correct
   - But what about SET size distribution?
   - What about incidence matrix spectrum?

ACTION ITEMS:
=============
1. Test NON-LINEAR models for Fisher-Rao
2. Cluster analysis of challenging cases
3. Test ALL divergences (not just Fisher-Rao)
4. Analyze α-connections with varying α
5. Geometric characterization of challenging cases
6. Boundary analysis of the manifold
7. Information-theoretic decomposition
"""

# Test 1: NON-LINEAR MODELS
print("=" * 80)
print("DEEP ANALYSIS 1: NON-LINEAR MODELS")
print("=" * 80)
print()

import numpy as np
import pickle
from approaches.information_geometry import InformationGeometryAnalyzer
from scipy.optimize import curve_fit
from scipy import stats

# Load data
with open('results/final_500/results_full.pkl', 'rb') as f:
    results = pickle.load(f)

families = [f for f in results['families'] if not f.get('skip', False) and 'error' not in f]

# Extract data
fisher_rao_dists = []
max_freqs = []

for family in families:
    freqs = np.array(family['frequencies']['all'])
    if len(freqs) == 0:
        continue
    freqs = freqs / np.sum(freqs)

    iga = InformationGeometryAnalyzer(freqs)
    geo = iga.geometric_statistics()

    fisher_rao_dists.append(geo['fisher_rao_distance_to_uniform'])
    max_freqs.append(family['frequencies']['max'])

x = np.array(fisher_rao_dists)
y = np.array(max_freqs)

# Test multiple models
models = {
    'Linear': lambda x, a, b: a * x + b,
    'Exponential': lambda x, a, b, c: a * np.exp(b * x) + c,
    'Logarithmic': lambda x, a, b: a * np.log(x + 0.01) + b,
    'Power': lambda x, a, b, c: a * x**b + c,
    'Sigmoid': lambda x, a, b, c, d: a / (1 + np.exp(-b * (x - c))) + d,
    'Square Root': lambda x, a, b: a * np.sqrt(x) + b
}

print("TESTING NON-LINEAR MODELS:")
print("-" * 80)

best_r2 = -1
best_model = None

for name, func in models.items():
    try:
        # Fit
        if name in ['Exponential', 'Power', 'Sigmoid']:
            p0 = [0.5, 1.0, 0.5] if name != 'Sigmoid' else [0.5, 1.0, 0.2, 0.5]
        else:
            p0 = [0.5, 0.5]

        params, _ = curve_fit(func, x, y, p0=p0, maxfev=10000)

        # Predict and compute R²
        y_pred = func(x, *params)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - ss_res / ss_tot

        # AIC (lower is better)
        n = len(x)
        k = len(params)
        rss = ss_res
        aic = n * np.log(rss / n) + 2 * k

        print(f"  {name:15s}: R² = {r2:.4f}, AIC = {aic:.2f}")

        if r2 > best_r2:
            best_r2 = r2
            best_model = (name, func, params)

    except Exception as e:
        print(f"  {name:15s}: Failed to fit")

print()
print(f"✅ BEST MODEL: {best_model[0]} with R² = {best_r2:.4f}")
print(f"   Parameters: {best_model[2]}")

# Save for later use
best_fit_func = best_model[1]
best_params = best_model[2]
