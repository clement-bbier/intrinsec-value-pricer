"""
app/ui/expert/terminals/graham_value_terminal.py

EXPERT TERMINAL — GRAHAM INTRINSIC VALUE (QUANT REVISED)
========================================================
Defensive screening formula (Revised 1974) enhanced with
a stochastic approach for earnings volatility.

Architecture: ST-4.1 (Screening & Probabilistic)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import GrahamTexts as Texts
from ..base_terminal import ExpertTerminalBase

# ==============================================================================
# NORMALIZATION CONSTANT
# ==============================================================================

_PERCENTAGE_DIVISOR = 100.0
"""Divisor for converting percentage inputs to decimals."""


class GrahamValueTerminal(ExpertTerminalBase):
    """
    Expert terminal for Benjamin Graham's intrinsic value formula.

    While the original model is deterministic, this terminal allows for
    sensitivity analysis through the global valuation engine.
    """

    MODE = ValuationMode.GRAHAM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration (Static Adaptation) ---
    SHOW_DISCOUNT_SECTION = False  # No explicit WACC/Ke required
    SHOW_TERMINAL_SECTION = False  # No Gordon/Exit Multiples
    SHOW_BRIDGE_SECTION = False    # Values the share directly

    SHOW_MONTE_CARLO = False
    SHOW_SCENARIOS = False
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = False
    SHOW_SUBMIT_BUTTON = False

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders operational inputs for the Graham model (Steps 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Parameters: manual_fcf_base (EPS), fcf_growth_rate (g),
            corporate_aaa_yield (Y), tax_rate (tau).
        """
        prefix = self.MODE.name

        # --- STEP 1: EARNINGS & GROWTH ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            eps = st.number_input(
                Texts.INP_EPS_NORM,
                value=None,
                format="%.2f",
                help=Texts.HELP_EPS_NORM,
                key=f"{prefix}_eps_norm"
            )

        with col2:
            g_lt = st.number_input(
                Texts.INP_GROWTH_G,
                value=None,
                format="%.3f",
                help=Texts.HELP_GROWTH_LT,
                key=f"{prefix}_growth_lt"
            )

        st.divider()

        # --- STEP 2: MARKET CONDITIONS ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            yield_aaa = st.number_input(
                Texts.INP_YIELD_AAA,
                value=None,
                format="%.3f",
                help=Texts.HELP_YIELD_AAA,
                key=f"{prefix}_yield_aaa"
            )

        with col2:
            tau = st.number_input(
                Texts.INP_TAX,
                value=None,
                format="%.2f",
                help=Texts.HELP_TAX,
                key=f"{prefix}_tax_rate"
            )

        st.caption(Texts.NOTE_GRAHAM)

        return {
            "manual_fcf_base": eps,
            "fcf_growth_rate": g_lt,
            "corporate_aaa_yield": yield_aaa,
            "tax_rate": tau,
            "projection_years": 1
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts Graham input data from streamlit session_state.

        Parameters
        ----------
        key_prefix : str
            Prefix based on the ValuationMode.

        Returns
        -------
        Dict[str, Any]
            Operational data for build_request.

        Note
        ----
        Three rate parameters require normalization:
        - fcf_growth_rate (g): Long-term growth expectation
        - corporate_aaa_yield (Y): Current AAA corporate bond yield
        - tax_rate (tau): Effective corporate tax rate

        EPS remains unchanged (absolute currency value per share).
        """
        # Helper function for percentage normalization
        def normalize(value):
            if value is None:
                return None
            return value / _PERCENTAGE_DIVISOR

        # Extract raw values
        raw_growth = st.session_state.get(f"{key_prefix}_growth_lt")
        raw_yield = st.session_state.get(f"{key_prefix}_yield_aaa")
        raw_tax = st.session_state.get(f"{key_prefix}_tax_rate")

        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_eps_norm"),
            "fcf_growth_rate": normalize(raw_growth),
            "corporate_aaa_yield": normalize(raw_yield),
            "tax_rate": normalize(raw_tax),
            "projection_years": 1
        }