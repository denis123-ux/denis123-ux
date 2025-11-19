"""
Graph Neural Network approach with symbolic rule extraction.

Train GNN to predict element frequencies, then use interpretability
techniques to extract symbolic mathematical rules.
"""

from .model import UnionClosedGNN
from .dataset import UnionClosedDataset
from .train import train_gnn
from .interpret import extract_symbolic_rules

__all__ = ['UnionClosedGNN', 'UnionClosedDataset', 'train_gnn', 'extract_symbolic_rules']
