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

from src.domain.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_projection_years


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
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_REV_BASE}**")
        st.latex(
            r"V_0 = \sum_{t=1}^{n} \frac{Rev_0(1+g_{rev})^t \times Margin_t}"
            r"{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
        )

        rev_base = st.number_input(
            ExpertTerminalTexts.INP_REV_TTM,
            value=None,
            format="%.0f",
            help=ExpertTerminalTexts.HELP_REV_TTM
        )
        st.divider()

        st.markdown(f"**{ExpertTerminalTexts.SEC_2_PROJ_GROWTH}**")

        col1, col2, col3 = st.columns(3)

        with col1:
            n_years = widget_projection_years(default=5, key="fcff_growth_years")

        with col2:
            g_rev = st.number_input(
                ExpertTerminalTexts.INP_REV_GROWTH,
                min_value=0.0,
                max_value=1.0,
                value=None,
                format="%.3f",
                help=ExpertTerminalTexts.HELP_REV_GROWTH
            )

        with col3:
            m_target = st.number_input(
                ExpertTerminalTexts.INP_MARGIN_TARGET,
                min_value=0.0,
                max_value=0.80,
                value=None,
                format="%.2f",
                help=ExpertTerminalTexts.HELP_MARGIN_TARGET
            )

        st.divider()

        return {
            "manual_fcf_base": rev_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rev,
            "target_fcf_margin": m_target,
        }
