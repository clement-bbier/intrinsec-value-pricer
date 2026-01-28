"""
app/ui/results/core/calculation_proof.py

CALCULATION PROOF TAB (Glass Box) — Institutional Grade.
Role: Orchestrates the sequential rendering of financial calculation steps.
Ensures full auditability of the valuation model.
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
    Strictly decouples rendering logic from calculation trace filtering.
    """

    # i18n identification
    TAB_ID = "calculation_proof"
    LABEL = KPITexts.TAB_CALC
    ORDER = 2
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders the valuation calculation sequence in an ordered fashion.
        """

        # 1. UI Business Logic: Filter technical/internal steps
        # Excludes prefixes defined in UIConstants (e.g., MC simulations, SOTP internals)
        core_steps = [
            step for step in result.calculation_trace
            if not any(prefix in step.step_key for prefix in UIConstants.EXCLUDED_STEP_PREFIXES)
        ]

        # 2. Empty state management
        if not core_steps:
            st.info(UIMessages.NO_CALCULATION_STEPS)
            return

        # 3. Tab Header (Zero hardcoding)
        st.markdown(f"### {KPITexts.TAB_CALC}")
        st.caption(KPITexts.SECTION_INPUTS_CAPTION)
        st.divider()

        # 4. Iterative rendering via stabilized atomic component
        # Each step is rendered within its own container with LaTeX support
        for idx, step in enumerate(core_steps, start=1):
            render_calculation_step(idx, step)

            # Institutional spacing between calculation blocks
            st.write("")

    def is_visible(self, result: ValuationResult) -> bool:
        """
        The tab is visible only if a calculation trace is present.
        """
        return bool(result.calculation_trace)