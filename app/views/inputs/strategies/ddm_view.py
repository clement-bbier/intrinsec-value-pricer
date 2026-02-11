import streamlit as st
from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import DDMTexts as Texts
from src.i18n import UISharedTexts
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_projection_years, widget_growth_rate

class DDMView(BaseStrategyView):
    MODE = ValuationMethodology.DDM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration (Sections Standards) ---
    SHOW_DISCOUNT_SECTION = True  # DDM uses Ke (Cost of Equity), not WACC
    SHOW_TERMINAL_SECTION = True  # Terminal value needed  
    SHOW_BRIDGE_SECTION = False   # Direct equity method, no bridge from EV to Equity

    # --- Extensions Flags ---
    SHOW_MONTE_CARLO = True
    SHOW_SENSITIVITY = True
    SHOW_BACKTEST = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False # False : Dividend model is per-share.
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(Texts.INP_BASE, value=None, format="%.2f", help=Texts.HELP_DIVIDEND_BASE, key=f"{prefix}_div_base")
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2 = st.columns(2)
        with c1: widget_projection_years(default=5, key_prefix=prefix)
        with c2: widget_growth_rate(label=UISharedTexts.INP_GROWTH_G, key_prefix=prefix)
        if hasattr(Texts, 'NOTE_DDM_SGR') and Texts.NOTE_DDM_SGR: st.caption(Texts.NOTE_DDM_SGR)
        st.divider()