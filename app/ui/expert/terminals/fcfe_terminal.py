"""
app/ui/expert/terminals/fcfe_terminal.py

EXPERT TERMINAL — FREE CASH FLOW TO EQUITY (FCFE)
=================================================
Implementation of the direct equity valuation interface.
Aligned with FCFEParameters for direct Pydantic injection.

Architecture: ST-3.2 (Direct Equity)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFETexts as Texts
from src.i18n import SharedTexts
from ..base_terminal import BaseTerminalExpert
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years
)


class FCFETerminalTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for shareholder cash flow valuation (FCFE).

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFE for direct equity valuation.
    """

    MODE = ValuationMethodology.FCFE
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Narrative LaTeX Formulas ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCFE_n(1+g_n)}{k_e - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the FCFE model.
        Keys are aligned with FCFEParameters fields.

        Returns
        -------
        Dict[str, Any]
            Full set of captured parameters for strategy extraction.
        """
        # --- STEP 1: SHAREHOLDER ANCHOR (Strategy -> fcfe_anchor / net_borrowing_delta) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            fcfe_anchor = st.number_input(
                Texts.INP_BASE,
                value=None,
                format="%.0f",
                help=Texts.HELP_FCFE_BASE,
                key="fcfe_anchor"  # Direct Pydantic Field
            )

        with col2:
            net_borrowing = st.number_input(
                Texts.INP_NET_BORROWING,
                value=None,
                format="%.0f",
                help=Texts.HELP_NET_BORROWING,
                key="net_borrowing_delta"  # Direct Pydantic Field
            )

        st.divider()

        # --- STEP 2: PROJECTION HORIZON (Strategy -> projection_years / growth_rate) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # Aligné via le préfixe 'strategy' pour donner 'strategy_years'
            n_years = widget_projection_years(default=5, key_prefix="strategy")
        with col2:
            g_rate = st.number_input(
                SharedTexts.INP_GROWTH_G,
                value=None,
                format="%.2f",
                help=SharedTexts.HELP_GROWTH_RATE,
                key="growth_rate"  # Direct Pydantic Field
            )

        st.divider()

        return {
            "fcfe_anchor": fcfe_anchor,
            "net_borrowing_delta": net_borrowing,
            "projection_years": n_years,
            "growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts FCFE-specific data for the 'strategy' block.

        Returns
        -------
        Dict[str, Any]
            Mirror dictionary of FCFEParameters.
        """
        return {
            "mode": self.MODE,
            "fcfe_anchor": st.session_state.get("fcfe_anchor"),
            "net_borrowing_delta": st.session_state.get("net_borrowing_delta"),
            "growth_rate": st.session_state.get("growth_rate"),
            "projection_years": st.session_state.get("strategy_years")
        }