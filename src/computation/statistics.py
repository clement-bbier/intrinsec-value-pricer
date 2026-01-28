"""
src/computation/statistics.py

STATISTICAL UTILITIES FOR MONTE CARLO SIMULATIONS
=================================================
Role: Provides random sampling generators for probabilistic sensitivity analysis.
Capabilities: Correlated multivariate sampling (Beta/Growth) and bounded independent draws.
Architecture: Modern NumPy default_rng protocols (2026 standards).

Style: Numpy docstrings
"""

from __future__ import annotations

from typing import Tuple, Optional
import numpy as np


# ============================================================================
# CORRELATED SAMPLING GENERATION
# ============================================================================

def generate_multivariate_samples(
    *,
    mu_beta: float,
    sigma_beta: float,
    mu_growth: float,
    sigma_growth: float,
    rho: float,
    num_simulations: int,
    seed: Optional[int] = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates correlated random samples for two continuous variables (e.g., Beta and Growth).

    Supports zero volatility for deterministic fallback scenarios.
    Ensures economic consistency by applying a correlation coefficient (rho).

    Parameters
    ----------
    mu_beta : float
        Mean value for the Beta distribution.
    sigma_beta : float
        Standard deviation for the Beta distribution.
    mu_growth : float
        Mean value for the Growth distribution.
    sigma_growth : float
        Standard deviation for the Growth distribution.
    rho : float
        Correlation coefficient between the two variables, must be in [-1, 1].
    num_simulations : int
        Number of iterations to generate.
    seed : int, optional
        Random seed for reproducibility, default is 42.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        A tuple containing (beta_samples, growth_samples).

    Raises
    ------
    ValueError
        If num_simulations is not positive or rho is outside the [-1, 1] range.
    """

    if num_simulations <= 0:
        raise ValueError("num_simulations must be strictly positive.")

    if not (-1.0 <= rho <= 1.0):
        raise ValueError("The correlation coefficient rho must be within [-1, 1].")

    if sigma_beta < 0 or sigma_growth < 0:
        raise ValueError("Volatilities must be positive or zero.")

    # GENERATOR INITIALIZATION (MODERN NUMPY 2026)
    # Using default_rng prevents pollution of the global np.random state
    rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # COVARIANCE MATRIX CALCULATION
    # ------------------------------------------------------------------
    # Formula: Cov(X, Y) = rho × σ_X × σ_Y
    covariance = rho * sigma_beta * sigma_growth

    cov_matrix = np.array([
        [sigma_beta ** 2, covariance],
        [covariance, sigma_growth ** 2]
    ])

    mean_vector = np.array([mu_beta, mu_growth])

    # ------------------------------------------------------------------
    # MULTIVARIATE DRAW
    # ------------------------------------------------------------------
    # The 'svd' method is highly robust for semi-definite positive matrices
    # (e.g., when sigma_beta or sigma_growth are 0.0)
    draws = rng.multivariate_normal(
        mean=mean_vector,
        cov=cov_matrix,
        size=num_simulations,
        method='svd'
    )

    betas = draws[:, 0]
    growths = draws[:, 1]

    return betas, growths


# ============================================================================
# INDEPENDENT SAMPLING GENERATION
# ============================================================================

def generate_independent_samples(
    *,
    mean: float,
    sigma: float,
    num_simulations: int,
    clip_min: Optional[float] = None,
    clip_max: Optional[float] = None,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generates independent normal distribution samples with optional economic clipping.

    Useful for variables with no known correlation to the core risk pair (e.g., SBC Dilution).

    Parameters
    ----------
    mean : float
        Mean value of the distribution.
    sigma : float
        Standard deviation (uncertainty).
    num_simulations : int
        Number of iterations.
    clip_min : float, optional
        Lower bound for values (clipping).
    clip_max : float, optional
        Upper bound for values (clipping).
    seed : int, optional
        Random seed.

    Returns
    -------
    np.ndarray
        Array of generated samples.
    """

    if num_simulations <= 0:
        raise ValueError("num_simulations must be strictly positive.")

    if sigma < 0:
        raise ValueError("sigma must be positive or zero.")

    # LOCAL GENERATOR INITIALIZATION
    rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # NORMAL DRAW
    # ------------------------------------------------------------------
    draws = rng.normal(
        loc=mean,
        scale=sigma,
        size=num_simulations
    )

    # ------------------------------------------------------------------
    # ECONOMIC CLIPPING (OPTIONAL)
    # ------------------------------------------------------------------
    # Ensures that simulated values remain within realistic bounds (e.g., no negative growth)
    if clip_min is not None or clip_max is not None:
        c_min = clip_min if clip_min is not None else -np.inf
        c_max = clip_max if clip_max is not None else np.inf

        if c_min > c_max:
            raise ValueError("clip_min cannot be greater than clip_max.")

        draws = np.clip(draws, c_min, c_max)

    return draws