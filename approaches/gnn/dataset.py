"""
Dataset for training GNN on union-closed families.
"""

import torch
from torch_geometric.data import Data, Dataset
import numpy as np
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.family import UnionClosedFamily
from core.generator import generate_test_suite


class UnionClosedDataset(Dataset):
    """
    PyTorch Geometric dataset for union-closed families.

    Each family is converted to a bipartite graph:
    - Set nodes (one per set in family)
    - Element nodes (one per element in universe)
    - Edges: set S connected to element x if x ∈ S
    """

    def __init__(self, families: List[UnionClosedFamily] = None,
                 num_families: int = 1000, max_n: int = 10,
                 seed: int = None):
        """
        Initialize dataset.

        Args:
            families: List of families (if None, generate random)
            num_families: Number of families to generate
            max_n: Maximum universe size
            seed: Random seed
        """
        super().__init__()

        if families is None:
            families = generate_test_suite(num_families, max_n, seed)

        self.families = families
        self.data_list = []

        # Convert each family to graph
        for family in families:
            graph_data = self.family_to_graph(family)
            self.data_list.append(graph_data)

    def len(self):
        return len(self.data_list)

    def get(self, idx):
        return self.data_list[idx]

    @staticmethod
    def family_to_graph(family: UnionClosedFamily) -> Data:
        """
        Convert union-closed family to bipartite graph.

        Graph structure:
        - Nodes 0 to m-1: Set nodes
        - Nodes m to m+n-1: Element nodes
        - Edge (i, m+j) if element j is in set i

        Node features:
        - Set nodes: [set_size, 0] (type indicator)
        - Element nodes: [frequency, 1] (type indicator)

        Returns:
            PyTorch Geometric Data object
        """
        m = family.m
        n = family.n

        if m == 0 or n == 0:
            # Empty graph
            return Data(
                x=torch.zeros((1, 2), dtype=torch.float),
                edge_index=torch.zeros((2, 0), dtype=torch.long),
                y=torch.tensor([0.0], dtype=torch.float),
                num_sets=0,
                num_elements=0
            )

        # Build node features
        node_features = []

        # Set nodes
        sets_list = sorted(family.sets, key=lambda s: (len(s), tuple(sorted(s))))
        for S in sets_list:
            node_features.append([len(S) / max(n, 1), 0.0])  # [normalized size, type=set]

        # Element nodes
        elem_order = sorted(family.universe)
        elem_to_idx = {elem: idx for idx, elem in enumerate(elem_order)}
        freqs = family.compute_frequencies()

        for elem in elem_order:
            node_features.append([freqs.get(elem, 0.0), 1.0])  # [frequency, type=element]

        x = torch.tensor(node_features, dtype=torch.float)

        # Build edges (bipartite: sets to elements)
        edge_list = []
        for set_idx, S in enumerate(sets_list):
            for elem in S:
                elem_idx = elem_to_idx[elem]
                # Edge from set node to element node
                edge_list.append([set_idx, m + elem_idx])
                # Also add reverse edge (undirected)
                edge_list.append([m + elem_idx, set_idx])

        if edge_list:
            edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        else:
            edge_index = torch.zeros((2, 0), dtype=torch.long)

        # Target: min and max frequency
        _, min_freq = family.min_frequency()
        _, max_freq = family.max_frequency()

        y = torch.tensor([min_freq, max_freq], dtype=torch.float)

        # Additional graph-level features
        stats = family.statistics()

        data = Data(
            x=x,
            edge_index=edge_index,
            y=y,
            num_sets=m,
            num_elements=n,
            avg_set_size=stats['avg_set_size'],
            density=stats['density']
        )

        return data


def create_dataloaders(train_size: int = 8000, val_size: int = 1000,
                       test_size: int = 1000, max_n: int = 10,
                       batch_size: int = 32, seed: int = 42):
    """
    Create train/val/test dataloaders.

    Args:
        train_size: Number of training examples
        val_size: Number of validation examples
        test_size: Number of test examples
        max_n: Maximum universe size
        batch_size: Batch size
        seed: Random seed

    Returns:
        (train_loader, val_loader, test_loader)
    """
    from torch_geometric.loader import DataLoader

    # Generate datasets
    np.random.seed(seed)

    train_dataset = UnionClosedDataset(num_families=train_size, max_n=max_n, seed=seed)
    val_dataset = UnionClosedDataset(num_families=val_size, max_n=max_n, seed=seed + 1)
    test_dataset = UnionClosedDataset(num_families=test_size, max_n=max_n, seed=seed + 2)

    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, test_loader


if __name__ == "__main__":
    # Test dataset creation
    print("Creating test dataset...")
    dataset = UnionClosedDataset(num_families=10, max_n=5, seed=42)

    print(f"Dataset size: {len(dataset)}")
    print(f"\nExample data point:")
    data = dataset[0]
    print(f"  Num nodes: {data.x.shape[0]}")
    print(f"  Num edges: {data.edge_index.shape[1]}")
    print(f"  Target (min_freq, max_freq): {data.y}")
    print(f"  Num sets: {data.num_sets}")
    print(f"  Num elements: {data.num_elements}")
