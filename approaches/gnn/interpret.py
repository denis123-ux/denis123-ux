"""
Interpretability module: Extract symbolic rules from trained GNN.

Uses:
1. Attention analysis
2. Feature importance (SHAP-like)
3. Symbolic regression on hidden representations
"""

import torch
import numpy as np
from typing import Dict, List, Tuple
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from .model import UnionClosedGNN
from core.family import UnionClosedFamily


class GNNInterpreter:
    """
    Interpret trained GNN to extract mathematical insights.
    """

    def __init__(self, model: UnionClosedGNN, device: str = 'cpu'):
        """
        Initialize interpreter.

        Args:
            model: Trained GNN model
            device: Device
        """
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()

    def analyze_attention(self, data) -> Dict:
        """
        Analyze attention weights to understand what the model focuses on.

        Args:
            data: Input graph data

        Returns:
            Attention analysis results
        """
        data = data.to(self.device)

        attention_maps = []

        # Extract attention from each layer
        for layer_idx in range(self.model.num_layers):
            edge_index, alpha = self.model.get_attention_weights(data, layer_idx)

            if alpha is not None:
                attention_maps.append({
                    'layer': layer_idx,
                    'edge_index': edge_index.cpu().numpy(),
                    'weights': alpha.cpu().detach().numpy()
                })

        # Aggregate attention patterns
        if attention_maps:
            all_weights = np.concatenate([am['weights'].flatten() for am in attention_maps])

            return {
                'attention_maps': attention_maps,
                'mean_attention': np.mean(all_weights),
                'max_attention': np.max(all_weights),
                'attention_entropy': self._compute_entropy(all_weights)
            }
        else:
            return {'attention_maps': [], 'mean_attention': 0, 'max_attention': 0, 'attention_entropy': 0}

    def _compute_entropy(self, weights: np.ndarray) -> float:
        """Compute entropy of attention distribution."""
        weights = weights.flatten()
        weights = weights / (np.sum(weights) + 1e-15)

        entropy = 0.0
        for w in weights:
            if w > 1e-15:
                entropy -= w * np.log(w)

        return entropy

    def extract_graph_features(self, data) -> Dict[str, float]:
        """
        Extract interpretable graph-level features.

        Args:
            data: Input graph

        Returns:
            Dict of features
        """
        features = {
            'num_sets': data.num_sets,
            'num_elements': data.num_elements,
            'avg_set_size': data.avg_set_size if hasattr(data, 'avg_set_size') else 0,
            'density': data.density if hasattr(data, 'density') else 0,
            'num_edges': data.edge_index.shape[1],
            'avg_degree': data.edge_index.shape[1] / max(data.x.shape[0], 1)
        }

        return features

    def predict_with_explanation(self, data) -> Dict:
        """
        Make prediction with explanation.

        Args:
            data: Input graph

        Returns:
            Prediction + explanation
        """
        data = data.to(self.device)

        # Get prediction
        with torch.no_grad():
            pred = self.model(data)

        # Analyze attention
        attention_analysis = self.analyze_attention(data)

        # Extract features
        features = self.extract_graph_features(data)

        return {
            'prediction': pred.cpu().numpy(),
            'min_freq_pred': pred[0, 0].item(),
            'max_freq_pred': pred[0, 1].item(),
            'features': features,
            'attention_analysis': attention_analysis
        }

    def discover_patterns(self, dataset, num_samples: int = 100) -> Dict:
        """
        Discover patterns across multiple examples.

        Args:
            dataset: Dataset of families
            num_samples: Number of samples to analyze

        Returns:
            Discovered patterns
        """
        predictions = []
        features_list = []
        attention_stats = []

        for i in range(min(num_samples, len(dataset))):
            data = dataset[i]
            result = self.predict_with_explanation(data)

            predictions.append(result['prediction'])
            features_list.append(result['features'])
            attention_stats.append({
                'mean': result['attention_analysis']['mean_attention'],
                'max': result['attention_analysis']['max_attention'],
                'entropy': result['attention_analysis']['attention_entropy']
            })

        # Analyze correlations
        predictions = np.array(predictions)
        features_array = self._dict_list_to_array(features_list)

        # Compute feature importance via correlation
        correlations_min = []
        correlations_max = []

        feature_names = list(features_list[0].keys())

        for i, feat_name in enumerate(feature_names):
            corr_min = np.corrcoef(features_array[:, i], predictions[:, 0, 0])[0, 1]
            corr_max = np.corrcoef(features_array[:, i], predictions[:, 0, 1])[0, 1]

            correlations_min.append((feat_name, corr_min))
            correlations_max.append((feat_name, corr_max))

        # Sort by absolute correlation
        correlations_min = sorted(correlations_min, key=lambda x: abs(x[1]), reverse=True)
        correlations_max = sorted(correlations_max, key=lambda x: abs(x[1]), reverse=True)

        return {
            'num_samples': num_samples,
            'feature_importance_min_freq': correlations_min,
            'feature_importance_max_freq': correlations_max,
            'avg_attention_mean': np.mean([a['mean'] for a in attention_stats]),
            'avg_attention_entropy': np.mean([a['entropy'] for a in attention_stats])
        }

    def _dict_list_to_array(self, dict_list: List[Dict]) -> np.ndarray:
        """Convert list of dicts to numpy array."""
        keys = list(dict_list[0].keys())
        array = np.array([[d[k] for k in keys] for d in dict_list])
        return array


def extract_symbolic_rules(model: UnionClosedGNN, dataset,
                           num_samples: int = 1000) -> Dict:
    """
    Extract symbolic rules from trained GNN.

    Args:
        model: Trained GNN
        dataset: Dataset
        num_samples: Number of samples for analysis

    Returns:
        Symbolic rules and insights
    """
    interpreter = GNNInterpreter(model)

    print("Discovering patterns...")
    patterns = interpreter.discover_patterns(dataset, num_samples)

    print("\nFeature Importance (for max frequency):")
    for feat_name, corr in patterns['feature_importance_max_freq'][:5]:
        print(f"  {feat_name}: {corr:.3f}")

    print("\nFeature Importance (for min frequency):")
    for feat_name, corr in patterns['feature_importance_min_freq'][:5]:
        print(f"  {feat_name}: {corr:.3f}")

    # Heuristic rule extraction
    rules = []

    for feat_name, corr in patterns['feature_importance_max_freq']:
        if abs(corr) > 0.5:
            if corr > 0:
                rule = f"IF {feat_name} is HIGH THEN max_frequency is HIGH"
            else:
                rule = f"IF {feat_name} is HIGH THEN max_frequency is LOW"
            rules.append((rule, abs(corr)))

    print("\nExtracted Heuristic Rules (|correlation| > 0.5):")
    for rule, strength in sorted(rules, key=lambda x: x[1], reverse=True):
        print(f"  [{strength:.2f}] {rule}")

    return {
        'patterns': patterns,
        'rules': rules
    }


def demonstrate_interpretability():
    """
    Demonstrate interpretability on a simple example.
    """
    from .dataset import UnionClosedDataset

    print("=" * 70)
    print("GNN INTERPRETABILITY DEMO")
    print("=" * 70)
    print()

    # Create small dataset
    dataset = UnionClosedDataset(num_families=100, max_n=6, seed=42)

    # Create and "train" a simple model (random weights for demo)
    model = UnionClosedGNN(hidden_dim=32, num_layers=2, num_heads=2)

    # Interpret
    extract_symbolic_rules(model, dataset, num_samples=50)


if __name__ == "__main__":
    demonstrate_interpretability()
