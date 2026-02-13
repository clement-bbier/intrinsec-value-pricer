import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_growth_rate
from src.config.constants import UIKeys
from src.i18n import UISharedTexts
from src.i18n.fr.ui.expert import DDMTexts as Texts
from src.models import ValuationMethodology


class DDMView(BaseStrategyView):
    """
    Expert terminal for Dividend Discount Model (DDM) valuation.

    Projection years are managed globally via the Sidebar slider.
    """

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
    SHOW_SOTP = False  # Dividend model is per-share.
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """Renders Step 1 (dividend base) and Step 2 (growth rate) inputs."""
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(
            Texts.INP_BASE, value=None, format="%.2f",
            help=Texts.HELP_DIVIDEND_BASE, key=f"{prefix}_{UIKeys.DIV_BASE}",
        )
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        widget_growth_rate(label=UISharedTexts.INP_GROWTH_G, key_prefix=prefix)
        if hasattr(Texts, 'NOTE_DDM_SGR') and Texts.NOTE_DDM_SGR:
            st.caption(Texts.NOTE_DDM_SGR)
        st.divider()
