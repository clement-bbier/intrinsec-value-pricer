"""
src/config/constants.py

CENTRALIZED VALUATION SYSTEM CONSTANTS
======================================
Role: Ultimate source of truth for fallback values and system thresholds.
Architecture: Immutable frozen dataclasses.
Alignment: Synchronized with Pydantic field names for automated resolution.

Usage:
------
    from src.config.constants import ModelDefaults, ValidationThresholds
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

# ==============================================================================
# 1. MONTE CARLO SIMULATION
# ==============================================================================

@dataclass(frozen=True)
class MonteCarloDefaults:
    """Standard parameters for stochastic simulations."""
    MIN_SIMULATIONS: int = 100
    MAX_SIMULATIONS: int = 20_000
    DEFAULT_SIMULATIONS: int = 5_000
    STEP_SIMULATIONS: int = 200
    DEFAULT_RHO: float = -0.30
    MIN_VALID_RATIO: float = 0.80
    CLAMPING_THRESHOLD: float = 0.10


# ==============================================================================
# 2. SENSITIVITY ANALYSIS (DETERMINISTIC)
# ==============================================================================

@dataclass(frozen=True)
class SensitivityDefaults:
    """Defaults for the WACC/Growth sensitivity heatmap."""
    DEFAULT_STEPS: int = 5              # 5x5 Matrix
    DEFAULT_WACC_SPAN: float = 0.01     # +/- 1.0%
    DEFAULT_GROWTH_SPAN: float = 0.005  # +/- 0.5%
    DEFAULT_YIELD_SPAN: float = 0.01    # +/- 1.0% (Graham/RIM)


# ==============================================================================
# 3. PEERS / MULTIPLES
# ==============================================================================

@dataclass(frozen=True)
class PeerDefaults:
    """Settings for relative valuation and peer discovery."""
    MAX_PEERS_ANALYSIS: int = 5
    MIN_PEERS_REQUIRED: int = 2
    API_TIMEOUT_SECONDS: float = 12.0
    MAX_RETRY_ATTEMPTS: int = 1


# ==============================================================================
# 4. BACKTEST & SOTP DEFAULTS
# ==============================================================================

@dataclass(frozen=True)
class BacktestDefaults:
    """Defaults for Historical Validation."""
    DEFAULT_LOOKBACK_YEARS: int = 3
    MAX_LOOKBACK_YEARS: int = 10

@dataclass(frozen=True)
class SOTPDefaults:
    """Defaults for Sum-of-the-Parts."""
    DEFAULT_CONGLOMERATE_DISCOUNT: float = 0.0


# ==============================================================================
# 5. SCENARIO DEFAULTS
# ==============================================================================

@dataclass(frozen=True)
class ScenarioDefaults:
    """Defaults for deterministic scenarios."""
    DEFAULT_CASE_NAME: str = "Base Case"
    DEFAULT_PROBABILITY: float = 1.0
    DEFAULT_GROWTH_ADJUSTMENT: float = 0.0
    DEFAULT_MARGIN_ADJUSTMENT: float = 0.0
    STANDARD_LABELS: Tuple[str, str, str] = ("Bear Case", "Base Case", "Bull Case")
    STANDARD_WEIGHTS: Tuple[float, float, float] = (0.25, 0.50, 0.25)


# ==============================================================================
# 6. VALIDATION THRESHOLDS (Ex-Audit)
# ==============================================================================

@dataclass(frozen=True)
class ValidationThresholds:
    """Safety boundaries for financial health checks (Sanity Checks)."""
    ICR_MIN: float = 1.5
    BETA_MIN: float = 0.4
    BETA_MAX: float = 3.0
    LIQUIDITY_RATIO_MIN: float = 1.0

    # SOTP
    SOTP_REVENUE_GAP_WARNING: float = 0.05
    SOTP_REVENUE_GAP_ERROR: float = 0.15
    SOTP_DISCOUNT_MAX: float = 0.25

    # Gordon Growth Model Safety
    WACC_G_SPREAD_MIN: float = 0.01
    WACC_G_SPREAD_WARNING: float = 0.02

    # Cash Flow Integrity
    FCF_GROWTH_MAX: float = 0.25
    FCF_MARGIN_MIN: float = 0.05
    REINVESTMENT_RATE_MAX: float = 1.0


# ==============================================================================
# 7. MACRO & MARKET DEFAULTS
# ==============================================================================

@dataclass(frozen=True)
class MacroDefaults:
    """Regional and global economic baseline rates."""
    DEFAULT_RISK_FREE_RATE: float = 0.0425
    DEFAULT_MARKET_RISK_PREMIUM: float = 0.05
    DEFAULT_TAX_RATE: float = 0.25
    DEFAULT_INFLATION_RATE: float = 0.02
    DEFAULT_CORPORATE_AAA_YIELD: float = 0.045
    LARGE_CAP_THRESHOLD: float = 5_000_000_000


# ==============================================================================
# 8. MODEL & CALCULATION DEFAULTS
# ==============================================================================

@dataclass(frozen=True)
class GrowthCalculationDefaults:
    """
    Defaults specific to the flow projection engines (Growth/Margin modes).
    Used by flow_projector.py.
    """
    DEFAULT_FCF_MARGIN_TARGET: float = 0.15
    DEFAULT_REVENUE_GROWTH_START: float = 0.10


@dataclass(frozen=True)
class ModelDefaults:
    """
    Fallback values for Parameters to ensure 0% None propagation.
    Naming corresponds to Pydantic field attributes.
    """
    # Capital Structure
    DEFAULT_WACC = None
    DEFAULT_PAYOUT_RATIO: float = 0.50
    DEFAULT_FCF_MARGIN_TARGET: float = 0.15
    DEFAULT_REVENUE_GROWTH_START: float = 0.10
    DEFAULT_RESULT_VALUE: float = 0.0
    DEFAULT_STEP_ID: int = 0
    DEFAULT_TOTAL_DEBT: float = 0.0
    DEFAULT_CASH_EQUIVALENTS: float = 0.0
    DEFAULT_MINORITY_INTERESTS: float = 0.0
    DEFAULT_PENSION_PROVISIONS: float = 0.0
    DEFAULT_SHARES_OUTSTANDING: float = 1.0
    DEFAULT_ANNUAL_DILUTION_RATE: float = 0.0
    DEFAULT_BETA: float = 1.0
    DEFAULT_COST_OF_DEBT: float = 0.06

    # Financials TTM
    DEFAULT_REVENUE_TTM: float = 0.0
    DEFAULT_EBIT_TTM: float = 0.0
    DEFAULT_NET_INCOME_TTM: float = 0.0
    DEFAULT_FCF_TTM: float = 0.0
    DEFAULT_NET_BORROWING_TTM: float = 0.0

    # Per Share & Misc
    DEFAULT_EPS_TTM: float = 0.0
    DEFAULT_DIVIDEND_PS: float = 0.0
    DEFAULT_BOOK_VALUE_PS: float = 0.0
    DEFAULT_PERSISTENCE_FACTOR: float = 0.60  # RIM Persistence (omega)

    # Projections
    DEFAULT_PROJECTION_YEARS: int = 5
    DEFAULT_GROWTH_RATE: float = 0.05
    DEFAULT_TERMINAL_GROWTH: float = 0.02
    DEFAULT_EXIT_MULTIPLE: float = 15.0


# ==============================================================================
# 9. VALUATION ENGINES CONSTANTS
# ==============================================================================

@dataclass(frozen=True)
class ValuationEngineDefaults:
    """
    Numerical solver settings and credit rating spreads (Damodaran).
    """

    MAX_ITERATIONS: int = 50
    CONVERGENCE_TOLERANCE: float = 1e-6
    REVERSE_DCF_LOW_BOUND: float = -0.50
    REVERSE_DCF_HIGH_BOUND: float = 1.00

    MAX_DILUTION_CLAMPING: float = 0.10

    # --- Credit Rating Spreads (ICR-based) ---
    # Format: List of (ICR Threshold, Spread)
    # Logic: If ICR > Threshold, use Spread. Order: Descending Threshold.

    # Large Cap (> $5B)
    SPREADS_LARGE_CAP: List[Tuple[float, float]] = field(default_factory=lambda: [
        (8.5, 0.0069),  # AAA
        (6.5, 0.0085),  # AA
        (5.5, 0.0107),  # A+
        (4.25, 0.0118),  # A
        (3.0, 0.0133),  # A-
        (2.5, 0.0171),  # BBB
        (2.25, 0.0216),  # BB+
        (2.0, 0.0270),  # BB
        (1.75, 0.0387),  # B+
        (1.5, 0.0522),  # B
        (1.25, 0.0810),  # B-
        (0.8, 0.1116),  # CCC
        (0.65, 0.1575),  # CC
        (0.2, 0.1750),  # C
        (-999, 0.2000)  # D (Default)
    ])

    # Small/Mid Cap (< $5B) - Higher risk premiums for same coverage
    SPREADS_SMALL_MID_CAP: List[Tuple[float, float]] = field(default_factory=lambda: [
        (12.5, 0.0069),  # AAA
        (9.5, 0.0085),  # AA
        (7.5, 0.0107),  # A+
        (6.0, 0.0118),  # A
        (4.5, 0.0133),  # A-
        (4.0, 0.0171),  # BBB
        (3.5, 0.0216),  # BB+
        (3.0, 0.0270),  # BB
        (2.5, 0.0387),  # B+
        (2.0, 0.0522),  # B
        (1.5, 0.0810),  # B-
        (1.25, 0.1116),  # CCC
        (0.8, 0.1575),  # CC
        (0.5, 0.1750),  # C
        (-999, 0.2000)  # D
    ])


# ==============================================================================
# 10. UI WIDGETS
# ==============================================================================

@dataclass(frozen=True)
class UIWidgetDefaults:
    """Human-readable input limits for UI widgets."""
    MIN_PROJECTION_YEARS: int = 1
    MAX_PROJECTION_YEARS: int = 15
    MAX_GROWTH_RATE: float = 500.0  # %
    MAX_TAX_RATE: float = 100.0     # %
    MAX_BETA: float = 5.0


# ==============================================================================
# 11. SYSTEM CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class SystemDefaults:
    """Global system behaviors."""
    CACHE_TTL_SHORT: int = 3600
    CACHE_TTL_LONG: int = 86400