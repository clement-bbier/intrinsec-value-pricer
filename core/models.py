"""
core/models.py

Modèles de données unifiés pour le moteur de valorisation.
Version : V1.1 — Chapitre 3 conforme (Glass Box Valuation Engine)

Principes non négociables :
- Contrat de sortie explicite et vérifiable
- Comparabilité stricte inter-modèles
- Refus des sorties incomplètes
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

    Toute entrée ici doit :
    - être académiquement référencée
    - correspondre à une méthode déterministe
    - être défendable devant un Investment / Risk Committee
    """

    FCFF_TWO_STAGE = "FCFF Two-Stage (Damodaran)"
    FCFF_NORMALIZED = "FCFF Normalized (Cyclical / Industrial)"
    FCFF_REVENUE_DRIVEN = "FCFF Revenue-Driven (High Growth / Tech)"
    RESIDUAL_INCOME_MODEL = "Residual Income Model (Penman)"
    GRAHAM_1974_REVISED = "Graham Intrinsic Value (1974 Revised)"


class InputSource(str, Enum):
    """Origine des hypothèses utilisées par le modèle."""
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class TerminalValueMethod(str, Enum):
    """Méthode de calcul de la valeur terminale."""
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"


# ============================================================
# 2. TRAÇABILITÉ — GLASS BOX
# ============================================================

@dataclass
class CalculationStep:
    """
    Étape atomique du raisonnement financier.
    Sert de preuve mathématique auditable.
    """
    label: str
    formula: str
    values: str
    result: float
    unit: str
    description: str = ""


# ============================================================
# 3. DONNÉES FINANCIÈRES (INPUT DU MODÈLE)
# ============================================================

@dataclass
class CompanyFinancials:
    """
    Snapshot cohérent et figé des données financières d'une entreprise.
    """

    # --- Identité ---
    ticker: str
    currency: str
    sector: str
    industry: str
    country: str

    # --- Marché ---
    current_price: float
    shares_outstanding: float
    beta: float

    # --- Structure financière ---
    total_debt: float
    cash_and_equivalents: float
    interest_expense: float

    # --- Compte de résultat / Cash-flow ---
    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None

    eps_ttm: Optional[float] = None
    last_dividend: Optional[float] = None
    book_value_per_share: Optional[float] = None

    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None

    # --- Métadonnées ---
    source_growth: str = "unknown"
    source_debt: str = "unknown"
    source_fcf: str = "unknown"


# ============================================================
# 4. PARAMÈTRES DU MODÈLE (HYPOTHÈSES)
# ============================================================

@dataclass
class DCFParameters:
    """
    Paramètres financiers unifiés.
    Compatibles avec toutes les méthodes déterministes V1.
    """

    # --- Marché & risque ---
    risk_free_rate: float
    market_risk_premium: float
    corporate_aaa_yield: float

    # --- Dette & fiscalité ---
    cost_of_debt: float
    tax_rate: float

    # --- Croissance & projection ---
    fcf_growth_rate: float
    projection_years: int
    high_growth_years: int = 0

    # --- Valeur terminale ---
    terminal_method: TerminalValueMethod = TerminalValueMethod.GORDON_GROWTH
    perpetual_growth_rate: float = 0.02
    exit_multiple_value: Optional[float] = None

    # --- Structure cible ---
    target_equity_weight: float = 0.0
    target_debt_weight: float = 0.0

    # --- Spécifique Growth ---
    target_fcf_margin: Optional[float] = None

    # --- Overrides experts ---
    manual_fcf_base: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None

    # --- Paramètres probabilistes (EXTENSION, non normative) ---
    beta_volatility: float = 0.0
    growth_volatility: float = 0.0
    terminal_growth_volatility: float = 0.0
    num_simulations: Optional[int] = None

    def normalize_weights(self) -> None:
        total = self.target_equity_weight + self.target_debt_weight
        if total > 0.0:
            self.target_equity_weight /= total
            self.target_debt_weight /= total


# ============================================================
# 5. CONTRAT DE SORTIE — CHAPITRE 3 (NORMATIF)
# ============================================================

@dataclass(frozen=True)
class ValuationOutputContract:
    """
    Contrat minimal obligatoire pour toute valorisation valide.

    Toute stratégie DOIT produire :
    1. Hypothèses explicites
    2. Taux utilisés et justifiés
    3. Projection explicite
    4. Valeur terminale
    5. Bridge EV → Equity → Valeur par action
    6. Trace Glass Box complète
    """

    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_equity_bridge: bool
    has_intrinsic_value: bool
    has_calculation_trace: bool

    def is_valid(self) -> bool:
        return all([
            self.has_params,
            self.has_projection,
            self.has_terminal_value,
            self.has_equity_bridge,
            self.has_intrinsic_value,
            self.has_calculation_trace
        ])


# ============================================================
# 6. AUDIT & CONTRÔLE QUALITÉ
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

    # Garde-fous
    block_monte_carlo: bool = False
    block_history: bool = False
    critical_warning: bool = False


# ============================================================
# 7. REQUÊTE DE VALORISATION
# ============================================================

@dataclass(frozen=True)
class ValuationRequest:
    """
    Requête immuable décrivant :
    - l'actif
    - la méthode
    - l'origine des hypothèses
    """
    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource

    manual_params: Optional[DCFParameters] = None
    manual_beta: Optional[float] = None
    options: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# 8. RÉSULTATS — CONTRAT DE SORTIE APPLICABLE
# ============================================================

@dataclass(kw_only=True)
class ValuationResult(ABC):
    """
    Classe abstraite racine de tous les résultats de valorisation.
    """

    request: Optional[ValuationRequest]
    financials: CompanyFinancials
    params: DCFParameters

    intrinsic_value_per_share: float
    market_price: float

    upside_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = field(default_factory=list)

    audit_report: Optional[AuditReport] = None

    # Extensions (non normatives)
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.market_price > 0:
            self.upside_pct = (
                self.intrinsic_value_per_share / self.market_price
            ) - 1.0

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        """
        Chaque résultat DOIT être capable d'exprimer explicitement
        s'il respecte le contrat de sortie Chapitre 3.
        """
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
            has_params=self.params is not None,
            has_projection=bool(self.projected_fcfs),
            has_terminal_value=self.terminal_value is not None,
            has_equity_bridge=self.enterprise_value is not None and self.equity_value is not None,
            has_intrinsic_value=self.intrinsic_value_per_share is not None,
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
            has_params=self.params is not None,
            has_projection=bool(self.projected_residual_incomes),
            has_terminal_value=self.terminal_value_ri is not None,
            has_equity_bridge=self.total_equity_value is not None,
            has_intrinsic_value=self.intrinsic_value_per_share is not None,
            has_calculation_trace=len(self.calculation_trace) > 0
        )


@dataclass(kw_only=True)
class GrahamValuationResult(ValuationResult):
    eps_used: float
    growth_rate_used: float
    aaa_yield_used: float

    base_pe: float = 8.5
    multiplier_factor: float = 2.0

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=self.params is not None,
            has_projection=False,  # Méthode sans projection explicite
            has_terminal_value=True,  # Heuristique intégrée
            has_equity_bridge=True,
            has_intrinsic_value=self.intrinsic_value_per_share is not None,
            has_calculation_trace=len(self.calculation_trace) > 0
        )
