import streamlit as st
from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFETexts as Texts
from src.i18n import SharedTexts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_projection_years

class FCFEView(BaseStrategyView):
    MODE = ValuationMethodology.FCFE
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration (Sections Standards) ---
    SHOW_DISCOUNT_SECTION = True  # FCFE uses Ke (Cost of Equity), not WACC
    SHOW_TERMINAL_SECTION = True  # Terminal value needed
    SHOW_BRIDGE_SECTION = False   # Direct equity method, no bridge from EV to Equity

    # --- Extensions Flags ---
    SHOW_MONTE_CARLO = True
    SHOW_SENSITIVITY = True
    SHOW_BACKTEST = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False # False : SOTP is EV based, FCFE is Equity based.
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        c1, c2 = st.columns(2)
        with c1: st.number_input(Texts.INP_BASE, value=None, format="%.0f", help=Texts.HELP_FCFE_BASE, key=f"{prefix}_fcfe_anchor")
        with c2: st.number_input(Texts.INP_NET_BORROWING, value=None, format="%.0f", help=Texts.HELP_NET_BORROWING, key=f"{prefix}_net_borrowing_delta")
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2 = st.columns(2)
        with c1: widget_projection_years(default=5, key_prefix=prefix)
        with c2: st.number_input(SharedTexts.INP_GROWTH_G, value=None, format="%.2f", help=SharedTexts.HELP_GROWTH_RATE, key=f"{prefix}_growth_rate")
        st.divider()