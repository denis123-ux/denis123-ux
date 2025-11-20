"""
DEEP RESEARCH: α-Divergences and Information Geometry
=====================================================

RESEARCH QUESTION:
Is Fisher-Rao distance the BEST information-geometric quantity, or do
other divergences (Hellinger, Jensen-Shannon, Jeffreys, Rényi) show
even stronger correlations with max_frequency?

APPROACH:
1. Compute multiple α-divergences for all 500 families
2. Test correlations with max_frequency
3. Test non-linear models for each divergence
4. Compare predictive power (R², RMSE)
5. Identify which divergence is the BEST certificate
"""

import numpy as np
import pickle
from scipy.optimize import curve_fit
from scipy import stats as scipy_stats
from approaches.information_geometry import InformationGeometryAnalyzer

print("=" * 80)
print("DEEP RESEARCH: α-Divergences Analysis")
print("=" * 80)
print()

# Load data
with open('results/final_500/results_full.pkl', 'rb') as f:
    results = pickle.load(f)

families = [f for f in results['families'] if not f.get('skip', False) and 'error' not in f]

print(f"Analyzing {len(families)} families...")
print()

# Compute all divergences
data = {
    'max_freq': [],
    'fisher_rao': [],
    'kl_divergence': [],
    'reverse_kl': [],
    'hellinger': [],
    'jensen_shannon': [],
    'chi_squared': [],
    'bhattacharyya': [],
    'renyi_0.5': [],
    'renyi_2.0': [],
    'tsallis_0.5': [],
    'tsallis_2.0': []
}

print("Computing divergences for all families...")

for family in families:
    freqs = np.array(family['frequencies']['all'])
    if len(freqs) == 0:
        continue

    freqs = freqs / np.sum(freqs)
    n = len(freqs)
    uniform = np.ones(n) / n

    iga = InformationGeometryAnalyzer(freqs)

    # Store max frequency
    data['max_freq'].append(family['frequencies']['max'])

    # Fisher-Rao distance
    data['fisher_rao'].append(iga.fisher_rao_distance(uniform))

    # α-divergences
    data['kl_divergence'].append(iga.alpha_divergence(uniform, alpha=1.0))
    data['reverse_kl'].append(iga.alpha_divergence(uniform, alpha=-1.0))
    data['hellinger'].append(iga.alpha_divergence(uniform, alpha=0.0))

    # Jensen-Shannon (symmetrized KL)
    data['jensen_shannon'].append(iga.information_radius(uniform))

    # Bhattacharyya coefficient → distance
    bc = np.sum(np.sqrt(freqs * uniform))
    data['bhattacharyya'].append(-np.log(bc))

    # Chi-squared divergence
    chi_sq = np.sum((freqs - uniform)**2 / uniform)
    data['chi_squared'].append(chi_sq)

    # Rényi divergences (different α values)
    # D_α(p||q) = 1/(α-1) log Σ pᵢ^α qᵢ^(1-α)
    for alpha in [0.5, 2.0]:
        if alpha == 1.0:
            renyi = data['kl_divergence'][-1]
        else:
            integral = np.sum(freqs**alpha * uniform**(1-alpha))
            renyi = np.log(integral) / (alpha - 1)
        data[f'renyi_{alpha}'].append(renyi)

    # Tsallis divergences (quantum generalization)
    # S_q(p||q) = 1/(q-1) [1 - Σ pᵢ^q qᵢ^(1-q)]
    for q in [0.5, 2.0]:
        if q == 1.0:
            tsallis = data['kl_divergence'][-1]
        else:
            integral = np.sum(freqs**q * uniform**(1-q))
            tsallis = (1 - integral) / (q - 1)
        data[f'tsallis_{q}'].append(tsallis)

# Convert to arrays
for key in data:
    data[key] = np.array(data[key])

print(f"✅ Computed {len(data) - 1} divergence measures")
print()

# Test correlations
print("=" * 80)
print("CORRELATION ANALYSIS")
print("=" * 80)
print()

correlations = {}
for key in data:
    if key == 'max_freq':
        continue

    corr = np.corrcoef(data[key], data['max_freq'])[0, 1]
    correlations[key] = corr

# Sort by absolute correlation
sorted_corrs = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

print("Divergences ranked by |correlation| with max_frequency:")
print("-" * 80)
for i, (name, corr) in enumerate(sorted_corrs, 1):
    stars = "⭐" * min(3, int(abs(corr) * 10))
    print(f"{i:2d}. {name:20s}: {corr:+.4f} {stars}")

print()

# Find the BEST divergence
best_name, best_corr = sorted_corrs[0]
print(f"🏆 BEST: {best_name} with correlation {best_corr:+.4f}")
print()

# Test non-linear models for top 3 divergences
print("=" * 80)
print("NON-LINEAR MODEL COMPARISON (Top 3 Divergences)")
print("=" * 80)
print()

models = {
    'Linear': lambda x, a, b: a * x + b,
    'Sigmoid': lambda x, a, b, c, d: a / (1 + np.exp(-b * (x - c))) + d,
    'Exponential': lambda x, a, b, c: a * np.exp(b * x) + c,
    'Power': lambda x, a, b, c: a * x**b + c,
}

for name, _ in sorted_corrs[:3]:
    print(f"\n{name.upper()}:")
    print("-" * 40)

    X = data[name]
    y = data['max_freq']

    best_model = None
    best_r2 = -np.inf
    best_params = None

    for model_name, model_func in models.items():
        try:
            # Fit model
            if model_name == 'Sigmoid':
                p0 = [0.2, 40, np.median(X), 0.6]
            elif model_name == 'Exponential':
                p0 = [0.1, 1.0, 0.5]
            elif model_name == 'Power':
                p0 = [0.5, 0.5, 0.5]
            else:  # Linear
                p0 = [1.0, 0.5]

            params, _ = curve_fit(model_func, X, y, p0=p0, maxfev=10000)
            y_pred = model_func(X, *params)

            # R² score
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r2 = 1 - ss_res / ss_tot

            print(f"  {model_name:12s}: R² = {r2:.4f}")

            if r2 > best_r2:
                best_r2 = r2
                best_model = model_name
                best_params = params

        except Exception as e:
            print(f"  {model_name:12s}: Failed to fit")

    print(f"\n  → Best model: {best_model} (R² = {best_r2:.4f})")

    # For the OVERALL best divergence, extrapolate to zero
    if name == best_name:
        print(f"\n  CRITICAL TEST: Extrapolation to {name} = 0")
        if best_model == 'Sigmoid':
            pred_at_zero = models[best_model](0, *best_params)
            print(f"    Predicted max_freq at {name}=0: {pred_at_zero:.6f}")
            if pred_at_zero > 0.5:
                print(f"    ✅ SUPPORTS CONJECTURE! {pred_at_zero:.4f} > 0.5")
            else:
                print(f"    ❌ Does not support conjecture: {pred_at_zero:.4f} ≤ 0.5")

print()

# Statistical test: Do near-uniform families (low divergence) have max_freq ≥ 0.5?
print("=" * 80)
print("BOUNDARY ANALYSIS: Near-Uniform Families")
print("=" * 80)
print()

for name, _ in sorted_corrs[:3]:
    print(f"\n{name}:")
    print("-" * 40)

    X = data[name]
    y = data['max_freq']

    # Find families with divergence < 1st percentile (most uniform-like)
    threshold = np.percentile(X, 1)
    near_uniform = X < threshold

    print(f"  Near-uniform threshold: {name} < {threshold:.6f}")
    print(f"  Number of near-uniform families: {near_uniform.sum()}")

    if near_uniform.sum() > 0:
        print(f"  Max frequencies of near-uniform families:")
        print(f"    Min:    {y[near_uniform].min():.6f}")
        print(f"    Median: {np.median(y[near_uniform]):.6f}")
        print(f"    Max:    {y[near_uniform].max():.6f}")

        violations = (y[near_uniform] < 0.5).sum()
        print(f"  Violations (max_freq < 0.5): {violations}")

        if violations == 0:
            print(f"  ✅ ALL near-uniform families satisfy conjecture!")
        else:
            print(f"  ❌ Found {violations} counterexamples")

print()

# Comparative analysis
print("=" * 80)
print("COMPARATIVE SUMMARY")
print("=" * 80)
print()

print("Metric                     | Correlation | Best R²  | Status")
print("-" * 80)

# Add previous tensor network result for comparison
print(f"{'Bond Dimension (Tensor)':26s} | {-0.156:+.4f}      | {'0.024':8s} | Baseline")

for name, corr in sorted_corrs[:5]:
    # Get best R² (run quick linear fit)
    X = data[name]
    y = data['max_freq']
    z = np.polyfit(X, y, 1)
    y_pred = np.polyval(z, X)
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r2_linear = 1 - ss_res / ss_tot

    status = "⭐ BEST" if name == best_name else "Strong" if abs(corr) > 0.3 else "Moderate"
    print(f"{name:26s} | {corr:+.4f}      | {r2_linear:.4f}   | {status}")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print(f"🏆 WINNER: {best_name}")
print(f"   Correlation: {best_corr:+.4f}")
print(f"   Interpretation: {best_name} is the STRONGEST information-geometric")
print(f"   predictor of max_frequency in union-closed families!")
print()

if abs(best_corr) > abs(correlations.get('fisher_rao', 0)):
    print(f"🎯 BREAKTHROUGH: {best_name} OUTPERFORMS Fisher-Rao distance!")
    print(f"   Previous best: Fisher-Rao ({correlations['fisher_rao']:+.4f})")
    print(f"   New best:      {best_name} ({best_corr:+.4f})")
    print(f"   Improvement:   {abs(best_corr) - abs(correlations['fisher_rao']):.4f}")
else:
    print(f"Fisher-Rao distance remains the best information-geometric metric.")
    print(f"This confirms Čencov's theorem - Fisher-Rao is the UNIQUE")
    print(f"Markov-invariant metric, and thus the natural choice!")

print()
print("=" * 80)
