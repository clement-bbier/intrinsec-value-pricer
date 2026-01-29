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


class GrahamValueTerminal(ExpertTerminalBase):
    """
    Expert terminal for Benjamin Graham's intrinsic value formula.

    While the original model is deterministic, this terminal allows for
    sensitivity analysis through the global valuation engine.

    Attributes
    ----------
    MODE : ValuationMode
        Set to GRAHAM for defensive value investing.

    Notes
    -----
    This terminal disables most optional features (Monte Carlo, Scenarios,
    SOTP, Peers) as Graham's formula is self-contained and does not
    require complex discount rate or terminal value mechanics.

    Percentage inputs are passed as-is to the Pydantic model layer,
    which handles normalization via field validators.
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
    SHOW_BACKTEST = False
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
                format="%.2f",
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
                format="%.2f",
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

        Notes
        -----
        Values are passed directly to Pydantic without normalization.
        The CoreRateParameters model handles percentage-to-decimal
        conversion via the _decimal_guard field validator.

        - EPS: Absolute currency value (no normalization)
        - Growth rate: Passed as-is; Pydantic normalizes if > 1.0
        - AAA Yield: Passed as-is; Pydantic normalizes if > 1.0
        - Tax rate: Passed as-is; Pydantic normalizes if > 1.0
        """
        return {
            # EPS: Absolute value, no normalization needed
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_eps_norm"),
            # Rates: Passed raw, Pydantic handles normalization
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_lt"),
            "corporate_aaa_yield": st.session_state.get(f"{key_prefix}_yield_aaa"),
            "tax_rate": st.session_state.get(f"{key_prefix}_tax_rate"),
            # Fixed projection for Graham model
            "projection_years": 1
        }