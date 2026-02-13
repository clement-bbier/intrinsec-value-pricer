import streamlit as st

from app.views.inputs.base_strategy import BaseStrategyView
from src.config.constants import UIKeys
from src.i18n.fr.ui.expert import GrahamTexts as Texts
from src.models import ValuationMethodology


class GrahamValueView(BaseStrategyView):
    """
    Expert terminal for Benjamin Graham Intrinsic Value formula.

    This is a simplified all-in-one formula that does not require
    discount rates, terminal values, or equity bridge sections.
    """

    MODE = ValuationMethodology.GRAHAM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration (Sections Standards) ---
    SHOW_DISCOUNT_SECTION = False  # Pas de WACC/Ke dans la formule
    SHOW_TERMINAL_SECTION = False  # Formule tout-en-un
    SHOW_BRIDGE_SECTION = False    # Donne un prix direct

    # --- Extensions Flags ---
    SHOW_MONTE_CARLO = True        # Utile pour varier EPS/Growth
    SHOW_SENSITIVITY = False       # Pas de WACC vs g
    SHOW_BACKTEST = True           # Très pertinent pour Graham
    SHOW_SCENARIOS = False         # Formule rigide
    SHOW_SOTP = False              # Non applicable
    SHOW_PEER_TRIANGULATION = False # Approche purement intrinsèque

    def render_model_inputs(self) -> None:
        """Renders Step 1 (EPS + growth) and Step 2 (AAA yield + tax) inputs."""
        prefix = self.MODE.name
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                Texts.INP_EPS, value=None, format="%.2f",
                help=Texts.HELP_EPS, key=f"{prefix}_{UIKeys.EPS_NORMALIZED}",
            )
        with c2:
            st.number_input(
                Texts.INP_GROWTH, value=None, format="%.2f",
                help=Texts.HELP_GROWTH_LT, key=f"{prefix}_{UIKeys.GROWTH_ESTIMATE}",
            )
        st.divider()
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(Texts.INP_YIELD_AAA, value=None, format="%.2f", help=Texts.HELP_YIELD_AAA, key=f"{prefix}_{UIKeys.YIELD_AAA}")
        with c2:
            st.number_input(Texts.INP_TAX, value=None, format="%.2f", help=Texts.HELP_TAX, key=f"{prefix}_{UIKeys.TAX}")
        if hasattr(Texts, 'NOTE_GRAHAM') and Texts.NOTE_GRAHAM:
            st.caption(Texts.NOTE_GRAHAM)
        st.divider()
