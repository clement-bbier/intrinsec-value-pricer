"""
app/ui/expert/terminals/fcff_normalized_terminal.py

EXPERT TERMINAL — FCFF NORMALIZED (SMOOTHED FLOW)
=================================================
Valuation interface based on smoothed normative flows.
Data mapping is automated via FCFFNormalizedParameters and UIBinder.

Pattern: Strategy (Concrete Implementation)
Architecture: V16 (Metadata-Driven Extraction)
Style: Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from app.adapters.ui_binder import UIBinder
from src.models import ValuationMethodology
from src.i18n.fr.ui.expert import FCFFNormalizedTexts as Texts
from src.models.parameters.strategies import FCFFNormalizedParameters
from app.ui.expert.base_terminal import BaseTerminalExpert
from app.views.inputs.strategies.shared_widgets import (
    widget_projection_years
)


class FCFFNormalizedTerminalExpert(BaseTerminalExpert):
    """
    Expert terminal for Normalized Free Cash Flow to the Firm (FCFF).

    This terminal focuses on mid-cycle valuation by using smoothed normative
    flows to avoid distortions from temporary cyclical peaks or troughs.

    Attributes
    ----------
    MODE : ValuationMethodology
        Set to FCFF_NORMALIZED for mid-cycle valuation.
    DISPLAY_NAME : str
        Human-readable name from i18n.
    DESCRIPTION : str
        Brief description from i18n.
    """

    MODE = ValuationMethodology.FCFF_NORMALIZED
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
        Renders operational inputs for the Normalized FCFF model.

        Widget keys are mapped to UIKey suffixes defined in
        FCFFNormalizedParameters to enable automated extraction.
        """
        prefix = self.MODE.name

        # --- STEP 1: NORMATIVE FLOW (Strategy -> fcf_norm) ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BASE,
            key=f"{prefix}_fcf_norm"  # Maps to FCFFNormalizedParameters.fcf_norm
        )
        st.divider()

        # --- STEP 2: GROWTH DYNAMICS (Strategy -> projection_years / cycle_growth_rate) ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            # key_prefix produces {prefix}_years suffix
            widget_projection_years(default=5, key_prefix=prefix)

        with col2:
            st.number_input(
                Texts.LBL_GROWTH_G,
                value=None,
                format="%.2f",
                key=f"{prefix}_growth_rate"  # Maps to FCFFNormalizedParameters.cycle_growth_rate
            )

        st.divider()

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Automated extraction of Normalized FCFF strategy data.

        Parameters
        ----------
        key_prefix : str
            The session state prefix (ValuationMode.name).

        Returns
        -------
        Dict[str, Any]
            Raw UI values mapped to FCFFNormalizedParameters fields via UIBinder.
        """
        return UIBinder.pull(FCFFNormalizedParameters, prefix=key_prefix)