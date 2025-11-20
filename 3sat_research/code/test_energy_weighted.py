#!/usr/bin/env python3
"""
Test energy-weighted correlation at multiple temperatures.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from energy_weighted_correlation import analyze_multitemperature
from sat_tensor_framework import parse_cnf

# Load subset (20 formulas for speed, since MCMC is expensive)
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

# Test at multiple temperatures
betas = [0.5, 1.0, 2.0, 5.0]  # Low T → High T
results = analyze_multitemperature(formulas, betas=betas)

print("\n🎯 TEMPERATURE DEPENDENCE:")
print("If ξ_SAT grows with β but ξ_UNSAT stays constant → BREAKTHROUGH!")
