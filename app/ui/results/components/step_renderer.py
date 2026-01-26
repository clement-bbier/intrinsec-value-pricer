"""
app/ui/results/components/step_renderer.py
RENDU DES ÉTAPES DE CALCUL (Glass Box) — Standard Institutionnel.
"""

from __future__ import annotations
from typing import Dict

import streamlit as st

from src.models import CalculationStep, VariableInfo, VariableSource
from src.i18n import KPITexts, CommonTexts, AuditTexts
from src.utilities.formatting import format_smart_number
from app.ui.components.ui_glass_box_registry import get_step_metadata

# ============================================================================
# CONFIGURATION DES THÈMES DE COULEURS (PROVENANCE INSTITUTIONNELLE)
# ============================================================================

# Mapping des couleurs hexadécimales pour les badges HTML
SOURCE_COLORS: Dict[VariableSource, str] = {
    VariableSource.YAHOO_FINANCE: "#10b981",  # Vert (Audité)
    VariableSource.MACRO_PROVIDER: "#3b82f6", # Bleu (Macro)
    VariableSource.CALCULATED: "#64748b",     # Gris (Déterminé)
    VariableSource.MANUAL_OVERRIDE: "#f59e0b",# Orange (Ajusté)
    VariableSource.DEFAULT: "#64748b",
}

def _render_status_badge(label: str, source: VariableSource) -> str:
    """Génère le composant HTML pour un badge de statut professionnel."""
    color = SOURCE_COLORS.get(source, "#64748b")
    return f"""
    <div style='text-align: right;'>
        <span style='
            background-color: {color}20; 
            color: {color}; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-size: 0.75rem; 
            font-weight: 700; 
            border: 1px solid {color}40;
            letter-spacing: 0.5px;
        '>
            {label.upper()}
        </span>
    </div>
    """

def _render_variable_details(variables_map: Dict[str, VariableInfo]) -> None:
    """Affiche le référentiel des variables avec couleurs institutionnelles."""
    if not variables_map:
        return

    for symbol, var in variables_map.items():
        color_hex = SOURCE_COLORS.get(var.source, "#64748b")

        col_sym, col_val, col_src = st.columns([1, 2, 3])
        col_sym.markdown(f"<b style='color:{color_hex}'>{symbol}</b>", unsafe_allow_html=True)
        col_val.markdown(f"`{var.formatted_value}`")

        # Source stylisée avec le label i18n
        col_src.markdown(
            f"<span style='color:{color_hex}; font-size:0.8rem; font-weight:600;'>"
            f"{CommonTexts.DATA_ORIGIN_LABEL} : {var.source.value.upper()}"
            f"</span>",
            unsafe_allow_html=True
        )

        if var.is_overridden and var.original_value is not None:
            st.caption(f"└ {CommonTexts.AUTO_VALUE_IGNORED} : {var.original_value:,.4f}")


@st.fragment
def render_calculation_step(index: int, step: CalculationStep) -> None:
    """Rendu d'une étape de calcul Glass Box avec badges stylisés."""

    # 1. Extraction des métadonnées centralisées (Label et Formule)
    meta = get_step_metadata(step.step_key)
    label = meta.get("label", step.label) or CommonTexts.STEP_GENERIC_LABEL
    formula = meta.get("formula", step.theoretical_formula)

    # 2. Logique de détermination du statut et de la couleur
    if step.has_overrides():
        status_label = CommonTexts.STATUS_ADJUSTED
        status_src = VariableSource.MANUAL_OVERRIDE
    elif any(v.source == VariableSource.YAHOO_FINANCE for v in step.variables_map.values()):
        status_label = CommonTexts.STATUS_AUDITED
        status_src = VariableSource.YAHOO_FINANCE
    else:
        status_label = CommonTexts.STATUS_CALCULATED
        status_src = VariableSource.CALCULATED

    # 3. Rendu du Container principal
    with st.container(border=True):
        # Header : Index | LABEL | BADGE
        h_left, h_right = st.columns([4, 1.5])
        h_left.markdown(f"**{KPITexts.STEP_LABEL.format(index=index)} : {label.upper()}**")
        # Correction du bug d'affichage : Utilisation du badge HTML
        h_right.markdown(_render_status_badge(status_label, status_src), unsafe_allow_html=True)

        st.divider()

        # Corps Mathématique : Théorie | Substitution | Résultat
        c_theory, c_subst, c_result = st.columns([3, 4, 2])

        with c_theory:
            st.caption(KPITexts.FORMULA_THEORY)
            if formula and formula != "N/A":
                st.latex(formula)
            else:
                st.markdown(f"*{AuditTexts.DEFAULT_FORMULA}*")

        with c_subst:
            st.caption(KPITexts.APP_NUMERIC)
            # Priorité au calcul réel effectué si disponible
            display_val = step.actual_calculation or step.numerical_substitution
            if display_val:
                st.code(display_val, language="text", wrap_lines=True)

        with c_result:
            unit_label = KPITexts.VALUE_UNIT.format(unit=step.unit or "")
            st.caption(unit_label)
            if step.result is not None:
                formatted_res = format_smart_number(step.result, decimals=2)
                st.subheader(formatted_res)

        # 4. Footer : Transparence des données (Source & Commentaire)
        if step.variables_map or step.interpretation:
            st.divider()
            # Expand par défaut si l'étape a été modifiée par l'analyste
            is_expanded = step.has_overrides()

            with st.expander(CommonTexts.DATA_ORIGIN_LABEL, expanded=is_expanded):
                if step.variables_map:
                    _render_variable_details(step.variables_map)

                if step.interpretation:
                    if step.variables_map: st.divider()
                    st.caption(CommonTexts.INTERPRETATION_LABEL)
                    # Utilisation du composant Info sans icône pour un style épuré
                    st.info(step.interpretation, icon=None)