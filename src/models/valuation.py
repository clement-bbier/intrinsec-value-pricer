"""
src/models/valuation.py

VALUATION REQUESTS AND RESULTS ORCHESTRATOR
===========================================
Role: Data structures for valuation requests and standardized outputs.
Scope: Forms the primary interface contract for all calculation engines.
Architecture: Abstract Base Class (ABC) pattern for result specialization.

Style: Numpy docstrings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import ValuationMode, InputSource
from .company import CompanyFinancials
from .dcf_parameters import DCFParameters
from .glass_box import CalculationStep
from .audit import AuditReport, ValuationOutputContract
from .scenarios import ScenarioSynthesis, SOTPParameters
from src.config.constants import ModelDefaults


# ==============================================================================
# 1. REQUEST & BACKTESTING MODELS
# ==============================================================================

class ValuationRequest(BaseModel):
    """
    Encapsulates a formal request for an intrinsic valuation.

    Attributes
    ----------
    ticker : str
        Stock symbol of the target entity.
    projection_years : int
        Duration of the explicit forecast horizon.
    mode : ValuationMode
        The specific valuation methodology to employ (e.g., FCFF, RIM).
    input_source : InputSource
        Origin of the data (AUTO for providers, MANUAL for experts).
    manual_params : DCFParameters, optional
        Expert-defined parameters for manual overrides.
    options : Dict[str, Any]
        Extensible dictionary for engine-specific flags.
    """
    model_config = ConfigDict(frozen=True)

    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource
    manual_params: Optional[DCFParameters] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class HistoricalPoint(BaseModel):
    """
    Represents a valuation snapshot at a specific point in time (Backtesting).
    """
    valuation_date: date
    intrinsic_value: float
    market_price: float
    error_pct: float
    was_undervalued: bool


class BacktestResult(BaseModel):
    """
    Aggregated synthesis of a historical backtest run.

    Used to evaluate model accuracy and alpha generation over time.
    """
    model_config = ConfigDict(protected_namespaces=())

    points: List[HistoricalPoint] = Field(default_factory=list)
    mean_absolute_error: float = 0.0
    alpha_vs_market: float = 0.0
    model_accuracy_score: float = 0.0


# ==============================================================================
# 2. ABSTRACT BASE RESULT CONTRACT
# ==============================================================================

class ValuationResult(BaseModel, ABC):
    """
    Abstract Base Class for all valuation outputs.

    Defines the shared contract for value representation, audit lineage,
    and sensitivity analysis.

    Attributes
    ----------
    intrinsic_value_per_share : float
        The calculated fair value of a single share.
    market_price : float
        Market price at the time of calculation.
    upside_pct : float, optional
        The delta between market price and intrinsic value:
        $$Upside = \frac{IV_{share}}{Price_{market}} - 1$$
    calculation_trace : List[CalculationStep]
        Full Glass Box traceability for mathematical audit.
    audit_report : AuditReport
        Institutional reliability assessment.
    simulation_results : List[float], optional
        Raw results from Monte Carlo iterations.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: Optional[ValuationRequest] = None
    financials: CompanyFinancials
    params: DCFParameters
    intrinsic_value_per_share: float
    market_price: float
    upside_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)
    audit_report: Optional[AuditReport] = None

    # Probabilistic Data (Monte Carlo)
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None
    rho_sensitivity: Dict[str, float] = Field(default_factory=dict)
    stress_test_value: Optional[float] = None
    mc_valid_ratio: Optional[float] = None
    mc_clamping_applied: Optional[bool] = None

    # Analytical Extensions
    multiples_triangulation: Optional['MultiplesValuationResult'] = None
    relative_valuation: Optional[Dict[str, float]] = None
    scenario_synthesis: Optional[ScenarioSynthesis] = None
    sotp_results: Optional[SOTPParameters] = None
    backtest_report: Optional[BacktestResult] = None

    def model_post_init(self, __context: Any) -> None:
        """Automatically calculates upside potential if price is available."""
        if self.market_price > 0 and self.upside_pct is None:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0

    @property
    def ticker(self) -> str:
        return self.request.ticker if self.request else "UNKNOWN"

    @property
    def mode(self) -> Optional[ValuationMode]:
        return self.request.mode if self.request else None

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        """Ensures that every result implementation satisfies the audit contract."""
        raise NotImplementedError


# ==============================================================================
# 3. CONCRETE VALUATION SPECIALIZATIONS
# ==============================================================================

class DCFValuationResult(ValuationResult):
    """Concrete implementation for Enterprise DCF (FCFF)."""
    # --- Rate Variables ---
    wacc: float
    cost_of_equity: float
    cost_of_debt_after_tax: float

    # --- Cash Flows & Terminal Values ---
    projected_fcfs: List[float]
    discount_factors: List[float]
    sum_discounted_fcf: float
    terminal_value: float
    discounted_terminal_value: Optional[float] = None
    enterprise_value: float
    equity_value: float

    # --- Observed Audit Metrics ---
    icr_observed: Optional[float] = None
    capex_to_da_ratio: Optional[float] = None
    terminal_value_weight: Optional[float] = None
    payout_ratio_observed: Optional[float] = None
    leverage_observed: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_fcfs) > 0,
            has_terminal_value=self.discounted_terminal_value is not None,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class RIMValuationResult(ValuationResult):
    """Concrete implementation for the Residual Income Model (RIM)."""
    cost_of_equity: float
    current_book_value: float
    total_equity_value: float

    # --- Projection Vectors ---
    projected_residual_incomes: List[float]
    projected_book_values: List[float]
    discount_factors: List[float]

    # --- Components ---
    sum_discounted_ri: float
    terminal_value_ri: float
    discounted_terminal_value: float

    # --- Banking-specific Audit Metrics ---
    roe_observed: Optional[float] = None
    payout_ratio_observed: Optional[float] = None
    spread_roe_ke: Optional[float] = None
    pb_ratio_observed: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_residual_incomes) > 0,
            has_terminal_value=True,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class GrahamValuationResult(ValuationResult):
    """Refined result for Graham Intrinsic Value screening."""
    eps_used: float
    growth_rate_used: float
    aaa_yield_used: float
    graham_multiplier: float
    pe_observed: Optional[float] = None
    payout_ratio_observed: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=True,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class EquityDCFValuationResult(ValuationResult):
    """Result for FCFE / Dividend Discount Models (DDM)."""
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


# ==============================================================================
# 4. RELATIVE VALUATION (PEER MULTIPLES)
# ==============================================================================

class PeerMetric(BaseModel):
    """Raw financial metrics for a competitor used in peer triangulation."""
    ticker: str
    name: Optional[str] = "Unknown"
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    market_cap: Optional[float] = None


class MultiplesData(BaseModel):
    """Sectoral synthesis for multiple-based triangulation."""
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
        return len(self.peers)


class MultiplesValuationResult(ValuationResult):
    """Results container for market-based relative valuation."""
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
            has_audit=self.audit_report is not None
        )