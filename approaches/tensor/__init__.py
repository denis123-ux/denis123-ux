"""
Tensor Network approach to Union-Closed Sets Conjecture.

Uses Matrix Product States (MPS) and tensor decompositions to
represent union-closed families and extract structure via
entanglement entropy and bond dimensions.
"""

from .mps import TensorNetworkApproach

__all__ = ['TensorNetworkApproach']
