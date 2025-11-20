#!/usr/bin/env python3
"""
Test advanced correlation analysis on moderate subset.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from correlation_advanced import analyze_advanced_correlation
from sat_tensor_framework import parse_cnf

# Load 50 formulas (25 SAT + 25 UNSAT)
benchmark_dir = Path(__file__).parent.parent / "benchmarks"

print("Loading formulas...")
sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:25]
unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:25]

formulas = []
for f in sat_files:
    formulas.append(parse_cnf(f))
for f in unsat_files:
    formulas.append(parse_cnf(f))

print(f"Loaded {len(formulas)} formulas (25 SAT + 25 UNSAT)")
print()

# Run advanced analysis
results = analyze_advanced_correlation(formulas)

# Find best discriminator
print("\n🎯 BEST DISCRIMINATOR:")
best_d = 0
best_metric = None

for metric, stats in results['comparison'].items():
    if abs(stats['cohens_d']) > abs(best_d):
        best_d = stats['cohens_d']
        best_metric = metric

print(f"  {best_metric}: d = {best_d:.4f}")
print()
