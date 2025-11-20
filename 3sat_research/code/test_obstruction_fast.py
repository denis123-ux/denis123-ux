#!/usr/bin/env python3
"""
Test FAST obstruction theory on larger dataset.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from obstruction_fast import analyze_fast_obstruction
from sat_tensor_framework import parse_cnf

# Load larger dataset (50 SAT + 50 UNSAT = 100)
benchmark_dir = Path(__file__).parent.parent / "benchmarks"

print("Loading formulas...")
sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:50]
unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:50]

formulas = []
for f in sat_files:
    formulas.append(parse_cnf(f))
for f in unsat_files:
    formulas.append(parse_cnf(f))

print(f"Loaded {len(formulas)} formulas (50 SAT + 50 UNSAT)\n")

# Run fast obstruction theory analysis
results = analyze_fast_obstruction(formulas)

print("\n🎯 FAST ANALYSIS COMPLETE!")
print("\nBest discriminator:")
best_d = 0
best_metric = None

for metric, stats in results['comparison'].items():
    if abs(stats['cohens_d']) > abs(best_d):
        best_d = stats['cohens_d']
        best_metric = metric

print(f"  {best_metric}: d = {best_d:.4f}")

# Summary
print("\n📊 SUMMARY:")
for metric, stats in results['comparison'].items():
    d = stats['cohens_d']
    if abs(d) > 0.5:
        print(f"  {metric}: d={d:.4f}")
