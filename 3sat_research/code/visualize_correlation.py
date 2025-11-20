#!/usr/bin/env python3
"""
Visualize correlation functions to understand what's happening.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import matplotlib.pyplot as plt
from correlation_length import CorrelationLengthDiscriminator
from sat_tensor_framework import parse_cnf

# Load one SAT and one UNSAT
benchmark_dir = Path(__file__).parent.parent / "benchmarks"

sat_file = sorted(list(benchmark_dir.glob("uf50-*.cnf")))[0]
unsat_file = sorted(list((benchmark_dir / "UUF50.218.1000").glob("*.cnf")))[0]

sat_formula = parse_cnf(sat_file)
unsat_formula = parse_cnf(unsat_file)

print("="*80)
print("📊 VISUALIZING CORRELATION FUNCTIONS")
print("="*80)
print(f"SAT: {sat_file.name}")
print(f"UNSAT: {unsat_file.name}")
print()

# Compute for SAT
print("Computing SAT correlation function...")
disc_sat = CorrelationLengthDiscriminator(sat_formula, n_samples=5000, max_distance=25)
result_sat = disc_sat.compute()

# Compute for UNSAT
print("Computing UNSAT correlation function...")
disc_unsat = CorrelationLengthDiscriminator(unsat_formula, n_samples=5000, max_distance=25)
result_unsat = disc_unsat.compute()

print()
print("SAT:")
print(f"  ξ = {result_sat['xi']:.3f}")
print(f"  A = {result_sat['A']:.3f}")
print(f"  Fit quality (R²) = {result_sat['fit_quality']:.3f}")
print(f"  Method: {result_sat['method']}")

print()
print("UNSAT:")
print(f"  ξ = {result_unsat['xi']:.3f}")
print(f"  A = {result_unsat['A']:.3f}")
print(f"  Fit quality (R²) = {result_unsat['fit_quality']:.3f}")
print(f"  Method: {result_unsat['method']}")

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# SAT
d_sat = result_sat['distances']
c_sat = result_sat['correlations']
ax1.plot(d_sat, c_sat, 'o-', color='blue', linewidth=2, markersize=8, label='Data')

# Fit curve
if not np.isnan(result_sat['xi']):
    d_fit = np.linspace(d_sat[0], d_sat[-1], 100)
    c_fit = result_sat['A'] * np.exp(-d_fit / result_sat['xi'])
    ax1.plot(d_fit, c_fit, '--', color='red', linewidth=2,
             label=f'Fit: ξ={result_sat["xi"]:.2f}')

ax1.set_xlabel('Hamming Distance d', fontsize=12, fontweight='bold')
ax1.set_ylabel('Correlation C(d)', fontsize=12, fontweight='bold')
ax1.set_title(f'SAT: {sat_file.name}', fontsize=14, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0, color='k', linestyle='-', linewidth=0.5)

# UNSAT
d_unsat = result_unsat['distances']
c_unsat = result_unsat['correlations']
ax2.plot(d_unsat, c_unsat, 'o-', color='red', linewidth=2, markersize=8, label='Data')

# Fit curve
if not np.isnan(result_unsat['xi']):
    d_fit = np.linspace(d_unsat[0], d_unsat[-1], 100)
    c_fit = result_unsat['A'] * np.exp(-d_fit / result_unsat['xi'])
    ax2.plot(d_fit, c_fit, '--', color='blue', linewidth=2,
             label=f'Fit: ξ={result_unsat["xi"]:.2f}')

ax2.set_xlabel('Hamming Distance d', fontsize=12, fontweight='bold')
ax2.set_ylabel('Correlation C(d)', fontsize=12, fontweight='bold')
ax2.set_title(f'UNSAT: {unsat_file.name}', fontsize=14, fontweight='bold')
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='k', linestyle='-', linewidth=0.5)

plt.tight_layout()
output_path = Path(__file__).parent.parent / "results" / "advanced" / "correlation_functions.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print()
print(f"✓ Plot saved: {output_path}")
print()
