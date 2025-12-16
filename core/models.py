from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC


# ============================================================
# Enums
# ============================================================

class ValuationMode(str, Enum):
    SIMPLE_FCFF = "SIMPLE_FCFF"
    FUNDAMENTAL_FCFF = "FUNDAMENTAL_FCFF"
    GROWTH_TECH = "GROWTH_TECH"
    MONTE_CARLO = "MONTE_CARLO"
    DDM_BANKS = "DDM_BANKS"
    GRAHAM_VALUE = "GRAHAM_VALUE"


class InputSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


# ============================================================
# Financial & Parameters Inputs
# ============================================================

@dataclass
class CompanyFinancials:
    ticker: str
    currency: str
    sector: str
    industry: str
    country: str

    current_price: float
    shares_outstanding: float

    total_debt: float
    cash_and_equivalents: float
    interest_expense: float

    beta: float

    # Champs optionnels (critiques pour Graham et DDM)
    last_dividend: Optional[float] = None
    book_value_per_share: Optional[float] = None
    eps_ttm: Optional[float] = None

    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None
    revenue_ttm: Optional[float] = None

    # Audit info
    source_growth: str = "unknown"
    source_debt: str = "unknown"
    source_fcf: str = "unknown"
    audit_score: Optional[int] = None
    audit_rating: Optional[str] = None


@dataclass
class DCFParameters:
    """Paramètres unifiés pour tous les moteurs."""
    risk_free_rate: float
    market_risk_premium: float
    cost_of_debt: float
    tax_rate: float

    fcf_growth_rate: float
    perpetual_growth_rate: float
    projection_years: int

    # Options avancées
    high_growth_years: int = 0
    target_equity_weight: float = 0.0
    target_debt_weight: float = 0.0
    target_fcf_margin: Optional[float] = 0.25

    # Overrides & Monte Carlo
    manual_fcf_base: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None

    beta_volatility: float = 0.0
    growth_volatility: float = 0.0
    terminal_growth_volatility: float = 0.0
    num_simulations: Optional[int] = None

    def normalize_weights(self) -> None:
        """Assure que We + Wd = 1.0 si définis."""
        total = self.target_equity_weight + self.target_debt_weight
        if total > 0.001:
            self.target_equity_weight /= total
            self.target_debt_weight /= total


# ============================================================
# Audit Models
# ============================================================

@dataclass
class AuditLog:
    category: str
    severity: str
    message: str
    penalty: float


@dataclass
class AuditReport:
    global_score: float
    rating: str
    audit_mode: str
    logs: List[AuditLog]
    breakdown: Dict[str, float]
    block_monte_carlo: bool = False
    block_history: bool = False
    critical_warning: bool = False


# ============================================================
# Valuation Request
# ============================================================

@dataclass(frozen=True)
class ValuationRequest:
    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource
    manual_params: Optional[DCFParameters] = None
    manual_beta: Optional[float] = None
    options: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Abstract Valuation Result (Polymorphic)
# ============================================================

# CORRECTION : Ajout de kw_only=True pour supporter l'héritage avec valeurs par défaut
@dataclass(kw_only=True)
class ValuationResult(ABC):
    """Classe de base pour tout résultat de valorisation."""
    request: Optional[ValuationRequest]
    financials: CompanyFinancials
    params: DCFParameters

    intrinsic_value_per_share: float
    market_price: float
    upside_pct: Optional[float] = None

    audit_report: Optional[AuditReport] = None
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.market_price > 0:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0


# --- Subclass 1: Standard DCF (Simple, Fundamental, Growth) ---
@dataclass(kw_only=True)
class DCFValuationResult(ValuationResult):
    wacc: float
    cost_of_equity: float
    cost_of_debt_after_tax: float

    projected_fcfs: List[float]
    discount_factors: List[float]

    sum_discounted_fcf: float
    terminal_value: float
    discounted_terminal_value: float

    enterprise_value: float
    equity_value: float


# --- Subclass 2: DDM (Banks) ---
@dataclass(kw_only=True)
class DDMValuationResult(ValuationResult):
    cost_of_equity: float

    projected_dividends: List[float]
    discount_factors: List[float]

    sum_discounted_dividends: float
    terminal_value: float
    discounted_terminal_value: float

    equity_value: float


# --- Subclass 3: Graham (Value) ---
@dataclass(kw_only=True)
class GrahamValuationResult(ValuationResult):
    eps_used: float
    book_value_used: float
    graham_multiplier: float = 22.5