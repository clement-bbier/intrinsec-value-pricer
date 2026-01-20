"""
app/ui_components/ui_kpis.py

COMPOSANTS UI PARTAGÉS — UTILITAIRES DE FORMATAGE

Rôle : Fournit les utilitaires de formatage et composants atomiques
       partagés entre les différents onglets de résultats.
Pattern : Utility functions + Atomic components
Style : Numpy docstrings

Migration vers ResultTabOrchestrator
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

# Standard library
from typing import List, Optional

# Third-party
import numpy as np
import streamlit as st

# Local
from src.models import AuditStep, AuditSeverity, CalculationStep
from app.ui.components.ui_glass_box_registry import get_step_metadata
from src.i18n import KPITexts, AuditTexts


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


# ==============================================================================
# 6. BANDEAUX D'ALERTE (ST-4.1)
# ==============================================================================

def render_degraded_mode_banner(
    reason: str,
    fallback_sources: List[str],
    confidence_score: float
) -> None:
    """
    Affiche un bandeau d'avertissement permanent pour le mode dégradé (ST-4.1).
    
    Parameters
    ----------
    reason : str
        Raison du passage en mode dégradé.
    fallback_sources : List[str]
        Liste des sources de fallback utilisées.
    confidence_score : float
        Score de confiance global (0-1).
    
    Notes
    -----
    Ce bandeau garantit la transparence envers l'utilisateur sur
    la source des données utilisées pour la valorisation.
    
    Financial Impact
    ----------------
    La signalétique claire permet à l'analyste de calibrer
    sa confiance dans les résultats de valorisation.
    
    Examples
    --------
    >>> if provider.is_degraded_mode():
    ...     info = provider.get_degraded_mode_info()
    ...     render_degraded_mode_banner(
    ...         reason=info["reason"],
    ...         fallback_sources=info["fallback_sources"],
    ...         confidence_score=info["confidence_score"]
    ...     )
    """
    # Couleur selon le score de confiance
    if confidence_score >= 0.8:
        color = "#1565C0"  # Bleu — Mineur
    elif confidence_score >= 0.6:
        color = "#FF6F00"  # Orange — Attention
    else:
        color = "#C62828"  # Rouge — Critique
    
    # Construction du message
    sources_text = ", ".join(fallback_sources) if fallback_sources else "Données de secours"
    confidence_pct = f"{confidence_score:.0%}"
    
    banner_html = f"""
    <div style="
        background-color: {color}10;
        border-left: 4px solid {color};
        padding: 12px 16px;
        margin-bottom: 16px;
        border-radius: 4px;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.2em;">{icon}</span>
            <strong style="color: {color};">MODE DÉGRADÉ</strong>
            <span style="
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.75em;
                margin-left: auto;
            ">Confiance: {confidence_pct}</span>
        </div>
        <p style="margin: 8px 0 4px 0; color: #424242; font-size: 0.9em;">
            <strong>Raison :</strong> {reason}
        </p>
        <p style="margin: 0; color: #616161; font-size: 0.85em;">
            <strong>Sources :</strong> {sources_text}
        </p>
    </div>
    """
    
    st.markdown(banner_html, unsafe_allow_html=True)


def render_data_source_badge(
    source: str,
    is_certified: bool = True,
    tooltip: str = ""
) -> str:
    """
    Génère un badge HTML pour indiquer la source des données (ST-4.1).
    
    Parameters
    ----------
    source : str
        Nom de la source (ex: "Yahoo Finance", "Fallback sectoriel").
    is_certified : bool
        True si donnée certifiée, False si fallback.
    tooltip : str
        Texte d'aide optionnel.
    
    Returns
    -------
    str
        HTML du badge à afficher.
    """
    if is_certified:
        color = "#2E7D32"
        icon = "●"
        label = "Certifié"
    else:
        color = "#FF6F00"
        icon = "◐"
        label = "Estimé"
    
    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 4px;
        color: {color};
        font-size: 0.8em;
    " title="{tooltip}">
        <span>{icon}</span>
        <span>{source}</span>
        <span style="
            background-color: {color}20;
            padding: 1px 6px;
            border-radius: 4px;
        ">{label}</span>
    </span>
    """
