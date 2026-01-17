"""
app/ui/expert_terminals/fcfe_terminal.py
Terminal Expert — Free Cash Flow to Equity (FCFE)

Cas d'usage : Valorisation directe des fonds propres.
Flux : FCF disponible pour les actionnaires (après dette).
Actualisation : Cost of Equity (Ke).
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_projection_years


class FCFETerminal(ExpertTerminalBase):
    """Terminal pour FCFE."""
    
    MODE = ValuationMode.FCFE
    DISPLAY_NAME = "DCF - Free Cash Flow to Equity"
    DESCRIPTION = "Flux disponibles pour les actionnaires, actualises au Ke"
    ICON = ""
    
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = False
    
    def render_model_inputs(self) -> Dict[str, Any]:
        """Inputs spécifiques FCFE."""
        
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FLOW}**")
        st.latex(r"FCFE = NI + D\&A - CapEx - \Delta WC + \Delta Debt")
        
        st.caption(
            "Le FCFE mesure le cash disponible pour les actionnaires apres "
            "remboursement de la dette. Utilise pour les LBO et entreprises a "
            "structure de capital stable."
        )
        
        years = widget_projection_years(default=5)
        
        st.divider()
        
        return {"projection_years": years}
