"""
src/models/params/strategies.py

SPECIFIC VALUATION STRATEGY PARAMETERS (ULTRA-CLINICAL & DRY)
============================================================
Role: Captures User Overrides with factored projection logic.
Architecture: Pydantic V2 inheritance. Factors common projection fields
              while keeping accounting anchors specialized per model.
"""

from __future__ import annotations
from typing import Optional, Literal, Union
from pydantic import BaseModel, Field
from src.models.enums import ValuationMode, TerminalValueMethod

# ==============================================================================
# 1. REUSABLE COMPONENTS
# ==============================================================================

class TerminalValueParameters(BaseModel):
    """Parameters for Step 4: Terminal Value (Exit Logic)."""
    method: Optional[TerminalValueMethod] = None
    perpetual_growth_rate: Optional[float] = None
    exit_multiple: Optional[float] = None

class BaseProjectedParameters(BaseModel):
    """
    Base Mixin for models requiring a discrete projection period.
    Factors common fields for DCF, DDM, and RIM.
    """
    projection_years: Optional[int] = Field(None, ge=1, le=50)
    terminal_value: TerminalValueParameters = Field(default_factory=TerminalValueParameters)

# ==============================================================================
# 2. STRATEGY CLASSES (The Drawers)
# ==============================================================================

class FCFFStandardParameters(BaseProjectedParameters):
    """Standard DCF based on Free Cash Flow to Firm."""
    mode: Literal[ValuationMode.FCFF_STANDARD] = ValuationMode.FCFF_STANDARD

    # --- Accounting Overrides ---
    fcf_anchor: Optional[float] = None
    ebit_ttm: Optional[float] = None
    capex_ttm: Optional[float] = None
    da_ttm: Optional[float] = None

    # --- Specific Lever ---
    growth_rate_p1: Optional[float] = None

class FCFFNormalizedParameters(BaseProjectedParameters):
    """DCF based on normalized cycle flows."""
    mode: Literal[ValuationMode.FCFF_NORMALIZED] = ValuationMode.FCFF_NORMALIZED

    # --- Accounting Overrides ---
    fcf_norm: Optional[float] = None
    ebit_norm: Optional[float] = None

    # --- Specific Lever ---
    cycle_growth_rate: Optional[float] = None

class FCFFGrowthParameters(BaseProjectedParameters):
    """DCF starting from Revenue and Margins."""
    mode: Literal[ValuationMode.FCFF_GROWTH] = ValuationMode.FCFF_GROWTH

    # --- Accounting Overrides ---
    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    capex_ttm: Optional[float] = None

    # --- Specific Lever ---
    revenue_growth_rate: Optional[float] = None

class FCFEParameters(BaseProjectedParameters):
    """Free Cash Flow to Equity (Post-Debt)."""
    mode: Literal[ValuationMode.FCFE] = ValuationMode.FCFE

    # --- Accounting Overrides ---
    fcfe_anchor: Optional[float] = None
    net_income_ttm: Optional[float] = None
    net_borrowing_delta: Optional[float] = None
    capex_ttm: Optional[float] = None

    # --- Specific Lever ---
    growth_rate: Optional[float] = None

class DDMParameters(BaseProjectedParameters):
    """Dividend Discount Model."""
    mode: Literal[ValuationMode.DDM] = ValuationMode.DDM

    # --- Accounting Overrides ---
    dividend_per_share: Optional[float] = None
    net_income_ttm: Optional[float] = None

    # --- Specific Lever ---
    dividend_growth_rate: Optional[float] = None

class RIMParameters(BaseProjectedParameters):
    """Residual Income Model (Ohlson)."""
    mode: Literal[ValuationMode.RIM] = ValuationMode.RIM

    # --- Accounting Overrides ---
    book_value_anchor: Optional[float] = None
    net_income_norm: Optional[float] = None
    total_assets: Optional[float] = None

    # --- Specific Levers ---
    growth_rate: Optional[float] = None
    persistence_factor: Optional[float] = None

class GrahamParameters(BaseModel):
    """
    Graham Intrinsic Value.
    Note: Does NOT inherit from BaseProjectedParameters (Static Formula).
    """
    mode: Literal[ValuationMode.GRAHAM] = ValuationMode.GRAHAM

    # --- Accounting Overrides ---
    eps_normalized: Optional[float] = None
    revenue_ttm: Optional[float] = None

    # --- Method Levers ---
    growth_estimate: Optional[float] = None

# ==============================================================================
# 3. THE ORCHESTRATOR
# ==============================================================================

StrategyUnionParameters = Union[
    FCFFStandardParameters,
    FCFFNormalizedParameters,
    FCFFGrowthParameters,
    FCFEParameters,
    DDMParameters,
    RIMParameters,
    GrahamParameters
]