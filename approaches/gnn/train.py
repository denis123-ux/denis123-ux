"""
Training script for GNN model.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from .model import UnionClosedGNN, EnsembleGNN
from .dataset import create_dataloaders


def train_epoch(model, loader, optimizer, criterion, device):
    """
    Train for one epoch.

    Args:
        model: GNN model
        loader: DataLoader
        optimizer: Optimizer
        criterion: Loss function
        device: Device

    Returns:
        Average loss
    """
    model.train()
    total_loss = 0
    num_batches = 0

    for data in loader:
        data = data.to(device)

        optimizer.zero_grad()

        # Forward pass
        pred = model(data)
        target = data.y

        # Loss
        loss = criterion(pred, target)

        # Backward pass
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / max(num_batches, 1)


def evaluate(model, loader, criterion, device):
    """
    Evaluate model.

    Args:
        model: GNN model
        loader: DataLoader
        criterion: Loss function
        device: Device

    Returns:
        (avg_loss, metrics)
    """
    model.eval()
    total_loss = 0
    num_batches = 0

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for data in loader:
            data = data.to(device)

            pred = model(data)
            target = data.y

            loss = criterion(pred, target)

            total_loss += loss.item()
            num_batches += 1

            all_preds.append(pred.cpu())
            all_targets.append(target.cpu())

    avg_loss = total_loss / max(num_batches, 1)

    # Compute metrics
    all_preds = torch.cat(all_preds, dim=0)
    all_targets = torch.cat(all_targets, dim=0)

    # MAE for min and max frequency
    mae_min = torch.abs(all_preds[:, 0] - all_targets[:, 0]).mean().item()
    mae_max = torch.abs(all_preds[:, 1] - all_targets[:, 1]).mean().item()

    # Check if predicted max_freq >= 0.5 when actual max_freq >= 0.5
    correct_conjecture = ((all_preds[:, 1] >= 0.5) == (all_targets[:, 1] >= 0.5)).float().mean().item()

    metrics = {
        'mae_min_freq': mae_min,
        'mae_max_freq': mae_max,
        'conjecture_accuracy': correct_conjecture
    }

    return avg_loss, metrics


def train_gnn(hidden_dim: int = 64, num_layers: int = 3, num_heads: int = 4,
              learning_rate: float = 1e-3, num_epochs: int = 100,
              train_size: int = 8000, val_size: int = 1000,
              test_size: int = 1000, batch_size: int = 32,
              device: str = None, save_path: str = 'gnn_model.pt'):
    """
    Train GNN model.

    Args:
        hidden_dim: Hidden dimension
        num_layers: Number of layers
        num_heads: Number of attention heads
        learning_rate: Learning rate
        num_epochs: Number of epochs
        train_size: Training set size
        val_size: Validation set size
        test_size: Test set size
        batch_size: Batch size
        device: Device (None = auto-detect)
        save_path: Path to save best model

    Returns:
        (model, train_history)
    """
    # Device
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    device = torch.device(device)

    print(f"Using device: {device}")

    # Create dataloaders
    print("Creating datasets...")
    train_loader, val_loader, test_loader = create_dataloaders(
        train_size=train_size,
        val_size=val_size,
        test_size=test_size,
        batch_size=batch_size
    )

    # Create model
    print("Creating model...")
    model = UnionClosedGNN(
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        num_heads=num_heads
    ).to(device)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Optimizer and loss
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)
    criterion = nn.MSELoss()

    # Training loop
    best_val_loss = float('inf')
    train_history = {
        'train_loss': [],
        'val_loss': [],
        'val_metrics': []
    }

    print(f"\nTraining for {num_epochs} epochs...")

    for epoch in range(num_epochs):
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)

        # Validate
        val_loss, val_metrics = evaluate(model, val_loader, criterion, device)

        # Scheduler step
        scheduler.step(val_loss)

        # Save history
        train_history['train_loss'].append(train_loss)
        train_history['val_loss'].append(val_loss)
        train_history['val_metrics'].append(val_metrics)

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'val_metrics': val_metrics
            }, save_path)

        # Print progress
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{num_epochs}")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Val MAE (min): {val_metrics['mae_min_freq']:.4f}")
            print(f"  Val MAE (max): {val_metrics['mae_max_freq']:.4f}")
            print(f"  Conjecture Acc: {val_metrics['conjecture_accuracy']:.2%}")

    # Load best model
    checkpoint = torch.load(save_path)
    model.load_state_dict(checkpoint['model_state_dict'])

    # Final evaluation on test set
    print("\nFinal evaluation on test set:")
    test_loss, test_metrics = evaluate(model, test_loader, criterion, device)
    print(f"  Test Loss: {test_loss:.4f}")
    print(f"  Test MAE (min): {test_metrics['mae_min_freq']:.4f}")
    print(f"  Test MAE (max): {test_metrics['mae_max_freq']:.4f}")
    print(f"  Conjecture Acc: {test_metrics['conjecture_accuracy']:.2%}")

    return model, train_history


if __name__ == "__main__":
    # Train model
    model, history = train_gnn(
        hidden_dim=64,
        num_layers=3,
        num_heads=4,
        learning_rate=1e-3,
        num_epochs=50,
        train_size=1000,  # Small for testing
        val_size=200,
        test_size=200,
        batch_size=32
    )
