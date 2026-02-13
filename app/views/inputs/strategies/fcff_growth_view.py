import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from src.config.constants import UIKeys
from src.i18n.fr.ui.expert import FCFFGrowthTexts as Texts
from src.models import ValuationMethodology


class FCFFGrowthView(BaseStrategyView):
    """
    Expert terminal for Revenue Growth FCFF valuation.

    Projection years are managed globally via the Sidebar slider.
    """

    MODE = ValuationMethodology.FCFF_GROWTH
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SENSITIVITY = True
    SHOW_BACKTEST = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """Renders Step 1 (revenue base) and Step 2 (growth + margin) inputs."""
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(Texts.INP_BASE, value=None, format="%.0f", help=Texts.HELP_REV_TTM, key=f"{prefix}_{UIKeys.REVENUE_TTM}")
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                Texts.INP_REV_GROWTH, value=None, format="%.2f",
                help=Texts.HELP_REV_GROWTH, key=f"{prefix}_{UIKeys.GROWTH_RATE}",
            )
        with c2:
            st.number_input(
                Texts.INP_MARGIN_TARGET, value=None, format="%.2f",
                help=Texts.HELP_MARGIN_TARGET, key=f"{prefix}_{UIKeys.FCF_MARGIN}",
            )
        st.divider()
