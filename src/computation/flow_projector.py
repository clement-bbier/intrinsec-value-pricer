"""
src/computation/flow_projector.py

CASH FLOW PROJECTION ENGINE — GROWTH TRAJECTORIES
=================================================
Role: Manages multi-period flow projections using varied strategies.
Supported Modes: Simple Growth, Margin Convergence, and Fade-down logic.
Architecture: Strategy Pattern (SOLID) with Glass Box traceability support.

Style: Numpy docstrings
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING, Dict
from pydantic import BaseModel, Field

# i18n Imports for UI-facing elements
from src.i18n import StrategyInterpretations, StrategyFormulas, KPITexts, RegistryTexts, SharedTexts
from src.utilities.formatting import format_smart_number
from src.config.constants import GrowthCalculationDefaults
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
    flows: List[float]
    method_label: str = ""
    theoretical_formula: str = ""
    actual_calculation: str = ""
    interpretation: str = ""
    variables: Dict[str, VariableInfo] = Field(default_factory=dict)


# ==============================================================================
# 2. ABSTRACT INTERFACE (SOLID)
# ==============================================================================

class FlowProjector(ABC):
    """
    Interface for flow projection strategies (Strategy Pattern).
    Ensures decoupled logic between different growth models.
    """

    @abstractmethod
    def project(
        self,
        base_value: float,
        financials: Company,
        params: Parameters
    ) -> ProjectionOutput:
        """
        Executes the projection and returns the flows with calculation trace.

        Parameters
        ----------
        base_value : float
            The anchor value (FCF0 or Revenue0).
        financials : Company
            Current company financial data.
        params : Parameters
            User-defined or automated projection parameters.
        """
        pass

    @staticmethod
    def _build_trace_variable(
        symbol: str,
        value: float,
        manual_value: Optional[float],
        provider_value: Optional[float],
        description: str,
        is_pct: bool = False
    ) -> VariableInfo:
        """Helper to build provenance-aware variables within the projector."""
        is_overridden = manual_value is not None
        source = VariableSource.MANUAL_OVERRIDE if is_overridden else (
            VariableSource.YAHOO_FINANCE if provider_value is not None else VariableSource.DEFAULT
        )

        if is_pct:
            formatted = f"{value:.2%}"
        else:
            from src.utilities.formatting import format_smart_number
            formatted = format_smart_number(value)

        return VariableInfo(
            symbol=symbol,
            value=value,
            formatted_value=formatted,
            source=source,
            description=description,
            is_overridden=is_overridden,
            original_value=provider_value
        )


# ==============================================================================
# 3. CONCRETE IMPLEMENTATIONS
# ==============================================================================

class SimpleFlowProjector(FlowProjector):
    """
    Standard projection: $FCF \times (1+g)^t$.
    Handles linear fade-down towards the perpetual growth rate (gn).
    """

    def project(
        self,
        base_value: float,
        financials: Company,
        params: Parameters
    ) -> ProjectionOutput:
        """Projects flows with full provenance of growth rates."""
        g = params.growth

        # Resolve growth rates for trace
        g_start = g.fcf_growth_rate or 0.03
        g_term = g.perpetual_growth_rate or 0.02

        flows = project_flows(
            base_flow=base_value,
            years=g.projection_years,
            g_start=g_start,
            g_term=g_term,
            high_growth_years=g.high_growth_years
        )

        # Phase 2: Variable Provenance Mapping
        variables = {
            "g": self._build_trace_variable(
                "g", g_start, g.fcf_growth_rate, None, SharedTexts.INP_GROWTH_G, True
            ),
            "g_n": self._build_trace_variable(
                "g_n", g_term, g.perpetual_growth_rate, None, SharedTexts.INP_PERP_G, True
            ),
            "n": VariableInfo(
                symbol="n", value=float(g.projection_years), source=VariableSource.CALCULATED,
                description=SharedTexts.INP_PROJ_YEARS
            )
        }

        return ProjectionOutput(
            flows=flows,
            method_label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=StrategyFormulas.FCF_PROJECTION,
            actual_calculation=f"{format_smart_number(base_value)} × (1 + {g_start:.1%})^{g.projection_years}",
            interpretation=StrategyInterpretations.PROJ.format(years=g.projection_years, g=g_start),
            variables=variables
        )


class MarginConvergenceProjector(FlowProjector):
    """
    Revenue-Driven projection with linear margin convergence.
    Designed for high-growth or volatile margin profiles.
    """

    def project(
        self,
        base_value: float,
        financials: Company,
        params: Parameters
    ) -> ProjectionOutput:
        """Projects FCF with margin expansion/contraction traceability."""
        g = params.growth
        rev_base = base_value

        # 1. Current Margin (Calculated from TTM)
        curr_margin = 0.0
        if financials.fcf_last and rev_base > 0:
            curr_margin = financials.fcf_last / rev_base

        # 2. Target Margin (Analyst choice or default)
        target_margin = g.target_fcf_margin if g.target_fcf_margin is not None else GrowthCalculationDefaults.DEFAULT_FCF_MARGIN_TARGET

        # 3. Revenue Growth Rate
        rev_growth = g.fcf_growth_rate or 0.05

        # Projection loop
        projected_fcfs = []
        curr_rev = rev_base
        for y in range(1, g.projection_years + 1):
            curr_rev *= (1.0 + rev_growth)
            applied_margin = curr_margin + (target_margin - curr_margin) * (y / g.projection_years)
            projected_fcfs.append(curr_rev * applied_margin)

        # Phase 2: Traceability map
        variables = {
            "m_0": VariableInfo(
                symbol="m_0", value=curr_margin, source=VariableSource.CALCULATED,
                description="Current FCF Margin (TTM)"
            ),
            "m_target": self._build_trace_variable(
                "m_target", target_margin, g.target_fcf_margin, None,
                "Target FCF Margin (Normative)", True
            ),
            "g_rev": self._build_trace_variable(
                "g_rev", rev_growth, g.fcf_growth_rate, None, "Revenue Growth Rate", True
            )
        }

        return ProjectionOutput(
            flows=projected_fcfs,
            method_label=RegistryTexts.GROWTH_MARGIN_L,
            theoretical_formula=StrategyFormulas.GROWTH_MARGIN_CONV,
            actual_calculation=KPITexts.SUB_MARGIN_CONV.format(
                curr=curr_margin, target=target_margin, years=g.projection_years
            ),
            interpretation=StrategyInterpretations.GROWTH_MARGIN,
            variables=variables
        )


# ==============================================================================
# 4. ATOMIC CALCULATION LOGIC
# ==============================================================================

def project_flows(
        base_flow: float,
        years: int,
        g_start: float,
        g_term: float,
        high_growth_years: Optional[int] = 0
) -> List[float]:
    """
    Atomic engine for financial flow projection.
    Supports a 'High Growth' plateau followed by a linear 'Fade-Down'.
    """
    if years <= 0:
        return []

    flows: List[float] = []
    current_flow = base_flow
    safe_high_growth = high_growth_years if high_growth_years is not None else 0
    n_high = max(0, min(safe_high_growth, years))

    for t in range(1, years + 1):
        if t <= n_high:
            current_g = g_start
        else:
            years_remaining = years - n_high
            if years_remaining > 0:
                step_in_fade = t - n_high
                alpha = step_in_fade / years_remaining
                current_g = g_start * (1 - alpha) + g_term * alpha
            else:
                current_g = g_term

        current_flow *= (1.0 + current_g)
        flows.append(current_flow)

    return flows