import streamlit as st
from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import RIMTexts as Texts
from src.i18n import SharedTexts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_projection_years

class RIMBankView(BaseStrategyView):
    MODE = ValuationMethodology.RIM
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
        st.number_input(Texts.INP_BV_BASE, value=None, format="%.0f", help=Texts.HELP_BV_BASE, key=f"{prefix}_bv_anchor")
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2 = st.columns(2)
        with c1: widget_projection_years(default=5, key_prefix=prefix)
        with c2: st.number_input(SharedTexts.INP_GROWTH_G, value=None, format="%.2f", help=SharedTexts.HELP_GROWTH_RATE, key=f"{prefix}_growth_rate")
        # st.number_input(SharedTexts.INP_OMEGA, min_value=0.0, max_value=1.0, value=None, format="%.2f", help=SharedTexts.HELP_OMEGA, key=f"{prefix}_omega")
        st.divider()