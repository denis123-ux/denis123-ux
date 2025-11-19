"""
Master script to run all approaches on union-closed families.

Integrates:
1. Quantum Density Matrix approach
2. Tensor Network approach
3. GNN approach

Generates comprehensive analysis and comparison.
"""

import numpy as np
import json
import argparse
from typing import List, Dict
from tqdm import tqdm

from core.family import UnionClosedFamily
from core.generator import FamilyGenerator, generate_test_suite
from core.verifier import ConjectureVerifier

from approaches.quantum.density_matrix import QuantumApproach
from approaches.tensor.mps import TensorNetworkApproach


def analyze_family_all_approaches(family: UnionClosedFamily) -> Dict:
    """
    Analyze a single family using all approaches.

    Args:
        family: Union-closed family

    Returns:
        Dict with results from all approaches
    """
    results = {
        'family_stats': family.statistics(),
        'is_union_closed': family.is_union_closed(),
        'satisfies_conjecture': family.satisfies_conjecture()
    }

    # Approach 1: Quantum
    try:
        qa = QuantumApproach(family)
        quantum_result = qa.test_conjecture_via_quantum()
        results['quantum'] = quantum_result
    except Exception as e:
        results['quantum'] = {'error': str(e)}

    # Approach 2: Tensor Network
    try:
        tna = TensorNetworkApproach(family)
        tensor_result = tna.test_conjecture_via_tensor()
        results['tensor'] = tensor_result
    except Exception as e:
        results['tensor'] = {'error': str(e)}

    # Approach 3: GNN
    # (Would require loading trained model)
    # Skip for now in batch analysis

    return results


def batch_analysis(num_families: int = 100, max_n: int = 8,
                   seed: int = 42) -> Dict:
    """
    Analyze a batch of families with all approaches.

    Args:
        num_families: Number of families to analyze
        max_n: Maximum universe size
        seed: Random seed

    Returns:
        Aggregated results
    """
    print(f"Generating {num_families} test families...")
    families = generate_test_suite(num_families, max_n, seed)

    print(f"Analyzing with all approaches...")

    all_results = []
    quantum_bounds = []
    tensor_predictions = []
    actual_max_freqs = []

    for family in tqdm(families, desc="Processing families"):
        if family.m == 0 or family.n == 0:
            continue

        result = analyze_family_all_approaches(family)
        all_results.append(result)

        # Collect statistics
        if 'quantum' in result and 'quantum_bound' in result['quantum']:
            quantum_bounds.append(result['quantum']['quantum_bound'])

        if 'tensor' in result and 'actual_max_frequency' in result['tensor']:
            tensor_predictions.append(result['tensor']['tensor_predicts_satisfaction'])

        actual_max_freqs.append(result['family_stats']['max_frequency'])

    # Aggregate statistics
    aggregated = {
        'num_families': len(all_results),
        'num_satisfying_conjecture': sum(r['satisfies_conjecture'] for r in all_results),
        'num_counterexamples': sum(not r['satisfies_conjecture'] for r in all_results),
        'quantum_analysis': {
            'avg_bound': np.mean(quantum_bounds) if quantum_bounds else 0,
            'min_bound': np.min(quantum_bounds) if quantum_bounds else 0,
            'max_bound': np.max(quantum_bounds) if quantum_bounds else 0,
            'num_bounds_above_half': sum(b >= 0.5 for b in quantum_bounds) if quantum_bounds else 0
        },
        'tensor_analysis': {
            'prediction_accuracy': np.mean(tensor_predictions) if tensor_predictions else 0
        },
        'actual_frequencies': {
            'avg_max_freq': np.mean(actual_max_freqs),
            'min_max_freq': np.min(actual_max_freqs),
            'max_max_freq': np.max(actual_max_freqs)
        },
        'detailed_results': all_results[:10]  # First 10 for inspection
    }

    return aggregated


def find_challenging_cases(num_families: int = 1000, max_n: int = 10,
                           num_top: int = 10) -> List[Dict]:
    """
    Find the most challenging families (lowest max frequency while still satisfying).

    Args:
        num_families: Number of families to search
        max_n: Maximum universe size
        num_top: Number of top challenging cases to return

    Returns:
        List of challenging cases
    """
    print(f"Searching for challenging cases among {num_families} families...")

    families = generate_test_suite(num_families, max_n, seed=42)

    challenging = []

    for family in tqdm(families, desc="Searching"):
        if family.m == 0 or family.n == 0:
            continue

        if family.is_union_closed() and family.satisfies_conjecture():
            _, max_freq = family.max_frequency()

            if max_freq < 0.6:  # Close to the boundary
                result = analyze_family_all_approaches(family)
                result['family_dict'] = family.to_dict()
                challenging.append(result)

    # Sort by max frequency (ascending)
    challenging = sorted(challenging, key=lambda x: x['family_stats']['max_frequency'])

    return challenging[:num_top]


def compare_approaches_accuracy(num_families: int = 200) -> Dict:
    """
    Compare accuracy of different approaches in predicting conjecture satisfaction.

    Args:
        num_families: Number of families to test

    Returns:
        Comparison results
    """
    print("Comparing approach accuracies...")

    families = generate_test_suite(num_families, max_n=8, seed=123)

    quantum_correct = 0
    tensor_correct = 0
    total = 0

    for family in tqdm(families, desc="Comparing"):
        if family.m == 0 or family.n == 0:
            continue

        result = analyze_family_all_approaches(family)
        actual = result['satisfies_conjecture']

        # Quantum prediction: bound >= 0.5
        if 'quantum' in result and 'quantum_bound' in result['quantum']:
            quantum_pred = result['quantum']['quantum_bound'] >= 0.5
            if quantum_pred == actual:
                quantum_correct += 1

        # Tensor prediction
        if 'tensor' in result and 'tensor_predicts_satisfaction' in result['tensor']:
            tensor_pred = result['tensor']['tensor_predicts_satisfaction']
            if tensor_pred == actual:
                tensor_correct += 1

        total += 1

    return {
        'total_families': total,
        'quantum_accuracy': quantum_correct / max(total, 1),
        'tensor_accuracy': tensor_correct / max(total, 1)
    }


def main():
    parser = argparse.ArgumentParser(description='Run all approaches on union-closed families')

    parser.add_argument('--mode', type=str, default='batch',
                       choices=['batch', 'challenging', 'compare', 'demo'],
                       help='Analysis mode')
    parser.add_argument('--num-families', type=int, default=100,
                       help='Number of families to analyze')
    parser.add_argument('--max-n', type=int, default=8,
                       help='Maximum universe size')
    parser.add_argument('--output', type=str, default='results/analysis.json',
                       help='Output file')

    args = parser.parse_args()

    print("=" * 70)
    print("UNION-CLOSED SETS CONJECTURE: MULTI-APPROACH ANALYSIS")
    print("=" * 70)
    print()

    if args.mode == 'batch':
        results = batch_analysis(args.num_families, args.max_n)

        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        print(f"Total families analyzed: {results['num_families']}")
        print(f"Satisfying conjecture: {results['num_satisfying_conjecture']}")
        print(f"Counterexamples found: {results['num_counterexamples']}")
        print()
        print("QUANTUM APPROACH:")
        print(f"  Avg quantum bound: {results['quantum_analysis']['avg_bound']:.3f}")
        print(f"  Bounds >= 0.5: {results['quantum_analysis']['num_bounds_above_half']}/{results['num_families']}")
        print()
        print("ACTUAL FREQUENCIES:")
        print(f"  Avg max frequency: {results['actual_frequencies']['avg_max_freq']:.3f}")
        print(f"  Min max frequency: {results['actual_frequencies']['min_max_freq']:.3f}")

        # Save results
        import os
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nFull results saved to {args.output}")

    elif args.mode == 'challenging':
        challenging = find_challenging_cases(args.num_families, args.max_n)

        print("\n" + "=" * 70)
        print(f"TOP {len(challenging)} CHALLENGING CASES")
        print("=" * 70)

        for i, case in enumerate(challenging):
            print(f"\n{i+1}. Max frequency: {case['family_stats']['max_frequency']:.3f}")
            print(f"   Num sets: {case['family_stats']['num_sets']}")
            print(f"   Num elements: {case['family_stats']['num_elements']}")
            if 'quantum' in case and 'quantum_bound' in case['quantum']:
                print(f"   Quantum bound: {case['quantum']['quantum_bound']:.3f}")

        # Save
        import os
        os.makedirs('results', exist_ok=True)
        with open('results/challenging_cases.json', 'w') as f:
            json.dump(challenging, f, indent=2)

    elif args.mode == 'compare':
        comparison = compare_approaches_accuracy(args.num_families)

        print("\n" + "=" * 70)
        print("APPROACH COMPARISON")
        print("=" * 70)
        print(f"Families tested: {comparison['total_families']}")
        print(f"Quantum approach accuracy: {comparison['quantum_accuracy']:.1%}")
        print(f"Tensor approach accuracy: {comparison['tensor_accuracy']:.1%}")

    elif args.mode == 'demo':
        print("Running demonstration on example families...\n")

        # Example 1
        print("Example 1: {{1}, {2}, {1,2}}")
        family1 = UnionClosedFamily([{1}, {2}, {1, 2}])
        result1 = analyze_family_all_approaches(family1)

        print(f"  Satisfies conjecture: {result1['satisfies_conjecture']}")
        print(f"  Max frequency: {result1['family_stats']['max_frequency']:.3f}")
        if 'quantum' in result1:
            print(f"  Quantum bound: {result1['quantum']['quantum_bound']:.3f}")
        if 'tensor' in result1:
            print(f"  Tensor max bond dim: {result1['tensor']['max_bond_dimension']}")
        print()

        # Example 2
        print("Example 2: Random family")
        gen = FamilyGenerator()
        family2 = gen.random_atoms(5, 3, seed=42)
        result2 = analyze_family_all_approaches(family2)

        print(f"  Satisfies conjecture: {result2['satisfies_conjecture']}")
        print(f"  Max frequency: {result2['family_stats']['max_frequency']:.3f}")
        if 'quantum' in result2:
            print(f"  Quantum bound: {result2['quantum']['quantum_bound']:.3f}")
        if 'tensor' in result2:
            print(f"  Tensor max bond dim: {result2['tensor']['max_bond_dimension']}")


if __name__ == "__main__":
    main()
