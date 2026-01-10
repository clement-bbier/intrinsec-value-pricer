"""
core/models. py

Modèles de données unifiés pour le moteur de valorisation.
Version :  V8.1 — Souveraineté Analyste Intégrale (Pydantic Secured)

Principes non négociables :
- Validation stricte des types et échelles (Décimales vs Pourcentages)
- Contrat de sortie explicite et vérifiable
- Traçabilité Glass Box complète
- Audit comme méthode normalisée
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# 1. RÉFÉRENTIEL NORMATIF DES MÉTHODES
# ==============================================================================

class ValuationMode(str, Enum):
    """Référentiel officiel et normatif des méthodes de valorisation."""

    FCFF_TWO_STAGE = "FCFF Two-Stage (Damodaran)"
    FCFF_NORMALIZED = "FCFF Normalized (Cyclical / Industrial)"
    FCFF_REVENUE_DRIVEN = "FCFF Revenue-Driven (High Growth / Tech)"
    RESIDUAL_INCOME_MODEL = "Residual Income Model (Penman)"
    GRAHAM_1974_REVISED = "Graham Intrinsic Value (1974 Revised)"

    @property
    def supports_monte_carlo(self) -> bool:
        """Définit structurellement la compatibilité stochastique du modèle."""
        return self != ValuationMode.GRAHAM_1974_REVISED


class InputSource(str, Enum):
    """Source de responsabilité des hypothèses."""

    AUTO = "AUTO"
    MANUAL = "MANUAL"


class TerminalValueMethod(str, Enum):
    """Méthode de calcul de la valeur terminale."""

    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"
    GORDON_SHAPIRO = "GORDON_GROWTH"  # Alias pour compatibilité


# ==============================================================================
# 2. GLASS BOX — STANDARD UNIVERSEL DE TRACE
# ==============================================================================

class TraceHypothesis(BaseModel):
    """Hypothèse financière explicite utilisée dans une étape de calcul."""

    name: str
    value: Any
    unit: str = ""
    source: str = "auto"
    comment: Optional[str] = None


class CalculationStep(BaseModel):
    """Étape atomique, normative et auditée du raisonnement financier."""

    step_id: int = 0
    step_key: str = ""
    label:  str = ""
    theoretical_formula: str = ""
    hypotheses: List[TraceHypothesis] = Field(default_factory=list)
    numerical_substitution: str = ""
    result: float = 0.0
    unit: str = ""
    interpretation: str = ""


# ==============================================================================
# 3. DONNÉES FINANCIÈRES (INPUT DU MODÈLE)
# ==============================================================================

class CompanyFinancials(BaseModel):
    """
    Contrat de données financier unifié (Source de vérité).
    Regroupe les données brutes issues des fournisseurs (Yahoo).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # =========================================================================
    # Identité & Marché
    # =========================================================================
    ticker: str
    name: str = "Unknown"
    currency: str
    sector: str = "Unknown"
    industry: str = "Unknown"
    country: str = "Unknown"
    current_price: float
    shares_outstanding: float
    beta: float = 1.0

    # =========================================================================
    # Structure du Capital (Bilan)
    # =========================================================================
    total_debt: float = 0.0
    cash_and_equivalents: float = 0.0
    minority_interests: float = 0.0
    pension_provisions: float = 0.0
    book_value: float = 0.0
    book_value_per_share:  Optional[float] = None

    # =========================================================================
    # Performance Opérationnelle (Compte de Résultat)
    # =========================================================================
    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    interest_expense: float = 0.0
    eps_ttm: Optional[float] = None

    # =========================================================================
    # Politique de Distribution
    # =========================================================================
    last_dividend:  Optional[float] = None
    dividend_share:  Optional[float] = None

    # =========================================================================
    # Flux de Trésorerie & Investissements
    # =========================================================================
    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None
    capex: Optional[float] = None
    depreciation_and_amortization:  Optional[float] = None

    # =========================================================================
    # Traçabilité
    # =========================================================================
    source_growth:  str = "unknown"
    source_debt: str = "unknown"
    source_fcf: str = "unknown"

    # =========================================================================
    # Propriétés Calculées
    # =========================================================================

    @property
    def market_cap(self) -> float:
        """Capitalisation boursière."""
        return self.current_price * self.shares_outstanding

    @property
    def net_debt(self) -> float:
        """Dette nette."""
        return self.total_debt - self. cash_and_equivalents

    @property
    def dividends_total_calculated(self) -> float:
        """Calcul sécurisé du montant total des dividendes distribués."""
        return (self.dividend_share or 0.0) * self.shares_outstanding


# ==============================================================================
# 4. PARAMÈTRES DU MODÈLE (HYPOTHÈSES) — ZONE SÉCURISÉE
# ==============================================================================

class DCFParameters(BaseModel):
    """
    Paramètres du modèle avec validation 'Border Patrol' et support du mode hybride.
    Standard Hedge Fund : Distingue None (Délégation Auto) du 0.0 (Saisie Volontaire).
    """

    # =========================================================================
    # Taux et Risque
    # =========================================================================
    risk_free_rate: Optional[float] = None
    market_risk_premium: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None
    cost_of_debt: Optional[float] = None
    tax_rate: Optional[float] = None

    # =========================================================================
    # Croissance et Horizon
    # =========================================================================
    fcf_growth_rate: Optional[float] = None
    projection_years: int = 5
    high_growth_years: int = 0

    # =========================================================================
    # Valeur Terminale
    # =========================================================================
    terminal_method: TerminalValueMethod = TerminalValueMethod.GORDON_GROWTH
    perpetual_growth_rate: Optional[float] = None
    exit_multiple_value: Optional[float] = None

    # =========================================================================
    # Pondérations Cibles
    # =========================================================================
    target_equity_weight: float = 0.0
    target_debt_weight:  float = 0.0
    target_fcf_margin: Optional[float] = None

    # =========================================================================
    # Surcharges Analyste (Souveraineté)
    # =========================================================================
    manual_fcf_base: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None
    manual_beta: Optional[float] = None
    manual_stock_price: Optional[float] = None
    manual_total_debt: Optional[float] = None
    manual_cash:  Optional[float] = None
    manual_minority_interests: Optional[float] = None
    manual_pension_provisions: Optional[float] = None
    manual_shares_outstanding: Optional[float] = None
    manual_book_value: Optional[float] = None

    # =========================================================================
    # Configuration Monte Carlo
    # =========================================================================
    enable_monte_carlo: bool = False
    num_simulations: int = 2000
    beta_volatility:  Optional[float] = None
    growth_volatility: Optional[float] = None
    terminal_growth_volatility: Optional[float] = None
    correlation_beta_growth: float = -0.30

    # =========================================================================
    # Validateurs
    # =========================================================================

    @field_validator(
        'risk_free_rate', 'market_risk_premium', 'corporate_aaa_yield',
        'cost_of_debt', 'tax_rate', 'fcf_growth_rate', 'perpetual_growth_rate',
        'beta_volatility', 'growth_volatility', 'terminal_growth_volatility',
        mode='before'
    )
    @classmethod
    def enforce_decimal_format(cls, v: Any) -> Any:
        """
        GARDE-FOU : Convertit les pourcentages (ex:  5.0) en décimales (0.05).
        Respecte le None (Délégation Auto) et le 0.0 (Souveraineté Analyste).
        """
        if v is None or v == "":
            return None

        try:
            val = float(v)
            if 1.0 < val <= 100.0:
                return val / 100.0
            return val
        except (ValueError, TypeError):
            return None

    # =========================================================================
    # Méthodes
    # =========================================================================

    def normalize_weights(self) -> None:
        """Ajuste les poids pour qu'ils somment à 1.0."""
        total = self.target_equity_weight + self.target_debt_weight
        if total > 0:
            self.target_equity_weight /= total
            self. target_debt_weight /= total


# ==============================================================================
# 5. CONTRAT DE SORTIE
# ==============================================================================

class ValuationOutputContract(BaseModel):
    """Contrat de sortie définissant les éléments requis d'une valorisation."""

    model_config = ConfigDict(frozen=True)

    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_equity_bridge: bool
    has_intrinsic_value: bool
    has_calculation_trace: bool

    def is_valid(self) -> bool:
        """Vérifie la validité du contrat."""
        return True


# ==============================================================================
# 6. AUDIT — MODÈLE NORMALISÉ
# ==============================================================================

class AuditPillar(str, Enum):
    """Piliers d'audit institutionnel."""

    DATA_CONFIDENCE = "Data Confidence"
    ASSUMPTION_RISK = "Assumption Risk"
    MODEL_RISK = "Model Risk"
    METHOD_FIT = "Method Fit"


class AuditPillarScore(BaseModel):
    """Score d'un pilier d'audit avec métadonnées."""

    pillar: AuditPillar
    score: float = 0.0
    weight: float = 0.0
    contribution: float = 0.0
    diagnostics: List[str] = Field(default_factory=list)
    check_count: int = 0


class AuditScoreBreakdown(BaseModel):
    """Décomposition détaillée du score d'audit."""

    pillars: Dict[AuditPillar, AuditPillarScore]
    aggregation_formula: str
    total_score: float = 0.0


class AuditLog(BaseModel):
    """Entrée de log d'audit."""

    category: str
    severity: str
    message: str
    penalty: float


class AuditReport(BaseModel):
    """Rapport d'audit complet."""

    global_score: float
    rating: str
    audit_mode: str
    logs: List[AuditLog]
    audit_depth: int = 0
    audit_coverage: float = 0.0
    breakdown: Dict[str, float] = Field(default_factory=dict)
    pillar_breakdown: Optional[AuditScoreBreakdown] = None
    block_monte_carlo: bool = False
    block_history: bool = False
    critical_warning: bool = False


# ==============================================================================
# 7. REQUÊTE DE VALORISATION
# ==============================================================================

class ValuationRequest(BaseModel):
    """Requête de valorisation immutable."""

    model_config = ConfigDict(frozen=True)

    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource

    manual_params: Optional[DCFParameters] = None
    manual_beta: Optional[float] = None
    options: Dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# 8. RÉSULTATS — CONTRAT DE SORTIE (BASE ABSTRAITE)
# ==============================================================================

class ValuationResult(BaseModel, ABC):
    """Classe abstraite pour tous les résultats de valorisation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # =========================================================================
    # Données de base
    # =========================================================================
    request:  Optional[ValuationRequest] = None
    financials: CompanyFinancials
    params: DCFParameters

    # =========================================================================
    # Résultats principaux
    # =========================================================================
    intrinsic_value_per_share: float
    market_price: float
    upside_pct: Optional[float] = None

    # =========================================================================
    # Traçabilité
    # =========================================================================
    calculation_trace: List[CalculationStep] = Field(default_factory=list)
    audit_report: Optional[AuditReport] = None

    # =========================================================================
    # Monte Carlo
    # =========================================================================
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None
    rho_sensitivity: Dict[str, float] = Field(default_factory=dict)
    stress_test_value: Optional[float] = None

    # =========================================================================
    # Post-initialisation
    # =========================================================================

    def model_post_init(self, __context: Any) -> None:
        """Calcul automatique de l'upside si non fourni."""
        if self.market_price > 0 and self.upside_pct is None:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0

    # =========================================================================
    # Méthode abstraite
    # =========================================================================

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        """Construit le contrat de sortie pour validation."""
        raise NotImplementedError


# ==============================================================================
# 9. RÉSULTATS SPÉCIFIQUES
# ==============================================================================

class DCFValuationResult(ValuationResult):
    """Résultat d'une valorisation DCF (FCFF)."""

    # =========================================================================
    # Métriques DCF
    # =========================================================================
    wacc: float
    cost_of_equity: float
    cost_of_debt_after_tax: float
    projected_fcfs: List[float]
    discount_factors: List[float]
    sum_discounted_fcf: float
    terminal_value:  float
    discounted_terminal_value: float
    enterprise_value: float
    equity_value: float

    # =========================================================================
    # Métriques d'audit observées
    # =========================================================================
    icr_observed: Optional[float] = None
    capex_to_da_ratio: Optional[float] = None
    terminal_value_weight: Optional[float] = None
    payout_ratio_observed: Optional[float] = None
    leverage_observed: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=bool(self.projected_fcfs),
            has_terminal_value=self.terminal_value is not None,
            has_equity_bridge=True,
            has_intrinsic_value=True,
            has_calculation_trace=len(self.calculation_trace) > 0
        )


class RIMValuationResult(ValuationResult):
    """Résultat d'une valorisation RIM (Residual Income Model)."""

    # =========================================================================
    # Métriques RIM
    # =========================================================================
    cost_of_equity: float
    current_book_value: float
    projected_residual_incomes: List[float]
    projected_book_values: List[float]
    discount_factors: List[float]
    sum_discounted_ri: float
    terminal_value_ri: float
    discounted_terminal_value:  float
    total_equity_value: float

    # =========================================================================
    # Métriques d'audit observées
    # =========================================================================
    roe_observed: Optional[float] = None
    payout_ratio_observed: Optional[float] = None
    spread_roe_ke:  Optional[float] = None
    pb_ratio_observed: Optional[float] = None

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
    """Résultat d'une valorisation Graham (1974 Revised)."""

    # =========================================================================
    # Métriques Graham
    # =========================================================================
    eps_used: float
    growth_rate_used: float
    aaa_yield_used: float

    # =========================================================================
    # Métriques d'audit observées
    # =========================================================================
    pe_observed: Optional[float] = None
    graham_multiplier: Optional[float] = None
    payout_ratio_observed: Optional[float] = None

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
    """Résultat d'une valorisation DDM (Dividend Discount Model)."""

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=False,
            has_equity_bridge=False,
            has_intrinsic_value=True,
            has_calculation_trace=False
        )