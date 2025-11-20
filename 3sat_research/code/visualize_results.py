#!/usr/bin/env python3
"""
📊 VISUALIZATION & ANALYSIS
================================================================================
Generate comprehensive visualizations and final report.
================================================================================
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import ttest_ind
import json

sns.set_style("whitegrid")
sns.set_palette("Set2")


def load_results(results_dir: Path) -> pd.DataFrame:
    """Load analysis results."""
    df = pd.DataFrame(pd.read_csv(results_dir / "full_analysis.csv"))
    print(f"✓ Loaded {len(df)} results")
    print(f"  SAT: {len(df[df['is_sat']==True])}")
    print(f"  UNSAT: {len(df[df['is_sat']==False])}")
    return df


def compute_cohens_d(sat_vals, unsat_vals):
    """Compute Cohen's d."""
    mean_sat = np.mean(sat_vals)
    mean_unsat = np.mean(unsat_vals)
    std_sat = np.std(sat_vals, ddof=1)
    std_unsat = np.std(unsat_vals, ddof=1)
    n_sat = len(sat_vals)
    n_unsat = len(unsat_vals)
    pooled_std = np.sqrt(((n_sat-1)*std_sat**2 + (n_unsat-1)*std_unsat**2) / (n_sat+n_unsat-2))
    return (mean_unsat - mean_sat) / pooled_std if pooled_std > 0 else 0.0


def generate_distributions_plot(df: pd.DataFrame, output_dir: Path):
    """
    Generate distribution plots for all discriminators.
    """
    discriminators = ['lm_mean_depth', 'fractional_derivative_1.5', 'holonomy']

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('🚀 Discriminator Distributions: SAT vs UNSAT', fontsize=16, fontweight='bold')

    sat_df = df[df['is_sat'] == True]
    unsat_df = df[df['is_sat'] == False]

    for idx, disc in enumerate(discriminators):
        ax = axes[idx]

        sat_vals = sat_df[disc].dropna().values
        unsat_vals = unsat_df[disc].dropna().values

        if len(sat_vals) < 10 or len(unsat_vals) < 10:
            ax.text(0.5, 0.5, 'INSUFFICIENT DATA', ha='center', va='center', fontsize=14)
            ax.set_title(disc)
            continue

        # Compute statistics
        cohens_d = compute_cohens_d(sat_vals, unsat_vals)
        t_stat, p_value = ttest_ind(sat_vals, unsat_vals)

        # Plot histograms
        bins = 30
        ax.hist(sat_vals, bins=bins, alpha=0.6, label=f'SAT (μ={np.mean(sat_vals):.3f})', color='blue', density=True)
        ax.hist(unsat_vals, bins=bins, alpha=0.6, label=f'UNSAT (μ={np.mean(unsat_vals):.3f})', color='red', density=True)

        ax.set_xlabel(disc.replace('_', ' ').title())
        ax.set_ylabel('Density')
        ax.legend()

        # Annotate with statistics
        verdict = "🏆 BREAKTHROUGH!" if abs(cohens_d) > 1.25 else \
                  "✅ VALIDATED" if abs(cohens_d) > 1.0 else \
                  "⚡ LARGE" if abs(cohens_d) > 0.8 else \
                  "📊 MEDIUM" if abs(cohens_d) > 0.5 else \
                  "❌ WEAK"

        ax.text(0.95, 0.95, f"Cohen's d = {cohens_d:.3f}\np = {p_value:.2e}\n{verdict}",
                transform=ax.transAxes, ha='right', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                fontsize=10, fontweight='bold')

        ax.set_title(f"{disc.replace('_', ' ').title()}", fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / "distributions.png", dpi=300, bbox_inches='tight')
    print(f"✓ Saved: distributions.png")


def generate_comparison_table(df: pd.DataFrame, output_dir: Path):
    """
    Generate comparison table with all statistics.
    """
    discriminators = ['lm_mean_depth', 'fractional_derivative_1.5', 'holonomy']

    sat_df = df[df['is_sat'] == True]
    unsat_df = df[df['is_sat'] == False]

    results = []

    for disc in discriminators:
        sat_vals = sat_df[disc].dropna().values
        unsat_vals = unsat_df[disc].dropna().values

        if len(sat_vals) < 10 or len(unsat_vals) < 10:
            continue

        mean_sat = np.mean(sat_vals)
        mean_unsat = np.mean(unsat_vals)
        std_sat = np.std(sat_vals, ddof=1)
        std_unsat = np.std(unsat_vals, ddof=1)

        cohens_d = compute_cohens_d(sat_vals, unsat_vals)
        t_stat, p_value = ttest_ind(sat_vals, unsat_vals)

        results.append({
            'Discriminator': disc.replace('_', ' ').title(),
            'SAT Mean': f"{mean_sat:.4f}",
            'SAT Std': f"{std_sat:.4f}",
            'UNSAT Mean': f"{mean_unsat:.4f}",
            'UNSAT Std': f"{std_unsat:.4f}",
            "Cohen's d": f"{cohens_d:.4f}",
            'p-value': f"{p_value:.2e}",
            'Verdict': "🏆 BREAKTHROUGH" if abs(cohens_d) > 1.25 else
                      "✅ VALIDATED" if abs(cohens_d) > 1.0 else
                      "⚡ LARGE" if abs(cohens_d) > 0.8 else
                      "📊 MEDIUM" if abs(cohens_d) > 0.5 else
                      "❌ WEAK"
        })

    results_df = pd.DataFrame(results)

    # Save as CSV
    results_df.to_csv(output_dir / "comparison_table.csv", index=False)
    print(f"✓ Saved: comparison_table.csv")

    # Also save as pretty text table
    with open(output_dir / "comparison_table.txt", 'w') as f:
        f.write("="*100 + "\n")
        f.write("📊 DISCRIMINATOR COMPARISON TABLE\n")
        f.write("="*100 + "\n\n")
        f.write(results_df.to_string(index=False))
        f.write("\n\n" + "="*100 + "\n")

    print(f"✓ Saved: comparison_table.txt")

    return results_df


def generate_scatter_plot(df: pd.DataFrame, output_dir: Path):
    """
    Generate scatter plot: lm_mean_depth vs fractional_derivative.
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    sat_df = df[df['is_sat'] == True]
    unsat_df = df[df['is_sat'] == False]

    ax.scatter(sat_df['lm_mean_depth'], sat_df['fractional_derivative_1.5'],
              alpha=0.5, s=30, label='SAT', color='blue')
    ax.scatter(unsat_df['lm_mean_depth'], unsat_df['fractional_derivative_1.5'],
              alpha=0.5, s=30, label='UNSAT', color='red')

    ax.set_xlabel('lm_mean_depth (baseline)', fontsize=12, fontweight='bold')
    ax.set_ylabel('fractional_derivative_1.5', fontsize=12, fontweight='bold')
    ax.set_title('Discriminator Correlation: Depth vs Fractional Derivative', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "scatter_depth_vs_frac.png", dpi=300, bbox_inches='tight')
    print(f"✓ Saved: scatter_depth_vs_frac.png")


def generate_final_report(df: pd.DataFrame, results_df: pd.DataFrame, output_dir: Path):
    """
    Generate comprehensive markdown report.
    """
    report = []

    report.append("# 🚀 P vs NP DISCRIMINATOR ANALYSIS - FINAL REPORT")
    report.append("")
    report.append("="*80)
    report.append("")

    # Summary
    n_sat = len(df[df['is_sat'] == True])
    n_unsat = len(df[df['is_sat'] == False])

    report.append("## Executive Summary")
    report.append("")
    report.append(f"**Dataset:** {n_sat} SAT + {n_unsat} UNSAT = {n_sat+n_unsat} total instances")
    report.append(f"**Benchmark:** uf50-218 (satisfiable) + uuf50-218 (unsatisfiable)")
    report.append(f"**Variables:** n=50, Clauses: m=218, Ratio: α=4.36")
    report.append("")

    # Results table
    report.append("## 📊 Results")
    report.append("")
    report.append("```")
    report.append(results_df.to_string(index=False))
    report.append("```")
    report.append("")

    # Winner
    max_d_row = results_df.iloc[results_df["Cohen's d"].astype(float).abs().idxmax()]
    winner = max_d_row['Discriminator']
    winner_d = float(max_d_row["Cohen's d"])

    report.append(f"## 🏆 Winner: {winner}")
    report.append("")
    report.append(f"**Cohen's d = {winner_d:.4f}**")
    report.append("")

    if abs(winner_d) > 1.25:
        report.append("🎉 **BREAKTHROUGH!** This discriminator beats the baseline (d=1.25)!")
    elif abs(winner_d) > 1.0:
        report.append("✅ **VALIDATED!** Strong discriminator (d>1.0).")
    elif abs(winner_d) > 0.8:
        report.append("⚡ **LARGE EFFECT!** Good discriminator (d>0.8).")
    else:
        report.append("📊 Moderate discriminator.")

    report.append("")

    # Insights
    report.append("## 💡 Key Insights")
    report.append("")

    for idx, row in results_df.iterrows():
        disc = row['Discriminator']
        d = float(row["Cohen's d"])
        p = float(row['p-value'])

        if abs(d) > 0.8:
            report.append(f"### {disc}")
            report.append(f"- **Effect size:** d={d:.4f} ({'UNSAT > SAT' if d > 0 else 'SAT > UNSAT'})")
            report.append(f"- **Significance:** p={p:.2e} ({'***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'n.s.'})")
            report.append(f"- **SAT:** μ={row['SAT Mean']}, σ={row['SAT Std']}")
            report.append(f"- **UNSAT:** μ={row['UNSAT Mean']}, σ={row['UNSAT Std']}")
            report.append("")

    # Conclusion
    report.append("## 📝 Conclusion")
    report.append("")

    if winner_d > 1.25:
        report.append(f"**{winner}** achieves breakthrough-level discrimination (d={winner_d:.4f} > 1.25)!")
        report.append("")
        report.append("This represents a **NEW STATE-OF-THE-ART** for 3-SAT discriminators,")
        report.append("surpassing the previous best (lm_mean_depth with d=1.25).")
    else:
        report.append(f"**{winner}** achieves the highest discrimination (d={winner_d:.4f}),")
        report.append(f"but does not surpass the breakthrough threshold (d=1.25).")
        report.append("")
        report.append("**Next steps:**")
        report.append("1. Explore hybrid discriminators (combinations)")
        report.append("2. Test on larger instances (n=100, n=200)")
        report.append("3. Investigate outliers and edge cases")

    report.append("")
    report.append("="*80)
    report.append("")
    report.append(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Save report
    with open(output_dir / "FINAL_REPORT.md", 'w') as f:
        f.write('\n'.join(report))

    print(f"✓ Saved: FINAL_REPORT.md")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    results_dir = Path("/home/user/denis123-ux/3sat_research/results")
    visualizations_dir = results_dir / "visualizations"
    visualizations_dir.mkdir(exist_ok=True)

    print("="*80)
    print("📊 VISUALIZATION & ANALYSIS")
    print("="*80)
    print()

    # Load results
    df = load_results(results_dir)
    print()

    # Generate visualizations
    print("Generating visualizations...")
    generate_distributions_plot(df, visualizations_dir)
    generate_scatter_plot(df, visualizations_dir)
    print()

    # Generate comparison table
    print("Generating comparison table...")
    results_df = generate_comparison_table(df, visualizations_dir)
    print()

    # Generate final report
    print("Generating final report...")
    generate_final_report(df, results_df, visualizations_dir)
    print()

    print("="*80)
    print(f"✅ DONE! Check {visualizations_dir} for all outputs.")
    print("="*80)
