from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValuationMode(str, Enum):
    SIMPLE_FCFF = "SIMPLE_FCFF"
    FUNDAMENTAL_FCFF = "FUNDAMENTAL_FCFF"
    MONTE_CARLO = "MONTE_CARLO"


class InputSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


@dataclass
class DCFParameters:
    """
    Core parameter container.

    Conventions:
    - rates in decimal (0.08 = 8%)
    - years are integers
    """
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

    # Canonical target capital structure fields used in engines/strategies
    target_equity_weight: float = 1.0
    target_debt_weight: float = 0.0

    # Optional overrides
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None

    # Backward-compatible aliases (do not remove):
    # Some parts of the code may refer to equity_weight/debt_weight or cost_of_equity_override.
    equity_weight: Optional[float] = None
    debt_weight: Optional[float] = None
    cost_of_equity_override: Optional[float] = None

    def normalize_weights(self) -> None:
        """
        Normalizes/aligns weight fields.
        Priority:
        - target_* if explicitly set
        - else equity_weight/debt_weight if provided
        """
        if self.equity_weight is not None and self.debt_weight is not None:
            self.target_equity_weight = float(self.equity_weight)
            self.target_debt_weight = float(self.debt_weight)

        total = float(self.target_equity_weight) + float(self.target_debt_weight)
        if total > 0:
            self.target_equity_weight /= total
            self.target_debt_weight /= total

        # Align legacy fields for downstream display if needed
        self.equity_weight = self.target_equity_weight
        self.debt_weight = self.target_debt_weight

        if self.manual_cost_of_equity is None and self.cost_of_equity_override is not None:
            self.manual_cost_of_equity = self.cost_of_equity_override


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


@dataclass
class DCFResult:
    enterprise_value: float
    equity_value: float
    intrinsic_value_per_share: float

    discounted_terminal_value: float
    terminal_value: float

    simulation_results: Optional[List[float]] = None


@dataclass(frozen=True)
class ValuationRequest:
    """
    Strict DTO: UI -> Workflow -> Engine.

    manual_params/manual_beta are only valid when input_source=MANUAL.
    """
    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource

    manual_params: Optional[DCFParameters] = None
    manual_beta: Optional[float] = None

    options: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValuationResult:
    """
    Strict DTO: Engine/Workflow -> UI.
    Keeps raw components for existing UI functions, plus computed headline metrics.
    """
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
