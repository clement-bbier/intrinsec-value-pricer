"""
app/ui/expert_terminals/fcff_growth_terminal.py

Terminal Expert — FCFF Revenue-Driven Growth

Cas d'usage : Entreprises en forte croissance (tech, biotech, etc.)
Approche : Projette le CA puis applique une marge FCF cible.
Actualisation : WACC

Avantage : Permet de modéliser la convergence vers une rentabilité cible.

Style : Numpy docstrings
"""

from typing import Dict, Any

import streamlit as st

from src.models import ValuationMode
from src.i18n import SharedTexts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import widget_projection_years


class FCFFGrowthTerminal(ExpertTerminalBase):
    """
    Terminal pour la valorisation revenue-driven.

    Ce modèle part du chiffre d'affaires et projette la convergence
    vers une marge FCF cible. Idéal pour les entreprises en hypercroissance
    qui ne génèrent pas encore de flux stables.

    Attributes
    ----------
    MODE : ValuationMode
        FCFF_GROWTH
    DISPLAY_NAME : str
        "DCF - Revenue-Driven Growth"
    """

    MODE = ValuationMode.FCFF_GROWTH
    DISPLAY_NAME = "DCF - Revenue-Driven Growth"
    DESCRIPTION = "Projection CA puis convergence vers marge FCF cible"

    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True  # Les scénarios incluent la marge pour ce modèle
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{Rev_n \times Margin_{target} \times (1+g_n)}{WACC - g_n}"
    BRIDGE_FORMULA = r"P = \dfrac{EV - Dette + Cash}{Actions}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Inputs spécifiques au modèle Revenue-Driven.

        Collecte :
        - Chiffre d'affaires de base
        - Croissance du CA
        - Marge FCF cible à atteindre
        - Horizon de convergence

        Returns
        -------
        Dict[str, Any]
            - manual_fcf_base : Revenue de base (utilisé comme proxy)
            - fcf_growth_rate : Croissance CA
            - target_fcf_margin : Marge FCF cible
            - projection_years : Horizon
        """
        st.markdown(f"**{SharedTexts.SEC_1_REV_BASE}**")
        st.latex(
            r"V_0 = \sum_{t=1}^{n} \frac{Rev_0(1+g_{rev})^t \times Margin_t}"
            r"{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
        )

        rev_base = st.number_input(
            SharedTexts.INP_REV_TTM,
            value=None,
            format="%.0f",
            help=SharedTexts.HELP_REV_TTM,
            key=f"{self.MODE.name}_rev_base"
        )
        st.divider()

        st.markdown(f"**{SharedTexts.SEC_2_PROJ_GROWTH}**")

        col1, col2, col3 = st.columns(3)

        with col1:
            n_years = widget_projection_years(default=5, key_prefix=self.MODE.name)

        with col2:
            g_rev = st.number_input(
                SharedTexts.INP_REV_GROWTH,
                min_value=0.0,
                max_value=1.0,
                value=None,
                format="%.3f",
                help=SharedTexts.HELP_REV_GROWTH,
                key=f"{self.MODE.name}_rev_growth"
            )

        with col3:
            m_target = st.number_input(
                SharedTexts.INP_MARGIN_TARGET,
                min_value=0.0,
                max_value=0.80,
                value=None,
                format="%.2f",
                help=SharedTexts.HELP_MARGIN_TARGET,
                key=f"{self.MODE.name}_margin_target"
            )

        st.divider()

        return {
            "manual_fcf_base": rev_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rev,
            "target_fcf_margin": m_target,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données spécifiques au modèle FCFF Growth depuis st.session_state.

        Parameters
        ----------
        key_prefix : str
            Préfixe de clé basé sur le mode (FCFF_GROWTH).

        Returns
        -------
        Dict[str, Any]
            Données FCFF Growth : rev_base, growth_rate, margin_target, projection_years.
        """
        data = {}

        # Clés spécifiques
        rev_key = f"{key_prefix}_rev_base"
        if rev_key in st.session_state:
            data["manual_fcf_base"] = st.session_state[rev_key]

        growth_key = f"{key_prefix}_rev_growth"
        if growth_key in st.session_state:
            data["fcf_growth_rate"] = st.session_state[growth_key]

        margin_key = f"{key_prefix}_margin_target"
        if margin_key in st.session_state:
            data["target_fcf_margin"] = st.session_state[margin_key]

        years_key = f"{key_prefix}_years"
        if years_key in st.session_state:
            data["projection_years"] = st.session_state[years_key]

        return data
