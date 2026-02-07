"""
src/models/results/options.py

ANALYTICAL EXTENSIONS OUTPUTS (MASTER ARCHITECTURE)
===================================================
Role: Stores computed data for Risk Engineering (Pillar 4) and Market Analysis (Pillar 5).
Scope:
  - Pillar 4: Monte Carlo, Sensitivity, Scenarios, Backtest.
  - Pillar 5: Peers, SOTP.
Architecture: Pydantic V2. Strictly complementary to ExtensionBundleParameters.
Style: Numpy docstrings.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.models.glass_box import CalculationStep


# ==============================================================================
# PILLAR 4: RISK ENGINEERING (Simulation, Sensitivity, Scenarios & Backtest)
# ==============================================================================

class MCResults(BaseModel):
    """
    Statistical outputs of the Monte Carlo simulation.

    Attributes
    ----------
    simulation_values : List[float]
        Raw intrinsic values from all iterations (histogram data).
    quantiles : Dict[str, float]
        Key probability points (P10, P50, P90) for risk assessment.
    mean : float
        Arithmetic average of all simulations.
    std_dev : float
        Standard deviation of the distribution (Volatility).
    """
    simulation_values: List[float] = Field(..., description="Raw intrinsic values from all iterations.")
    quantiles: Dict[str, float] = Field(..., description="Key probability points (P10, P50, P90).")
    mean: float = Field(..., description="Arithmetic average of all simulations.")
    std_dev: float = Field(..., description="Standard deviation of the distribution.")


class SensitivityResults(BaseModel):
    """
    Output of the Sensitivity Analysis (2D Matrix).

    Attributes
    ----------
    x_axis_name : str
        Name of the parameter on X axis (e.g., 'WACC').
    y_axis_name : str
        Name of the parameter on Y axis (e.g., 'Growth').
    x_values : List[float]
        The variation steps for X axis.
    y_values : List[float]
        The variation steps for Y axis.
    values : List[List[float]]
        2D Array of intrinsic values matching the X/Y grid.
    center_value : float
        The base case value at the center of the matrix.
    sensitivity_score : float
        A metric of volatility (Spread / Base).
    """
    x_axis_name: str = Field(..., description="Name of the parameter on X axis (e.g. 'WACC').")
    y_axis_name: str = Field(..., description="Name of the parameter on Y axis (e.g. 'Growth').")
    x_values: List[float] = Field(..., description="The variation steps for X axis.")
    y_values: List[float] = Field(..., description="The variation steps for Y axis.")
    values: List[List[float]] = Field(..., description="2D Array of intrinsic values.")
    center_value: float = Field(..., description="The value at the center (Base Case).")
    sensitivity_score: float = Field(0.0, description="Metric of volatility (Spread / Base).")


class ScenarioOutcome(BaseModel):
    """
    Individual result of a specific deterministic case (Bull, Base, Bear).

    Attributes
    ----------
    label : str
        Name of the scenario.
    intrinsic_value : float
        Resulting value per share.
    upside_pct : float
        Upside vs current market price.
    probability : float
        Weight assigned to this scenario (0-1).
    """
    label: str
    intrinsic_value: float
    upside_pct: float
    probability: float


class ScenariosResults(BaseModel):
    """
    Synthesis of the multi-scenario weighted analysis.

    Attributes
    ----------
    expected_intrinsic_value : float
        Weighted average Intrinsic Value across all cases.
    outcomes : List[ScenarioOutcome]
        Detailed results for each scenario.
    """
    expected_intrinsic_value: float = Field(..., description="Weighted average IV across all cases.")
    outcomes: List[ScenarioOutcome] = Field(default_factory=list)


class HistoricalPoint(BaseModel):
    """
    Valuation snapshot at a past fiscal point for backtesting.

    Attributes
    ----------
    valuation_date : date
        The date of the historical valuation.
    calculated_iv : float
        The model's estimate at that time.
    market_price : float
        The actual trading price at that time.
    error_pct : float
        The deviation ((IV - Price) / Price).
    """
    valuation_date: date
    calculated_iv: float
    market_price: float
    error_pct: float


class BacktestResults(BaseModel):
    """
    Historical performance and accuracy metrics of the model.

    Attributes
    ----------
    points : List[HistoricalPoint]
        Collection of past valuations vs actuals.
    mean_absolute_error : float
        Average absolute error over the period.
    accuracy_score : float
        A computed score (0-100) reflecting model predictive power.
    """
    points: List[HistoricalPoint] = Field(default_factory=list)
    mean_absolute_error: float = Field(..., description="Average error over the period.")
    accuracy_score: float = Field(..., ge=0, le=100)


# ==============================================================================
# PILLAR 5: MARKET ANALYSIS (Peers & SOTP)
# ==============================================================================

class PeerIntrinsicDetail(BaseModel):
    """
    Intrinsic summary of a peer after running the engine.

    Attributes
    ----------
    ticker : str
        Peer symbol.
    intrinsic_value : float
        IV calculated for the peer using the same strategy.
    upside_pct : float
        Upside/Downside of the peer vs its own market price.
    """
    ticker: str
    intrinsic_value: float = Field(..., description="IV calculated for the peer using the same strategy.")
    upside_pct: float = Field(..., description="Upside/Downside of the peer vs its own market price.")


class PeersResults(BaseModel):
    """
    Output of the relative valuation triangulation and batch intrinsic analysis.

    Attributes
    ----------
    median_multiples_used : Dict[str, float]
        Medians (P/E, EV/EBITDA) extracted from the peer group.
    implied_prices : Dict[str, float]
        Calculated prices for the target based on peer multiples.
    peer_valuations : List[PeerIntrinsicDetail]
        Full intrinsic results for each peer defined in Parameters.
    final_relative_iv : float
        Synthesized Intrinsic Value from peer triangulation.
    """
    median_multiples_used: Dict[str, float] = Field(..., description="Medians (P/E, EV/EBITDA, etc.) extracted from the peer group.")
    implied_prices: Dict[str, float] = Field(..., description="Calculated prices for our target based on peer multiples.")
    peer_valuations: List[PeerIntrinsicDetail] = Field(default_factory=list, description="Full intrinsic results for each peer defined in Parameters.")
    final_relative_iv: float = Field(..., description="Synthesized Intrinsic Value from peer triangulation.")


class SOTPResults(BaseModel):
    """
    Calculated breakdown of a Sum-of-the-Parts valuation.

    Attributes
    ----------
    total_enterprise_value : float
        Sum of all operating segment values.
    segment_values : Dict[str, float]
        Final value attributed to each segment name.
    implied_equity_value : float
        Final Equity Value after Bridge (EV - Net Debt).
    equity_value_per_share : float
        Implied share price.
    sotp_trace : List[CalculationStep]
        Glass Box steps for the SOTP aggregation.
    """
    total_enterprise_value: float = Field(..., description="Sum of all operating segment values.")
    segment_values: Dict[str, float] = Field(..., description="Final value attributed to each segment name.")
    implied_equity_value: float = Field(..., description="Final Equity Value after Bridge.")
    equity_value_per_share: float = Field(..., description="Implied share price.")
    sotp_trace: List[CalculationStep] = Field(default_factory=list, description="Glass Box steps.")


# ==============================================================================
# THE BUNDLE (Unified Container)
# ==============================================================================

class ExtensionBundleResults(BaseModel):
    """
    Unified container for all optional analytical outputs.
    Attributes remain None if the corresponding extension was not executed.
    """
    # Pillar 4: Risk Engineering
    monte_carlo: Optional[MCResults] = None
    sensitivity: Optional[SensitivityResults] = None
    scenarios: Optional[ScenariosResults] = None
    backtest: Optional[BacktestResults] = None

    # Pillar 5: Market Analysis
    peers: Optional[PeersResults] = None
    sotp: Optional[SOTPResults] = None