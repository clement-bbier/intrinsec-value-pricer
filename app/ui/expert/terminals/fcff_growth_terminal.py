"""
app/ui/expert_terminals/fcff_growth_terminal.py

EXPERT TERMINAL — FCFF REVENUE-DRIVEN (GROWTH & MARGIN)
======================================================
Valuation interface based on revenue growth and margin convergence.
This model calculates FCFF by projecting top-line revenue and target FCF margins.

Architecture: ST-3.2 (Enterprise Value)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st
from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFFGrowthTexts as Texts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import widget_projection_years

class FCFFGrowthTerminal(ExpertTerminalBase):
    """
    Expert terminal for the Revenue-Driven FCFF model.

    This approach is ideal for growth companies where margins are expected
    to converge toward an industry target over a projection horizon.
    """

    MODE = ValuationMode.FCFF_GROWTH
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the Revenue-Driven FCFF model (Steps 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Parameters: manual_fcf_base (revenue), projection_years,
            fcf_growth_rate (rev growth), target_fcf_margin.
        """
        prefix = self.MODE.name

        # --- STEP 1: REVENUE BASE ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        rev_base = st.number_input(
            Texts.INP_BASE, value=None, format="%.0f",
            help=Texts.HELP_REV_TTM, key=f"{prefix}_rev_base"
        )
        st.divider()

        # --- STEP 2: MARGIN CONVERGENCE ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        col1, col2, col3 = st.columns(3)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rev = st.number_input(
                Texts.INP_REV_GROWTH, value=None, format="%.3f",
                help=Texts.HELP_REV_GROWTH, key=f"{prefix}_rev_growth"
            )
        with col3:
            m_target = st.number_input(
                Texts.INP_MARGIN_TARGET, value=None, format="%.2f",
                help=Texts.HELP_MARGIN_TARGET, key=f"{prefix}_margin_target"
            )

        st.divider()
        return {
            "manual_fcf_base": rev_base, "projection_years": n_years,
            "fcf_growth_rate": g_rev, "target_fcf_margin": m_target
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts FCFF Growth data from the session_state.

        Parameters
        ----------
        key_prefix : str
            Prefix based on the ValuationMode.

        Returns
        -------
        Dict[str, Any]
            Operational data for build_request.
        """
        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_rev_base"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_rev_growth"),
            "target_fcf_margin": st.session_state.get(f"{key_prefix}_margin_target"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }