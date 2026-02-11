import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_projection_years
from src.i18n.fr.ui.expert import FCFFGrowthTexts as Texts
from src.models import ValuationMethodology


class FCFFGrowthView(BaseStrategyView):
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
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(Texts.INP_BASE, value=None, format="%.0f", help=Texts.HELP_REV_TTM, key=f"{prefix}_revenue_ttm")
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2, c3 = st.columns(3)
        with c1:
            widget_projection_years(default=5, key_prefix=prefix)
        with c2:
            st.number_input(Texts.INP_REV_GROWTH, value=None, format="%.2f", help=Texts.HELP_REV_GROWTH, key=f"{prefix}_growth_rate")
        with c3:
            st.number_input(Texts.INP_MARGIN_TARGET, value=None, format="%.2f", help=Texts.HELP_MARGIN_TARGET, key=f"{prefix}_fcf_margin")
        st.divider()
