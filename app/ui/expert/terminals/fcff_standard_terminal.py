"""
app/ui/expert_terminals/fcff_standard_terminal.py

TERMINAL EXPERT — FCFF TWO-STAGE STANDARD

Rôle : Valorisation d'entreprises matures avec FCF stable
Pattern : Template Method (hérite de ExpertTerminalBase)
Style : Numpy docstrings

Terminal FCFF Standard
Risques financiers : Calculs de valorisation, sensibilité aux inputs

Dépendances critiques :
- streamlit >= 1.28.0
- core.models.ValuationMode.FCFF_STANDARD
- app.ui.base.ExpertTerminalBase

Cas d'usage : Entreprises matures avec FCF positif et stable
Flux : Free Cash Flow to Firm (avant service de la dette)
Actualisation : WACC (Weighted Average Cost of Capital)
Niveau : Enterprise Value → Equity Value via Bridge

Formule principale :
    V0 = Σ(FCFt / (1+WACC)^t) + TVn / (1+WACC)^n
"""

from typing import Dict, Any

import streamlit as st

from src.models import ValuationMode
from src.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class FCFFStandardTerminal(ExpertTerminalBase):
    """
    Terminal pour la valorisation FCFF Two-Stage classique.

    Ce modèle est adapté aux entreprises matures générant des flux
    de trésorerie positifs et stables. Il utilise le WACC comme
    taux d'actualisation et requiert un equity bridge complet.

    Attributes
    ----------
    MODE : ValuationMode
        FCFF_STANDARD
    DISPLAY_NAME : str
        "DCF - Free Cash Flow to Firm"
    """

    MODE = ValuationMode.FCFF_STANDARD
    DISPLAY_NAME = "DCF - Free Cash Flow to Firm"
    DESCRIPTION = "DCF classique : flux operationnels actualises au WACC"

    # Configuration des sections
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_SOTP = False
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    # Formules LaTeX
    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    BRIDGE_FORMULA = r"P = \dfrac{EV - Dette + Cash - Min - Pensions}{Actions}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Inputs spécifiques au modèle FCFF Standard.

        Collecte :
        - FCF de base (TTM ou manuel)
        - Horizon de projection
        - Taux de croissance Phase 1

        Returns
        -------
        Dict[str, Any]
            - manual_fcf_base : FCF de départ
            - projection_years : Horizon explicite
            - fcf_growth_rate : Croissance Phase 1
        """
        # Formule du modèle
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FCF_STD}**")
        st.latex(
            r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + "
            r"\frac{TV_n}{(1+WACC)^n}"
        )

        # FCF de base
        fcf_base = st.number_input(
            ExpertTerminalTexts.INP_FCF_TTM,
            value=None,
            format="%.0f",
            help=ExpertTerminalTexts.HELP_FCF_TTM,
            key=f"{self.MODE.name}_fcf_base"
        )
        st.divider()

        # Section croissance
        st.markdown(f"**{ExpertTerminalTexts.SEC_2_PROJ}**")

        col1, col2 = st.columns(2)

        with col1:
            n_years = widget_projection_years(default=5, key_prefix=self.MODE.name)

        with col2:
            g_rate = widget_growth_rate(
                label=ExpertTerminalTexts.INP_GROWTH_G,
                min_val=-0.50,
                max_val=1.0,
                key_prefix=self.MODE.name
            )

        st.divider()

        return {
            "manual_fcf_base": fcf_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données spécifiques au modèle FCFF Standard depuis st.session_state.

        Parameters
        ----------
        key_prefix : str
            Préfixe de clé basé sur le mode (FCFF_STANDARD).

        Returns
        -------
        Dict[str, Any]
            Données FCFF Standard : fcf_base, projection_years, growth_rate.
        """
        data = {}

        # Clé FCF spécifique
        fcf_key = f"{key_prefix}_fcf_base"
        if fcf_key in st.session_state:
            data["manual_fcf_base"] = st.session_state[fcf_key]

        # Clés communes (growth, projection years)
        growth_key = f"{key_prefix}_growth_rate"
        if growth_key in st.session_state:
            data["fcf_growth_rate"] = st.session_state[growth_key]

        years_key = f"{key_prefix}_years"
        if years_key in st.session_state:
            data["projection_years"] = st.session_state[years_key]

        return data
