"""
app/ui/expert/terminals/fcff_standard_terminal.py

EXPERT TERMINAL — FCFF TWO-STAGE STANDARD (CONTINUOUS FLOW)
==========================================================
Implementation of the Entity DCF (FCFF) interface.
Aligned with FCFFStandardParameters for direct Pydantic injection.

Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFFStandardTexts as Texts
from ..base_terminal import BaseTerminalExpert
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years
)


class FCFFStandardTerminalTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for Free Cash Flow to the Firm (FCFF) valuation.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFF_STANDARD for entity-level DCF valuation.
    """

    MODE = ValuationMethodology.FCFF_STANDARD
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Narrative LaTeX Formulas ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders operational inputs (Steps 1 & 2).
        Keys are aligned with FCFFStandardParameters fields.

        Returns
        -------
        Dict[str, Any]
            Captured parameters: fcf_anchor, projection_years, growth_rate_p1.
        """
        # --- STEP 1: CASH FLOW ANCHOR (Strategy -> fcf_anchor) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)
        fcf_anchor = st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BASE,
            key="fcf_anchor"  # Direct Pydantic Field
        )
        st.divider()

        # --- STEP 2: GROWTH PROJECTION (Strategy -> projection_years / growth_rate_p1) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # Note: widget_projection_years doit être mis à jour pour accepter 'key' direct
            # Pour l'instant on force l'alignement via l'extraction
            n_years = widget_projection_years(default=5, key_prefix="strategy")

        with col2:
            growth_p1 = st.number_input(
                Texts.INP_GROWTH_G,
                value=None,
                format="%.2f",
                help=Texts.HELP_GROWTH_RATE,
                key="growth_rate_p1" # Direct Pydantic Field
            )

        st.divider()

        return {
            "fcf_anchor": fcf_anchor,
            "projection_years": n_years,
            "growth_rate_p1": growth_p1,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts FCFF-specific data for the 'strategy' block.

        Returns
        -------
        Dict[str, Any]
            Dictionnaire miroir de FCFFStandardParameters.
        """
        return {
            "mode": self.MODE,
            "fcf_anchor": st.session_state.get("fcf_anchor"),
            "growth_rate_p1": st.session_state.get("growth_rate_p1"),
            "projection_years": st.session_state.get("strategy_years"), # Aligné sur widget_projection_years
        }