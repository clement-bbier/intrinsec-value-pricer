"""
app/ui/expert/terminals/fcff_normalized_terminal.py

EXPERT TERMINAL — FCFF NORMALIZED (SMOOTHED FLOW)
=================================================
Valuation interface based on smoothed normative flows.
This terminal implements steps 1 and 2 for companies with cyclical
but predictable cash flows.

Architecture: ST-3.2 (Enterprise Value)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFFNormalizedTexts as Texts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)

# ==============================================================================
# NORMALIZATION CONSTANT
# ==============================================================================

_PERCENTAGE_DIVISOR = 100.0
"""Divisor for converting percentage inputs to decimals."""


class FCFFNormalizedTerminal(ExpertTerminalBase):
    """
    Expert terminal for Normalized Free Cash Flow to the Firm (FCFF).

    This model uses a 'smoothed' or normative cash flow anchor to avoid
    valuation distortions caused by temporary cyclical peaks or troughs.
    """

    MODE = ValuationMode.FCFF_NORMALIZED
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    SHOW_SOTP = True

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Renders specific inputs for the Normalized FCFF model (Steps 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Parameters: manual_fcf_base, projection_years, fcf_growth_rate.
        """
        prefix = self.MODE.name

        # --- STEP 1: NORMATIVE FLOW ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        fcf_base = st.number_input(
            Texts.INP_BASE, value=None, format="%.0f",
            help=Texts.HELP_BASE, key=f"{prefix}_fcf_base"
        )
        st.divider()

        # --- STEP 2: GROWTH DYNAMICS ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(key_prefix=prefix)

        st.divider()
        return {
            "manual_fcf_base": fcf_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts Normalized FCFF data from the session_state.

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
        """
        # Extract raw values
        raw_growth_rate = st.session_state.get(f"{key_prefix}_growth_rate")

        # Normalize growth rate from percentage to decimal
        normalized_growth_rate = None
        if raw_growth_rate is not None:
            normalized_growth_rate = raw_growth_rate / _PERCENTAGE_DIVISOR

        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_fcf_base"),
            "fcf_growth_rate": normalized_growth_rate,
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }