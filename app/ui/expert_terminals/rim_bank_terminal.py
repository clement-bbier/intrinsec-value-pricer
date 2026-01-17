"""
app/ui/expert_terminals/rim_bank_terminal.py
Terminal Expert — Residual Income Model (RIM)

Cas d'usage : Institutions financières (banques, assurances).
Modèle : Ohlson / Edwards-Bell-Ohlson
Actualisation : Cost of Equity (Ke)
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_projection_years


class RIMBankTerminal(ExpertTerminalBase):
    """Terminal pour le Residual Income Model (banques)."""
    
    MODE = ValuationMode.RIM
    DISPLAY_NAME = "Residual Income Model"
    DESCRIPTION = "Valorisation par les profits residuels - Institutions financieres"
    ICON = ""
    
    SHOW_MONTE_CARLO = False  # Moins pertinent pour RIM
    SHOW_SCENARIOS = False
    SHOW_TERMINAL_SECTION = False  # Terminal implicite dans RIM
    
    def render_model_inputs(self) -> Dict[str, Any]:
        """Inputs spécifiques RIM."""
        
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FLOW}**")
        st.latex(r"V_0 = BV_0 + \sum_{t=1}^{\infty} \frac{RI_t}{(1+k_e)^t}")
        st.latex(r"RI_t = NI_t - k_e \times BV_{t-1}")
        
        st.caption(
            "Modele specialise pour les banques et assurances. "
            "Le FCFF n'est pas pertinent pour les institutions financieres "
            "car leur dette est un outil operationnel, pas de financement."
        )
        
        col1, col2 = st.columns(2)
        
        years = col1.number_input(
            ExpertTerminalTexts.INP_PROJ_YEARS,
            min_value=3, max_value=15, value=5
        )
        
        target_roe = col2.number_input(
            "ROE cible (%)",
            min_value=0.0, max_value=0.25, value=None,
            format="%.3f",
            help="Return on Equity à maturité (vide = historique)"
        )
        
        payout = st.number_input(
            "Taux de distribution (Payout)",
            min_value=0.0, max_value=1.0, value=None,
            format="%.2f",
            help="Dividendes / Résultat Net (vide = auto)"
        )
        
        st.divider()
        
        return {
            "projection_years": years,
            "target_roe": target_roe,
            "payout_ratio": payout,
        }
