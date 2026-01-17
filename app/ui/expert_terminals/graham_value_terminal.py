"""
app/ui/expert_terminals/graham_value_terminal.py
Terminal Expert — Graham Number (Value Investing)

Cas d'usage : Screening rapide de valeur intrinsèque.
Formule : V = √(22.5 × EPS × BVPS)
Pas d'actualisation (formule statique).
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase


class GrahamValueTerminal(ExpertTerminalBase):
    """Terminal pour le Graham Number."""
    
    MODE = ValuationMode.GRAHAM
    DISPLAY_NAME = "Graham Number"
    DESCRIPTION = "Formule classique de Benjamin Graham (1974)"
    ICON = ""
    
    # Graham n'utilise pas ces sections
    SHOW_DISCOUNT_SECTION = False
    SHOW_GROWTH_SECTION = False
    SHOW_TERMINAL_SECTION = False
    SHOW_MONTE_CARLO = False
    SHOW_SCENARIOS = False
    
    def render_model_inputs(self) -> Dict[str, Any]:
        """Inputs spécifiques au Graham Number."""
        
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FLOW}**")
        st.latex(r"V = \sqrt{22.5 \times EPS \times BVPS}")
        
        st.caption(
            "Le Graham Number est une formule de screening rapide. "
            "Elle suppose un P/E max de 15 et un P/B max de 1.5 (15 x 1.5 = 22.5)."
        )
        
        st.caption(
            "Note: Cette methode ne convient pas aux entreprises de croissance "
            "ou avec EPS/BVPS negatifs."
        )
        
        col1, col2 = st.columns(2)
        
        manual_eps = col1.number_input(
            "EPS (Bénéfice par action)",
            min_value=-100.0, max_value=500.0, value=None,
            format="%.2f",
            help="Laissez vide pour utiliser le TTM"
        )
        
        manual_bvps = col2.number_input(
            "BVPS (Valeur comptable par action)",
            min_value=0.0, max_value=5000.0, value=None,
            format="%.2f",
            help="Laissez vide pour utiliser le dernier bilan"
        )
        
        st.divider()
        
        return {
            "manual_eps": manual_eps,
            "manual_bvps": manual_bvps,
            "projection_years": 1,  # Non utilisé mais requis
        }
