"""
app/views/results/pillars/calculation_proof.py
PILLAR 2: CALCULATION PROOF (GLASS BOX)
=======================================
Role: Orchestrates the sequential rendering of financial calculation steps.
Ensures full auditability and transparency of the valuation model by
decomposing the final result into its mathematical constituents.
"""

import streamlit as st
from src.models import ValuationResult
from src.i18n import KPITexts, PillarLabels, ResultsTexts
from app.views.components.step_renderer import render_calculation_step

# Constants for filtering internal/technical steps that shouldn't appear in the audit
EXCLUDED_STEP_PREFIXES = ("_meta", "internal_", "debug_")

def render_glass_box(result: ValuationResult) -> None:
    """
    Renders Pillar 2: The Mathematical Trace (Glass Box).

    This function iterates through the calculation trace provided by the backend
    and renders each step using a standardized UI component. It filters out
    technical steps to ensure the view remains relevant for financial auditing.

    Parameters
    ----------
    result : ValuationResult
        The fully computed valuation object containing the `calculation_trace` list.
    """
    # 1. Header and Context
    st.subheader(PillarLabels.PILLAR_2_TRACE)
    st.caption(KPITexts.HELP_IV)
    st.divider()

    # 2. Data Validation
    if not result.calculation_trace:
        st.info(ResultsTexts.NO_FINANCIALS_PROVIDED)
        return

    # 3. Trace Extraction and Filtering
    core_steps = [
        step for step in result.calculation_trace
        if not any(step.step_key.startswith(prefix) for prefix in EXCLUDED_STEP_PREFIXES)
    ]

    # 4. Empty State Management
    if not core_steps:
        st.info("Aucune étape majeure disponible pour ce calcul.")
        return

    # 5. Iterative Rendering
    # Each calculation step is encapsulated in its own rendering context
    for idx, step in enumerate(core_steps, start=1):
        render_calculation_step(index=idx, step=step)

        # Spacer for readability
        st.write("")