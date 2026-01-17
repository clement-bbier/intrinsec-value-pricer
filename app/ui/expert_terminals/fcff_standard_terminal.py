"""
app/ui/expert_terminals/fcff_standard_terminal.py
Terminal Expert — FCFF Two-Stage Standard

Cas d'usage : Entreprises matures avec FCF positif et stable.
Flux : Free Cash Flow to Firm (avant service de la dette)
Actualisation : WACC
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_projection_years, widget_peer_multiples


class FCFFStandardTerminal(ExpertTerminalBase):
    """Terminal pour la valorisation FCFF Two-Stage classique."""
    
    MODE = ValuationMode.FCFF_STANDARD
    DISPLAY_NAME = "DCF - Free Cash Flow to Firm"
    DESCRIPTION = "DCF classique : flux actualises au WACC puis valeur terminale"
    ICON = ""
    
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    
    def render_model_inputs(self) -> Dict[str, Any]:
        """Inputs spécifiques au modèle FCFF Standard."""
        
        # Formule affichée
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FLOW}**")
        st.latex(r"FCF = EBIT(1-\tau) + D\&A - CapEx - \Delta WC")
        
        st.caption(
            "Le FCF est calcule automatiquement a partir des etats financiers. "
            "Vous pouvez ajuster les hypotheses de croissance ci-dessous."
        )
        
        # Horizon de projection
        years = widget_projection_years(default=5)
        
        # Option multiples
        multiples_config = widget_peer_multiples()
        
        st.divider()
        
        return {
            "projection_years": years,
            **multiples_config,
        }
