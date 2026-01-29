"""
app/ui/expert/terminals/fcfe_terminal.py

EXPERT TERMINAL — FREE CASH FLOW TO EQUITY (FCFE)
=================================================
Implementation of the direct equity valuation interface.
This terminal constitutes steps 1 and 2 of the "Logical Path" for the FCFE model.

Architecture: ST-3.2 (Direct Equity)
Style: Numpy docstrings

IMPORTANT: Normalization is handled by Pydantic validators in DCFParameters.
           This terminal passes raw values from the UI to the model layer.
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFETexts as Texts
from src.i18n import SharedTexts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class FCFETerminal(ExpertTerminalBase):
    """
    Expert terminal for shareholder cash flow valuation.

    The FCFE model values equity directly by discounting residual
    cash flows after debt service at the cost of equity (Ke).

    Attributes
    ----------
    MODE : ValuationMode
        Set to FCFE for direct equity valuation.

    Notes
    -----
    Percentage inputs are passed as-is to the Pydantic model layer,
    which handles normalization via field validators.
    """

    MODE = ValuationMode.FCFE
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
        Renders specific inputs for the FCFE model (Steps 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Parameters: manual_fcf_base, manual_net_borrowing,
            projection_years, fcf_growth_rate.
        """
        prefix = self.MODE.name

        # --- STEP 1: SHAREHOLDER ANCHOR ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            fcfe_base = st.number_input(
                Texts.INP_BASE,
                value=None,
                format="%.0f",
                help=Texts.HELP_FCFE_BASE,
                key=f"{prefix}_fcf_base"
            )

        with col2:
            net_borrowing = st.number_input(
                Texts.INP_NET_BORROWING,
                value=None,
                format="%.0f",
                help=Texts.HELP_NET_BORROWING,
                key=f"{prefix}_net_borrowing"
            )

        st.divider()

        # --- STEP 2: PROJECTION HORIZON ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(label=SharedTexts.INP_GROWTH_G, key_prefix=prefix)

        st.divider()

        return {
            "manual_fcf_base": fcfe_base,
            "manual_net_borrowing": net_borrowing,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extracts FCFE data from the session_state.

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
        - Net borrowing: Absolute currency value (no normalization)
        - Growth rate: Passed as-is; Pydantic normalizes if > 1.0
        """
        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_fcf_base"),
            "manual_net_borrowing": st.session_state.get(f"{key_prefix}_net_borrowing"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }