"""
app/views/inputs/strategies/fcff_normalized_view.py

EXPERT VIEW — FCFF NORMALIZED (SMOOTHED FLOW)
=============================================
Valuation interface based on smoothed normative flows.
Role: Renders inputs for Normalized FCF and Cycle Growth.

Pattern: Strategy View (MVC)
Architecture: V16 (Stateless Rendering)
Style: Numpy docstrings
"""

import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFFNormalizedTexts as Texts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import (
    widget_projection_years
)


class FCFFNormalizedView(BaseStrategyView):
    """
    Expert view for Normalized Free Cash Flow to the Firm (FCFF).

    This terminal focuses on mid-cycle valuation by using smoothed normative
    flows to avoid distortions from temporary cyclical peaks or troughs.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFF_NORMALIZED for mid-cycle valuation.
    """

    MODE = ValuationMethodology.FCFF_NORMALIZED
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """
        Renders specific inputs for the Normalized FCFF model.
        Writes directly to st.session_state for the Controller.
        """
        prefix = self.MODE.name

        # --- STEP 1: NORMALIZED ANCHOR (Strategy -> fcf_norm) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BASE,
            key=f"{prefix}_fcf_norm"  # Maps to FCFFNormalizedParameters.fcf_norm
        )
        st.divider()

        # --- STEP 2: GROWTH DYNAMICS (Strategy -> projection_years / cycle_growth_rate) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # key_prefix produces {prefix}_years suffix
            widget_projection_years(default=5, key_prefix=prefix)

        with col2:
            st.number_input(
                Texts.LBL_GROWTH_G,
                value=None,
                format="%.2f",
                key=f"{prefix}_growth_rate"  # Maps to FCFFNormalizedParameters.cycle_growth_rate
            )

        st.divider()