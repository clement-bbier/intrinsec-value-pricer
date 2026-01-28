"""
src/config/settings.py

CENTRALIZED CONFIGURATION SETTINGS
==================================
Role: Type-safe configuration objects (Single Source of Truth).
Architecture: Aggregates raw constants into high-level functional settings.
Style: Numpy Style docstrings.

Financial Risk Note:
-------------------
These parameters directly govern simulation behaviors, audit strictness,
and model convergence. Modifications may significantly impact result quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


# ==============================================================================
# 1. MONTE CARLO SIMULATION CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class MonteCarloSimulationConfig:
    """
    Comprehensive configuration for probabilistic Monte Carlo simulations.

    Inherits baseline limits and defaults from the centralized constants
    repository to ensure system-wide consistency.
    """

    # Local import to prevent circular dependencies during initialization
    from src.config.constants import MonteCarloDefaults

    # Baseline Iteration Parameters
    default_simulations: int = MonteCarloDefaults.DEFAULT_SIMULATIONS
    min_simulations: int = MonteCarloDefaults.MIN_SIMULATIONS
    max_simulations: int = MonteCarloDefaults.MAX_SIMULATIONS

    # Correlation Parameters for Risk Pairings
    default_rho: float = -0.30
    rho_bounds: tuple[float, float] = (-1.0, 1.0)

    # Standard Deviation Defaults (Volatility)
    default_volatility_beta: float = 0.10
    default_volatility_growth: float = 0.02
    default_volatility_terminal: float = 0.01

    # Statistical Validity Thresholds
    min_valid_ratio: float = 0.80
    max_clamping_ratio: float = 0.10

    # Safety and Sensitivity Guards
    growth_safety_margin: float = 0.015
    sensitivity_simulations: int = 1000
    max_iv_filter: float = 100_000.0
    default_wacc_fallback: float = 0.08

    # Execution Timeout to prevent UI hanging
    timeout_seconds: int = 30


# ==============================================================================
# 2. AUDIT AND VALIDATION CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class AuditValidationConfig:
    """
    Configuration for financial audit thresholds and consistency checks.
    Used by the AuditEngine to generate institutional ratings.
    """

    # Core Financial Health Thresholds
    icr_minimum: float = 1.5
    beta_minimum: float = 0.4
    beta_maximum: float = 3.0
    liquidity_ratio_minimum: float = 1.0

    # SOTP Reconciliation Thresholds
    sotp_revenue_gap_warning: float = 0.05
    sotp_revenue_gap_error: float = 0.15
    sotp_discount_maximum: float = 0.25

    # Convergence and Spread Thresholds (Gordon Safety)
    wacc_growth_spread_minimum: float = 0.01
    wacc_growth_spread_warning: float = 0.02

    # Operational Cash Flow Integrity Thresholds
    fcf_growth_maximum: float = 0.25
    fcf_margin_minimum: float = 0.05

    # Investment Efficiency Thresholds
    reinvestment_rate_maximum: float = 1.0


# ==============================================================================
# 3. SYSTEM AND PERFORMANCE CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class SystemPerformanceConfig:
    """
    System-level settings governing caching, API resilience, and logging.
    """

    # Cache Time-To-Live (TTL) Settings
    cache_ttl_short: int = 3600   # 1 Hour
    cache_ttl_medium: int = 14400 # 4 Hours
    cache_ttl_long: int = 86400   # 24 Hours

    # API Resiliency Policy
    yahoo_api_timeout: float = 12.0
    retry_attempts: int = 3
    retry_delay_base: float = 0.5

    # UI Presentation Limits
    max_display_rows: int = 100
    chart_height: int = 400

    # Logging Infrastructure
    max_log_file_size: int = 10_000_000  # 10MB
    max_log_backup_files: int = 5


# ==============================================================================
# 4. VALUATION MODEL CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class ValuationModelConfig:
    """
    Global defaults and constraints for valuation models (DCF, Graham, RIM).
    """

    # Projection Horizon Constraints
    default_projection_years: int = 5
    minimum_projection_years: int = 1
    maximum_projection_years: int = 15

    # Macro-economic Fallbacks
    default_risk_free_rate: float = 0.04
    default_market_risk_premium: float = 0.05
    default_tax_rate: float = 0.25

    # Terminal Growth Constraints
    default_terminal_growth: float = 0.02
    maximum_terminal_growth: float = 0.04

    # Numerical Solver Limits
    maximum_iterations: int = 1000
    convergence_tolerance: float = 1e-6


# ==============================================================================
# GLOBAL CONFIGURATION INSTANCES
# ==============================================================================



# Primary Configuration Singletons
SIMULATION_CONFIG = MonteCarloSimulationConfig()
AUDIT_CONFIG = AuditValidationConfig()
SYSTEM_CONFIG = SystemPerformanceConfig()
VALUATION_CONFIG = ValuationModelConfig()

# Registry for programmatic access and dependency injection
CONFIG_REGISTRY: Dict[str, Any] = {
    "simulation": SIMULATION_CONFIG,
    "audit": AUDIT_CONFIG,
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
        Supported: 'simulation', 'audit', 'system', 'valuation'.

    Returns
    -------
    Any
        The requested frozen configuration dataclass instance.

    Raises
    ------
    KeyError
        If the section name is invalid or not registered.
    """
    if section not in CONFIG_REGISTRY:
        available = ", ".join(CONFIG_REGISTRY.keys())
        raise KeyError(f"Unknown configuration section '{section}'. Available: {available}")
    return CONFIG_REGISTRY[section]


# ==============================================================================
# INITIALIZATION VALIDATION
# ==============================================================================

def _validate_configurations():
    """
    Performs integrity checks on configurations at module load time.
    Ensures that logical bounds are respected to prevent runtime crashes.
    """

    # Monte Carlo Boundaries Validation
    assert SIMULATION_CONFIG.min_simulations < SIMULATION_CONFIG.default_simulations
    assert SIMULATION_CONFIG.default_simulations <= SIMULATION_CONFIG.max_simulations

    # Audit Sensitivity Validation
    assert AUDIT_CONFIG.beta_minimum < AUDIT_CONFIG.beta_maximum
    assert AUDIT_CONFIG.sotp_revenue_gap_warning < AUDIT_CONFIG.sotp_revenue_gap_error

    # Valuation Horizon Validation
    assert VALUATION_CONFIG.minimum_projection_years <= VALUATION_CONFIG.default_projection_years
    assert VALUATION_CONFIG.default_projection_years <= VALUATION_CONFIG.maximum_projection_years


# Execute validation upon module import
_validate_configurations()