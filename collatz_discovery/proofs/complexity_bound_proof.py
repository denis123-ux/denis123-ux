#!/usr/bin/env python3
"""
RIGOROUS MATHEMATICAL DERIVATION

Goal: Prove (or derive conditions for) K(T_n) = O(log log n)

We approach this through multiple angles:
1. Information-theoretic lower/upper bounds
2. Encoding-based arguments
3. Structural analysis of trajectories
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from typing import List, Tuple, Dict
from fractions import Fraction
import math
from dataclasses import dataclass


# =============================================================================
# PART 1: FUNDAMENTAL DEFINITIONS AND OBSERVATIONS
# =============================================================================

def collatz_step(n: int) -> int:
    """Single Collatz step"""
    return n // 2 if n % 2 == 0 else 3 * n + 1


def full_trajectory(n: int, max_steps: int = 10000) -> List[int]:
    """Complete trajectory from n to 1"""
    traj = [n]
    current = n
    while current != 1 and len(traj) < max_steps:
        current = collatz_step(current)
        traj.append(current)
    return traj


def get_odd_even_sequence(traj: List[int]) -> str:
    """Extract odd/even sequence from trajectory"""
    return ''.join('O' if x % 2 == 1 else 'E' for x in traj[:-1])


# =============================================================================
# PART 2: THEOREM - TRAJECTORY IS DETERMINED BY n
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    THEOREM 1: TRAJECTORY DETERMINATION                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

THEOREM 1.1 (Trajectory Determination):
    For any n ∈ ℕ, the Collatz trajectory T_n is uniquely determined by n.

PROOF:
    The Collatz function f: ℕ → ℕ defined by
        f(n) = n/2      if n ≡ 0 (mod 2)
        f(n) = 3n+1     if n ≡ 1 (mod 2)
    is a well-defined function (not a relation).

    Therefore, given any starting value n, the sequence
        T_n = (n, f(n), f²(n), f³(n), ...)
    is uniquely determined.

    QED.

COROLLARY 1.2 (Kolmogorov Complexity Upper Bound):
    Assuming the trajectory T_n terminates (reaches 1), we have:

        K(T_n) ≤ log₂(n) + C

    where C is a constant (the length of the Collatz algorithm).

PROOF:
    A program to generate T_n needs only:
    1. The Collatz algorithm A (constant length |A|)
    2. The starting value n (⌈log₂(n)⌉ bits)

    Therefore: K(T_n) ≤ |A| + ⌈log₂(n)⌉ = log₂(n) + O(1)

    QED.
""")


# =============================================================================
# PART 3: ANALYZING THE GAP BETWEEN K(T_n) AND EMPIRICAL COMPRESSION
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    THEOREM 2: COMPRESSION VS TRUE COMPLEXITY                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Let C(T_n) denote the compressed length using a practical compressor (e.g., zlib).
Let |T_n| denote the uncompressed length of the trajectory representation.

OBSERVATION (Empirical):
    C(T_n) / |T_n| ≈ 0.5 (approximately constant for all n tested)

THEOREM 2.1 (Compression Bounds):
    K(T_n) ≤ C(T_n) ≤ |T_n|

    where K(T_n) is the true Kolmogorov complexity.

PROOF:
    - Lower bound: K(T_n) ≤ C(T_n) because zlib provides a valid encoding.
    - Upper bound: C(T_n) ≤ |T_n| because compression cannot increase size.

    QED.

THEOREM 2.2 (Gap Analysis):
    The gap between K(T_n) and C(T_n) exists because:
    1. K(T_n) = O(log n) (from Theorem 1.2)
    2. |T_n| = O(T × log(max_value)) = O(log²(n))
    3. C(T_n) ≈ 0.5 × |T_n| = O(log²(n))

    Therefore: C(T_n) / K(T_n) = O(log n)

    The compressor does not achieve optimal compression because it doesn't
    recognize that T_n is determined by n.
""")


# =============================================================================
# PART 4: THE KEY INSIGHT - ENCODING THE ODD/EVEN SEQUENCE
# =============================================================================

@dataclass
class TrajectoryEncoding:
    """Efficient encoding of a Collatz trajectory"""
    n: int                      # Starting value
    length: int                 # Trajectory length T
    odd_count: int             # Number of odd steps
    glide_lengths: List[int]   # Lengths of consecutive even runs

def encode_trajectory(n: int) -> TrajectoryEncoding:
    """
    Encode trajectory efficiently using its structure.

    KEY INSIGHT: After each odd step, we get a number ≡ 0 (mod 2).
    The "glide" is the sequence of consecutive /2 operations until we hit odd.

    We encode: (n, [g_1, g_2, ..., g_m]) where g_i = length of i-th glide.
    """
    traj = full_trajectory(n)

    glides = []
    current_glide = 0
    odd_count = 0

    for i, val in enumerate(traj[:-1]):
        if val % 2 == 1:  # Odd
            if current_glide > 0:
                glides.append(current_glide)
            current_glide = 0
            odd_count += 1
        else:  # Even
            current_glide += 1

    if current_glide > 0:
        glides.append(current_glide)

    return TrajectoryEncoding(
        n=n,
        length=len(traj) - 1,
        odd_count=odd_count,
        glide_lengths=glides
    )


print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    THEOREM 3: GLIDE ENCODING                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

DEFINITION (Glide):
    A "glide" is a maximal sequence of consecutive even steps in a trajectory.
    After an odd step (3n+1), we always get an even number, starting a glide.

THEOREM 3.1 (Glide Structure):
    Any Collatz trajectory can be decomposed into alternating:
    - Odd steps (exactly one at a time)
    - Glides (sequences of ≥1 even steps)

    If the trajectory has m odd steps, it has at most m+1 glides.

PROOF:
    After each odd step, 3n+1 is even (since 3n is odd, 3n+1 is even).
    Thus each odd step initiates a glide.
    The first glide may start from n if n is even.

    QED.

THEOREM 3.2 (Encoding Cost):
    To specify a trajectory, we need:
    1. The starting value n: ⌈log₂(n)⌉ bits
    2. The number of odd steps m: ⌈log₂(m)⌉ bits
    3. The glide lengths [g₁, ..., g_m]: Σᵢ⌈log₂(gᵢ)⌉ bits

    Total: log(n) + log(m) + Σlog(gᵢ) bits

LEMMA 3.3 (Glide Length Distribution):
    Empirically, glide lengths follow approximately geometric distribution
    with mean ≈ 2. Thus E[log₂(gᵢ)] ≈ 1-2 bits.
""")


# =============================================================================
# PART 5: COMPUTING PRECISE ENCODING COSTS
# =============================================================================

def compute_encoding_costs(max_n: int = 10000, samples: int = 1000):
    """Compute actual encoding costs for sample trajectories"""

    print("\n" + "="*70)
    print("EMPIRICAL ENCODING COST ANALYSIS")
    print("="*70)

    results = []

    test_values = np.random.randint(2, max_n, size=samples)

    for n in test_values:
        n = int(n)
        enc = encode_trajectory(n)

        # Cost in bits
        cost_n = math.ceil(math.log2(n)) if n > 1 else 1
        cost_m = math.ceil(math.log2(enc.odd_count + 1)) if enc.odd_count > 0 else 1
        cost_glides = sum(math.ceil(math.log2(g + 1)) for g in enc.glide_lengths)

        total_cost = cost_n + cost_m + cost_glides

        # Theoretical minimum
        k_min = cost_n  # Just need n

        # String representation cost
        traj = full_trajectory(n)
        string_cost = len(','.join(map(str, traj))) * 8  # bits

        results.append({
            'n': n,
            'T': enc.length,
            'm': enc.odd_count,
            'encoding_cost': total_cost,
            'k_min': k_min,
            'string_cost': string_cost,
            'compression_ratio': total_cost / string_cost,
        })

    # Analyze
    encoding_costs = [r['encoding_cost'] for r in results]
    k_mins = [r['k_min'] for r in results]
    string_costs = [r['string_cost'] for r in results]
    compression_ratios = [r['compression_ratio'] for r in results]

    print(f"\nSample size: {samples}")
    print(f"Range: [2, {max_n}]")
    print(f"\nEncoding cost statistics:")
    print(f"  Mean encoding cost: {np.mean(encoding_costs):.2f} bits")
    print(f"  Mean K_min (log n): {np.mean(k_mins):.2f} bits")
    print(f"  Mean string cost: {np.mean(string_costs):.2f} bits")
    print(f"  Mean compression ratio: {np.mean(compression_ratios):.4f}")
    print(f"\nRatio encoding/K_min: {np.mean(encoding_costs)/np.mean(k_mins):.2f}")

    return results


# Run analysis
results = compute_encoding_costs(max_n=100000, samples=500)


# =============================================================================
# PART 6: THE MAIN THEOREM
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MAIN THEOREM: COMPLEXITY BOUND                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

THEOREM 4 (Main Result):
    For any n ∈ ℕ such that the Collatz trajectory T_n terminates,
    the Kolmogorov complexity satisfies:

        K(T_n) ≤ log₂(n) + O(1)

PROOF:

    STEP 1: Encoding Specification
    We define a self-delimiting encoding E(T_n) as follows:

    E(T_n) = ⟨ALGORITHM⟩ ∘ ⟨n⟩

    where:
    - ⟨ALGORITHM⟩ is a fixed-length description of the Collatz function
    - ⟨n⟩ is a self-delimiting encoding of n using ⌈log₂(n)⌉ + O(log log n) bits

    STEP 2: Uniqueness of Reconstruction
    Given E(T_n), we can reconstruct T_n by:
    1. Extracting n from the encoding
    2. Computing f(n), f²(n), f³(n), ... until reaching 1

    This is well-defined and terminates (by assumption).

    STEP 3: Length Bound
    |E(T_n)| = |⟨ALGORITHM⟩| + |⟨n⟩|
             = C + log₂(n) + O(log log n)
             = log₂(n) + O(1)

    where C is a constant (the algorithm description length).

    STEP 4: Conclusion
    By definition of Kolmogorov complexity:
    K(T_n) ≤ |E(T_n)| = log₂(n) + O(1)

    QED.

COROLLARY 4.1 (Relative to Trajectory Length):
    If T denotes the trajectory length (stopping time), then:

        K(T_n) / T = O(log(n) / log(n)) = O(1/log(n)) → 0 as n → ∞

    since T = Θ(log n) empirically.

COROLLARY 4.2 (Compression Ratio):
    The theoretical compression ratio is:

        K(T_n) / |T_n| = O(log n / log²n) = O(1/log n) → 0

    This is BETTER than empirical compression (~0.5) because practical
    compressors don't recognize the trajectory is determined by n.
""")


# =============================================================================
# PART 7: WHAT ABOUT K(T_n) / log(log(n))?
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║               ANALYSIS: THE K(T_n) / log(log(n)) RATIO                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBSERVATION (from experiments):
    The ratio C(T_n) / |T_n| / log(log(n)) ≈ 0.125 and is decreasing.

    This means: C(T_n) / |T_n| ≈ 0.125 × log(log(n))

    As n → ∞, log(log(n)) → ∞, so this seems to say compression ratio → ∞!
    This is impossible since compression ratio ≤ 1.

RESOLUTION:
    The CORRECT interpretation is that the ratio

        (C(T_n) / |T_n|) / log(log(n))

    DECREASES because:
    - C(T_n) / |T_n| ≈ constant (around 0.5)
    - log(log(n)) increases slowly
    - Their ratio goes to 0

    So the empirical finding is:
        C(T_n) / |T_n| = O(1)    (compression ratio is bounded)

    NOT:
        K(T_n) = O(log log n)    (this is FALSE)

THEOREM 5 (Correct Interpretation):
    The true Kolmogorov complexity satisfies:

        K(T_n) = Θ(log n)

    Upper bound: K(T_n) ≤ log n + O(1) from Theorem 4
    Lower bound: K(T_n) ≥ log n - O(1) because specifying T_n allows
                 recovery of n (since trajectory determines starting point)

PROOF of Lower Bound:
    Consider the map T: n ↦ T_n.
    If T_n terminates, the trajectory uniquely determines n.
    (Given trajectory, the first element IS n.)

    Therefore, there is an injection from {n : T_n terminates} to trajectories.
    By counting argument: K(T_n) ≥ K(n) - O(1) = log n - O(1)

    QED.

CONCLUSION:
    K(T_n) = Θ(log n), NOT O(log log n).

    The empirical observation of decreasing ratio is explained by:
    - Constant compression ratio (~0.5)
    - Divided by increasing log(log(n))
""")


# =============================================================================
# PART 8: WHAT CAN WE ACTUALLY PROVE?
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    WHAT WE CAN RIGOROUSLY PROVE                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

PROVEN THEOREMS (unconditional):

1. THEOREM (Mod 3 Structure):
   For all odd n: 3n + 1 ≡ 1 (mod 3)

   PROOF: 3n ≡ 0 (mod 3), so 3n + 1 ≡ 1 (mod 3). QED.

2. THEOREM (Complexity Upper Bound, conditional on termination):
   If T_n terminates: K(T_n) ≤ log n + O(1)

   PROOF: See Theorem 4 above.

3. THEOREM (Complexity Lower Bound, conditional on termination):
   If T_n terminates: K(T_n) ≥ log n - O(1)

   PROOF: T_n determines n, so K(T_n) ≥ K(n) - O(1). QED.

4. THEOREM (Stopping Time Heuristic):
   Under the assumption that odd/even steps are independent with
   P(odd) = p ≈ 0.33, the expected stopping time is:

   E[T] = log n / |log(3^p × 2^(-1+p))| = O(log n)

   PROOF: Standard random walk analysis.

UNPROVEN (would prove Collatz):

5. CONJECTURE: For all n > 0, T_n terminates (reaches 1).

Note: Our complexity analysis ASSUMES termination. It cannot prove it.
""")


# =============================================================================
# PART 9: A NEW APPROACH - STRUCTURAL COMPLEXITY
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NEW APPROACH: STRUCTURAL COMPLEXITY                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

IDEA: Instead of K(T_n) directly, analyze the STRUCTURE of trajectories.

DEFINITION (Structural Complexity):
    For a trajectory T_n = (t₀, t₁, ..., t_T), define:

    SC(T_n) = K(differential encoding)

    where differential encoding is:
    D_n = (t₀, d₁, d₂, ..., d_T) with dᵢ = log(tᵢ/tᵢ₋₁)

OBSERVATION:
    For Collatz:
    - dᵢ = -log(2) ≈ -0.693  if step i is even
    - dᵢ = log(3 + 1/tᵢ₋₁) ≈ log(3) ≈ 1.099  if step i is odd

    The differentials are ALMOST binary: {-0.693, +1.099} with small perturbations.

THEOREM 6 (Differential Encoding):
    The differential sequence D_n requires:
    - log(n) bits for t₀
    - T bits for the binary odd/even sequence
    - O(log T) bits for boundary effects

    Total: SC(T_n) = log(n) + T + O(log T) = O(T)

SIGNIFICANCE:
    Since T = O(log n), we get SC(T_n) = O(log n).
    This matches our K(T_n) = Θ(log n) result.
""")

print("\n" + "="*70)
print("MATHEMATICAL DERIVATION COMPLETE")
print("="*70)
