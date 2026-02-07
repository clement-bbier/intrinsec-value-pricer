"""
src/models/results/strategies.py

STRATEGY-SPECIFIC CALCULATION OUTPUTS
=====================================
Role: Stores the specific projections and intermediate outputs of each model.
Scope: Projections (Arrays), Terminal Values, and Audit Ratios.
Architecture: Pydantic V2. Strictly complementary to Parameters.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import List, Union
from pydantic import BaseModel, Field
from src.models.glass_box import CalculationStep


# --- Reusable DCF Components ---

class BaseFlowResults(BaseModel):
    """
    Base components for any flow-based projection (DCF family).

    Attributes
    ----------
    projected_flows : List[float]
        The sequence of projected flows (FCF, Dividends, etc.) for the explicit period.
    discount_factors : List[float]
        The discount factors (1/(1+r)^n) applied to each year.
    terminal_value : float
        The calculated exit value (via Gordon Growth or Exit Multiple) at the horizon.
    discounted_terminal_value : float
        The Present Value (PV) of the Terminal Value.
    tv_weight_pct : float
        The percentage of the total value derived from the Terminal Value (Audit Risk).
    strategy_trace : List[CalculationStep]
        Detailed audit trail of the projection steps.
    """
    projected_flows: List[float] = Field(..., description="The sequence of projected flows (FCF, Dividends, etc.).")
    discount_factors: List[float] = Field(..., description="The discount factors (1/(1+r)^n) used for NPV.")
    terminal_value: float = Field(..., description="The calculated exit value (Gordon or Multiple).")
    discounted_terminal_value: float = Field(..., description="PV of the Terminal Value.")
    tv_weight_pct: float = Field(..., description="Contribution of TV to total value (Audit Risk).")
    strategy_trace: List[CalculationStep] = Field(default_factory=list)


# --- Concrete Strategy Results ---

class FCFFStandardResults(BaseFlowResults):
    """
    Outputs for Standard FCFF.
    Inherits all flow fields. Focus on simple FCF projection from EBIT/EBITDA.
    """
    pass


class FCFFNormalizedResults(BaseFlowResults):
    """
    Outputs for Normalized FCFF.

    Attributes
    ----------
    normalized_fcf_used : float
        The mid-cycle Free Cash Flow value used as the anchor.
    """
    normalized_fcf_used: float


class FCFFGrowthResults(BaseFlowResults):
    """
    Outputs for Growth FCFF (Top-Down).

    Attributes
    ----------
    projected_revenues : List[float]
        The revenue trajectory over the projection period.
    projected_margins : List[float]
        The FCF margin evolution (converging to target).
    target_margin_reached : float
        The final margin achieved in the terminal year.
    """
    projected_revenues: List[float] = Field(..., description="Revenue trajectory used to derive FCF.")
    projected_margins: List[float] = Field(..., description="FCF Margin evolution.")
    target_margin_reached: float


class FCFEResults(BaseFlowResults):
    """
    Outputs for FCFE (Equity level).

    Attributes
    ----------
    projected_net_borrowing : List[float]
        The net debt issuance/repayment projected each year.
    """
    projected_net_borrowing: List[float]


class DDMResults(BaseFlowResults):
    """
    Outputs for Dividend Discount Model.

    Attributes
    ----------
    projected_dividends : List[float]
        The stream of expected dividends.
    payout_ratio_observed : float
        The payout ratio used to derive dividends from earnings.
    """
    projected_dividends: List[float]
    payout_ratio_observed: float


class RIMResults(BaseModel):
    """
    Outputs for Residual Income Model (Ohlson).
    Note: This is NOT a flow-based model, so it does not inherit BaseFlowResults.

    Attributes
    ----------
    current_book_value : float
        Starting Equity Book Value.
    projected_book_values : List[float]
        Evolution of Book Value via clean surplus relation.
    projected_residual_incomes : List[float]
        Excess returns: Net Income - (Ke * Prior Book Value).
    terminal_value_ri : float
        The continuing value of residual income.
    discounted_terminal_value : float
        Present value of the terminal component.
    strategy_trace : List[CalculationStep]
        Audit trail specific to RIM.
    """
    current_book_value: float
    projected_book_values: List[float] = Field(..., description="Evolution of Equity Book Value.")
    projected_residual_incomes: List[float] = Field(..., description="Net Income - (Ke * BV).")
    terminal_value_ri: float
    discounted_terminal_value: float
    strategy_trace: List[CalculationStep] = Field(default_factory=list)


class GrahamResults(BaseModel):
    """
    Outputs for Benjamin Graham Intrinsic Value formula.

    Attributes
    ----------
    eps_used : float
        The Normalized EPS used in the formula.
    growth_estimate : float
        The conservative growth rate applied.
    aaa_yield_used : float
        The corporate bond yield benchmark.
    graham_multiplier : float
        The resulting multiplier (e.g., 8.5 + 2g).
    strategy_trace : List[CalculationStep]
        Audit trail of the formula inputs.
    """
    eps_used: float
    growth_estimate: float
    aaa_yield_used: float
    graham_multiplier: float
    strategy_trace: List[CalculationStep] = Field(default_factory=list)


# --- The Orchestrator ---

StrategyUnionResults = Union[
    FCFFStandardResults,
    FCFFNormalizedResults,
    FCFFGrowthResults,
    FCFEResults,
    DDMResults,
    RIMResults,
    GrahamResults
]