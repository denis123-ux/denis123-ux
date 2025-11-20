"""Validation modules for statistical rigor and sanity checks."""

from .statistical import (
    compute_confidence_interval,
    bonferroni_correction,
    compute_effect_size,
    check_normality,
    bootstrap_ci
)
from .sanity_checks import (
    check_area_law_properties,
    check_entropy_bounds,
    check_metric_properties,
    check_stress_tensor_conservation
)

__all__ = [
    'compute_confidence_interval',
    'bonferroni_correction',
    'compute_effect_size',
    'check_normality',
    'bootstrap_ci',
    'check_area_law_properties',
    'check_entropy_bounds',
    'check_metric_properties',
    'check_stress_tensor_conservation'
]
