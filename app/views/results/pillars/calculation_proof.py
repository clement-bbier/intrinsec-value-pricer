"""
app/views/results/pillars/calculation_proof.py
PILLAR 2: CALCULATION PROOF (GLASS BOX)
=======================================
Role: Orchestrates the sequential rendering of financial calculation steps.
Ensures full auditability and transparency of the valuation model by
decomposing the final result into its mathematical constituents.
"""

import streamlit as st

from app.views.components.step_renderer import render_calculation_step
from src.i18n import KPITexts, PillarLabels, ResultsTexts, UIMessages
from src.models import CalculationStep, ValuationResult

# Constants for filtering internal/technical steps that shouldn't appear in the audit
EXCLUDED_STEP_PREFIXES = ("_meta", "internal_", "debug_")


def render_glass_box(result: ValuationResult) -> None:
    """
    Renders Pillar 2: The Mathematical Trace (Glass Box).

    This function iterates through the calculation traces provided by the backend
    (both Strategy-specific and Common Bridge steps) and renders each step
    using a standardized UI component.

    Parameters
    ----------
    result : ValuationResult
        The fully computed valuation object containing the nested results structures.
    """
    # 1. Header and Context
    st.subheader(PillarLabels.PILLAR_2_TRACE)
    st.caption(KPITexts.HELP_IV)
    st.divider()

    # 2. Trace Extraction (Aggregation from Architectural Pillars)
    # We must combine the strategy-specific steps (DCF/Graham logic)
    # with the common bridge steps (WACC, Debt, Equity Bridge).

    # Access via safe Pydantic paths
    strategy_trace = result.results.strategy.strategy_trace
    bridge_trace = result.results.common.bridge_trace

    # Merge traces: Strategy first (Operating Value), then Bridge (Equity Value)
    full_trace: list[CalculationStep] = strategy_trace + bridge_trace

    # 3. Data Validation & Filtering
    if not full_trace:
        st.info(ResultsTexts.NO_FINANCIALS_PROVIDED)
        return

    core_steps = [step for step in full_trace if not any(step.step_key.startswith(prefix) for prefix in EXCLUDED_STEP_PREFIXES)]

    # 4. Empty State Management
    if not core_steps:
        st.info(UIMessages.NO_MAJOR_CALC_STEPS)
        return

    # 5. Iterative Rendering
    # Each calculation step is encapsulated in its own rendering context
    for idx, step in enumerate(core_steps, start=1):
        render_calculation_step(index=idx, step=step)

        # Spacer for readability
        st.write("")
