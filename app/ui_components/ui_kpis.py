from typing import Any, List, Dict
import streamlit as st
import pandas as pd
import numpy as np

from core.models import (
    ValuationResult,
    ValuationMode,
    AuditReport,
    AuditLog
)
from app.ui_components.ui_methodology import (
    display_simple_dcf_formula,
    display_fundamental_dcf_formula,
    display_monte_carlo_formula
)


def format_currency(x: float | None, currency: str) -> str:
    if x is None: return "-"
    # Gestion automatique des grands nombres
    if abs(x) >= 1_000_000_000:
        return f"{x / 1e9:,.2f} B {currency}"
    if abs(x) >= 1_000_000:
        return f"{x / 1e6:,.2f} M {currency}"
    return f"{x:,.2f} {currency}"


def _render_audit_category_block(title: str, score: float, logs: List[AuditLog]):
    color = "green" if score >= 80 else "orange" if score >= 50 else "red"
    with st.expander(f"{title} (Score: {score:.0f}/100)", expanded=(score < 100)):
        st.progress(int(score) / 100, text=None)
        for log in logs:
            if log.severity == "success":
                st.markdown(f":green[**[OK]**] {log.message}")
            else:
                tag = "[FAIL]" if log.severity in ["critical", "high"] else "[WARN]"
                st.markdown(f":red[**{tag}**] {log.message} *(-{abs(log.penalty)} pts)*")


def _render_detailed_audit_view(report: AuditReport):
    categories = ["Données", "Cohérence", "Méthode"]
    for cat in categories:
        cat_logs = [l for l in report.logs if l.category == cat]
        if not cat_logs: continue
        cat_score = report.breakdown.get(cat, 0.0)
        _render_audit_category_block(cat, cat_score, cat_logs)


def _render_assumptions(financials, params, result, mode):
    currency = financials.currency
    st.markdown("#### Hypothèses Clés")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Coût du Capital**")
        st.metric("WACC", f"{result.dcf.wacc:.1%}")
        st.caption(f"Ke: {result.dcf.cost_of_equity:.1%} | Kd(net): {result.dcf.after_tax_cost_of_debt:.1%}")

    with c2:
        st.markdown("**Croissance**")
        st.metric("Croissance (g)", f"{params.fcf_growth_rate:.1%}")
        st.caption(f"Terminale: {params.perpetual_growth_rate:.1%}")

    with c3:
        st.markdown("**Structure**")
        net_debt = financials.total_debt - financials.cash_and_equivalents
        st.metric("Dette Nette", format_currency(net_debt, currency))
        st.caption(f"Levier (D/E): {params.target_debt_weight / params.target_equity_weight:.2f}")


def display_results(res: ValuationResult):
    financials = res.financials
    dcf = res.dcf
    mode = res.request.mode
    currency = financials.currency

    st.subheader(f"Résultats : {financials.ticker}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Prix Marché", format_currency(res.market_price, currency))
    with c2:
        label_val = "Valeur Intrinsèque"
        if mode == ValuationMode.MONTE_CARLO: label_val += " (P50)"
        st.metric(label_val, format_currency(res.intrinsic_value_per_share, currency),
                  delta=f"{res.upside_pct:.1%}" if res.upside_pct else None)
    with c3:
        if dcf.quantiles:
            st.metric("Fourchette (P10 - P90)",
                      f"{dcf.quantiles['P10']:,.0f} - {dcf.quantiles['P90']:,.0f}")
        else:
            st.metric("Equity Value", format_currency(dcf.equity_value, currency))

    st.markdown("---")

    t1, t2, t3, t4 = st.tabs(["Synthèse", "Projections", "Méthodologie", "Détail Audit"])

    with t1:
        _render_assumptions(financials, res.params, res, mode)
    with t2:
        fcfs = dcf.projected_fcfs
        years = [f"An {i + 1}" for i in range(len(fcfs))]
        df_proj = pd.DataFrame({
            "Année": years,
            "FCF Projeté": fcfs,
            "Discount Factor": dcf.discount_factors
        })
        st.dataframe(df_proj.style.format({"FCF Projeté": "{:,.0f}", "Discount Factor": "{:.3f}"}),
                     use_container_width=True)
    with t3:
        if mode == ValuationMode.SIMPLE_FCFF:
            display_simple_dcf_formula(financials, res.params)
        elif mode == ValuationMode.FUNDAMENTAL_FCFF:
            display_fundamental_dcf_formula(financials, res.params)
        elif mode == ValuationMode.MONTE_CARLO:
            display_monte_carlo_formula(financials, res.params)
    with t4:
        if res.audit_report:
            _render_detailed_audit_view(res.audit_report)
        else:
            st.info("Pas de rapport d'audit disponible.")