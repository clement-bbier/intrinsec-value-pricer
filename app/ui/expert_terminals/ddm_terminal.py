"""
app/ui/expert_terminals/ddm_terminal.py

Terminal Expert — Dividend Discount Model (DDM)

Cas d'usage : Entreprises matures avec politique de dividende stable.
Flux : Dividendes par action
Actualisation : Ke (Cost of Equity)

Avantage : Simple et direct pour les entreprises distribuant des dividendes.
Limitation : Inutilisable si pas de dividendes ou politique erratique.

Style : Numpy docstrings
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
)


class DDMTerminal(ExpertTerminalBase):
    """
    Terminal pour le Dividend Discount Model.

    Le DDM valorise l'action comme la somme actualisée des dividendes
    futurs. Recommandé pour les utilities, REITs, et entreprises matures
    avec un payout ratio stable.

    Notes
    -----
    Attention au "dividend trap" : un dividende élevé non soutenable
    peut surévaluer l'action. Vérifier le payout ratio (< 100%).

    Attributes
    ----------
    MODE : ValuationMode
        DDM
    DISPLAY_NAME : str
        "Dividend Discount Model"
    """

    MODE = ValuationMode.DDM
    DISPLAY_NAME = "Dividend Discount Model"
    DESCRIPTION = "Valorisation par les dividendes futurs actualises au Ke"

    # DDM = Direct Equity
    SHOW_BRIDGE_SECTION = True  # Simplifié (juste actions)

    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_PEER_TRIANGULATION = True

    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{D_n(1+g_n)}{k_e - g_n}"
    BRIDGE_FORMULA = r"P = \frac{\text{Equity Value}}{\text{Actions}}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Inputs spécifiques au DDM.

        Collecte :
        - Dividende par action de base (D0)
        - Horizon et croissance des dividendes

        Returns
        -------
        Dict[str, Any]
            - manual_dividend_base : Dividende D0
            - projection_years : Horizon
            - fcf_growth_rate : Croissance dividendes
        """
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_DDM_BASE}**")
        st.latex(
            r"P = \sum_{t=1}^{n} \frac{D_0(1+g)^t}{(1+k_e)^t} + "
            r"\frac{TV_n}{(1+k_e)^n}"
        )

        d0_base = st.number_input(
            ExpertTerminalTexts.INP_DIVIDEND_BASE,
            value=None,
            format="%.2f",
            help=ExpertTerminalTexts.HELP_DIVIDEND_BASE
        )

        st.divider()

        st.markdown(f"**{ExpertTerminalTexts.SEC_2_PROJ}**")

        col1, col2 = st.columns(2)

        with col1:
            n_years = widget_projection_years(default=5, key="ddm_years")

        with col2:
            g_rate = widget_growth_rate(
                label="Croissance dividendes (g)",
                min_val=0.0,
                max_val=0.20,
                key="ddm_growth"
            )

        st.caption(
            "*Rappel : g doit etre soutenable. "
            "SGR = ROE × (1 - Payout) est une borne superieure.*"
        )

        st.divider()

        return {
            "manual_dividend_base": d0_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }
