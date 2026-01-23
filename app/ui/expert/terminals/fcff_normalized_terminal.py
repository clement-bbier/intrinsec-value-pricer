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

from src.models import ValuationMode
from src.i18n import SharedTexts
from ..base_terminal import ExpertTerminalBase
from app.ui.expert.terminals.shared_widgets import (
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
    SHOW_SUBMIT_BUTTON = False

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
        st.markdown(f"**{SharedTexts.SEC_1_FCF_NORM}**")
        st.latex(
            r"V_0 = \sum_{t=1}^{n} \frac{FCF_{norm}(1+g)^t}{(1+WACC)^t} + "
            r"\frac{TV_n}{(1+WACC)^n}"
        )

        fcf_base = st.number_input(
            SharedTexts.INP_FCF_SMOOTHED,
            value=None,
            format="%.0f",
            help=SharedTexts.HELP_FCF_SMOOTHED,
            key=f"{self.MODE.name}_fcf_base"
        )
        st.divider()

        st.markdown(f"**{SharedTexts.SEC_2_PROJ_FUND}**")

        col1, col2 = st.columns(2)

        with col1:
            n_years = widget_projection_years(default=5, key_prefix=self.MODE.name)

        with col2:
            g_rate = widget_growth_rate(
                label=SharedTexts.INP_GROWTH_G,
                min_val=-0.20,
                max_val=0.30,
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
        Extrait les données spécifiques au modèle FCFF Normalized depuis st.session_state.

        Parameters
        ----------
        key_prefix : str
            Préfixe de clé basé sur le mode (FCFF_NORMALIZED).

        Returns
        -------
        Dict[str, Any]
            Données FCFF Normalized : fcf_base, projection_years, growth_rate.
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
