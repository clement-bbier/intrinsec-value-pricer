"""
src/models/parameters/strategies.py

SPECIFIC VALUATION STRATEGY PARAMETERS
======================================
Role: Captures User Overrides with factored projection logic and UI mapping.
Architecture: Inherits from BaseNormalizedModel for automatic scaling.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from src.config.constants import UIKeys
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
    roic_stable : float | None
        Return on Invested Capital in stable state (decimal form, e.g., 0.15 for 15%).
        Used to apply the "Golden Rule" of terminal value: ensures consistency
        between perpetual growth and required reinvestment. If None, no adjustment
        is applied (conservative approach).
    """

    method: TerminalValueMethod | None = None
    perpetual_growth_rate: Annotated[float | None, UIKey(UIKeys.GN, scale="pct")] = None
    exit_multiple: Annotated[float | None, UIKey(UIKeys.EXIT_MULT, scale="raw")] = None
    roic_stable: Annotated[float | None, UIKey(UIKeys.ROIC_STABLE, scale="pct")] = None


class BaseProjectedParameters(BaseNormalizedModel):
    """
    Mixin for models requiring a discrete projection period.

    Attributes
    ----------
    projection_years : int | None
        Number of years in the explicit forecast period (Standard: 5-10).
    high_growth_period : int | None
        Number of years of high growth before linear fade to terminal rate.
        If None, defaults to projection_years (no fade transition).
    manual_growth_vector : List[float] | None
        Optional year-by-year growth overrides provided by the user.
    terminal_value : TerminalValueParameters
        Configuration for the post-projection value.
    """

    projection_years: Annotated[int | None, UIKey(UIKeys.YEARS, scale="raw")] = Field(None, ge=1, le=50)
    high_growth_period: Annotated[int | None, UIKey(UIKeys.HIGH_GROWTH_YEARS, scale="raw")] = Field(None, ge=0, le=50)
    manual_growth_vector: Annotated[list[float] | None, UIKey(UIKeys.GROWTH_VECTOR, scale="pct")] = None
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
    fcf_anchor: Annotated[float | None, UIKey(UIKeys.FCF_BASE, scale="million")] = None
    growth_rate_p1: Annotated[float | None, UIKey(UIKeys.GROWTH_RATE, scale="pct")] = None


class FCFFNormalizedParameters(BaseProjectedParameters):
    """
    DCF based on normalized flows to smooth out cyclicality.

    Implements Damodaran value creation drivers: g = ROIC × Reinvestment Rate.

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to FCFF_NORMALIZED.
    fcf_norm : float | None
        The normalized (mid-cycle) Free Cash Flow.
    roic : float | None
        Return on Invested Capital (ROIC), used to compute growth.
    reinvestment_rate : float | None
        Proportion of earnings reinvested, used to compute growth.
    growth_rate : float | None
        Optional manual override for growth rate (g). If provided, used for
        consistency validation against ROIC × Reinvestment Rate.
    """

    mode: Literal[ValuationMethodology.FCFF_NORMALIZED] = ValuationMethodology.FCFF_NORMALIZED
    fcf_norm: Annotated[float | None, UIKey(UIKeys.FCF_NORM, scale="million")] = None
    roic: Annotated[float | None, UIKey(UIKeys.ROIC, scale="pct")] = None
    reinvestment_rate: Annotated[float | None, UIKey(UIKeys.REINVESTMENT_RATE, scale="pct")] = None
    growth_rate: Annotated[float | None, UIKey(UIKeys.GROWTH_RATE, scale="pct")] = None


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
    wcr_to_revenue_ratio : float | None
        Working Capital Requirement to Revenue ratio. Used to calculate
        working capital needs based on revenue changes (ΔBFR = ΔRevenue × ratio).
        If None, uses historical average from company data.
    """

    mode: Literal[ValuationMethodology.FCFF_GROWTH] = ValuationMethodology.FCFF_GROWTH
    revenue_ttm: Annotated[float | None, UIKey(UIKeys.REVENUE_TTM, scale="million")] = None
    revenue_growth_rate: Annotated[float | None, UIKey(UIKeys.GROWTH_RATE, scale="pct")] = None
    target_fcf_margin: Annotated[float | None, UIKey(UIKeys.FCF_MARGIN, scale="pct")] = None
    wcr_to_revenue_ratio: Annotated[float | None, UIKey(UIKeys.WCR_TO_REVENUE_RATIO, scale="pct")] = None


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
    net_borrowing_delta : float | None
        Net change in borrowings (ΔDebt) for the projection period.
    """

    mode: Literal[ValuationMethodology.FCFE] = ValuationMethodology.FCFE
    fcfe_anchor: Annotated[float | None, UIKey(UIKeys.FCFE_ANCHOR, scale="million")] = None
    growth_rate: Annotated[float | None, UIKey(UIKeys.GROWTH_RATE, scale="pct")] = None
    net_borrowing_delta: Annotated[float | None, UIKey(UIKeys.NET_BORROWING_DELTA, scale="million")] = None


class DDMParameters(BaseProjectedParameters):
    """
    Dividend Discount Model (Gordon + Multi-stage).

    Attributes
    ----------
    mode : ValuationMethodology
        Fixed to DDM.
    dividend_per_share : float | None
        Base year Dividend Per Share (DPS).
    growth_rate : float | None
        Expected annual growth of dividends.
    """

    mode: Literal[ValuationMethodology.DDM] = ValuationMethodology.DDM
    dividend_per_share: Annotated[float | None, UIKey(UIKeys.DIV_BASE, scale="raw")] = None
    growth_rate: Annotated[float | None, UIKey(UIKeys.GROWTH_RATE, scale="pct")] = None


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
    growth_rate : float | None
        Expected earnings growth rate.
    eps_anchor : float | None
        Normalized or adjusted Earnings Per Share.
    """

    mode: Literal[ValuationMethodology.RIM] = ValuationMethodology.RIM
    book_value_anchor: Annotated[float | None, UIKey(UIKeys.BV_ANCHOR, scale="million")] = None
    persistence_factor: Annotated[float | None, UIKey(UIKeys.OMEGA, scale="raw")] = None
    growth_rate: Annotated[float | None, UIKey(UIKeys.GROWTH_RATE, scale="pct")] = None
    eps_anchor: Annotated[float | None, UIKey(UIKeys.EPS_ANCHOR, scale="raw")] = None


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
    yield_aaa : float | None
        Corporate AAA Bond Yield override.
    tax_rate : float | None
        Effective tax rate override.
    """

    mode: Literal[ValuationMethodology.GRAHAM] = ValuationMethodology.GRAHAM
    eps_normalized: Annotated[float | None, UIKey(UIKeys.EPS_NORMALIZED, scale="raw")] = None
    growth_estimate: Annotated[float | None, UIKey(UIKeys.GROWTH_ESTIMATE, scale="pct")] = None
    yield_aaa: Annotated[float | None, UIKey(UIKeys.YIELD_AAA, scale="pct")] = None
    tax_rate: Annotated[float | None, UIKey(UIKeys.TAX, scale="pct")] = None


StrategyUnionParameters = (
    FCFFStandardParameters
    | FCFFNormalizedParameters
    | FCFFGrowthParameters
    | FCFEParameters
    | DDMParameters
    | RIMParameters
    | GrahamParameters
)
