"""
src/config/constants.py

CENTRALIZED VALUATION SYSTEM CONSTANTS
=======================================
Role: Single source of truth for configuration thresholds and default parameters.
Scope: Financial calculations, audit rules, API resiliency, and UI constraints.
Architecture: Immutable frozen dataclasses.

Usage:
------
    from src.config.constants import AuditThresholds, MonteCarloDefaults
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. MONTE CARLO SIMULATION
# ==============================================================================

@dataclass(frozen=True)
class MonteCarloDefaults:
    """
    Configuration defaults for stochastic Monte Carlo simulations.

    Attributes
    ----------
    MIN_SIMULATIONS : int
        Minimum allowed iterations.
    MAX_SIMULATIONS : int
        Maximum allowed iterations (capped for performance).
    DEFAULT_SIMULATIONS : int
        Standard run size (5,000).
    STEP_SIMULATIONS : int
        UI slider increment step.
    DEFAULT_RHO : float
        Default correlation between Beta and Growth.
    MIN_VALID_RATIO : float
        Audit threshold for simulation convergence.
    CLAMPING_THRESHOLD : float
        Maximum allowed percentage of out-of-bounds draws before warning.
    """
    MIN_SIMULATIONS: int = 100
    MAX_SIMULATIONS: int = 20_000
    DEFAULT_SIMULATIONS: int = 5_000
    STEP_SIMULATIONS: int = 200
    DEFAULT_RHO: float = -0.30
    MIN_VALID_RATIO: float = 0.80
    CLAMPING_THRESHOLD: float = 0.10


# ==============================================================================
# 2. PEERS / MULTIPLES
# ==============================================================================

@dataclass(frozen=True)
class PeerDefaults:
    """
    Configuration for peer cohort discovery and relative valuation.

    Attributes
    ----------
    MAX_PEERS_ANALYSIS : int
        Limit of peers used for triangulation to avoid statistical noise.
    MIN_PEERS_REQUIRED : int
        Minimum cohort size for a valid relative valuation signal.
    API_TIMEOUT_SECONDS : float
        Max wait time for external financial data fetching.
    MAX_RETRY_ATTEMPTS : int
        Resiliency policy for secondary data acquisition.
    """
    MAX_PEERS_ANALYSIS: int = 5
    MIN_PEERS_REQUIRED: int = 2
    API_TIMEOUT_SECONDS: float = 12.0
    MAX_RETRY_ATTEMPTS: int = 1


# ==============================================================================
# 3. AUDIT - VALIDATION THRESHOLDS
# ==============================================================================

@dataclass(frozen=True)
class AuditThresholds:
    """
    Business rules and thresholds for the reliability audit (Pillar 3).

    Attributes
    ----------
    ICR_MIN : float
        Minimum Interest Coverage Ratio for solvency validation.
    BETA_MIN / BETA_MAX : float
        Acceptable range for systemic risk coefficients.
    LIQUIDITY_RATIO_MIN : float
        Threshold for secondary market liquidity checks.
    SOTP_REVENUE_GAP_WARNING / ERROR : float
        Tolerance levels for segment revenue reconciliation.
    SOTP_DISCOUNT_MAX : float
        Prudent limit for conglomerate/holding discounts.
    WACC_G_SPREAD_MIN : float
        Critical divergence limit: model must satisfy r > g.
    FCF_GROWTH_MAX : float
        Upper limit for sustainable Phase 1 growth.
    REINVESTMENT_RATE_MAX : float
        Upper limit for industrial maintenance CapEx ratio.
    """
    ICR_MIN: float = 1.5
    BETA_MIN: float = 0.4
    BETA_MAX: float = 3.0
    LIQUIDITY_RATIO_MIN: float = 1.0
    SOTP_REVENUE_GAP_WARNING: float = 0.05
    SOTP_REVENUE_GAP_ERROR: float = 0.15
    SOTP_DISCOUNT_MAX: float = 0.25
    WACC_G_SPREAD_MIN: float = 0.01
    WACC_G_SPREAD_WARNING: float = 0.02
    FCF_GROWTH_MAX: float = 0.25
    FCF_MARGIN_MIN: float = 0.05
    REINVESTMENT_RATE_MAX: float = 1.0


# ==============================================================================
# 4. AUDIT - PENALTIES
# ==============================================================================

@dataclass(frozen=True)
class AuditPenalties:
    """
    Scoring penalties applied when audit invariants are violated.
    Values are deducted from the 0-100 reliability score.
    """
    CRITICAL: float = 100.0
    HIGH: float = 35.0
    MEDIUM: float = 15.0
    LOW: float = 5.0
    INFO: float = 0.0


# ==============================================================================
# 5. MACRO ECONOMIC & SPREADS
# ==============================================================================

@dataclass(frozen=True)
class MacroDefaults:
    """
    Baseline macro-economic parameters and fallback rates.

    Attributes
    ----------
    DEFAULT_AAA_SPREAD : float
        Baseline spread over Risk-Free for AAA corporate debt.
    FALLBACK_RISK_FREE_RATE_USD / EUR : float
        Hardcoded rates if API macro context fails.
    LARGE_CAP_THRESHOLD : float
        Market Cap limit used to toggle synthetic spread tables ($5B).
    """
    DEFAULT_AAA_SPREAD: float = 0.0070
    FALLBACK_RISK_FREE_RATE_USD: float = 0.04
    FALLBACK_RISK_FREE_RATE_EUR: float = 0.027
    DEFAULT_INFLATION_RATE: float = 0.02
    DEFAULT_MARKET_RISK_PREMIUM: float = 0.05
    LARGE_CAP_THRESHOLD: float = 5_000_000_000


# ==============================================================================
# 6. DATA EXTRACTION & API
# ==============================================================================

@dataclass(frozen=True)
class DataExtractionDefaults:
    """
    Settings for low-level data acquisition and normalization engines.

    Attributes
    ----------
    RETRY_DELAY_BASE : float
        Starting delay for exponential backoff (seconds).
    HISTORICAL_CAGR_YEARS : int
        Lookback window for automatic growth estimation.
    PRICE_FORMAT_MULTIPLIER : float
        Conversion factor for specific currencies (e.g., Pence to Pounds).
    """
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_BASE: float = 0.5
    RETRY_BACKOFF_MULTIPLIER: int = 2
    YAHOO_RAW_MAX_RETRIES: int = 2
    HISTORICAL_CAGR_YEARS: int = 3
    PRICE_FORMAT_MULTIPLIER: float = 100.0
    NORMALIZATION_LAST_QUARTERS: int = 4


# ==============================================================================
# 7. VALUATION ENGINES
# ==============================================================================

@dataclass(frozen=True)
class ValuationEngineDefaults:
    """
    Technical parameters for numerical solvers and model-specific constants.

    Attributes
    ----------
    MAX_ITERATIONS : int
        Loop limit for iterative solvers (e.g., Reverse DCF).
    STRESS_BETA : float
        Max beta applied in Monte Carlo stress tests.
    RIM_DEFAULT_OMEGA : float
        Default persistence coefficient for Residual Income (ω).
    SPREADS_LARGE_CAP : List[Tuple]
        Mapping of Interest Coverage Ratio to credit spreads for Large Caps.
    """
    MAX_ITERATIONS: int = 50
    CONVERGENCE_TOLERANCE: float = 1e-6
    STRESS_GROWTH_RATE: float = 0.0
    STRESS_PERPETUAL_GROWTH: float = 0.01
    STRESS_BETA: float = 1.50
    RIM_DEFAULT_OMEGA: float = 0.60
    RIM_MAX_PAYOUT_RATIO: float = 0.95

    # Credit Rating Spreads (ICR-based)
    SPREAD_AAA: float = 0.0045
    SPREAD_AA: float = 0.0060
    SPREAD_A: float = 0.0077
    SPREAD_BBB: float = 0.0085
    SPREAD_BB: float = 0.0120
    SPREAD_B: float = 0.0183
    SPREAD_CCC: float = 0.0728

    SPREADS_LARGE_CAP = [
        (8.5, SPREAD_AAA), (6.5, SPREAD_AA), (5.5, SPREAD_A), (4.25, SPREAD_BBB),
        (3.0, 0.0095), (2.5, SPREAD_BB), (2.25, 0.0155), (2.0, SPREAD_B),
        (1.75, 0.0261), (1.5, 0.0300), (1.25, 0.0442), (0.8, SPREAD_CCC),
        (0.65, 0.1010), (0.2, 0.1550), (-999, 0.1900)
    ]

    SPREADS_SMALL_MID_CAP = [
        (12.5, SPREAD_AAA_SMALL := 0.0045), (9.5, SPREAD_AA_SMALL := 0.0060),
        (7.5, SPREAD_A_SMALL := 0.0077), (6.0, SPREAD_BBB_SMALL := 0.0085),
        (4.5, 0.0095), (4.0, SPREAD_BB_SMALL := 0.0120),
        (3.5, SPREAD_B_SMALL := 0.0155), (3.0, SPREAD_B),
        (2.5, 0.0261), (2.0, 0.0300), (1.5, 0.0442),
        (1.25, SPREAD_CCC_SMALL := 0.0728),
        (0.8, 0.1010), (0.5, 0.1550), (-999, 0.1900)
    ]


# ==============================================================================
# 8. DEFAULT DATA MODELS
# ==============================================================================

@dataclass(frozen=True)
class ModelDefaults:
    """Fallback values for Pydantic domain models to ensure field validity."""
    DEFAULT_BETA: float = 1.0
    DEFAULT_TOTAL_DEBT: float = 0.0
    DEFAULT_CASH_EQUIVALENTS: float = 0.0
    DEFAULT_MINORITY_INTERESTS: float = 0.0
    DEFAULT_PENSION_PROVISIONS: float = 0.0
    DEFAULT_BOOK_VALUE: float = 0.0
    DEFAULT_INTEREST_EXPENSE: float = 0.0
    DEFAULT_MEAN_ABSOLUTE_ERROR: float = 0.0
    DEFAULT_ALPHA_VS_MARKET: float = 0.0
    DEFAULT_MODEL_ACCURACY_SCORE: float = 0.0
    DEFAULT_MEDIAN_PE: float = 0.0
    DEFAULT_MEDIAN_EV_EBITDA: float = 0.0
    DEFAULT_MEDIAN_EV_EBIT: float = 0.0
    DEFAULT_MEDIAN_PB: float = 0.0
    DEFAULT_MEDIAN_EV_REV: float = 0.0
    DEFAULT_IMPLIED_VALUE_EV_EBITDA: float = 0.0
    DEFAULT_IMPLIED_VALUE_PE: float = 0.0
    DEFAULT_PE_BASED_PRICE: float = 0.0
    DEFAULT_EBITDA_BASED_PRICE: float = 0.0
    DEFAULT_REV_BASED_PRICE: float = 0.0
    DEFAULT_PROBABILITY: float = 0.333
    DEFAULT_EXPECTED_VALUE: float = 0.0
    DEFAULT_MAX_UPSIDE: float = 0.0
    DEFAULT_MAX_DOWNSIDE: float = 0.0
    DEFAULT_CONGLOMERATE_DISCOUNT: float = 0.0
    DEFAULT_STEP_ID: int = 0
    DEFAULT_RESULT_VALUE: float = 0.0
    DEFAULT_INDICATOR_VALUE: float = 0.0
    DEFAULT_PROJECTION_YEARS: int = 5
    DEFAULT_HIGH_GROWTH_YEARS: int = 0


# ==============================================================================
# 9. UI WIDGETS & INTERFACE PARAMETERS
# ==============================================================================

@dataclass(frozen=True)
class UIWidgetDefaults:
    """Limits and standard steps for Streamlit user input widgets."""
    DEFAULT_PROJECTION_YEARS: int = 5
    MIN_PROJECTION_YEARS: int = 3
    MAX_PROJECTION_YEARS: int = 15
    MIN_GROWTH_RATE: float = -0.50
    MAX_GROWTH_RATE: float = 1.0
    MAX_TERMINAL_GROWTH: float = 0.05
    MAX_DISCOUNT_RATE: float = 0.20
    MAX_BETA: float = 5.0
    MAX_TAX_RATE: float = 0.60
    MAX_COST_OF_DEBT: float = 0.20
    MAX_EXIT_MULTIPLE: float = 100.0
    MAX_MANUAL_PRICE: float = 10000.0
    DEFAULT_BASE_FLOW_VOLATILITY: float = 0.05


# ==============================================================================
# 10. GROWTH & FINANCIAL CALCULATIONS
# ==============================================================================

@dataclass(frozen=True)
class GrowthCalculationDefaults:
    """Default parameters for growth convergence and sustainability models."""
    DEFAULT_MARGIN: float = 0.0
    DEFAULT_FCF_MARGIN_TARGET: float = 0.20
    DEFAULT_HIGH_GROWTH_YEARS: int = 0
    DEFAULT_HIGH_GROWTH_PERIOD: Optional[int] = 0
    MIN_RETENTION_RATE: float = 0.0
    MAX_RETENTION_RATE: float = 1.0


# ==============================================================================
# 11. TECHNICAL CONSTANTS & VALIDATION
# ==============================================================================

@dataclass(frozen=True)
class TechnicalDefaults:
    """Numerical tolerances and technical clamping parameters."""
    NUMERICAL_TOLERANCE: float = 0.001
    PROBABILITY_TOLERANCE: float = 0.001
    BACKTEST_ERROR_THRESHOLD: float = 0.20
    VALUATION_CONVERGENCE_THRESHOLD: float = 0.5
    REVERSE_DCF_LOW_BOUND: float = -0.20
    REVERSE_DCF_HIGH_BOUND: float = 0.50
    BORROWING_RATIO_MAX: float = 0.5
    GROWTH_AUDIT_THRESHOLD: float = 0.20
    PERCENTAGE_MULTIPLIER: float = 100.0
    DEFAULT_AAA_YIELD: float = 0.044
    MAX_DILUTION_CLAMPING: float = 0.10
    DEFAULT_VOLATILITY = 0.05


# ==============================================================================
# 12. REPORTING CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class ReportingConfig:
    """Physical dimensions and margins for PDF generation (A4 standard)."""
    PAGE_WIDTH_A4: float = 595.28
    PAGE_HEIGHT_A4: float = 841.89
    MARGIN_LEFT: float = 50.0
    MARGIN_RIGHT: float = 50.0
    MARGIN_TOP: float = 50.0
    MARGIN_BOTTOM: float = 50.0

    @property
    def usable_width(self) -> float:
        """Available content width after margins."""
        return self.PAGE_WIDTH_A4 - self.MARGIN_LEFT - self.MARGIN_RIGHT

    @property
    def usable_height(self) -> float:
        """Available content height after margins."""
        return self.PAGE_HEIGHT_A4 - self.MARGIN_TOP - self.MARGIN_BOTTOM


# ==============================================================================
# 13. AUDIT WEIGHTS BY MODE
# ==============================================================================

class AuditWeights:
    """
    Weights assigned to audit pillars based on the data input strategy.

    AUTO: Higher focus on data source quality (Yahoo Finance stability).
    MANUAL: Higher focus on assumption risk (User convictions).
    """
    AUTO = {
        "DATA_CONFIDENCE": 0.30,
        "ASSUMPTION_RISK": 0.30,
        "MODEL_RISK": 0.25,
        "METHOD_FIT": 0.15,
    }

    MANUAL = {
        "DATA_CONFIDENCE": 0.10,
        "ASSUMPTION_RISK": 0.50,
        "MODEL_RISK": 0.20,
        "METHOD_FIT": 0.20,
    }

    @classmethod
    def get_weights(cls, is_manual: bool) -> Dict[str, float]:
        """Returns the specific weighting map for the current workflow."""
        return cls.MANUAL if is_manual else cls.AUTO


# ==============================================================================
# 14. SYSTEM DEFAULTS
# ==============================================================================

@dataclass(frozen=True)
class SystemDefaults:
    """High-level system defaults and caching policies."""
    DEFAULT_PROJECTION_YEARS: int = 5
    MIN_PROJECTION_YEARS: int = 1
    MAX_PROJECTION_YEARS: int = 15
    DEFAULT_RISK_FREE_RATE: float = 0.04
    DEFAULT_TAX_RATE: float = 0.25
    DEFAULT_PERPETUAL_GROWTH: float = 0.02
    MAX_PERPETUAL_GROWTH: float = 0.04
    CACHE_TTL_SHORT: int = 3600
    CACHE_TTL_LONG: int = 14400
    DEFAULT_MARKET_RISK_PREMIUM: float = 0.05


# ==============================================================================
# 15. LOADING VALIDATION (INTEGRITY CHECK)
# ==============================================================================

def _validate_constants():
    """Validates the logical consistency of constants upon module loading."""
    # Monte Carlo logic checks
    assert MonteCarloDefaults.MIN_SIMULATIONS < MonteCarloDefaults.MAX_SIMULATIONS
    assert MonteCarloDefaults.DEFAULT_SIMULATIONS >= MonteCarloDefaults.MIN_SIMULATIONS

    # Audit boundary checks
    assert AuditThresholds.BETA_MIN < AuditThresholds.BETA_MAX
    assert AuditThresholds.SOTP_REVENUE_GAP_WARNING < AuditThresholds.SOTP_REVENUE_GAP_ERROR

    # Statistical weight integrity
    assert abs(sum(AuditWeights.AUTO.values()) - 1.0) < 0.001
    assert abs(sum(AuditWeights.MANUAL.values()) - 1.0) < 0.001

    # UI sanity checks
    assert UIWidgetDefaults.MIN_PROJECTION_YEARS <= UIWidgetDefaults.DEFAULT_PROJECTION_YEARS
    assert UIWidgetDefaults.DEFAULT_PROJECTION_YEARS <= UIWidgetDefaults.MAX_PROJECTION_YEARS

    # Engine stability checks
    assert ValuationEngineDefaults.MAX_ITERATIONS > 0
    assert ValuationEngineDefaults.CONVERGENCE_TOLERANCE > 0

# Run integrity validation on import
_validate_constants()


# ==============================================================================
# 16. UI CONTROL PARAMETERS
# ==============================================================================

@dataclass(frozen=True)
class UIConstants:
    """Visual steering parameters for the Streamlit front-end."""

    # Internal step keys to exclude from main 'Calculation Proof' tab
    EXCLUDED_STEP_PREFIXES: tuple[str, ...] = ("MC_", "SOTP_DETAIL_", "BACKTEST_")

    MAX_STEPS_BEFORE_PAGINATION: int = 20
    DEFAULT_CHART_HEIGHT: int = 400

    # Visual alert thresholds (Institutional branding)
    WACC_WARNING_THRESHOLD: float = 0.15
    UPSIDE_SUCCESS_THRESHOLD: float = 0.20


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "MonteCarloDefaults",
    "PeerDefaults",
    "AuditThresholds",
    "AuditPenalties",
    "AuditWeights",
    "SystemDefaults",
    "MacroDefaults",
    "DataExtractionDefaults",
    "ValuationEngineDefaults",
    "ModelDefaults",
    "UIWidgetDefaults",
    "GrowthCalculationDefaults",
    "TechnicalDefaults",
    "ReportingConfig",
    "UIConstants"
]