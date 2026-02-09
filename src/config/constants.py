"""
src/config/constants.py

CENTRALIZED VALUATION SYSTEM CONSTANTS
======================================
Role: Ultimate source of truth for fallback values and system thresholds.
Architecture: Mix of Dataclasses (for config objects) and Static Classes (for lookups).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Dict

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
# 2. SENSITIVITY ANALYSIS
# ==============================================================================

@dataclass(frozen=True)
class SensitivityDefaults:
    DEFAULT_STEPS: int = 5
    DEFAULT_WACC_SPAN: float = 0.01
    DEFAULT_GROWTH_SPAN: float = 0.005
    DEFAULT_YIELD_SPAN: float = 0.01


# ==============================================================================
# 3. PEERS / MULTIPLES
# ==============================================================================

@dataclass(frozen=True)
class PeerDefaults:
    MAX_PEERS_ANALYSIS: int = 5
    MIN_PEERS_REQUIRED: int = 2
    API_TIMEOUT_SECONDS: float = 12.0
    MAX_RETRY_ATTEMPTS: int = 1


# ==============================================================================
# 4. BACKTEST & SOTP
# ==============================================================================

@dataclass(frozen=True)
class BacktestDefaults:
    DEFAULT_LOOKBACK_YEARS: int = 3
    MAX_LOOKBACK_YEARS: int = 10

@dataclass(frozen=True)
class SOTPDefaults:
    DEFAULT_CONGLOMERATE_DISCOUNT: float = 0.0


# ==============================================================================
# 5. SCENARIOS
# ==============================================================================

@dataclass(frozen=True)
class ScenarioDefaults:
    DEFAULT_CASE_NAME: str = "Base Case"
    DEFAULT_PROBABILITY: float = 1.0
    DEFAULT_GROWTH_ADJUSTMENT: float = 0.0
    DEFAULT_MARGIN_ADJUSTMENT: float = 0.0
    STANDARD_LABELS: Tuple[str, str, str] = ("Bear Case", "Base Case", "Bull Case")
    STANDARD_WEIGHTS: Tuple[float, float, float] = (0.25, 0.50, 0.25)


# ==============================================================================
# 6. VALIDATION THRESHOLDS
# ==============================================================================

@dataclass(frozen=True)
class ValidationThresholds:
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
# 7. MACRO & MARKET
# ==============================================================================

@dataclass(frozen=True)
class MacroDefaults:
    DEFAULT_RISK_FREE_RATE: float = 0.0425
    DEFAULT_MARKET_RISK_PREMIUM: float = 0.05
    DEFAULT_TAX_RATE: float = 0.25
    DEFAULT_INFLATION_RATE: float = 0.02
    DEFAULT_CORPORATE_AAA_YIELD: float = 0.045
    LARGE_CAP_THRESHOLD: float = 5_000_000_000


# ==============================================================================
# 8. MODEL DEFAULTS
# ==============================================================================

@dataclass(frozen=True)
class GrowthCalculationDefaults:
    DEFAULT_FCF_MARGIN_TARGET: float = 0.15
    DEFAULT_REVENUE_GROWTH_START: float = 0.10

@dataclass(frozen=True)
class ModelDefaults:
    # Capital Structure
    DEFAULT_WACC: float = 0.10
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

    # Financials
    DEFAULT_REVENUE_TTM: float = 0.0
    DEFAULT_EBIT_TTM: float = 0.0
    DEFAULT_NET_INCOME_TTM: float = 0.0
    DEFAULT_FCF_TTM: float = 0.0
    DEFAULT_NET_BORROWING_TTM: float = 0.0

    # Per Share
    DEFAULT_EPS_TTM: float = 0.0
    DEFAULT_DIVIDEND_PS: float = 0.0
    DEFAULT_BOOK_VALUE_PS: float = 0.0
    DEFAULT_PERSISTENCE_FACTOR: float = 0.60

    # Projections
    DEFAULT_PROJECTION_YEARS: int = 5
    DEFAULT_GROWTH_RATE: float = 0.05
    DEFAULT_TERMINAL_GROWTH: float = 0.02
    DEFAULT_EXIT_MULTIPLE: float = 15.0


# ==============================================================================
# 9. VALUATION ENGINES CONSTANTS (STATIC)
# ==============================================================================

class ValuationEngineDefaults:
    """
    Static constants for the valuation engine.
    NOT a dataclass, so attributes are accessible without instantiation.
    """

    MAX_ITERATIONS: int = 50
    CONVERGENCE_TOLERANCE: float = 1e-6
    REVERSE_DCF_LOW_BOUND: float = -0.50
    REVERSE_DCF_HIGH_BOUND: float = 1.00
    MAX_DILUTION_CLAMPING: float = 0.10

    # --- Credit Rating Spreads (ICR-based) ---
    # Converted to DICT for O(1) Lookup in financial_math.py

    # Large Cap (> $5B)
    SPREADS_LARGE_CAP: Dict[float, float] = {
        8.5: 0.0069,   # AAA
        6.5: 0.0085,   # AA
        5.5: 0.0107,   # A+
        4.25: 0.0118,  # A
        3.0: 0.0133,   # A-
        2.5: 0.0171,   # BBB
        2.25: 0.0216,  # BB+
        2.0: 0.0270,   # BB
        1.75: 0.0387,  # B+
        1.5: 0.0522,   # B
        1.25: 0.0810,  # B-
        0.8: 0.1116,   # CCC
        0.65: 0.1575,  # CC
        0.2: 0.1750,   # C
        -999.0: 0.2000 # D (Default)
    }

    # Small/Mid Cap (< $5B)
    SPREADS_SMALL_MID_CAP: Dict[float, float] = {
        12.5: 0.0069,
        9.5: 0.0085,
        7.5: 0.0107,
        6.0: 0.0118,
        4.5: 0.0133,
        4.0: 0.0171,
        3.5: 0.0216,
        3.0: 0.0270,
        2.5: 0.0387,
        2.0: 0.0522,
        1.5: 0.0810,
        1.25: 0.1116,
        0.8: 0.1575,
        0.5: 0.1750,
        -999.0: 0.2000
    }


# ==============================================================================
# 10. UI WIDGETS
# ==============================================================================

@dataclass(frozen=True)
class UIWidgetDefaults:
    # Projection Temporelle
    DEFAULT_PROJECTION_YEARS: int = 5
    MIN_PROJECTION_YEARS: int = 1
    MAX_PROJECTION_YEARS: int = 15

    # Taux de Croissance (g) - Bornes (%)
    MIN_GROWTH_RATE: float = -100.0  # Décroissance totale possible
    MAX_GROWTH_RATE: float = 500.0   # Hyper-croissance (Startup/Biotech)

    # Paramètres Fiscaux et Risque
    MAX_TAX_RATE: float = 100.0      # Impôt confiscatoire théorique
    MAX_BETA: float = 5.0            # Volatilité extrême (> 5 est souvent du bruit)


# ==============================================================================
# 11. SYSTEM CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class SystemDefaults:
    CACHE_TTL_SHORT: int = 3600
    CACHE_TTL_LONG: int = 86400