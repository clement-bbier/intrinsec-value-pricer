"""
src/config/constants.py

CENTRALIZED VALUATION SYSTEM CONSTANTS — GHOST RESOLUTION VERSION
==================================================================
Role: Ultimate source of truth for fallback values and system thresholds.
Architecture: Immutable frozen dataclasses.
Alignment: Synchronized with Pydantic field names for automated resolution.

Usage:
------
    from src.config.constants import ModelDefaults, AuditThresholds
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Tuple

logger = logging.getLogger(__name__)

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
# 2. PEERS / MULTIPLES
# ==============================================================================

@dataclass(frozen=True)
class PeerDefaults:
    """Settings for relative valuation and peer discovery."""
    MAX_PEERS_ANALYSIS: int = 5
    MIN_PEERS_REQUIRED: int = 2
    API_TIMEOUT_SECONDS: float = 12.0
    MAX_RETRY_ATTEMPTS: int = 1


# ==============================================================================
# 3. AUDIT - VALIDATION THRESHOLDS
# ==============================================================================

@dataclass(frozen=True)
class AuditThresholds:
    """Safety boundaries for financial health checks (Pillar 3)."""
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
# 4. MACRO & MARKET DEFAULTS (PILLAR 2)
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
# 5. MODEL DEFAULTS — ALIGNED WITH PYDANTIC (CRITICAL FOR RESOLVER)
# ==============================================================================

@dataclass(frozen=True)
class ModelDefaults:
    """
    Fallback values for all Parameters fields to ensure 0% None propagation.

    Naming corresponds to Pydantic field attributes for easier mapping.
    """
    # --- Pillar 2: Common / Capital Structure ---
    DEFAULT_TOTAL_DEBT: float = 0.0
    DEFAULT_CASH_EQUIVALENTS: float = 0.0
    DEFAULT_MINORITY_INTERESTS: float = 0.0
    DEFAULT_PENSION_PROVISIONS: float = 0.0
    DEFAULT_SHARES_OUTSTANDING: float = 1.0
    DEFAULT_ANNUAL_DILUTION_RATE: float = 0.0
    DEFAULT_BETA: float = 1.0
    DEFAULT_COST_OF_DEBT: float = 0.06

    # --- Pillar 3: Strategy Anchors ---
    DEFAULT_REVENUE_TTM: float = 0.0
    DEFAULT_EBIT_TTM: float = 0.0
    DEFAULT_NET_INCOME_TTM: float = 0.0
    DEFAULT_FCF_TTM: float = 0.0
    DEFAULT_NET_BORROWING_TTM: float = 0.0

    # --- Pillar 3: Strategy Specifics ---
    DEFAULT_EPS_TTM: float = 0.0
    DEFAULT_DIVIDEND_PS: float = 0.0
    DEFAULT_BOOK_VALUE_PS: float = 0.0
    DEFAULT_PERSISTENCE_FACTOR: float = 0.60  # RIM Persistence (omega)

    # --- Projections & Exit ---
    DEFAULT_PROJECTION_YEARS: int = 5
    DEFAULT_GROWTH_RATE: float = 0.05
    DEFAULT_TERMINAL_GROWTH: float = 0.02
    DEFAULT_EXIT_MULTIPLE: float = 15.0


# ==============================================================================
# 6. VALUATION ENGINES TECHNICAL CONSTANTS
# ==============================================================================

@dataclass(frozen=True)
class ValuationEngineDefaults:
    """Numerical solver settings and credit rating spreads."""
    MAX_ITERATIONS: int = 50
    CONVERGENCE_TOLERANCE: float = 1e-6

    # Credit Rating Spreads (ICR-based) for Cost of Debt synthetic calculation
    SPREADS_LARGE_CAP: List[Tuple[float, float]] = None # Initialized in __post_init__ or below

ValuationEngineDefaults.SPREADS_LARGE_CAP = [
    (8.5, 0.0045), (6.5, 0.0060), (5.5, 0.0077), (4.25, 0.0085),
    (3.0, 0.0095), (2.5, 0.0120), (2.25, 0.0155), (2.0, 0.0183),
    (-999, 0.2000)
]


# ==============================================================================
# 7. UI WIDGETS & CONSTRAINTS
# ==============================================================================

@dataclass(frozen=True)
class UIWidgetDefaults:
    """Human-readable input limits for Streamlit widgets."""
    MIN_PROJECTION_YEARS: int = 1
    MAX_PROJECTION_YEARS: int = 15
    MAX_GROWTH_RATE: float = 500.0  # %
    MAX_TAX_RATE: float = 100.0    # %
    MAX_BETA: float = 5.0


# ==============================================================================
# 8. AUDIT WEIGHTS
# ==============================================================================

class AuditWeights:
    """Weights assigned to audit pillars."""
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


# ==============================================================================
# 9. SYSTEM CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class SystemDefaults:
    """Global system behaviors."""
    CACHE_TTL_SHORT: int = 3600
    CACHE_TTL_LONG: int = 86400


# ==============================================================================
# 10. LOADING VALIDATION
# ==============================================================================

def _validate_constants():
    """Performs integrity checks upon module import."""
    assert MonteCarloDefaults.MIN_SIMULATIONS < MonteCarloDefaults.MAX_SIMULATIONS
    assert ModelDefaults.DEFAULT_SHARES_OUTSTANDING > 0
    assert abs(sum(AuditWeights.AUTO.values()) - 1.0) < 0.001

_validate_constants()

# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "MonteCarloDefaults",
    "PeerDefaults",
    "AuditThresholds",
    "MacroDefaults",
    "ModelDefaults",
    "ValuationEngineDefaults",
    "UIWidgetDefaults",
    "AuditWeights",
    "SystemDefaults"
]