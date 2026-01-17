"""
app/ui/expert_terminals/fcfe_terminal.py

Terminal Expert — FCFE (Free Cash Flow to Equity)

Cas d'usage : Valorisation directe des fonds propres.
Flux : FCFE = FCF - (Intérêts)(1-τ) + Δ Dette nette
Actualisation : Ke (Cost of Equity) au lieu du WACC

Avantage : Pas besoin d'equity bridge, valorise directement l'action.
Risque : Sensible aux hypothèses de politique de dette.

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


class FCFETerminal(ExpertTerminalBase):
    """
    Terminal pour la valorisation FCFE (Direct Equity).

    Le FCFE représente les flux disponibles pour les actionnaires
    après service de la dette. Il est actualisé au coût des fonds
    propres (Ke) et ne nécessite pas d'equity bridge.

    Notes
    -----
    Ce modèle est particulièrement sensible aux hypothèses sur
    le Net Borrowing (variation de dette nette). Un Net Borrowing
    positif augmente artificiellement le FCFE.

    Attributes
    ----------
    MODE : ValuationMode
        FCFE
    DISPLAY_NAME : str
        "DCF - Free Cash Flow to Equity"
    """

    MODE = ValuationMode.FCFE
    DISPLAY_NAME = "DCF - Free Cash Flow to Equity"
    DESCRIPTION = "Valorisation directe equity : flux actionnaires actualises au Ke"

    # FCFE = Direct Equity, pas besoin de bridge complet
    SHOW_BRIDGE_SECTION = True  # Mais bridge simplifié (juste actions)

    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_PEER_TRIANGULATION = True

    TERMINAL_VALUE_FORMULA = (
        r"TV_n = \begin{cases} "
        r"\dfrac{FCFE_n(1+g_n)}{k_e - g_n} & \text{(Gordon)} \\ "
        r"FCFE_n \times \text{Multiple} & \text{(Exit)} \end{cases}"
    )
    BRIDGE_FORMULA = r"P = \frac{\text{Equity Value}}{\text{Actions}}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Inputs spécifiques au modèle FCFE.

        Collecte :
        - FCFE de base
        - Net Borrowing (variation dette)
        - Horizon et croissance

        Returns
        -------
        Dict[str, Any]
            - manual_fcf_base : FCFE de départ
            - manual_net_borrowing : Δ Dette nette
            - projection_years : Horizon
            - fcf_growth_rate : Croissance
        """
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FCFE_BASE}**")
        st.latex(
            r"P = \sum_{t=1}^{n} \frac{FCFE_t}{(1+k_e)^t} + "
            r"\frac{TV_n}{(1+k_e)^n}"
        )

        col1, col2 = st.columns(2)

        with col1:
            fcfe_base = st.number_input(
                ExpertTerminalTexts.INP_FCFE_BASE,
                value=None,
                format="%.0f",
                help=ExpertTerminalTexts.HELP_FCFE_BASE
            )

        with col2:
            net_borrowing = st.number_input(
                ExpertTerminalTexts.INP_NET_BORROWING,
                value=None,
                format="%.0f",
                help=ExpertTerminalTexts.HELP_NET_BORROWING
            )

        st.divider()

        st.markdown(f"**{ExpertTerminalTexts.SEC_2_PROJ}**")

        col1, col2 = st.columns(2)

        with col1:
            n_years = widget_projection_years(default=5, key="fcfe_years")

        with col2:
            g_rate = widget_growth_rate(
                label=ExpertTerminalTexts.INP_GROWTH_G,
                min_val=-0.50,
                max_val=1.0,
                key="fcfe_growth"
            )

        st.divider()

        return {
            "manual_fcf_base": fcfe_base,
            "manual_net_borrowing": net_borrowing,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }
