"""
app/ui/expert_terminals/fcff_standard_terminal.py

TERMINAL EXPERT — FCFF TWO-STAGE STANDARD (NARRATIVE FLOW)
==========================================================
Ce module implémente l'interface de valorisation DCF Entité classique.
Il suit une approche pédagogique permettant à l'analyste de construire
sa propre thèse de flux de trésorerie étape par étape.

Architecture : ST-3.1 (Fondamental - DCF)
Flux : Free Cash Flow to Firm (FCFF)
"""

from typing import Dict, Any, Optional
import streamlit as st

from src.models import ValuationMode
from src.i18n.fr.ui.expert import FCFFStandardTexts as Texts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class FCFFStandardTerminal(ExpertTerminalBase):
    """
    Terminal expert pour la valorisation par les flux de trésorerie à la firme.

    Ce terminal guide l'utilisateur à travers les étapes de projection
    du modèle DCF avant d'intégrer les paramètres de risque et les
    ajustements de structure hérités de la classe de base.

    Attributes
    ----------
    MODE : ValuationMode
        Identifiant unique du modèle (FCFF_STANDARD).
    DISPLAY_NAME : str
        Nom affiché dans l'en-tête du terminal (issu de i18n).
    DESCRIPTION : str
        Explication concise du modèle (issue de i18n).
    """

    MODE = ValuationMode.FCFF_STANDARD
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- Configuration du Pipeline UI ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Formules LaTeX narratives ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    BRIDGE_FORMULA = Texts.FORMULA_BRIDGE

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Rendu séquentiel et vertical des entrées spécifiques au modèle FCFF.

        Suit le flux narratif défini dans le référentiel i18n :
        Étape 1 : Ancrage du flux (Normalisation du point de départ).
        Étape 2 : Projection (Hypothèses de croissance explicite).

        Returns
        -------
        Dict[str, Any]
            Dictionnaire des paramètres capturés pour le moteur de calcul.
        """

        # --- ÉTAPE 1 : ANCRAGE ---
        st.markdown(Texts.STEP_1_TITLE)
        st.info(Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)
        fcf_base = st.number_input(
            Texts.INP_BASE,
            value=None, format="%.0f",
            key=f"{self.MODE.name}_fcf_base"
        )
        st.divider()

        # --- ÉTAPE 2 : PROJECTION ---
        st.markdown(Texts.STEP_2_TITLE)
        st.info(Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=self.MODE.name)
        with col2:
            g_rate = widget_growth_rate(label=Texts.INP_GROWTH_G, key_prefix=self.MODE.name)
        st.divider()

        return {
            "manual_fcf_base": fcf_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données du session_state selon le préfixe du terminal.

        Parameters
        ----------
        key_prefix : str
            Préfixe de clé (généralement le nom du mode).

        Returns
        -------
        Dict[str, Any]
            Données brutes extraites.
        """
        data = {}

        # Extraction sécurisée des états Streamlit
        data["manual_fcf_base"] = st.session_state.get(f"{key_prefix}_fcf_base")
        data["fcf_growth_rate"] = st.session_state.get(f"{key_prefix}_growth_rate")
        data["projection_years"] = st.session_state.get(f"{key_prefix}_years")

        return data