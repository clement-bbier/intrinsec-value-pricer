import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from app.state.store import get_state
from src.i18n import SidebarTexts
from src.i18n.fr.ui.expert import FCFFStandardTexts as Texts
from src.models import ValuationMethodology


class FCFFStandardView(BaseStrategyView):
    MODE = ValuationMethodology.FCFF_STANDARD
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
        st.number_input(Texts.INP_BASE, value=None, format="%.0f", help=Texts.HELP_BASE, key=f"{prefix}_fcf_base")
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"{SidebarTexts.YEARS_LABEL}: {get_state().projection_years}")
        with c2:
            st.number_input(
                Texts.INP_GROWTH_G, value=None, format="%.2f",
                help=Texts.HELP_GROWTH_RATE, key=f"{prefix}_growth_rate",
            )
        st.divider()
