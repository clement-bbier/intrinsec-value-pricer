"""
app/ui/expert/terminals/fcff_normalized_terminal.py

EXPERT TERMINAL — FCFF NORMALIZED (SMOOTHED FLOW)
=================================================
Valuation interface based on smoothed normative flows.
Aligned with FCFFNormalizedParameters for direct Pydantic injection.

Architecture: ST-3.2 (Enterprise Value)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFFNormalizedTexts as Texts
from ..base_terminal import BaseTerminalExpert
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years
)


class FCFFNormalizedTerminalTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for Normalized Free Cash Flow to the Firm (FCFF).

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFF_NORMALIZED for mid-cycle valuation.
    """

    MODE = ValuationMethodology.FCFF_NORMALIZED
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Narrative LaTeX Formulas ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCF_{norm}(1+g_n)}{WACC - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the Normalized FCFF model.
        Keys are aligned with FCFFNormalizedParameters fields.

        Returns
        -------
        Dict[str, Any]
            Captured parameters for the strategy block.
        """
        # --- STEP 1: NORMATIVE FLOW (Strategy -> fcf_norm) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        fcf_norm = st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BASE,
            key="fcf_norm" # Direct Pydantic Field
        )
        st.divider()

        # --- STEP 2: GROWTH DYNAMICS (Strategy -> projection_years / cycle_growth_rate) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        col1, col2 = st.columns(2)
        with col1:
            # Aligné via le préfixe 'strategy' pour donner 'strategy_years'
            n_years = widget_projection_years(default=5, key_prefix="strategy")
        with col2:
            cycle_g = st.number_input(
                Texts.LBL_GROWTH_G, # Ou label spécifique i18n
                value=None,
                format="%.2f",
                key="cycle_growth_rate" # Direct Pydantic Field
            )

        st.divider()
        return {
            "fcf_norm": fcf_norm,
            "projection_years": n_years,
            "cycle_growth_rate": cycle_g
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts Normalized FCFF data for the 'strategy' block.

        Returns
        -------
        Dict[str, Any]
            Dictionnaire miroir de FCFFNormalizedParameters.
        """
        return {
            "mode": self.MODE,
            "fcf_norm": st.session_state.get("fcf_norm"),
            "cycle_growth_rate": st.session_state.get("cycle_growth_rate"),
            "projection_years": st.session_state.get("strategy_years")
        }