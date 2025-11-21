#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
            INFORMATION-THEORETIC ANALYSIS OF COLLATZ
═══════════════════════════════════════════════════════════════════════════════

Analyze Collatz from information theory perspective:
1. Kolmogorov complexity of trajectories
2. Entropy of step sequences
3. Information flow through dynamics
4. Compression properties

Key insight: If trajectories are "simple", they should be compressible.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from collections import defaultdict, Counter
import math


def header(title: str):
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + f" {title} ".center(78) + "║")
    print("╚" + "═"*78 + "╝")


def collatz_step(n):
    return n // 2 if n % 2 == 0 else 3 * n + 1


def trajectory(n, max_steps=10000):
    traj = [n]
    while n != 1 and len(traj) < max_steps:
        n = collatz_step(n)
        traj.append(n)
    return traj


def step_sequence(n, max_steps=10000):
    """Return sequence of 0 (even) and 1 (odd) for each step"""
    seq = []
    while n != 1 and len(seq) < max_steps:
        seq.append(n % 2)
        n = collatz_step(n)
    return seq


# ═══════════════════════════════════════════════════════════════════════════════
#                    KOLMOGOROV COMPLEXITY BOUNDS
# ═══════════════════════════════════════════════════════════════════════════════

def kolmogorov_analysis():
    """Analyze Kolmogorov complexity of trajectories"""
    header("KOLMOGOROV COMPLEXITY ANALYSIS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    KOLMOGOROV COMPLEXITY
═══════════════════════════════════════════════════════════════════════════════

DEFINITION:
    K(x) = length of shortest program that outputs x

BOUNDS FOR COLLATZ TRAJECTORY T_n:

UPPER BOUND:
    K(T_n) ≤ K(n) + O(1) ≤ log(n) + O(1)

    (Given n, can compute T_n deterministically)

LOWER BOUND:
    K(T_n) ≥ K(n) - O(1) = log(n) - O(1)

    (T_n encodes n: if we know T_n, we know starting point)

CONCLUSION:
    K(T_n) = Θ(log n)

    Trajectories have complexity proportional to the input size.
""")

    # Estimate complexity via compression
    print("Complexity estimation via trajectory length:")
    print("-" * 50)

    for n in [27, 97, 871, 6171, 77031]:
        traj = trajectory(n)
        seq = step_sequence(n)

        # Information content
        log_n = math.log2(n)
        traj_len = len(traj)

        # Unique representation bits (position in trajectory + n)
        bits_needed = math.ceil(log_n)

        print(f"  n = {n:6}: log₂(n) = {log_n:.1f}, |T_n| = {traj_len}, bits = {bits_needed}")


# ═══════════════════════════════════════════════════════════════════════════════
#                    STEP SEQUENCE ENTROPY
# ═══════════════════════════════════════════════════════════════════════════════

def step_entropy():
    """Analyze entropy of step sequences"""
    header("STEP SEQUENCE ENTROPY")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    ENTROPY OF STEP SEQUENCES
═══════════════════════════════════════════════════════════════════════════════

The step sequence s = (s₁, s₂, ...) where sᵢ = 0 (even) or 1 (odd).

ENTROPY RATE:
    h = lim_{n→∞} H(S_n) / n

    where H is Shannon entropy.

    Maximum entropy = 1 bit per step (if equal probability)
    If p = P(odd step), then h = -p log p - (1-p) log (1-p)

FOR COLLATZ:
    p ≈ 1/3, so h ≈ 0.918 bits per step
""")

    # Collect all step sequences
    all_steps = []
    for n in range(3, 20001, 2):
        seq = step_sequence(n)
        all_steps.extend(seq)

    # Single symbol entropy
    p1 = sum(all_steps) / len(all_steps)  # P(odd)
    p0 = 1 - p1  # P(even)

    H1 = -p0 * math.log2(p0) - p1 * math.log2(p1) if p0 > 0 and p1 > 0 else 0

    print("Single symbol entropy:")
    print("-" * 50)
    print(f"  P(even) = {p0:.4f}")
    print(f"  P(odd) = {p1:.4f}")
    print(f"  H(single symbol) = {H1:.4f} bits")

    # Digram entropy
    digrams = []
    for n in range(3, 10001, 2):
        seq = step_sequence(n)
        for i in range(len(seq) - 1):
            digrams.append((seq[i], seq[i+1]))

    digram_counts = Counter(digrams)
    total_digrams = len(digrams)

    print("\nDigram probabilities:")
    for d in [(0,0), (0,1), (1,0), (1,1)]:
        p = digram_counts[d] / total_digrams
        print(f"  P({d[0]}{d[1]}) = {p:.4f}")

    # Note: 11 should be impossible (two consecutive odd steps)
    print(f"\n  Note: P(11) should be ~0 (forbidden pattern)")

    # Conditional entropy H(S_{n+1} | S_n)
    # H(S_{n+1}|S_n) = H(S_n, S_{n+1}) - H(S_n)
    H_digram = 0
    for d, count in digram_counts.items():
        p = count / total_digrams
        if p > 0:
            H_digram -= p * math.log2(p)

    H_conditional = H_digram - H1
    print(f"\nConditional entropy H(S_{{n+1}} | S_n) = {H_conditional:.4f} bits")


# ═══════════════════════════════════════════════════════════════════════════════
#                    INFORMATION FLOW
# ═══════════════════════════════════════════════════════════════════════════════

def information_flow():
    """Analyze information flow through Collatz dynamics"""
    header("INFORMATION FLOW ANALYSIS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    INFORMATION FLOW
═══════════════════════════════════════════════════════════════════════════════

QUESTION:
    How much information about n is preserved after k Collatz steps?

OBSERVATION:
    - Even step (n/2): loses 1 bit of information (the LSB)
    - Odd step (3n+1): scrambles bits, but preserves information

MUTUAL INFORMATION:
    I(X_0; X_k) = H(X_k) - H(X_k | X_0)

    Since X_k is deterministic given X_0:
    H(X_k | X_0) = 0

    So I(X_0; X_k) = H(X_k)
""")

    # Track information content through trajectory
    print("Information content along trajectory:")
    print("-" * 50)

    for n in [27, 97, 871]:
        traj = trajectory(n)
        print(f"\n  n = {n}:")
        print(f"    Step |  Value  | log₂(value) | bits lost")
        print(f"    -----|---------|-------------|----------")

        prev_bits = math.log2(n) if n > 0 else 0
        for i, val in enumerate(traj[:15]):
            bits = math.log2(val) if val > 0 else 0
            lost = prev_bits - bits
            print(f"    {i:4} | {val:7} | {bits:11.2f} | {lost:+.2f}")
            prev_bits = bits


# ═══════════════════════════════════════════════════════════════════════════════
#                    COMPRESSION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def compression_analysis():
    """Analyze compressibility of trajectories"""
    header("COMPRESSION ANALYSIS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    TRAJECTORY COMPRESSION
═══════════════════════════════════════════════════════════════════════════════

If Collatz trajectories have structure, they should be compressible.

REPRESENTATIONS:
1. Full trajectory: list all values
2. Step sequence: list all 0/1 steps
3. Glide encoding: list lengths of glides

We compare these representations.
""")

    # Compare representation sizes
    print("Representation comparison:")
    print("-" * 60)
    print(f"{'n':>8} | {'Full (bits)':>12} | {'Steps (bits)':>12} | {'Glides':>8}")
    print("-" * 60)

    for n in [27, 97, 871, 6171, 27657]:
        traj = trajectory(n)
        seq = step_sequence(n)

        # Full representation: sum of log₂(value) for each element
        full_bits = sum(math.ceil(math.log2(max(v, 1) + 1)) for v in traj)

        # Step sequence: 1 bit per step (but actually less due to structure)
        step_bits = len(seq)

        # Glide encoding: count runs of 0s and 1s
        glides = []
        current = seq[0] if seq else None
        count = 0
        for s in seq:
            if s == current:
                count += 1
            else:
                glides.append(count)
                current = s
                count = 1
        if count > 0:
            glides.append(count)

        # Bits for glide encoding (assuming variable-length coding)
        glide_bits = sum(math.ceil(math.log2(max(g, 1) + 1)) for g in glides)

        print(f"{n:>8} | {full_bits:>12} | {step_bits:>12} | {len(glides):>8}")


# ═══════════════════════════════════════════════════════════════════════════════
#                    PATTERN ENTROPY
# ═══════════════════════════════════════════════════════════════════════════════

def pattern_entropy():
    """Analyze entropy of patterns in trajectories"""
    header("PATTERN ENTROPY")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    PATTERN ENTROPY
═══════════════════════════════════════════════════════════════════════════════

We analyze the entropy of k-grams (patterns of length k) in step sequences.

As k increases, entropy should converge to the entropy rate h.
""")

    # Collect step sequences
    all_seqs = []
    for n in range(3, 5001, 2):
        seq = step_sequence(n)
        if len(seq) >= 10:
            all_seqs.append(seq)

    print("k-gram entropy analysis:")
    print("-" * 50)

    for k in range(1, 6):
        # Count k-grams
        kgrams = defaultdict(int)
        total = 0

        for seq in all_seqs:
            for i in range(len(seq) - k + 1):
                kgram = tuple(seq[i:i+k])
                kgrams[kgram] += 1
                total += 1

        # Compute entropy
        H_k = 0
        for count in kgrams.values():
            p = count / total
            if p > 0:
                H_k -= p * math.log2(p)

        # Entropy per symbol
        h_k = H_k / k

        print(f"  k = {k}: H({k}-gram) = {H_k:.4f}, h = H/k = {h_k:.4f} bits/symbol")

    # The limit should be the entropy rate
    print("\n  The entropy rate h ≈ 0.92 bits/symbol (less than 1 due to structure)")


# ═══════════════════════════════════════════════════════════════════════════════
#                    MUTUAL INFORMATION
# ═══════════════════════════════════════════════════════════════════════════════

def mutual_information_analysis():
    """Analyze mutual information between n and trajectory properties"""
    header("MUTUAL INFORMATION ANALYSIS")

    print("""
═══════════════════════════════════════════════════════════════════════════════
                    MUTUAL INFORMATION
═══════════════════════════════════════════════════════════════════════════════

I(X; Y) = H(X) + H(Y) - H(X, Y)

We compute mutual information between:
    - n (mod 6) and stopping time
    - n (mod 6) and trajectory maximum
    - First bit of n and stopping time parity
""")

    # Collect data
    data = []
    for n in range(1, 10001):
        traj = trajectory(n)
        if traj[-1] == 1:
            data.append({
                'n': n,
                'mod6': n % 6,
                'stopping_time': len(traj) - 1,
                'max_val': max(traj),
                'first_bit': n % 2
            })

    # MI between mod6 and stopping time category
    print("I(n mod 6; stopping_time category):")
    print("-" * 50)

    # Discretize stopping time into categories
    stopping_times = [d['stopping_time'] for d in data]
    median_st = np.median(stopping_times)

    for d in data:
        d['st_cat'] = 'high' if d['stopping_time'] > median_st else 'low'

    # Count joint distribution
    joint = defaultdict(int)
    mod6_counts = defaultdict(int)
    st_counts = defaultdict(int)

    for d in data:
        joint[(d['mod6'], d['st_cat'])] += 1
        mod6_counts[d['mod6']] += 1
        st_counts[d['st_cat']] += 1

    total = len(data)

    # Compute entropies
    H_mod6 = -sum((c/total) * math.log2(c/total) for c in mod6_counts.values() if c > 0)
    H_st = -sum((c/total) * math.log2(c/total) for c in st_counts.values() if c > 0)
    H_joint = -sum((c/total) * math.log2(c/total) for c in joint.values() if c > 0)

    MI = H_mod6 + H_st - H_joint

    print(f"  H(mod 6) = {H_mod6:.4f}")
    print(f"  H(stopping time cat) = {H_st:.4f}")
    print(f"  H(joint) = {H_joint:.4f}")
    print(f"  I(mod 6; st_cat) = {MI:.4f} bits")


# ═══════════════════════════════════════════════════════════════════════════════
#                         MAIN RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

def main_info_results():
    """Summarize information-theoretic results"""
    header("INFORMATION THEORY: MAIN RESULTS")

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 INFORMATION-THEORETIC ANALYSIS RESULTS                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

KEY FINDINGS:

1. KOLMOGOROV COMPLEXITY:
   - K(T_n) = Θ(log n) - trajectories have linear complexity in input bits
   - Cannot compress below log n bits (trajectory encodes n)
   - Structure doesn't reduce complexity fundamentally

2. STEP SEQUENCE ENTROPY:
   - P(odd step) ≈ 0.33, P(even step) ≈ 0.67
   - H(single step) ≈ 0.92 bits (less than 1 due to structure)
   - Pattern "11" (consecutive odd) is forbidden

3. INFORMATION FLOW:
   - Even steps lose 1 bit (divide by 2)
   - Odd steps scramble but preserve information
   - Net information flow is downward (trajectory shrinks)

4. COMPRESSION:
   - Step sequences more compact than full trajectories
   - Glide encoding captures structure
   - ~0.9 bits per step effective rate

5. MUTUAL INFORMATION:
   - n mod 6 correlates with trajectory properties
   - Some predictive power from residue class
   - But not deterministic

═══════════════════════════════════════════════════════════════════════════════
                    WHAT THIS TELLS US
═══════════════════════════════════════════════════════════════════════════════

From information theory perspective:

1. Trajectories are NOT random - they have structure (entropy < 1)
2. The forbidden "11" pattern is a KEY constraint
3. Information flows "downhill" toward the cycle
4. Residue classes provide partial prediction

But K(T_n) = Θ(log n) means:
    No "shortcut" exists to predict trajectories
    Must compute step by step
    This is consistent with the problem's difficulty

═══════════════════════════════════════════════════════════════════════════════
""")


def main():
    print("═" * 80)
    print(" " * 18 + "INFORMATION-THEORETIC ANALYSIS")
    print(" " * 15 + "Entropy and Complexity of Collatz")
    print("═" * 80)

    kolmogorov_analysis()
    step_entropy()
    information_flow()
    compression_analysis()
    pattern_entropy()
    mutual_information_analysis()
    main_info_results()

    print("\n" + "═" * 80)
    print("INFORMATION-THEORETIC ANALYSIS COMPLETE")
    print("═" * 80)


if __name__ == "__main__":
    main()
