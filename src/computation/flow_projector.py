"""
src/computation/flow_projector.py

CASH FLOW PROJECTION ENGINE — GROWTH TRAJECTORIES
=================================================
Role: Manages multi-period flow projections using varied strategies.
Supported Modes: Simple Growth, Margin Convergence, and Fade-down logic.
Architecture: Strategy Pattern (SOLID) with Glass Box traceability support.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from src.core.formatting import format_smart_number

# i18n Imports for UI-facing elements
from src.i18n import KPITexts, RegistryTexts, SharedTexts, StrategyFormulas, StrategyInterpretations
from src.models import VariableInfo, VariableSource

if TYPE_CHECKING:
    from src.models import Company, Parameters

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. OUTPUT MODELS (CONTRACTS)
# ==============================================================================


class ProjectionOutput(BaseModel):
    """
    Data contract for projection results, ready for Glass Box rendering.

    Attributes
    ----------
    flows : List[float]
        The series of projected cash flows.
    method_label : str
        Localized name of the projection method.
    theoretical_formula : str
        LaTeX representation of the applied formula.
    actual_calculation : str
        Numerical application for transparency (Year-n substitution).
    interpretation : str
        Analytical note describing the projection logic.
    variables : Dict[str, VariableInfo]
        Traceability map for all parameters used during the projection.
    """

    flows: list[float]
    method_label: str = ""
    theoretical_formula: str = ""
    actual_calculation: str = ""
    interpretation: str = ""
    variables: dict[str, VariableInfo] = Field(default_factory=dict)


# ==============================================================================
# 2. ABSTRACT INTERFACE (SOLID)
# ==============================================================================


class FlowProjector(ABC):
    """
    Interface for flow projection strategies (Strategy Pattern).
    Ensures decoupled logic between different growth models.
    """

    @abstractmethod
    def project(self, base_value: float, financials: Company, params: Parameters) -> ProjectionOutput:
        """
        Executes the projection and returns the flows with calculation trace.

        Parameters
        ----------
        base_value : float
            The anchor value (FCF0 or Revenue0).
        financials : Company
            Current company financial data (Identity & Context).
        params : Parameters
            User-defined or automated projection parameters (Strategy).
        """
        pass

    @staticmethod
    def _build_trace_variable(
        symbol: str,
        value: float,
        manual_value: float | None,
        provider_value: float | None,
        description: str,
        is_pct: bool = False,
    ) -> VariableInfo:
        """Helper to build provenance-aware variables within the projector."""
        is_overridden = manual_value is not None
        source = (
            VariableSource.MANUAL_OVERRIDE
            if is_overridden
            else (VariableSource.YAHOO_FINANCE if provider_value is not None else VariableSource.DEFAULT)
        )

        formatted = f"{value:.2%}" if is_pct else format_smart_number(value)

        return VariableInfo(
            symbol=symbol,
            value=value,
            formatted_value=formatted,
            source=source,
            description=description,
            is_overridden=is_overridden,
            original_value=provider_value,
        )


# ==============================================================================
# 3. CONCRETE IMPLEMENTATIONS
# ==============================================================================


class SimpleFlowProjector(FlowProjector):
    """
    Standard projection: $FCF \times (1+g)^t$.
    Handles linear fade-down towards the perpetual growth rate (gn) if required.
    """

    def project(self, base_value: float, financials: Company, params: Parameters) -> ProjectionOutput:
        """Projects flows with full provenance of growth rates."""
        # 1. Strategy Extraction (New Model Architecture)
        strat = params.strategy

        # Handle Polymorphism: Standard DCF uses 'growth_rate_p1', others 'growth_rate'
        # We try to fetch the explicit period growth rate safely
        g_start = getattr(strat, "growth_rate_p1", getattr(strat, "growth_rate", 0.03)) or 0.03

        # Terminal Growth Rate
        g_term = 0.02
        if hasattr(strat, "terminal_value") and strat.terminal_value:
            g_term = strat.terminal_value.perpetual_growth_rate or 0.02

        years = getattr(strat, "projection_years", 5) or 5

        # High Growth Period: If not set, default to full projection period (no fade)
        high_growth_years = getattr(strat, "high_growth_period", None)
        if high_growth_years is None:
            high_growth_years = years

        # 2. Computation
        flows = project_flows(
            base_flow=base_value,
            years=years,
            g_start=g_start,
            g_term=g_term,
            high_growth_years=high_growth_years,
        )

        # 3. Glass Box Traceability
        variables = {
            "g": self._build_trace_variable("g", g_start, g_start, None, SharedTexts.INP_GROWTH_G, True),
            "g_n": self._build_trace_variable("g_n", g_term, g_term, None, SharedTexts.INP_PERP_G, True),
            "n": VariableInfo(
                symbol="n", value=float(years), source=VariableSource.CALCULATED, description=SharedTexts.INP_PROJ_YEARS
            ),
        }

        return ProjectionOutput(
            flows=flows,
            method_label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=StrategyFormulas.FCF_PROJECTION,
            actual_calculation=f"{format_smart_number(base_value)} × (1 + {g_start:.1%})^{years}",
            interpretation=StrategyInterpretations.PROJ.format(years=years, g=g_start),
            variables=variables,
        )


class MarginConvergenceProjector(FlowProjector):
    """
    Revenue-Driven projection with linear margin convergence.
    Designed for high-growth or volatile margin profiles.
    Used primarily by FCFFGrowthParameters.
    """

    def project(self, base_value: float, financials: Company, params: Parameters) -> ProjectionOutput:
        """Projects FCF with margin expansion/contraction traceability."""
        strat = params.strategy

        # base_value here is assumed to be Revenue TTM
        rev_base = base_value

        # 1. Resolve Parameters safely
        target_margin = getattr(strat, "target_fcf_margin", 0.10) or 0.10
        rev_growth = getattr(strat, "revenue_growth_rate", 0.05) or 0.05
        years = getattr(strat, "projection_years", 5) or 5

        # 2. Estimate Current Margin
        # Since 'Company' is frozen/static, we infer current margin from the strategy
        # or defaults if not provided. Ideally, we would need FCF TTM here.
        # Fallback: Assume current margin is implied 0 if unknown, or rely on caller context.
        # For calculation safety, we start at a conservative estimate if data is missing.
        curr_margin = 0.0
        # Attempt to find implied margin if FCF TTM is available elsewhere,
        # otherwise we assume a linear ramp from 0 or a simplistic start.
        # In this specific context, we'll assume the ramp starts from the implied margin
        # if 'fcf_anchor' was available, but FCFFGrowth doesn't use anchor.
        # Simplification: Start at 50% of target if unknown, or 0.

        # 3. Projection Loop
        projected_fcfs = []
        curr_rev = rev_base

        for y in range(1, years + 1):
            curr_rev *= 1.0 + rev_growth
            # Linear interpolation of margin
            applied_margin = curr_margin + (target_margin - curr_margin) * (y / years)
            projected_fcfs.append(curr_rev * applied_margin)

        # 4. Traceability
        variables = {
            "m_target": self._build_trace_variable(
                "m_target", target_margin, target_margin, None, "Target FCF Margin (Normative)", True
            ),
            "g_rev": self._build_trace_variable("g_rev", rev_growth, rev_growth, None, "Revenue Growth Rate", True),
        }

        return ProjectionOutput(
            flows=projected_fcfs,
            method_label=RegistryTexts.GROWTH_MARGIN_L,
            theoretical_formula=StrategyFormulas.GROWTH_MARGIN_CONV,
            actual_calculation=KPITexts.SUB_MARGIN_CONV.format(curr=curr_margin, target=target_margin, years=years),
            interpretation=StrategyInterpretations.GROWTH_MARGIN,
            variables=variables,
        )


# ==============================================================================
# 4. ATOMIC CALCULATION LOGIC
# ==============================================================================


def project_flows(
    base_flow: float, years: int, g_start: float, g_term: float, high_growth_years: int | None = 0
) -> list[float]:
    """
    Atomic engine for financial flow projection with fade transition.

    Supports a 'High Growth' plateau followed by a linear 'Fade-Down' to terminal growth.
    This eliminates the brutal shock between strong growth and perpetual growth rates.

    Parameters
    ----------
    base_flow : float
        The starting cash flow value (FCF0, Revenue0, etc.).
    years : int
        Total number of projection years.
    g_start : float
        High growth rate during the plateau phase.
    g_term : float
        Terminal perpetual growth rate.
    high_growth_years : int | None, optional
        Number of years to maintain high growth before fading.
        If None, defaults to full projection period (no fade).
        If 0, fade begins immediately from year 1.

    Returns
    -------
    list[float]
        Projected cash flows for each year.

    Notes
    -----
    The fade phase uses linear interpolation:
    - Year t in fade phase: g(t) = g_start * (1 - α) + g_term * α
    - Where α = (t - high_growth_years) / (years - high_growth_years)
    
    Examples
    --------
    >>> # 5 years projection, 3 years high growth at 10%, then fade to 2%
    >>> flows = project_flows(1000, 5, 0.10, 0.02, 3)
    >>> # Years 1-3: 10% growth
    >>> # Years 4-5: Linear fade from 10% to 2%
    """
    if years <= 0:
        return []

    flows: list[float] = []
    current_flow = base_flow

    # If high_growth_years is not set (None), assume full period is high growth
    safe_high_growth = high_growth_years if high_growth_years is not None else years
    n_high = max(0, min(safe_high_growth, years))

    for t in range(1, years + 1):
        if t <= n_high:
            current_g = g_start
        else:
            # Linear interpolation towards terminal growth
            years_remaining = years - n_high
            if years_remaining > 0:
                step_in_fade = t - n_high
                alpha = step_in_fade / years_remaining
                current_g = g_start * (1 - alpha) + g_term * alpha
            else:
                current_g = g_term

        current_flow *= 1.0 + current_g
        flows.append(current_flow)

    return flows
