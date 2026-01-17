"""
app/ui/expert_terminals/ddm_terminal.py
Terminal Expert — Dividend Discount Model (DDM)

Cas d'usage : Entreprises matures avec dividendes stables et prévisibles.
Flux : Dividendes par action (DPS)
Actualisation : Cost of Equity (Ke)
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_projection_years


class DDMTerminal(ExpertTerminalBase):
    """Terminal pour le Dividend Discount Model."""
    
    MODE = ValuationMode.DDM
    DISPLAY_NAME = "Dividend Discount Model"
    DESCRIPTION = "Valorisation par les dividendes futurs actualises au Ke"
    ICON = ""
    
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = False  # Moins pertinent pour DDM
    
    def render_model_inputs(self) -> Dict[str, Any]:
        """Inputs spécifiques au modèle DDM."""
        
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FLOW}**")
        st.latex(r"P_0 = \sum_{t=1}^{n} \frac{D_t}{(1+k_e)^t} + \frac{D_{n+1}}{(k_e - g)(1+k_e)^n}")
        
        st.caption(
            "Le DDM est adapte aux entreprises avec une politique de "
            "dividendes stable (utilities, banques matures, REITs)."
        )
        
        col1, col2 = st.columns(2)
        
        years = col1.number_input(
            ExpertTerminalTexts.INP_PROJ_YEARS,
            min_value=1, max_value=15, value=5,
            help="Horizon avant le terminal"
        )
        
        div_growth = col2.number_input(
            ExpertTerminalTexts.INP_DIV_GROWTH,
            min_value=-0.10, max_value=0.20, value=None,
            format="%.3f",
            help="Croissance des dividendes Phase 1 (vide = auto)"
        )
        
        manual_dps = st.number_input(
            "Dividende par action (DPS) manuel",
            min_value=0.0, max_value=500.0, value=None,
            format="%.2f",
            help="Laissez vide pour utiliser le dernier dividende déclaré"
        )
        
        st.divider()
        
        return {
            "projection_years": years,
            "dividend_growth_rate": div_growth,
            "manual_dividend": manual_dps,
        }
    
    def render_growth_assumptions(self) -> Dict[str, Any]:
        """Croissance spécifique aux dividendes."""
        st.markdown(f"**{ExpertTerminalTexts.SEC_4_GROWTH}**")
        
        perpetual = st.number_input(
            "Croissance perpétuelle des dividendes (g)",
            min_value=0.0, max_value=0.04, value=0.02,
            format="%.3f",
            help="Doit être ≤ croissance PIB nominal long terme"
        )
        
        st.divider()
        return {"perpetual_growth_rate": perpetual}
