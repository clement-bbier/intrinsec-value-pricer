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

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .enums import ValuationMode, InputSource
from .company import Company
from .parameters import Parameters, ScenarioSynthesis, SOTPParameters
from .glass_box import CalculationStep
from .audit import AuditReport, ValuationOutputContract
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
        The specific valuation methodology to employ.
    input_source : InputSource
        Origin of the data (AUTO or MANUAL).
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
    manual_params: Optional[Parameters] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class HistoricalPoint(BaseModel):
    """Represents a valuation snapshot at a specific point in time."""
    valuation_date: date
    intrinsic_value: float
    market_price: float
    error_pct: float
    was_undervalued: bool


class BacktestResult(BaseModel):
    """Aggregated synthesis of a historical backtest run."""
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

    Provides a standardized interface for UI components and audit engines.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: Optional[ValuationRequest] = None
    financials: Company
    params: Parameters
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
    multiples_triangulation: Optional[MultiplesValuationResult] = None
    relative_valuation: Optional[Dict[str, float]] = None
    scenario_synthesis: Optional[ScenarioSynthesis] = None
    sotp_results: Optional[SOTPParameters] = None
    backtest_report: Optional[BacktestResult] = None

    def model_post_init(self, __context: Any) -> None:
        """Automatically calculates upside potential if price is available."""
        if self.market_price > 0 and self.upside_pct is None:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0

    # --- UNIVERSAL COMPUTED PROPERTIES (PROV-V2) ---

    @computed_field
    @property
    def ticker_symbol(self) -> str:
        """Safe access to the ticker symbol."""
        return self.request.ticker if self.request else "UNKNOWN"

    @computed_field
    @property
    def discount_rate(self) -> float:
        """Universal discount rate accessor (WACC or Ke)."""
        return getattr(self, 'wacc', 0.0) or getattr(self, 'cost_of_equity', 0.0)

    @computed_field
    @property
    def terminal_growth_rate(self) -> float:
        """Direct access to perpetual growth rate (g)."""
        return self.params.growth.perpetual_growth_rate or 0.0

    @computed_field
    @property
    def market_cap(self) -> float:
        """Current market capitalization."""
        return self.market_price * self.financials.shares_outstanding

    @computed_field
    @property
    def intrinsic_price(self) -> float:
        """Clean alias for IV per share."""
        return self.intrinsic_value_per_share

    @computed_field
    @property
    def upside(self) -> float:
        """Safe access to calculated upside."""
        return self.upside_pct or 0.0

    @computed_field
    @property
    def total_equity(self) -> float:
        """
        Calculates total market value of equity.
        Renamed from 'equity_value' to avoid shadowing warnings with fields.
        """
        for attr in ['equity_value', 'total_equity_value']:
            val = getattr(self, attr, None)
            if val is not None:
                return val
        return self.intrinsic_value_per_share * self.financials.shares_outstanding

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        """Validates that the result satisfies audit requirements."""
        raise NotImplementedError


# ==============================================================================
# 3. CONCRETE VALUATION MODELS
# ==============================================================================

class DCFValuationResult(ValuationResult):
    """Enterprise DCF Result (shadows equity_value via field)."""
    wacc: float
    cost_of_equity: float
    cost_of_debt_after_tax: float
    projected_fcfs: List[float]
    discount_factors: List[float]
    sum_discounted_fcf: float
    terminal_value: float
    discounted_terminal_value: Optional[float] = None
    enterprise_value: float
    equity_value: float

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
    """Residual Income Model Result."""
    cost_of_equity: float
    current_book_value: float
    total_equity_value: float
    projected_residual_incomes: List[float]
    projected_book_values: List[float]
    discount_factors: List[float]
    sum_discounted_ri: float
    terminal_value_ri: float
    discounted_terminal_value: float

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
    """Graham Intrinsic Value Screening Result."""
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
    """Direct Equity DCF Result (FCFE / DDM)."""
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
# 4. RELATIVE VALUATION MODELS (MULTIPLES)
# ==============================================================================

class PeerMetric(BaseModel):
    """Raw financial metrics for a specific competitor."""
    ticker: str
    name: Optional[str] = "Unknown"
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    market_cap: Optional[float] = None


class MultiplesData(BaseModel):
    """Sectoral synthesis used for triangulation."""
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
    """Market Multiples Triangulation Result."""
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

