"""
app/ui_components/ui_kpis.py

COMPOSANTS UI PARTAGÉS — UTILITAIRES DE FORMATAGE

Rôle : Fournit les utilitaires de formatage et composants atomiques
       partagés entre les différents onglets de résultats.
Pattern : Utility functions + Atomic components
Style : Numpy docstrings

Version : V2.0 — ST-2.2 (Migration ResultTabOrchestrator)
Risques financiers : Aucun calcul, formatage seulement

Dépendances critiques :
- numpy >= 1.21.0
- pandas >= 1.3.0
- streamlit >= 1.28.0

Migration ST-2.2 :
- Ancien : Contenait toute la logique d'affichage des résultats
- Nouveau : Bibliothèque de composants réutilisables seulement

Contenu :
- format_smart_number() : Formatage intelligent des nombres
- atom_kpi_metric() : Composant métrique standardisé
- _render_smart_step() : Carte de preuve mathématique
- atom_audit_card() : Carte d'audit avec badges
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np
import pandas as pd
import streamlit as st

# Standard library
import logging
from typing import Any, List, Optional

# Third-party
import numpy as np
import pandas as pd
import streamlit as st

# Local
from src.domain.models import AuditStep, AuditSeverity, CalculationStep
from app.ui_components.ui_glass_box_registry import get_step_metadata
from core.i18n import KPITexts, AuditTexts


# ==============================================================================
# 0. HELPERS DE FORMATAGE PROFESSIONNEL
# ==============================================================================

def format_smart_number(val: Optional[float], currency: str = "", is_pct: bool = False) -> str:
    """Formatte les nombres pour éviter les coupures UI (Millions, Billions)."""
    if val is None or (isinstance(val, float) and np.isnan(val)): return "—"
    if is_pct: return f"{val:.2%}"

    abs_val = abs(val)
    if abs_val >= 1e12: return f"{val/1e12:,.2f} T {currency}"
    if abs_val >= 1e9:  return f"{val/1e9:,.2f} B {currency}"
    if abs_val >= 1e6:  return f"{val/1e6:,.2f} M {currency}"
    return f"{val:,.2f} {currency}"


# ==============================================================================
# 1. COMPOSANTS ATOMIQUES (UI COMPONENTS)
# ==============================================================================

def atom_kpi_metric(label: str, value: str, help_text: str = "") -> None:
    """Affiche une métrique clé avec le style institutionnel."""
    st.metric(label, value, help=help_text)


def _render_smart_step(index: int, step: CalculationStep) -> None:
    """Carte de preuve mathématique avec lookup prioritaire dans le registre."""
    meta = get_step_metadata(step.step_key)
    label = meta.get("label", step.label) or "Calcul"
    formula = meta.get("formula", step.theoretical_formula)

    with st.container(border=True):
        st.markdown(f"**{KPITexts.STEP_LABEL.format(index=index)} : {label.upper()}**")
        c1, c2, c3 = st.columns([2.5, 4, 1.5])

        with c1:
            st.caption(KPITexts.FORMULA_THEORY)
            if formula and formula != "N/A":
                st.latex(formula)
            else:
                st.markdown(f"*{KPITexts.FORMULA_DATA_SOURCE}*")

        with c2:
            st.caption(KPITexts.APP_NUMERIC)
            if step.numerical_substitution:
                st.code(step.numerical_substitution, language="text")
            else:
                st.divider()

        with c3:
            st.caption(KPITexts.VALUE_UNIT.format(unit=meta.get("unit", "")))
            st.markdown(f"### {step.result:,.2f}")

        if step.interpretation:
            st.divider()
            st.caption(f"ANALYSIS : {step.interpretation}")


def atom_audit_card(step: AuditStep) -> None:
    """Carte d'Audit Glass Box Professionnelle sans emojis."""
    meta = get_step_metadata(step.step_key)
    color = "#28a745" if step.verdict else ("#fd7e14" if step.severity == AuditSeverity.WARNING else "#dc3545")
    status = AuditTexts.STATUS_OK if step.verdict else AuditTexts.STATUS_ALERT

    with st.container(border=True):
        h_left, h_right = st.columns([0.7, 0.3])
        with h_left:
            st.markdown(f"**{meta.get('label', step.label).upper()}**")
            st.caption(meta.get('description', ""))
        with h_right:
            badge_html = f"""<div style="text-align:right;"><span style="color:{color}; border:1px solid {color}; 
            padding:2px 10px; border-radius:4px; font-weight:bold; font-size:12px;">{status.upper()}</span></div>"""
            st.markdown(badge_html, unsafe_allow_html=True)

        st.divider()
        st.info(f"**{step.evidence}**")


# ==============================================================================
# 2. NAVIGATION ET AGGREGATION (ORCHESTRATION COMPLÈTE V13.0)
# ==============================================================================

# Fonction déplacée vers app/ui/result_tabs/orchestrator.py (ResultTabOrchestrator)


# ==============================================================================
# 3. RENDU DES ONGLETS INDIVIDUELS
# ==============================================================================

# Fonction déplacée vers app/ui/result_tabs/core/inputs_summary.py


# Fonction déplacée vers app/ui/result_tabs/optional/peer_multiples.py


# Fonction déplacée vers app/ui/result_tabs/optional/sotp_breakdown.py


# Fonction déplacée vers app/ui/result_tabs/optional/scenario_analysis.py


# Fonction déplacée vers app/ui/result_tabs/optional/historical_backtest.py


# ==============================================================================
# 4. AUDIT ET MONTE CARLO
# ==============================================================================

# Fonction déplacée vers app/ui/result_tabs/core/audit_report.py


# Fonction déplacée vers app/ui/result_tabs/optional/monte_carlo_distribution.py


# ==============================================================================
# 5. WRAPPERS DE SYNTHÈSE
# ==============================================================================

# Fonction déplacée vers app/ui/result_tabs/core/executive_summary.py
