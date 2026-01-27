"""
app/ui/expert_terminals/fcff_standard_terminal.py

TERMINAL EXPERT — FCFF TWO-STAGE STANDARD (FLUX CONTINU)
==========================================================
Implémentation de l'interface DCF Entité (FCFF).
Ce terminal constitue les étapes 1 et 2 du "Logical Path" analytique.

Architecture : ST-3.1 (Fondamental - DCF)
Style : Numpy docstrings
"""

from typing import Dict, Any
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

    Ce module guide l'analyste dans la définition de son ancrage (Y0)
    et de sa trajectoire de croissance avant de passer aux étapes de
    risque et de structure gérées par la classe de base.
    """

    MODE = ValuationMode.FCFF_STANDARD
    DISPLAY_NAME = Texts.TITLE
    DESCRIPTION = Texts.DESCRIPTION

    # --- Configuration du Pipeline UI (9 Étapes) ---
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = True  # Activé : devient l'Étape 9 du tunnel expert
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # --- Formules LaTeX narratives ---
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Rendu des entrées opérationnelles (Étapes 1 & 2).

        Returns
        -------
        Dict[str, Any]
            Paramètres capturés : manual_fcf_base, projection_years, fcf_growth_rate.
        """
        prefix = self.MODE.name

        # --- ÉTAPE 1 : ANCRAGE DU FLUX ---
        self._render_step_header(Texts.STEP_1_TITLE, Texts.STEP_1_DESC)

        st.latex(Texts.STEP_1_FORMULA)
        fcf_base = st.number_input(
            Texts.INP_BASE,
            value=None,
            format="%.0f",
            help=Texts.HELP_BASE,
            key=f"{prefix}_fcf_base"
        )
        st.divider()

        # --- ÉTAPE 2 : PROJECTION DE LA CROISSANCE ---
        self._render_step_header(Texts.STEP_2_TITLE, Texts.STEP_2_DESC)

        col1, col2 = st.columns(2)
        with col1:
            n_years = widget_projection_years(default=5, key_prefix=prefix)
        with col2:
            g_rate = widget_growth_rate(label=Texts.INP_GROWTH_G, key_prefix=prefix)

        st.divider()

        return {
            "manual_fcf_base": fcf_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données spécifiques au FCFF depuis le session_state.

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
            "fcf_growth_rate": st.session_state.get(f"{key_prefix}_growth_rate"),
            "projection_years": st.session_state.get(f"{key_prefix}_years")
        }