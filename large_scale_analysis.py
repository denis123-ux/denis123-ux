"""
Large-scale analysis of Union-Closed Sets Conjecture.

Optimized for analyzing 10,000+ families with comprehensive statistics,
checkpointing, and automatic report generation.
"""

import numpy as np
import json
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from core.family import UnionClosedFamily
from core.generator import generate_test_suite
from core.verifier import ConjectureVerifier
from approaches.quantum.density_matrix import QuantumApproach
from approaches.tensor.mps import TensorNetworkApproach


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


class LargeScaleAnalyzer:
    """
    Optimized analyzer for large-scale experiments.
    """

    def __init__(self, output_dir: str = "results/large_scale"):
        """
        Initialize analyzer.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            'metadata': {
                'start_time': datetime.now().isoformat(),
                'num_families': 0,
                'completed': 0,
                'errors': 0
            },
            'families': [],
            'statistics': {},
            'challenging_cases': [],
            'counterexamples': []
        }

        self.checkpoint_every = 100  # Save every 100 families

    def analyze_family(self, family: UnionClosedFamily, idx: int) -> Dict:
        """
        Analyze a single family with all approaches.

        Args:
            family: Family to analyze
            idx: Index in dataset

        Returns:
            Analysis results
        """
        result = {
            'index': idx,
            'basic': {
                'n': family.n,
                'm': family.m,
                'is_union_closed': family.is_union_closed(),
                'satisfies_conjecture': family.satisfies_conjecture()
            }
        }

        # Skip empty families
        if family.n == 0 or family.m == 0:
            result['skip'] = True
            return result

        try:
            # Basic statistics
            stats = family.statistics()
            result['statistics'] = stats

            # Frequencies
            freqs = family.compute_frequencies()
            result['frequencies'] = {
                'min': stats['min_frequency'],
                'max': stats['max_frequency'],
                'avg': stats['avg_frequency'],
                'all': list(freqs.values())
            }

            # Quantum approach
            try:
                qa = QuantumApproach(family)
                result['quantum'] = {
                    'von_neumann_entropy': qa.von_neumann_entropy(),
                    'purity': qa.purity(),
                    'participation_ratio': qa.participation_ratio(),
                    'quantum_bound': qa.quantum_frequency_bound(),
                    'max_eigenvalue': qa.max_eigenvalue(),
                    'effective_dimension': qa.effective_dimension()
                }
            except Exception as e:
                result['quantum'] = {'error': str(e)}

            # Tensor approach
            try:
                tna = TensorNetworkApproach(family)
                tstats = tna.tensor_statistics()
                result['tensor'] = {
                    'tensor_rank': tstats['tensor_rank'],
                    'avg_entanglement': tstats['avg_entanglement'],
                    'max_entanglement': tstats['max_entanglement'],
                    'max_bond_dimension': tstats['max_bond_dimension'],
                    'avg_bond_dimension': tstats['avg_bond_dimension'],
                    'max_correlation': tstats['max_correlation']
                }
            except Exception as e:
                result['tensor'] = {'error': str(e)}

            # Spectral properties
            try:
                spectral = family.spectral_properties()
                result['spectral'] = spectral
            except Exception as e:
                result['spectral'] = {'error': str(e)}

        except Exception as e:
            result['error'] = str(e)
            return result

        return result

    def run_analysis(self, num_families: int = 10000, max_n: int = 12, seed: int = 42):
        """
        Run large-scale analysis.

        Args:
            num_families: Number of families to analyze
            max_n: Maximum universe size
            seed: Random seed
        """
        print("=" * 80)
        print("LARGE-SCALE ANALYSIS: UNION-CLOSED SETS CONJECTURE")
        print("=" * 80)
        print(f"Target families: {num_families}")
        print(f"Max universe size: {max_n}")
        print(f"Output directory: {self.output_dir}")
        print("=" * 80)
        print()

        self.results['metadata']['num_families'] = num_families
        self.results['metadata']['max_n'] = max_n
        self.results['metadata']['seed'] = seed

        # Generate families in batches
        batch_size = 1000
        num_batches = (num_families + batch_size - 1) // batch_size

        print(f"Generating and analyzing in {num_batches} batches of {batch_size}...")
        print()

        total_start = time.time()
        completed = 0
        errors = 0

        for batch_idx in range(num_batches):
            batch_start = time.time()
            current_batch_size = min(batch_size, num_families - completed)

            print(f"Batch {batch_idx + 1}/{num_batches} ({current_batch_size} families)...")

            # Generate batch
            batch_seed = seed + batch_idx * 1000
            families = generate_test_suite(current_batch_size, max_n, batch_seed)

            # Analyze batch
            for i, family in enumerate(families):
                try:
                    result = self.analyze_family(family, completed + i)
                    self.results['families'].append(result)

                    # Track challenging cases
                    if not result.get('skip', False):
                        max_freq = result['frequencies']['max']
                        if 0.5 <= max_freq <= 0.55 and result['basic']['satisfies_conjecture']:
                            self.results['challenging_cases'].append(result)

                        # Track counterexamples
                        if not result['basic']['satisfies_conjecture']:
                            self.results['counterexamples'].append(result)

                except Exception as e:
                    errors += 1
                    print(f"  Error on family {completed + i}: {e}")

                # Progress indicator
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - batch_start
                    rate = (i + 1) / elapsed
                    print(f"  Progress: {i + 1}/{current_batch_size} ({rate:.1f} families/sec)")

            completed += current_batch_size
            batch_time = time.time() - batch_start

            print(f"  Batch completed in {batch_time:.1f}s")
            print()

            # Checkpoint
            self.save_checkpoint()

        total_time = time.time() - total_start

        self.results['metadata']['completed'] = completed
        self.results['metadata']['errors'] = errors
        self.results['metadata']['total_time'] = total_time
        self.results['metadata']['end_time'] = datetime.now().isoformat()

        print("=" * 80)
        print(f"Analysis complete!")
        print(f"  Total families: {completed}")
        print(f"  Errors: {errors}")
        print(f"  Total time: {total_time:.1f}s ({completed/total_time:.1f} families/sec)")
        print("=" * 80)
        print()

        # Compute aggregate statistics
        self.compute_aggregate_statistics()

        # Save final results
        self.save_results()

        # Generate report
        self.generate_report()

    def compute_aggregate_statistics(self):
        """Compute aggregate statistics across all families."""
        print("Computing aggregate statistics...")

        valid_families = [f for f in self.results['families'] if not f.get('skip', False) and 'error' not in f]

        if not valid_families:
            print("No valid families to analyze!")
            return

        # Basic statistics
        basic_stats = {
            'total_families': len(valid_families),
            'union_closed_count': sum(f['basic']['is_union_closed'] for f in valid_families),
            'satisfies_conjecture_count': sum(f['basic']['satisfies_conjecture'] for f in valid_families),
            'counterexample_count': len(self.results['counterexamples'])
        }

        # Frequency statistics
        max_freqs = [f['frequencies']['max'] for f in valid_families]
        min_freqs = [f['frequencies']['min'] for f in valid_families]

        frequency_stats = {
            'max_frequency': {
                'mean': np.mean(max_freqs),
                'std': np.std(max_freqs),
                'min': np.min(max_freqs),
                'max': np.max(max_freqs),
                'median': np.median(max_freqs),
                'q25': np.percentile(max_freqs, 25),
                'q75': np.percentile(max_freqs, 75)
            },
            'min_frequency': {
                'mean': np.mean(min_freqs),
                'std': np.std(min_freqs),
                'min': np.min(min_freqs),
                'max': np.max(min_freqs),
                'median': np.median(min_freqs)
            }
        }

        # Quantum statistics
        quantum_valid = [f for f in valid_families if 'quantum' in f and 'error' not in f['quantum']]
        if quantum_valid:
            entropies = [f['quantum']['von_neumann_entropy'] for f in quantum_valid]
            purities = [f['quantum']['purity'] for f in quantum_valid]
            bounds = [f['quantum']['quantum_bound'] for f in quantum_valid]

            quantum_stats = {
                'num_valid': len(quantum_valid),
                'von_neumann_entropy': {
                    'mean': np.mean(entropies),
                    'std': np.std(entropies),
                    'min': np.min(entropies),
                    'max': np.max(entropies)
                },
                'purity': {
                    'mean': np.mean(purities),
                    'std': np.std(purities)
                },
                'quantum_bound': {
                    'mean': np.mean(bounds),
                    'std': np.std(bounds),
                    'min': np.min(bounds),
                    'max': np.max(bounds),
                    'above_half_count': sum(b >= 0.5 for b in bounds)
                }
            }
        else:
            quantum_stats = {'num_valid': 0}

        # Tensor statistics
        tensor_valid = [f for f in valid_families if 'tensor' in f and 'error' not in f['tensor']]
        if tensor_valid:
            ranks = [f['tensor']['tensor_rank'] for f in tensor_valid]
            bond_dims = [f['tensor']['max_bond_dimension'] for f in tensor_valid]
            entanglements = [f['tensor']['avg_entanglement'] for f in tensor_valid]

            tensor_stats = {
                'num_valid': len(tensor_valid),
                'tensor_rank': {
                    'mean': np.mean(ranks),
                    'std': np.std(ranks),
                    'max': np.max(ranks)
                },
                'max_bond_dimension': {
                    'mean': np.mean(bond_dims),
                    'std': np.std(bond_dims),
                    'max': np.max(bond_dims)
                },
                'avg_entanglement': {
                    'mean': np.mean(entanglements),
                    'std': np.std(entanglements)
                }
            }
        else:
            tensor_stats = {'num_valid': 0}

        # Correlations
        correlations = self.compute_correlations(valid_families)

        self.results['statistics'] = {
            'basic': basic_stats,
            'frequencies': frequency_stats,
            'quantum': quantum_stats,
            'tensor': tensor_stats,
            'correlations': correlations,
            'challenging_cases_count': len(self.results['challenging_cases'])
        }

        print(f"  Analyzed {len(valid_families)} valid families")
        print(f"  Counterexamples: {basic_stats['counterexample_count']}")
        print(f"  Challenging cases: {len(self.results['challenging_cases'])}")

    def compute_correlations(self, families: List[Dict]) -> Dict:
        """Compute correlations between different measures."""
        # Extract data
        max_freqs = []
        entropies = []
        purities = []
        bond_dims = []

        for f in families:
            max_freqs.append(f['frequencies']['max'])

            if 'quantum' in f and 'error' not in f['quantum']:
                entropies.append(f['quantum']['von_neumann_entropy'])
                purities.append(f['quantum']['purity'])
            else:
                entropies.append(np.nan)
                purities.append(np.nan)

            if 'tensor' in f and 'error' not in f['tensor']:
                bond_dims.append(f['tensor']['max_bond_dimension'])
            else:
                bond_dims.append(np.nan)

        max_freqs = np.array(max_freqs)
        entropies = np.array(entropies)
        purities = np.array(purities)
        bond_dims = np.array(bond_dims)

        # Compute correlations (ignoring NaN)
        correlations = {}

        # Entropy vs max frequency
        mask = ~np.isnan(entropies)
        if mask.sum() > 0:
            correlations['entropy_vs_max_freq'] = float(np.corrcoef(entropies[mask], max_freqs[mask])[0, 1])

        # Purity vs max frequency
        mask = ~np.isnan(purities)
        if mask.sum() > 0:
            correlations['purity_vs_max_freq'] = float(np.corrcoef(purities[mask], max_freqs[mask])[0, 1])

        # Bond dimension vs max frequency
        mask = ~np.isnan(bond_dims)
        if mask.sum() > 0:
            correlations['bond_dim_vs_max_freq'] = float(np.corrcoef(bond_dims[mask], max_freqs[mask])[0, 1])

        return correlations

    def save_checkpoint(self):
        """Save checkpoint."""
        checkpoint_path = self.output_dir / "checkpoint.pkl"
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(self.results, f)

    def save_results(self):
        """Save final results."""
        print("Saving results...")

        # Save full results (pickle)
        results_pkl = self.output_dir / "results_full.pkl"
        with open(results_pkl, 'wb') as f:
            pickle.dump(self.results, f)
        print(f"  Full results: {results_pkl}")

        # Save statistics (JSON)
        stats_json = self.output_dir / "statistics.json"
        with open(stats_json, 'w') as f:
            json.dump(convert_numpy_types(self.results['statistics']), f, indent=2)
        print(f"  Statistics: {stats_json}")

        # Save challenging cases (JSON)
        if self.results['challenging_cases']:
            challenging_json = self.output_dir / "challenging_cases.json"
            # Keep only top 100
            top_challenging = sorted(
                self.results['challenging_cases'],
                key=lambda x: x['frequencies']['max']
            )[:100]
            with open(challenging_json, 'w') as f:
                json.dump(convert_numpy_types(top_challenging), f, indent=2)
            print(f"  Challenging cases: {challenging_json}")

        # Save counterexamples if any
        if self.results['counterexamples']:
            counterexamples_json = self.output_dir / "COUNTEREXAMPLES.json"
            with open(counterexamples_json, 'w') as f:
                json.dump(convert_numpy_types(self.results['counterexamples']), f, indent=2)
            print(f"  ⚠️ COUNTEREXAMPLES: {counterexamples_json}")

    def generate_report(self):
        """Generate human-readable report."""
        report_path = self.output_dir / "REPORT.md"

        stats = self.results['statistics']
        meta = self.results['metadata']

        report = f"""# Large-Scale Analysis Report
## Union-Closed Sets Conjecture

**Generated:** {meta['end_time']}
**Analysis Duration:** {meta['total_time']:.1f} seconds

---

## Dataset Summary

- **Total Families Analyzed:** {meta['completed']}
- **Max Universe Size:** {meta['max_n']}
- **Errors:** {meta['errors']}
- **Analysis Rate:** {meta['completed']/meta['total_time']:.1f} families/second

---

## Basic Statistics

- **Union-Closed Families:** {stats['basic']['union_closed_count']} ({100*stats['basic']['union_closed_count']/stats['basic']['total_families']:.1f}%)
- **Satisfying Conjecture:** {stats['basic']['satisfies_conjecture_count']} ({100*stats['basic']['satisfies_conjecture_count']/stats['basic']['total_families']:.1f}%)
- **Counterexamples Found:** {stats['basic']['counterexample_count']} {'⚠️ ALERT!' if stats['basic']['counterexample_count'] > 0 else '✅'}

---

## Frequency Analysis

### Max Frequency Distribution
- **Mean:** {stats['frequencies']['max_frequency']['mean']:.4f}
- **Std:** {stats['frequencies']['max_frequency']['std']:.4f}
- **Min:** {stats['frequencies']['max_frequency']['min']:.4f}
- **Max:** {stats['frequencies']['max_frequency']['max']:.4f}
- **Median:** {stats['frequencies']['max_frequency']['median']:.4f}
- **Q25-Q75:** [{stats['frequencies']['max_frequency']['q25']:.4f}, {stats['frequencies']['max_frequency']['q75']:.4f}]

### Min Frequency Distribution
- **Mean:** {stats['frequencies']['min_frequency']['mean']:.4f}
- **Std:** {stats['frequencies']['min_frequency']['std']:.4f}
- **Range:** [{stats['frequencies']['min_frequency']['min']:.4f}, {stats['frequencies']['min_frequency']['max']:.4f}]

---

## Quantum Information Analysis

- **Valid Quantum Analyses:** {stats['quantum']['num_valid']}
"""

        if stats['quantum']['num_valid'] > 0:
            report += f"""
### Von Neumann Entropy
- **Mean:** {stats['quantum']['von_neumann_entropy']['mean']:.4f}
- **Std:** {stats['quantum']['von_neumann_entropy']['std']:.4f}
- **Range:** [{stats['quantum']['von_neumann_entropy']['min']:.4f}, {stats['quantum']['von_neumann_entropy']['max']:.4f}]

### Purity
- **Mean:** {stats['quantum']['purity']['mean']:.4f}
- **Std:** {stats['quantum']['purity']['std']:.4f}

### Quantum Bound
- **Mean:** {stats['quantum']['quantum_bound']['mean']:.4f}
- **Std:** {stats['quantum']['quantum_bound']['std']:.4f}
- **Range:** [{stats['quantum']['quantum_bound']['min']:.4f}, {stats['quantum']['quantum_bound']['max']:.4f}]
- **Bounds ≥ 0.5:** {stats['quantum']['quantum_bound']['above_half_count']} ({100*stats['quantum']['quantum_bound']['above_half_count']/stats['quantum']['num_valid']:.1f}%)
"""

        report += f"""
---

## Tensor Network Analysis

- **Valid Tensor Analyses:** {stats['tensor']['num_valid']}
"""

        if stats['tensor']['num_valid'] > 0:
            report += f"""
### Tensor Rank
- **Mean:** {stats['tensor']['tensor_rank']['mean']:.2f}
- **Std:** {stats['tensor']['tensor_rank']['std']:.2f}
- **Max:** {stats['tensor']['tensor_rank']['max']}

### Bond Dimension
- **Mean:** {stats['tensor']['max_bond_dimension']['mean']:.2f}
- **Std:** {stats['tensor']['max_bond_dimension']['std']:.2f}
- **Max:** {stats['tensor']['max_bond_dimension']['max']}

### Entanglement Entropy
- **Mean:** {stats['tensor']['avg_entanglement']['mean']:.4f}
- **Std:** {stats['tensor']['avg_entanglement']['std']:.4f}
"""

        report += f"""
---

## Correlations

"""

        if stats['correlations']:
            for key, value in stats['correlations'].items():
                report += f"- **{key.replace('_', ' ').title()}:** {value:.4f}\n"

        report += f"""
---

## Challenging Cases

- **Total Challenging Cases Found:** {stats['challenging_cases_count']}
- **Definition:** Families with 0.50 ≤ max_frequency ≤ 0.55

Top challenging cases saved to: `challenging_cases.json`

---

## Key Findings

"""

        # Add key findings
        if stats['basic']['counterexample_count'] > 0:
            report += "### ⚠️ COUNTEREXAMPLES FOUND!\n\n"
            report += f"Found {stats['basic']['counterexample_count']} potential counterexamples to the conjecture!\n"
            report += "See `COUNTEREXAMPLES.json` for details.\n\n"
        else:
            report += "### ✅ No Counterexamples\n\n"
            report += "All analyzed families satisfy the conjecture.\n\n"

        if stats['frequencies']['max_frequency']['min'] >= 0.5:
            report += "### ✅ Universal Satisfaction\n\n"
            report += f"ALL families have max_frequency ≥ 0.5 (minimum: {stats['frequencies']['max_frequency']['min']:.4f})\n\n"

        if stats['correlations']:
            report += "### 📊 Correlation Insights\n\n"
            for key, value in stats['correlations'].items():
                if abs(value) > 0.3:
                    strength = "strong" if abs(value) > 0.6 else "moderate"
                    direction = "positive" if value > 0 else "negative"
                    report += f"- **{strength.title()} {direction} correlation** between {key.replace('_', ' ')}: {value:.4f}\n"

        report += f"""
---

## Next Steps

1. **Investigate challenging cases** with max_frequency close to 0.5
2. **Analyze correlations** to derive theoretical bounds
3. **Train GNN** on this dataset for pattern discovery
4. **Formalize insights** into rigorous mathematical statements

---

*Analysis completed successfully.*
"""

        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\n📄 Report generated: {report_path}")


def main():
    """Run large-scale analysis."""
    analyzer = LargeScaleAnalyzer()
    analyzer.run_analysis(num_families=10000, max_n=12, seed=42)


if __name__ == "__main__":
    main()
