"""
Graph Neural Network model for union-closed families.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, global_mean_pool, global_max_pool
from torch_geometric.data import Data, Batch


class UnionClosedGNN(nn.Module):
    """
    Graph Attention Network for predicting element frequencies.

    Architecture:
    1. Node embedding layer
    2. Multiple GAT layers with attention
    3. Global pooling (mean + max)
    4. MLP for prediction

    Outputs:
    - min_frequency
    - max_frequency
    """

    def __init__(self, hidden_dim: int = 64, num_layers: int = 3,
                 num_heads: int = 4, dropout: float = 0.1):
        """
        Initialize GNN model.

        Args:
            hidden_dim: Hidden dimension size
            num_layers: Number of GAT layers
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        super().__init__()

        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.dropout = dropout

        # Input embedding (2 features: size/freq, type)
        self.input_embed = nn.Linear(2, hidden_dim)

        # GAT layers
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()

        for i in range(num_layers):
            if i == 0:
                in_dim = hidden_dim
            else:
                in_dim = hidden_dim * num_heads

            # Last layer: single head
            heads = 1 if i == num_layers - 1 else num_heads

            self.convs.append(
                GATConv(in_dim, hidden_dim, heads=heads, dropout=dropout, concat=(i < num_layers - 1))
            )
            self.norms.append(nn.LayerNorm(hidden_dim if i == num_layers - 1 else hidden_dim * num_heads))

        # Output dimension after GAT
        final_dim = hidden_dim

        # Global pooling dimension (mean + max)
        pool_dim = final_dim * 2

        # MLP for prediction
        self.mlp = nn.Sequential(
            nn.Linear(pool_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 2)  # [min_freq, max_freq]
        )

    def forward(self, data: Data):
        """
        Forward pass.

        Args:
            data: PyTorch Geometric Data or Batch

        Returns:
            Predictions [batch_size, 2] (min_freq, max_freq)
        """
        x, edge_index = data.x, data.edge_index

        # Input embedding
        x = self.input_embed(x)
        x = F.relu(x)

        # GAT layers
        for i, (conv, norm) in enumerate(zip(self.convs, self.norms)):
            x_new = conv(x, edge_index)
            x_new = norm(x_new)
            x_new = F.relu(x_new)
            x_new = F.dropout(x_new, p=self.dropout, training=self.training)

            # Residual connection (if dimensions match)
            if i > 0 and x.shape[-1] == x_new.shape[-1]:
                x = x + x_new
            else:
                x = x_new

        # Global pooling
        batch = data.batch if hasattr(data, 'batch') else torch.zeros(x.shape[0], dtype=torch.long, device=x.device)

        x_mean = global_mean_pool(x, batch)
        x_max = global_max_pool(x, batch)

        x_global = torch.cat([x_mean, x_max], dim=-1)

        # MLP
        out = self.mlp(x_global)

        # Ensure outputs are in [0, 1]
        out = torch.sigmoid(out)

        return out

    def get_attention_weights(self, data: Data, layer_idx: int = 0):
        """
        Extract attention weights from specific GAT layer.

        Args:
            data: Input graph
            layer_idx: Which GAT layer to extract from

        Returns:
            Attention weights
        """
        x, edge_index = data.x, data.edge_index

        # Forward pass up to specified layer
        x = self.input_embed(x)
        x = F.relu(x)

        for i, (conv, norm) in enumerate(zip(self.convs, self.norms)):
            if i == layer_idx:
                # Get attention weights
                x_new, (edge_index_attn, alpha) = conv(x, edge_index, return_attention_weights=True)
                return edge_index_attn, alpha

            x = conv(x, edge_index)
            x = norm(x)
            x = F.relu(x)

        return None, None


class EnsembleGNN(nn.Module):
    """
    Ensemble of multiple GNN models for better predictions.
    """

    def __init__(self, num_models: int = 5, **model_kwargs):
        """
        Initialize ensemble.

        Args:
            num_models: Number of models in ensemble
            **model_kwargs: Arguments for UnionClosedGNN
        """
        super().__init__()

        self.models = nn.ModuleList([
            UnionClosedGNN(**model_kwargs) for _ in range(num_models)
        ])

    def forward(self, data: Data):
        """
        Forward pass through ensemble (average predictions).

        Args:
            data: Input graph

        Returns:
            Averaged predictions
        """
        predictions = []

        for model in self.models:
            pred = model(data)
            predictions.append(pred)

        # Average predictions
        avg_pred = torch.stack(predictions).mean(dim=0)

        return avg_pred

    def predict_with_uncertainty(self, data: Data):
        """
        Predict with uncertainty estimates.

        Args:
            data: Input graph

        Returns:
            (mean_prediction, std_prediction)
        """
        predictions = []

        for model in self.models:
            pred = model(data)
            predictions.append(pred)

        predictions = torch.stack(predictions)

        mean = predictions.mean(dim=0)
        std = predictions.std(dim=0)

        return mean, std


if __name__ == "__main__":
    # Test model
    print("Testing GNN model...")

    model = UnionClosedGNN(hidden_dim=32, num_layers=3, num_heads=4)

    # Create dummy data
    x = torch.randn(10, 2)  # 10 nodes, 2 features
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)

    data = Data(x=x, edge_index=edge_index)

    # Forward pass
    out = model(data)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {out.shape}")
    print(f"Output (min_freq, max_freq): {out}")
    print(f"\nModel parameters: {sum(p.numel() for p in model.parameters()):,}")
