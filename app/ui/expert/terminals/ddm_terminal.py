"""
app/ui/expert/terminals/ddm_terminal.py

EXPERT TERMINAL — DIVIDEND DISCOUNT MODEL (DDM)
===============================================
Valuation interface based on discounted future dividends.
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import DDMTexts as Texts
from src.i18n import SharedTexts
from ..base_terminal import BaseTerminalExpert
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class DDMTerminalTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for the Dividend Discount Model.
    """

    MODE = ValuationMethodology.DDM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Narrative LaTeX Formulas ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{D_n(1+g_n)}{k_e - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the DDM model (Steps 1 & 2).
        """
        prefix = self.MODE.name  # "DDM"

        # --- STEP 1: DIVIDEND CASH FLOWS ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)

        d0_base = st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.2f",
            help=Texts.HELP_DIVIDEND_BASE,
            key=f"{prefix}_dividend_base"  # Clé: DDM_dividend_base
        )

        st.divider()

        # --- STEP 2: DIVIDEND DYNAMICS ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # Ce widget génère la clé : {prefix}_years
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            # Ce widget génère la clé : {prefix}_growth_rate
            g_rate = widget_growth_rate(
                label=SharedTexts.INP_GROWTH_G,
                key_prefix=prefix
            )

        if Texts.NOTE_DDM_SGR:
            st.caption(Texts.NOTE_DDM_SGR)

        st.divider()

        return {
            "dividend_per_share": d0_base,
            "dividend_growth_rate": g_rate,
            "projection_years": n_years
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts DDM data from streamlit session_state with precise keys.
        """
        # On s'assure que les clés de récupération correspondent
        # exactement à celles définies dans render_model_inputs et shared_widgets.
        return {
            "dividend_per_share": st.session_state.get(f"{key_prefix}_dividend_base"),
            "dividend_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }