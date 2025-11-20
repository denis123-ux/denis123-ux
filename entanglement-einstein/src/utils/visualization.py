"""
Publication-Quality Visualization
==================================

Creates publication-ready plots for scientific papers:
- Area law fits with confidence intervals
- Metric tensor heatmaps
- Curvature visualizations
- Convergence plots
- Error analysis

All plots follow Nature/Science style guidelines.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import matplotlib as mpl

# Set publication-quality defaults
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'lines.linewidth': 1.5,
    'axes.grid': True,
    'grid.alpha': 0.3
})


class PublicationPlot:
    """Helper class for creating publication-quality plots."""

    def __init__(self, style: str = 'default'):
        """
        Initialize plot style.

        Parameters
        ----------
        style : str
            'default', 'dark', 'minimal'
        """
        if style == 'dark':
            plt.style.use('dark_background')
        elif style == 'minimal':
            sns.set_style('whitegrid')
        else:
            sns.set_style('darkgrid')

    @staticmethod
    def save(fig, path: Path, formats: List[str] = ['pdf', 'png']):
        """Save figure in multiple formats."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        for fmt in formats:
            output_path = path.with_suffix(f'.{fmt}')
            fig.savefig(output_path, format=fmt, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")


def plot_area_law_fit(
    results_df,
    theoretical_slope: Optional[float] = None,
    save_path: Optional[Path] = None,
    show_ci: bool = True
) -> plt.Figure:
    """
    Plot area law verification with fits and confidence intervals.

    Parameters
    ----------
    results_df : DataFrame
        Results with columns: ['size', 'boundary', 'S_EE', 'd_bond', 'seed']
    theoretical_slope : float, optional
        Theoretical prediction for slope (e.g., c/3)
    save_path : Path, optional
        Where to save figure
    show_ci : bool
        Show confidence intervals

    Returns
    -------
    Figure
    """
    from scipy.stats import linregress
    import pandas as pd

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Area Law Verification for Entanglement Entropy', fontsize=14, y=0.995)

    # Get unique bond dimensions
    d_bonds = sorted(results_df['d_bond'].unique())
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(d_bonds)))

    # Panel 1: S(A) vs log(boundary) for different d_bond
    ax1 = axes[0, 0]
    for i, d_bond in enumerate(d_bonds):
        subset = results_df[results_df['d_bond'] == d_bond]

        # Aggregate by size
        grouped = subset.groupby('boundary').agg({
            'S_EE': ['mean', 'std']
        }).reset_index()

        boundaries = grouped['boundary'].values
        S_mean = grouped['S_EE']['mean'].values
        S_std = grouped['S_EE']['std'].values

        log_boundary = np.log(boundaries)

        ax1.errorbar(log_boundary, S_mean, yerr=S_std if show_ci else None,
                    fmt='o', label=f'd_bond={d_bond}', color=colors[i],
                    markersize=6, capsize=3, alpha=0.7)

        # Fit line
        slope, intercept, r, p, se = linregress(log_boundary, S_mean)
        fit_line = slope * log_boundary + intercept
        ax1.plot(log_boundary, fit_line, '-', color=colors[i], alpha=0.5,
                linewidth=1.5)

    if theoretical_slope is not None:
        # Show theoretical prediction
        log_b_range = ax1.get_xlim()
        log_b_theory = np.linspace(*log_b_range, 100)
        # Fit intercept from data
        S_theory = theoretical_slope * log_b_theory
        S_theory -= np.mean(S_theory) - np.mean(ax1.get_ylim())
        ax1.plot(log_b_theory, S_theory, 'k--', linewidth=2,
                label=f'Theory: slope={theoretical_slope:.3f}', alpha=0.7)

    ax1.set_xlabel('log(Boundary Size)')
    ax1.set_ylabel('Entanglement Entropy S(A)')
    ax1.set_title('Area Law: S(A) ~ log(∂A)')
    ax1.legend(framealpha=0.9, loc='best')
    ax1.grid(True, alpha=0.3)

    # Panel 2: R² vs d_bond (convergence)
    ax2 = axes[0, 1]
    r_squared_values = []
    for d_bond in d_bonds:
        subset = results_df[results_df['d_bond'] == d_bond]
        grouped = subset.groupby('boundary').agg({'S_EE': 'mean'}).reset_index()

        log_boundary = np.log(grouped['boundary'].values)
        S_mean = grouped['S_EE'].values

        slope, intercept, r, p, se = linregress(log_boundary, S_mean)
        r_squared_values.append(r**2)

    ax2.plot(d_bonds, r_squared_values, 'o-', markersize=8, linewidth=2, color='darkblue')
    ax2.axhline(0.99, color='red', linestyle='--', linewidth=1.5, label='Target R²=0.99')
    ax2.set_xlabel('Bond Dimension d_bond')
    ax2.set_ylabel('R² (Goodness of Fit)')
    ax2.set_title('Convergence with Bond Dimension')
    ax2.set_xscale('log')
    ax2.set_ylim([0.9, 1.0])
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Panel 3: Slope vs d_bond (should converge to theoretical value)
    ax3 = axes[1, 0]
    slopes = []
    slope_errors = []
    for d_bond in d_bonds:
        subset = results_df[results_df['d_bond'] == d_bond]
        grouped = subset.groupby('boundary').agg({'S_EE': 'mean'}).reset_index()

        log_boundary = np.log(grouped['boundary'].values)
        S_mean = grouped['S_EE'].values

        slope, intercept, r, p, se = linregress(log_boundary, S_mean)
        slopes.append(slope)
        slope_errors.append(se)

    ax3.errorbar(d_bonds, slopes, yerr=slope_errors, fmt='o-', markersize=8,
                linewidth=2, capsize=5, color='darkgreen')

    if theoretical_slope is not None:
        ax3.axhline(theoretical_slope, color='red', linestyle='--', linewidth=1.5,
                   label=f'Theory: {theoretical_slope:.4f}')
        ax3.fill_between(ax3.get_xlim(),
                        theoretical_slope * 0.95, theoretical_slope * 1.05,
                        alpha=0.2, color='red', label='±5% error')

    ax3.set_xlabel('Bond Dimension d_bond')
    ax3.set_ylabel('Fitted Slope')
    ax3.set_title('Slope Convergence to c/3')
    ax3.set_xscale('log')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Panel 4: Residuals analysis
    ax4 = axes[1, 1]
    # Use highest bond dimension for residuals
    d_bond_max = max(d_bonds)
    subset = results_df[results_df['d_bond'] == d_bond_max]
    grouped = subset.groupby('boundary').agg({'S_EE': 'mean'}).reset_index()

    log_boundary = np.log(grouped['boundary'].values)
    S_mean = grouped['S_EE'].values

    slope, intercept, r, p, se = linregress(log_boundary, S_mean)
    S_fit = slope * log_boundary + intercept
    residuals = S_mean - S_fit

    ax4.scatter(log_boundary, residuals, s=50, alpha=0.7, color='purple')
    ax4.axhline(0, color='black', linestyle='-', linewidth=1)
    ax4.axhline(2*se, color='red', linestyle='--', linewidth=1, alpha=0.5, label='±2σ')
    ax4.axhline(-2*se, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax4.set_xlabel('log(Boundary Size)')
    ax4.set_ylabel('Residuals')
    ax4.set_title(f'Residuals (d_bond={d_bond_max})')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        PublicationPlot.save(fig, save_path)

    return fig


def plot_convergence_analysis(
    d_bonds: List[int],
    errors: List[float],
    error_type: str = 'Einstein equations',
    save_path: Optional[Path] = None
) -> plt.Figure:
    """
    Plot convergence analysis vs bond dimension.

    Parameters
    ----------
    d_bonds : list
        Bond dimensions
    errors : list
        Error values
    error_type : str
        Type of error being measured
    save_path : Path, optional
        Where to save

    Returns
    -------
    Figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Linear plot
    ax1.semilogy(d_bonds, errors, 'o-', markersize=8, linewidth=2, color='darkred')
    ax1.set_xlabel('Bond Dimension d_bond')
    ax1.set_ylabel(f'Error: {error_type}')
    ax1.set_title('Convergence Analysis (Linear Scale)')
    ax1.grid(True, alpha=0.3)

    # Log-log plot (power law fit)
    ax2.loglog(d_bonds, errors, 'o', markersize=8, label='Data')

    # Fit power law: error ~ d_bond^(-α)
    from scipy.stats import linregress
    log_d = np.log(d_bonds)
    log_err = np.log(errors)
    slope, intercept, r, p, se = linregress(log_d, log_err)

    fit_d = np.array(d_bonds)
    fit_err = np.exp(intercept) * fit_d**slope

    ax2.loglog(fit_d, fit_err, '--', linewidth=2, color='blue',
              label=f'Fit: ∝ d^({slope:.2f}), R²={r**2:.4f}')

    ax2.set_xlabel('Bond Dimension d_bond')
    ax2.set_ylabel(f'Error: {error_type}')
    ax2.set_title('Convergence Analysis (Log-Log)')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both')

    plt.tight_layout()

    if save_path:
        PublicationPlot.save(fig, save_path)

    return fig


def plot_metric_tensor(
    metric: np.ndarray,
    title: str = 'Metric Tensor g_μν',
    save_path: Optional[Path] = None
) -> plt.Figure:
    """
    Visualize metric tensor as heatmap.

    Parameters
    ----------
    metric : ndarray, shape (d, d)
        Metric tensor
    title : str
        Plot title
    save_path : Path, optional
        Where to save

    Returns
    -------
    Figure
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    im = ax.imshow(metric, cmap='RdBu_r', aspect='auto')
    ax.set_title(title)
    ax.set_xlabel('ν')
    ax.set_ylabel('μ')

    # Add grid
    ax.set_xticks(np.arange(len(metric)))
    ax.set_yticks(np.arange(len(metric)))
    ax.grid(False)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('g_μν', rotation=270, labelpad=20)

    # Annotate values
    for i in range(len(metric)):
        for j in range(len(metric)):
            text = ax.text(j, i, f'{metric[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)

    plt.tight_layout()

    if save_path:
        PublicationPlot.save(fig, save_path)

    return fig


def plot_experimental_timeline(
    logger_data: Dict[str, Any],
    save_path: Optional[Path] = None
) -> plt.Figure:
    """
    Create timeline visualization of experimental progress.

    Parameters
    ----------
    logger_data : dict
        Data from AutoLogger
    save_path : Path, optional
        Where to save

    Returns
    -------
    Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    successes = logger_data.get('successes', [])
    failures = logger_data.get('failures', [])

    # Parse timestamps and plot
    from datetime import datetime

    for i, item in enumerate(successes):
        timestamp = datetime.fromisoformat(item['timestamp'])
        ax.scatter(timestamp, 1, color='green', s=100, marker='o', alpha=0.7)
        ax.text(timestamp, 1.1, f"✓ {item['message'][:30]}...",
               rotation=45, ha='right', fontsize=8)

    for i, item in enumerate(failures):
        timestamp = datetime.fromisoformat(item['timestamp'])
        ax.scatter(timestamp, 0, color='red', s=100, marker='x', alpha=0.7)
        ax.text(timestamp, -0.1, f"✗ {item['message'][:30]}...",
               rotation=45, ha='right', fontsize=8)

    ax.set_ylim([-0.5, 1.5])
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Failures', 'Successes'])
    ax.set_xlabel('Time')
    ax.set_title('Experimental Timeline')
    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_path:
        PublicationPlot.save(fig, save_path)

    return fig
