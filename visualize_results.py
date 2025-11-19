"""
Visualization script for large-scale analysis results.

Generates comprehensive plots and figures from analysis data.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 150


def load_results(results_dir: str = "results/large_scale"):
    """Load analysis results."""
    results_dir = Path(results_dir)

    # Load full results
    with open(results_dir / "results_full.pkl", 'rb') as f:
        results = pickle.load(f)

    return results


def plot_frequency_distributions(results, output_dir):
    """Plot frequency distributions."""
    print("Generating frequency distribution plots...")

    valid_families = [f for f in results['families'] if not f.get('skip', False) and 'error' not in f]

    max_freqs = [f['frequencies']['max'] for f in valid_families]
    min_freqs = [f['frequencies']['min'] for f in valid_families]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Max frequency histogram
    axes[0, 0].hist(max_freqs, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    axes[0, 0].axvline(0.5, color='red', linestyle='--', linewidth=2, label='Conjecture threshold')
    axes[0, 0].set_xlabel('Max Frequency', fontsize=12)
    axes[0, 0].set_ylabel('Count', fontsize=12)
    axes[0, 0].set_title('Distribution of Max Frequencies', fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Min frequency histogram
    axes[0, 1].hist(min_freqs, bins=50, edgecolor='black', alpha=0.7, color='coral')
    axes[0, 1].set_xlabel('Min Frequency', fontsize=12)
    axes[0, 1].set_ylabel('Count', fontsize=12)
    axes[0, 1].set_title('Distribution of Min Frequencies', fontsize=14, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)

    # Cumulative distribution of max frequency
    sorted_max = np.sort(max_freqs)
    cumulative = np.arange(1, len(sorted_max) + 1) / len(sorted_max)
    axes[1, 0].plot(sorted_max, cumulative, linewidth=2, color='darkblue')
    axes[1, 0].axvline(0.5, color='red', linestyle='--', linewidth=2)
    axes[1, 0].set_xlabel('Max Frequency', fontsize=12)
    axes[1, 0].set_ylabel('Cumulative Probability', fontsize=12)
    axes[1, 0].set_title('CDF of Max Frequencies', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)

    # Box plot
    axes[1, 1].boxplot([max_freqs, min_freqs], labels=['Max Frequency', 'Min Frequency'])
    axes[1, 1].axhline(0.5, color='red', linestyle='--', linewidth=2, alpha=0.5)
    axes[1, 1].set_ylabel('Frequency', fontsize=12)
    axes[1, 1].set_title('Frequency Distributions (Box Plot)', fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "frequency_distributions.png", bbox_inches='tight')
    print(f"  Saved: frequency_distributions.png")
    plt.close()


def plot_quantum_analysis(results, output_dir):
    """Plot quantum information theory results."""
    print("Generating quantum analysis plots...")

    valid_families = [f for f in results['families']
                     if not f.get('skip', False)
                     and 'quantum' in f
                     and 'error' not in f['quantum']]

    if not valid_families:
        print("  No valid quantum data!")
        return

    entropies = [f['quantum']['von_neumann_entropy'] for f in valid_families]
    purities = [f['quantum']['purity'] for f in valid_families]
    bounds = [f['quantum']['quantum_bound'] for f in valid_families]
    max_freqs = [f['frequencies']['max'] for f in valid_families]

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # Entropy distribution
    axes[0, 0].hist(entropies, bins=40, edgecolor='black', alpha=0.7, color='purple')
    axes[0, 0].set_xlabel('Von Neumann Entropy', fontsize=11)
    axes[0, 0].set_ylabel('Count', fontsize=11)
    axes[0, 0].set_title('Von Neumann Entropy Distribution', fontsize=12, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)

    # Purity distribution
    axes[0, 1].hist(purities, bins=40, edgecolor='black', alpha=0.7, color='green')
    axes[0, 1].set_xlabel('Purity', fontsize=11)
    axes[0, 1].set_ylabel('Count', fontsize=11)
    axes[0, 1].set_title('Purity Distribution', fontsize=12, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)

    # Quantum bound distribution
    axes[0, 2].hist(bounds, bins=40, edgecolor='black', alpha=0.7, color='orange')
    axes[0, 2].axvline(0.5, color='red', linestyle='--', linewidth=2)
    axes[0, 2].set_xlabel('Quantum Bound', fontsize=11)
    axes[0, 2].set_ylabel('Count', fontsize=11)
    axes[0, 2].set_title('Quantum Bound Distribution', fontsize=12, fontweight='bold')
    axes[0, 2].grid(True, alpha=0.3)

    # Entropy vs Max Frequency
    axes[1, 0].scatter(entropies, max_freqs, alpha=0.3, s=10)
    axes[1, 0].axhline(0.5, color='red', linestyle='--', alpha=0.5)
    axes[1, 0].set_xlabel('Von Neumann Entropy', fontsize=11)
    axes[1, 0].set_ylabel('Max Frequency', fontsize=11)
    axes[1, 0].set_title('Entropy vs Max Frequency', fontsize=12, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)

    # Purity vs Max Frequency
    axes[1, 1].scatter(purities, max_freqs, alpha=0.3, s=10, color='green')
    axes[1, 1].axhline(0.5, color='red', linestyle='--', alpha=0.5)
    axes[1, 1].set_xlabel('Purity', fontsize=11)
    axes[1, 1].set_ylabel('Max Frequency', fontsize=11)
    axes[1, 1].set_title('Purity vs Max Frequency', fontsize=12, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)

    # Quantum Bound vs Actual Max Frequency
    axes[1, 2].scatter(bounds, max_freqs, alpha=0.3, s=10, color='orange')
    axes[1, 2].plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect bound')
    axes[1, 2].axhline(0.5, color='red', linestyle='--', alpha=0.3)
    axes[1, 2].axvline(0.5, color='red', linestyle='--', alpha=0.3)
    axes[1, 2].set_xlabel('Quantum Bound', fontsize=11)
    axes[1, 2].set_ylabel('Actual Max Frequency', fontsize=11)
    axes[1, 2].set_title('Quantum Bound vs Actual', fontsize=12, fontweight='bold')
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "quantum_analysis.png", bbox_inches='tight')
    print(f"  Saved: quantum_analysis.png")
    plt.close()


def plot_tensor_analysis(results, output_dir):
    """Plot tensor network analysis results."""
    print("Generating tensor network plots...")

    valid_families = [f for f in results['families']
                     if not f.get('skip', False)
                     and 'tensor' in f
                     and 'error' not in f['tensor']]

    if not valid_families:
        print("  No valid tensor data!")
        return

    ranks = [f['tensor']['tensor_rank'] for f in valid_families]
    bond_dims = [f['tensor']['max_bond_dimension'] for f in valid_families]
    entanglements = [f['tensor']['avg_entanglement'] for f in valid_families]
    max_freqs = [f['frequencies']['max'] for f in valid_families]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Tensor rank distribution
    axes[0, 0].hist(ranks, bins=40, edgecolor='black', alpha=0.7, color='teal')
    axes[0, 0].set_xlabel('Tensor Rank', fontsize=12)
    axes[0, 0].set_ylabel('Count', fontsize=12)
    axes[0, 0].set_title('Tensor Rank Distribution', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)

    # Bond dimension distribution
    axes[0, 1].hist(bond_dims, bins=40, edgecolor='black', alpha=0.7, color='crimson')
    axes[0, 1].set_xlabel('Max Bond Dimension', fontsize=12)
    axes[0, 1].set_ylabel('Count', fontsize=12)
    axes[0, 1].set_title('Bond Dimension Distribution', fontsize=14, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)

    # Entanglement vs Max Frequency
    axes[1, 0].scatter(entanglements, max_freqs, alpha=0.3, s=10, color='navy')
    axes[1, 0].axhline(0.5, color='red', linestyle='--', alpha=0.5)
    axes[1, 0].set_xlabel('Avg Entanglement Entropy', fontsize=12)
    axes[1, 0].set_ylabel('Max Frequency', fontsize=12)
    axes[1, 0].set_title('Entanglement vs Max Frequency', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)

    # Bond Dimension vs Max Frequency
    axes[1, 1].scatter(bond_dims, max_freqs, alpha=0.3, s=10, color='darkred')
    axes[1, 1].axhline(0.5, color='red', linestyle='--', alpha=0.5)
    axes[1, 1].set_xlabel('Max Bond Dimension', fontsize=12)
    axes[1, 1].set_ylabel('Max Frequency', fontsize=12)
    axes[1, 1].set_title('Bond Dimension vs Max Frequency', fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "tensor_analysis.png", bbox_inches='tight')
    print(f"  Saved: tensor_analysis.png")
    plt.close()


def plot_correlations(results, output_dir):
    """Plot correlation matrix and scatter plots."""
    print("Generating correlation plots...")

    valid_families = [f for f in results['families']
                     if not f.get('skip', False)
                     and 'quantum' in f and 'error' not in f['quantum']
                     and 'tensor' in f and 'error' not in f['tensor']]

    if not valid_families:
        print("  Not enough data for correlations!")
        return

    # Extract features
    data = {
        'Max Freq': [f['frequencies']['max'] for f in valid_families],
        'Min Freq': [f['frequencies']['min'] for f in valid_families],
        'Entropy': [f['quantum']['von_neumann_entropy'] for f in valid_families],
        'Purity': [f['quantum']['purity'] for f in valid_families],
        'Q-Bound': [f['quantum']['quantum_bound'] for f in valid_families],
        'Bond Dim': [f['tensor']['max_bond_dimension'] for f in valid_families],
        'T-Rank': [f['tensor']['tensor_rank'] for f in valid_families]
    }

    # Correlation matrix
    import pandas as pd
    df = pd.DataFrame(data)
    corr_matrix = df.corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm',
                center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('Correlation Matrix: All Measures', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / "correlation_matrix.png", bbox_inches='tight')
    print(f"  Saved: correlation_matrix.png")
    plt.close()


def plot_challenging_cases(results, output_dir):
    """Plot analysis of challenging cases."""
    print("Generating challenging cases plot...")

    challenging = results.get('challenging_cases', [])

    if not challenging:
        print("  No challenging cases found!")
        return

    # Sort by max frequency
    challenging = sorted(challenging, key=lambda x: x['frequencies']['max'])

    max_freqs = [c['frequencies']['max'] for c in challenging]
    indices = list(range(len(max_freqs)))

    plt.figure(figsize=(12, 6))
    plt.scatter(indices, max_freqs, s=50, alpha=0.6, color='darkred')
    plt.axhline(0.5, color='red', linestyle='--', linewidth=2, label='Conjecture threshold')
    plt.axhline(0.55, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    plt.xlabel('Case Index (sorted by max frequency)', fontsize=12)
    plt.ylabel('Max Frequency', fontsize=12)
    plt.title(f'Challenging Cases (n={len(challenging)}): Max Frequency ∈ [0.50, 0.55]',
              fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "challenging_cases.png", bbox_inches='tight')
    print(f"  Saved: challenging_cases.png")
    plt.close()


def plot_summary_dashboard(results, output_dir):
    """Create summary dashboard."""
    print("Generating summary dashboard...")

    stats = results['statistics']

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle('Union-Closed Sets Conjecture: Analysis Dashboard',
                 fontsize=18, fontweight='bold', y=0.98)

    # Stats boxes
    ax_stats = fig.add_subplot(gs[0, :])
    ax_stats.axis('off')

    stats_text = f"""
    Total Families: {stats['basic']['total_families']:,}
    Satisfying Conjecture: {stats['basic']['satisfies_conjecture_count']:,} ({100*stats['basic']['satisfies_conjecture_count']/stats['basic']['total_families']:.2f}%)
    Counterexamples: {stats['basic']['counterexample_count']} {'⚠️' if stats['basic']['counterexample_count'] > 0 else '✅'}
    Challenging Cases: {stats['challenging_cases_count']}

    Max Frequency: μ={stats['frequencies']['max_frequency']['mean']:.4f}, σ={stats['frequencies']['max_frequency']['std']:.4f}, min={stats['frequencies']['max_frequency']['min']:.4f}
    """

    ax_stats.text(0.5, 0.5, stats_text, ha='center', va='center',
                  fontsize=12, family='monospace',
                  bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Frequency histogram
    valid_families = [f for f in results['families'] if not f.get('skip', False) and 'error' not in f]
    max_freqs = [f['frequencies']['max'] for f in valid_families]

    ax1 = fig.add_subplot(gs[1, 0])
    ax1.hist(max_freqs, bins=40, edgecolor='black', alpha=0.7, color='steelblue')
    ax1.axvline(0.5, color='red', linestyle='--', linewidth=2)
    ax1.set_xlabel('Max Frequency')
    ax1.set_ylabel('Count')
    ax1.set_title('Max Frequency Distribution')
    ax1.grid(True, alpha=0.3)

    # Quantum entropy (if available)
    if stats['quantum']['num_valid'] > 0:
        quantum_families = [f for f in valid_families
                          if 'quantum' in f and 'error' not in f['quantum']]
        entropies = [f['quantum']['von_neumann_entropy'] for f in quantum_families]

        ax2 = fig.add_subplot(gs[1, 1])
        ax2.hist(entropies, bins=40, edgecolor='black', alpha=0.7, color='purple')
        ax2.set_xlabel('Von Neumann Entropy')
        ax2.set_ylabel('Count')
        ax2.set_title('Quantum Entropy')
        ax2.grid(True, alpha=0.3)

    # Tensor bond dimension (if available)
    if stats['tensor']['num_valid'] > 0:
        tensor_families = [f for f in valid_families
                         if 'tensor' in f and 'error' not in f['tensor']]
        bond_dims = [f['tensor']['max_bond_dimension'] for f in tensor_families]

        ax3 = fig.add_subplot(gs[1, 2])
        ax3.hist(bond_dims, bins=40, edgecolor='black', alpha=0.7, color='crimson')
        ax3.set_xlabel('Bond Dimension')
        ax3.set_ylabel('Count')
        ax3.set_title('Tensor Bond Dimension')
        ax3.grid(True, alpha=0.3)

    # Scatter plots
    if stats['quantum']['num_valid'] > 0:
        quantum_families = [f for f in valid_families
                          if 'quantum' in f and 'error' not in f['quantum']]
        entropies = [f['quantum']['von_neumann_entropy'] for f in quantum_families]
        q_max_freqs = [f['frequencies']['max'] for f in quantum_families]

        ax4 = fig.add_subplot(gs[2, 0])
        ax4.scatter(entropies, q_max_freqs, alpha=0.3, s=5)
        ax4.axhline(0.5, color='red', linestyle='--', alpha=0.5)
        ax4.set_xlabel('Entropy')
        ax4.set_ylabel('Max Freq')
        ax4.set_title('Entropy vs Frequency')
        ax4.grid(True, alpha=0.3)

    if stats['quantum']['num_valid'] > 0:
        bounds = [f['quantum']['quantum_bound'] for f in quantum_families]

        ax5 = fig.add_subplot(gs[2, 1])
        ax5.scatter(bounds, q_max_freqs, alpha=0.3, s=5, color='orange')
        ax5.plot([0, 1], [0, 1], 'r--', linewidth=2, alpha=0.5)
        ax5.axhline(0.5, color='red', linestyle='--', alpha=0.3)
        ax5.axvline(0.5, color='red', linestyle='--', alpha=0.3)
        ax5.set_xlabel('Quantum Bound')
        ax5.set_ylabel('Max Freq')
        ax5.set_title('Quantum Bound vs Actual')
        ax5.grid(True, alpha=0.3)

    # Correlation text
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.axis('off')

    if stats['correlations']:
        corr_text = "Key Correlations:\n\n"
        for key, value in stats['correlations'].items():
            corr_text += f"{key}:\n  {value:.4f}\n\n"
        ax6.text(0.1, 0.5, corr_text, va='center', fontsize=10, family='monospace')

    plt.savefig(output_dir / "dashboard.png", bbox_inches='tight', dpi=150)
    print(f"  Saved: dashboard.png")
    plt.close()


def generate_all_plots(results_dir: str = "results/large_scale"):
    """Generate all visualization plots."""
    print("=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)
    print()

    results_dir = Path(results_dir)
    results = load_results(results_dir)

    plot_frequency_distributions(results, results_dir)
    plot_quantum_analysis(results, results_dir)
    plot_tensor_analysis(results, results_dir)
    plot_correlations(results, results_dir)
    plot_challenging_cases(results, results_dir)
    plot_summary_dashboard(results, results_dir)

    print()
    print("=" * 80)
    print("✅ All visualizations generated!")
    print(f"📁 Output directory: {results_dir}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        generate_all_plots()
    except FileNotFoundError:
        print("❌ Results not found! Run large_scale_analysis.py first.")
