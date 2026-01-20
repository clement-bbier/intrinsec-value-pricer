"""
app/ui/result_tabs/components/step_renderer.py

RENDU DES ÉTAPES DE CALCUL (Glass Box).

Rendu des étapes - Visualisation fiable
Pattern : Component Renderer
Style : Numpy docstrings

ST-3.3 : VISUALISATION DE LA FIABILITÉ
========================================
Chaque étape affiche :
- Un badge de confiance coloré (Vert/Orange/Rouge)
- L'interaction "Source" pour voir la provenance des variables
- Le détail des surcharges manuelles vs données automatiques

Financial Impact:
    La transparence sur la source des données permet à l'analyste
    de calibrer sa confiance dans le résultat final.
"""

from __future__ import annotations

from typing import Dict

import streamlit as st

from src.models import CalculationStep, VariableInfo, VariableSource
from src.i18n import KPITexts
from app.ui.components.ui_glass_box_registry import get_step_metadata


# ============================================================================
# CONSTANTES DE STYLE (ST-3.3)
# ============================================================================

# Mapping source → couleur de badge
SOURCE_BADGE_COLORS: Dict[VariableSource, str] = {
    VariableSource.YAHOO_FINANCE: "#2E7D32",   # Vert — Donnée Certifiée
    VariableSource.MACRO_PROVIDER: "#1565C0",  # Bleu — Donnée Macro
    VariableSource.CALCULATED: "#455A64",       # Gris — Calculé
    VariableSource.MANUAL_OVERRIDE: "#FF6F00", # Orange — Manuel
    VariableSource.DEFAULT: "#9E9E9E",          # Gris clair — Défaut
}

# Labels de confiance
CONFIDENCE_LABELS: Dict[str, str] = {
    "certified": "Certifié",
    "calculated": "Calculé",
    "estimated": "Estimé",
    "manual": "Manuel",
}


def _get_confidence_badge(step: CalculationStep) -> tuple[str, str, str]:
    """
    Détermine le badge de confiance à afficher pour une étape.
    
    Parameters
    ----------
    step : CalculationStep
        L'étape à analyser.
    
    Returns
    -------
    tuple[str, str, str]
        (couleur_hex, emoji, label) du badge.
    
    Notes
    -----
    Logique de scoring :
    - Si toutes les variables viennent de Yahoo Finance → Vert (Certifié)
    - Si mix avec calculs → Bleu (Calculé)
    - Si surcharges manuelles présentes → Orange (Manuel/Estimé)
    - Si données par défaut → Rouge (Défaut)
    """
    if not step.variables_map:
        return "#9E9E9E", "◯", "—"
    
    sources = [v.source for v in step.variables_map.values()]
    has_override = step.has_overrides()
    
    # Priorité aux surcharges manuelles
    if has_override:
        return "#FF6F00", "◐", CONFIDENCE_LABELS["manual"]
    
    # Vérifier si toutes les sources sont certifiées
    certified_sources = {VariableSource.YAHOO_FINANCE, VariableSource.MACRO_PROVIDER}
    if all(s in certified_sources for s in sources):
        return "#2E7D32", "●", CONFIDENCE_LABELS["certified"]
    
    # Mix de sources
    if VariableSource.DEFAULT in sources:
        return "#9E9E9E", "◌", CONFIDENCE_LABELS["estimated"]
    
    return "#455A64", "◐", CONFIDENCE_LABELS["calculated"]


def _render_variable_details(variables_map: Dict[str, VariableInfo]) -> None:
    """
    Affiche le détail des variables avec leur provenance (ST-3.3).
    
    Parameters
    ----------
    variables_map : Dict[str, VariableInfo]
        Dictionnaire des variables de l'étape.
    """
    if not variables_map:
        st.caption("*Aucune variable traçable*")
        return
    
    for symbol, var_info in variables_map.items():
        color = SOURCE_BADGE_COLORS.get(var_info.source, "#9E9E9E")
        
        # Badge coloré + symbole + valeur + source
        override_indicator = ""
        
        st.markdown(
            f"<span style='color:{color}; font-weight:600;'>●</span> "
            f"**{symbol}** = {var_info.formatted_value} "
            f"<span style='color:#757575; font-size:0.85em;'>— {var_info.source.value}{override_indicator}</span>",
            unsafe_allow_html=True
        )
        
        # Si surchargé, afficher la valeur originale
        if var_info.is_overridden and var_info.original_value is not None:
            st.caption(
                f"↳ Valeur auto : {var_info.original_value:.4f}"
            )


@st.fragment
def render_calculation_step(index: int, step: CalculationStep) -> None:
    """
    Affiche une étape de calcul avec formule, application numérique et badges.
    
    ST-3.3 : Inclut les badges de confiance et l'interaction Source.
    
    Parameters
    ----------
    index : int
        Numéro de l'étape (1-based).
    step : CalculationStep
        L'étape à afficher.
    
    Financial Impact
    ----------------
    L'affichage de la provenance permet à l'analyste de calibrer
    sa confiance dans chaque composante du calcul.
    """
    # Récupérer les métadonnées enrichies du registre
    meta = get_step_metadata(step.step_key)
    label = meta.get("label", step.label) or "Calcul"
    formula = meta.get("formula", step.theoretical_formula)
    
    # Badge de confiance (ST-3.3)
    badge_color, badge_icon, badge_label = _get_confidence_badge(step)
    
    with st.container(border=True):
        # Header avec badge de confiance
        header_col1, header_col2 = st.columns([6, 2])
        
        with header_col1:
            st.markdown(
                f"**{KPITexts.STEP_LABEL.format(index=index)} : {label.upper()}**"
            )
        
        with header_col2:
            # Badge de confiance aligné à droite
            st.markdown(
                f"<div style='text-align:right;'>"
                f"<span style='background-color:{badge_color}; color:white; "
                f"padding:2px 8px; border-radius:4px; font-size:0.75em;'>"
                f"{badge_icon} {badge_label}</span></div>",
                unsafe_allow_html=True
            )
        
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
            # Priorité à actual_calculation (ST-2.1), fallback sur numerical_substitution
            calc_display = step.actual_calculation or step.numerical_substitution
            if calc_display:
                if len(calc_display) > 80:
                    st.markdown(
                        f"<div style='font-size: 0.85em; font-family: monospace; "
                        f"white-space: pre-wrap;'>{calc_display}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.code(calc_display, language="text")
            else:
                st.markdown("*—*")
        
        with col3:
            st.caption("Résultat")
            if step.result is not None:
                unit_display = f" {step.unit}" if step.unit else ""
                st.markdown(f"**{step.result:,.2f}{unit_display}**")
            else:
                st.markdown("*—*")
        
        # Section interactive : Détails des variables (ST-3.3)
        if step.variables_map:
            with st.expander("📊 Détails des variables", expanded=False):
                _render_variable_details(step.variables_map)
                
                # Interprétation pédagogique si disponible
                if step.interpretation:
                    st.divider()
                    st.markdown(f"*💡 {step.interpretation}*")
