"""
app/ui/expert_terminals/rim_bank_terminal.py

Terminal Expert — Residual Income Model (RIM)

Cas d'usage : Valorisation des institutions financières (banques, assurances).
Approche : BV + Σ(Residual Income) où RI = NI - (Ke × BV)
Actualisation : Ke (Cost of Equity)

Avantage : Mieux adapté aux business où le capital est un input (banques).
Concept : L'entreprise vaut sa book value + la valeur créée au-delà du Ke.

Style : Numpy docstrings
"""

from typing import Dict, Any

import streamlit as st

from src.domain.models import ValuationMode
from src.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
    widget_growth_rate,
    widget_terminal_value_rim,
)


class RIMBankTerminal(ExpertTerminalBase):
    """
    Terminal pour le Residual Income Model.

    Le RIM décompose la valeur en : Book Value + Valeur des profits
    anormaux. Un "residual income" positif signifie que l'entreprise
    génère un ROE supérieur à son coût du capital.

    Notes
    -----
    Particulièrement adapté aux banques où l'EV/Equity bridge
    n'a pas de sens (pas de dette "classique").

    Attributes
    ----------
    MODE : ValuationMode
        RIM
    DISPLAY_NAME : str
        "Residual Income Model"
    """

    MODE = ValuationMode.RIM
    DISPLAY_NAME = "Residual Income Model"
    DESCRIPTION = "BV + profits anormaux. Adapte aux institutions financieres"

    # RIM = Direct Equity
    SHOW_BRIDGE_SECTION = True  # Simplifié
    SHOW_TERMINAL_SECTION = False  # Géré spécifiquement via omega

    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_PEER_TRIANGULATION = True

    BRIDGE_FORMULA = r"P = \dfrac{\text{Equity Value}}{\text{Actions}}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Inputs spécifiques au RIM.

        Collecte :
        - Book Value initiale (BV0)
        - Net Income TTM
        - Horizon et croissance des profits
        - Facteur de persistance (omega)

        Returns
        -------
        Dict[str, Any]
            - manual_book_value : BV0
            - manual_fcf_base : NI (utilisé comme proxy)
            - fcf_growth_rate : Croissance NI
            - exit_multiple_value : Omega (persistance)
        """
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_RIM_BASE}**")
        st.latex(
            r"P = BV_0 + \sum_{t=1}^{n} \frac{NI_t - (k_e \times BV_{t-1})}"
            r"{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}"
        )

        col1, col2 = st.columns(2)

        with col1:
            bv = st.number_input(
                ExpertTerminalTexts.INP_BV_INITIAL,
                value=None,
                format="%.0f",
                help=ExpertTerminalTexts.HELP_BV_INITIAL
            )

        with col2:
            ni = st.number_input(
                ExpertTerminalTexts.INP_NI_TTM,
                value=None,
                format="%.0f",
                help=ExpertTerminalTexts.HELP_NI_TTM
            )

        st.divider()

        st.markdown(f"**{ExpertTerminalTexts.SEC_2_PROJ_RIM}**")

        g_ni = widget_growth_rate(
            label="Croissance Net Income (g)",
            min_val=0.0,
            max_val=0.50,
            key="rim_growth"
        )

        st.divider()

        # Valeur terminale RIM (facteur omega)
        tv_data = widget_terminal_value_rim(
            r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}"
        )

        return {
            "manual_book_value": bv,
            "manual_fcf_base": ni,
            "fcf_growth_rate": g_ni,
            **tv_data,
        }
