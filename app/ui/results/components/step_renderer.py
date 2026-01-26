"""
app/ui/results/components/step_renderer.py
RENDU DES ÉTAPES DE CALCUL (Glass Box) — Standard Institutionnel.
Architecture : Composants UI Atomiques / SOLID
"""

from __future__ import annotations
from typing import Dict

import streamlit as st

from src.models import CalculationStep, VariableInfo, VariableSource
from src.i18n import KPITexts, CommonTexts
from src.utilities.formatting import format_smart_number
from app.ui.components.ui_glass_box_registry import get_step_metadata

# ============================================================================
# CONSTANTES DE COULEURS (PROVENANCE INSTITUTIONNELLE)
# ============================================================================

SOURCE_THEMES: Dict[VariableSource, str] = {
    VariableSource.YAHOO_FINANCE: "green",
    VariableSource.MACRO_PROVIDER: "blue",
    VariableSource.CALCULATED: "gray",
    VariableSource.MANUAL_OVERRIDE: "orange",
    VariableSource.DEFAULT: "gray",
}

def _render_variable_details(variables_map: Dict[str, VariableInfo]) -> None:
    """Affiche le référentiel des variables utilisées dans l'équation."""
    if not variables_map:
        return

    # Utilisation d'un petit tableau pour la clarté institutionnelle
    for symbol, var in variables_map.items():
        theme = SOURCE_THEMES.get(var.source, "gray")

        # Ligne de variable : Symbole | Valeur | Source
        col_sym, col_val, col_src = st.columns([1, 2, 3])
        col_sym.markdown(f":{theme}[**{symbol}**]")
        col_val.markdown(f"`{var.formatted_value}`")
        col_src.caption(f"Source : {var.source.value.upper()}")

        if var.is_overridden and var.original_value is not None:
            st.caption(f"└ {CommonTexts.AUTO_VALUE_IGNORED} : {var.original_value:,.4f}")


@st.fragment
def render_calculation_step(index: int, step: CalculationStep) -> None:
    """
    Rendu d'une étape de calcul Glass Box.
    Structure : Container > Columns > Divider > Expander
    """
    # 1. Préparation des métadonnées Registry
    meta = get_step_metadata(step.step_key)
    label = meta.get("label", step.label) or CommonTexts.STEP_GENERIC_LABEL
    formula = meta.get("formula", step.theoretical_formula)

    # 2. Détermination du statut institutionnel
    if step.has_overrides():
        status_label = CommonTexts.STATUS_ADJUSTED
        status_color = SOURCE_THEMES[VariableSource.MANUAL_OVERRIDE]
    elif any(v.source == VariableSource.YAHOO_FINANCE for v in step.variables_map.values()):
        status_label = CommonTexts.STATUS_AUDITED
        status_color = SOURCE_THEMES[VariableSource.YAHOO_FINANCE]
    else:
        status_label = CommonTexts.STATUS_CALCULATED
        status_color = SOURCE_THEMES[VariableSource.CALCULATED]

    # 3. Rendu Visuel
    with st.container(border=True):
        # En-tête : Index. LABEL | STATUT
        h_left, h_right = st.columns([4, 1])
        h_left.markdown(f"**{KPITexts.STEP_LABEL.format(index=index)} : {label.upper()}**")
        h_right.markdown(f"<div style='text-align:right;'><small>:{status_color}[{status_label}]</small></div>", unsafe_allow_html=True)

        st.divider()

        # Corps de la Trace Mathématique
        c_theory, c_subst, c_result = st.columns([3, 4, 2])

        with c_theory:
            st.caption(KPITexts.FORMULA_THEORY)
            if formula and formula != "N/A":
                # Rendu LaTeX centré
                st.latex(formula)

        with c_subst:
            st.caption(KPITexts.APP_NUMERIC)
            display_val = step.actual_calculation or step.numerical_substitution
            if display_val:
                st.code(display_val, language="text", wrap_lines=True)

        with c_result:
            # Gestion de l'unité dynamique via i18n V21
            unit_label = KPITexts.VALUE_UNIT.format(unit=step.unit or "")
            st.caption(unit_label)

            if step.result is not None:
                # Utilisation du formatage intelligent centralisé
                formatted_res = format_smart_number(step.result, decimals=2)
                st.subheader(formatted_res)

        # 4. Footer : Glass Box Details (Variables & Interpretation)
        if step.variables_map or step.interpretation:
            st.divider()
            # On n'ouvre l'expander par défaut que si c'est une étape ajustée (Audit)
            is_expanded = step.has_overrides()

            with st.expander(CommonTexts.DATA_ORIGIN_LABEL, expanded=is_expanded):
                if step.variables_map:
                    _render_variable_details(step.variables_map)

                if step.interpretation:
                    if step.variables_map: st.divider()
                    st.caption(CommonTexts.INTERPRETATION_LABEL)
                    st.info(step.interpretation, icon=None)