"""
Statistical Validation Framework
=================================

Rigorous statistical methods for hypothesis testing:
- Confidence intervals (parametric & bootstrap)
- Multiple testing correction (Bonferroni, FDR)
- Effect size calculations (Cohen's d, eta-squared)
- Normality tests
- Power analysis
"""

import numpy as np
from scipy import stats
from typing import Tuple, Optional, Union, List
import warnings


def compute_confidence_interval(
    data: np.ndarray,
    confidence: float = 0.95,
    method: str = 'normal'
) -> Tuple[float, float]:
    """
    Compute confidence interval for the mean.

    Parameters
    ----------
    data : array_like
        Sample data
    confidence : float, default 0.95
        Confidence level (0-1)
    method : str, default 'normal'
        Method: 'normal' (t-test) or 'bootstrap'

    Returns
    -------
    Tuple[float, float]
        (lower_bound, upper_bound) of CI

    Examples
    --------
    >>> data = np.random.normal(0, 1, 100)
    >>> ci = compute_confidence_interval(data, 0.95)
    >>> print(f"95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]")
    """
    data = np.asarray(data)

    if method == 'normal':
        # Parametric CI using t-distribution
        mean = np.mean(data)
        sem = stats.sem(data)  # Standard error of mean
        n = len(data)

        # t-statistic for confidence level
        alpha = 1 - confidence
        t_crit = stats.t.ppf(1 - alpha/2, n - 1)

        margin = t_crit * sem
        return (mean - margin, mean + margin)

    elif method == 'bootstrap':
        return bootstrap_ci(data, confidence)

    else:
        raise ValueError(f"Unknown method: {method}")


def bootstrap_ci(
    data: np.ndarray,
    confidence: float = 0.95,
    n_bootstrap: int = 10000,
    statistic=np.mean,
    random_state: Optional[int] = None
) -> Tuple[float, float]:
    """
    Bootstrap confidence interval for arbitrary statistic.

    Parameters
    ----------
    data : array_like
        Sample data
    confidence : float
        Confidence level
    n_bootstrap : int
        Number of bootstrap samples
    statistic : callable
        Function to compute statistic (default: mean)
    random_state : int, optional
        Random seed for reproducibility

    Returns
    -------
    Tuple[float, float]
        (lower_bound, upper_bound) of CI
    """
    if random_state is not None:
        np.random.seed(random_state)

    data = np.asarray(data)
    n = len(data)

    # Bootstrap resampling
    bootstrap_stats = np.zeros(n_bootstrap)
    for i in range(n_bootstrap):
        resample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats[i] = statistic(resample)

    # Percentile method
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, alpha/2 * 100)
    upper = np.percentile(bootstrap_stats, (1 - alpha/2) * 100)

    return (lower, upper)


def bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[bool], float]:
    """
    Bonferroni correction for multiple testing.

    Parameters
    ----------
    p_values : list of float
        List of p-values from multiple tests
    alpha : float
        Family-wise error rate (FWER)

    Returns
    -------
    Tuple[List[bool], float]
        (reject_list, corrected_alpha)
        reject_list[i] = True if null hypothesis i should be rejected

    Examples
    --------
    >>> p_values = [0.01, 0.03, 0.04, 0.50]
    >>> reject, alpha_corr = bonferroni_correction(p_values, 0.05)
    >>> print(f"Corrected alpha: {alpha_corr}")
    >>> print(f"Reject: {reject}")
    """
    n_tests = len(p_values)
    alpha_corrected = alpha / n_tests

    reject = [p < alpha_corrected for p in p_values]

    return reject, alpha_corrected


def fdr_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[bool], List[float]]:
    """
    Benjamini-Hochberg FDR (False Discovery Rate) correction.

    Less conservative than Bonferroni for many tests.

    Parameters
    ----------
    p_values : list of float
        P-values from multiple tests
    alpha : float
        Desired FDR level

    Returns
    -------
    Tuple[List[bool], List[float]]
        (reject_list, adjusted_p_values)
    """
    p_values = np.asarray(p_values)
    n = len(p_values)

    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # BH threshold
    thresholds = alpha * np.arange(1, n + 1) / n

    # Find largest i where p[i] <= threshold[i]
    reject_sorted = sorted_p <= thresholds
    if np.any(reject_sorted):
        max_i = np.where(reject_sorted)[0][-1]
        reject = np.zeros(n, dtype=bool)
        reject[sorted_indices[:max_i + 1]] = True
    else:
        reject = np.zeros(n, dtype=bool)

    # Adjusted p-values
    adjusted_p = np.minimum(1, sorted_p * n / np.arange(1, n + 1))
    # Enforce monotonicity
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])

    # Restore original order
    adjusted_p_original = np.zeros(n)
    adjusted_p_original[sorted_indices] = adjusted_p

    return list(reject), list(adjusted_p_original)


def compute_effect_size(
    group1: np.ndarray,
    group2: np.ndarray,
    method: str = 'cohen_d'
) -> float:
    """
    Compute effect size between two groups.

    Parameters
    ----------
    group1, group2 : array_like
        Two groups to compare
    method : str
        'cohen_d': Cohen's d (standardized mean difference)
        'hedges_g': Hedges' g (corrected for small samples)
        'glass_delta': Glass's delta (use SD of group2)

    Returns
    -------
    float
        Effect size

    Examples
    --------
    >>> group1 = np.random.normal(0, 1, 100)
    >>> group2 = np.random.normal(0.5, 1, 100)
    >>> d = compute_effect_size(group1, group2)
    >>> print(f"Cohen's d = {d:.3f}")
    """
    group1 = np.asarray(group1)
    group2 = np.asarray(group2)

    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)

    if method == 'cohen_d':
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        return (mean1 - mean2) / pooled_std

    elif method == 'hedges_g':
        # Cohen's d with correction factor
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        d = (mean1 - mean2) / pooled_std
        # Correction factor for small samples
        correction = 1 - 3 / (4 * (n1 + n2) - 9)
        return d * correction

    elif method == 'glass_delta':
        # Use SD of group2 (control)
        return (mean1 - mean2) / std2

    else:
        raise ValueError(f"Unknown method: {method}")


def check_normality(
    data: np.ndarray,
    alpha: float = 0.05,
    method: str = 'shapiro'
) -> Tuple[bool, float]:
    """
    Test if data is normally distributed.

    Parameters
    ----------
    data : array_like
        Sample data
    alpha : float
        Significance level
    method : str
        'shapiro': Shapiro-Wilk test
        'anderson': Anderson-Darling test
        'ks': Kolmogorov-Smirnov test

    Returns
    -------
    Tuple[bool, float]
        (is_normal, p_value)

    Examples
    --------
    >>> data = np.random.normal(0, 1, 100)
    >>> is_normal, p = check_normality(data)
    >>> print(f"Normal? {is_normal} (p={p:.4f})")
    """
    data = np.asarray(data)

    if method == 'shapiro':
        statistic, p_value = stats.shapiro(data)
        is_normal = p_value > alpha
        return is_normal, p_value

    elif method == 'anderson':
        result = stats.anderson(data, dist='norm')
        # Critical values for significance levels [15%, 10%, 5%, 2.5%, 1%]
        # Use 5% level (index 2)
        critical_value = result.critical_values[2]
        is_normal = result.statistic < critical_value
        # Approximate p-value (not exact for Anderson-Darling)
        p_value = 0.05 if is_normal else 0.01
        return is_normal, p_value

    elif method == 'ks':
        # Fit normal distribution to data
        mu, sigma = np.mean(data), np.std(data, ddof=1)
        statistic, p_value = stats.kstest(data, 'norm', args=(mu, sigma))
        is_normal = p_value > alpha
        return is_normal, p_value

    else:
        raise ValueError(f"Unknown method: {method}")


def eta_squared(
    groups: List[np.ndarray]
) -> float:
    """
    Compute eta-squared (effect size for ANOVA).

    Parameters
    ----------
    groups : list of array_like
        List of groups for ANOVA

    Returns
    -------
    float
        Eta-squared (proportion of variance explained)

    Examples
    --------
    >>> group1 = np.random.normal(0, 1, 30)
    >>> group2 = np.random.normal(0.5, 1, 30)
    >>> group3 = np.random.normal(1, 1, 30)
    >>> eta2 = eta_squared([group1, group2, group3])
    >>> print(f"η² = {eta2:.3f}")
    """
    # Flatten all data
    all_data = np.concatenate([np.asarray(g) for g in groups])
    grand_mean = np.mean(all_data)

    # Between-group sum of squares
    ss_between = sum(
        len(g) * (np.mean(g) - grand_mean)**2
        for g in groups
    )

    # Total sum of squares
    ss_total = np.sum((all_data - grand_mean)**2)

    # Eta-squared
    return ss_between / ss_total if ss_total > 0 else 0.0


def power_analysis(
    effect_size: float,
    n: int,
    alpha: float = 0.05,
    alternative: str = 'two-sided'
) -> float:
    """
    Compute statistical power for t-test.

    Parameters
    ----------
    effect_size : float
        Cohen's d
    n : int
        Sample size per group
    alpha : float
        Significance level
    alternative : str
        'two-sided' or 'one-sided'

    Returns
    -------
    float
        Statistical power (0-1)

    Examples
    --------
    >>> power = power_analysis(effect_size=0.5, n=50, alpha=0.05)
    >>> print(f"Power = {power:.2%}")
    """
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n / 2)

    # Degrees of freedom
    df = 2 * n - 2

    # Critical t-value
    if alternative == 'two-sided':
        t_crit = stats.t.ppf(1 - alpha/2, df)
    else:
        t_crit = stats.t.ppf(1 - alpha, df)

    # Power = P(reject H0 | H1 is true)
    # Use non-central t distribution
    if alternative == 'two-sided':
        power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    else:
        power = 1 - stats.nct.cdf(t_crit, df, ncp)

    return power


def sample_size_for_power(
    effect_size: float,
    power: float = 0.8,
    alpha: float = 0.05,
    alternative: str = 'two-sided'
) -> int:
    """
    Compute required sample size per group for desired power.

    Parameters
    ----------
    effect_size : float
        Cohen's d
    power : float
        Desired power (default 0.8)
    alpha : float
        Significance level
    alternative : str
        'two-sided' or 'one-sided'

    Returns
    -------
    int
        Required sample size per group

    Examples
    --------
    >>> n = sample_size_for_power(effect_size=0.5, power=0.8)
    >>> print(f"Required n per group: {n}")
    """
    # Binary search for sample size
    n_low, n_high = 2, 10000
    target_power = power

    while n_low < n_high - 1:
        n_mid = (n_low + n_high) // 2
        current_power = power_analysis(effect_size, n_mid, alpha, alternative)

        if current_power < target_power:
            n_low = n_mid
        else:
            n_high = n_mid

    return n_high
