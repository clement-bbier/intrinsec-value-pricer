"""
app/ui/expert/terminals/fcff_normalized_terminal.py

EXPERT TERMINAL — FCFF NORMALIZED (SMOOTHED FLOW)
=================================================
Valuation interface based on smoothed normative flows.
This terminal implements steps 1 and 2 for companies with cyclical
but predictable cash flows.

Architecture: ST-3.2 (Enterprise Value)
Style: Numpy docstrings

IMPORTANT: Normalization is handled by Pydantic validators in DCFParameters.
           This terminal passes raw values from the UI to the model layer.
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


class FCFFNormalizedTerminal(ExpertTerminalBase):
    """
    Expert terminal for Normalized Free Cash Flow to the Firm (FCFF).

    This model uses a 'smoothed' or normative cash flow anchor to avoid
    valuation distortions caused by temporary cyclical peaks or troughs.

    Attributes
    ----------
    MODE : ValuationMode
        Set to FCFF_NORMALIZED for mid-cycle valuation.

    Notes
    -----
    Percentage inputs are passed as-is to the Pydantic model layer,
    which handles normalization via field validators.
    """

    MODE = ValuationMode.FCFF_NORMALIZED
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

        Notes
        -----
        Values are passed directly to Pydantic without normalization.
        The GrowthParameters model handles percentage-to-decimal
        conversion via the _decimal_guard field validator.

        - FCF base: Absolute currency value (no normalization)
        - Growth rate: Passed as-is; Pydantic normalizes if > 1.0
        """
        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_fcf_base"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }