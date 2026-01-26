"""
app/ui/components/ui_kpis.py
Composants atomiques — Zéro émoji, style épuré.
"""
from __future__ import annotations
from typing import List, Optional
import streamlit as st

from src.models import AuditStep, AuditSeverity
from src.i18n import AuditTexts, CommonTexts
from src.utilities.formatting import format_smart_number
from app.ui.components.ui_glass_box_registry import get_step_metadata

def atom_kpi_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: str = ""
) -> None:
    """Composant de base pour les métriques financières."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color, help=help_text)

def render_audit_reliability_gauge(score: float, rating: str) -> None:
    """Jauge institutionnelle pour le score de fiabilité."""
    if score >= 80:
        color, label = "green", "FIABILITÉ ÉLEVÉE"
    elif score >= 60:
        color, label = "orange", "FIABILITÉ MODÉRÉE"
    else:
        color, label = "red", "FIABILITÉ FAIBLE"

    with st.container(border=True):
        st.markdown(f"**{AuditTexts.RATING_SCORE.upper()} : {rating}**")
        st.progress(score / 100)
        c1, c2 = st.columns(2)
        c1.markdown(f":{color}[**{label}**]")
        c2.markdown(f"<div style='text-align:right; color:gray;'>{score:.1f}%</div>", unsafe_allow_html=True)

def atom_audit_card(step: AuditStep) -> None:
    """Carte d'audit pour le pilier Audit Report."""
    meta = get_step_metadata(step.step_key)
    if step.verdict:
        color, status = "green", AuditTexts.STATUS_OK
    else:
        color = "red" if step.severity == AuditSeverity.CRITICAL else "orange"
        status = AuditTexts.STATUS_ALERT

    with st.container(border=True):
        col_text, col_status = st.columns([0.8, 0.2])
        col_text.markdown(f"**{meta.get('label', step.label).upper()}**")
        col_text.caption(meta.get('description', ""))
        col_status.markdown(f"<div style='text-align:right;'>:{color}[**{status.upper()}**]</div>", unsafe_allow_html=True)

        if step.evidence:
            st.divider()
            st.info(step.evidence)