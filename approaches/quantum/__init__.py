"""
Quantum Information Theory approach to Union-Closed Sets Conjecture.

Maps union-closed families to quantum density matrices and uses
quantum information measures (von Neumann entropy, purity, fidelity)
to bound element frequencies.
"""

from .density_matrix import QuantumApproach

__all__ = ['QuantumApproach']
