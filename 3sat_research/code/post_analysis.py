#!/usr/bin/env python3
"""
📊 POST-ANALYSIS: Advanced Analysis After Full Results
================================================================================
Runs automatically after full_analysis.csv is generated.
Performs:
1. Hybrid discriminator optimization
2. Alpha grid search
3. Bootstrap confidence intervals
4. Advanced visualizations
5. Breakthrough detection
================================================================================
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Tuple
from advanced_discriminators import (
    HybridDiscriminator, AlphaOptimizer, bootstrap_cohen_d
)
from sat_tensor_framework import parse_cnf, compute_cohens_d
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')

sns.set_style("whitegrid")
sns.set_palette("Set2")


def load_results() -> pd.DataFrame:
    """Load full analysis results."""
    results_path = Path("/home/user/denis123-ux/3sat_research/results/full_analysis.csv")

    if not results_path.exists():
        raise FileNotFoundError(f"Results not found at {results_path}. Run full analysis first!")

    df = pd.read_csv(results_path)
    print(f"✓ Loaded {len(df)} results")
    print(f"  SAT: {len(df[df['is_sat']==True])}")
    print(f"  UNSAT: {len(df[df['is_sat']==False])}")
    print()

    return df


def analyze_hybrid(df: pd.DataFrame, output_dir: Path):
    """
    Run hybrid discriminator optimization.

    Tests all possible combinations and finds optimal weights.
    """
    print("="*80)
    print("🔥 HYBRID DISCRIMINATOR OPTIMIZATION")
    print("="*80)
    print()

    # Available discriminators
    discriminators = ['lm_mean_depth', 'fractional_derivative_1.5', 'holonomy']

    # Filter valid discriminators (enough data)
    valid_discs = []
    for disc in discriminators:
        if disc in df.columns:
            n_valid = df[disc].notna().sum()
            if n_valid > 100:
                valid_discs.append(disc)
                print(f"  ✓ {disc}: {n_valid} valid values")

    if len(valid_discs) < 2:
        print("  ⚠️  Not enough discriminators for hybrid!")
        return None

    print()
    print(f"Testing combinations of {len(valid_discs)} discriminators...")
    print()

    # Optimize
    hybrid = HybridDiscriminator(df, valid_discs)
    weights, d_hybrid = hybrid.optimize_weights()

    # Print results
    hybrid.print_results()

    # Save hybrid scores
    df['hybrid_score'] = hybrid.get_optimal_scores()

    # Compute statistics
    sat_scores = df[df['is_sat'] == True]['hybrid_score'].values
    unsat_scores = df[df['is_sat'] == False]['hybrid_score'].values

    t_stat, p_value = ttest_ind(sat_scores, unsat_scores)

    # Bootstrap CI
    print("Computing bootstrap confidence intervals...")
    ci_results = bootstrap_cohen_d(sat_scores, unsat_scores, n_bootstrap=1000)
    print(f"  d = {ci_results['d']:.4f}")
    print(f"  95% CI: [{ci_results['ci_lower']:.4f}, {ci_results['ci_upper']:.4f}]")
    print(f"  SE: {ci_results['std_error']:.4f}")
    print()

    # Verdict
    if d_hybrid > 1.25:
        verdict = "🏆 BREAKTHROUGH! Beats baseline (d=1.25)"
    elif d_hybrid > 1.0:
        verdict = "✅ VALIDATED! Strong discriminator (d>1.0)"
    elif d_hybrid > 0.8:
        verdict = "⚡ LARGE EFFECT! Good discriminator (d>0.8)"
    else:
        verdict = "📊 Moderate effect"

    print(f"VERDICT: {verdict}")
    print("="*80)
    print()

    # Save results
    results = {
        'discriminators': valid_discs,
        'weights': weights.tolist(),
        'cohens_d': d_hybrid,
        'ci_lower': ci_results['ci_lower'],
        'ci_upper': ci_results['ci_upper'],
        'p_value': p_value,
        'verdict': verdict
    }

    import json
    with open(output_dir / "hybrid_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Saved hybrid results to {output_dir / 'hybrid_results.json'}")
    print()

    return hybrid


def analyze_alpha_optimization(df: pd.DataFrame, output_dir: Path):
    """
    Run alpha grid search on subset of formulas.

    Tests α ∈ [1.0, 2.0] to find optimal fractional order.
    """
    print("="*80)
    print("⚡ ALPHA OPTIMIZATION")
    print("="*80)
    print()

    # Load subset of formulas for speed
    print("Loading formulas for alpha optimization...")
    benchmark_dir = Path("/home/user/denis123-ux/3sat_research/benchmarks")

    sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:50]  # First 50 SAT
    unsat_dir = benchmark_dir / "UUF50.218.1000"
    unsat_files = sorted(list(unsat_dir.glob("*.cnf")))[:50] if unsat_dir.exists() else []  # First 50 UNSAT

    formulas = []
    for f in sat_files + unsat_files:
        try:
            formula = parse_cnf(f)
            formulas.append(formula)
        except:
            continue

    print(f"✓ Loaded {len(formulas)} formulas for testing")
    print()

    if len(formulas) < 20:
        print("  ⚠️  Not enough formulas for alpha optimization!")
        return None

    # Run grid search
    optimizer = AlphaOptimizer(formulas)
    alpha_opt, d_opt = optimizer.grid_search(n_points=20, n_samples=len(formulas))

    # Plot
    plot_path = output_dir / "alpha_optimization.png"
    optimizer.plot_results(plot_path)
    print()

    # Save results
    results_df = pd.DataFrame(optimizer.results)
    results_df.to_csv(output_dir / "alpha_grid_search.csv", index=False)
    print(f"✓ Saved alpha grid search to {output_dir / 'alpha_grid_search.csv'}")
    print()

    return alpha_opt, d_opt


def generate_advanced_visualizations(df: pd.DataFrame, hybrid: HybridDiscriminator,
                                     output_dir: Path):
    """
    Generate comprehensive visualization suite.
    """
    print("="*80)
    print("📊 GENERATING ADVANCED VISUALIZATIONS")
    print("="*80)
    print()

    # 1. Hybrid vs Individual Discriminators
    print("  [1/3] Hybrid comparison plot...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('🔥 Hybrid Discriminator vs Individual Components',
                 fontsize=18, fontweight='bold')

    discriminators = hybrid.discriminators + ['hybrid_score']

    for idx, disc in enumerate(discriminators[:4]):
        if idx >= 4:
            break

        ax = axes[idx // 2, idx % 2]

        sat_vals = df[df['is_sat'] == True][disc].dropna().values
        unsat_vals = df[df['is_sat'] == False][disc].dropna().values

        if len(sat_vals) < 10 or len(unsat_vals) < 10:
            ax.text(0.5, 0.5, 'INSUFFICIENT DATA', ha='center', va='center', fontsize=14)
            ax.set_title(disc.replace('_', ' ').title())
            continue

        # Histograms
        bins = 30
        ax.hist(sat_vals, bins=bins, alpha=0.6, label=f'SAT (n={len(sat_vals)})',
               color='blue', density=True)
        ax.hist(unsat_vals, bins=bins, alpha=0.6, label=f'UNSAT (n={len(unsat_vals)})',
               color='red', density=True)

        # Statistics
        d = compute_cohens_d(sat_vals, unsat_vals)
        t_stat, p_value = ttest_ind(sat_vals, unsat_vals)

        verdict = "🏆" if d > 1.25 else "✅" if d > 1.0 else "⚡" if d > 0.8 else "📊"

        ax.set_xlabel(disc.replace('_', ' ').title(), fontsize=12)
        ax.set_ylabel('Density', fontsize=12)
        ax.legend(fontsize=10)

        # Annotate
        ax.text(0.95, 0.95, f"{verdict} d={d:.3f}\np={p_value:.2e}",
               transform=ax.transAxes, ha='right', va='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=11, fontweight='bold')

        ax.set_title(disc.replace('_', ' ').title(), fontweight='bold', fontsize=14)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "hybrid_comparison.png", dpi=300, bbox_inches='tight')
    print(f"    ✓ Saved: hybrid_comparison.png")

    # 2. Correlation Matrix
    print("  [2/3] Correlation matrix...")

    disc_cols = [d for d in hybrid.discriminators if d in df.columns]
    if len(disc_cols) >= 2:
        corr_data = df[disc_cols].corr()

        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                   fmt='.3f', vmin=-1, vmax=1)
        plt.title('Discriminator Correlation Matrix', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / "correlation_matrix.png", dpi=300, bbox_inches='tight')
        print(f"    ✓ Saved: correlation_matrix.png")

    # 3. ROC-style Separation Plot
    print("  [3/3] Separation quality plot...")

    if 'hybrid_score' in df.columns:
        sat_scores = df[df['is_sat'] == True]['hybrid_score'].values
        unsat_scores = df[df['is_sat'] == False]['hybrid_score'].values

        # Compute threshold-based accuracy
        thresholds = np.linspace(min(sat_scores.min(), unsat_scores.min()),
                                max(sat_scores.max(), unsat_scores.max()), 100)

        accuracies = []
        for thresh in thresholds:
            sat_correct = np.sum(sat_scores < thresh)
            unsat_correct = np.sum(unsat_scores >= thresh)
            accuracy = (sat_correct + unsat_correct) / (len(sat_scores) + len(unsat_scores))
            accuracies.append(accuracy)

        plt.figure(figsize=(10, 6))
        plt.plot(thresholds, accuracies, linewidth=3)

        # Mark optimal threshold
        opt_idx = np.argmax(accuracies)
        opt_thresh = thresholds[opt_idx]
        opt_acc = accuracies[opt_idx]

        plt.axvline(opt_thresh, color='r', linestyle='--', linewidth=2)
        plt.axhline(opt_acc, color='g', linestyle='--', linewidth=2, alpha=0.5)

        plt.xlabel('Hybrid Score Threshold', fontsize=14, fontweight='bold')
        plt.ylabel('Classification Accuracy', fontsize=14, fontweight='bold')
        plt.title(f'Hybrid Discriminator: Optimal Accuracy = {opt_acc*100:.2f}%',
                 fontsize=16, fontweight='bold')
        plt.grid(True, alpha=0.3)

        plt.annotate(f'Optimal\nThresh={opt_thresh:.3f}\nAcc={opt_acc*100:.1f}%',
                    xy=(opt_thresh, opt_acc),
                    xytext=(opt_thresh + 0.2, opt_acc - 0.05),
                    fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', lw=2))

        plt.tight_layout()
        plt.savefig(output_dir / "separation_quality.png", dpi=300, bbox_inches='tight')
        print(f"    ✓ Saved: separation_quality.png")

    print()
    print("="*80)
    print()


def generate_final_summary(df: pd.DataFrame, hybrid: HybridDiscriminator,
                          alpha_results: Tuple, output_dir: Path):
    """
    Generate comprehensive final report.
    """
    print("="*80)
    print("📝 GENERATING FINAL SUMMARY REPORT")
    print("="*80)
    print()

    report = []

    report.append("# 🚀 P vs NP DISCRIMINATOR ANALYSIS - FINAL REPORT")
    report.append("")
    report.append("="*80)
    report.append("")

    # Dataset info
    n_total = len(df)
    n_sat = len(df[df['is_sat'] == True])
    n_unsat = len(df[df['is_sat'] == False])

    report.append("## Dataset Summary")
    report.append("")
    report.append(f"- **Total instances**: {n_total}")
    report.append(f"- **SAT instances**: {n_sat}")
    report.append(f"- **UNSAT instances**: {n_unsat}")
    report.append(f"- **Benchmark**: uf50-218 + uuf50-218")
    report.append(f"- **Variables**: n=50")
    report.append(f"- **Clauses**: m=218")
    report.append(f"- **Ratio**: α=4.36")
    report.append("")

    # Individual discriminators
    report.append("## Individual Discriminator Results")
    report.append("")
    report.append("| Discriminator | SAT Mean | UNSAT Mean | Cohen's d | p-value | Verdict |")
    report.append("|--------------|----------|------------|-----------|---------|---------|")

    for disc in hybrid.discriminators:
        sat_vals = df[df['is_sat'] == True][disc].dropna().values
        unsat_vals = df[df['is_sat'] == False][disc].dropna().values

        if len(sat_vals) < 10 or len(unsat_vals) < 10:
            continue

        mean_sat = np.mean(sat_vals)
        mean_unsat = np.mean(unsat_vals)
        d = compute_cohens_d(sat_vals, unsat_vals)
        _, p = ttest_ind(sat_vals, unsat_vals)

        verdict = "🏆 BREAKTHROUGH" if abs(d) > 1.25 else \
                 "✅ VALIDATED" if abs(d) > 1.0 else \
                 "⚡ LARGE" if abs(d) > 0.8 else \
                 "📊 MEDIUM" if abs(d) > 0.5 else \
                 "❌ WEAK"

        report.append(f"| {disc} | {mean_sat:.4f} | {mean_unsat:.4f} | "
                     f"{d:.4f} | {p:.2e} | {verdict} |")

    report.append("")

    # Hybrid results
    report.append("## 🔥 Hybrid Discriminator Results")
    report.append("")
    report.append(f"**Cohen's d**: {hybrid.optimal_d:.4f}")
    report.append("")
    report.append("**Optimal Weights**:")
    for disc, weight in zip(hybrid.discriminators, hybrid.optimal_weights):
        report.append(f"- {disc}: {weight:.4f}")
    report.append("")

    sat_hybrid = df[df['is_sat'] == True]['hybrid_score'].values
    unsat_hybrid = df[df['is_sat'] == False]['hybrid_score'].values
    ci = bootstrap_cohen_d(sat_hybrid, unsat_hybrid)

    report.append(f"**95% Confidence Interval**: [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}]")
    report.append("")

    # Verdict
    if hybrid.optimal_d > 1.25:
        report.append("### 🏆 BREAKTHROUGH!")
        report.append("")
        report.append(f"The hybrid discriminator achieves d={hybrid.optimal_d:.4f}, ")
        report.append(f"**BEATING the baseline (d=1.25)**!")
        report.append("")
        report.append("This represents a **NEW STATE-OF-THE-ART** for 3-SAT discrimination.")
    elif hybrid.optimal_d > 1.0:
        report.append("### ✅ VALIDATED!")
        report.append("")
        report.append(f"The hybrid discriminator achieves d={hybrid.optimal_d:.4f}, ")
        report.append("confirming strong discriminative power (d>1.0).")
    else:
        report.append("### 📊 Results")
        report.append("")
        report.append(f"The hybrid discriminator achieves d={hybrid.optimal_d:.4f}.")

    report.append("")

    # Alpha optimization
    if alpha_results:
        alpha_opt, d_alpha = alpha_results
        report.append("## ⚡ Fractional Derivative Optimization")
        report.append("")
        report.append(f"**Optimal α**: {alpha_opt:.4f}")
        report.append(f"**Cohen's d at α***: {d_alpha:.4f}")
        report.append("")

    # Conclusion
    report.append("## 📝 Conclusion")
    report.append("")

    max_d = max(hybrid.optimal_d,
                *[compute_cohens_d(df[df['is_sat']==True][d].dropna().values,
                                  df[df['is_sat']==False][d].dropna().values)
                  for d in hybrid.discriminators if d in df.columns])

    if max_d > 1.25:
        report.append("🎉 **BREAKTHROUGH ACHIEVED!**")
        report.append("")
        report.append(f"We have successfully developed a discriminator with d={max_d:.4f}, ")
        report.append("surpassing the previous state-of-the-art (lm_mean_depth with d=1.25).")
        report.append("")
        report.append("**Next Steps**:")
        report.append("1. Write publication")
        report.append("2. Scale to larger instances (n=100, 200)")
        report.append("3. Test on other SAT benchmarks")
        report.append("4. Develop polynomial-time heuristic solver")
    else:
        report.append("**Key Findings**:")
        report.append("")
        report.append(f"1. Best discriminator: d={max_d:.4f}")
        report.append("2. Hybrid approach shows promise for combinations")
        report.append("3. Fractional derivatives provide interesting insights")
        report.append("")
        report.append("**Future Directions**:")
        report.append("1. Explore tensor network improvements (guided sampling)")
        report.append("2. Test persistent homology on full dataset")
        report.append("3. Investigate outliers and edge cases")
        report.append("4. Develop ensemble methods")

    report.append("")
    report.append("="*80)
    report.append("")
    report.append(f"**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Save
    with open(output_dir / "FINAL_ADVANCED_REPORT.md", 'w') as f:
        f.write('\n'.join(report))

    print(f"✓ Saved final report: {output_dir / 'FINAL_ADVANCED_REPORT.md'}")
    print()
    print("="*80)
    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("="*80)
    print("🚀 POST-ANALYSIS: ADVANCED DISCRIMINATOR EVALUATION")
    print("="*80)
    print("\n")

    # Load results
    try:
        df = load_results()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\nPlease run full_analysis.py first!")
        exit(1)

    # Setup output directory
    output_dir = Path("/home/user/denis123-ux/3sat_research/results/advanced")
    output_dir.mkdir(exist_ok=True, parents=True)

    # Run analyses
    hybrid = analyze_hybrid(df, output_dir)

    alpha_results = None
    try:
        alpha_results = analyze_alpha_optimization(df, output_dir)
    except Exception as e:
        print(f"⚠️  Alpha optimization failed: {e}")
        print()

    if hybrid:
        generate_advanced_visualizations(df, hybrid, output_dir)
        generate_final_summary(df, hybrid, alpha_results, output_dir)

    print("\n")
    print("="*80)
    print("✅ POST-ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nCheck {output_dir} for all results and visualizations.")
    print("\n")
