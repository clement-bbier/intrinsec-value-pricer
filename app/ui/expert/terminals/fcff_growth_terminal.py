"""
app/ui/expert/terminals/fcff_growth_terminal.py

EXPERT TERMINAL — FCFF REVENUE-DRIVEN (GROWTH & MARGIN)
======================================================
Valuation interface based on revenue growth and margin convergence.
Aligned with FCFFGrowthParameters for direct Pydantic injection.

Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFFGrowthTexts as Texts
from ..base_terminal import BaseTerminalExpert
from app.ui.expert.terminals.shared_widgets import widget_projection_years


class FCFFGrowthTerminalTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for the Revenue-Driven FCFF model.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFF_GROWTH for revenue-driven valuation.
    """

    MODE = ValuationMethodology.FCFF_GROWTH
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Narrative LaTeX Formulas ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{Rev_n \times Margin_{target} \times (1+g_n)}{WACC - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the Revenue-Driven FCFF model.
        Keys are aligned with FCFFGrowthParameters fields.

        Returns
        -------
        Dict[str, Any]
            Full set of captured parameters for strategy extraction.
        """
        # --- STEP 1: REVENUE BASE (Strategy -> revenue_ttm) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        rev_base = st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_REV_TTM,
            key="revenue_ttm"  # Direct Pydantic Field
        )
        st.divider()

        # --- STEP 2: MARGIN CONVERGENCE (Strategy -> growth & margin) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        col1, col2, col3 = st.columns(3)
        with col1:
            # Aligné via le préfixe 'strategy' pour donner 'strategy_years'
            n_years = widget_projection_years(default=5, key_prefix="strategy")
        with col2:
            g_rev = st.number_input(
                Texts.INP_REV_GROWTH,
                value=None,
                format="%.2f",
                help=Texts.HELP_REV_GROWTH,
                key="revenue_growth_rate"  # Direct Pydantic Field
            )
        with col3:
            m_target = st.number_input(
                Texts.INP_MARGIN_TARGET,
                value=None,
                format="%.2f",
                help=Texts.HELP_MARGIN_TARGET,
                key="target_fcf_margin"  # Direct Pydantic Field
            )

        st.divider()
        return {
            "revenue_ttm": rev_base,
            "projection_years": n_years,
            "revenue_growth_rate": g_rev,
            "target_fcf_margin": m_target
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts FCFF Growth data for the 'strategy' block.

        Returns
        -------
        Dict[str, Any]
            Mirror dictionary of FCFFGrowthParameters.
        """
        return {
            "mode": self.MODE,
            "revenue_ttm": st.session_state.get("revenue_ttm"),
            "revenue_growth_rate": st.session_state.get("revenue_growth_rate"),
            "target_fcf_margin": st.session_state.get("target_fcf_margin"),
            "projection_years": st.session_state.get("strategy_years")
        }