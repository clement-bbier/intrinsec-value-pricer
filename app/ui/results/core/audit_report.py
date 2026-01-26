"""
app/ui/results/core/audit_report.py
ONGLET — RAPPORT D'AUDIT (Pilier 3)
==================================
Rôle : Analyse de fiabilité des données et validation des invariants métier.
Architecture : Homogénéité totale avec les Piliers de Configuration et de Calcul.
"""

from typing import Any, List
import streamlit as st

from src.models import ValuationResult, AuditSeverity, AuditStep
from src.i18n import AuditTexts, KPITexts, PillarLabels
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import (
    render_audit_reliability_gauge,
    atom_kpi_metric
)
from app.ui.components.ui_glass_box_registry import get_step_metadata

class AuditReportTab(ResultTabBase):
    """
    Pilier 3 : Audit de fiabilité.
    Design : FactSheet institutionnelle avec indicateurs de confiance et PV détaillé.
    """

    TAB_ID = "audit_report"
    LABEL = PillarLabels.PILLAR_3_AUDIT
    ORDER = 3
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu du rapport d'audit avec hiérarchisation des anomalies."""
        report = result.audit_report

        if not report:
            st.info(AuditTexts.NO_REPORT)
            return

        # --- 1. EN-TÊTE NORMALISÉ (Style Grade-A) ---
        st.markdown(f"### {PillarLabels.PILLAR_3_AUDIT}")
        st.caption(AuditTexts.CHECK_TABLE)
        st.write("")

        # --- 2. SYNTHÈSE DE FIABILITÉ (Jauge & Métriques clés) ---
        with st.container(border=True):
            col_gauge, col_metrics = st.columns([1, 1.2])

            with col_gauge:
                # Affichage de la jauge de score global (0-100%)
                render_audit_reliability_gauge(report.global_score, report.rating)

            with col_metrics:
                st.write("") # Alignement vertical
                m1, m2 = st.columns(2)
                with m1:
                    atom_kpi_metric(
                        label=AuditTexts.COVERAGE,
                        value=f"{report.audit_coverage:.0%}"
                    )
                with m2:
                    atom_kpi_metric(
                        label=AuditTexts.H_INDICATOR,
                        value=str(len(report.audit_steps))
                    )

                # Note pédagogique sur le score
                st.caption(f"_{AuditTexts.GLOBAL_SCORE.format(score=report.global_score)}_")

        # --- 3. ALERTES CRITIQUES (Gestion des Red Flags) ---
        critical_fails = [s for s in report.audit_steps if not s.verdict and s.severity == AuditSeverity.CRITICAL]
        if critical_fails:
            st.write("")
            # Utilisation de la couleur critique i18n
            st.error(f"**{AuditTexts.STATUS_ALERT} : {len(critical_fails)} invariants critiques violés**")
            for fail in critical_fails:
                meta = get_step_metadata(fail.step_key)
                st.caption(f"• **{meta.get('label', fail.label)}** : {meta.get('description', '')}")

        st.write("")
        st.divider()

        # --- 4. PROCÈS-VERBAL DÉTAILLÉ (Cartes de tests) ---
        # Tri : On place les échecs en haut, puis on trie par sévérité
        sorted_steps = sorted(
            report.audit_steps,
            key=lambda s: (s.verdict, s.severity != AuditSeverity.CRITICAL)
        )

        st.markdown(f"#### {AuditTexts.AUDIT_NOTES_EXPANDER}")

        for step in sorted_steps:
            self._render_audit_step_card(step)

    @staticmethod
    def _render_audit_step_card(step: AuditStep) -> None:
        """
        Rendu d'une carte d'audit style 'Compliance Report'.
        Utilise des badges HTML pour une signalétique précise.
        """
        meta = get_step_metadata(step.step_key)

        # 1. Détermination de la signalétique (Couleurs & Icônes)
        if step.verdict:
            color = "#10b981"  # Vert
            status_label = AuditTexts.STATUS_OK
            icon = "✅"
        else:
            is_crit = step.severity == AuditSeverity.CRITICAL
            color = "#ef4444" if is_crit else "#f59e0b"  # Rouge vs Orange
            status_label = AuditTexts.STATUS_ALERT
            icon = "❌" if is_crit else "⚠️"

        # 2. Construction de la carte
        with st.container(border=True):
            # Ligne de titre : Nom du test | Badge de statut
            h_left, h_right = st.columns([0.70, 0.30])

            display_label = meta.get('label', step.label)
            h_left.markdown(f"**{display_label}**")

            # Badge HTML stylisé (Sentence case)
            badge_html = f"""
            <div style='text-align: right;'>
                <span style='background-color:{color}15; color:{color}; padding:3px 12px; border-radius:8px; font-weight:700; border:1px solid {color}30; font-size:0.8rem;'>
                    {icon} {status_label}
                </span>
            </div>
            """
            h_right.markdown(badge_html, unsafe_allow_html=True)

            # Description du test
            st.caption(meta.get('description', ""))

            # Grille technique : Règle | Preuve | Résultat
            st.write("")
            c_rule, c_evidence, c_verdict = st.columns([1.2, 1, 0.8])

            with c_rule:
                st.markdown(f"<p style='font-size:0.8rem; color:gray; margin-bottom:0;'>{AuditTexts.H_RULE}</p>", unsafe_allow_html=True)
                st.latex(step.rule_formula or AuditTexts.DEFAULT_FORMULA)

            with c_evidence:
                st.markdown(f"<p style='font-size:0.8rem; color:gray; margin-bottom:5px;'>{AuditTexts.H_EVIDENCE}</p>", unsafe_allow_html=True)
                st.markdown(f"_{step.evidence or AuditTexts.INTERNAL_CALC}_")

            with c_verdict:
                st.markdown(f"<p style='font-size:0.8rem; color:gray; margin-bottom:5px;'>{AuditTexts.H_VERDICT}</p>", unsafe_allow_html=True)

                # Formatage dynamique de la valeur indicateur
                val = step.indicator_value
                try:
                    num_val = float(val)
                    # Si c'est un ratio faible, on affiche en %, sinon en flottant
                    display_val = f"{num_val:.1%}" if abs(num_val) <= 1.0 else f"{num_val:.2f}"
                except (ValueError, TypeError):
                    display_val = str(val)

                st.markdown(f"**{display_val}**")

    def is_visible(self, result: ValuationResult) -> bool:
        """L'onglet n'est visible que si un audit a été généré par le moteur."""
        return result.audit_report is not None