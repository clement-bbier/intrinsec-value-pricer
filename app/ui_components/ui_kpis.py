"""
app/ui_components/ui_kpis.py
RESTITUTION "GLASS BOX" — VERSION V9.3 (Institutional Design & Bug Fix)
Rôle : Affichage haute fidélité sans emojis, design épuré et professionnel.
Architecture : Alignée sur la segmentation DCFParameters (Rates, Growth, MC).
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np
import streamlit as st

from core.models import (
    AuditReport,
    AuditStep,
    AuditSeverity,
    CalculationStep,
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    ValuationMode,
    TerminalValueMethod
)
from app.ui_components.ui_glass_box_registry import get_step_metadata
from app.ui_components.ui_texts import KPITexts, AuditTexts, ExpertTerminalTexts

logger = logging.getLogger(__name__)


# ==============================================================================
# 0. HELPERS DE FORMATAGE PROFESSIONNEL
# ==============================================================================

def format_smart_number(val: Optional[float], currency: str = "", is_pct: bool = False) -> str:
    """Formatte les nombres pour éviter les coupures UI (Millions, Billions, Trillions)."""
    if val is None: return "—"
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


def atom_calculation_card(index: int, step: CalculationStep) -> None:
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

    if step.verdict:
        color, status = "#28a745", AuditTexts.STATUS_OK.upper()
    else:
        color = "#fd7e14" if step.severity == AuditSeverity.WARNING else "#dc3545"
        status = AuditTexts.STATUS_ALERT.upper()

    with st.container(border=True):
        h_left, h_right = st.columns([0.7, 0.3])
        with h_left:
            st.markdown(f"**{meta.get('label', step.label).upper()}**")
            st.caption(meta.get('description', ""))
        with h_right:
            badge_html = f"""<div style="text-align:right;"><span style="color:{color}; border:1px solid {color}; 
            padding:2px 10px; border-radius:4px; font-weight:bold; font-size:12px;">{status}</span></div>"""
            st.markdown(badge_html, unsafe_allow_html=True)

        st.divider()
        col_rule, col_evidence = st.columns(2)
        with col_rule:
            st.caption(AuditTexts.H_RULE)
            st.latex(meta.get('formula', r'\text{N/A}'))
        with col_evidence:
            st.caption(AuditTexts.H_EVIDENCE)
            st.info(f"**{step.evidence}**")


# ==============================================================================
# 2. NAVIGATION ET AGGREGATION
# ==============================================================================

def display_valuation_details(result: ValuationResult, _provider: Any = None) -> None:
    """Orchestrateur des onglets post-calcul."""
    st.divider()

    core_steps = [s for s in result.calculation_trace if not s.step_key.startswith("MC_")]
    mc_steps = [s for s in result.calculation_trace if s.step_key.startswith("MC_")]

    tab_labels = [KPITexts.TAB_INPUTS, KPITexts.TAB_CALC, KPITexts.TAB_AUDIT]
    if result.params.monte_carlo.enable_monte_carlo and mc_steps:
        tab_labels.append(KPITexts.TAB_MC)

    tabs = st.tabs(tab_labels)

    with tabs[0]: _render_inputs_tab(result)
    with tabs[1]:
        for idx, step in enumerate(core_steps, start=1):
            _render_smart_step(idx, step)
    with tabs[2]: _render_reliability_report(result.audit_report)

    if len(tabs) > 3:
        with tabs[3]: _render_monte_carlo_tab(result, mc_steps)


# ==============================================================================
# 3. ONGLET DONNÉES D'ENTRÉE (CORRIGÉ SANS DOUBLONS)
# ==============================================================================

def _render_inputs_tab(result: ValuationResult) -> None:
    f, p = result.financials, result.params
    st.markdown(f"{KPITexts.SECTION_INPUTS_HEADER}")
    st.caption(KPITexts.SECTION_INPUTS_CAPTION)

    # Section A : Identité
    with st.expander(KPITexts.SEC_A_IDENTITY.upper(), expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**{KPITexts.LABEL_TICKER}**\n\n`{f.ticker}`")
        c2.markdown(f"**{KPITexts.LABEL_NAME}**\n\n`{f.name}`")
        c3.markdown(f"**{KPITexts.LABEL_SECTOR}**\n\n`{f.sector}`")
        c4.markdown(f"**{KPITexts.LABEL_COUNTRY}**\n\n`{f.country}`")
        st.divider()
        c5, c6, c7, c8 = st.columns(4)
        c5.markdown(f"**{KPITexts.LABEL_INDUSTRY}**\n\n`{f.industry}`")
        c6.markdown(f"**{KPITexts.LABEL_CURRENCY}**\n\n`{f.currency}`")
        c7.markdown(f"**{KPITexts.LABEL_BETA}**\n\n`{f.beta:.2f}`")
        c8.markdown(f"**{KPITexts.LABEL_SHARES}**\n\n`{f.shares_outstanding:,.0f}`")

    # Section B : Données Financières
    with st.expander(KPITexts.SEC_B_FINANCIALS.upper(), expanded=True):
        st.markdown(f"**{KPITexts.SUB_MARKET.upper()}**")
        c1, c2, c3 = st.columns(3)
        c1.metric(KPITexts.LABEL_PRICE, f"{f.current_price:,.2f} {f.currency}")
        c2.metric(KPITexts.LABEL_MCAP, format_smart_number(f.market_cap, f.currency))
        c3.metric(KPITexts.LABEL_BVPS, f"{f.book_value_per_share:,.2f}" if f.book_value_per_share else "—")

        st.divider()
        st.markdown(f"**{KPITexts.SUB_CAPITAL.upper()}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(KPITexts.LABEL_DEBT, format_smart_number(f.total_debt))
        c2.metric(KPITexts.LABEL_CASH, format_smart_number(f.cash_and_equivalents))
        c3.metric(KPITexts.LABEL_NET_DEBT, format_smart_number(f.net_debt))
        c4.metric(KPITexts.LABEL_INTEREST, format_smart_number(f.interest_expense))

        st.divider()
        st.markdown(f"**{KPITexts.SUB_PERF.upper()}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(KPITexts.LABEL_REV, format_smart_number(f.revenue_ttm))
        c2.metric(KPITexts.LABEL_EBIT, format_smart_number(f.ebit_ttm))
        c3.metric(KPITexts.LABEL_NI, format_smart_number(f.net_income_ttm))
        c4.metric(KPITexts.LABEL_EPS, f"{f.eps_ttm:,.2f}" if f.eps_ttm else "—")

    # Section C : Paramètres Modèle
    with st.expander(KPITexts.SEC_C_MODEL.upper(), expanded=True):
        r, g = p.rates, p.growth
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(KPITexts.LABEL_RF, format_smart_number(r.risk_free_rate, is_pct=True))
        c2.metric(KPITexts.LABEL_MRP, format_smart_number(r.market_risk_premium, is_pct=True))
        c3.metric(KPITexts.LABEL_KD, format_smart_number(r.cost_of_debt, is_pct=True))
        c4.metric(KPITexts.LABEL_TAX, format_smart_number(r.tax_rate, is_pct=True))
        st.divider()
        c5, c6, c7 = st.columns(3)
        c5.metric(KPITexts.LABEL_G, format_smart_number(g.fcf_growth_rate, is_pct=True))
        c6.metric(KPITexts.LABEL_GN, format_smart_number(g.perpetual_growth_rate, is_pct=True))
        c7.metric(KPITexts.LABEL_HORIZON, f"{g.projection_years} ans")


# ==============================================================================
# 4. ONGLET AUDIT ET MONTE CARLO
# ==============================================================================

def _render_reliability_report(report: Optional[AuditReport]) -> None:
    if not report:
        st.info(AuditTexts.NO_REPORT)
        return

    st.markdown(f"### {AuditTexts.GLOBAL_SCORE.format(score=report.global_score)}")
    st.progress(report.global_score / 100)
    c1, c2 = st.columns(2)
    c1.metric(AuditTexts.RATING_SCORE, report.rating)
    c2.metric(AuditTexts.COVERAGE, f"{report.audit_coverage:.0%}")
    st.divider()

    if report.audit_steps:
        for step in sorted(report.audit_steps, key=lambda x: x.verdict):
            atom_audit_card(step)
    else:
        for log in report.logs: st.warning(f"**[{log.category.upper()}]** {log.message}")


def _render_monte_carlo_tab(result: ValuationResult, mc_steps: List[CalculationStep]) -> None:
    from app.ui_components.ui_charts import display_simulation_chart
    if not result.simulation_results: return

    st.markdown(AuditTexts.MC_TITLE)
    q = result.quantiles or {}
    c1, c2, c3 = st.columns(3)
    c1.metric(AuditTexts.MC_MEDIAN, f"{q.get('P50', 0.0):,.2f}")
    c2.metric(AuditTexts.MC_TAIL_RISK, f"{q.get('P10', 0.0):,.2f}")
    c3.metric("VALID RATIO", f"{getattr(result, 'mc_valid_ratio', 0):.1%}")

    display_simulation_chart(result.simulation_results, result.market_price, result.financials.currency)

    with st.expander(AuditTexts.MC_AUDIT_STOCH):
        for idx, step in enumerate(mc_steps, start=1): _render_smart_step(idx, step)


# ==============================================================================
# 5. WRAPPERS ET SYNTHÈSE
# ==============================================================================

def render_executive_summary(result: ValuationResult) -> None:
    f = result.financials
    st.subheader(KPITexts.EXEC_TITLE.format(name=f.name, ticker=f.ticker).upper())
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric(KPITexts.LABEL_PRICE, f"{result.market_price:,.2f} {f.currency}")
        c2.metric(KPITexts.LABEL_IV, f"{result.intrinsic_value_per_share:,.2f} {f.currency}")
        c3.metric(KPITexts.EXEC_CONFIDENCE, result.audit_report.rating if result.audit_report else "—")


def _render_smart_step(index: int, step: CalculationStep) -> None:
    """Correction du TypeError : On passe l'objet step entier à la fonction atomique."""
    atom_calculation_card(index=index, step=step)