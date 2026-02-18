import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_high_growth_years
from src.config.constants import UIKeys
from src.i18n.fr.ui.terminals import FCFFNormalizedTexts as Texts
from src.models import ValuationMethodology


class FCFFNormalizedView(BaseStrategyView):
    """
    Expert terminal for Normalized FCFF valuation.

    Projection years are managed globally via the Sidebar slider.
    """

    MODE = ValuationMethodology.FCFF_NORMALIZED
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
        """Renders Step 1 (normalized FCF) and Step 2 (ROIC and Reinvestment Rate) inputs."""
        prefix = self.MODE.name

        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.2f",
            key=f"{prefix}_{UIKeys.FCF_NORM}",
        )
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        st.number_input(Texts.LBL_GROWTH_G, value=None, format="%.2f", key=f"{prefix}_{UIKeys.GROWTH_RATE}")
        # Add maturity years slider for fade transition
        widget_high_growth_years(prefix)
        st.divider()
