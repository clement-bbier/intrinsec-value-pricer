"""
app/ui/expert_terminals/fcff_normalized_terminal.py
TERMINAL EXPERT — FCFF NORMALIZED (SMOOTHED FLOW)
"""

from typing import Dict, Any
import streamlit as st
from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFFNormalizedTexts as Texts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)

class FCFFNormalizedTerminal(ExpertTerminalBase):
    MODE = ValuationMode.FCFF_NORMALIZED
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    SHOW_SOTP = True

    def render_model_inputs(self) -> Dict[str, Any]:
        prefix = self.MODE.name

        # --- ÉTAPE 1 : FLUX NORMATIF ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        fcf_base = st.number_input(
            Texts.INP_BASE, value=None, format="%.0f",
            help=Texts.HELP_BASE, key=f"{prefix}_fcf_base"
        )
        st.divider()

        # --- ÉTAPE 2 : DYNAMIQUE DE CROISSANCE ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(key_prefix=prefix)

        st.divider()
        return {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate}

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_fcf_base"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }