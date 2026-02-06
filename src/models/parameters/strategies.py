"""
src/models/parameters/strategies.py

SPECIFIC VALUATION STRATEGY PARAMETERS
======================================
Role: Captures User Overrides with factored projection logic and UI mapping.
Architecture: Inherits from BaseNormalizedModel for automatic scaling.
"""

from __future__ import annotations
from typing import Optional, Literal, Union, Annotated, List
from pydantic import Field
from src.models.enums import ValuationMethodology, TerminalValueMethod
from src.models.parameters.ui_bridge import UIKey
from .common import BaseNormalizedModel

class TerminalValueParameters(BaseNormalizedModel):
    """Parameters for Step 4: Terminal Value (Exit Logic)."""
    method: Optional[TerminalValueMethod] = None
    perpetual_growth_rate: Annotated[Optional[float], UIKey("gn", scale="pct")] = None
    exit_multiple: Annotated[Optional[float], UIKey("exit_mult", scale="raw")] = None

class BaseProjectedParameters(BaseNormalizedModel):
    """Mixin for models requiring a discrete projection period."""
    projection_years: Annotated[Optional[int], UIKey("years", scale="raw")] = Field(None, ge=1, le=50)
    manual_growth_vector: Annotated[Optional[List[float]], UIKey("growth_vector", scale="pct")] = None
    terminal_value: TerminalValueParameters = Field(default_factory=TerminalValueParameters)

class FCFFStandardParameters(BaseProjectedParameters):
    """Standard DCF based on Free Cash Flow to Firm."""
    mode: Literal[ValuationMethodology.FCFF_STANDARD] = ValuationMethodology.FCFF_STANDARD
    fcf_anchor: Annotated[Optional[float], UIKey("fcf_base", scale="million")] = None
    growth_rate_p1: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None

class FCFFNormalizedParameters(BaseProjectedParameters):
    """DCF based on normalized cycle flows."""
    mode: Literal[ValuationMethodology.FCFF_NORMALIZED] = ValuationMethodology.FCFF_NORMALIZED
    fcf_norm: Annotated[Optional[float], UIKey("fcf_norm", scale="million")] = None
    cycle_growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None

class FCFFGrowthParameters(BaseProjectedParameters):
    """DCF starting from Revenue and Margins."""
    mode: Literal[ValuationMethodology.FCFF_GROWTH] = ValuationMethodology.FCFF_GROWTH
    revenue_ttm: Annotated[Optional[float], UIKey("revenue_ttm", scale="million")] = None
    revenue_growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None
    target_fcf_margin: Annotated[Optional[float], UIKey("fcf_margin", scale="pct")] = None

class FCFEParameters(BaseProjectedParameters):
    """Free Cash Flow to Equity (Post-Debt)."""
    mode: Literal[ValuationMethodology.FCFE] = ValuationMethodology.FCFE
    fcfe_anchor: Annotated[Optional[float], UIKey("fcfe_anchor", scale="million")] = None
    growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None

class DDMParameters(BaseProjectedParameters):
    """Dividend Discount Model."""
    mode: Literal[ValuationMethodology.DDM] = ValuationMethodology.DDM
    dividend_per_share: Annotated[Optional[float], UIKey("div_base", scale="raw")] = None
    dividend_growth_rate: Annotated[Optional[float], UIKey("growth_rate", scale="pct")] = None

class RIMParameters(BaseProjectedParameters):
    """Residual Income Model (Ohlson)."""
    mode: Literal[ValuationMethodology.RIM] = ValuationMethodology.RIM
    book_value_anchor: Annotated[Optional[float], UIKey("bv_anchor", scale="million")] = None
    persistence_factor: Annotated[Optional[float], UIKey("omega", scale="raw")] = None

class GrahamParameters(BaseNormalizedModel):
    """Graham Intrinsic Value (Static Formula)."""
    mode: Literal[ValuationMethodology.GRAHAM] = ValuationMethodology.GRAHAM
    eps_normalized: Annotated[Optional[float], UIKey("eps_normalized", scale="raw")] = None
    growth_estimate: Annotated[Optional[float], UIKey("growth_estimate", scale="pct")] = None

StrategyUnionParameters = Union[
    FCFFStandardParameters, FCFFNormalizedParameters, FCFFGrowthParameters,
    FCFEParameters, DDMParameters, RIMParameters, GrahamParameters
]