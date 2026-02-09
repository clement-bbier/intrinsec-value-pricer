"""
app/views/inputs/strategies/fcff_growth_view.py

EXPERT VIEW — FCFF REVENUE-DRIVEN (GROWTH & MARGIN)
===================================================
Valuation interface based on revenue growth and margin convergence.
Role: Renders inputs for Revenue, Growth Rate, and Target Margin.

Pattern: Strategy View (MVC)
Architecture: V16 (Stateless Rendering)
Style: Numpy docstrings
"""

import streamlit as st

from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFFGrowthTexts as Texts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_projection_years


class FCFFGrowthView(BaseStrategyView):
    """
    Expert view for the Revenue-Driven FCFF model.

    This interface guides the analyst in projecting top-line growth
    and target margin convergence to derive future cash flows.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFF_GROWTH for revenue-driven valuation.
    """

    MODE = ValuationMethodology.FCFF_GROWTH
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """
        Renders specific inputs for the Revenue-Driven FCFF model.
        Writes directly to st.session_state for the Controller to pick up.
        """
        prefix = self.MODE.name

        # --- STEP 1: REVENUE BASE (Strategy -> revenue_ttm) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_REV_TTM,
            key=f"{prefix}_revenue_ttm"  # Maps to FCFFGrowthParameters.revenue_ttm
        )
        st.divider()

        # --- STEP 2: MARGIN CONVERGENCE (Strategy -> growth & margin) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2, col3 = st.columns(3)
        with col1:
            # key_prefix produces {prefix}_years suffix
            widget_projection_years(default=5, key_prefix=prefix)

        with col2:
            st.number_input(
                Texts.INP_REV_GROWTH,
                value=None,
                format="%.2f",
                help=Texts.HELP_REV_GROWTH,
                key=f"{prefix}_growth_rate"  # Maps to FCFFGrowthParameters.revenue_growth_rate
            )

        with col3:
            st.number_input(
                Texts.INP_MARGIN_TARGET,
                value=None,
                format="%.2f",
                help=Texts.HELP_MARGIN_TARGET,
                key=f"{prefix}_fcf_margin"  # Maps to FCFFGrowthParameters.target_fcf_margin
            )

        st.divider()