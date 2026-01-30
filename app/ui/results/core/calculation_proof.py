"""
app/ui/results/core/calculation_proof.py

PILLAR 2 — CALCULATION PROOF (GLASS BOX)
========================================
Role: Orchestrates the sequential rendering of financial calculation steps.
Ensures full auditability and transparency of the valuation model by
decomposing the final result into its mathematical constituents.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import KPITexts, UIMessages
from src.config.constants import UIConstants
from app.ui.results.base_result import ResultTabBase
from app.ui.results.components.step_renderer import render_calculation_step


class CalculationProofTab(ResultTabBase):
    """
    Glass Box calculation proof tab.

    This component manages the institutional hierarchy of the valuation trace,
    ensuring that complex formulas are presented in a readable, step-by-step
    format for professional auditing.
    """

    TAB_ID = "calculation_proof"
    LABEL = KPITexts.TAB_CALC
    ORDER = 2
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders the valuation calculation sequence in an ordered fashion.

        Parameters
        ----------
        result : ValuationResult
            The complete valuation result containing the calculation trace.
        **kwargs : Any
            Additional rendering context.
        """
        # 1. UI Business Logic: Filter technical/internal steps
        # Excludes internal calculation steps defined in UIConstants (e.g., MC internals)
        core_steps = [
            step for step in result.calculation_trace
            if not any(prefix in step.step_key for prefix in UIConstants.EXCLUDED_STEP_PREFIXES)
        ]

        # 2. Empty state management
        if not core_steps:
            st.info(UIMessages.NO_CALCULATION_STEPS)
            return

        # 3. Tab Header (Standardized formatting)
        st.markdown(f"### {KPITexts.TAB_CALC}")
        st.caption(KPITexts.SECTION_INPUTS_CAPTION)
        st.divider()

        # 4. Iterative rendering via stabilized atomic component
        # Each calculation step is encapsulated in its own rendering context
        for idx, step in enumerate(core_steps, start=1):
            render_calculation_step(idx, step)

            # Institutional vertical spacing between blocks
            st.write("")

    def is_visible(self, result: ValuationResult) -> bool:
        """
        Determines visibility based on the presence of a calculation trace.

        Parameters
        ----------
        result : ValuationResult
            The valuation result to inspect.

        Returns
        -------
        bool
            True if the calculation trace contains data, False otherwise.
        """
        return bool(result.calculation_trace)