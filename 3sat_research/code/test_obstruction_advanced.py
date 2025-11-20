#!/usr/bin/env python3
"""
Test ADVANCED obstruction theory with integer homology and torsion.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from obstruction_advanced import analyze_advanced_obstruction
from sat_tensor_framework import parse_cnf

# Load moderate subset (20 formulas for thorough test)
benchmark_dir = Path(__file__).parent.parent / "benchmarks"

print("Loading formulas...")
sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:15]
unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:15]

formulas = []
for f in sat_files:
    formulas.append(parse_cnf(f))
for f in unsat_files:
    formulas.append(parse_cnf(f))

print(f"Loaded {len(formulas)} formulas (15 SAT + 15 UNSAT)\n")

# Run advanced obstruction theory analysis
results = analyze_advanced_obstruction(formulas)

print("\n🎯 ADVANCED TEST COMPLETE!")
print("\nBest discriminator:")
best_d = 0
best_metric = None

for metric, stats in results['comparison'].items():
    if abs(stats['cohens_d']) > abs(best_d):
        best_d = stats['cohens_d']
        best_metric = metric

print(f"  {best_metric}: d = {best_d:.4f}")

# Check if torsion discriminates
sat_results = results['results']['sat']
unsat_results = results['results']['unsat']

print("\nTORSION ANALYSIS:")
print(f"  SAT with torsion: {sum(r['has_torsion'] for r in sat_results)}/{len(sat_results)}")
print(f"  UNSAT with torsion: {sum(r['has_torsion'] for r in unsat_results)}/{len(unsat_results)}")
print(f"  SAT with 2-torsion: {sum(r['has_2_torsion'] for r in sat_results)}/{len(sat_results)}")
print(f"  UNSAT with 2-torsion: {sum(r['has_2_torsion'] for r in unsat_results)}/{len(unsat_results)}")
