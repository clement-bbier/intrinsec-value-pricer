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
# Audit Models (Nouveau)
# ============================================================

@dataclass
class AuditLog:
    """Un élément atomique du rapport d'audit."""
    category: str  # 'Données', 'Cohérence', 'Méthode'...
    severity: str  # 'info', 'low', 'medium', 'high', 'critical'
    message: str  # Description utilisateur
    penalty: float  # Impact sur le score (négatif)


@dataclass
class AuditReport:
    """Rapport d'audit complet."""
    global_score: float  # 0 à 100
    rating: str  # A, B, C, D, F
    audit_mode: str  # "Qualité Données (Auto)" ou "Cohérence (Expert)"
    logs: List[AuditLog]
    breakdown: Dict[str, float]  # Score par catégorie

    # Flags d'action
    block_monte_carlo: bool = False
    block_history: bool = False
    critical_warning: bool = False


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

    # Options stateless
    num_simulations: Optional[int] = None
    random_seed: Optional[int] = None

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

    # Audit Summary (Legacy compat, mais AuditReport est la source de vérité)
    audit_score: Optional[int] = None
    audit_rating: Optional[str] = None

    implied_growth_rate: Optional[float] = None


# ============================================================
# DCF Result
# ============================================================

@dataclass
class DCFResult:
    wacc: float
    cost_of_equity: float
    after_tax_cost_of_debt: float
    projected_fcfs: List[float]
    discount_factors: List[float]
    sum_discounted_fcf: float
    terminal_value: float
    discounted_terminal_value: float
    enterprise_value: float
    equity_value: float
    intrinsic_value_per_share: float

    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None


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

    # Intégration du rapport complet
    audit_report: Optional[AuditReport] = None

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