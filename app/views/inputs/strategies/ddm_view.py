"""
app/views/inputs/strategies/ddm_view.py

EXPERT VIEW — DIVIDEND DISCOUNT MODEL (DDM)
===========================================
Valuation interface based on discounted future dividends.
Role: Renders inputs for Dividend Base and Growth Trajectory.

Pattern: Strategy View (MVC)
Architecture: V16 (Stateless Rendering)
Style: Numpy docstrings
"""

import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import DDMTexts as Texts
from src.i18n import SharedTexts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class DDMTerminalExpert(BaseStrategyView):
    """
    Expert view for the Dividend Discount Model (DDM).

    This interface focuses on capturing the dividend base (D0) and
    the long-term growth trajectory for income-seeking investors.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to DDM for dividend-based valuation.
    """

    MODE = ValuationMethodology.DDM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False  # Irrelevant for pure dividend models
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """
        Renders specific inputs for the DDM model (Steps 1 & 2).
        Writes directly to st.session_state for the Controller to pick up.
        """
        prefix = self.MODE.name  # "DDM"

        # --- STEP 1: DIVIDEND CASH FLOWS (Strategy -> dividend_per_share) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.2f",
            help=Texts.HELP_DIVIDEND_BASE,
            key=f"{prefix}_div_base"  # Maps to DDMParameters.dividend_per_share
        )
        st.divider()

        # --- STEP 2: DIVIDEND DYNAMICS (Strategy -> projection_years / dividend_growth_rate) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # key_prefix produces {prefix}_years suffix
            widget_projection_years(default=5, key_prefix=prefix)

        with col2:
            # key_prefix produces {prefix}_growth_rate suffix
            widget_growth_rate(
                label=SharedTexts.INP_GROWTH_G,
                key_prefix=prefix
            )

        if Texts.NOTE_DDM_SGR:
            st.caption(Texts.NOTE_DDM_SGR)

        st.divider()