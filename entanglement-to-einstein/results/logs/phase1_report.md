# Experiment Report: phase1_area_law

**Session ID:** 20251120_171314
**Status:** running
**Start Time:** 2025-11-20T17:13:14.272544

## Preregistration

**Hypothesis:** Area law for entanglement entropy in 1D free fermion CFT

**Prediction:** S(L) = 0.166667 * log(L) + const, R² > 0.99

**Method:** Free fermion correlation matrix method + linear regression

**Preregistration Hash:** `0c850d871dc0c9c331d366540dfb68b445141cbc79b5af3756b3d603fd6c8da4`

## Results Summary

Total results logged: 1

## Summary Messages

- ✓ SUCCESS: Slope consistent with theoretical prediction
- ✗ FAILURE: Not all success criteria met

## Environment

- Python: 3.11.14
- Platform: Linux-4.4.0-x86_64-with-glibc2.39
- NumPy: 2.3.5

## Reproducibility

To reproduce this experiment, use:
```bash
python experiments/phase1_area_law.py --reproduce 20251120_171314
```