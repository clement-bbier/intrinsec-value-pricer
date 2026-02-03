"""
app/ui/expert/terminals/rim_bank_terminal.py

EXPERT TERMINAL — RESIDUAL INCOME MODEL (RIM)
=============================================
Dedicated interface for valuing financial institutions and banks.
Data mapping is automated via RIMParameters and UIBinder.

Pattern: Strategy (Concrete Implementation)
Architecture: V16 (Metadata-Driven Extraction)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from app.adapters.ui_binder import UIBinder
from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import RIMTexts as Texts
from src.i18n import SharedTexts
from src.models.parameters.strategies import RIMParameters
from ..base_terminal import BaseTerminalExpert
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years
)


class RIMBankTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for the Residual Income Model (Ohlson Model).

    This terminal is specifically designed for valuing financial institutions
    where traditional cash flow models are less effective, focusing instead
    on book value and residual income persistence.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to RIM for bank and financial institution valuation.
    DISPLAY_NAME : str
        Human-readable name from i18n.
    DESCRIPTION : str
        Brief description from i18n.
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

    def render_model_inputs(self) -> None:
        """
        Renders operational inputs for the RIM model.

        Widget keys are mapped to UIKey suffixes defined in
        RIMParameters to enable automated extraction.
        """
        prefix = self.MODE.name

        # --- STEP 1: BALANCE SHEET ANCHOR (Strategy -> bv_anchor / ni_norm) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                Texts.INP_BV_INITIAL,
                value=None,
                format="%.0f",
                help=Texts.HELP_BV_INITIAL,
                key=f"{prefix}_bv_anchor"  # Maps to RIMParameters.book_value_anchor
            )

        with col2:
            st.number_input(
                Texts.INP_NI_TTM,
                value=None,
                format="%.0f",
                help=Texts.HELP_NI_TTM,
                key=f"{prefix}_ni_norm"  # Maps to RIMParameters.net_income_norm
            )

        st.divider()

        # --- STEP 2: PROJECTION & PERSISTENCE (Strategy -> growth_rate / omega) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # key_prefix produces {prefix}_years suffix
            widget_projection_years(default=5, key_prefix=prefix)

        with col2:
            st.number_input(
                SharedTexts.INP_GROWTH_G,
                value=None,
                format="%.2f",
                help=SharedTexts.HELP_GROWTH_RATE,
                key=f"{prefix}_growth_rate"  # Maps to RIMParameters.growth_rate
            )

        # Persistence Factor (Omega) - Specific to RIM Strategy
        st.number_input(
            SharedTexts.INP_OMEGA,
            min_value=0.0,
            max_value=1.0,
            value=None,
            format="%.2f",
            help=SharedTexts.HELP_OMEGA,
            key=f"{prefix}_omega"  # Maps to RIMParameters.persistence_factor
        )

        st.divider()

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Automated extraction of RIM-specific strategy data.

        Parameters
        ----------
        key_prefix : str
            The session state prefix (ValuationMode.name).

        Returns
        -------
        Dict[str, Any]
            Raw UI values mapped to RIMParameters fields via UIBinder.
        """
        return UIBinder.pull(RIMParameters, prefix=key_prefix)