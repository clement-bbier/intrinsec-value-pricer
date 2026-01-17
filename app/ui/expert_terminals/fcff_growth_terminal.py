"""
app/ui/expert_terminals/fcff_growth_terminal.py
Terminal Expert — FCFF Revenue-Driven (Growth)

Cas d'usage : Entreprises en croissance (start-ups matures, tech).
Spécificité : Modélisation par les revenus avec convergence des marges.
"""

from typing import Dict, Any

import streamlit as st

from core.models import ValuationMode
from core.i18n import ExpertTerminalTexts
from app.ui.base import ExpertTerminalBase
from app.ui.expert_terminals.shared_widgets import widget_peer_multiples


class FCFFGrowthTerminal(ExpertTerminalBase):
    """Terminal pour valorisation Revenue-Driven."""
    
    MODE = ValuationMode.FCFF_GROWTH
    DISPLAY_NAME = "DCF - Revenue-Driven Growth"
    DESCRIPTION = "Valorisation par les revenus avec convergence des marges vers maturite"
    ICON = ""
    
    SHOW_MONTE_CARLO = True
    SHOW_SCENARIOS = True
    
    def render_model_inputs(self) -> Dict[str, Any]:
        """Inputs centrés sur les revenus et marges."""
        
        st.markdown(f"**{ExpertTerminalTexts.SEC_1_FLOW}**")
        st.latex(r"FCF_t = Revenue_t \times Marge_{FCF,t} \times (1 - Reinv\_rate)")
        
        st.caption(
            "Modele adapte aux entreprises ou le FCF actuel n'est pas "
            "representatif de la capacite beneficiaire a maturite."
        )
        
        years = st.number_input(
            ExpertTerminalTexts.INP_PROJ_YEARS,
            min_value=3, max_value=15, value=7,
            help="Horizon plus long pour les growth stocks"
        )
        
        st.markdown("**Hypotheses de Marge**")
        col1, col2 = st.columns(2)
        
        current_margin = col1.number_input(
            "Marge FCF actuelle",
            min_value=-0.50, max_value=0.40, value=None,
            format="%.2f",
            help="Marge actuelle (vide = calculée)"
        )
        
        target_margin = col2.number_input(
            "Marge FCF cible (maturité)",
            min_value=0.05, max_value=0.40, value=0.15,
            format="%.2f",
            help="Marge attendue à maturité"
        )
        
        convergence = st.slider(
            "Années de convergence",
            min_value=3, max_value=15, value=7,
            help="Durée pour atteindre la marge cible"
        )
        
        multiples_config = widget_peer_multiples()
        
        st.divider()
        
        return {
            "projection_years": years,
            "current_fcf_margin": current_margin,
            "target_fcf_margin": target_margin,
            "margin_convergence_years": convergence,
            **multiples_config,
        }
    
    def render_growth_assumptions(self) -> Dict[str, Any]:
        """Croissance des revenus."""
        st.markdown(f"**{ExpertTerminalTexts.SEC_4_GROWTH}**")
        
        col1, col2 = st.columns(2)
        
        rev_growth = col1.number_input(
            "Croissance CA Phase 1",
            min_value=-0.10, max_value=0.50, value=None,
            format="%.3f",
            help="Croissance annuelle des revenus (vide = historique)"
        )
        
        perpetual = col2.number_input(
            ExpertTerminalTexts.INP_PERP_G,
            min_value=0.0, max_value=0.04, value=0.02,
            format="%.3f"
        )
        
        st.divider()
        return {"revenue_growth_rate": rev_growth, "perpetual_growth_rate": perpetual}
