"""
Statistical validation framework for quantum gravity research.

Implements rigorous statistical methods:
- Confidence intervals (bootstrap, parametric)
- Hypothesis testing (t-tests, ANOVA)
- Multiple testing correction (Bonferroni, FDR)
- Effect size calculation
- Power analysis
"""

import numpy as np
from scipy import stats
from typing import Tuple, Optional, List, Dict, Any
import warnings


def compute_confidence_interval(
    data: np.ndarray,
    confidence: float = 0.95,
    method: str = 'bootstrap',
    n_bootstrap: int = 10000
) -> Tuple[float, float]:
    """
    Compute confidence interval for data.

    Args:
        data: 1D array of data points
        confidence: Confidence level (default 0.95 for 95% CI)
        method: 'bootstrap' or 'parametric'
        n_bootstrap: Number of bootstrap samples

    Returns:
        (mean, lower_bound, upper_bound)
    """
    data = np.asarray(data)
    mean = np.mean(data)

    if method == 'parametric':
        # Parametric CI assuming normal distribution
        sem = stats.sem(data)
        ci = stats.t.interval(confidence, len(data)-1, loc=mean, scale=sem)
        return ci[1] - mean  # Return half-width

    elif method == 'bootstrap':
        # Non-parametric bootstrap CI
        bootstrap_means = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(data, size=len(data), replace=True)
            bootstrap_means.append(np.mean(sample))

        bootstrap_means = np.array(bootstrap_means)
        alpha = 1 - confidence
        ci = np.percentile(bootstrap_means, [100*alpha/2, 100*(1-alpha/2)])
        return ci[1] - mean  # Return half-width

    else:
        raise ValueError(f"Unknown method: {method}")


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], float]:
    """
    Apply Bonferroni correction for multiple comparisons.

    Args:
        p_values: List of p-values
        alpha: Family-wise error rate

    Returns:
        (reject_list, corrected_alpha)
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests

    reject = [p < corrected_alpha for p in p_values]

    return reject, corrected_alpha


def false_discovery_rate(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction.

    Args:
        p_values: List of p-values
        alpha: False discovery rate

    Returns:
        List of booleans indicating rejection
    """
    p_values = np.array(p_values)
    n = len(p_values)

    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Find largest i where p(i) <= (i/n) * alpha
    threshold_line = np.arange(1, n+1) / n * alpha
    below_threshold = sorted_p <= threshold_line

    if not np.any(below_threshold):
        return [False] * n

    # Find largest i
    k = np.where(below_threshold)[0][-1]

    # Reject all hypotheses up to k
    reject = np.zeros(n, dtype=bool)
    reject[sorted_indices[:k+1]] = True

    return reject.tolist()


def cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.

    Args:
        group1: First group data
        group2: Second group data

    Returns:
        Cohen's d (standardized mean difference)
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)

    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1 + n2 - 2))

    d = (mean1 - mean2) / pooled_std
    return d


def bayesian_t_test(
    group1: np.ndarray,
    group2: np.ndarray,
    prior_scale: float = 1.0
) -> Dict[str, float]:
    """
    Bayesian t-test using BIC approximation.

    Args:
        group1: First group data
        group2: Second group data
        prior_scale: Scale of Cauchy prior

    Returns:
        Dictionary with Bayes factor and posterior odds
    """
    # Classical t-test
    t_stat, p_value = stats.ttest_ind(group1, group2)

    n1, n2 = len(group1), len(group2)
    n = n1 + n2

    # BIC approximation for Bayes factor
    # BF10 = exp((BIC0 - BIC1) / 2)
    # Simplified approximation
    bf10 = np.sqrt(n) * np.exp(-t_stat**2 / 2)

    return {
        'bayes_factor_10': bf10,
        'bayes_factor_01': 1/bf10,
        'p_value': p_value,
        't_statistic': t_stat
    }


def linear_regression_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    confidence: float = 0.95
) -> Dict[str, Any]:
    """
    Linear regression with complete statistical analysis.

    Args:
        x: Independent variable
        y: Dependent variable
        confidence: Confidence level for intervals

    Returns:
        Dictionary with slope, intercept, R², p-values, and CIs
    """
    from scipy.stats import linregress

    # Perform regression
    slope, intercept, r_value, p_value, std_err = linregress(x, y)

    # Compute confidence intervals
    n = len(x)
    t_crit = stats.t.ppf((1 + confidence) / 2, n - 2)

    # Prediction
    y_pred = slope * x + intercept
    residuals = y - y_pred
    mse = np.sum(residuals**2) / (n - 2)

    # Standard errors
    x_mean = np.mean(x)
    sxx = np.sum((x - x_mean)**2)
    se_slope = np.sqrt(mse / sxx)
    se_intercept = np.sqrt(mse * (1/n + x_mean**2/sxx))

    # Confidence intervals
    slope_ci = (slope - t_crit*se_slope, slope + t_crit*se_slope)
    intercept_ci = (intercept - t_crit*se_intercept, intercept + t_crit*se_intercept)

    # Adjusted R²
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_squared_adj = 1 - (ss_res/(n-2)) / (ss_tot/(n-1))

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'r_squared_adjusted': r_squared_adj,
        'p_value': p_value,
        'std_err_slope': se_slope,
        'std_err_intercept': se_intercept,
        'slope_ci': slope_ci,
        'intercept_ci': intercept_ci,
        'residuals': residuals,
        'predictions': y_pred
    }


def check_normality(data: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Test normality assumption using Shapiro-Wilk test.

    Args:
        data: Data to test
        alpha: Significance level

    Returns:
        Dictionary with test results
    """
    stat, p_value = stats.shapiro(data)

    return {
        'test': 'Shapiro-Wilk',
        'statistic': stat,
        'p_value': p_value,
        'is_normal': p_value > alpha,
        'message': 'Data is normal' if p_value > alpha else 'Data is NOT normal'
    }


def check_heteroscedasticity(residuals: np.ndarray, predicted: np.ndarray) -> Dict[str, Any]:
    """
    Check for heteroscedasticity (non-constant variance).

    Args:
        residuals: Regression residuals
        predicted: Predicted values

    Returns:
        Dictionary with test results
    """
    # Breusch-Pagan test approximation
    # Regress squared residuals on predicted values
    residuals_sq = residuals**2
    corr = np.corrcoef(residuals_sq, predicted)[0, 1]

    return {
        'correlation': corr,
        'warning': abs(corr) > 0.3,
        'message': 'Possible heteroscedasticity' if abs(corr) > 0.3 else 'No strong heteroscedasticity'
    }


def compute_effect_size_and_power(
    observed_effect: float,
    std_dev: float,
    n_samples: int,
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Compute effect size and statistical power.

    Args:
        observed_effect: Observed effect size (e.g., mean difference)
        std_dev: Standard deviation
        n_samples: Sample size
        alpha: Significance level

    Returns:
        Dictionary with effect size and power
    """
    # Standardized effect size
    cohens_d = observed_effect / std_dev

    # Statistical power (approximate)
    from scipy.stats import norm
    z_alpha = norm.ppf(1 - alpha/2)
    z_beta = np.sqrt(n_samples) * abs(cohens_d) - z_alpha
    power = norm.cdf(z_beta)

    return {
        'cohens_d': cohens_d,
        'effect_size_interpretation': _interpret_cohens_d(cohens_d),
        'power': power,
        'power_interpretation': 'Adequate' if power > 0.8 else 'Inadequate'
    }


def _interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d effect size."""
    d = abs(d)
    if d < 0.2:
        return 'negligible'
    elif d < 0.5:
        return 'small'
    elif d < 0.8:
        return 'medium'
    else:
        return 'large'


def cross_validation_score(
    x: np.ndarray,
    y: np.ndarray,
    n_folds: int = 5,
    metric: str = 'r2'
) -> Dict[str, Any]:
    """
    K-fold cross-validation for linear regression.

    Args:
        x: Independent variable
        y: Dependent variable
        n_folds: Number of folds
        metric: 'r2' or 'mse'

    Returns:
        Dictionary with CV scores
    """
    from sklearn.model_selection import KFold
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_squared_error

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    scores = []

    X = x.reshape(-1, 1) if x.ndim == 1 else x

    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        if metric == 'r2':
            score = r2_score(y_test, y_pred)
        elif metric == 'mse':
            score = mean_squared_error(y_test, y_pred)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        scores.append(score)

    return {
        'cv_scores': scores,
        'mean_score': np.mean(scores),
        'std_score': np.std(scores),
        'metric': metric
    }
