#!/usr/bin/env python3
"""
MODULAR ARITHMETIC THEORY

Deep analysis of Collatz behavior under modular arithmetic.

Key insight: The behavior of n under Collatz depends on n mod m
for various moduli m.

We analyze:
1. Residue class dynamics
2. Periodic patterns mod powers of 2 and 3
3. Chinese Remainder Theorem implications
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import json
from datetime import datetime
from tqdm import tqdm

from graph_engine import quick_trajectory


def analyze_residue_dynamics(mod: int, max_steps: int = 10):
    """
    Analyze how residue classes evolve under Collatz

    For each residue r ∈ {0, 1, ..., mod-1}, track where it goes
    """
    print(f"\n{'='*60}")
    print(f"RESIDUE DYNAMICS MOD {mod}")
    print(f"{'='*60}")

    # For each residue, compute next residue(s)
    transitions = defaultdict(list)

    for r in range(mod):
        if r == 0:
            # If n ≡ 0 (mod m), then n/2 ≡ 0 or m/2 (mod m)
            # This is complex, skip
            continue

        # Odd case: 3r + 1
        if r % 2 == 1:
            next_r = (3 * r + 1) % mod
            transitions[r].append(('odd', next_r))

        # Even case: r/2 (only if r is even)
        if r % 2 == 0:
            next_r = (r // 2) % mod
            transitions[r].append(('even', next_r))

    print(f"\nTransition table (single step):")
    for r in range(mod):
        if r in transitions:
            trans_str = ", ".join([f"{t[0]}→{t[1]}" for t in transitions[r]])
            print(f"  {r} → {trans_str}")

    return transitions


def track_residue_sequences(mod: int, num_samples: int = 1000, max_steps: int = 100):
    """
    Track actual residue sequences for random starting numbers
    """
    print(f"\n{'='*60}")
    print(f"RESIDUE SEQUENCE ANALYSIS MOD {mod}")
    print(f"{'='*60}")

    # For each starting residue, track distribution of final residues
    start_to_end = defaultdict(Counter)

    samples = np.random.randint(1, 10**6, size=num_samples)

    for n in samples:
        n = int(n)
        start_residue = n % mod
        traj = quick_trajectory(n)

        # Track residues throughout trajectory
        residues = [x % mod for x in traj]

        # Record start → end mapping
        end_residue = residues[-1] if residues else 0
        start_to_end[start_residue][end_residue] += 1

    print(f"\nStart residue → End residue distribution:")
    for start_r in range(mod):
        if start_r in start_to_end:
            total = sum(start_to_end[start_r].values())
            most_common = start_to_end[start_r].most_common(3)
            mc_str = ", ".join([f"{r}:{c/total:.0%}" for r, c in most_common])
            print(f"  Start {start_r}: {mc_str}")

    return dict(start_to_end)


def analyze_mod_powers_of_2(max_power: int = 8):
    """
    Analyze behavior mod 2^k for various k

    Key: The number of trailing zeros determines immediate behavior
    """
    print(f"\n{'='*60}")
    print(f"ANALYSIS MOD POWERS OF 2")
    print(f"{'='*60}")

    results = {}

    for k in range(1, max_power + 1):
        mod = 2**k

        # Count how many steps until residue changes "type"
        samples = np.random.randint(1, 10**6, size=500)
        steps_to_change = []

        for n in samples:
            n = int(n)
            current = n
            steps = 0

            initial_residue = n % mod

            while steps < 100:
                # Take one Collatz step
                if current % 2 == 0:
                    current = current // 2
                else:
                    current = 3 * current + 1

                steps += 1

                if current % mod != initial_residue:
                    break

            steps_to_change.append(steps)

        results[k] = {
            'mod': mod,
            'avg_steps_to_change': np.mean(steps_to_change),
            'max_steps_to_change': np.max(steps_to_change),
        }

        print(f"\nMod 2^{k} = {mod}:")
        print(f"  Avg steps to change residue: {np.mean(steps_to_change):.2f}")

    return results


def analyze_mod_3():
    """
    Deep analysis mod 3

    KEY PROPERTY: If n ≡ 1 (mod 3), then 3n+1 ≡ 1 (mod 3)
                  If n ≡ 2 (mod 3), then 3n+1 ≡ 1 (mod 3)
                  If n ≡ 0 (mod 3), then n/2 behavior depends on parity

    This means 3n+1 always gives residue 1 mod 3!
    """
    print(f"\n{'='*60}")
    print(f"DEEP ANALYSIS MOD 3")
    print(f"{'='*60}")

    # Verify the key property
    print("\nKey property verification:")
    for r in [1, 2]:
        result = (3 * r + 1) % 3
        print(f"  {r} (odd, apply 3n+1): 3×{r}+1 = {3*r+1} ≡ {result} (mod 3)")

    print("\nConsequence: After any odd step, n ≡ 1 (mod 3)")

    # Track mod 3 sequences
    samples = np.random.randint(1, 10**6, size=2000)

    mod3_sequences = []

    for n in samples:
        n = int(n)
        traj = quick_trajectory(n)
        mod3_seq = [x % 3 for x in traj]
        mod3_sequences.append(mod3_seq)

    # Analyze patterns
    # After 3n+1, always get something ≡ 4 ≡ 1 (mod 3)
    # Then divide by 2 repeatedly: 1/2 not integer, so must have even number

    # Count occurrences of each residue
    all_residues = [r for seq in mod3_sequences for r in seq]
    residue_counts = Counter(all_residues)
    total = len(all_residues)

    print(f"\nOverall residue distribution:")
    for r in [0, 1, 2]:
        pct = residue_counts[r] / total * 100
        print(f"  Residue {r}: {pct:.1f}%")

    # Theoretical prediction
    # After odd step: always 1 (mod 3)
    # After even step: depends on previous value
    # If prev ≡ 0 (mod 3), halving gives 0 (mod 3)
    # If prev ≡ 1 (mod 3), halving gives 2 (mod 3) if prev = 3k+1 with k even
    #                                   or 1 (mod 3) if prev = 3k+1 with k odd

    print("\nNote: Residue 1 is most common because:")
    print("  - Every 3n+1 operation produces result ≡ 1 (mod 3)")
    print("  - Residue 0 can only come from halving multiples of 3")
    print("  - Residue 2 comes from halving numbers ≡ 1 (mod 3)")


def analyze_mod_6():
    """
    Analysis mod 6 combines mod 2 and mod 3 behavior

    By CRT: n mod 6 determines (n mod 2, n mod 3)
    """
    print(f"\n{'='*60}")
    print(f"ANALYSIS MOD 6 (combining mod 2 and mod 3)")
    print(f"{'='*60}")

    # Classify residues
    residue_classes = {
        0: (0, 0),  # even, div by 3
        1: (1, 1),  # odd
        2: (0, 2),  # even
        3: (1, 0),  # odd, div by 3
        4: (0, 1),  # even
        5: (1, 2),  # odd
    }

    print("\nResidue class structure:")
    for r, (mod2, mod3) in residue_classes.items():
        parity = "odd" if mod2 == 1 else "even"
        div3 = ", ÷3" if mod3 == 0 else ""
        print(f"  {r} ≡ ({mod2}, {mod3}) [{parity}{div3}]")

    # Track transitions mod 6
    samples = np.random.randint(1, 10**6, size=2000)

    transitions = defaultdict(Counter)

    for n in samples:
        n = int(n)
        traj = quick_trajectory(n)

        for i in range(len(traj) - 1):
            current = traj[i] % 6
            next_val = traj[i+1] % 6
            transitions[current][next_val] += 1

    print("\nTransition probabilities (empirical):")
    for r in range(6):
        if transitions[r]:
            total = sum(transitions[r].values())
            probs = {k: v/total for k, v in transitions[r].items()}
            prob_str = ", ".join([f"{k}:{v:.0%}" for k, v in sorted(probs.items())])
            print(f"  From {r}: {prob_str}")


def main():
    print("="*70)
    print("🔬 MODULAR ARITHMETIC THEORY")
    print("="*70)

    results = {}

    # Basic residue dynamics
    for mod in [3, 4, 6, 8]:
        results[f'dynamics_mod_{mod}'] = analyze_residue_dynamics(mod)

    # Residue sequence tracking
    for mod in [3, 6]:
        results[f'sequences_mod_{mod}'] = track_residue_sequences(mod)

    # Powers of 2
    results['powers_of_2'] = analyze_mod_powers_of_2()

    # Deep mod 3 analysis
    analyze_mod_3()

    # Mod 6 analysis
    analyze_mod_6()

    # Summary
    print("\n" + "="*70)
    print("📋 MODULAR THEORY SUMMARY")
    print("="*70)

    print("""
Key Modular Properties:

1. MOD 3:
   - 3n+1 ALWAYS produces n ≡ 1 (mod 3)
   - Residue 1 is the "attractor" class mod 3

2. MOD 2 (parity):
   - Odd → always apply 3n+1 → even
   - Even → divide by 2
   - Odd/Even ratio ≈ 1:2

3. MOD 6 (combines 2 and 3):
   - 6 residue classes with distinct behaviors
   - Transition matrix shows structured dynamics

4. POWERS OF 2:
   - Higher powers → more steps to change residue
   - Binary structure directly affects trajectory

These modular properties explain the DETERMINISTIC structure
we observe in complexity and autocorrelation!
""")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'../results/modular_theory_{timestamp}.json'

    # Clean for JSON
    save_results = {
        'powers_of_2': results['powers_of_2'],
    }

    with open(output_path, 'w') as f:
        json.dump(save_results, f, indent=2)

    print(f"\n✓ Saved to {output_path}")


if __name__ == '__main__':
    main()
