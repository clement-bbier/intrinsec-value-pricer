"""
app/ui/expert_terminals/fcfe_terminal.py

TERMINAL EXPERT — FREE CASH FLOW TO EQUITY (FCFE)
=================================================
Implémentation de l'interface de valorisation directe des fonds propres.
Ce terminal constitue les étapes 1 et 2 du "Logical Path" pour le modèle FCFE.

Architecture : ST-3.2 (Direct Equity)
Style : Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFETexts as Texts
from src.i18n import SharedTexts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class FCFETerminal(ExpertTerminalBase):
    """
    Terminal expert pour la valorisation par les flux de trésorerie actionnaires.

    Le modèle FCFE valorise directement l'action en actualisant les flux
    résiduels après service de la dette au coût des fonds propres (Ke).
    """

    MODE = ValuationMode.FCFE
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- Configuration du Pipeline UI ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Formules LaTeX narratives ---
    # La classe de base utilisera SharedTexts.FORMULA_BRIDGE_SIMPLE automatiquement
    # car ValuationMode.FCFE.is_direct_equity est True.
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCFE_n(1+g_n)}{k_e - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Rendu des entrées spécifiques au modèle FCFE (Étapes 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Paramètres : manual_fcf_base, manual_net_borrowing,
            projection_years, fcf_growth_rate.
        """
        prefix = self.MODE.name

        # --- ÉTAPE 1 : ANCRAGE ACTIONNAIRE ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            fcfe_base = st.number_input(
                Texts.INP_BASE,
                value=None,
                format="%.0f",
                help=Texts.HELP_FCFE_BASE,
                key=f"{prefix}_fcf_base"
            )

        with col2:
            net_borrowing = st.number_input(
                Texts.INP_NET_BORROWING,
                value=None,
                format="%.0f",
                help=Texts.HELP_NET_BORROWING,
                key=f"{prefix}_net_borrowing"
            )

        st.divider()

        # --- ÉTAPE 2 : HORIZON DE PROJECTION ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(label=SharedTexts.INP_GROWTH_G, key_prefix=prefix)

        st.divider()

        return {
            "manual_fcf_base": fcfe_base,
            "manual_net_borrowing": net_borrowing,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données FCFE depuis le session_state.

        Parameters
        ----------
        key_prefix : str
            Préfixe basé sur le ValuationMode.

        Returns
        -------
        Dict[str, Any]
            Données opérationnelles pour build_request.
        """
        return {
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_fcf_base"),
            "manual_net_borrowing": st.session_state.get(f"{key_prefix}_net_borrowing"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }