"""
core/models.py

Modèles de données unifiés pour le moteur de valorisation.
Version : V1.2 — Chapitres 3 & 4 conformes (Glass Box Valuation Engine)

Principes non négociables :
- Contrat de sortie explicite et vérifiable (Chapitre 3)
- Traçabilité Glass Box complète et homogène (Chapitre 4)
- Comparabilité stricte inter-modèles
- Aucune étape de calcul implicite
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


# ============================================================
# 1. RÉFÉRENTIEL NORMATIF DES MÉTHODES
# ============================================================

class ValuationMode(str, Enum):
    """
    Référentiel officiel et normatif des méthodes de valorisation (V1).
    """

    FCFF_TWO_STAGE = "FCFF Two-Stage (Damodaran)"
    FCFF_NORMALIZED = "FCFF Normalized (Cyclical / Industrial)"
    FCFF_REVENUE_DRIVEN = "FCFF Revenue-Driven (High Growth / Tech)"
    RESIDUAL_INCOME_MODEL = "Residual Income Model (Penman)"
    GRAHAM_1974_REVISED = "Graham Intrinsic Value (1974 Revised)"


class InputSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class TerminalValueMethod(str, Enum):
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"


# ============================================================
# 2. GLASS BOX — STANDARD UNIVERSEL DE TRACE (CHAPITRE 4)
# ============================================================

@dataclass(frozen=True)
class TraceHypothesis:
    """
    Hypothèse financière explicite utilisée dans une étape de calcul.
    """
    name: str
    value: Any
    unit: Optional[str] = None
    source: Optional[str] = None
    comment: Optional[str] = None


@dataclass(frozen=True)
class CalculationStep:
    """
    Étape atomique, normative et auditée du raisonnement financier.

    Toute étape DOIT exposer :
    - la formule théorique
    - les hypothèses utilisées
    - la substitution numérique explicite
    - le résultat intermédiaire
    - l’unité
    - l’interprétation financière
    """

    label: str

    # Théorie
    theoretical_formula: str

    # Hypothèses explicites
    hypotheses: List[TraceHypothesis]

    # Substitution numérique
    numerical_substitution: str

    # Résultat
    result: float
    unit: str

    # Interprétation financière
    interpretation: str


# ============================================================
# 3. DONNÉES FINANCIÈRES (INPUT DU MODÈLE)
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
    beta: float

    total_debt: float
    cash_and_equivalents: float
    interest_expense: float

    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None

    eps_ttm: Optional[float] = None
    last_dividend: Optional[float] = None
    book_value_per_share: Optional[float] = None

    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None

    source_growth: str = "unknown"
    source_debt: str = "unknown"
    source_fcf: str = "unknown"


# ============================================================
# 4. PARAMÈTRES DU MODÈLE (HYPOTHÈSES)
# ============================================================

@dataclass
class DCFParameters:
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

    target_fcf_margin: Optional[float] = None

    manual_fcf_base: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None

    beta_volatility: float = 0.0
    growth_volatility: float = 0.0
    terminal_growth_volatility: float = 0.0
    num_simulations: Optional[int] = None

    def normalize_weights(self) -> None:
        total = self.target_equity_weight + self.target_debt_weight
        if total > 0:
            self.target_equity_weight /= total
            self.target_debt_weight /= total


# ============================================================
# 5. CONTRAT DE SORTIE — CHAPITRE 3
# ============================================================

@dataclass(frozen=True)
class ValuationOutputContract:
    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_equity_bridge: bool
    has_intrinsic_value: bool
    has_calculation_trace: bool

    def is_valid(self) -> bool:
        return all(vars(self).values())


# ============================================================
# 6. AUDIT
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
# 7. REQUÊTE DE VALORISATION
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
# 8. RÉSULTATS — CONTRAT DE SORTIE
# ============================================================

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
            self.upside_pct = (
                self.intrinsic_value_per_share / self.market_price
            ) - 1.0

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        raise NotImplementedError


# ============================================================
# 9. RÉSULTATS SPÉCIFIQUES
# ============================================================

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

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=bool(self.projected_fcfs),
            has_terminal_value=self.terminal_value is not None,
            has_equity_bridge=True,
            has_intrinsic_value=True,
            has_calculation_trace=len(self.calculation_trace) > 0
        )


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

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=bool(self.projected_residual_incomes),
            has_terminal_value=self.terminal_value_ri is not None,
            has_equity_bridge=True,
            has_intrinsic_value=True,
            has_calculation_trace=len(self.calculation_trace) > 0
        )


@dataclass(kw_only=True)
class GrahamValuationResult(ValuationResult):
    eps_used: float
    growth_rate_used: float
    aaa_yield_used: float

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=True,
            has_equity_bridge=True,
            has_intrinsic_value=True,
            has_calculation_trace=len(self.calculation_trace) > 0
        )
