import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from src.config.constants import UIKeys
from src.i18n.fr.ui.expert import FCFFStandardTexts as Texts
from src.models import ValuationMethodology


class FCFFStandardView(BaseStrategyView):
    """
    Expert terminal for Standard FCFF (Free Cash Flow to Firm) valuation.

    Projection years are managed globally via the Sidebar slider.
    """

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
        """Renders Step 1 (base FCF) and Step 2 (growth rate) inputs."""
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(
            Texts.INP_BASE, value=None, format="%.0f",
            help=Texts.HELP_BASE, key=f"{prefix}_{UIKeys.FCF_BASE}",
        )
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        st.number_input(
            Texts.INP_GROWTH_G, value=None, format="%.2f",
            help=Texts.HELP_GROWTH_RATE, key=f"{prefix}_{UIKeys.GROWTH_RATE}",
        )
        st.divider()
