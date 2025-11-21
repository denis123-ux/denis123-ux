"""
Collatz Graph Engine - High Performance Implementation
Builds directed graph of Collatz function with efficient sparse representation
"""

import numpy as np
import networkx as nx
from scipy import sparse
from typing import Dict, Set, List, Tuple, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
import pickle


@dataclass
class CollatzNode:
    """Single node in Collatz graph"""
    value: int
    successors: List[int]  # Next values in Collatz sequence
    predecessors: List[int]  # Values that lead to this one
    stopping_time: Optional[int] = None
    max_value: Optional[int] = None


class CollatzGraph:
    """
    Directed graph representation of Collatz function

    Key innovation: We can analyze this as a GRAPH with spectral properties
    rather than just individual sequences!
    """

    def __init__(self, max_value: int = 10000):
        self.max_value = max_value
        self.nodes: Dict[int, CollatzNode] = {}
        self.adjacency: Dict[int, Set[int]] = defaultdict(set)
        self.reverse_adjacency: Dict[int, Set[int]] = defaultdict(set)

    def collatz_next(self, n: int) -> int:
        """Single Collatz step"""
        return n // 2 if n % 2 == 0 else 3 * n + 1

    def collatz_predecessors(self, n: int) -> List[int]:
        """
        Find ALL numbers that map to n under Collatz

        Critical: This is the INVERSE function!
        - If n is result of even step: predecessor is 2n
        - If n is result of odd step: predecessor is (n-1)/3 (if (n-1) % 3 == 0 and odd)
        """
        preds = []

        # Predecessor from even step: 2n
        if 2 * n <= self.max_value:
            preds.append(2 * n)

        # Predecessor from odd step: (n-1)/3
        # Only valid if (n-1) % 3 == 0 and result is odd
        if n > 1 and (n - 1) % 3 == 0:
            pred = (n - 1) // 3
            if pred % 2 == 1 and pred > 0 and pred <= self.max_value:
                preds.append(pred)

        return preds

    def build_graph(self, verbose: bool = True):
        """
        Build complete Collatz graph up to max_value

        This creates the FULL graph structure needed for spectral analysis
        """
        if verbose:
            print(f"Building Collatz graph for n ∈ [1, {self.max_value}]...")

        # Build all nodes and forward edges
        for n in range(1, self.max_value + 1):
            if n not in self.nodes:
                self.nodes[n] = CollatzNode(value=n, successors=[], predecessors=[])

            # Forward edge
            next_val = self.collatz_next(n)
            self.nodes[n].successors.append(next_val)
            self.adjacency[n].add(next_val)

            # Track reverse edge
            if next_val <= self.max_value:
                self.reverse_adjacency[next_val].add(n)

            if verbose and n % 100000 == 0:
                print(f"  Processed {n:,} nodes...")

        # Build backward edges
        for n in range(1, self.max_value + 1):
            preds = self.collatz_predecessors(n)
            self.nodes[n].predecessors = preds

        # Compute stopping times via BFS from 1
        self._compute_stopping_times()

        if verbose:
            print(f"✓ Graph built: {len(self.nodes):,} nodes, {len(self.adjacency):,} edges")

    def _compute_stopping_times(self):
        """Compute stopping time for all nodes via reverse BFS from sink (1)"""
        queue = deque([1])
        self.nodes[1].stopping_time = 0

        while queue:
            current = queue.popleft()
            current_time = self.nodes[current].stopping_time

            # All predecessors have stopping time = current_time + 1
            for pred in self.reverse_adjacency[current]:
                if pred in self.nodes and self.nodes[pred].stopping_time is None:
                    self.nodes[pred].stopping_time = current_time + 1
                    queue.append(pred)

    def to_networkx(self) -> nx.DiGraph:
        """Convert to NetworkX graph for analysis"""
        G = nx.DiGraph()

        for node_val, node in self.nodes.items():
            G.add_node(node_val,
                      stopping_time=node.stopping_time,
                      max_value=node.max_value)

        for src, targets in self.adjacency.items():
            for tgt in targets:
                if tgt in self.nodes:  # Only add edge if target is in range
                    G.add_edge(src, tgt)

        return G

    def to_adjacency_matrix(self) -> Tuple[sparse.csr_matrix, List[int]]:
        """
        Convert to sparse adjacency matrix for spectral analysis

        Returns:
            (adjacency_matrix, node_list) where indices correspond to node_list
        """
        node_list = sorted(self.nodes.keys())
        node_to_idx = {node: idx for idx, node in enumerate(node_list)}
        n = len(node_list)

        # Build sparse matrix in COO format
        rows = []
        cols = []
        data = []

        for node_val in node_list:
            src_idx = node_to_idx[node_val]
            for successor in self.nodes[node_val].successors:
                if successor in node_to_idx:
                    tgt_idx = node_to_idx[successor]
                    rows.append(src_idx)
                    cols.append(tgt_idx)
                    data.append(1.0)

        # Convert to CSR for efficient operations
        adjacency = sparse.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()

        return adjacency, node_list

    def get_subgraph(self, nodes: Set[int]) -> 'CollatzGraph':
        """Extract subgraph containing only specified nodes"""
        subgraph = CollatzGraph(max_value=self.max_value)

        for node_val in nodes:
            if node_val in self.nodes:
                subgraph.nodes[node_val] = self.nodes[node_val]

                # Filter adjacency to only include nodes in subgraph
                for succ in self.nodes[node_val].successors:
                    if succ in nodes:
                        subgraph.adjacency[node_val].add(succ)
                        subgraph.reverse_adjacency[succ].add(node_val)

        return subgraph

    def find_strongly_connected_components(self) -> List[Set[int]]:
        """Find strongly connected components (cycles in Collatz graph)"""
        G = self.to_networkx()
        return list(nx.strongly_connected_components(G))

    def compute_graph_statistics(self) -> Dict:
        """Compute key graph statistics"""
        G = self.to_networkx()

        # Basic stats
        stats = {
            'num_nodes': len(self.nodes),
            'num_edges': sum(len(succs) for succs in self.adjacency.values()),
            'avg_degree': np.mean([len(succs) for succs in self.adjacency.values()]),
        }

        # Stopping time statistics
        stopping_times = [n.stopping_time for n in self.nodes.values()
                         if n.stopping_time is not None]
        if stopping_times:
            stats['avg_stopping_time'] = np.mean(stopping_times)
            stats['max_stopping_time'] = np.max(stopping_times)
            stats['std_stopping_time'] = np.std(stopping_times)

        # Connected components
        sccs = self.find_strongly_connected_components()
        stats['num_strongly_connected_components'] = len(sccs)
        stats['largest_scc_size'] = max(len(scc) for scc in sccs) if sccs else 0

        # Check if graph is a DAG (no cycles except trivial 1->1)
        stats['is_dag'] = nx.is_directed_acyclic_graph(G) or (
            len(sccs) == len(self.nodes) - 1  # All singleton except {1}
        )

        return stats

    def save(self, filepath: str):
        """Save graph to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'max_value': self.max_value,
                'nodes': self.nodes,
                'adjacency': dict(self.adjacency),
                'reverse_adjacency': dict(self.reverse_adjacency),
            }, f)

    @classmethod
    def load(cls, filepath: str) -> 'CollatzGraph':
        """Load graph from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        graph = cls(max_value=data['max_value'])
        graph.nodes = data['nodes']
        graph.adjacency = defaultdict(set, data['adjacency'])
        graph.reverse_adjacency = defaultdict(set, data['reverse_adjacency'])

        return graph


def quick_trajectory(n: int, max_steps: int = 10000) -> List[int]:
    """Generate single trajectory (for standalone use)"""
    traj = [n]
    current = n
    steps = 0

    while current != 1 and steps < max_steps:
        current = current // 2 if current % 2 == 0 else 3 * current + 1
        traj.append(current)
        steps += 1

    return traj
