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
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel

# i18n Imports for UI-facing elements
from src.i18n import StrategyInterpretations, StrategyFormulas, KPITexts, RegistryTexts
from src.utilities.formatting import format_smart_number
from src.config.constants import GrowthCalculationDefaults

if TYPE_CHECKING:
    from src.models import CompanyFinancials, DCFParameters

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
    numerical_substitution : str
        Numerical application for transparency (Year-n substitution).
    interpretation : str
        Analytical note describing the projection logic.
    """
    flows: List[float]
    method_label: str = ""
    theoretical_formula: str = ""
    numerical_substitution: str = ""
    interpretation: str = ""

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
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ProjectionOutput:
        """
        Executes the projection and returns the flows with calculation trace.

        Parameters
        ----------
        base_value : float
            The anchor value (FCF0 or Revenue0).
        financials : CompanyFinancials
            Current company financial data.
        params : DCFParameters
            User-defined or automated projection parameters.
        """
        pass

# ==============================================================================
# 3. CONCRETE IMPLEMENTATIONS
# ==============================================================================

class SimpleFlowProjector(FlowProjector):
    """
    Standard projection: $FCF \times (1+g)^t$.
    Handles linear fade-down towards the perpetual growth rate (gn).
    Recommended for 'Standard' and 'Fundamental' models.
    """

    def project(
        self,
        base_value: float,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ProjectionOutput:
        """
        Projects flows using the atomic fade-down logic.
        """
        g = params.growth

        # Atomic logic execution for growth trajectories
        flows = project_flows(
            base_flow=base_value,
            years=g.projection_years,
            g_start=g.fcf_growth_rate or 0.0,
            g_term=g.perpetual_growth_rate or 0.0,
            high_growth_years=g.high_growth_years
        )

        # Glass Box Trace Generation
        formula = StrategyFormulas.FCF_PROJECTION
        base_formatted = format_smart_number(base_value)
        growth_rate = g.fcf_growth_rate or 0.0

        # Substitution template for UI transparency
        sub = f"{base_formatted} × (1 + {growth_rate:.1%})^{g.projection_years}"

        # Localized analytical interpretation
        interp = StrategyInterpretations.PROJ.format(
            years=g.projection_years,
            g=g.fcf_growth_rate or 0
        )

        return ProjectionOutput(
            flows=flows,
            method_label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=formula,
            numerical_substitution=sub,
            interpretation=interp
        )


class MarginConvergenceProjector(FlowProjector):
    """
    Revenue-Driven projection with linear margin convergence.
    Designed for high-growth or volatile margin profiles (Tech / Growth).
    """

    def project(
        self,
        base_value: float,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ProjectionOutput:
        """
        Projects FCF by forecasting Revenue and converging current margins to a target profile.
        """
        g = params.growth
        rev_base = base_value

        # Determine current and target margins for the convergence bridge
        curr_margin = 0.0
        if financials.fcf_last and rev_base > 0:
            curr_margin = financials.fcf_last / rev_base

        # Target margin resolution (Expert override or sector default)
        target_margin = g.target_fcf_margin if g.target_fcf_margin is not None else GrowthCalculationDefaults.DEFAULT_FCF_MARGIN_TARGET

        # Revenue and FCF projection loop (Linear Bridge)
        projected_fcfs = []
        curr_rev = rev_base
        for y in range(1, g.projection_years + 1):
            curr_rev *= (1.0 + (g.fcf_growth_rate or 0.0))
            # Linear interpolation of margins over the projection horizon
            applied_margin = curr_margin + (target_margin - curr_margin) * (y / g.projection_years)
            projected_fcfs.append(curr_rev * applied_margin)

        # Specific Glass Box trace for margin logic
        formula = r"FCF_t = Rev_t \times [Margin_0 + (Margin_n - Margin_0) \times \frac{t}{n}]"
        sub = KPITexts.SUB_MARGIN_CONV.format(
            curr=curr_margin,
            target=target_margin,
            years=g.projection_years
        )
        interp = StrategyInterpretations.GROWTH_MARGIN

        return ProjectionOutput(
            flows=projected_fcfs,
            method_label=RegistryTexts.GROWTH_MARGIN_L,
            theoretical_formula=formula,
            numerical_substitution=sub,
            interpretation=interp
        )

# ==============================================================================
# 4. ATOMIC CALCULATION LOGIC (RESILIENT)
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
    Supports a 'High Growth' plateau followed by a linear 'Fade-Down' towards g_perpetual.

    Parameters
    ----------
    base_flow : float
        Starting flow (Year 0).
    years : int
        Total projection horizon.
    g_start : float
        Initial growth rate (Phase 1).
    g_term : float
        Target terminal growth rate (Phase 2).
    high_growth_years : int, optional
        Duration of the growth plateau before fade-down begins.
    """
    if years <= 0:
        return []

    flows: List[float] = []
    current_flow = base_flow

    # Safety clamping for plateau duration
    safe_high_growth = high_growth_years if high_growth_years is not None else 0
    n_high = max(0, min(safe_high_growth, years))

    gs = g_start if g_start is not None else 0.0
    gt = g_term if g_term is not None else 0.0

    for t in range(1, years + 1):
        if t <= n_high:
            current_g = gs
        else:
            # Linear transition (Fade-down) from start growth to terminal growth
            years_remaining = years - n_high
            if years_remaining > 0:
                step_in_fade = t - n_high
                alpha = step_in_fade / years_remaining
                current_g = gs * (1 - alpha) + gt * alpha
            else:
                current_g = gt

        current_flow = current_flow * (1.0 + current_g)
        flows.append(current_flow)

    return flows