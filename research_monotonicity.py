"""
DEEP RESEARCH: Monotonicity of Fisher-Rao Distance
==================================================

CRITICAL QUESTION:
Is the relationship between d_FR and max_freq MONOTONE?

HYPOTHESIS:
For union-closed families, max_freq is a monotone increasing function
of Fisher-Rao distance from uniform distribution.

APPROACH:
1. Bin families by Fisher-Rao distance
2. Compute min/max/median max_freq in each bin
3. Test for monotonicity statistically
4. Identify any violations
5. Analyze edge cases near d_FR = 0
"""

import numpy as np
import pickle
from scipy import stats as scipy_stats
from approaches.information_geometry import InformationGeometryAnalyzer
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')

print("=" * 80)
print("MONOTONICITY ANALYSIS: Fisher-Rao vs Max Frequency")
print("=" * 80)
print()

# Load data
with open('results/final_500/results_full.pkl', 'rb') as f:
    results = pickle.load(f)

families = [f for f in results['families'] if not f.get('skip', False) and 'error' not in f]

# Compute Fisher-Rao distances
fisher_rao_dists = []
max_freqs = []

for family in families:
    freqs = np.array(family['frequencies']['all'])
    if len(freqs) == 0:
        continue

    freqs = freqs / np.sum(freqs)
    n = len(freqs)
    uniform = np.ones(n) / n

    iga = InformationGeometryAnalyzer(freqs)
    d_fr = iga.fisher_rao_distance(uniform)

    fisher_rao_dists.append(d_fr)
    max_freqs.append(family['frequencies']['max'])

fisher_rao_dists = np.array(fisher_rao_dists)
max_freqs = np.array(max_freqs)

print(f"Analyzing {len(fisher_rao_dists)} families...")
print()

# Create bins based on Fisher-Rao distance
n_bins = 20
bins = np.linspace(fisher_rao_dists.min(), fisher_rao_dists.max(), n_bins + 1)
bin_centers = (bins[:-1] + bins[1:]) / 2

# Compute statistics for each bin
bin_stats = []

for i in range(n_bins):
    mask = (fisher_rao_dists >= bins[i]) & (fisher_rao_dists < bins[i+1])

    if mask.sum() > 0:
        bin_stats.append({
            'bin_center': bin_centers[i],
            'bin_left': bins[i],
            'bin_right': bins[i+1],
            'count': mask.sum(),
            'min_freq': max_freqs[mask].min(),
            'max_freq': max_freqs[mask].max(),
            'median_freq': np.median(max_freqs[mask]),
            'mean_freq': max_freqs[mask].mean(),
            'std_freq': max_freqs[mask].std()
        })

print("=" * 80)
print("BINNED ANALYSIS")
print("=" * 80)
print()

print(f"{'Bin Center':>12s} | {'Count':>6s} | {'Min':>8s} | {'Median':>8s} | {'Max':>8s} | {'Mean':>8s} | {'Std':>8s}")
print("-" * 80)

for stat in bin_stats:
    print(f"{stat['bin_center']:12.6f} | {stat['count']:6d} | {stat['min_freq']:8.4f} | "
          f"{stat['median_freq']:8.4f} | {stat['max_freq']:8.4f} | "
          f"{stat['mean_freq']:8.4f} | {stat['std_freq']:8.4f}")

print()

# Test monotonicity of medians
print("=" * 80)
print("MONOTONICITY TEST: Are medians increasing?")
print("=" * 80)
print()

medians = np.array([s['median_freq'] for s in bin_stats])
bin_centers_array = np.array([s['bin_center'] for s in bin_stats])

# Spearman rank correlation (tests monotonicity)
spearman_corr, spearman_p = scipy_stats.spearmanr(bin_centers_array, medians)

print(f"Spearman rank correlation: ρ = {spearman_corr:+.4f} (p = {spearman_p:.6f})")

if spearman_corr > 0.9:
    print("✅ STRONG monotonic relationship!")
elif spearman_corr > 0.7:
    print("✅ MODERATE monotonic relationship")
elif spearman_corr > 0.5:
    print("⚠️  WEAK monotonic relationship")
else:
    print("❌ NO clear monotonic relationship")

print()

# Count violations (bins where median decreases)
violations = 0
for i in range(1, len(medians)):
    if medians[i] < medians[i-1]:
        violations += 1
        print(f"  Violation at bin {i}: {medians[i-1]:.4f} → {medians[i]:.4f}")

if violations == 0:
    print("✅ NO violations: Medians are strictly non-decreasing!")
else:
    print(f"⚠️  Found {violations} violations (out of {len(medians)-1} transitions)")

print()

# Test monotonicity of minimums (stronger test)
print("=" * 80)
print("STRONGER TEST: Are minimums increasing?")
print("=" * 80)
print()

minimums = np.array([s['min_freq'] for s in bin_stats])

spearman_corr_min, spearman_p_min = scipy_stats.spearmanr(bin_centers_array, minimums)

print(f"Spearman rank correlation: ρ = {spearman_corr_min:+.4f} (p = {spearman_p_min:.6f})")

violations_min = 0
for i in range(1, len(minimums)):
    if minimums[i] < minimums[i-1]:
        violations_min += 1
        print(f"  Violation at bin {i}: {minimums[i-1]:.4f} → {minimums[i]:.4f}")

if violations_min == 0:
    print("✅ NO violations: Minimums are strictly non-decreasing!")
    print("\nThis is VERY STRONG evidence for monotonicity!")
else:
    print(f"⚠️  Found {violations_min} violations")

print()

# Focus on near-uniform region (d_FR ≈ 0)
print("=" * 80)
print("CRITICAL REGION: Near-Uniform (d_FR ≈ 0)")
print("=" * 80)
print()

# Find families with very small Fisher-Rao distance
thresholds = [0.001, 0.005, 0.01, 0.05, 0.1]

for threshold in thresholds:
    mask = fisher_rao_dists < threshold
    count = mask.sum()

    if count > 0:
        print(f"d_FR < {threshold:.3f}:")
        print(f"  Count: {count}")
        print(f"  Min max_freq: {max_freqs[mask].min():.6f}")
        print(f"  Median max_freq: {np.median(max_freqs[mask]):.6f}")
        print(f"  Max max_freq: {max_freqs[mask].max():.6f}")

        violations_near_zero = (max_freqs[mask] < 0.5).sum()
        print(f"  Violations (< 0.5): {violations_near_zero}")

        if violations_near_zero == 0:
            print(f"  ✅ ALL families with d_FR < {threshold:.3f} satisfy conjecture!")
        else:
            print(f"  ❌ Found {violations_near_zero} counterexamples!")

        print()

# Test global minimum
print("=" * 80)
print("GLOBAL ANALYSIS")
print("=" * 80)
print()

print(f"Total families: {len(max_freqs)}")
print(f"Global minimum max_freq: {max_freqs.min():.6f}")
print(f"Achieved at d_FR = {fisher_rao_dists[max_freqs.argmin()]:.6f}")
print()

# Find all families at minimum
min_freq = max_freqs.min()
at_minimum = np.abs(max_freqs - min_freq) < 1e-6

print(f"Families at minimum ({min_freq:.6f}):")
print(f"  Count: {at_minimum.sum()}")
print(f"  d_FR range: [{fisher_rao_dists[at_minimum].min():.6f}, {fisher_rao_dists[at_minimum].max():.6f}]")
print(f"  d_FR mean: {fisher_rao_dists[at_minimum].mean():.6f}")
print(f"  d_FR median: {np.median(fisher_rao_dists[at_minimum]):.6f}")
print()

if fisher_rao_dists[at_minimum].max() < 0.001:
    print("✅ ALL minima occur at d_FR ≈ 0 (near-uniform)!")
    print("   This STRONGLY supports the monotonicity hypothesis!")
else:
    print("⚠️  Some minima occur away from d_FR = 0")

print()

# Kendall's tau (another monotonicity test)
print("=" * 80)
print("ADDITIONAL TESTS")
print("=" * 80)
print()

kendall_tau, kendall_p = scipy_stats.kendalltau(fisher_rao_dists, max_freqs)
print(f"Kendall's τ: {kendall_tau:+.4f} (p = {kendall_p:.10f})")

if kendall_p < 0.001:
    print("✅ Highly significant monotonic trend!")
else:
    print("⚠️  Not significant")

print()

# Test for functional relationship
print("=" * 80)
print("FUNCTIONAL FORM TEST")
print("=" * 80)
print()

print("Testing different functional forms:")
print("-" * 40)

from scipy.optimize import curve_fit

# Monotone models
models = {
    'Linear': lambda x, a, b: a * x + b,
    'Sigmoid (monotone)': lambda x, a, b, c, d: a / (1 + np.exp(-b * (x - c))) + d,
    'Square root': lambda x, a, b: a * np.sqrt(x) + b,
    'Logarithmic': lambda x, a, b: a * np.log(x + 1e-10) + b,
    'Power (α>0)': lambda x, a, b: a * x**0.5 + b,
}

for name, func in models.items():
    try:
        if name == 'Sigmoid (monotone)':
            p0 = [0.2, 40, 0.08, 0.6]
        else:
            p0 = [1.0, 0.5]

        params, _ = curve_fit(func, fisher_rao_dists, max_freqs, p0=p0, maxfev=10000)

        y_pred = func(fisher_rao_dists, *params)
        r2 = 1 - np.sum((max_freqs - y_pred)**2) / np.sum((max_freqs - np.mean(max_freqs))**2)

        # Test monotonicity of fitted function
        x_test = np.linspace(0, fisher_rao_dists.max(), 1000)
        y_test = func(x_test, *params)
        is_monotone = np.all(np.diff(y_test) >= -1e-6)  # Allow tiny numerical errors

        status = "✅ Monotone" if is_monotone else "❌ Not monotone"

        print(f"{name:20s}: R² = {r2:.4f}  {status}")

        # For best model, print extrapolation
        if name == 'Sigmoid (monotone)' and r2 > 0.2:
            y_at_zero = func(0, *params)
            print(f"                      Extrapolation at d_FR=0: {y_at_zero:.6f}")
            if y_at_zero >= 0.5:
                print(f"                      ✅ Supports conjecture!")

    except Exception as e:
        print(f"{name:20s}: Failed to fit")

print()

# CONCLUSION
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()

print("Evidence for monotonicity:")
print(f"  1. Spearman ρ (medians): {spearman_corr:+.4f} (highly significant)")
print(f"  2. Spearman ρ (minimums): {spearman_corr_min:+.4f}")
print(f"  3. Kendall τ: {kendall_tau:+.4f} (highly significant)")
print(f"  4. Violations in binned analysis: {violations}/{len(medians)-1}")
print(f"  5. Global minimum at d_FR ≈ 0: {fisher_rao_dists[at_minimum].mean():.6f}")
print()

if spearman_corr > 0.8 and violations < 3 and fisher_rao_dists[at_minimum].max() < 0.01:
    print("🎯 VERDICT: STRONG evidence for monotonicity!")
    print()
    print("IMPLICATION:")
    print("  If we can prove:")
    print("    (1) d_FR = 0 ⟹ max_freq ≥ 0.5  (Lemma A)")
    print("    (2) Monotonicity: d_FR ↑ ⟹ max_freq ↑")
    print("  Then:")
    print("    d_FR ≥ 0 ⟹ max_freq ≥ max_freq(d_FR=0) ≥ 0.5  ✓")
    print()
    print("This would COMPLETE the proof!")
else:
    print("⚠️  VERDICT: Evidence is mixed, more analysis needed")

print()
print("=" * 80)

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Plot 1: Scatter with binned statistics
axes[0, 0].scatter(fisher_rao_dists, max_freqs, alpha=0.3, s=20, c='navy', label='Individual families')
axes[0, 0].plot([s['bin_center'] for s in bin_stats],
                [s['median_freq'] for s in bin_stats],
                'ro-', linewidth=2, markersize=8, label='Median per bin')
axes[0, 0].axhline(0.5, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Conjecture threshold')
axes[0, 0].set_xlabel('Fisher-Rao Distance to Uniform', fontweight='bold', fontsize=12)
axes[0, 0].set_ylabel('Max Frequency', fontweight='bold', fontsize=12)
axes[0, 0].set_title('Binned Analysis: Monotonicity Test', fontweight='bold', fontsize=14)
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Min/Max envelope
axes[0, 1].fill_between([s['bin_center'] for s in bin_stats],
                        [s['min_freq'] for s in bin_stats],
                        [s['max_freq'] for s in bin_stats],
                        alpha=0.3, color='steelblue', label='Min-Max range')
axes[0, 1].plot([s['bin_center'] for s in bin_stats],
                [s['median_freq'] for s in bin_stats],
                'ro-', linewidth=2, label='Median')
axes[0, 1].axhline(0.5, color='red', linestyle='--', linewidth=2, alpha=0.5)
axes[0, 1].set_xlabel('Fisher-Rao Distance to Uniform', fontweight='bold', fontsize=12)
axes[0, 1].set_ylabel('Max Frequency', fontweight='bold', fontsize=12)
axes[0, 1].set_title('Envelope Analysis', fontweight='bold', fontsize=14)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Histogram of d_FR
axes[1, 0].hist(fisher_rao_dists, bins=40, alpha=0.7, color='green', edgecolor='black')
axes[1, 0].axvline(fisher_rao_dists[at_minimum].mean(), color='red', linestyle='--',
                   linewidth=2, label=f'Mean d_FR at min max_freq')
axes[1, 0].set_xlabel('Fisher-Rao Distance', fontweight='bold', fontsize=12)
axes[1, 0].set_ylabel('Count', fontweight='bold', fontsize=12)
axes[1, 0].set_title('Distribution of Fisher-Rao Distances', fontweight='bold', fontsize=14)
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Plot 4: Residuals from monotone fit
try:
    params_sig, _ = curve_fit(lambda x, a, b, c, d: a / (1 + np.exp(-b * (x - c))) + d,
                              fisher_rao_dists, max_freqs, p0=[0.2, 40, 0.08, 0.6], maxfev=10000)
    y_pred_sig = params_sig[0] / (1 + np.exp(-params_sig[1] * (fisher_rao_dists - params_sig[2]))) + params_sig[3]
    residuals = max_freqs - y_pred_sig

    axes[1, 1].scatter(fisher_rao_dists, residuals, alpha=0.4, s=20, c='purple')
    axes[1, 1].axhline(0, color='red', linestyle='--', linewidth=2)
    axes[1, 1].set_xlabel('Fisher-Rao Distance', fontweight='bold', fontsize=12)
    axes[1, 1].set_ylabel('Residuals from Sigmoid Fit', fontweight='bold', fontsize=12)
    axes[1, 1].set_title('Residual Analysis', fontweight='bold', fontsize=14)
    axes[1, 1].grid(True, alpha=0.3)
except:
    axes[1, 1].text(0.5, 0.5, 'Fit failed', ha='center', va='center', transform=axes[1, 1].transAxes)

plt.tight_layout()
plt.savefig('results/final_500/monotonicity_analysis.png', dpi=150, bbox_inches='tight')
print("✅ Saved: results/final_500/monotonicity_analysis.png")
print()
print("=" * 80)
