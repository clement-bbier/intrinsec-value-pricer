"""
app/ui/expert_terminals/fcff_growth_terminal.py
TERMINAL EXPERT — FCFF REVENUE-DRIVEN (GROWTH & MARGIN)
"""

from typing import Dict, Any
import streamlit as st
from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFFGrowthTexts as Texts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import widget_projection_years

class FCFFGrowthTerminal(ExpertTerminalBase):
    MODE = ValuationMode.FCFF_GROWTH
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    def render_model_inputs(self) -> Dict[str, Any]:
        prefix = self.MODE.name

        # --- ÉTAPE 1 : ASSIETTE DE REVENUS ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)
        rev_base = st.number_input(
            Texts.INP_BASE, value=None, format="%.0f",
            help=Texts.HELP_REV_TTM, key=f"{prefix}_rev_base"
        )
        st.divider()

        # --- ÉTAPE 2 : CONVERGENCE DES MARGES ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)
        col1, col2, col3 = st.columns(3)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rev = st.number_input(
                Texts.INP_REV_GROWTH, value=None, format="%.3f",
                help=Texts.HELP_REV_GROWTH, key=f"{prefix}_rev_growth"
            )
        with col3:
            m_target = st.number_input(
                Texts.INP_MARGIN_TARGET, value=None, format="%.2f",
                help=Texts.HELP_MARGIN_TARGET, key=f"{prefix}_margin_target"
            )

        st.divider()
        return {
            "manual_fcf_base": rev_base, "projection_years": n_years,
            "fcf_growth_rate": g_rev, "target_fcf_margin": m_target
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_rev_base"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_rev_growth"),
            "target_fcf_margin": st.session_state.get(f"{key_prefix}_margin_target"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }