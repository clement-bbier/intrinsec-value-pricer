import streamlit as st

from app.state.store import get_state
from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_high_growth_years
from src.config.constants import UIKeys
from src.i18n.fr.ui.terminals import FCFFStandardTexts as Texts
from src.models import ValuationMethodology


class FCFFStandardView(BaseStrategyView):
    """
    Expert terminal for Standard FCFF (Free Cash Flow to Firm) valuation.

    Projection years are managed globally via the Sidebar slider.
    """

    MODE = ValuationMethodology.FCFF_STANDARD
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION
    FORMULA_GLOBAL = Texts.FORMULA_GLOBAL

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
        state = get_state()
        
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.2f",
            key=f"{prefix}_{UIKeys.FCF_BASE}",
        )
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        st.number_input(
            Texts.INP_GROWTH_G,
            value=None,
            format="%.2f",
            help=Texts.HELP_GROWTH_RATE,
            key=f"{prefix}_{UIKeys.GROWTH_RATE}",
        )
        # Add maturity years slider for fade transition
        widget_high_growth_years(prefix, state.projection_years)
        st.divider()
