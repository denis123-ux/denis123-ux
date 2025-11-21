#!/usr/bin/env python3
"""
COMPLETE EXPERIMENTAL ANALYSIS

Runs all three revolutionary approaches:
1. Spectral Graph Theory
2. Ricci Curvature Geometry
3. Kolmogorov Complexity

Tests key theorems and generates results
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import json
from datetime import datetime

from graph_engine import CollatzGraph, quick_trajectory
from spectral_analysis import CollatzSpectralAnalyzer, test_spectral_convergence_theorem
from ricci_curvature import analyze_ricci_curvature_collatz
from complexity import (
    KolmogorovComplexityAnalyzer,
    test_low_complexity_theorem,
    analyze_complexity_vs_stopping_time
)


class CollatzExperiment:
    """Main experiment runner"""

    def __init__(self, max_value: int = 10000, results_dir: str = '../results'):
        self.max_value = max_value
        self.results_dir = results_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create results directory
        os.makedirs(results_dir, exist_ok=True)

        # Results storage
        self.results = {
            'metadata': {
                'max_value': max_value,
                'timestamp': self.timestamp,
            },
            'graph_statistics': {},
            'spectral_analysis': {},
            'ricci_curvature': {},
            'complexity_analysis': {},
        }

    def build_graph(self, verbose: bool = True):
        """Step 1: Build Collatz graph"""
        if verbose:
            print("\n" + "="*70)
            print("STEP 1: BUILDING COLLATZ GRAPH")
            print("="*70)

        self.graph = CollatzGraph(max_value=self.max_value)
        self.graph.build_graph(verbose=verbose)

        # Compute statistics
        stats = self.graph.compute_graph_statistics()
        self.results['graph_statistics'] = stats

        if verbose:
            print(f"\nGraph Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

    def run_spectral_analysis(self, verbose: bool = True):
        """Step 2: Spectral analysis"""
        if verbose:
            print("\n" + "="*70)
            print("STEP 2: SPECTRAL ANALYSIS")
            print("="*70)

        # Convert to adjacency matrix
        adj_matrix, node_list = self.graph.to_adjacency_matrix()

        # Create analyzer
        analyzer = CollatzSpectralAnalyzer(adj_matrix, node_list)

        # Run analysis
        test_results = test_spectral_convergence_theorem(analyzer, verbose=verbose)

        # Store results
        props = test_results['spectral_properties']
        self.results['spectral_analysis'] = {
            'spectral_gap': float(props.spectral_gap),
            'spectral_radius': float(props.spectral_radius),
            'algebraic_connectivity': float(props.algebraic_connectivity),
            'mixing_time_bound': float(props.mixing_time_bound) if props.mixing_time_bound else None,
            'eigenvalues': props.eigenvalues.tolist()[:10],  # Store top 10
            'theorem_supported': test_results['theorem_supported'],
        }

        # Plot spectrum
        if verbose:
            print("\nGenerating spectral plots...")
        fig = analyzer.plot_spectrum(k=20)
        plot_path = os.path.join(self.results_dir, f'spectrum_{self.timestamp}.png')
        fig.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        if verbose:
            print(f"Saved spectrum plot to {plot_path}")

        return analyzer

    def run_ricci_curvature_analysis(self, verbose: bool = True):
        """Step 3: Ricci curvature analysis"""
        if verbose:
            print("\n" + "="*70)
            print("STEP 3: RICCI CURVATURE ANALYSIS")
            print("="*70)

        # Convert to NetworkX
        G = self.graph.to_networkx()

        # Limit analysis to reasonable number of edges for performance
        sample_edges = min(2000, len(G.edges()))

        # Run analysis
        orc, test_results = analyze_ricci_curvature_collatz(
            G,
            alpha=0.5,
            max_distance=3,
            sample_edges=sample_edges,
            verbose=verbose
        )

        # Store results
        analysis = test_results['analysis']
        self.results['ricci_curvature'] = {
            'mean_curvature': float(analysis['mean_curvature']),
            'median_curvature': float(analysis['median_curvature']),
            'std_curvature': float(analysis['std_curvature']),
            'min_curvature': float(analysis['min_curvature']),
            'max_curvature': float(analysis['max_curvature']),
            'fraction_negative': float(analysis['fraction_negative']),
            'fraction_positive': float(analysis['fraction_positive']),
            'hypothesis_supported': test_results['hypothesis_supported'],
            'strength': float(test_results['strength']),
        }

        # Plot curvature distribution
        if verbose:
            print("\nGenerating curvature plots...")
        self._plot_curvature_distribution(orc.curvatures)

        return orc

    def run_complexity_analysis(self, verbose: bool = True, num_samples: int = 1000):
        """Step 4: Kolmogorov complexity analysis"""
        if verbose:
            print("\n" + "="*70)
            print("STEP 4: KOLMOGOROV COMPLEXITY ANALYSIS")
            print("="*70)

        # Sample trajectories
        if verbose:
            print(f"\nGenerating {num_samples} trajectories...")

        sample_values = np.random.choice(
            range(2, self.max_value + 1),
            size=min(num_samples, self.max_value),
            replace=False
        )

        trajectories = []
        stopping_times = []

        for n in sample_values:
            traj = quick_trajectory(int(n))
            trajectories.append(traj)
            stopping_times.append(len(traj) - 1)

        # Run complexity tests
        test_results = test_low_complexity_theorem(
            trajectories,
            sample_values.tolist(),
            verbose=verbose
        )

        # Analyze complexity vs stopping time
        if verbose:
            print("\nAnalyzing complexity vs stopping time correlation...")

        correlation_results = analyze_complexity_vs_stopping_time(
            trajectories,
            stopping_times
        )

        # Store results
        self.results['complexity_analysis'] = {
            'mean_complexity_ratio': float(test_results['mean_ratio']),
            'std_complexity_ratio': float(test_results['std_ratio']),
            'max_complexity_ratio': float(test_results['max_ratio']),
            'aggregate_metrics': {k: float(v) for k, v in test_results['aggregate_metrics'].items()},
            'theorem_supported': test_results['theorem_supported'],
            'correlations': {k: float(v) if not np.isnan(v) else None
                           for k, v in correlation_results.items()},
        }

        # Plot complexity distributions
        if verbose:
            print("\nGenerating complexity plots...")
        self._plot_complexity_analysis(test_results, correlation_results, stopping_times)

        return test_results

    def _plot_curvature_distribution(self, curvatures: Dict):
        """Plot curvature distribution"""
        curv_values = list(curvatures.values())

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Histogram
        axes[0].hist(curv_values, bins=50, edgecolor='black', alpha=0.7)
        axes[0].axvline(x=0, color='r', linestyle='--', linewidth=2, label='κ = 0')
        axes[0].axvline(x=np.mean(curv_values), color='g', linestyle='--',
                       linewidth=2, label=f'Mean = {np.mean(curv_values):.3f}')
        axes[0].set_xlabel('Ricci Curvature κ', fontsize=12)
        axes[0].set_ylabel('Frequency', fontsize=12)
        axes[0].set_title('Ricci Curvature Distribution', fontsize=14, fontweight='bold')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # CDF
        sorted_curvs = np.sort(curv_values)
        cdf = np.arange(1, len(sorted_curvs) + 1) / len(sorted_curvs)
        axes[1].plot(sorted_curvs, cdf, linewidth=2)
        axes[1].axvline(x=0, color='r', linestyle='--', linewidth=2, label='κ = 0')
        axes[1].set_xlabel('Ricci Curvature κ', fontsize=12)
        axes[1].set_ylabel('CDF', fontsize=12)
        axes[1].set_title('Cumulative Distribution', fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        plot_path = os.path.join(self.results_dir, f'ricci_curvature_{self.timestamp}.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved curvature plots to {plot_path}")

    def _plot_complexity_analysis(self, test_results: Dict, corr_results: Dict,
                                  stopping_times: List[int]):
        """Plot complexity analysis results"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Plot 1: Complexity ratio distribution
        ratios = test_results['complexity_ratios']
        axes[0, 0].hist(ratios, bins=50, edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(x=np.mean(ratios), color='r', linestyle='--',
                          linewidth=2, label=f'Mean = {np.mean(ratios):.3f}')
        axes[0, 0].set_xlabel('K(T_n) / log(log(n))', fontsize=12)
        axes[0, 0].set_ylabel('Frequency', fontsize=12)
        axes[0, 0].set_title('Complexity Ratio Distribution', fontsize=14, fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Plot 2: Aggregate metrics
        metrics = test_results['aggregate_metrics']
        metric_names = list(metrics.keys())
        metric_values = list(metrics.values())

        axes[0, 1].barh(metric_names, metric_values)
        axes[0, 1].set_xlabel('Value', fontsize=12)
        axes[0, 1].set_title('Average Complexity Metrics', fontsize=14, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='x')

        # Plot 3: Complexity vs stopping time (scatter)
        # We need to regenerate this data
        axes[1, 0].scatter(stopping_times[:100], ratios[:100], alpha=0.5)
        axes[1, 0].set_xlabel('Stopping Time', fontsize=12)
        axes[1, 0].set_ylabel('K(T_n) / log(log(n))', fontsize=12)
        axes[1, 0].set_title('Complexity vs Stopping Time', fontsize=14, fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3)

        # Add correlation text
        pearson_corr = corr_results.get('pearson_correlation_K_vs_time', 0)
        axes[1, 0].text(0.05, 0.95, f'Pearson r = {pearson_corr:.3f}',
                       transform=axes[1, 0].transAxes, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # Plot 4: Summary statistics
        summary_text = (
            f"COMPLEXITY ANALYSIS SUMMARY\n\n"
            f"Mean ratio: {test_results['mean_ratio']:.4f}\n"
            f"Std ratio: {test_results['std_ratio']:.4f}\n"
            f"Max ratio: {test_results['max_ratio']:.4f}\n\n"
            f"Avg compressibility: {metrics['avg_compressibility']:.4f}\n"
            f"Avg Shannon entropy: {metrics['avg_shannon_entropy']:.4f}\n"
            f"Avg LZ complexity: {metrics['avg_lz_complexity']:.4f}\n\n"
            f"Theorem supported: {test_results['theorem_supported']}"
        )

        axes[1, 1].text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                       verticalalignment='center')
        axes[1, 1].axis('off')

        plt.tight_layout()

        plot_path = os.path.join(self.results_dir, f'complexity_analysis_{self.timestamp}.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved complexity plots to {plot_path}")

    def save_results(self):
        """Save all results to JSON"""
        output_path = os.path.join(self.results_dir, f'results_{self.timestamp}.json')

        # Custom encoder to handle numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                if isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (np.bool_, bool)):
                    return bool(obj)
                return super().default(obj)

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, cls=NumpyEncoder)

        print(f"\n✓ Saved results to {output_path}")

    def generate_summary_report(self):
        """Generate human-readable summary"""
        print("\n" + "="*70)
        print("FINAL SUMMARY REPORT")
        print("="*70)

        print("\n📊 GRAPH STATISTICS:")
        for key, value in self.results['graph_statistics'].items():
            print(f"  {key}: {value}")

        print("\n🌊 SPECTRAL ANALYSIS:")
        spec = self.results['spectral_analysis']
        print(f"  Spectral gap: {spec['spectral_gap']:.6f}")
        print(f"  Algebraic connectivity: {spec['algebraic_connectivity']:.6f}")
        print(f"  Theorem supported: {spec['theorem_supported']}")

        print("\n📐 RICCI CURVATURE:")
        ricci = self.results['ricci_curvature']
        print(f"  Mean curvature: {ricci['mean_curvature']:.6f}")
        print(f"  Fraction negative: {ricci['fraction_negative']:.2%}")
        print(f"  Hypothesis supported: {ricci['hypothesis_supported']}")

        print("\n🎲 KOLMOGOROV COMPLEXITY:")
        comp = self.results['complexity_analysis']
        print(f"  Mean K/log(log(n)): {comp['mean_complexity_ratio']:.6f}")
        print(f"  Avg compressibility: {comp['aggregate_metrics']['avg_compressibility']:.6f}")
        print(f"  Theorem supported: {comp['theorem_supported']}")

        print("\n" + "="*70)
        print("🔥 OVERALL CONCLUSION:")
        print("="*70)

        # Count how many theorems are supported
        supported = sum([
            spec['theorem_supported'],
            ricci['hypothesis_supported'],
            comp['theorem_supported']
        ])

        print(f"\n{supported}/3 theorems supported by empirical evidence")

        if supported == 3:
            print("\n✅ STRONG EVIDENCE: All three independent approaches support convergence!")
            print("   This suggests deep mathematical structure in Collatz conjecture.")
        elif supported == 2:
            print("\n⚠️  MODERATE EVIDENCE: Two approaches support convergence.")
            print("   Further investigation needed on the third approach.")
        else:
            print("\n❌ WEAK EVIDENCE: Need more analysis or larger dataset.")

        print("\n" + "="*70)


def main():
    """Run complete experimental pipeline"""
    print("="*70)
    print("COLLATZ CONJECTURE: SPECTRAL-GEOMETRIC-COMPLEXITY ANALYSIS")
    print("="*70)

    # Run experiments with moderate size (balance between speed and accuracy)
    experiment = CollatzExperiment(max_value=10000, results_dir='../results')

    # Run all analyses
    experiment.build_graph(verbose=True)
    experiment.run_spectral_analysis(verbose=True)
    experiment.run_ricci_curvature_analysis(verbose=True)
    experiment.run_complexity_analysis(verbose=True, num_samples=500)

    # Save and summarize
    experiment.save_results()
    experiment.generate_summary_report()

    print("\n✅ EXPERIMENT COMPLETE!")
    print(f"Results saved to: {experiment.results_dir}/")


if __name__ == '__main__':
    main()
