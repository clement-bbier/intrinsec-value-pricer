"""
app/views/inputs/strategies/fcfe_view.py

EXPERT VIEW — FREE CASH FLOW TO EQUITY (FCFE)
=============================================
Implementation of the direct equity valuation interface.
Role: Renders inputs for FCFE Anchor and Net Borrowing.

Pattern: Strategy View (MVC)
Architecture: V16 (Stateless Rendering)
Style: Numpy docstrings
"""

import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFETexts as Texts
from src.i18n import SharedTexts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import (
    widget_projection_years
)


class FCFEView(BaseStrategyView):
    """
    Expert view for shareholder cash flow valuation (FCFE).

    The FCFE model values equity directly by discounting residual
    cash flows after debt service at the cost of equity (Ke).

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFE for direct equity valuation.
    """

    MODE = ValuationMethodology.FCFE
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False  # Usually irrelevant for specific equity flows
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """
        Renders operational inputs for the FCFE model.
        Writes directly to st.session_state for the Controller to pick up.
        """
        prefix = self.MODE.name

        # --- STEP 1: SHAREHOLDER ANCHOR (Strategy -> fcfe_anchor / net_borrowing_delta) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                Texts.INP_BASE,
                value=None,
                format="%.0f",
                help=Texts.HELP_FCFE_BASE,
                key=f"{prefix}_fcfe_anchor"  # Maps to FCFEParameters.fcfe_anchor
            )

        with col2:
            st.number_input(
                Texts.INP_NET_BORROWING,
                value=None,
                format="%.0f",
                help=Texts.HELP_NET_BORROWING,
                key=f"{prefix}_net_borrowing_delta"  # Maps to FCFEParameters.net_borrowing_delta
            )

        st.divider()

        # --- STEP 2: PROJECTION HORIZON (Strategy -> projection_years / growth_rate) ---
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
                key=f"{prefix}_growth_rate"  # Maps to FCFEParameters.growth_rate
            )

        st.divider()