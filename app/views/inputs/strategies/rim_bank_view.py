"""
app/views/inputs/strategies/rim_bank_view.py

EXPERT VIEW — RESIDUAL INCOME MODEL (RIM)
=========================================
Dedicated interface for valuing financial institutions and banks.
Role: Renders inputs for Book Value Anchor, Growth, and Persistence (Omega).

Pattern: Strategy View (MVC)
Architecture: V16 (Stateless Rendering)
Style: Numpy docstrings
"""

import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import RIMTexts as Texts
from src.i18n import SharedTexts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import (
    widget_projection_years
)


class RIMBankView(BaseStrategyView):
    """
    Expert view for the Residual Income Model (Ohlson Model).

    This terminal is specifically designed for valuing financial institutions
    where traditional cash flow models are less effective, focusing instead
    on Book Value and Residual Income persistence (ROE vs Ke).

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
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """
        Renders specific inputs for the RIM model.
        Writes directly to st.session_state for the Controller.
        """
        prefix = self.MODE.name  # "RIM"

        # --- STEP 1: BOOK VALUE ANCHOR (Strategy -> book_value_anchor) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        st.number_input(
            Texts.INP_BV_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BV_BASE,
            key=f"{prefix}_bv_anchor"  # Maps to RIMParameters.book_value_anchor
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
        # Omega determines how quickly ROE reverts to Cost of Equity.
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