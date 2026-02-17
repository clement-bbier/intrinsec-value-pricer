import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from app.views.inputs.strategies.shared_widgets import widget_high_growth_years
from src.config.constants import UIKeys
from src.i18n.fr.ui.terminals import CommonTerminals
from src.i18n.fr.ui.terminals import FCFETexts as Texts
from src.models import ValuationMethodology


class FCFEView(BaseStrategyView):
    """
    Expert terminal for Free Cash Flow to Equity (FCFE) valuation.

    Projection years are managed globally via the Sidebar slider.
    """

    MODE = ValuationMethodology.FCFE
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION
    FORMULA_GLOBAL = Texts.FORMULA_GLOBAL

    # --- UI Pipeline Configuration (Sections Standards) ---
    SHOW_DISCOUNT_SECTION = True  # FCFE uses Ke (Cost of Equity), not WACC
    SHOW_TERMINAL_SECTION = True  # Terminal value needed
    SHOW_BRIDGE_SECTION = False  # Direct equity method, no bridge from EV to Equity

    # --- Extensions Flags ---
    SHOW_MONTE_CARLO = True
    SHOW_SENSITIVITY = True
    SHOW_BACKTEST = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False  # SOTP is EV based, FCFE is Equity based.
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> None:
        """Renders Step 1 (FCFE base + borrowing) and Step 2 (growth rate) inputs."""
        prefix = self.MODE.name

        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                Texts.INP_BASE,
                value=None,
                format="%.2f",
                help=Texts.HELP_FCFE_BASE,
                key=f"{prefix}_{UIKeys.FCFE_ANCHOR}",
            )
        with c2:
            st.number_input(
                Texts.INP_NET_BORROWING,
                value=None,
                format="%.2f",
                help=Texts.HELP_NET_BORROWING,
                key=f"{prefix}_{UIKeys.NET_BORROWING_DELTA}",
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
        # Add maturity years slider for fade transition
        widget_high_growth_years(prefix)
        st.divider()
