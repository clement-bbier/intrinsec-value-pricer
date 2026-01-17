"""
app/ui/result_tabs/core/audit_report.py
Onglet — Rapport d'Audit (Fiabilité)

Affiche le score de confiance et les tests passés/échoués.
"""

from typing import Any

import streamlit as st

from core.models import ValuationResult, AuditReport, AuditStep, AuditSeverity
from core.i18n import AuditTexts
from app.ui.base import ResultTabBase


class AuditReportTab(ResultTabBase):
    """Onglet du rapport d'audit."""
    
    TAB_ID = "audit_report"
    LABEL = "Audit"
    ICON = ""
    ORDER = 3
    IS_CORE = True
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche le rapport d'audit."""
        report = result.audit_report
        
        if not report:
            st.info(AuditTexts.NO_REPORT)
            return
        
        # Score global
        self._render_global_score(report)
        
        st.divider()
        
        # Détail des tests
        self._render_audit_details(report)
    
    def _render_global_score(self, report: AuditReport) -> None:
        """Affiche le score global avec jauge."""
        st.markdown(f"### {AuditTexts.GLOBAL_SCORE.format(score=report.global_score)}")
        
        # Barre de progression colorée
        color = self._get_score_color(report.global_score)
        st.progress(report.global_score / 100)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Rating", report.rating)
        col2.metric("Couverture", f"{report.audit_coverage:.0%}")
        col3.metric("Tests exécutés", report.audit_depth)
    
    def _render_audit_details(self, report: AuditReport) -> None:
        """Affiche le detail des tests."""
        st.markdown("**Detail des Tests**")
        
        if not report.audit_steps:
            st.info("Aucun test détaillé disponible.")
            return
        
        # Trier : échecs en premier
        sorted_steps = sorted(report.audit_steps, key=lambda s: (s.verdict, s.step_key))
        
        for step in sorted_steps:
            self._render_audit_card(step)
    
    def _render_audit_card(self, step: AuditStep) -> None:
        """Affiche une carte pour un test d'audit."""
        # Determiner le style selon le resultat
        if step.verdict:
            icon = "[OK]"
            color = "#28a745"
            status = "PASS"
        else:
            severity_styles = {
                AuditSeverity.CRITICAL: ("[X]", "#dc3545", "CRITICAL"),
                AuditSeverity.WARNING: ("[!]", "#ffc107", "WARNING"),
                AuditSeverity.INFO: ("[i]", "#17a2b8", "INFO"),
            }
            icon, color, status = severity_styles.get(
                step.severity, ("[-]", "#6c757d", "UNKNOWN")
            )
        
        with st.container(border=True):
            col1, col2 = st.columns([0.85, 0.15])
            
            with col1:
                st.markdown(f"**{step.step_key}**")
                if step.evidence:
                    st.caption(step.evidence)
            
            with col2:
                st.markdown(
                    f"<span style='color:{color}; font-weight:bold;'>{icon} {status}</span>",
                    unsafe_allow_html=True
                )
    
    @staticmethod
    def _get_score_color(score: float) -> str:
        """Retourne la couleur selon le score."""
        if score >= 80:
            return "#28a745"  # Vert
        elif score >= 60:
            return "#ffc107"  # Jaune
        else:
            return "#dc3545"  # Rouge
