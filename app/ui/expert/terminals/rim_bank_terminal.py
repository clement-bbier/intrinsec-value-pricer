"""
app/ui/expert/terminals/rim_bank_terminal.py

EXPERT TERMINAL — RESIDUAL INCOME MODEL (RIM)
==============================================
Dedicated interface for valuing financial institutions and banks.
The model relies on Book Value and the persistence of Residual Income.

Architecture: ST-3.2 (Direct Equity)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import RIMTexts as Texts
from src.i18n import SharedTexts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate
)

# ==============================================================================
# NORMALIZATION CONSTANT
# ==============================================================================

_PERCENTAGE_DIVISOR = 100.0
"""Divisor for converting percentage inputs to decimals."""


class RIMBankTerminal(ExpertTerminalBase):
    """
    Expert terminal for the Residual Income Model (Ohlson Model).

    This model values a firm as the sum of its current book value
    and the present value of future abnormal profits (Residual Income).
    """

    MODE = ValuationMode.RIM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # RIM integrates its own exit logic within Step 2
    SHOW_TERMINAL_SECTION = False

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the RIM model (Steps 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Parameters: manual_book_value, manual_fcf_base (NI),
            projection_years, fcf_growth_rate, exit_multiple_value (omega).
        """
        prefix = self.MODE.name

        # --- STEP 1: BALANCE SHEET ANCHOR ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            bv_initial = st.number_input(
                Texts.INP_BV_INITIAL,
                value=None,
                format="%.0f",
                help=Texts.HELP_BV_INITIAL,
                key=f"{prefix}_bv_initial"
            )

        with col2:
            ni_base = st.number_input(
                Texts.INP_NI_TTM,
                value=None,
                format="%.0f",
                help=Texts.HELP_NI_TTM,
                key=f"{prefix}_ni_ttm"
            )

        st.divider()

        # --- STEP 2: RESIDUAL INCOME & PERSISTENCE ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(label=SharedTexts.INP_GROWTH_G, key_prefix=prefix)

        st.divider()

        return {
            "manual_book_value": bv_initial,
            "manual_fcf_base": ni_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts RIM data from the session_state.

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
        Growth rate is normalized from percentage (e.g., 5) to decimal (0.05).
        Book value, Net Income, and Omega (persistence factor) remain unchanged:
        - Book value and NI are absolute currency values
        - Omega is already a persistence coefficient between 0 and 1
        """
        # Extract raw values
        raw_growth_rate = st.session_state.get(f"{key_prefix}_growth_rate")

        # Normalize growth rate from percentage to decimal
        normalized_growth_rate = None
        if raw_growth_rate is not None:
            normalized_growth_rate = raw_growth_rate / _PERCENTAGE_DIVISOR

        return {
            "manual_book_value": st.session_state.get(f"{key_prefix}_bv_initial"),
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_ni_ttm"),
            "fcf_growth_rate": normalized_growth_rate,
            "projection_years": st.session_state.get(f"{key_prefix}_years"),
            # Omega is NOT normalized - it's already a coefficient [0, 1]
            "exit_multiple_value": st.session_state.get(f"{key_prefix}_omega")
        }