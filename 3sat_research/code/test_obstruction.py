#!/usr/bin/env python3
"""
Test obstruction theory discriminator on small subset.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from obstruction_theory import analyze_obstruction_theory
from sat_tensor_framework import parse_cnf

# Load small subset (10 SAT + 10 UNSAT)
benchmark_dir = Path(__file__).parent.parent / "benchmarks"

print("Loading formulas...")
sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:10]
unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:10]

formulas = []
for f in sat_files:
    formulas.append(parse_cnf(f))
for f in unsat_files:
    formulas.append(parse_cnf(f))

print(f"Loaded {len(formulas)} formulas (10 SAT + 10 UNSAT)\n")

# Run obstruction theory analysis
results = analyze_obstruction_theory(formulas)

print("\n🎯 TEST COMPLETE!")
print("\nBest discriminator:")
best_d = 0
best_metric = None

for metric, stats in results['comparison'].items():
    if abs(stats['cohens_d']) > abs(best_d):
        best_d = stats['cohens_d']
        best_metric = metric

print(f"  {best_metric}: d = {best_d:.4f}")
