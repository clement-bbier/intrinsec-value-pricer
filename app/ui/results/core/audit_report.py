"""
app/ui/results/core/audit_report.py
Onglet — Rapport d'Audit & Procès-Verbal de Conformité (Pillier 3)
Architecture : Pillar 3 - Robustesse & Intégrité des Invariants.
"""

from typing import Any, List
import streamlit as st

from src.models import ValuationResult, AuditSeverity, AuditStep
from src.i18n import AuditTexts, KPITexts, CommonTexts
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import (
    render_audit_reliability_gauge,
    atom_kpi_metric
)
from app.ui.components.ui_glass_box_registry import get_step_metadata

class AuditReportTab(ResultTabBase):
    """
    Pillier 3 : Audit Report.
    Rendu exhaustif des tests normatifs avec justification LaTeX.
    """

    TAB_ID = "audit_report"
    LABEL = KPITexts.TAB_AUDIT
    ORDER = 3
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu du PV d'audit avec preuve numérique."""
        report = result.audit_report

        if not report:
            st.info(AuditTexts.NO_REPORT)
            return

        # --- SECTION 1 : SYNTHÈSE DE FIABILITÉ ---
        with st.container(border=True):
            col_gauge, col_metrics = st.columns([1, 1.2])

            with col_gauge:
                render_audit_reliability_gauge(report.score, report.rating)

            with col_metrics:
                m1, m2 = st.columns(2)
                with m1:
                    atom_kpi_metric(
                        label=AuditTexts.COVERAGE,
                        value=f"{report.audit_coverage:.0%}"
                    )
                with m2:
                    # Utilisation du nombre de tests pour la profondeur
                    atom_kpi_metric(
                        label=AuditTexts.H_INDICATOR,
                        value=str(len(report.steps))
                    )

        st.write("")

        # --- SECTION 2 : RÉSUMÉ DES ALERTES CRITIQUES (RED FLAGS) ---
        critical_fails = [s for s in report.steps if not s.verdict and s.severity == AuditSeverity.CRITICAL]
        if critical_fails:
            st.error(f"**{AuditTexts.STATUS_ALERT.upper()} : {len(critical_fails)} INVARIANTS VIOLÉS**")
            for fail in critical_fails:
                meta = get_step_metadata(fail.step_key)
                st.caption(f"• {meta.get('label', fail.label)}")

        st.divider()
        st.markdown(f"**{AuditTexts.CHECK_TABLE.upper()}**")

        # --- SECTION 3 : PROCÈS-VERBAL DÉTAILLÉ DES TESTS ---
        # Tri : Verdicts négatifs (Alerte) d'abord, puis par sévérité
        sorted_steps = sorted(
            report.steps,
            key=lambda s: (s.verdict, s.severity != AuditSeverity.CRITICAL)
        )

        for step in sorted_steps:
            self._render_audit_step_card(step)

    def _render_audit_step_card(self, step: AuditStep) -> None:
        """Rendu d'une carte de test individuelle style Factsheet."""
        meta = get_step_metadata(step.step_key)

        # Détermination du statut institutionnel
        if step.verdict:
            status_color = ":green"
            status_label = AuditTexts.STATUS_OK
        else:
            status_color = ":red" if step.severity == AuditSeverity.CRITICAL else ":orange"
            status_label = AuditTexts.STATUS_ALERT

        with st.container(border=True):
            # En-tête : Label | Status
            h_left, h_right = st.columns([0.75, 0.25])
            h_left.markdown(f"**{meta.get('label', step.label).upper()}**")
            h_right.markdown(
                f"<div style='text-align:right;'>{status_color}[**{status_label.upper()}**]</div>",
                unsafe_allow_html=True
            )

            st.caption(meta.get('description', ""))
            st.write("")

            # Preuve en 3 colonnes : Théorie | Réel | Résultat
            c_rule, c_evidence, c_verdict = st.columns([1, 1, 1])

            with c_rule:
                st.caption(AuditTexts.H_RULE)
                formula = meta.get('formula')
                if formula:
                    st.latex(formula)
                else:
                    st.markdown(f"`{CommonTexts.STATUS_AUDITED}`")

            with c_evidence:
                st.caption(AuditTexts.H_EVIDENCE)
                if step.numerical_evidence:
                    # Affichage mis en valeur de l'inégalité/preuve
                    st.markdown(f"**{step.numerical_evidence}**")
                else:
                    st.markdown(f"`{CommonTexts.STATUS_CALCULATED}`")

            with c_verdict:
                st.caption(AuditTexts.H_VERDICT)
                st.markdown(f"### {step.result_value}")

            # Commentaire analytique (si présent)
            if step.evidence:
                st.divider()
                st.caption(CommonTexts.INTERPRETATION_LABEL)
                st.info(step.evidence, icon=None)

    def is_visible(self, result: ValuationResult) -> bool:
        return result.audit_report is not None