# Contributing to Entanglement-to-Einstein

## Research Collaboration

This is an active research project. If you're interested in contributing, please:

1. **Contact**: Reach out to Denis with your background and interests
2. **Read**: Familiarize yourself with the theoretical background (see References in README)
3. **Propose**: Submit an issue describing your proposed contribution

## Code Contributions

### Development Setup

```bash
# Clone repo
git clone <repo-url>
cd entanglement-einstein

# Create development environment
conda env create -f environment.yml
conda activate entanglement-einstein

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

### Code Standards

1. **Style**: Follow PEP 8, use `black` for formatting
2. **Type hints**: All functions must have type annotations
3. **Documentation**: Docstrings for all public functions (Google style)
4. **Tests**: Write tests for new functionality (aim for >80% coverage)

### Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes with clear, atomic commits
3. Add tests for new functionality
4. Update documentation (README, docstrings)
5. Run tests: `pytest tests/`
6. Format code: `black src/ tests/`
7. Submit PR with clear description

### Scientific Integrity

All contributors must adhere to:

1. **Preregistration**: Hypotheses must be registered BEFORE analysis
2. **Reproducibility**: All code must be reproducible (set random seeds)
3. **Transparency**: Document all assumptions and limitations
4. **Validation**: Use multiple independent methods for critical calculations

## Areas for Contribution

### High Priority

1. **Exact Free Fermion Ground State**:
   - Implement proper free fermion CFT ground state
   - Currently using placeholder random state
   - Reference: Calabrese & Cardy (2004)

2. **MERA Optimization**:
   - Implement gradient-based optimization of MERA tensors
   - Use automatic differentiation (autograd/jax)
   - Reference: Vidal (2007), Evenbly & Vidal (2015)

3. **Tensor Network Contraction**:
   - Use quimb or cotengra for efficient contraction
   - Implement custom algorithms for MERA-specific contractions

### Medium Priority

1. **GPU Acceleration**: Port critical sections to cupy/jax
2. **Parallel Computing**: Parallelize entropy calculations
3. **Alternative Tensor Networks**: Implement PEPS, TTN
4. **Advanced Metrics**: Entanglement negativity, reflected entropy

### Low Priority

1. **Visualization**: Interactive 3D plots of emergent geometry
2. **Documentation**: Jupyter notebooks with tutorials
3. **Performance**: Profiling and optimization

## Testing

### Run Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_entropy.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

Follow this structure:

```python
def test_descriptive_name():
    """Clear description of what is being tested."""
    # Arrange: Set up test data
    state = create_test_state(...)

    # Act: Perform operation
    result = function_under_test(state)

    # Assert: Check result
    assert condition, "Clear error message"
```

## Documentation

### Docstring Format

Use Google style:

```python
def compute_entropy(rho: np.ndarray, base: float = np.e) -> float:
    """
    Compute von Neumann entropy.

    Parameters
    ----------
    rho : ndarray, shape (d, d)
        Density matrix
    base : float, default np.e
        Logarithm base

    Returns
    -------
    float
        Entropy S = -Tr(ρ log ρ)

    Examples
    --------
    >>> rho = np.eye(4) / 4
    >>> S = compute_entropy(rho, base=2)
    >>> print(f"S = {S:.2f} bits")
    S = 2.00 bits

    References
    ----------
    .. [1] von Neumann, J. (1932). Mathematical Foundations of Quantum Mechanics
    """
    ...
```

## Questions?

Open an issue or contact the maintainer.

---

**Thank you for contributing to fundamental physics research!** 🚀
