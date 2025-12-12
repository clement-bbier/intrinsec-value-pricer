# Fichier : core/models.py

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ============================================================
# Enums
# ============================================================

class ValuationMode(str, Enum):
    SIMPLE_FCFF = "SIMPLE_FCFF"
    FUNDAMENTAL_FCFF = "FUNDAMENTAL_FCFF"
    MONTE_CARLO = "MONTE_CARLO"

class InputSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"

# ============================================================
# Core Parameters
# ============================================================

@dataclass
class DCFParameters:
    risk_free_rate: float
    market_risk_premium: float
    cost_of_debt: float
    tax_rate: float
    fcf_growth_rate: float
    perpetual_growth_rate: float
    projection_years: int
    high_growth_years: int = 0
    beta_volatility: float = 0.0
    growth_volatility: float = 0.0
    terminal_growth_volatility: float = 0.0
    manual_fcf_base: Optional[float] = None
    target_equity_weight: float = 1.0
    target_debt_weight: float = 0.0
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None
    # Legacy aliases
    equity_weight: Optional[float] = None
    debt_weight: Optional[float] = None
    cost_of_equity_override: Optional[float] = None

    def normalize_weights(self) -> None:
        if self.equity_weight is not None and self.debt_weight is not None:
            self.target_equity_weight = float(self.equity_weight)
            self.target_debt_weight = float(self.debt_weight)
        total = float(self.target_equity_weight) + float(self.target_debt_weight)
        if total > 0:
            self.target_equity_weight /= total
            self.target_debt_weight /= total
        self.equity_weight = self.target_equity_weight
        self.debt_weight = self.target_debt_weight
        if self.manual_cost_of_equity is None and self.cost_of_equity_override is not None:
            self.manual_cost_of_equity = self.cost_of_equity_override

# ============================================================
# Financial Snapshot
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
    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None
    source_growth: str = "unknown"
    source_debt: str = "unknown"
    source_fcf: str = "unknown"
    audit_score: Optional[int] = None
    audit_rating: Optional[str] = None
    audit_details: Optional[str] = None
    audit_breakdown: Optional[Dict[str, Any]] = None
    audit_logs: List[str] = field(default_factory=list)
    implied_growth_rate: Optional[float] = None

# ============================================================
# DCF Result (ENGINE OUTPUT)
# ============================================================

@dataclass
class DCFResult:
    """
    Output of a valuation engine.
    Single Source of Truth for math results.
    """
    # --- Discounting ---
    wacc: float                     # <--- CE CHAMP EST OBLIGATOIRE
    cost_of_equity: float
    after_tax_cost_of_debt: float

    # --- Cash-flow projection ---
    projected_fcfs: List[float]
    discount_factors: List[float]
    sum_discounted_fcf: float

    # --- Terminal value ---
    terminal_value: float
    discounted_terminal_value: float

    # --- Valuation ---
    enterprise_value: float
    equity_value: float
    intrinsic_value_per_share: float

    # --- Monte Carlo (optional) ---
    simulation_results: Optional[List[float]] = None

# ============================================================
# Valuation Request & Result
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

@dataclass(frozen=True)
class ValuationResult:
    request: ValuationRequest
    financials: CompanyFinancials
    params: DCFParameters
    dcf: DCFResult
    audit_score: Optional[int] = None
    audit_rating: Optional[str] = None
    audit_details: Optional[str] = None
    audit_breakdown: Optional[Dict[str, Any]] = None
    audit_logs: List[str] = field(default_factory=list)
    intrinsic_value_per_share: float = 0.0
    market_price: float = 0.0
    upside_pct: Optional[float] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        mp = float(self.financials.current_price)
        iv = float(self.dcf.intrinsic_value_per_share)
        object.__setattr__(self, "market_price", mp)
        object.__setattr__(self, "intrinsic_value_per_share", iv)
        object.__setattr__(self, "upside_pct", (iv / mp - 1.0) if mp > 0 else None)