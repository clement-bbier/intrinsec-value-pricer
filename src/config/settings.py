"""
src/config/settings.py

CENTRALIZED CONFIGURATION SETTINGS
==================================
Role: Type-safe configuration objects (Single Source of Truth).
Architecture: Aggregates raw constants into high-level functional settings.
Style: Numpy Style docstrings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Use specific imports to avoid circular dependencies if possible,
# or use full paths inside methods.
from src.config.constants import (
    ModelDefaults,
    MonteCarloDefaults,
    SystemDefaults,
    ValidationThresholds,
    ValuationEngineDefaults,
)

# ==============================================================================
# 1. MONTE CARLO SIMULATION CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class MonteCarloSimulationConfig:
    """
    Comprehensive configuration for probabilistic Monte Carlo simulations.
    """
    # Baseline Iteration Parameters
    default_simulations: int = MonteCarloDefaults.DEFAULT_SIMULATIONS
    min_simulations: int = MonteCarloDefaults.MIN_SIMULATIONS
    max_simulations: int = MonteCarloDefaults.MAX_SIMULATIONS

    # Correlation Parameters
    default_rho: float = MonteCarloDefaults.DEFAULT_RHO
    rho_bounds: tuple[float, float] = (-1.0, 1.0)

    # Standard Deviation Defaults (Volatility)
    default_volatility_beta: float = 0.10
    default_volatility_growth: float = 0.02
    default_volatility_terminal: float = 0.01
    default_volatility_base_flow: float = 0.05

    # Statistical Validity
    min_valid_ratio: float = MonteCarloDefaults.MIN_VALID_RATIO
    max_clamping_ratio: float = MonteCarloDefaults.CLAMPING_THRESHOLD

    # Safety
    timeout_seconds: int = 30


# ==============================================================================
# 2. VALIDATION CONFIGURATION (Ex-Audit)
# ==============================================================================

@dataclass(frozen=True)
class ValidationConfig:
    """
    Configuration for financial sanity checks.
    Used by the engine to validate model integrity.
    """
    # Core Financial Health
    icr_minimum: float = ValidationThresholds.ICR_MIN
    beta_minimum: float = ValidationThresholds.BETA_MIN
    beta_maximum: float = ValidationThresholds.BETA_MAX
    liquidity_ratio_minimum: float = ValidationThresholds.LIQUIDITY_RATIO_MIN

    # SOTP Reconciliation
    sotp_revenue_gap_warning: float = ValidationThresholds.SOTP_REVENUE_GAP_WARNING
    sotp_revenue_gap_error: float = ValidationThresholds.SOTP_REVENUE_GAP_ERROR
    sotp_discount_maximum: float = ValidationThresholds.SOTP_DISCOUNT_MAX

    # Convergence and Spread
    wacc_growth_spread_minimum: float = ValidationThresholds.WACC_G_SPREAD_MIN
    wacc_growth_spread_warning: float = ValidationThresholds.WACC_G_SPREAD_WARNING

    # Operational Cash Flow Integrity
    fcf_growth_maximum: float = ValidationThresholds.FCF_GROWTH_MAX
    fcf_margin_minimum: float = ValidationThresholds.FCF_MARGIN_MIN

    # Investment Efficiency
    reinvestment_rate_maximum: float = ValidationThresholds.REINVESTMENT_RATE_MAX


# ==============================================================================
# 3. SYSTEM AND PERFORMANCE CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class SystemPerformanceConfig:
    """
    System-level settings governing caching, API resilience, and logging.
    """
    # Cache Time-To-Live (TTL)
    cache_ttl_short: int = SystemDefaults.CACHE_TTL_SHORT
    cache_ttl_long: int = SystemDefaults.CACHE_TTL_LONG

    # API Resiliency
    yahoo_api_timeout: float = 12.0
    retry_attempts: int = 3
    retry_delay_base: float = 0.5

    # UI Presentation Limits
    max_display_rows: int = 100
    chart_height: int = 400


# ==============================================================================
# 4. VALUATION MODEL CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class ValuationModelConfig:
    """
    Global defaults and constraints for valuation models.
    """
    # Projection Horizon
    default_projection_years: int = ModelDefaults.DEFAULT_PROJECTION_YEARS
    minimum_projection_years: int = 1
    maximum_projection_years: int = 15

    # Solver Limits
    maximum_iterations: int = ValuationEngineDefaults.MAX_ITERATIONS
    convergence_tolerance: float = ValuationEngineDefaults.CONVERGENCE_TOLERANCE


# ==============================================================================
# GLOBAL CONFIGURATION INSTANCES
# ==============================================================================

# Primary Configuration Singletons
SIMULATION_CONFIG = MonteCarloSimulationConfig()
VALIDATION_CONFIG = ValidationConfig()
SYSTEM_CONFIG = SystemPerformanceConfig()
VALUATION_CONFIG = ValuationModelConfig()

# Registry for programmatic access
CONFIG_REGISTRY: dict[str, Any] = {
    "simulation": SIMULATION_CONFIG,
    "validation": VALIDATION_CONFIG,
    "system": SYSTEM_CONFIG,
    "valuation": VALUATION_CONFIG,
}


def get_config(section: str) -> Any:
    """
    Retrieves a specific configuration section.

    Parameters
    ----------
    section : str
        The name of the configuration section.

    Returns
    -------
    Any
        The requested frozen configuration dataclass instance.
    """
    if section not in CONFIG_REGISTRY:
        available = ", ".join(CONFIG_REGISTRY.keys())
        raise KeyError(f"Unknown configuration section '{section}'. Available: {available}")
    return CONFIG_REGISTRY[section]
