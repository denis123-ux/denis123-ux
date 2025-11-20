#!/usr/bin/env python3
"""
Quick subset analysis: 100 SAT + 100 UNSAT = 200 instances
Fast, robust, and enough for meaningful Cohen's d
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from run_full_analysis import run_full_analysis
from pathlib import Path

if __name__ == "__main__":
    # Run with max_instances=100 (100 SAT + 100 UNSAT = 200 total)
    print("="*80)
    print("🚀 SUBSET ANALYSIS: 100 SAT + 100 UNSAT = 200 instances")
    print("="*80)
    print("ETA: ~10 minutes (vs 90 min for full 2000)")
    print("Goal: Get robust Cohen's d + test hybrid discriminator")
    print("="*80)
    print()

    benchmark_dir = Path(__file__).parent.parent / "benchmarks"
    run_full_analysis(benchmark_dir, max_instances=100)
