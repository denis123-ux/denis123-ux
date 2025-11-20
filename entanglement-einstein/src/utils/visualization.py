"""
Publication-quality visualization for quantum gravity research.

All plots follow these principles:
- High DPI (300+) for publications
- Clear labels with units
- Error bars/confidence intervals
- Consistent styling
- Saved in multiple formats (PDF, PNG)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import seaborn as sns

# Set publication-quality defaults
rcParams['font.size'] = 11
rcParams['axes.labelsize'] = 12
rcParams['axes.titlesize'] = 13
rcParams['xtick.labelsize'] = 10
rcParams['ytick.labelsize'] = 10
rcParams['legend.fontsize'] = 10
rcParams['figure.titlesize'] = 14
rcParams['figure.dpi'] = 150
rcParams['savefig.dpi'] = 300
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Computer Modern Roman']
rcParams['text.usetex'] = False  # Set to True if LaTeX installed

# Color palette
COLORS = sns.color_palette("husl", 8)


def plot_area_law_fit(
    entropies: np.ndarray,
    boundary_lengths: np.ndarray,
    slope: float,
    intercept: float,
    r_squared: float,
    theoretical_slope: Optional[float] = None,
    title: str = "Area Law Verification",
    save_path: Optional[str] = None,
    confidence_interval: Optional[Tuple[float, float]] = None
):
    """
    Plot entanglement entropy vs boundary length with area law fit.

    Args:
        entropies: Array of entanglement entropy values
        boundary_lengths: Array of boundary lengths
        slope: Fitted slope
        intercept: Fitted intercept
        r_squared: R² value of fit
        theoretical_slope: Expected theoretical slope (e.g., c/3)
        title: Plot title
        save_path: Path to save figure
        confidence_interval: (lower, upper) CI for slope
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Plot 1: Data with fit
    log_boundaries = np.log(boundary_lengths)

    ax1.scatter(log_boundaries, entropies, alpha=0.6, s=50,
                color=COLORS[0], label='Data', edgecolors='black', linewidth=0.5)

    # Fitted line
    x_fit = np.linspace(log_boundaries.min(), log_boundaries.max(), 100)
    y_fit = slope * x_fit + intercept
    ax1.plot(x_fit, y_fit, 'r-', linewidth=2,
             label=f'Fit: $S = {slope:.4f} \log|∂A| + {intercept:.3f}$')

    # Theoretical line if provided
    if theoretical_slope is not None:
        y_theory = theoretical_slope * x_fit + intercept
        ax1.plot(x_fit, y_theory, 'g--', linewidth=2, alpha=0.7,
                 label=f'Theory: slope = {theoretical_slope:.4f}')

    ax1.set_xlabel(r'$\log(|\partial A|)$ (log boundary length)')
    ax1.set_ylabel(r'$S_{EE}(A)$ (entanglement entropy)')
    ax1.set_title(f'{title}\n$R^2 = {r_squared:.5f}$')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Residuals
    y_pred = slope * log_boundaries + intercept
    residuals = entropies - y_pred

    ax2.scatter(log_boundaries, residuals, alpha=0.6, s=50,
                color=COLORS[1], edgecolors='black', linewidth=0.5)
    ax2.axhline(y=0, color='r', linestyle='--', linewidth=2)
    ax2.set_xlabel(r'$\log(|\partial A|)$')
    ax2.set_ylabel('Residuals')
    ax2.set_title('Residual Analysis')
    ax2.grid(True, alpha=0.3)

    # Add statistics text
    stats_text = f'Slope: {slope:.6f}'
    if confidence_interval:
        stats_text += f' ± {confidence_interval[1] - slope:.6f}'
    if theoretical_slope:
        deviation = abs(slope - theoretical_slope) / theoretical_slope * 100
        stats_text += f'\nDeviation from theory: {deviation:.2f}%'

    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save in multiple formats
        plt.savefig(save_path, bbox_inches='tight')
        plt.savefig(save_path.with_suffix('.png'), bbox_inches='tight')
        print(f"✓ Figure saved: {save_path}")

    plt.show()


def plot_convergence(
    iterations: np.ndarray,
    values: np.ndarray,
    ylabel: str = "Fidelity",
    title: str = "Optimization Convergence",
    save_path: Optional[str] = None,
    target_value: Optional[float] = None
):
    """
    Plot convergence of optimization.

    Args:
        iterations: Iteration numbers
        values: Values at each iteration
        ylabel: Label for y-axis
        title: Plot title
        save_path: Path to save figure
        target_value: Optional target value to show as horizontal line
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(iterations, values, linewidth=2, color=COLORS[0])

    if target_value is not None:
        ax.axhline(y=target_value, color='r', linestyle='--',
                   linewidth=2, label=f'Target: {target_value:.6f}')
        ax.legend()

    ax.set_xlabel('Iteration')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    # Use log scale if converging to small values
    if values[-1] / values[0] < 0.01:
        ax.set_yscale('log')

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight')
        plt.savefig(save_path.with_suffix('.png'), bbox_inches='tight')
        print(f"✓ Figure saved: {save_path}")

    plt.show()


def plot_bond_dimension_scaling(
    bond_dimensions: List[int],
    errors: List[float],
    error_bars: Optional[List[float]] = None,
    title: str = "Continuum Limit Extrapolation",
    save_path: Optional[str] = None,
    fit_params: Optional[Dict] = None
):
    """
    Plot error vs bond dimension for continuum extrapolation.

    Args:
        bond_dimensions: List of bond dimensions
        errors: Errors at each bond dimension
        error_bars: Optional error bars
        title: Plot title
        save_path: Path to save figure
        fit_params: Optional fit parameters for extrapolation
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data
    if error_bars:
        ax.errorbar(bond_dimensions, errors, yerr=error_bars,
                    fmt='o', markersize=8, capsize=5, capthick=2,
                    color=COLORS[0], label='Data')
    else:
        ax.plot(bond_dimensions, errors, 'o', markersize=8,
                color=COLORS[0], label='Data')

    # Plot fit if provided
    if fit_params:
        d_fit = np.linspace(min(bond_dimensions), max(bond_dimensions)*2, 100)
        if 'alpha' in fit_params:
            # Power law: error ~ 1/d^alpha
            error_fit = fit_params['A'] / d_fit**fit_params['alpha']
            ax.plot(d_fit, error_fit, 'r--', linewidth=2,
                    label=f"Fit: $\epsilon \sim d^{{-{fit_params['alpha']:.2f}}}$")

            # Extrapolation to infinity
            ax.axhline(y=0, color='g', linestyle=':', linewidth=2,
                       label='Continuum limit (d→∞)')

    ax.set_xlabel('Bond Dimension $d$')
    ax.set_ylabel('Error')
    ax.set_title(title)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight')
        plt.savefig(save_path.with_suffix('.png'), bbox_inches='tight')
        print(f"✓ Figure saved: {save_path}")

    plt.show()


def plot_metric_heatmap(
    metric_tensor: np.ndarray,
    coordinates: Optional[List[str]] = None,
    title: str = "Emergent Metric Tensor",
    save_path: Optional[str] = None
):
    """
    Plot heatmap of metric tensor components.

    Args:
        metric_tensor: 2D array representing metric
        coordinates: Labels for coordinates
        title: Plot title
        save_path: Path to save figure
    """
    fig, ax = plt.subplots(figsize=(8, 7))

    # Plot heatmap
    im = ax.imshow(metric_tensor, cmap='RdBu_r', aspect='auto')

    # Set ticks
    if coordinates:
        ax.set_xticks(np.arange(len(coordinates)))
        ax.set_yticks(np.arange(len(coordinates)))
        ax.set_xticklabels(coordinates)
        ax.set_yticklabels(coordinates)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('$g_{μν}$', rotation=270, labelpad=20)

    # Add values in cells
    for i in range(metric_tensor.shape[0]):
        for j in range(metric_tensor.shape[1]):
            text = ax.text(j, i, f'{metric_tensor[i, j]:.3f}',
                          ha="center", va="center", color="black", fontsize=9)

    ax.set_title(title)
    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight')
        plt.savefig(save_path.with_suffix('.png'), bbox_inches='tight')
        print(f"✓ Figure saved: {save_path}")

    plt.show()


def plot_comparison_multiple_methods(
    data_dict: Dict[str, np.ndarray],
    x_values: np.ndarray,
    xlabel: str,
    ylabel: str,
    title: str = "Method Comparison",
    save_path: Optional[str] = None
):
    """
    Plot comparison of multiple methods.

    Args:
        data_dict: Dictionary mapping method names to y-values
        x_values: X-axis values
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title
        save_path: Path to save figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, (method_name, y_values) in enumerate(data_dict.items()):
        ax.plot(x_values, y_values, marker='o', linewidth=2,
                color=COLORS[i % len(COLORS)], label=method_name)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight')
        plt.savefig(save_path.with_suffix('.png'), bbox_inches='tight')
        print(f"✓ Figure saved: {save_path}")

    plt.show()
