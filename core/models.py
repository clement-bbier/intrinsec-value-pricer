import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Dict


# --- ENUMS ---

class ValuationMode(Enum):
    SIMPLE_FCFF = "SIMPLE_FCFF"
    FUNDAMENTAL_FCFF = "FUNDAMENTAL_FCFF"
    MONTE_CARLO = "MONTE_CARLO"


class InputSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class FCFSource(Enum):
    TTM = "TTM"
    WEIGHTED = "WEIGHTED"
    SIMPLE_ANNUAL = "SIMPLE_ANNUAL"
    NONE = "NONE"


class GrowthSource(Enum):
    ANALYSTS = "ANALYSTS"
    CAGR = "CAGR"
    SUSTAINABLE = "SUSTAINABLE"
    MACRO = "MACRO"
    MANUAL = "MANUAL"


class DebtSource(Enum):
    SYNTHETIC = "SYNTHETIC"
    SECTOR = "SECTOR"
    MANUAL = "MANUAL"


# --- DATA STRUCTURES (INPUTS) ---

@dataclass
class DCFParameters:
    """Paramètres d'hypothèses DCF (Input Model)."""
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
    target_equity_weight: float = 0.0
    target_debt_weight: float = 0.0
    manual_fcf_base: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None


@dataclass
class CompanyFinancials:
    """Données Financières de l'Entreprise (Input Provider)."""
    ticker: str
    currency: str
    sector: str
    industry: str
    country: str = "Unknown"  # <-- CHAMP CRITIQUE AJOUTÉ
    current_price: float = 0.0
    shares_outstanding: float = 0.0
    total_debt: float = 0.0
    cash_and_equivalents: float = 0.0
    interest_expense: float = 0.0
    beta: float = 1.0
    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None
    implied_growth_rate: Optional[float] = None
    source_fcf: str = FCFSource.NONE.value
    source_growth: str = GrowthSource.MACRO.value
    source_debt: str = DebtSource.SECTOR.value
    audit_score: float = 0.0
    audit_rating: str = "N/A"
    audit_details: List[Dict[str, Any]] = field(default_factory=list)
    audit_logs: List[str] = field(default_factory=list)
    audit_breakdown: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


# --- DATA STRUCTURES (OUTPUTS) ---

@dataclass
class DCFResult:
    """Résultats du Calcul DCF (Output Engine)."""
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
    implied_growth_rate: Optional[float] = None


# --- CONFIG & VALIDATION ---

@dataclass
class MethodConfigBase(ABC):
    mode: ValuationMode
    params: DCFParameters

    @abstractmethod
    def validate(self, context_beta: float) -> None:
        pass

    def _check_global_constraints(self, beta: float) -> None:
        p = self.params
        if p.projection_years < 1:
            raise ValueError("Horizon de projection invalide (< 1 an).")

        if p.target_equity_weight > 0:
            if not math.isclose(p.target_equity_weight + p.target_debt_weight, 1.0, rel_tol=1e-3):
                raise ValueError("La somme des poids (Dette + Equity) doit être égale à 100%.")

        cost_equity = p.manual_cost_of_equity if p.manual_cost_of_equity else (
                    p.risk_free_rate + beta * p.market_risk_premium)
        wacc_est = (0.8 * cost_equity) + (0.2 * p.cost_of_debt * (1 - p.tax_rate))

        if wacc_est <= p.perpetual_growth_rate:
            raise ValueError(
                f"WACC estimé ({wacc_est:.2%}) <= Croissance Terminale ({p.perpetual_growth_rate:.2%}). Modèle impossible.")


@dataclass
class SimpleDCFConfig(MethodConfigBase):
    def validate(self, context_beta: float) -> None: self._check_global_constraints(context_beta)


@dataclass
class FundamentalDCFConfig(MethodConfigBase):
    def validate(self, context_beta: float) -> None: self._check_global_constraints(context_beta)


@dataclass
class MonteCarloDCFConfig(MethodConfigBase):
    def validate(self, context_beta: float) -> None:
        self._check_global_constraints(context_beta)
        if self.params.growth_volatility > 0.50:
            raise ValueError("Volatilité de croissance excessive (>50%).")


class ConfigFactory:
    @staticmethod
    def get_config(mode: ValuationMode, params: DCFParameters) -> MethodConfigBase:
        if mode == ValuationMode.SIMPLE_FCFF:
            return SimpleDCFConfig(mode, params)
        elif mode == ValuationMode.FUNDAMENTAL_FCFF:
            return FundamentalDCFConfig(mode, params)
        elif mode == ValuationMode.MONTE_CARLO:
            return MonteCarloDCFConfig(mode, params)
        raise ValueError(f"Mode inconnu : {mode}")