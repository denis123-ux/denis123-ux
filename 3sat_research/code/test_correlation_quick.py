#!/usr/bin/env python3
"""
Quick validation test for correlation length discriminator.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from correlation_length import CorrelationLengthDiscriminator, analyze_correlation_length
from sat_tensor_framework import parse_cnf

# Load small subset
benchmark_dir = Path(__file__).parent.parent / "benchmarks"

print("Loading formulas...")
sat_files = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[:10]
unsat_files = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[:10]

formulas = []
for f in sat_files:
    formulas.append(parse_cnf(f))
for f in unsat_files:
    formulas.append(parse_cnf(f))

print(f"Loaded {len(formulas)} formulas (10 SAT + 10 UNSAT)")
print()

# Run analysis
results = analyze_correlation_length(formulas, n_samples=2000, max_distance=15)

print("\n🎯 QUICK TEST COMPLETE!")
print(f"ξ_SAT = {results['sat_xi'].mean():.2f} ± {results['sat_xi'].std():.2f}")
print(f"ξ_UNSAT = {results['unsat_xi'].mean():.2f} ± {results['unsat_xi'].std():.2f}")
print(f"Cohen's d = {results['cohens_d']:.4f}")
