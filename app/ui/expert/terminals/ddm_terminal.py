"""
app/ui/expert_terminals/ddm_terminal.py

TERMINAL EXPERT — DIVIDEND DISCOUNT MODEL (DDM)
==============================================
Interface de valorisation par l'actualisation des dividendes futurs.
Ce terminal implémente les étapes 1 et 2 pour les entreprises matures.

Architecture : ST-3.2 (Direct Equity)
Style : Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import DDMTexts as Texts
from src.i18n import SharedTexts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class DDMTerminal(ExpertTerminalBase):
    """
    Terminal expert pour le modèle d'actualisation des dividendes.

    Le DDM valorise l'action comme la valeur présente des flux de dividendes
    attendus, actualisés au coût des fonds propres (Ke).
    """

    MODE = ValuationMode.DDM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- Configuration du Pipeline UI ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Formules LaTeX narratives ---
    # Note : Le bridge utilisera SharedTexts.FORMULA_BRIDGE_SIMPLE car is_direct_equity est True.
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{D_n(1+g_n)}{k_e - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Rendu des entrées spécifiques au modèle DDM (Étapes 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Paramètres : manual_dividend_base, projection_years, fcf_growth_rate.
        """
        prefix = self.MODE.name

        # --- ÉTAPE 1 : FLUX DE DIVIDENDES ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)

        d0_base = st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.2f",
            help=Texts.HELP_DIVIDEND_BASE,
            key=f"{prefix}_dividend_base"
        )

        st.divider()

        # --- ÉTAPE 2 : DYNAMIQUE DES DIVIDENDES ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(
                label=SharedTexts.INP_GROWTH_G,
                key_prefix=prefix
            )

        if Texts.NOTE_DDM_SGR:
            st.caption(Texts.NOTE_DDM_SGR)

        st.divider()

        return {
            "manual_dividend_base": d0_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données DDM depuis le session_state.

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
            "manual_dividend_base": st.session_state.get(f"{key_prefix}_dividend_base"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }