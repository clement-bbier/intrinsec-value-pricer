"""
app/ui/expert_terminals/graham_value_terminal.py

Terminal Expert — Graham Intrinsic Value (1974 Revised Formula)

Cas d'usage : Screening value investing, quick valuation.
Formule : V = EPS × (8.5 + 2g) × 4.4 / Y

Origine : Benjamin Graham, "The Intelligent Investor" (formule révisée 1974)

Notes :
- 8.5 = P/E d'une entreprise sans croissance
- 2g = ajustement pour croissance (g en %)
- 4.4 = rendement AAA historique (1962)
- Y = rendement AAA actuel

Style : Numpy docstrings
"""

from typing import Dict, Any

import streamlit as st

from src.domain.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_peer_triangulation


class GrahamValueTerminal(ExpertTerminalBase):
    """
    Terminal pour la formule de Graham (1974).

    Formule simplifiée pour une estimation rapide de la valeur
    intrinsèque basée sur l'EPS et la croissance attendue.

    Notes
    -----
    Cette formule est un outil de screening, pas une valorisation
    complète. Elle ne prend pas en compte la structure du capital,
    la qualité des actifs, ou les risques spécifiques.

    Attributes
    ----------
    MODE : ValuationMode
        GRAHAM
    DISPLAY_NAME : str
        "Graham Intrinsic Value"
    """

    MODE = ValuationMode.GRAHAM
    DISPLAY_NAME = "Graham Intrinsic Value"
    DESCRIPTION = "Formule de screening value investing (Benjamin Graham 1974)"

    # Graham est un modèle simplifié, moins de sections
    SHOW_DISCOUNT_SECTION = False  # Pas de WACC/Ke explicite
    SHOW_TERMINAL_SECTION = False  # Pas de TV
    SHOW_BRIDGE_SECTION = False    # Valorise directement l'action
    SHOW_MONTE_CARLO = False       # Pas adapté
    SHOW_SCENARIOS = True          # On peut tester différents g
    SHOW_PEER_TRIANGULATION = True

    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Inputs spécifiques à la formule de Graham.

        Collecte :
        - EPS normalisé
        - Taux de croissance long terme (g)
        - Rendement AAA actuel (Y)
        - Taux d'imposition (optionnel)

        Returns
        -------
        Dict[str, Any]
            - manual_fcf_base : EPS (utilisé comme proxy)
            - fcf_growth_rate : Croissance g
            - corporate_aaa_yield : Rendement Y
            - tax_rate : Taux d'imposition
            - projection_years : 1 (formule statique)
        """
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_GRAHAM_BASE}**")
        st.latex(r"V = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}")

        col1, col2 = st.columns(2)

        with col1:
            eps = st.number_input(
                ExpertTerminalTexts.INP_EPS_NORM,
                value=None,
                format="%.2f",
                help=ExpertTerminalTexts.HELP_EPS_NORM
            )

        with col2:
            g_lt = st.number_input(
                "Croissance long terme g (%)",
                min_value=0.0,
                max_value=0.20,
                value=None,
                format="%.3f",
                help=ExpertTerminalTexts.HELP_GROWTH_LT
            )

        st.divider()

        st.markdown(f"**{ExpertTerminalTexts.SEC_2_GRAHAM}**")

        col1, col2 = st.columns(2)

        with col1:
            yield_aaa = st.number_input(
                ExpertTerminalTexts.INP_YIELD_AAA,
                min_value=0.0,
                max_value=0.20,
                value=None,
                format="%.3f",
                help=ExpertTerminalTexts.HELP_YIELD_AAA
            )

        with col2:
            tau = st.number_input(
                "Taux d'imposition effectif",
                min_value=0.0,
                max_value=0.60,
                value=None,
                format="%.2f",
                help=ExpertTerminalTexts.HELP_TAX
            )

        st.divider()

        st.caption(
            "*Formule de Graham : approximation historique. "
            "A utiliser comme screening, pas comme valorisation definitive.*"
        )

        return {
            "manual_fcf_base": eps,
            "fcf_growth_rate": g_lt,
            "corporate_aaa_yield": yield_aaa,
            "tax_rate": tau,
            "projection_years": 1,  # Formule statique
            "enable_monte_carlo": False,
        }
