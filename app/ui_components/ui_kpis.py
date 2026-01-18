"""
app/ui_components/ui_kpis.py
RESTITUTION "GLASS BOX" HYBRIDE — VERSION V13.0 (Sprint 6 Final)
Rôle : Affichage haute fidélité incluant SOTP, Scénarios et Backtesting.
Standards : SOLID, i18n Secured (ui_texts.py), Honest Data.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np
import pandas as pd
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
    MultiplesValuationResult,
    ScenarioSynthesis,
    BacktestResult,
    HistoricalPoint
)
from app.ui_components.ui_glass_box_registry import get_step_metadata
from core.i18n import KPITexts, AuditTexts, ExpertTerminalTexts, SOTPTexts, BacktestTexts
# Force reload of KPITexts to ensure SUB_SCENARIO_WEIGHTS is available

logger = logging.getLogger(__name__)


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

def display_valuation_details(result: ValuationResult, _provider: Any = None) -> None:
    """Orchestrateur des onglets post-calcul (Intégration SOTP & Backtest)."""
    st.divider()

    core_steps = [s for s in result.calculation_trace if not s.step_key.startswith("MC_")]
    mc_steps = [s for s in result.calculation_trace if s.step_key.startswith("MC_")]

    # 1. Définition dynamique des étiquettes d'onglets (Ordre Analytique)
    tab_labels = [KPITexts.TAB_INPUTS, KPITexts.TAB_CALC]

    if result.multiples_triangulation:
        tab_labels.append(KPITexts.SEC_E_RELATIVE)

    if result.params.sotp.enabled:
        tab_labels.append(SOTPTexts.TITLE)

    if result.scenario_synthesis:
        tab_labels.append(KPITexts.TAB_SCENARIOS)

    # Étiquette Backtesting (ST 4.2)
    if result.backtest_report:
        tab_labels.append(BacktestTexts.TITLE)

    tab_labels.append(KPITexts.TAB_AUDIT)

    if result.params.monte_carlo.enable_monte_carlo and mc_steps:
        tab_labels.append(KPITexts.TAB_MC)

    # 2. Rendu séquentiel
    tabs = st.tabs(tab_labels)
    t_idx = 0

    with tabs[t_idx]:
        _render_inputs_tab(result)
        t_idx += 1

    with tabs[t_idx]:
        for idx, step in enumerate(core_steps, start=1):
            _render_smart_step(idx, step)
        t_idx += 1

    if result.multiples_triangulation:
        with tabs[t_idx]:
            _render_relative_valuation_tab(result.multiples_triangulation)
        t_idx += 1

    if result.params.sotp.enabled:
        with tabs[t_idx]:
            _render_sotp_tab(result)
        t_idx += 1

    if result.scenario_synthesis:
        with tabs[t_idx]:
            _render_scenarios_tab(result.scenario_synthesis, result.financials.currency)
        t_idx += 1

    # Rendu Backtesting (ST 4.2)
    if result.backtest_report:
        with tabs[t_idx]:
            _render_backtest_tab(result)
        t_idx += 1

    with tabs[t_idx]:
        _render_reliability_report(result.audit_report)
        t_idx += 1

    if len(tabs) > t_idx:
        with tabs[t_idx]:
            _render_monte_carlo_tab(result, mc_steps)


# ==============================================================================
# 3. RENDU DES ONGLETS INDIVIDUELS
# ==============================================================================

def _render_inputs_tab(result: ValuationResult) -> None:
    """Rendu de l'onglet des données d'entrée."""
    f, p = result.financials, result.params
    st.markdown(f"{KPITexts.SECTION_INPUTS_HEADER}")
    st.caption(KPITexts.SECTION_INPUTS_CAPTION)

    with st.expander(KPITexts.SEC_A_IDENTITY.upper(), expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**{KPITexts.LABEL_TICKER}**\n\n`{f.ticker}`")
        c2.markdown(f"**{KPITexts.LABEL_NAME}**\n\n`{f.name}`")
        c3.markdown(f"**{KPITexts.LABEL_SECTOR}**\n\n`{f.sector}`")
        c4.markdown(f"**{KPITexts.LABEL_COUNTRY}**\n\n`{f.country}`")

    with st.expander(KPITexts.SEC_B_FINANCIALS.upper(), expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(KPITexts.LABEL_PRICE, f"{f.current_price:,.2f} {f.currency}")
        c2.metric(KPITexts.LABEL_MCAP, format_smart_number(f.market_cap, f.currency))
        c3.metric(KPITexts.LABEL_REV, format_smart_number(f.revenue_ttm))
        c4.metric(KPITexts.LABEL_NI, format_smart_number(f.net_income_ttm))

    with st.expander(KPITexts.SEC_C_MODEL.upper(), expanded=True):
        r, g = p.rates, p.growth
        is_direct_equity = result.request.mode.is_direct_equity if result.request else False

        if is_direct_equity:
            label_rate = KPITexts.LABEL_KE
            actual_discount_rate = r.manual_cost_of_equity or getattr(result, 'cost_of_equity', None)
        else:
            label_rate = KPITexts.LABEL_WACC
            actual_discount_rate = r.wacc_override or getattr(result, 'wacc', None)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(KPITexts.LABEL_RF, format_smart_number(r.risk_free_rate, is_pct=True))
        c2.metric(label_rate, format_smart_number(actual_discount_rate, is_pct=True))
        c3.metric(KPITexts.LABEL_G, format_smart_number(g.fcf_growth_rate, is_pct=True))
        c4.metric(KPITexts.LABEL_HORIZON, f"{g.projection_years} {KPITexts.UNIT_YEARS}")


def _render_relative_valuation_tab(rel_result: MultiplesValuationResult) -> None:
    """Tableau de bord sectoriel (Sprint 4)."""
    st.markdown(f"#### {KPITexts.SEC_E_RELATIVE}")
    st.caption(KPITexts.RELATIVE_VAL_DESC)

    m = rel_result.multiples_data
    c1, c2, c3 = st.columns(3)
    c1.metric(KPITexts.LABEL_PE_RATIO, f"{m.median_pe:.1f}x")
    c2.metric(KPITexts.LABEL_EV_EBITDA, f"{m.median_ev_ebitda:.1f}x")
    c3.metric(KPITexts.LABEL_EV_REVENUE, f"{m.median_ev_rev:.1f}x")

    st.divider()

    if m.peers:
        peer_list = []
        for p in m.peers:
            peer_list.append({
                "Ticker": p.ticker, "Name": p.name, "Mcap": format_smart_number(p.market_cap),
                "P/E": f"{p.pe_ratio:.1f}x" if p.pe_ratio else "—",
                "EV/EBITDA": f"{p.ev_ebitda:.1f}x" if p.ev_ebitda else "—",
                "EV/Rev": f"{p.ev_revenue:.1f}x" if p.ev_revenue else "—"
            })
        st.dataframe(pd.DataFrame(peer_list), hide_index=True, width='stretch')

    with st.expander(KPITexts.TAB_CALC, expanded=False):
        for idx, step in enumerate(rel_result.calculation_trace, start=1):
            _render_smart_step(idx, step)


def _render_sotp_tab(result: ValuationResult) -> None:
    """Rendu de l'onglet Sum-of-the-Parts (ST 4.1)."""
    from app.ui_components.ui_charts import display_sotp_waterfall

    st.markdown(f"#### {SOTPTexts.TITLE}")
    display_sotp_waterfall(result)

    st.divider()
    st.caption(SOTPTexts.LBL_BU_DETAILS)

    df_sotp = pd.DataFrame([
        {
            SOTPTexts.LBL_SEGMENT_NAME: b.name,
            SOTPTexts.LBL_SEGMENT_VALUE: format_smart_number(b.enterprise_value, result.financials.currency),
            SOTPTexts.LBL_SEGMENT_METHOD: b.method.value
        } for b in result.params.sotp.segments
    ])
    st.table(df_sotp)


def _render_scenarios_tab(synthesis: ScenarioSynthesis, currency: str) -> None:
    """Rendu détaillé des scénarios Bull/Base/Bear (Sprint 5)."""
    st.markdown(f"#### {KPITexts.TAB_SCENARIOS}")
    # Utilisation sécurisée de SUB_SCENARIO_WEIGHTS avec fallback
    scenario_weights_text = getattr(KPITexts, 'SUB_SCENARIO_WEIGHTS', "Ponderation des scenarios selon leur probabilite")
    st.caption(scenario_weights_text)

    rows = []
    labels_map = {"Bull": ExpertTerminalTexts.LABEL_SCENARIO_BULL,
                  "Base": ExpertTerminalTexts.LABEL_SCENARIO_BASE,
                  "Bear": ExpertTerminalTexts.LABEL_SCENARIO_BEAR}

    for v in synthesis.variants:
        rows.append({
            "Scénario": labels_map.get(v.label, v.label),
            "Probabilité": f"{v.probability:.0%}",
            "Croissance (g)": f"{v.growth_used:.2%}",
            "Marge FCF": f"{v.margin_used:.1%}" if v.margin_used is not None and v.margin_used != 0 else ("Base"),
            "Valeur par Action": f"{v.intrinsic_value:,.2f} {currency}"
        })

    st.table(pd.DataFrame(rows))
    st.info(f"**{KPITexts.LABEL_SCENARIO_RANGE}** : {synthesis.max_downside:,.2f} à {synthesis.max_upside:,.2f} {currency}")


def _render_backtest_tab(result: ValuationResult) -> None:
    """Restitution de la validation historique (ST 4.2)."""
    from app.ui_components.ui_charts import display_backtest_convergence_chart

    st.markdown(f"#### {BacktestTexts.TITLE}")

    # SÉCURITÉ : Utilisation de la clé correcte issue de ui_texts.py
    if not result.backtest_report or not result.backtest_report.points:
        st.warning(AuditTexts.MC_NO_DATA)
        return

    # A. Score de fiabilité historique
    report = result.backtest_report
    c1, c2, c3 = st.columns(3)
    c1.metric(BacktestTexts.METRIC_MAE, f"{report.mean_absolute_error:.1%}", help=BacktestTexts.HELP_BACKTEST)
    c2.metric(BacktestTexts.METRIC_ACCURACY, f"{report.model_accuracy_score:.1f}/100")

    # B. Graphique Convergence
    display_backtest_convergence_chart(report, result.financials.currency)

    # C. Audit Trail Temporel
    st.divider()
    st.caption(BacktestTexts.SEC_RESULTS)
    raw_table = []
    for p in report.points:
        raw_table.append({
            "Date": p.valuation_date,
            BacktestTexts.LBL_HIST_IV: f"{p.intrinsic_value:,.2f}",
            BacktestTexts.LBL_REAL_PRICE: f"{p.market_price:,.2f}",
            BacktestTexts.LBL_ERROR_GAP: f"{p.error_pct:+.1%}"
        })
    st.table(pd.DataFrame(raw_table))


# ==============================================================================
# 4. AUDIT ET MONTE CARLO
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

    for step in sorted(report.audit_steps, key=lambda x: x.verdict):
        atom_audit_card(step)


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
# 5. WRAPPERS DE SYNTHÈSE
# ==============================================================================

def render_executive_summary(result: ValuationResult) -> None:
    """Synthèse Exécutive Institutionnelle (Sprint 6 Ready)."""
    f = result.financials
    st.subheader(KPITexts.EXEC_TITLE.format(name=f.name, ticker=f.ticker).upper())

    with st.container(border=True):
        if result.scenario_synthesis:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(KPITexts.LABEL_PRICE, f"{result.market_price:,.2f} {f.currency}")
            ev = result.scenario_synthesis.expected_value
            upside_ev = (ev / result.market_price) - 1
            c2.metric(KPITexts.LABEL_EXPECTED_VALUE, f"{ev:,.2f} {f.currency}", delta=f"{upside_ev:.1%}")
            c3.metric(KPITexts.LABEL_IV, f"{result.intrinsic_value_per_share:,.2f} {f.currency}")
            c4.metric(KPITexts.EXEC_CONFIDENCE, result.audit_report.rating if result.audit_report else "—")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric(KPITexts.LABEL_PRICE, f"{result.market_price:,.2f} {f.currency}")
            c2.metric(KPITexts.LABEL_IV, f"{result.intrinsic_value_per_share:,.2f} {f.currency}", delta=f"{result.upside_pct:.1%}")
            c3.metric(KPITexts.EXEC_CONFIDENCE, result.audit_report.rating if result.audit_report else "—")

    st.markdown(f"#### {KPITexts.FOOTBALL_FIELD_TITLE}")
    if result.multiples_triangulation:
        rel = result.multiples_triangulation
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(KPITexts.LABEL_FOOTBALL_FIELD_IV, f"{result.intrinsic_value_per_share:,.1f}")
            c2.metric(KPITexts.LABEL_FOOTBALL_FIELD_PE, f"{rel.pe_based_price:,.1f}")
            c3.metric(KPITexts.LABEL_FOOTBALL_FIELD_EBITDA, f"{rel.ebitda_based_price:,.1f}")
            c4.metric(KPITexts.LABEL_FOOTBALL_FIELD_PRICE, f"{result.market_price:,.1f}")
    else:
        st.info(KPITexts.LABEL_MULTIPLES_UNAVAILABLE)