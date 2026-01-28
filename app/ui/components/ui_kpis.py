"""
app/ui/components/ui_kpis.py
ATOMIC COMPONENTS — Minimalist style, zero emojis.
Role: Standardized KPI and Audit cards for institutional rendering.
"""

from __future__ import annotations
from typing import Optional, Literal
import streamlit as st

from src.models import AuditStep, AuditSeverity
from src.i18n import AuditTexts
from app.ui.components.ui_glass_box_registry import get_step_metadata

def atom_kpi_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: Literal["normal", "inverse", "off", "red", "orange", "yellow", "green", "blue", "violet", "gray", "grey", "primary"] = "normal",
    help_text: str = ""
) -> None:
    """Base component for financial metrics display."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color, help=help_text)

def render_audit_reliability_gauge(score: float, rating: str) -> None:
    """Institutional gauge for the global reliability score."""
    if score >= 80:
        color, label = "green", AuditTexts.RELIABILITY_HIGH
    elif score >= 60:
        color, label = "orange", AuditTexts.RELIABILITY_MODERATE
    else:
        color, label = "red", AuditTexts.RELIABILITY_LOW

    with st.container(border=True):
        st.markdown(f"**{AuditTexts.RATING_SCORE.upper()} : {rating}**")
        st.progress(score / 100)
        c1, c2 = st.columns(2)
        c1.markdown(f":{color}[**{label.upper()}**]")
        c2.markdown(f"<div style='text-align:right; color:gray;'>{score:.1f}%</div>", unsafe_allow_html=True)

def atom_audit_card(step: AuditStep) -> None:
    """Audit card component for the Reliability Audit pillar."""
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