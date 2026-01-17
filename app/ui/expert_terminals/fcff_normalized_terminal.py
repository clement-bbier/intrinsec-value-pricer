"""
app/ui/expert_terminals/fcff_normalized_terminal.py

Terminal Expert — FCFF Normalized (Fundamental)

Cas d'usage : Entreprises cycliques ou avec FCF volatile.
Approche : Utilise un FCF normalisé (lissé sur cycle) plutôt que TTM.
Actualisation : WACC

Avantage : Réduit le bruit des variations de cycle économique.

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


class FCFFNormalizedTerminal(ExpertTerminalBase):
    """
    Terminal pour la valorisation FCFF avec flux normalisés.

    Ce modèle utilise un FCF lissé sur le cycle économique pour
    réduire l'impact des fluctuations conjoncturelles.
    Recommandé pour les secteurs cycliques (auto, construction, etc.)

    Attributes
    ----------
    MODE : ValuationMode
        FCFF_NORMALIZED
    DISPLAY_NAME : str
        "DCF - Normalized Free Cash Flow"
    """

    MODE = ValuationMode.FCFF_NORMALIZED
    DISPLAY_NAME = "DCF - Normalized Free Cash Flow"
    DESCRIPTION = "DCF avec flux lisses sur le cycle economique"

    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    SHOW_PEER_TRIANGULATION = True

    TERMINAL_VALUE_FORMULA = r"TV_n = \frac{FCF_{norm}(1+g_n)}{WACC - g_n}"
    BRIDGE_FORMULA = r"P = \dfrac{EV - Dette + Cash}{Actions}"

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Inputs spécifiques au modèle FCFF Normalized.

        Collecte :
        - FCF normalisé (moyenne cycle)
        - Horizon de projection
        - Taux de croissance moyen

        Returns
        -------
        Dict[str, Any]
            - manual_fcf_base : FCF normalisé
            - projection_years : Horizon
            - fcf_growth_rate : Croissance
        """
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FCF_NORM}**")
        st.latex(
            r"V_0 = \sum_{t=1}^{n} \frac{FCF_{norm}(1+g)^t}{(1+WACC)^t} + "
            r"\frac{TV_n}{(1+WACC)^n}"
        )

        fcf_base = st.number_input(
            ExpertTerminalTexts.INP_FCF_SMOOTHED,
            value=None,
            format="%.0f",
            help=ExpertTerminalTexts.HELP_FCF_SMOOTHED
        )
        st.divider()

        st.markdown(f"**{ExpertTerminalTexts.SEC_2_PROJ_FUND}**")

        col1, col2 = st.columns(2)

        with col1:
            n_years = widget_projection_years(default=5, key="fcff_norm_years")

        with col2:
            g_rate = widget_growth_rate(
                label=ExpertTerminalTexts.INP_GROWTH_G,
                min_val=-0.20,
                max_val=0.30,
                key="fcff_norm_growth"
            )

        st.divider()

        return {
            "manual_fcf_base": fcf_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
        }
