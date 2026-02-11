"""
src/models/parameters/strategies.py

SPECIFIC VALUATION STRATEGY PARAMETERS
======================================
Role: Captures User Overrides with factored projection logic and UI mapping.
Architecture: Inherits from BaseNormalizedModel for automatic scaling.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from src.models.enums import TerminalValueMethod, ValuationMethodology
from src.models.parameters.common import BaseNormalizedModel
from src.models.parameters.input_metadata import UIKey


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
    method: TerminalValueMethod | None = None
    perpetual_growth_rate: Annotated[float | None, UIKey("gn", scale="pct")] = None
    exit_multiple: Annotated[float | None, UIKey("exit_mult", scale="raw")] = None


class BaseProjectedParameters(BaseNormalizedModel):
    """
    Mixin for models requiring a discrete projection period.

    Attributes
    ----------
    projection_years : int | None
        Number of years in the explicit forecast period (Standard: 5-10).
    manual_growth_vector : List[float] | None
        Optional year-by-year growth overrides provided by the user.
    terminal_value : TerminalValueParameters
        Configuration for the post-projection value.
    """
    projection_years: Annotated[int | None, UIKey("years", scale="raw")] = Field(None, ge=1, le=50)
    manual_growth_vector: Annotated[list[float] | None, UIKey("growth_vector", scale="pct")] = None
    terminal_value: TerminalValueParameters = Field(default_factory=TerminalValueParameters)


class FCFFStandardParameters(BaseProjectedParameters):
    """
    Standard DCF based on Free Cash Flow to Firm (Starting from EBIT/EBITDA).

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to FCFF_STANDARD.
    fcf_anchor : float | None
        The base year Free Cash Flow to Firm (usually LTM).
    growth_rate_p1 : float | None
        The CAGR applied during the explicit projection period.
    """
    mode: Literal[ValuationMethodology.FCFF_STANDARD] = ValuationMethodology.FCFF_STANDARD
    fcf_anchor: Annotated[float | None, UIKey("fcf_base", scale="million")] = None
    growth_rate_p1: Annotated[float | None, UIKey("growth_rate", scale="pct")] = None


class FCFFNormalizedParameters(BaseProjectedParameters):
    """
    DCF based on normalized flows to smooth out cyclicality.

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to FCFF_NORMALIZED.
    fcf_norm : float | None
        The normalized (mid-cycle) Free Cash Flow.
    cycle_growth_rate : float | None
        The growth rate applied to the normalized base.
    """
    mode: Literal[ValuationMethodology.FCFF_NORMALIZED] = ValuationMethodology.FCFF_NORMALIZED
    fcf_norm: Annotated[float | None, UIKey("fcf_norm", scale="million")] = None
    cycle_growth_rate: Annotated[float | None, UIKey("growth_rate", scale="pct")] = None


class FCFFGrowthParameters(BaseProjectedParameters):
    """
    DCF derived from Revenue Growth and Target Margins.

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to FCFF_GROWTH.
    revenue_ttm : float | None
        Trailing Twelve Months Revenue.
    revenue_growth_rate : float | None
        Expected annual revenue growth.
    target_fcf_margin : float | None
        The expected FCF margin (FCF / Revenue) at maturity.
    """
    mode: Literal[ValuationMethodology.FCFF_GROWTH] = ValuationMethodology.FCFF_GROWTH
    revenue_ttm: Annotated[float | None, UIKey("revenue_ttm", scale="million")] = None
    revenue_growth_rate: Annotated[float | None, UIKey("growth_rate", scale="pct")] = None
    target_fcf_margin: Annotated[float | None, UIKey("fcf_margin", scale="pct")] = None


class FCFEParameters(BaseProjectedParameters):
    """
    Free Cash Flow to Equity (Post-Debt) Valuation.

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to FCFE.
    fcfe_anchor : float | None
        Base year Free Cash Flow to Equity.
    growth_rate : float | None
        Growth rate of equity cash flows.
    """
    mode: Literal[ValuationMethodology.FCFE] = ValuationMethodology.FCFE
    fcfe_anchor: Annotated[float | None, UIKey("fcfe_anchor", scale="million")] = None
    growth_rate: Annotated[float | None, UIKey("growth_rate", scale="pct")] = None


class DDMParameters(BaseProjectedParameters):
    """
    Dividend Discount Model (Gordon + Multi-stage).

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to DDM.
    dividend_per_share : float | None
        Base year Dividend Per Share (DPS).
    dividend_growth_rate : float | None
        Expected annual growth of dividends.
    """
    mode: Literal[ValuationMethodology.DDM] = ValuationMethodology.DDM
    dividend_per_share: Annotated[float | None, UIKey("div_base", scale="raw")] = None
    dividend_growth_rate: Annotated[float | None, UIKey("growth_rate", scale="pct")] = None


class RIMParameters(BaseProjectedParameters):
    """
    Residual Income Model (Ohlson Model).

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to RIM.
    book_value_anchor : float | None
        Current Book Value of Equity.
    persistence_factor : float | None
        The 'Omega' factor (0-1) determining how long excess returns persist.
    """
    mode: Literal[ValuationMethodology.RIM] = ValuationMethodology.RIM
    book_value_anchor: Annotated[float | None, UIKey("bv_anchor", scale="million")] = None
    persistence_factor: Annotated[float | None, UIKey("omega", scale="raw")] = None


class GrahamParameters(BaseNormalizedModel):
    """
    Benjamin Graham Intrinsic Value (Static Formula).

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to GRAHAM.
    eps_normalized : float | None
        Normalized Earnings Per Share.
    growth_estimate : float | None
        Conservative growth estimate (7-10 years).
    """
    mode: Literal[ValuationMethodology.GRAHAM] = ValuationMethodology.GRAHAM
    eps_normalized: Annotated[float | None, UIKey("eps_normalized", scale="raw")] = None
    growth_estimate: Annotated[float | None, UIKey("growth_estimate", scale="pct")] = None


StrategyUnionParameters = (
    FCFFStandardParameters | FCFFNormalizedParameters | FCFFGrowthParameters
    | FCFEParameters | DDMParameters | RIMParameters | GrahamParameters
)
