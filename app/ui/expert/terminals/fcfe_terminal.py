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

from src.models import ValuationMode
from src.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
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
    DISPLAY_NAME = "FCFE - Free Cash Flow to Equity"
    DESCRIPTION = "Valorisation directe equity : flux actionnaires actualises au Ke"

    # FCFE = Direct Equity, pas besoin de bridge complet
    SHOW_BRIDGE_SECTION = True  # Mais bridge simplifié (juste actions)

    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_PEER_TRIANGULATION = True
    SHOW_SUBMIT_BUTTON = False

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
                help=ExpertTerminalTexts.HELP_FCFE_BASE,
                key=f"{self.MODE.name}_fcf_base"
            )

        with col2:
            net_borrowing = st.number_input(
                ExpertTerminalTexts.INP_NET_BORROWING,
                value=None,
                format="%.0f",
                help=ExpertTerminalTexts.HELP_NET_BORROWING,
                key=f"{self.MODE.name}_net_borrowing"
            )

        st.divider()

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
            "manual_fcf_base": fcfe_base,
            "manual_net_borrowing": net_borrowing,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données spécifiques au modèle FCFE depuis st.session_state.

        Parameters
        ----------
        key_prefix : str
            Préfixe de clé basé sur le mode (FCFE).

        Returns
        -------
        Dict[str, Any]
            Données FCFE : fcf_base, net_borrowing, projection_years, growth_rate.
        """
        data = {}

        # Clés FCFE spécifiques
        fcf_key = f"{key_prefix}_fcf_base"
        if fcf_key in st.session_state:
            data["manual_fcf_base"] = st.session_state[fcf_key]

        net_borrowing_key = f"{key_prefix}_net_borrowing"
        if net_borrowing_key in st.session_state:
            data["manual_net_borrowing"] = st.session_state[net_borrowing_key]

        # Clés communes (growth, projection years)
        growth_key = f"{key_prefix}_growth_rate"
        if growth_key in st.session_state:
            data["fcf_growth_rate"] = st.session_state[growth_key]

        years_key = f"{key_prefix}_years"
        if years_key in st.session_state:
            data["projection_years"] = st.session_state[years_key]

        return data
