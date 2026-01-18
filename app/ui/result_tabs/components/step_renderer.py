"""
app/ui/result_tabs/components/step_renderer.py
Rendu des étapes de calcul (Glass Box).
"""

import streamlit as st

from core.models import CalculationStep
from core.i18n import KPITexts
from app.ui_components.ui_glass_box_registry import get_step_metadata


def render_calculation_step(index: int, step: CalculationStep) -> None:
    """
    Affiche une étape de calcul avec formule et application numérique.
    
    Parameters
    ----------
    index : int
        Numéro de l'étape (1-based).
    step : CalculationStep
        L'étape à afficher.
    """
    # Récupérer les métadonnées enrichies du registre
    meta = get_step_metadata(step.step_key)
    label = meta.get("label", step.label) or "Calcul"
    formula = meta.get("formula", step.theoretical_formula)
    
    with st.container(border=True):
        # Header
        st.markdown(f"**{KPITexts.STEP_LABEL.format(index=index)} : {label.upper()}**")
        
        # Trois colonnes : Formule | Application | Résultat
        col1, col2, col3 = st.columns([2.5, 4, 1.5])
        
        with col1:
            st.caption(KPITexts.FORMULA_THEORY)
            if formula and formula != "N/A":
                st.latex(formula)
            else:
                st.markdown(f"*{KPITexts.FORMULA_DATA_SOURCE}*")
        
        with col2:
            st.caption(KPITexts.APP_NUMERIC)
            if step.numerical_substitution:
                # Améliorer l'affichage des substitutions longues
                if len(step.numerical_substitution) > 80:
                    # Pour les longues substitutions, utiliser une police plus petite
                    st.markdown(f"<div style='font-size: 0.85em; font-family: monospace; white-space: pre-wrap;'>{step.numerical_substitution}</div>", unsafe_allow_html=True)
                else:
                    st.code(step.numerical_substitution, language="text")
            else:
                st.markdown("*—*")
        
        with col3:
            st.caption("Résultat")
            if step.result is not None:
                st.markdown(f"**{step.result:,.2f}**")
            else:
                st.markdown("*—*")
