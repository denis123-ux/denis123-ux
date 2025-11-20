"""
Visualization tools for publication-quality plots.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict, Any, List
from pathlib import Path
import pandas as pd


# Set publication-quality defaults
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.5)
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Computer Modern Roman']
plt.rcParams['text.usetex'] = False  # Set to True if LaTeX is available


def plot_area_law_fit(
    results_df: pd.DataFrame,
    theoretical_slope: float,
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot area law verification with fits.

    Args:
        results_df: DataFrame with columns ['d_bond', 'slope', 'r_squared']
        theoretical_slope: Theoretical c/3 value
        save_path: Path to save figure
        show: Whether to display the plot
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Slope vs bond dimension
    ax1 = axes[0]

    for d_bond in results_df['d_bond'].unique():
        subset = results_df[results_df['d_bond'] == d_bond]
        slopes = subset['slope'].values

        ax1.scatter(
            [d_bond] * len(slopes),
            slopes,
            alpha=0.3,
            s=20,
            label=f'd_bond={d_bond}'
        )

        # Plot mean and error bars
        mean_slope = slopes.mean()
        std_slope = slopes.std()
        ax1.errorbar(
            d_bond,
            mean_slope,
            yerr=std_slope,
            fmt='o',
            markersize=10,
            capsize=5,
            capthick=2
        )

    # Theoretical value
    ax1.axhline(
        theoretical_slope,
        color='red',
        linestyle='--',
        linewidth=2,
        label=f'Theory: c/3 = {theoretical_slope:.4f}'
    )

    ax1.set_xlabel('Bond Dimension')
    ax1.set_ylabel('Fitted Slope')
    ax1.set_title('Area Law: Slope Convergence')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: R² vs bond dimension
    ax2 = axes[1]

    for d_bond in results_df['d_bond'].unique():
        subset = results_df[results_df['d_bond'] == d_bond]
        r2_values = subset['r_squared'].values

        ax2.scatter(
            [d_bond] * len(r2_values),
            r2_values,
            alpha=0.3,
            s=20
        )

        # Plot mean
        mean_r2 = r2_values.mean()
        std_r2 = r2_values.std()
        ax2.errorbar(
            d_bond,
            mean_r2,
            yerr=std_r2,
            fmt='o',
            markersize=10,
            capsize=5,
            capthick=2
        )

    # Threshold line
    ax2.axhline(
        0.99,
        color='green',
        linestyle='--',
        linewidth=2,
        label='Target: R² > 0.99'
    )

    ax2.set_xlabel('Bond Dimension')
    ax2.set_ylabel('R² Value')
    ax2.set_title('Fit Quality')
    ax2.set_ylim([0.95, 1.0])
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"[Visualization] Saved: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_entanglement_entropy_vs_size(
    sizes: np.ndarray,
    entropies: np.ndarray,
    fit_params: Optional[Dict[str, float]] = None,
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot entanglement entropy vs subsystem size with fit.

    Args:
        sizes: Array of subsystem sizes
        entropies: Corresponding entanglement entropies
        fit_params: Dictionary with 'slope', 'intercept', 'r_squared'
        save_path: Path to save figure
        show: Whether to display the plot
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Data points
    ax.scatter(sizes, entropies, s=50, alpha=0.6, label='Computed S(A)')

    # Fit line if provided
    if fit_params:
        log_sizes = np.log(sizes)
        fit_line = fit_params['slope'] * log_sizes + fit_params['intercept']
        ax.plot(sizes, fit_line, 'r--', linewidth=2,
                label=f"Fit: S = {fit_params['slope']:.4f} log(L) + {fit_params['intercept']:.2f}\n"
                      f"R² = {fit_params['r_squared']:.5f}")

    ax.set_xlabel('Subsystem Size')
    ax.set_ylabel('Entanglement Entropy S(A)')
    ax.set_title('Area Law Verification')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"[Visualization] Saved: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_convergence_history(
    history: List[float],
    ylabel: str = "Value",
    title: str = "Convergence History",
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot optimization convergence history.

    Args:
        history: List of values over iterations
        ylabel: Y-axis label
        title: Plot title
        save_path: Path to save figure
        show: Whether to display the plot
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    iterations = np.arange(len(history))
    ax.plot(iterations, history, linewidth=2)

    ax.set_xlabel('Iteration')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    # Add exponential fit for convergence rate
    if len(history) > 10:
        try:
            from scipy.optimize import curve_fit

            def exp_decay(x, a, b, c):
                return a * np.exp(-b * x) + c

            popt, _ = curve_fit(
                exp_decay,
                iterations[-len(history)//2:],
                history[-len(history)//2:],
                maxfev=5000
            )

            fit_vals = exp_decay(iterations, *popt)
            ax.plot(iterations, fit_vals, 'r--', linewidth=2,
                   label=f'Exponential fit: rate = {popt[1]:.4f}')
            ax.legend()
        except:
            pass

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"[Visualization] Saved: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_method_comparison(
    method_names: List[str],
    values: List[np.ndarray],
    ylabel: str = "Value",
    title: str = "Method Comparison",
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot comparison of different methods with error bars.

    Args:
        method_names: Names of methods
        values: List of arrays of values for each method
        ylabel: Y-axis label
        title: Plot title
        save_path: Path to save figure
        show: Whether to display the plot
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    means = [np.mean(v) for v in values]
    stds = [np.std(v) for v in values]

    x_pos = np.arange(len(method_names))

    bars = ax.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(method_names, rotation=45, ha='right')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for i, (mean, std) in enumerate(zip(means, stds)):
        ax.text(i, mean + std, f'{mean:.4f}\n±{std:.4f}',
               ha='center', va='bottom', fontsize=10)

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"[Visualization] Saved: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_continuum_extrapolation(
    bond_dims: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    theoretical_value: Optional[float] = None,
    ylabel: str = "Value",
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot continuum limit extrapolation.

    Args:
        bond_dims: Array of bond dimensions
        values: Corresponding values
        errors: Error bars
        theoretical_value: Theoretical continuum value
        ylabel: Y-axis label
        save_path: Path to save figure
        show: Whether to display the plot
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data
    ax.errorbar(
        1.0 / bond_dims,
        values,
        yerr=errors,
        fmt='o',
        markersize=10,
        capsize=5,
        capthick=2,
        label='Computed values'
    )

    # Fit to 1/d form
    try:
        from scipy.optimize import curve_fit

        def power_law(x, a, b):
            return a * x + b

        popt, pcov = curve_fit(power_law, 1.0 / bond_dims, values, sigma=errors)

        x_fit = np.linspace(0, 1.0 / bond_dims.min(), 100)
        y_fit = power_law(x_fit, *popt)

        ax.plot(x_fit, y_fit, 'r--', linewidth=2,
               label=f'Fit: y = {popt[0]:.4f}/d + {popt[1]:.4f}\n'
                     f'Continuum (d→∞): {popt[1]:.4f}')

        # Extrapolated value
        extrapolated = popt[1]
        ax.axhline(extrapolated, color='red', linestyle=':', linewidth=2)

    except:
        print("[Visualization] Warning: Could not fit continuum extrapolation")

    # Theoretical value
    if theoretical_value is not None:
        ax.axhline(theoretical_value, color='green', linestyle='--',
                  linewidth=2, label=f'Theory: {theoretical_value:.4f}')

    ax.set_xlabel('1 / Bond Dimension')
    ax.set_ylabel(ylabel)
    ax.set_title('Continuum Limit Extrapolation')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"[Visualization] Saved: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()
