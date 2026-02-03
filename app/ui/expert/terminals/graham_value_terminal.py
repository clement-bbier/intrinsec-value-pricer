"""
app/ui/expert/terminals/graham_value_terminal.py

EXPERT TERMINAL — GRAHAM INTRINSIC VALUE (QUANT REVISED)
========================================================
Defensive screening formula (Revised 1974) enhanced with
a stochastic approach for earnings volatility.
Aligned with GrahamParameters (Strategy) and FinancialRatesParameters (Common).

Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import GrahamTexts as Texts
from ..base_terminal import BaseTerminalExpert


class GrahamValueTerminalTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for Benjamin Graham's intrinsic value formula.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to GRAHAM for defensive value investing.
    """

    MODE = ValuationMethodology.GRAHAM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    # La section Discount standard est masquée car Graham intègre ses propres taux.
    SHOW_DISCOUNT_SECTION = False
    SHOW_TERMINAL_SECTION = False
    SHOW_BRIDGE_SECTION = False

    SHOW_MONTE_CARLO = False
    SHOW_SCENARIOS = False
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = False
    SHOW_BACKTEST = False
    SHOW_SUBMIT_BUTTON = False

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders operational inputs for the Graham model.
        All keys are aligned with Pydantic schemas (GrahamParameters & FinancialRatesParameters).

        Returns
        -------
        Dict[str, Any]
            Full set of captured parameters for session storage.
        """
        # --- STEP 1: EARNINGS & GROWTH (Strategy Block) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            eps = st.number_input(
                Texts.INP_EPS_NORM,
                value=None,
                format="%.2f",
                help=Texts.HELP_EPS_NORM,
                key="eps_normalized"  # Strategy: GrahamParameters
            )

        with col2:
            g_estimate = st.number_input(
                Texts.INP_GROWTH_G,
                value=None,
                format="%.2f",
                help=Texts.HELP_GROWTH_LT,
                key="growth_estimate"  # Strategy: GrahamParameters
            )

        st.divider()

        # --- STEP 2: MARKET CONDITIONS (Common Rates Block) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # Saisie manuelle du taux AAA pour le bloc Common.
            yield_aaa = st.number_input(
                Texts.INP_YIELD_AAA,
                value=None,
                format="%.2f",
                help=Texts.HELP_YIELD_AAA,
                key="corporate_aaa_yield"  # Common: FinancialRatesParameters
            )

        with col2:
            # Saisie manuelle du taux d'imposition pour le bloc Common.
            tau = st.number_input(
                Texts.INP_TAX,
                value=None,
                format="%.2f",
                help=Texts.HELP_TAX,
                key="tax_rate"  # Common: FinancialRatesParameters
            )

        st.caption(Texts.NOTE_GRAHAM)

        # Correction : Retourne l'intégralité des champs saisis pour build_request.
        return {
            "eps_normalized": eps,
            "growth_estimate": g_estimate,
            "corporate_aaa_yield": yield_aaa,
            "tax_rate": tau
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts only Graham-specific data for the 'strategy' dicationary.

        Returns
        -------
        Dict[str, Any]
            Mirror dictionary of GrahamParameters.
        """
        return {
            "mode": self.MODE,
            "eps_normalized": st.session_state.get("eps_normalized"),
            "growth_estimate": st.session_state.get("growth_estimate"),
        }