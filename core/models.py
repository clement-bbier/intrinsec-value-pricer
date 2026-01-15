"""
core/models.py

Modèles de données unifiés pour le moteur de valorisation.
Version : V9.7 — Sprint 1 Final : Restoration of Computed Dividends & Data Contracts

Principes appliqués :
- SOLID : Propriétés calculées isolées dans le modèle de données.
- Robustesse : Gestion des valeurs nulles (None) pour les dividendes.
- Glass Box : Traçabilité complète maintenue.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==============================================================================
# 1. RÉFÉRENTIEL NORMATIF (ENUMS)
# ==============================================================================

class ValuationMode(str, Enum):
    # Approche Entité (Firm Value)
    FCFF_TWO_STAGE = "FCFF Two-Stage (Damodaran)"
    FCFF_NORMALIZED = "FCFF Normalized (Cyclical / Industrial)"
    FCFF_REVENUE_DRIVEN = "FCFF Revenue-Driven (High Growth / Tech)"

    # Approche Actionnaire (Equity Value) - NOUVEAUTÉ SPRINT 3
    FCFE_TWO_STAGE = "FCFE Two-Stage (Direct Equity)"
    DDM_GORDON_GROWTH = "Dividend Discount Model (Gordon / DDM)"

    # Autres Modèles
    RESIDUAL_INCOME_MODEL = "Residual Income Model (Penman)"
    GRAHAM_1974_REVISED = "Graham Intrinsic Value (1974 Revised)"

    @property
    def supports_monte_carlo(self) -> bool:
        return self != ValuationMode.GRAHAM_1974_REVISED

    @property
    def is_direct_equity(self) -> bool:
        """Détermine si le modèle calcule directement la valeur actionnariale."""
        return self in [
            ValuationMode.FCFE_TWO_STAGE,
            ValuationMode.DDM_GORDON_GROWTH,
            ValuationMode.RESIDUAL_INCOME_MODEL,
            ValuationMode.GRAHAM_1974_REVISED
        ]


class InputSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"


class TerminalValueMethod(str, Enum):
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"


class AuditSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


# ==============================================================================
# 2. GLASS BOX — STANDARDS DE TRACABILITÉ
# ==============================================================================

class TraceHypothesis(BaseModel):
    name: str
    value: Any
    unit: str = ""
    source: str = "auto"
    comment: Optional[str] = None


class CalculationStep(BaseModel):
    step_id: int = 0
    step_key: str = ""
    label: str = ""
    theoretical_formula: str = ""
    hypotheses: List[TraceHypothesis] = Field(default_factory=list)
    numerical_substitution: str = ""
    result: float = 0.0
    unit: str = ""
    interpretation: str = ""


class AuditStep(BaseModel):
    step_id: int = 0
    step_key: str = ""
    label: str = ""
    rule_formula: str = ""
    indicator_value: Union[float, str] = 0.0
    threshold_value: Union[float, str, None] = None
    severity: AuditSeverity = AuditSeverity.INFO
    verdict: bool = True
    evidence: str = ""
    description: str = ""

class ScenarioVariant(BaseModel):
    """Représente une variante spécifique (Bull, Base ou Bear)."""
    label: str
    growth_rate: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    probability: float = 0.333

class ScenarioResult(BaseModel):
    """Stocke le résultat individuel d'un scénario calculé."""
    label: str
    intrinsic_value: float
    probability: float
    growth_used: float
    margin_used: float

class ScenarioSynthesis(BaseModel):
    """Conteneur final pour la restitution UI des scénarios."""
    variants: List[ScenarioResult] = Field(default_factory=list)
    expected_value: float = 0.0 # Moyenne pondérée (Sum of IV * Prob)
    max_upside: float = 0.0
    max_downside: float = 0.0

class ScenarioParameters(BaseModel):
    """Segment de pilotage des scénarios déterministes."""
    enabled: bool = False
    bull: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bull", probability=0.25))
    base: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Base", probability=0.50))
    bear: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bear", probability=0.25))

    @model_validator(mode='after')
    def validate_probabilities(self) -> 'ScenarioParameters':
        """Standard Pydantic : Assure que la somme des probabilités est cohérente (100%)."""
        if self.enabled:
            total = self.bull.probability + self.base.probability + self.bear.probability
            if not (0.98 <= total <= 1.02): # Marge de tolérance pour les flottants
                raise ValueError("La somme des probabilités (Bull+Base+Bear) doit être égale à 1.0 (100%).")
        return self

# ==============================================================================
# 3. DONNÉES FINANCIÈRES (Yahoo Source)
# ==============================================================================

class CompanyFinancials(BaseModel):
    """Contrat de données financier unifié."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ticker: str
    name: str = "Unknown"
    currency: str
    sector: str = "Unknown"
    industry: str = "Unknown"
    country: str = "Unknown"
    current_price: float
    shares_outstanding: float
    beta: float = 1.0

    total_debt: float = 0.0
    cash_and_equivalents: float = 0.0
    minority_interests: float = 0.0
    pension_provisions: float = 0.0
    book_value: float = 0.0
    book_value_per_share: Optional[float] = None

    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    interest_expense: float = 0.0
    eps_ttm: Optional[float] = None

    dividend_share: Optional[float] = None
    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None

    net_borrowing_ttm: Optional[float] = None

    capex: Optional[float] = None
    depreciation_and_amortization: Optional[float] = None

    @property
    def market_cap(self) -> float:
        return self.current_price * self.shares_outstanding

    @property
    def net_debt(self) -> float:
        return self.total_debt - self.cash_and_equivalents

    @property
    def dividends_total_calculated(self) -> float:
        """Calcul sécurisé du montant total des dividendes versés."""
        return (self.dividend_share or 0.0) * self.shares_outstanding


# ==============================================================================
# 4. PARAMÈTRES DU MODÈLE (Segmentation)
# ==============================================================================

class CoreRateParameters(BaseModel):
    risk_free_rate: Optional[float] = None
    risk_free_source: str = "N/A"
    market_risk_premium: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None
    cost_of_debt: Optional[float] = None
    tax_rate: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None
    manual_beta: Optional[float] = None

    @field_validator('risk_free_rate', 'market_risk_premium', 'corporate_aaa_yield',
                     'cost_of_debt', 'tax_rate', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class GrowthParameters(BaseModel):
    fcf_growth_rate: Optional[float] = None
    projection_years: int = 5
    high_growth_years: int = 0
    terminal_method: TerminalValueMethod = TerminalValueMethod.GORDON_GROWTH
    perpetual_growth_rate: Optional[float] = None
    exit_multiple_value: Optional[float] = None
    target_equity_weight: Optional[float] = None
    target_debt_weight: Optional[float] = None
    target_fcf_margin: Optional[float] = None

    # Surcharges Analyste
    manual_fcf_base: Optional[float] = None
    manual_stock_price: Optional[float] = None
    manual_total_debt: Optional[float] = None
    manual_cash: Optional[float] = None
    manual_minority_interests: Optional[float] = None
    manual_pension_provisions: Optional[float] = None
    manual_shares_outstanding: Optional[float] = None
    manual_book_value: Optional[float] = None
    manual_net_borrowing: Optional[float] = None
    manual_dividend_base: Optional[float] = None

    @field_validator('fcf_growth_rate', 'perpetual_growth_rate', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class MonteCarloConfig(BaseModel):
    enable_monte_carlo: bool = False
    num_simulations: int = 2000
    base_flow_volatility: Optional[float] = None
    beta_volatility: Optional[float] = None
    growth_volatility: Optional[float] = None
    terminal_growth_volatility: Optional[float] = None
    correlation_beta_growth: float = -0.30

    @field_validator('beta_volatility', 'growth_volatility', 'terminal_growth_volatility', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)

class DCFParameters(BaseModel):
    rates: CoreRateParameters = Field(default_factory=CoreRateParameters)
    growth: GrowthParameters = Field(default_factory=GrowthParameters)
    monte_carlo: MonteCarloConfig = Field(default_factory=MonteCarloConfig)
    scenarios: ScenarioParameters = Field(default_factory=ScenarioParameters)

    def normalize_weights(self) -> None:
        w_e = self.growth.target_equity_weight or 0.0
        w_d = self.growth.target_debt_weight or 0.0
        total = w_e + w_d
        if total > 0:
            self.growth.target_equity_weight = w_e / total
            self.growth.target_debt_weight = w_d / total
        else:
            self.growth.target_equity_weight = 1.0
            self.growth.target_debt_weight = 0.0

    @classmethod
    def from_legacy(cls, data: Dict[str, Any]) -> DCFParameters:
        return cls(
            rates=CoreRateParameters(**data),
            growth=GrowthParameters(**data),
            monte_carlo=MonteCarloConfig(**data)
        )


def _decimal_guard(v: Any) -> Optional[float]:
    if v is None or v == "": return None
    try:
        val = float(v)
        return val / 100.0 if 1.0 < val <= 100.0 else val
    except (ValueError, TypeError):
        return None


# ==============================================================================
# 5. AUDIT & CONTRATS
# ==============================================================================

class AuditPillar(str, Enum):
    DATA_CONFIDENCE = "Data Confidence"
    ASSUMPTION_RISK = "Assumption Risk"
    MODEL_RISK = "Model Risk"
    METHOD_FIT = "Method Fit"


class AuditPillarScore(BaseModel):
    pillar: AuditPillar
    score: float = 0.0
    weight: float = 0.0
    contribution: float = 0.0
    diagnostics: List[str] = Field(default_factory=list)
    check_count: int = 0


class AuditScoreBreakdown(BaseModel):
    pillars: Dict[AuditPillar, AuditPillarScore]
    aggregation_formula: str
    total_score: float = 0.0


class AuditLog(BaseModel):
    category: str
    severity: str
    message: str
    penalty: float


class AuditReport(BaseModel):
    global_score: float
    rating: str
    audit_mode: Union[InputSource, str]
    audit_depth: int = 0
    audit_coverage: float = 0.0
    audit_steps: List[AuditStep] = Field(default_factory=list)
    pillar_breakdown: Optional[AuditScoreBreakdown] = None
    logs: List[AuditLog] = Field(default_factory=list)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    block_monte_carlo: bool = False
    critical_warning: bool = False


class ValuationOutputContract(BaseModel):
    model_config = ConfigDict(frozen=True)
    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_intrinsic_value: bool
    has_audit: bool

    def is_valid(self) -> bool:
        return all([self.has_params, self.has_intrinsic_value, self.has_audit])


# ==============================================================================
# 6. RÉSULTATS (FINAL)
# ==============================================================================

class ValuationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource
    manual_params: Optional[DCFParameters] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class ValuationResult(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: Optional[ValuationRequest] = None
    financials: CompanyFinancials
    params: DCFParameters
    intrinsic_value_per_share: float
    market_price: float
    upside_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)
    audit_report: Optional[AuditReport] = None
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None
    rho_sensitivity: Dict[str, float] = Field(default_factory=dict)
    stress_test_value: Optional[float] = None
    mc_valid_ratio: Optional[float] = None
    mc_clamping_applied: Optional[bool] = None
    multiples_triangulation: Optional['MultiplesValuationResult'] = None
    relative_valuation: Optional[Dict[str, float]] = None
    scenario_synthesis: Optional[ScenarioSynthesis] = None

    def model_post_init(self, __context: Any) -> None:
        if self.market_price > 0 and self.upside_pct is None:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        raise NotImplementedError


class DCFValuationResult(ValuationResult):
    wacc: float
    projected_fcfs: List[float]
    enterprise_value: float
    equity_value: float
    discounted_terminal_value: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True, has_projection=len(self.projected_fcfs) > 0,
            has_terminal_value=self.discounted_terminal_value is not None,
            has_intrinsic_value=True, has_audit=self.audit_report is not None
        )


class RIMValuationResult(ValuationResult):
    cost_of_equity: float
    total_equity_value: float
    projected_residual_incomes: List[float]

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True, has_projection=len(self.projected_residual_incomes) > 0,
            has_terminal_value=True, has_intrinsic_value=True, has_audit=self.audit_report is not None
        )


class GrahamValuationResult(ValuationResult):
    eps_used: float
    growth_rate_used: float

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True, has_projection=False,
            has_terminal_value=True, has_intrinsic_value=True, has_audit=self.audit_report is not None
        )

class EquityDCFValuationResult(ValuationResult):
    cost_of_equity: float
    projected_equity_flows: List[float]
    equity_value: float
    discounted_terminal_value: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_equity_flows) > 0,
            has_terminal_value=self.discounted_terminal_value is not None,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )

class PeerMetric(BaseModel):
    """Métriques brutes d'un concurrent."""
    ticker: str
    name: Optional[str] = "Unknown"
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    market_cap: Optional[float] = None

class MultiplesData(BaseModel):
    """Synthèse sectorielle pour la triangulation."""
    peers: List[PeerMetric] = Field(default_factory=list)
    median_pe: float = 0.0
    median_ev_ebitda: float = 0.0
    median_ev_rev: float = 0.0
    source: str = "Yahoo Finance"

class MultiplesValuationResult(ValuationResult):
    """Résultat spécifique à la valorisation par multiples (Relative Valuation)."""
    pe_based_price: float = 0.0
    ebitda_based_price: float = 0.0
    rev_based_price: float = 0.0
    multiples_data: MultiplesData # Données de la Phase 3

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True, has_projection=False,
            has_terminal_value=False, has_intrinsic_value=True, has_audit=True
        )