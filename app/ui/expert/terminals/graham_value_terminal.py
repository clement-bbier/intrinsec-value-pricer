"""
app/ui/expert_terminals/graham_value_terminal.py

TERMINAL EXPERT — GRAHAM INTRINSIC VALUE (QUANT REVISED)
========================================================
Formule de screening défensive (Revised 1974) enrichie par
une approche stochastique (Monte Carlo sur EPS).

Architecture : ST-4.1 (Screening & Probabiliste)
Style : Numpy docstrings
"""

from typing import Dict, Any
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import GrahamTexts as Texts
from ..base_terminal import ExpertTerminalBase


class GrahamValueTerminal(ExpertTerminalBase):
    """
    Terminal expert pour la formule de Graham.

    Bien que le modèle original soit déterministe, ce terminal permet
    une analyse de sensibilité via Monte Carlo sur les bénéfices (EPS)
    et les scénarios de croissance.
    """

    MODE = ValuationMode.GRAHAM
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- Configuration du Pipeline UI (Adaptation Statique) ---
    SHOW_DISCOUNT_SECTION = False  # Pas de WACC/Ke explicite
    SHOW_TERMINAL_SECTION = False  # Pas de TV Gordon/Multiples
    SHOW_BRIDGE_SECTION = False    # Valorise directement l'action

    SHOW_MONTE_CARLO = False        # Activé pour simuler l'EPS
    SHOW_SCENARIOS = False
    SHOW_SOTP = False              # Non applicable à Graham
    SHOW_PEER_TRIANGULATION = False
    SHOW_SUBMIT_BUTTON = False

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Rendu des entrées spécifiques au modèle Graham (Étapes 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Paramètres : manual_fcf_base (EPS), fcf_growth_rate (g),
            corporate_aaa_yield (Y), tax_rate (tau).
        """
        prefix = self.MODE.name

        # --- ÉTAPE 1 : BÉNÉFICES & CROISSANCE ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)
        st.latex(Texts.STEP_1_FORMULA)

        col1, col2 = st.columns(2)
        with col1:
            eps = st.number_input(
                Texts.INP_EPS_NORM,
                value=None,
                format="%.2f",
                help=Texts.HELP_EPS_NORM,
                key=f"{prefix}_eps_norm"
            )

        with col2:
            g_lt = st.number_input(
                Texts.INP_GROWTH_G,
                value=None,
                format="%.3f",
                help=Texts.HELP_GROWTH_LT,
                key=f"{prefix}_growth_lt"
            )

        st.divider()

        # --- ÉTAPE 2 : CONDITIONS DE MARCHÉ ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            yield_aaa = st.number_input(
                Texts.INP_YIELD_AAA,
                value=None,
                format="%.3f",
                help=Texts.HELP_YIELD_AAA,
                key=f"{prefix}_yield_aaa"
            )

        with col2:
            tau = st.number_input(
                Texts.INP_TAX,
                value=None,
                format="%.2f",
                help=Texts.HELP_TAX,
                key=f"{prefix}_tax_rate"
            )

        st.caption(Texts.NOTE_GRAHAM)
        st.divider()

        return {
            "manual_fcf_base": eps,
            "fcf_growth_rate": g_lt,
            "corporate_aaa_yield": yield_aaa,
            "tax_rate": tau,
            "projection_years": 1
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données Graham depuis le session_state.

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
            "manual_fcf_base": st.session_state.get(f"{key_prefix}_eps_norm"),
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_lt"),
            "corporate_aaa_yield": st.session_state.get(f"{key_prefix}_yield_aaa"),
            "tax_rate": st.session_state.get(f"{key_prefix}_tax_rate"),
            "projection_years": 1
        }