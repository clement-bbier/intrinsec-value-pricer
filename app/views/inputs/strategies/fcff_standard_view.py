"""
app/ui/expert/terminals/fcff_standard_terminal.py

EXPERT TERMINAL — FCFF TWO-STAGE STANDARD (CONTINUOUS FLOW)
==========================================================
Implementation of the Entity DCF (FCFF) interface.
Data mapping is automated via FCFFStandardParameters and UIBinder.

Pattern: Strategy (Concrete Implementation)
Architecture: V16 (Metadata-Driven Extraction)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMethodology
from src.models.parameters.strategies import FCFFStandardParameters
from src.i18n.fr.ui.expert import FCFFStandardTexts as Texts
from app.adapters.ui_binder import UIBinder
from app.ui.expert.base_terminal import BaseTerminalExpert
from app.views.inputs.strategies.shared_widgets import widget_projection_years


class FCFFStandardTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for Free Cash Flow to the Firm (FCFF) valuation.

    This terminal focuses on defining the cash flow anchor and the
    growth trajectory using standard two-stage DCF logic.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFF_STANDARD for entity-level valuation.
    """

    MODE = ValuationMethodology.FCFF_STANDARD
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- UI Pipeline Configuration ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    def render_model_inputs(self) -> None:
        """
        Renders operational inputs (Steps 1 & 2).

        Widget keys are mapped to UIKey suffixes defined in
        FCFFStandardParameters to enable automated extraction.
        """
        prefix = self.MODE.name

        # --- STEP 1: CASH FLOW ANCHOR (Strategy -> fcf_anchor) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BASE,
            key=f"{prefix}_fcf_base"  # Maps to FCFFStandardParameters.fcf_anchor
        )
        st.divider()

        # --- STEP 2: GROWTH PROJECTION (Strategy -> projection_years / growth_rate_p1) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # key_prefix produces {prefix}_years suffix
            widget_projection_years(default=5, key_prefix=prefix)

        with col2:
            st.number_input(
                Texts.INP_GROWTH_G,
                value=None,
                format="%.2f",
                help=Texts.HELP_GROWTH_RATE,
                key=f"{prefix}_growth_rate"  # Maps to FCFFStandardParameters.growth_rate_p1
            )

        st.divider()

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Automated extraction of FCFF-specific strategy data.

        Parameters
        ----------
        key_prefix : str
            The session state prefix (ValuationMode.name).

        Returns
        -------
        Dict[str, Any]
            Raw UI values mapped to FCFFStandardParameters fields.
        """
        return UIBinder.pull(FCFFStandardParameters, prefix=key_prefix)