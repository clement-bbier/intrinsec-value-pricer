"""
app/ui/expert/terminals/graham_value_terminal.py

EXPERT TERMINAL — GRAHAM INTRINSIC VALUE (QUANT REVISED)
========================================================
Defensive screening formula (Revised 1974) enhanced with
a stochastic approach for earnings volatility.
Data mapping is automated via GrahamParameters and UIBinder.

Pattern: Strategy (Concrete Implementation)
Architecture: V16 (Metadata-Driven Extraction)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from app.adapters.ui_binder import UIBinder
from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import GrahamTexts as Texts
from src.models.parameters.strategies import GrahamParameters
from app.ui.expert.base_terminal import BaseTerminalExpert


class GrahamValueTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for Benjamin Graham's intrinsic value formula.

    This terminal implements the revised 1974 formula, focusing on normalized
    earnings and long-term growth estimates for defensive screening.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to GRAHAM for defensive value investing.
    DISPLAY_NAME : str
        Human-readable name from i18n.
    DESCRIPTION : str
        Brief description from i18n.
    """

    MODE = ValuationMethodology.GRAHAM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    # Standard discount and terminal sections are hidden as Graham uses fixed rates.
    SHOW_DISCOUNT_SECTION = False
    SHOW_TERMINAL_SECTION = False
    SHOW_BRIDGE_SECTION = False

    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = False
    SHOW_BACKTEST = True
    SHOW_SUBMIT_BUTTON = False

    def render_model_inputs(self) -> None:
        """
        Renders operational inputs for the Graham model.

        Widget keys are mapped to UIKey suffixes defined in
        GrahamParameters and FinancialRatesParameters to enable
        automated extraction.
        """
        prefix = self.MODE.name

        # --- STEP 1: EARNINGS & GROWTH (Strategy Block -> GrahamParameters) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                Texts.INP_EPS_NORM,
                value=None,
                format="%.2f",
                help=Texts.HELP_EPS_NORM,
                key=f"{prefix}_eps_normalized"  # Maps to GrahamParameters.eps_normalized
            )

        with col2:
            st.number_input(
                Texts.INP_GROWTH_G,
                value=None,
                format="%.2f",
                help=Texts.HELP_GROWTH_LT,
                key=f"{prefix}_growth_estimate"  # Maps to GrahamParameters.growth_estimate
            )

        st.divider()

        # --- STEP 2: MARKET CONDITIONS (Common Rates Block -> FinancialRatesParameters) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                Texts.INP_YIELD_AAA,
                value=None,
                format="%.2f",
                help=Texts.HELP_YIELD_AAA,
                key=f"{prefix}_yield_aaa"  # Maps to FinancialRatesParameters.corporate_aaa_yield
            )

        with col2:
            st.number_input(
                Texts.INP_TAX,
                value=None,
                format="%.2f",
                help=Texts.HELP_TAX,
                key=f"{prefix}_tax"  # Maps to FinancialRatesParameters.tax_rate
            )

        st.caption(Texts.NOTE_GRAHAM)

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Automated extraction of Graham-specific strategy data.

        Parameters
        ----------
        key_prefix : str
            The session state prefix (ValuationMode.name).

        Returns
        -------
        Dict[str, Any]
            Raw UI values mapped to GrahamParameters fields via UIBinder.
        """
        return UIBinder.pull(GrahamParameters, prefix=key_prefix)