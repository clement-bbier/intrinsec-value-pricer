"""
src/domain/models/request_response.py

Requêtes et résultats de valorisation.

Version : V2.0 — ST-1.2 Type-Safe Resolution
Pattern : Pydantic Model (Request/Response Objects)
Style : Numpy Style docstrings

RISQUES FINANCIERS:
- ValuationResult est le contrat de sortie principal
- Toute modification impacte l'ensemble de la chaîne de valeur

DEPENDANCES CRITIQUES:
- pydantic >= 2.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional  # Any requis pour Pydantic model_post_init

from pydantic import BaseModel, ConfigDict, Field

from .enums import ValuationMode, InputSource
from .company import CompanyFinancials
from .dcf_inputs import DCFParameters
from .glass_box import CalculationStep
from .audit import AuditReport, ValuationOutputContract
from .scenarios import ScenarioSynthesis, SOTPParameters
from src.config.constants import ModelDefaults


class ValuationRequest(BaseModel):
    """Requete de valorisation."""
    model_config = ConfigDict(frozen=True)

    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource
    manual_params: Optional[DCFParameters] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class HistoricalPoint(BaseModel):
    """Resultat de valorisation a un instant T passe (Backtest)."""
    valuation_date: date
    intrinsic_value: float
    market_price: float
    error_pct: float
    was_undervalued: bool


class BacktestResult(BaseModel):
    """Synthese complete d'un backtesting."""
    model_config = ConfigDict(protected_namespaces=())

    points: List[HistoricalPoint] = Field(default_factory=list)
    mean_absolute_error: float = 0.0
    alpha_vs_market: float = 0.0
    model_accuracy_score: float = 0.0


class ValuationResult(BaseModel, ABC):
    """Resultat de valorisation (classe abstraite)."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    request: Optional[ValuationRequest] = None
    financials: CompanyFinancials
    params: DCFParameters
    intrinsic_value_per_share: float
    market_price: float
    upside_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)
    audit_report: Optional[AuditReport] = None
    
    # Monte Carlo
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None
    rho_sensitivity: Dict[str, float] = Field(default_factory=dict)
    stress_test_value: Optional[float] = None
    mc_valid_ratio: Optional[float] = None
    mc_clamping_applied: Optional[bool] = None

    # Extensions
    multiples_triangulation: Optional['MultiplesValuationResult'] = None
    relative_valuation: Optional[Dict[str, float]] = None
    scenario_synthesis: Optional[ScenarioSynthesis] = None
    sotp_results: Optional[SOTPParameters] = None
    backtest_report: Optional[BacktestResult] = None

    def model_post_init(self, __context: Any) -> None:
        if self.market_price > 0 and self.upside_pct is None:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0

    @property
    def ticker(self) -> str:
        """Retourne le ticker du résultat ou 'UNKNOWN' si non disponible."""
        return self.request.ticker if self.request else "UNKNOWN"

    @property
    def mode(self) -> Optional[ValuationMode]:
        """Retourne le mode de valorisation ou None si non disponible."""
        return self.request.mode if self.request else None

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        raise NotImplementedError


class DCFValuationResult(ValuationResult):
    """Resultat DCF (FCFF)."""
    wacc: float
    projected_fcfs: List[float]
    enterprise_value: float
    equity_value: float
    discounted_terminal_value: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_fcfs) > 0,
            has_terminal_value=self.discounted_terminal_value is not None,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class RIMValuationResult(ValuationResult):
    """Resultat Residual Income Model."""
    cost_of_equity: float
    total_equity_value: float
    projected_residual_incomes: List[float]

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_residual_incomes) > 0,
            has_terminal_value=True,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class GrahamValuationResult(ValuationResult):
    """Resultat Graham Number."""
    eps_used: float
    growth_rate_used: float

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=True,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class EquityDCFValuationResult(ValuationResult):
    """Resultat FCFE / DDM."""
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
    """Metriques brutes d'un concurrent."""
    ticker: str
    name: Optional[str] = "Unknown"
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    market_cap: Optional[float] = None


class MultiplesData(BaseModel):
    """Synthese sectorielle pour la triangulation."""
    peers: List[PeerMetric] = Field(default_factory=list)
    median_pe: float = ModelDefaults.DEFAULT_MEDIAN_PE
    median_ev_ebitda: float = ModelDefaults.DEFAULT_MEDIAN_EV_EBITDA
    median_ev_ebit: float = ModelDefaults.DEFAULT_MEDIAN_EV_EBIT
    median_pb: float = ModelDefaults.DEFAULT_MEDIAN_PB
    median_ev_rev: float = ModelDefaults.DEFAULT_MEDIAN_EV_REV
    implied_value_ev_ebitda: float = ModelDefaults.DEFAULT_IMPLIED_VALUE_EV_EBITDA
    implied_value_pe: float = ModelDefaults.DEFAULT_IMPLIED_VALUE_PE
    source: str = "Yahoo Finance"

    @property
    def peer_count(self) -> int:
        """Nombre de sociétés comparables dans le panel."""
        return len(self.peers)


class MultiplesValuationResult(ValuationResult):
    """Resultat de valorisation par multiples."""
    pe_based_price: float = ModelDefaults.DEFAULT_PE_BASED_PRICE
    ebitda_based_price: float = ModelDefaults.DEFAULT_EBITDA_BASED_PRICE
    rev_based_price: float = ModelDefaults.DEFAULT_REV_BASED_PRICE
    multiples_data: MultiplesData

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=False,
            has_intrinsic_value=True,
            has_audit=True
        )
