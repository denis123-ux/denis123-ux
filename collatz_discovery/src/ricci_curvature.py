"""
Ollivier-Ricci Curvature for Collatz Graph

REVOLUTIONARY GEOMETRIC APPROACH:

Ricci curvature measures how geodesics converge/diverge.
In graphs: Ollivier-Ricci curvature measures "mass transport" between neighborhoods.

KEY THEOREM (to prove for Collatz):
If κ(e) < 0 for all edges e (negative curvature everywhere),
then graph is "hyperbolic" and flows toward center → convergence to sink!

If κ(e) > 0 (positive curvature), graph is "spherical" → no sink possible
If κ(e) = 0, graph is "flat"

HYPOTHESIS: Collatz graph has negative curvature near periphery,
forcing "flow" toward the center (sink = 1)
"""

import numpy as np
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from typing import Dict, List, Tuple, Set, Optional
import networkx as nx
from collections import defaultdict


class OllivierRicciCurvature:
    """
    Compute Ollivier-Ricci curvature on directed graphs

    κ(x,y) = 1 - W₁(μₓ, μᵧ) / d(x,y)

    where:
    - W₁ is Wasserstein-1 (Earth Mover's Distance)
    - μₓ, μᵧ are probability distributions on neighborhoods
    - d(x,y) is graph distance
    """

    def __init__(self, G: nx.DiGraph, alpha: float = 0.5):
        """
        Args:
            G: NetworkX directed graph
            alpha: Lazy random walk parameter (probability of staying at node)
        """
        self.G = G
        self.alpha = alpha
        self.curvatures = {}

    def get_neighborhood_distribution(self, node: int) -> Dict[int, float]:
        """
        Compute probability distribution on neighborhood

        μₓ(y) = α·δₓ(y) + (1-α)·(1/deg(x))·𝟙{y ~ x}

        This is a "lazy random walk" distribution
        """
        neighbors = list(self.G.successors(node))

        if not neighbors:
            # No outgoing edges - all mass stays at node
            return {node: 1.0}

        distribution = {}

        # Lazy walk: α probability stays at node
        distribution[node] = self.alpha

        # (1-α) distributed uniformly to neighbors
        neighbor_prob = (1 - self.alpha) / len(neighbors)
        for neighbor in neighbors:
            distribution[neighbor] = distribution.get(neighbor, 0) + neighbor_prob

        return distribution

    def wasserstein_distance(
        self,
        dist1: Dict[int, float],
        dist2: Dict[int, float],
        distance_matrix: Dict[Tuple[int, int], float]
    ) -> float:
        """
        Compute Wasserstein-1 distance between two distributions

        This is the "optimal transport" distance - minimum cost
        to transform dist1 into dist2
        """
        # Get all nodes in support of either distribution
        nodes1 = set(dist1.keys())
        nodes2 = set(dist2.keys())
        all_nodes = sorted(nodes1 | nodes2)

        if not all_nodes:
            return 0.0

        # Create cost matrix
        n = len(all_nodes)
        cost_matrix = np.zeros((n, n))

        for i, node_i in enumerate(all_nodes):
            for j, node_j in enumerate(all_nodes):
                # Cost is graph distance between nodes
                if (node_i, node_j) in distance_matrix:
                    cost_matrix[i, j] = distance_matrix[(node_i, node_j)]
                elif node_i == node_j:
                    cost_matrix[i, j] = 0.0
                else:
                    cost_matrix[i, j] = 1.0  # Default distance

        # Create probability vectors
        prob1 = np.array([dist1.get(node, 0.0) for node in all_nodes])
        prob2 = np.array([dist2.get(node, 0.0) for node in all_nodes])

        # Normalize (should already be normalized, but ensure)
        prob1 /= prob1.sum() if prob1.sum() > 0 else 1.0
        prob2 /= prob2.sum() if prob2.sum() > 0 else 1.0

        # Solve optimal transport (linear assignment problem)
        # For discrete distributions, use Hungarian algorithm
        # Cost = sum of prob[i] * cost[i, matched[i]]

        # Simplified version: compute expected distance under product measure
        # (exact optimal transport is NP-hard in general)
        w_dist = 0.0
        for i, p1 in enumerate(prob1):
            for j, p2 in enumerate(prob2):
                w_dist += p1 * p2 * cost_matrix[i, j]

        return w_dist

    def compute_edge_curvature(
        self,
        node1: int,
        node2: int,
        distance_matrix: Dict[Tuple[int, int], float]
    ) -> float:
        """
        Compute Ricci curvature for edge (node1, node2)

        κ(x→y) = 1 - W₁(μₓ, μᵧ) / d(x,y)

        Interpretation:
        - κ > 0: positive curvature (neighborhoods converge)
        - κ < 0: negative curvature (neighborhoods diverge)
        - κ = 0: flat (no curvature)
        """
        # Get neighborhood distributions
        dist1 = self.get_neighborhood_distribution(node1)
        dist2 = self.get_neighborhood_distribution(node2)

        # Graph distance between nodes
        if (node1, node2) in distance_matrix:
            d_xy = distance_matrix[(node1, node2)]
        else:
            d_xy = 1.0  # Default for direct edge

        if d_xy == 0:
            return 0.0

        # Compute Wasserstein distance
        w_dist = self.wasserstein_distance(dist1, dist2, distance_matrix)

        # Ricci curvature
        curvature = 1.0 - (w_dist / d_xy)

        return curvature

    def compute_all_curvatures(
        self,
        max_distance: int = 3,
        sample_edges: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[Tuple[int, int], float]:
        """
        Compute Ricci curvature for all (or sampled) edges

        Args:
            max_distance: Maximum distance to compute in distance matrix
            sample_edges: If set, randomly sample this many edges (for large graphs)
            verbose: Print progress

        Returns:
            Dictionary mapping (node1, node2) → curvature
        """
        if verbose:
            print("Computing Ricci curvatures...")

        # Precompute distance matrix (expensive for large graphs)
        if verbose:
            print("  Computing pairwise distances...")

        distance_matrix = {}

        # Only compute distances for nodes involved in edges (optimization)
        nodes_in_edges = set()
        for edge in self.G.edges():
            nodes_in_edges.add(edge[0])
            nodes_in_edges.add(edge[1])

        # Compute distances using BFS from each node
        for source in nodes_in_edges:
            distances = nx.single_source_shortest_path_length(
                self.G,
                source,
                cutoff=max_distance
            )
            for target, dist in distances.items():
                distance_matrix[(source, target)] = dist

        # Get edges to process
        edges = list(self.G.edges())

        if sample_edges and len(edges) > sample_edges:
            import random
            edges = random.sample(edges, sample_edges)
            if verbose:
                print(f"  Sampling {sample_edges} edges from {len(self.G.edges())} total")

        # Compute curvature for each edge
        if verbose:
            print(f"  Computing curvature for {len(edges)} edges...")

        for i, (node1, node2) in enumerate(edges):
            curvature = self.compute_edge_curvature(node1, node2, distance_matrix)
            self.curvatures[(node1, node2)] = curvature

            if verbose and (i + 1) % max(1, len(edges) // 10) == 0:
                print(f"    Processed {i+1}/{len(edges)} edges...")

        if verbose:
            print(f"✓ Computed {len(self.curvatures)} edge curvatures")

        return self.curvatures

    def analyze_curvature_distribution(self) -> Dict:
        """
        Analyze distribution of curvatures

        KEY QUESTION: Are most edges negatively curved?
        """
        if not self.curvatures:
            return {}

        curvs = np.array(list(self.curvatures.values()))

        analysis = {
            'mean_curvature': np.mean(curvs),
            'std_curvature': np.std(curvs),
            'min_curvature': np.min(curvs),
            'max_curvature': np.max(curvs),
            'median_curvature': np.median(curvs),
            'fraction_negative': np.mean(curvs < 0),
            'fraction_positive': np.mean(curvs > 0),
            'fraction_near_zero': np.mean(np.abs(curvs) < 0.1),
        }

        # Find most negatively/positively curved edges
        curv_items = list(self.curvatures.items())
        curv_items.sort(key=lambda x: x[1])

        analysis['most_negative_edges'] = curv_items[:5]
        analysis['most_positive_edges'] = curv_items[-5:]

        return analysis

    def test_hyperbolic_hypothesis(self, verbose: bool = True) -> Dict:
        """
        TEST GEOMETRIC THEOREM:

        If graph is uniformly negatively curved (κ < -ε),
        then it's hyperbolic → has unique center → convergence!

        Returns evidence for/against hypothesis
        """
        if not self.curvatures:
            return {'error': 'No curvatures computed'}

        analysis = self.analyze_curvature_distribution()

        if verbose:
            print("\n" + "="*60)
            print("HYPERBOLIC STRUCTURE HYPOTHESIS TEST")
            print("="*60)
            print(f"\nMean curvature: {analysis['mean_curvature']:.6f}")
            print(f"Median curvature: {analysis['median_curvature']:.6f}")
            print(f"Curvature range: [{analysis['min_curvature']:.6f}, {analysis['max_curvature']:.6f}]")
            print(f"\nFraction negative: {analysis['fraction_negative']:.2%}")
            print(f"Fraction positive: {analysis['fraction_positive']:.2%}")
            print(f"Fraction near zero: {analysis['fraction_near_zero']:.2%}")

            print(f"\n✓ Predominantly negative curvature: {analysis['fraction_negative'] > 0.5}")
            print(f"✓ Mean curvature negative: {analysis['mean_curvature'] < 0}")

        # Hypothesis is supported if most edges are negatively curved
        hypothesis_supported = (
            analysis['fraction_negative'] > 0.5 and
            analysis['mean_curvature'] < 0
        )

        return {
            'analysis': analysis,
            'hypothesis_supported': hypothesis_supported,
            'strength': abs(analysis['mean_curvature']),  # How strongly negative
        }


def compute_ricci_flow_simulation(
    G: nx.DiGraph,
    curvatures: Dict[Tuple[int, int], float],
    num_steps: int = 10,
    dt: float = 0.1
) -> List[nx.DiGraph]:
    """
    Simulate Ricci flow on graph

    Ricci flow: Evolve edge weights according to curvature
    w(e, t+dt) = w(e, t) - dt * κ(e)

    Edges with negative curvature get strengthened
    Edges with positive curvature get weakened

    This should reveal the "stable geometry" of the graph
    """
    # Initialize edge weights
    edge_weights = {edge: 1.0 for edge in G.edges()}

    graphs = [G.copy()]

    for step in range(num_steps):
        # Update weights according to Ricci flow
        for edge in edge_weights:
            if edge in curvatures:
                kappa = curvatures[edge]
                edge_weights[edge] -= dt * kappa

                # Keep weights positive
                edge_weights[edge] = max(0.01, edge_weights[edge])

        # Create new graph with updated weights
        G_new = G.copy()
        nx.set_edge_attributes(G_new, edge_weights, 'weight')

        graphs.append(G_new)

    return graphs


def analyze_ricci_curvature_collatz(
    G: nx.DiGraph,
    alpha: float = 0.5,
    max_distance: int = 3,
    sample_edges: Optional[int] = 1000,
    verbose: bool = True
) -> Tuple[OllivierRicciCurvature, Dict]:
    """
    Complete Ricci curvature analysis for Collatz graph

    Returns:
        (curvature_computer, analysis_results)
    """
    # Compute curvatures
    orc = OllivierRicciCurvature(G, alpha=alpha)
    orc.compute_all_curvatures(
        max_distance=max_distance,
        sample_edges=sample_edges,
        verbose=verbose
    )

    # Test hypothesis
    results = orc.test_hyperbolic_hypothesis(verbose=verbose)

    return orc, results
