from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC


# ============================================================
# 1. ENUMS & CONSTANTES
# ============================================================

class ValuationMode(str, Enum):
    DISCOUNTED_CASH_FLOW_STANDARD = "Two-Stage FCFF (Standard)"
    NORMALIZED_FCFF_CYCLICAL = "Normalized FCFF (Cyclical/Industrial)"
    REVENUE_DRIVEN_GROWTH = "Revenue-Driven (High Growth/Tech)"
    PROBABILISTIC_DCF_MONTE_CARLO = "Probabilistic DCF (Monte Carlo)"
    RESIDUAL_INCOME_MODEL = "Residual Income Model (Banks/Insurance)"
    GRAHAM_1974_REVISED = "Graham Intrinsic Value (1974 Revised)"


class InputSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class TerminalValueMethod(str, Enum):
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"


# ============================================================
# 2. TRAÇABILITÉ
# ============================================================

@dataclass
class CalculationStep:
    label: str
    formula: str
    values: str
    result: float
    unit: str
    description: str


# ============================================================
# 3. DONNÉES FINANCIÈRES
# ============================================================

@dataclass
class CompanyFinancials:
    """Snapshot des données financières."""
    # --- CHAMPS OBLIGATOIRES (Doivent être au début) ---
    ticker: str
    currency: str
    sector: str
    industry: str
    country: str

    current_price: float
    shares_outstanding: float

    # Bilan
    total_debt: float
    cash_and_equivalents: float
    interest_expense: float

    # Indicateur de Risque (OBLIGATOIRE)
    beta: float

    # --- CHAMPS OPTIONNELS (Avec valeurs par défaut) ---
    # Critiques pour certains modèles spécifiques
    book_value_per_share: Optional[float] = None

    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None

    eps_ttm: Optional[float] = None
    last_dividend: Optional[float] = None

    # Free Cash Flow
    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None

    # Audit Metadata
    source_growth: str = "unknown"
    source_debt: str = "unknown"
    source_fcf: str = "unknown"
    audit_score: Optional[int] = None
    audit_rating: Optional[str] = None


@dataclass
class DCFParameters:
    """Paramètres unifiés."""

    risk_free_rate: float
    market_risk_premium: float
    corporate_aaa_yield: float

    cost_of_debt: float
    tax_rate: float

    fcf_growth_rate: float
    projection_years: int
    high_growth_years: int = 0

    terminal_method: TerminalValueMethod = TerminalValueMethod.GORDON_GROWTH
    perpetual_growth_rate: float = 0.02
    exit_multiple_value: Optional[float] = None

    target_equity_weight: float = 0.0
    target_debt_weight: float = 0.0

    target_fcf_margin: Optional[float] = 0.25

    manual_fcf_base: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None

    beta_volatility: float = 0.0
    growth_volatility: float = 0.0
    terminal_growth_volatility: float = 0.0
    num_simulations: Optional[int] = None

    def normalize_weights(self) -> None:
        total = self.target_equity_weight + self.target_debt_weight
        if total > 0.001:
            self.target_equity_weight /= total
            self.target_debt_weight /= total


# ============================================================
# 4. AUDIT & RÉSULTATS
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


@dataclass(frozen=True)
class ValuationRequest:
    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource
    manual_params: Optional[DCFParameters] = None
    manual_beta: Optional[float] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class ValuationResult(ABC):
    request: Optional[ValuationRequest]
    financials: CompanyFinancials
    params: DCFParameters

    intrinsic_value_per_share: float
    market_price: float
    upside_pct: Optional[float] = None

    calculation_trace: List[CalculationStep] = field(default_factory=list)

    audit_report: Optional[AuditReport] = None
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.market_price > 0:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0


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


@dataclass(kw_only=True)
class RIMValuationResult(ValuationResult):
    cost_of_equity: float
    current_book_value: float
    projected_residual_incomes: List[float]
    projected_book_values: List[float]
    discount_factors: List[float]
    sum_discounted_ri: float
    terminal_value_ri: float
    discounted_terminal_value: float
    total_equity_value: float


@dataclass(kw_only=True)
class GrahamValuationResult(ValuationResult):
    eps_used: float
    growth_rate_used: float
    aaa_yield_used: float
    base_pe: float = 8.5
    multiplier_factor: float = 2.0