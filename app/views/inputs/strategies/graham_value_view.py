"""
app/views/inputs/strategies/graham_value_view.py

EXPERT VIEW — GRAHAM INTRINSIC VALUE (QUANT REVISED)
====================================================
Defensive screening formula (Revised 1974).
Role: Renders inputs for EPS, Growth, and Bond Yields.

Pattern: Strategy View (MVC)
Architecture: V16 (Stateless Rendering)
Style: Numpy docstrings
"""

import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import GrahamTexts as Texts
from app.views.inputs.base_strategy import BaseStrategyView


class GrahamValueView(BaseStrategyView):
    """
    Expert view for Benjamin Graham's intrinsic value formula.

    This terminal implements the revised 1974 formula, focusing on normalized
    earnings and long-term growth estimates for defensive screening.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to GRAHAM for defensive value investing.
    """

    MODE = ValuationMethodology.GRAHAM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_DISCOUNT_SECTION = False  # Graham uses specific Yields, not WACC
    SHOW_TERMINAL_SECTION = False  # The formula is self-contained
    SHOW_BRIDGE_SECTION = False    # Graham gives Price per Share directly
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = False
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = False

    def render_model_inputs(self) -> None:
        """
        Renders specific inputs for the Graham Formula.

        Note:
        - EPS & Growth map to Strategy Parameters (Prefix: GRAHAM_).
        - Yield & Tax map to Common Parameters (No Prefix, Global Keys).
        """
        prefix = self.MODE.name

        # --- STEP 1: EARNINGS POWER (Strategy -> eps_normalized / growth_estimate) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                Texts.INP_EPS,
                value=None,
                format="%.2f",
                help=Texts.HELP_EPS,
                key=f"{prefix}_eps_normalized"  # Maps to GrahamParameters.eps_normalized
            )

        with col2:
            st.number_input(
                Texts.INP_GROWTH,
                value=None,
                format="%.2f",
                help=Texts.HELP_GROWTH_LT,
                key=f"{prefix}_growth_estimate"  # Maps to GrahamParameters.growth_estimate
            )

        st.divider()

        # --- STEP 2: MARKET CONDITIONS (Common Rates Block) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # Maps to FinancialRatesParameters.corporate_aaa_yield (Global Key)
            st.number_input(
                Texts.INP_YIELD_AAA,
                value=None,
                format="%.2f",
                help=Texts.HELP_YIELD_AAA,
                key="yield_aaa"  # Note: No prefix, maps to Common Params directly
            )

        with col2:
            # Maps to FinancialRatesParameters.tax_rate (Global Key)
            st.number_input(
                Texts.INP_TAX,
                value=None,
                format="%.2f",
                help=Texts.HELP_TAX,
                key="tax_rate"  # Note: No prefix, maps to Common Params directly
            )

        st.caption(Texts.NOTE_GRAHAM)
        st.divider()