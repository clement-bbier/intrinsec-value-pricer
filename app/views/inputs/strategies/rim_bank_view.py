import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from src.config.constants import UIKeys
from src.i18n.fr.ui.terminals import CommonTerminals
from src.i18n.fr.ui.terminals import RIMTexts as Texts
from src.models import ValuationMethodology


class RIMBankView(BaseStrategyView):
    """
    Expert terminal for Residual Income Model (RIM / Ohlson) valuation.

    Projection years are managed globally via the Sidebar slider.
    """

    MODE = ValuationMethodology.RIM
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
        """Renders Step 1 (book value anchor + EPS anchor) and Step 2 (growth rate) inputs."""
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                Texts.INP_BV_BASE,
                value=None,
                format="%.2f",
                help=Texts.HELP_BV_BASE,
                key=f"{prefix}_{UIKeys.BV_ANCHOR}",
            )
        with c2:
            st.number_input(
                Texts.INP_EPS_ANCHOR,
                value=None,
                format="%.2f",
                help=Texts.HELP_EPS_ANCHOR,
                key=f"{prefix}_{UIKeys.EPS_ANCHOR}",
            )
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        st.number_input(
            CommonTerminals.INP_GROWTH_G,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_GROWTH_RATE,
            key=f"{prefix}_{UIKeys.GROWTH_RATE}",
        )
        st.divider()
