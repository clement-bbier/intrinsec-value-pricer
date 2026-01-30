"""
app/ui/results/core/audit_report.py

PILLAR 3 — RELIABILITY AUDIT
============================
Role: Data reliability analysis and business invariant validation.
Architecture: Institutional compliance report providing high-level confidence
metrics and granular test results.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult, AuditSeverity, AuditStep
from src.i18n import AuditTexts, PillarLabels
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import (
    render_audit_reliability_gauge,
    atom_kpi_metric
)
from app.ui.components.ui_glass_box_registry import get_step_metadata


class AuditReportTab(ResultTabBase):
    """
    Pillar 3: Reliability Audit Tab.

    This component serves as a financial "Due Diligence" sheet, presenting
    the results of the diagnostic engine through institutional gauges,
    prioritized alerts, and detailed compliance cards.
    """

    TAB_ID = "audit_report"
    LABEL = PillarLabels.PILLAR_3_AUDIT
    ORDER = 3
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders the audit report with prioritized anomaly hierarchical display.

        Parameters
        ----------
        result : ValuationResult
            The valuation result containing audit report data.
        **kwargs : Any
            Additional rendering context.
        """
        report = result.audit_report

        if not report:
            st.info(AuditTexts.NO_REPORT)
            return

        # --- 1. PILLAR HEADER (Institutional Standard) ---
        st.markdown(f"### {PillarLabels.PILLAR_3_AUDIT}")
        st.caption(AuditTexts.CHECK_TABLE)
        st.write("")

        # --- 2. RELIABILITY SYNTHESIS (Score & Metrics) ---
        with st.container(border=True):
            col_gauge, col_metrics = st.columns([1, 1.2])

            with col_gauge:
                # Visualization of the global score (0-100%) and rating (A-F)
                render_audit_reliability_gauge(report.global_score, report.rating)

            with col_metrics:
                st.write("")  # Vertical centering alignment
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

                # Summary explanation of the scoring logic
                st.caption(f"_{AuditTexts.GLOBAL_SCORE.format(score=report.global_score)}_")

        # --- 3. CRITICAL ALERTS (Red Flag Management) ---
        # Immediate visibility for violations that could invalidate the valuation
        critical_fails = [
            s for s in report.audit_steps
            if not s.verdict and s.severity == AuditSeverity.CRITICAL
        ]

        if critical_fails:
            st.write("")
            alert_msg = AuditTexts.CRITICAL_VIOLATION_MSG.format(count=len(critical_fails))
            st.error(f"**{AuditTexts.STATUS_ALERT} : {alert_msg}**")

            for fail in critical_fails:
                meta = get_step_metadata(fail.step_key)
                st.caption(f"• **{meta.get('label', fail.label)}** : {meta.get('description', '')}")

        st.write("")
        st.divider()

        # --- 4. DETAILED PROCEEDINGS (Audit Log) ---
        # Prioritization: Failed tests and criticalities appear first
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
        Renders an individual audit card using compliance signaling standards.

        Parameters
        ----------
        step : AuditStep
            The specific audit step/test result to render.
        """
        meta = get_step_metadata(step.step_key)

        # 1. Signaling Logic: Colors and Status Mapping
        if step.verdict:
            color = "#10b981"  # Institutional Green (Pass)
            status_label = AuditTexts.STATUS_OK
            icon = "✅"
        else:
            is_crit = step.severity == AuditSeverity.CRITICAL
            color = "#ef4444" if is_crit else "#f59e0b"  # Red (Critical) vs Amber (Warning)
            status_label = AuditTexts.STATUS_ALERT
            icon = "❌" if is_crit else "⚠️"

        # 2. Card Layout Construction
        with st.container(border=True):
            h_left, h_right = st.columns([0.70, 0.30])

            display_label = meta.get('label', step.label)
            h_left.markdown(f"**{display_label}**")

            # Status Badge: Uses light background alpha for institutional look
            badge_html = f"""
            <div style='text-align: right;'>
                <span style='background-color:{color}15; color:{color}; padding:3px 12px; border-radius:8px; font-weight:700; border:1px solid {color}30; font-size:0.8rem;'>
                    {icon} {status_label}
                </span>
            </div>
            """
            h_right.markdown(badge_html, unsafe_allow_html=True)

            # Contextual metadata from registry
            st.caption(meta.get('description', ""))

            # Technical Evidence Grid (Audit Trail)
            st.write("")
            c_rule, c_evidence, c_verdict = st.columns([1.2, 1, 0.8])

            with c_rule:
                st.markdown(
                    f"<p style='font-size:0.8rem; color:gray; margin-bottom:0;'>{AuditTexts.H_RULE}</p>",
                    unsafe_allow_html=True
                )
                st.latex(step.rule_formula or AuditTexts.DEFAULT_FORMULA)

            with c_evidence:
                st.markdown(
                    f"<p style='font-size:0.8rem; color:gray; margin-bottom:5px;'>{AuditTexts.H_EVIDENCE}</p>",
                    unsafe_allow_html=True
                )
                st.markdown(f"_{step.evidence or AuditTexts.INTERNAL_CALC}_")

            with c_verdict:
                st.markdown(
                    f"<p style='font-size:0.8rem; color:gray; margin-bottom:5px;'>{AuditTexts.H_VERDICT}</p>",
                    unsafe_allow_html=True
                )

                # Indicator Formatting (Ratio % vs Unit Value)
                val = step.indicator_value
                try:
                    num_val = float(val)
                    display_val = f"{num_val:.1%}" if abs(num_val) <= 1.0 else f"{num_val:.2f}"
                except (ValueError, TypeError):
                    display_val = str(val)

                st.markdown(f"**{display_val}**")

    def is_visible(self, result: ValuationResult) -> bool:
        """
        Determines the visibility of the audit tab.

        Parameters
        ----------
        result : ValuationResult
            The valuation result to inspect.

        Returns
        -------
        bool
            True if the valuation contains an audit report, False otherwise.
        """
        return result.audit_report is not None