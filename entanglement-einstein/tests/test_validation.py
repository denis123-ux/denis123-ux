"""
Unit tests for validation framework.
"""

import numpy as np
import pytest
from src.validation.sanity_checks import (
    check_entanglement_entropy_bounds,
    check_density_matrix_valid,
    check_metric_properties,
    check_numerical_stability
)
from src.validation.statistical import (
    compute_confidence_interval,
    linear_regression_with_ci,
    cohens_d
)


class TestSanityChecks:
    """Test suite for sanity check validation."""

    def test_entropy_bounds_valid(self):
        """Test entropy bounds check with valid entropy."""
        S = 0.5
        dim = 4

        result = check_entanglement_entropy_bounds(S, dim, "test_region")

        assert result['passed'], "Valid entropy should pass"
        assert len(result['violations']) == 0

    def test_entropy_bounds_negative(self):
        """Test entropy bounds check catches negative entropy."""
        S = -0.1
        dim = 4

        with pytest.raises(Exception):  # Should raise SanityCheckError
            check_entanglement_entropy_bounds(S, dim, "test_region")

    def test_density_matrix_valid(self):
        """Test valid density matrix passes all checks."""
        # Valid density matrix: maximally mixed state
        rho = np.eye(4) / 4

        result = check_density_matrix_valid(rho)

        assert result['passed'], "Valid density matrix should pass"
        assert len(result['violations']) == 0
        assert np.abs(result['trace'] - 1.0) < 1e-10

    def test_density_matrix_not_hermitian(self):
        """Test non-Hermitian matrix fails."""
        rho = np.array([[0.5, 0.1], [0.2, 0.5]])  # Not Hermitian

        result = check_density_matrix_valid(rho)

        assert not result['passed'], "Non-Hermitian matrix should fail"
        assert 'Not Hermitian' in str(result['violations'])

    def test_numerical_stability_nan(self):
        """Test NaN detection."""
        with pytest.raises(Exception):  # Should raise SanityCheckError
            check_numerical_stability(np.nan, "test_value")

    def test_numerical_stability_inf(self):
        """Test Inf detection."""
        with pytest.raises(Exception):
            check_numerical_stability(np.inf, "test_value")


class TestStatisticalValidation:
    """Test suite for statistical validation."""

    def test_confidence_interval_normal(self):
        """Test confidence interval calculation."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 1000)

        ci_width = compute_confidence_interval(data, confidence=0.95, method='parametric')

        # Should be close to 2*1.96*std/sqrt(n) ≈ 0.062
        expected_half_width = 1.96 * 1.0 / np.sqrt(1000)

        assert np.abs(ci_width - expected_half_width) < 0.02

    def test_linear_regression(self):
        """Test linear regression with known line."""
        np.random.seed(42)

        # y = 2x + 3 + noise
        x = np.linspace(0, 10, 100)
        y = 2 * x + 3 + np.random.normal(0, 0.1, 100)

        result = linear_regression_with_ci(x, y)

        assert np.abs(result['slope'] - 2.0) < 0.1, f"Slope should be ~2, got {result['slope']}"
        assert np.abs(result['intercept'] - 3.0) < 0.5, f"Intercept should be ~3, got {result['intercept']}"
        assert result['r_squared'] > 0.98, f"R² should be high, got {result['r_squared']}"

    def test_cohens_d_no_effect(self):
        """Test Cohen's d for no effect."""
        np.random.seed(42)

        group1 = np.random.normal(0, 1, 100)
        group2 = np.random.normal(0, 1, 100)

        d = cohens_d(group1, group2)

        # Should be small
        assert np.abs(d) < 0.3, f"Cohen's d should be small, got {d}"

    def test_cohens_d_large_effect(self):
        """Test Cohen's d for large effect."""
        np.random.seed(42)

        group1 = np.random.normal(0, 1, 100)
        group2 = np.random.normal(3, 1, 100)  # 3 SD difference

        d = cohens_d(group1, group2)

        # Should be ~3
        assert np.abs(d + 3.0) < 0.5, f"Cohen's d should be ~-3, got {d}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
