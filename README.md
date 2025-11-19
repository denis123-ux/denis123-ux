# Union-Closed Sets Conjecture: Computational Attack

**Status**: 🔴 OPEN since 1979 | **Impact**: 🏆🏆🏆🏆🏆

## The Problem (30 seconds)

Given a family F of sets that is **union-closed** (if A,B ∈ F then A∪B ∈ F), does there always exist an element appearing in ≥50% of the sets?

**Example:**
```
F = {{a}, {b}, {a,b}}
Union-closed: ✓ ({a} ∪ {b} = {a,b} ∈ F)
Frequencies: a=67%, b=67%
Conjecture satisfied: ✓
```

## Current State (2025)

- ✅ **Proven for**: large families, large average set size (Gilmer 2024 breakthrough!)
- ❌ **Open for**: general case, sparse families with small sets
- **Gap**: SMALL - we're at 95%, need the final 5%!

## Our Approach: 5 Novel Methods

### 1. **Quantum Density Matrix** (Quantum Information Theory)
Map families to quantum density matrices, use von Neumann entropy and purification theory.

### 2. **Tensor Networks** (Quantum Many-Body Physics)
Represent families as Matrix Product States (MPS), exploit entanglement entropy bounds.

### 3. **GNN + Symbolic Extraction** (AI-Assisted)
Train Graph Neural Networks to predict min frequency, extract symbolic rules via interpretability.

### 4. **Tropical Geometry** (Max-Plus Algebra)
Tropicalize to max-plus algebra, use Newton polygon and convex geometry.

### 5. **Noncommutative Geometry** (Connes Framework)
Construct spectral triple (A,H,D), apply index theorem to bound frequencies.

## Repository Structure

```
.
├── core/                  # Core utilities
│   ├── family.py         # Union-closed family operations
│   ├── generator.py      # Family generators
│   └── verifier.py       # Conjecture verification
├── approaches/
│   ├── quantum/          # Approach #1: Density matrices
│   ├── tensor/           # Approach #2: MPS/PEPS
│   ├── gnn/              # Approach #3: Graph Neural Networks
│   ├── tropical/         # Approach #4: Tropical geometry
│   └── noncomm/          # Approach #5: Noncommutative geometry
├── experiments/          # Experimental notebooks
├── data/                 # Generated test families
└── results/              # Experimental results

```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate test families
python core/generator.py --num-families 10000 --max-size 20

# Run quantum approach
python approaches/quantum/density_matrix.py

# Train GNN
python approaches/gnn/train.py

# Run all approaches
python run_all.py
```

## Key Results

*To be updated as we make progress...*

## References

1. **Frankl's Conjecture** (1979) - Original problem statement
2. **Gilmer's Breakthrough** (2024) - Proof for average size ≥ 0.01n
3. **Quantum Information Theory** - Nielsen & Chuang
4. **Tensor Networks** - Orús, Vidal, Verstraete
5. **Tropical Geometry** - Mikhalkin, Sturmfels
6. **Noncommutative Geometry** - Alain Connes

---

**Goal**: Settle a 46-year-old conjecture using modern computational and theoretical techniques! 🚀
