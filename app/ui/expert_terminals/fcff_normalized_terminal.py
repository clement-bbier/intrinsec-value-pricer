"""
app/ui/expert_terminals/fcff_normalized_terminal.py
Terminal Expert — FCFF Normalized (Fundamental)

Cas d'usage : Entreprises cycliques avec FCF volatil.
Spécificité : Lissage du FCF sur plusieurs années.
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_peer_multiples


class FCFFNormalizedTerminal(ExpertTerminalBase):
    """Terminal pour FCFF avec normalisation."""
    
    MODE = ValuationMode.FCFF_NORMALIZED
    DISPLAY_NAME = "FCFF Normalise"
    DESCRIPTION = "DCF avec lissage du FCF pour les entreprises cycliques"
    ICON = ""
    
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    
    def render_model_inputs(self) -> Dict[str, Any]:
        """Inputs avec option de lissage."""
        
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FLOW}**")
        st.latex(r"FCF_{norm} = \frac{1}{n}\sum_{i=1}^{n} FCF_i")
        
        st.caption(
            "Le FCF normalise lisse les variations cycliques en moyennant "
            "les flux sur plusieurs annees historiques."
        )
        
        col1, col2 = st.columns(2)
        
        years = col1.number_input(
            ExpertTerminalTexts.INP_PROJ_YEARS,
            min_value=1, max_value=15, value=5
        )
        
        smoothing = col2.number_input(
            "Années de lissage",
            min_value=1, max_value=5, value=3,
            help="Nombre d'années pour moyenner le FCF historique"
        )
        
        multiples_config = widget_peer_multiples()
        
        st.divider()
        
        return {
            "projection_years": years,
            "smoothing_years": smoothing,
            **multiples_config,
        }
