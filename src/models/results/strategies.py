"""
src/models/results/strategies.py

STRATEGY-SPECIFIC CALCULATION OUTPUTS
=====================================
Role: Stores the specific projections and intermediate outputs of each model.
Scope: Projections (Arrays), Terminal Values, and Audit Ratios.
Architecture: Pydantic V2. Strictly complementary to Parameters.
"""

from __future__ import annotations
from typing import List, Union
from pydantic import BaseModel, Field
from src.models.glass_box import CalculationStep

# --- Reusable DCF Components ---

class BaseFlowResults(BaseModel):
    """Base components for any flow-based projection (DCF family)."""
    projected_flows: List[float] = Field(..., description="The sequence of projected flows (FCF, Dividends, etc.).")
    discount_factors: List[float] = Field(..., description="The discount factors (1/(1+r)^n) used for NPV.")
    terminal_value: float = Field(..., description="The calculated exit value (Gordon or Multiple).")
    discounted_terminal_value: float = Field(..., description="PV of the Terminal Value.")
    tv_weight_pct: float = Field(..., description="Contribution of TV to total value (Audit Risk).")
    strategy_trace: List[CalculationStep] = Field(default_factory=list)

# --- Concrete Strategy Results ---

class FCFFStandardResults(BaseFlowResults):
    """Outputs for Standard FCFF. Focus on simple FCF projection."""
    pass

class FCFFNormalizedResults(BaseFlowResults):
    """Outputs for Normalized FCFF. Focus on cycle-adjusted flows."""
    normalized_fcf_used: float

class FCFFGrowthResults(BaseFlowResults):
    """Outputs for Growth FCFF. Includes revenue and margin projections for charts."""
    projected_revenues: List[float] = Field(..., description="Revenue trajectory used to derive FCF.")
    projected_margins: List[float] = Field(..., description="FCF Margin evolution.")
    target_margin_reached: float

class FCFEResults(BaseFlowResults):
    """Outputs for FCFE (Equity level). Includes net borrowing impact."""
    projected_net_borrowing: List[float]

class DDMResults(BaseFlowResults):
    """Outputs for Dividend Discount Model. Includes payout tracking."""
    projected_dividends: List[float]
    payout_ratio_observed: float

class RIMResults(BaseModel):
    """Outputs for Residual Income Model (NOT a DCF)."""
    current_book_value: float
    projected_book_values: List[float] = Field(..., description="Evolution of Equity Book Value.")
    projected_residual_incomes: List[float] = Field(..., description="Net Income - (Ke * BV).")
    terminal_value_ri: float
    discounted_terminal_value: float
    strategy_trace: List[CalculationStep] = Field(default_factory=list)

class GrahamResults(BaseModel):
    """Outputs for Graham Intrinsic Value screening."""
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