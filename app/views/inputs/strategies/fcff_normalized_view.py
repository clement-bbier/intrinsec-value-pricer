import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_projection_years
from src.i18n.fr.ui.expert import FCFFNormalizedTexts as Texts
from src.models import ValuationMethodology


class FCFFNormalizedView(BaseStrategyView):
    MODE = ValuationMethodology.FCFF_NORMALIZED
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
        st.number_input(Texts.INP_BASE, value=None, format="%.0f", help=Texts.HELP_BASE, key=f"{prefix}_fcf_norm")
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2 = st.columns(2)
        with c1:
            widget_projection_years(default=5, key_prefix=prefix)
        with c2:
            st.number_input(Texts.LBL_GROWTH_G, value=None, format="%.2f", key=f"{prefix}_growth_rate")
        st.divider()
