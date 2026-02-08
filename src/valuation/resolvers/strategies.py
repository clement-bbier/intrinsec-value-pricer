"""
src/models/parameters/strategies.py

SPECIFIC VALUATION STRATEGY PARAMETERS
======================================
Role: Captures User Overrides with factored projection logic and UI mapping.
Architecture: Inherits from BaseNormalizedModel for automatic scaling.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Optional, Literal, Union, Annotated, List
from pydantic import Field

from src.models.enums import ValuationMethodology, TerminalValueMethod
from src.models.parameters.input_metadata import UIKey
from src.models.parameters.common import BaseNormalizedModel


# ==============================================================================
# 1. REUSABLE COMPONENTS
# ==============================================================================

class TerminalValueParameters(BaseNormalizedModel):
    """
    Parameters for Step 4: Terminal Value (Exit Logic).

    Attributes
    ----------
    method : TerminalValueMethod | None
        The method used to calculate terminal value (Perpetual Growth or Exit Multiple).
    perpetual_growth_rate : float | None
        The stable growth rate (g) assumed in perpetuity (Gordon Growth).
    exit_multiple : float | None
        The EV/EBITDA or PE multiple applied to the final projected year.
    """
    method: Optional[TerminalValueMethod] = None
    perpetual_growth_rate: Annotated[Optional[float], UIKey("gn", scale="pct")] = None
    exit_multiple: Annotated[Optional[float], UIKey("exit_mult", scale="raw")] = None


class BaseProjectedParameters(BaseNormalizedModel):
    """
    Mixin for models requiring a discrete projection period.
    Factors common fields for DCF, DDM, and RIM.

    Attributes
    ----------
    projection_years : int | None
        Number of years in the explicit forecast period (Standard: 5-10).
    terminal_value : TerminalValueParameters
        Configuration for the post-projection value.
    manual_growth_vector : List[float] | None
        Optional year-by-year growth overrides provided by the user.
    """
    projection_years: Annotated[Optional[int], UIKey("years", scale="raw")] = Field(None, ge=1, le=50)
    manual_growth_vector: Annotated[Optional[List[float]], UIKey("growth_vector", scale="pct")] = None
    terminal_value: TerminalValueParameters = Field(default_factory=TerminalValueParameters)


# ==============================================================================
# 2. STRATEGY CLASSES (The Drawers)
# ==============================================================================

class FCFFStandardParameters(BaseProjectedParameters):
    """
    Standard DCF based on Free Cash Flow to Firm (Starting from EBIT/EBITDA).
    """
    mode: Literal[ValuationMethodology.FCFF_STANDARD] = ValuationMethodology.FCFF_STANDARD

    # --- Accounting Overrides ---
    fcf_anchor: Annotated[Optional[float], UIKey("fcf_base", scale="million")] = None
    ebit_ttm: Annotated[Optional[float], UIKey("ebit_ttm", scale="million")] = None
    capex_ttm: Annotated[Optional[float], UIKey("capex_ttm", scale="million")] = None
    da_ttm: Annotated[Optional[float], UIKey("da_ttm", scale="million")] = None

    # --- Specific Lever ---
    growth_rate_p1: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None


class FCFFNormalizedParameters(BaseProjectedParameters):
    """
    DCF based on normalized flows to smooth out cyclicality.
    """
    mode: Literal[ValuationMethodology.FCFF_NORMALIZED] = ValuationMethodology.FCFF_NORMALIZED

    # --- Accounting Overrides ---
    fcf_norm: Annotated[Optional[float], UIKey("fcf_norm", scale="million")] = None
    ebit_norm: Annotated[Optional[float], UIKey("ebit_norm", scale="million")] = None

    # --- Specific Lever ---
    cycle_growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None


class FCFFGrowthParameters(BaseProjectedParameters):
    """
    DCF derived from Revenue Growth and Target Margins.
    """
    mode: Literal[ValuationMethodology.FCFF_GROWTH] = ValuationMethodology.FCFF_GROWTH

    # --- Accounting Overrides ---
    revenue_ttm: Annotated[Optional[float], UIKey("revenue_ttm", scale="million")] = None
    ebitda_ttm: Annotated[Optional[float], UIKey("ebitda_ttm", scale="million")] = None
    target_fcf_margin: Annotated[Optional[float], UIKey("fcf_margin", scale="pct")] = None
    capex_ttm: Annotated[Optional[float], UIKey("capex_ttm", scale="million")] = None

    # --- Specific Lever ---
    revenue_growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None


class FCFEResolvers(BaseProjectedParameters): # Renaming Note: Should be FCFEParameters ideally
    """
    Free Cash Flow to Equity (Post-Debt).
    NOTE: Renamed to FCFEParameters for consistency.
    """
    pass

class FCFEParameters(BaseProjectedParameters):
    """Free Cash Flow to Equity (Post-Debt)."""
    mode: Literal[ValuationMethodology.FCFE] = ValuationMethodology.FCFE

    # --- Accounting Overrides ---
    fcfe_anchor: Annotated[Optional[float], UIKey("fcfe_anchor", scale="million")] = None
    net_income_ttm: Annotated[Optional[float], UIKey("net_income_ttm", scale="million")] = None
    net_borrowing_delta: Annotated[Optional[float], UIKey("net_borrowing", scale="million")] = None
    capex_ttm: Annotated[Optional[float], UIKey("capex_ttm", scale="million")] = None

    # --- Specific Lever ---
    growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None


class DDMParameters(BaseProjectedParameters):
    """
    Dividend Discount Model.
    """
    mode: Literal[ValuationMethodology.DDM] = ValuationMethodology.DDM

    # --- Accounting Overrides ---
    dividend_per_share: Annotated[Optional[float], UIKey("div_base", scale="raw")] = None
    net_income_ttm: Annotated[Optional[float], UIKey("net_income_ttm", scale="million")] = None

    # --- Specific Lever ---
    dividend_growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None


class RIMParameters(BaseProjectedParameters):
    """
    Residual Income Model (Ohlson).
    """
    mode: Literal[ValuationMethodology.RIM] = ValuationMethodology.RIM

    # --- Accounting Overrides ---
    book_value_anchor: Annotated[Optional[float], UIKey("bv_anchor", scale="million")] = None
    net_income_norm: Annotated[Optional[float], UIKey("net_income_norm", scale="million")] = None
    total_assets: Annotated[Optional[float], UIKey("total_assets", scale="million")] = None

    # --- Specific Levers ---
    growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None
    persistence_factor: Annotated[Optional[float], UIKey("omega", scale="raw")] = None


class GrahamParameters(BaseNormalizedModel):
    """
    Graham Intrinsic Value.
    Note: Does NOT inherit from BaseProjectedParameters (Static Formula).
    """
    mode: Literal[ValuationMethodology.GRAHAM] = ValuationMethodology.GRAHAM

    # --- Accounting Overrides ---
    eps_normalized: Annotated[Optional[float], UIKey("eps_normalized", scale="raw")] = None
    revenue_ttm: Annotated[Optional[float], UIKey("revenue_ttm", scale="million")] = None

    # --- Method Levers ---
    growth_estimate: Annotated[Optional[float], UIKey("growth_estimate", scale="pct")] = None


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