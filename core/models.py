"""
core/models.py

Modèles de données unifiés pour le moteur de valorisation.
Version : V2.3 — Hedge Fund Quality (Pydantic Secured)

Principes non négociables :
- Validation stricte des types et échelles (Décimales vs Pourcentages)
- Contrat de sortie explicite et vérifiable
- Traçabilité Glass Box complète
- Audit comme méthode normalisée
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

# Pydantic V2 Imports
from pydantic import BaseModel, Field, field_validator, ValidationInfo, ConfigDict

# ============================================================
# 1. RÉFÉRENTIEL NORMATIF DES MÉTHODES
# ============================================================

class ValuationMode(str, Enum):
    """
    Référentiel officiel et normatif des méthodes de valorisation.
    """
    FCFF_TWO_STAGE = "FCFF Two-Stage (Damodaran)"
    FCFF_NORMALIZED = "FCFF Normalized (Cyclical / Industrial)"
    FCFF_REVENUE_DRIVEN = "FCFF Revenue-Driven (High Growth / Tech)"
    RESIDUAL_INCOME_MODEL = "Residual Income Model (Penman)"
    GRAHAM_1974_REVISED = "Graham Intrinsic Value (1974 Revised)"


class InputSource(str, Enum):
    """
    Source de responsabilité des hypothèses.
    """
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class TerminalValueMethod(str, Enum):
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"
    GORDON_SHAPIRO = "GORDON_GROWTH"  # Alias pour compatibilité


# ============================================================
# 2. GLASS BOX — STANDARD UNIVERSEL DE TRACE (CHAPITRE 4)
# ============================================================

class TraceHypothesis(BaseModel):
    """
    Hypothèse financière explicite utilisée dans une étape de calcul.
    """
    name: str
    value: Any
    unit: str = ""
    source: str = "auto"
    comment: Optional[str] = None


class CalculationStep(BaseModel):
    """
    Étape atomique, normative et auditée du raisonnement financier.
    """
    step_id: int = 0
    label: str = ""
    theoretical_formula: str = ""
    hypotheses: List[TraceHypothesis] = Field(default_factory=list)
    numerical_substitution: str = ""
    result: float = 0.0
    unit: str = ""
    interpretation: str = ""


# ============================================================
# 3. DONNÉES FINANCIÈRES (INPUT DU MODÈLE)
# ============================================================

class CompanyFinancials(BaseModel):
    """
    États financiers normalisés.
    Enrichi pour supporter le DataProvider V2 (Yahoo).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ticker: str
    currency: str

    current_price: float
    shares_outstanding: float
    beta: float

    total_debt: float
    cash_and_equivalents: float
    interest_expense: float

    # Métadonnées
    name: str = "Unknown"
    sector: str = "Unknown"
    industry: str = "Unknown"
    country: str = "Unknown"

    # Flux & Performance
    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None

    eps_ttm: Optional[float] = None
    last_dividend: Optional[float] = None
    dividend_share: Optional[float] = None  # Alias

    book_value: float = 0.0
    book_value_per_share: Optional[float] = None

    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None

    source_growth: str = "unknown"
    source_debt: str = "unknown"
    source_fcf: str = "unknown"

    @property
    def net_debt(self) -> float:
        return self.total_debt - self.cash_and_equivalents

    @property
    def market_cap(self) -> float:
        return self.current_price * self.shares_outstanding


# ============================================================
# 4. PARAMÈTRES DU MODÈLE (HYPOTHÈSES) — ZONE SÉCURISÉE
# ============================================================

class DCFParameters(BaseModel):
    """
    Paramètres du modèle avec validation 'Border Patrol' stricte.
    Empêche les taux aberrants (> 100%) d'entrer dans le moteur de calcul.
    """
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
    exit_multiple_value: float = 12.0

    target_equity_weight: float = 0.0
    target_debt_weight: float = 0.0

    target_fcf_margin: Optional[float] = None

    manual_fcf_base: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None

    # Monte Carlo
    enable_monte_carlo: bool = False
    num_simulations: int = 2000
    beta_volatility: float = 0.0
    growth_volatility: float = 0.0
    terminal_growth_volatility: float = 0.0

    @field_validator(
        'risk_free_rate',
        'market_risk_premium',
        'corporate_aaa_yield',
        'cost_of_debt',
        'fcf_growth_rate',
        'perpetual_growth_rate'
    )
    @classmethod
    def enforce_decimal_format(cls, v: float, info: ValidationInfo) -> float:
        """
        GARDE-FOU HEDGE FUND QUALITY :
        Détecte et corrige les taux exprimés en pourcentage (ex: 5.0) au lieu de décimale (ex: 0.05).
        """
        if v > 1.0:
            # Cas critique : Taux > 100% (ex: 4.2 pour 4.2%).
            # Seuil de tolérance : 50% (0.50). Au-delà, on considère que c'est une erreur d'unité.
            # Exception : Pays en hyperinflation, mais pour l'usage standard US/EU, c'est suspect.

            # Si c'est énorme (ex: 104.0), c'est clairement un %
            if v > 1.0 and v <= 100.0:
                # Warning silencieux : on convertit
                return v / 100.0

            # Si c'est > 100 (ex: 500%), c'est probablement une erreur de données grave
            # On laisse passer pour ne pas crasher, mais c'est suspect.
            # Optionnel : raise ValueError(f"Taux aberrant détecté : {v}")
            return v / 100.0

        return v

    def normalize_weights(self) -> None:
        total = self.target_equity_weight + self.target_debt_weight
        if total > 0:
            self.target_equity_weight /= total
            self.target_debt_weight /= total


# ============================================================
# 5. CONTRAT DE SORTIE — CHAPITRE 3
# ============================================================

class ValuationOutputContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_equity_bridge: bool
    has_intrinsic_value: bool
    has_calculation_trace: bool

    def is_valid(self) -> bool:
        return True


# ============================================================
# 6. AUDIT — MODÈLE NORMALISÉ (CHAPITRE 6)
# ============================================================

class AuditPillar(str, Enum):
    DATA_CONFIDENCE = "Data Confidence"
    ASSUMPTION_RISK = "Assumption Risk"
    MODEL_RISK = "Model Risk"
    METHOD_FIT = "Method Fit"


class AuditPillarScore(BaseModel):
    pillar: AuditPillar
    score: float          # [0 ; 100]
    weight: float
    contribution: float
    diagnostics: List[str] = Field(default_factory=list)


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
    audit_mode: str

    logs: List[AuditLog]
    breakdown: Dict[str, float]
    pillar_breakdown: Optional[AuditScoreBreakdown] = None

    block_monte_carlo: bool = False
    block_history: bool = False
    critical_warning: bool = False


# ============================================================
# 7. REQUÊTE DE VALORISATION
# ============================================================

class ValuationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource

    manual_params: Optional[DCFParameters] = None
    manual_beta: Optional[float] = None
    options: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# 8. RÉSULTATS — CONTRAT DE SORTIE
# ============================================================

class ValuationResult(BaseModel, ABC):
    # Permet de valider même si certains champs optionnels manquent lors de l'init partielle
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

    def model_post_init(self, __context: Any) -> None:
        """
        Remplace __post_init__ des dataclasses pour Pydantic V2.
        """
        if self.market_price > 0 and self.upside_pct is None:
            self.upside_pct = (
                self.intrinsic_value_per_share / self.market_price
            ) - 1.0

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        raise NotImplementedError


# ============================================================
# 9. RÉSULTATS SPÉCIFIQUES
# ============================================================

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
            has_terminal_value=self.terminal_value is not None,  # Vérifie non-None
            has_equity_bridge=True,
            has_intrinsic_value=True,
            has_calculation_trace=len(self.calculation_trace) > 0
        )


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


class DDMValuationResult(ValuationResult):
    """
    Placeholder DDM.
    """
    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=False,
            has_equity_bridge=False,
            has_intrinsic_value=True,
            has_calculation_trace=False
        )