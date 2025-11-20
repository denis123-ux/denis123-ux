"""
Statistical validation tools for scientific rigor.

Includes confidence intervals, hypothesis testing, multiple testing
correction, and effect size calculations.
"""

import numpy as np
from scipy import stats
from typing import Tuple, Optional, Dict, Any


def compute_confidence_interval(
    data: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Compute confidence interval for the mean.

    Args:
        data: Array of observations
        confidence: Confidence level (default 0.95)

    Returns:
        (lower, upper) bounds of confidence interval
    """
    n = len(data)
    mean = np.mean(data)
    se = stats.sem(data)

    # Use t-distribution for small samples
    if n < 30:
        t_val = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin = t_val * se
    else:
        z_val = stats.norm.ppf((1 + confidence) / 2)
        margin = z_val * se

    return (mean - margin, mean + margin)


def compute_mean_with_ci(
    data: np.ndarray,
    confidence: float = 0.95
) -> Dict[str, float]:
    """
    Compute mean with confidence interval.

    Returns:
        Dictionary with 'mean', 'ci_lower', 'ci_upper', 'std', 'sem'
    """
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    se = stats.sem(data)
    ci_lower, ci_upper = compute_confidence_interval(data, confidence)

    return {
        'mean': mean,
        'std': std,
        'sem': se,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'n': len(data)
    }


def hypothesis_test_mean(
    data: np.ndarray,
    expected_value: float,
    alternative: str = 'two-sided'
) -> Dict[str, Any]:
    """
    Test if mean is significantly different from expected value.

    Args:
        data: Array of observations
        expected_value: Expected value under null hypothesis
        alternative: 'two-sided', 'greater', or 'less'

    Returns:
        Dictionary with 't_statistic', 'p_value', 'reject_null', 'effect_size'
    """
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    # t-test
    t_stat, p_value = stats.ttest_1samp(data, expected_value, alternative=alternative)

    # Cohen's d effect size
    effect_size = (mean - expected_value) / std

    # Reject null at alpha = 0.05
    reject_null = p_value < 0.05

    return {
        't_statistic': t_stat,
        'p_value': p_value,
        'reject_null': reject_null,
        'effect_size': effect_size,
        'mean': mean,
        'expected': expected_value,
        'std': std,
        'n': n
    }


def bonferroni_correction(
    p_values: np.ndarray,
    alpha: float = 0.05
) -> np.ndarray:
    """
    Apply Bonferroni correction for multiple testing.

    Args:
        p_values: Array of p-values
        alpha: Significance level

    Returns:
        Boolean array indicating which tests are significant
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests
    return p_values < corrected_alpha


def benjamini_hochberg_correction(
    p_values: np.ndarray,
    alpha: float = 0.05
) -> np.ndarray:
    """
    Apply Benjamini-Hochberg FDR correction.

    Args:
        p_values: Array of p-values
        alpha: False discovery rate

    Returns:
        Boolean array indicating which tests are significant
    """
    n_tests = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Find largest i such that P(i) <= (i/m) * alpha
    threshold_line = np.arange(1, n_tests + 1) / n_tests * alpha
    significant = sorted_p_values <= threshold_line

    if not np.any(significant):
        return np.zeros(n_tests, dtype=bool)

    max_significant_idx = np.where(significant)[0][-1]

    # All tests up to this index are significant
    result = np.zeros(n_tests, dtype=bool)
    result[sorted_indices[:max_significant_idx + 1]] = True

    return result


def kolmogorov_smirnov_test(
    data1: np.ndarray,
    data2: np.ndarray
) -> Dict[str, Any]:
    """
    Two-sample Kolmogorov-Smirnov test.

    Tests if two samples come from the same distribution.

    Returns:
        Dictionary with 'statistic', 'p_value', 'reject_null'
    """
    statistic, p_value = stats.ks_2samp(data1, data2)

    return {
        'statistic': statistic,
        'p_value': p_value,
        'reject_null': p_value < 0.05
    }


def bootstrap_confidence_interval(
    data: np.ndarray,
    statistic_func: callable = np.mean,
    n_bootstrap: int = 10000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Bootstrap confidence interval for any statistic.

    Args:
        data: Array of observations
        statistic_func: Function to compute statistic (default: mean)
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level

    Returns:
        (lower, upper) bounds of bootstrap CI
    """
    n = len(data)
    bootstrap_stats = np.zeros(n_bootstrap)

    for i in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats[i] = statistic_func(sample)

    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

    return (lower, upper)


def compute_effect_size_cohens_d(
    data1: np.ndarray,
    data2: np.ndarray
) -> float:
    """
    Compute Cohen's d effect size between two samples.

    Args:
        data1: First sample
        data2: Second sample

    Returns:
        Cohen's d (standardized mean difference)
    """
    mean1, mean2 = np.mean(data1), np.mean(data2)
    std1, std2 = np.std(data1, ddof=1), np.std(data2, ddof=1)

    n1, n2 = len(data1), len(data2)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    return (mean1 - mean2) / pooled_std


def check_normality(data: np.ndarray) -> Dict[str, Any]:
    """
    Check if data is normally distributed using multiple tests.

    Returns:
        Dictionary with test results
    """
    # Shapiro-Wilk test
    shapiro_stat, shapiro_p = stats.shapiro(data)

    # Anderson-Darling test
    anderson_result = stats.anderson(data)

    # Jarque-Bera test
    jb_stat, jb_p = stats.jarque_bera(data)

    return {
        'shapiro_wilk': {
            'statistic': shapiro_stat,
            'p_value': shapiro_p,
            'is_normal': shapiro_p > 0.05
        },
        'jarque_bera': {
            'statistic': jb_stat,
            'p_value': jb_p,
            'is_normal': jb_p > 0.05
        },
        'anderson_darling': {
            'statistic': anderson_result.statistic,
            'critical_values': anderson_result.critical_values,
            'significance_levels': anderson_result.significance_level
        }
    }


def convergence_test(
    sequence: np.ndarray,
    window_size: int = 10,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Test if a sequence has converged.

    Args:
        sequence: Array of values over iterations
        window_size: Size of window to check
        tolerance: Convergence tolerance

    Returns:
        Dictionary with convergence information
    """
    if len(sequence) < 2 * window_size:
        return {
            'converged': False,
            'reason': 'Insufficient data'
        }

    # Check last window for convergence
    last_window = sequence[-window_size:]
    mean_last = np.mean(last_window)
    std_last = np.std(last_window)

    # Relative change
    if abs(mean_last) > 1e-10:
        relative_change = std_last / abs(mean_last)
    else:
        relative_change = std_last

    converged = relative_change < tolerance

    # Check monotonicity (for optimization)
    diffs = np.diff(sequence)
    is_monotonic_increasing = np.all(diffs >= 0)
    is_monotonic_decreasing = np.all(diffs <= 0)

    return {
        'converged': converged,
        'relative_change': relative_change,
        'std_last_window': std_last,
        'mean_last_window': mean_last,
        'is_monotonic_increasing': is_monotonic_increasing,
        'is_monotonic_decreasing': is_monotonic_decreasing
    }


def pearson_correlation_test(
    x: np.ndarray,
    y: np.ndarray
) -> Dict[str, Any]:
    """
    Compute Pearson correlation with significance test.

    Args:
        x: First variable
        y: Second variable

    Returns:
        Dictionary with correlation coefficient and p-value
    """
    corr, p_value = stats.pearsonr(x, y)

    return {
        'correlation': corr,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'n': len(x)
    }


def linear_regression_with_uncertainty(
    x: np.ndarray,
    y: np.ndarray
) -> Dict[str, Any]:
    """
    Linear regression with full uncertainty quantification.

    Args:
        x: Independent variable
        y: Dependent variable

    Returns:
        Dictionary with slope, intercept, R², and uncertainties
    """
    from scipy.stats import linregress

    result = linregress(x, y)

    # Predictions and residuals
    y_pred = result.slope * x + result.intercept
    residuals = y - y_pred

    # Sum of squares
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y))**2)

    # R-squared
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return {
        'slope': result.slope,
        'intercept': result.intercept,
        'r_squared': r_squared,
        'p_value': result.pvalue,
        'std_err_slope': result.stderr,
        'std_err_intercept': result.intercept_stderr,
        'residuals': residuals,
        'rmse': np.sqrt(np.mean(residuals**2))
    }
