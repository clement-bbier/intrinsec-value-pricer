"""
app/ui/expert/terminals/rim_bank_terminal.py

EXPERT TERMINAL — RESIDUAL INCOME MODEL (RIM)
=============================================
Dedicated interface for valuing financial institutions and banks.
Aligned with RIMParameters for Pydantic injection.

Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import RIMTexts as Texts
from src.i18n import SharedTexts
from ..base_terminal import BaseTerminalExpert
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years
)

class RIMBankTerminalTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for the Residual Income Model (Ohlson Model).

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to RIM for bank and financial institution valuation.
    """

    MODE = ValuationMethodology.RIM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the RIM model.
        Keys are aligned with RIMParameters fields.

        Returns
        -------
        Dict[str, Any]
            Captured parameters for the strategy block.
        """
        # --- STEP 1: BALANCE SHEET ANCHOR (Strategy -> book_value_anchor / net_income_norm) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            bv_anchor = st.number_input(
                Texts.INP_BV_INITIAL,
                value=None,
                format="%.0f",
                help=Texts.HELP_BV_INITIAL,
                key="book_value_anchor"  # Direct Pydantic Field
            )

        with col2:
            ni_norm = st.number_input(
                Texts.INP_NI_TTM,
                value=None,
                format="%.0f",
                help=Texts.HELP_NI_TTM,
                key="net_income_norm"  # Direct Pydantic Field
            )

        st.divider()

        # --- STEP 2: RESIDUAL INCOME & PERSISTENCE (Strategy -> growth_rate / persistence_factor) ---
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

        # Persistence Factor (Omega) - Intégré à la stratégie RIM
        persistence = st.number_input(
            SharedTexts.INP_OMEGA,
            min_value=0.0,
            max_value=1.0,
            value=None,
            format="%.2f",
            help=SharedTexts.HELP_OMEGA,
            key="persistence_factor"  # Direct Pydantic Field
        )

        st.divider()

        return {
            "book_value_anchor": bv_anchor,
            "net_income_norm": ni_norm,
            "projection_years": n_years,
            "growth_rate": g_rate,
            "persistence_factor": persistence
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts RIM-specific data for the 'strategy' block.

        Returns
        -------
        Dict[str, Any]
            Dictionnaire miroir de RIMParameters.
        """
        return {
            "mode": self.MODE,
            "book_value_anchor": st.session_state.get("book_value_anchor"),
            "net_income_norm": st.session_state.get("net_income_norm"),
            "growth_rate": st.session_state.get("growth_rate"),
            "persistence_factor": st.session_state.get("persistence_factor"),
            "projection_years": st.session_state.get("strategy_years")
        }