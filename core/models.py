"""
core/models.py

Modèles de données unifiés pour le moteur de valorisation.
Version : V1 Normative (CFA / Damodaran / Buy-Side)

Règle fondamentale :
- ValuationMode = référentiel académique unique
- Aucune méthode non référencée académiquement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC


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
    Une étape atomique du raisonnement financier.
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

    Ces données sont :
    - soit fournies automatiquement (Provider)
    - soit corrigées / enrichies manuellement
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
        """Normalise les poids de structure financière si nécessaire."""
        total = self.target_equity_weight + self.target_debt_weight
        if total > 0.0:
            self.target_equity_weight /= total
            self.target_debt_weight /= total


# ============================================================
# 5. AUDIT & CONTRÔLE QUALITÉ
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
# 6. REQUÊTE DE VALORISATION
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
# 7. RÉSULTATS (OUTPUT DU MODÈLE)
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
