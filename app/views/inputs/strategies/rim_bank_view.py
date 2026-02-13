import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from src.config.constants import UIKeys
from src.i18n import UISharedTexts
from src.i18n.fr.ui.expert import RIMTexts as Texts
from src.models import ValuationMethodology


class RIMBankView(BaseStrategyView):
    """
    Expert terminal for Residual Income Model (RIM / Ohlson) valuation.

    Projection years are managed globally via the Sidebar slider.
    """

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
        """Renders Step 1 (book value anchor) and Step 2 (growth rate) inputs."""
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(
            Texts.INP_BV_BASE, value=None, format="%.0f",
            help=Texts.HELP_BV_BASE, key=f"{prefix}_{UIKeys.BV_ANCHOR}",
        )
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        st.number_input(
            UISharedTexts.INP_GROWTH_G, value=None, format="%.2f",
            help=UISharedTexts.HELP_GROWTH_RATE, key=f"{prefix}_{UIKeys.GROWTH_RATE}",
        )
        st.divider()
