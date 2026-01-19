"""
app/ui/result_tabs/core/calculation_proof.py
Onglet — Preuve de Calcul (Glass Box)

Affiche chaque étape du calcul avec :
- Formule théorique (LaTeX)
- Application numérique
- Résultat intermédiaire
"""

from typing import Any, List

import streamlit as st

from src.domain.models import ValuationResult, CalculationStep
from src.i18n import KPITexts, UIMessages
from app.ui.base import ResultTabBase
from app.ui.results.components.step_renderer import render_calculation_step


class CalculationProofTab(ResultTabBase):
    """Onglet de preuve de calcul Glass Box."""
    
    TAB_ID = "calculation_proof"
    LABEL = "Preuve de Calcul"
    ICON = ""
    ORDER = 2
    IS_CORE = True
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche les étapes de calcul."""
        
        # Séparer les étapes core des étapes Monte Carlo
        core_steps = [s for s in result.calculation_trace if not s.step_key.startswith("MC_")]
        
        if not core_steps:
            st.info(UIMessages.NO_CALCULATION_STEPS)
            return
        
        st.markdown(f"**{KPITexts.TAB_CALC}**")
        st.caption(
            "Chaque étape montre la formule théorique et son application numérique. "
            "Cette transparence permet de vérifier et comprendre le résultat."
        )
        
        # Rendre chaque étape
        for idx, step in enumerate(core_steps, start=1):
            render_calculation_step(idx, step)
