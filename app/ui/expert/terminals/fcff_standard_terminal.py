"""
app/ui/expert_terminals/fcff_standard_terminal.py

EXPERT TERMINAL — FCFF TWO-STAGE STANDARD (CONTINUOUS FLOW)
==========================================================
Implementation of the Entity DCF (FCFF) interface.
This terminal constitutes steps 1 and 2 of the analytical "Logical Path".

Architecture: ST-3.1 (Fundamental - DCF)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFFStandardTexts as Texts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class FCFFStandardTerminal(ExpertTerminalBase):
    """
    Expert terminal for Free Cash Flow to the Firm (FCFF) valuation.

    This module guides the analyst in defining the cash flow anchor (Y0)
    and the growth trajectory before proceeding to risk and capital
    structure steps managed by the base class.
    """

    MODE = ValuationMode.FCFF_STANDARD
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration (9 Steps) ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True  # Enabled: becomes Step 9 of the expert tunnel
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Narrative LaTeX Formulas ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders operational inputs (Steps 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Captured parameters: manual_fcf_base, projection_years, fcf_growth_rate.
        """
        prefix = self.MODE.name

        # --- STEP 1: CASH FLOW ANCHOR ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)
        fcf_base = st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BASE,
            key=f"{prefix}_fcf_base"
        )
        st.divider()

        # --- STEP 2: GROWTH PROJECTION ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(label=Texts.INP_GROWTH_G, key_prefix=prefix)

        st.divider()

        return {
            "manual_fcf_base": fcf_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts FCFF-specific data from the session_state.

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
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_fcf_base"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }