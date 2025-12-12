from typing import Any, List, Dict
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

from core.models import CompanyFinancials, DCFParameters, ValuationMode, DCFResult, InputSource
from app.ui_components.ui_methodology import (
    display_simple_dcf_formula,
    display_fundamental_dcf_formula,
    display_monte_carlo_formula,
    display_audit_methodology
)


def format_currency(x: float | None, currency: str) -> str:
    if x is None: return "-"
    return f"{x:,.2f} {currency}".replace(",", " ")


def _render_assumptions_tab_content(financials, params, result, mode, currency):
    st.caption(f"Données : {financials.source_fcf.upper()} | Croissance : {financials.source_growth.upper()}")
    c1, c2, c3 = st.columns(3)
    cfg_txt = st.column_config.TextColumn("Indicateur", width="medium")
    cfg_val = st.column_config.TextColumn("Valeur", width="small")

    with c1:
        st.markdown("**Coût du Capital**")
        df = pd.DataFrame([
            {"Indicateur": "Coût Equity", "Valeur": f"{result.cost_of_equity:.2%}"},
            {"Indicateur": "Coût Dette Net", "Valeur": f"{result.after_tax_cost_of_debt:.2%}"},
            {"Indicateur": "WACC Final", "Valeur": f"{result.wacc:.2%}"}
        ])
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Indicateur": cfg_txt, "Valeur": cfg_val})

    with c2:
        st.markdown("**Croissance**")
        lbl = "FCF Normatif" if mode == ValuationMode.FUNDAMENTAL_FCFF else "FCF TTM"
        val = financials.fcf_fundamental_smoothed if mode == ValuationMode.FUNDAMENTAL_FCFF else financials.fcf_last
        df = pd.DataFrame([
            {"Indicateur": lbl, "Valeur": format_currency(val, currency)},
            {"Indicateur": "Croissance Initiale", "Valeur": f"{params.fcf_growth_rate:.2%}"},
            {"Indicateur": "Croissance Terminale", "Valeur": f"{params.perpetual_growth_rate:.2%}"}
        ])
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Indicateur": cfg_txt, "Valeur": cfg_val})

    with c3:
        st.markdown("**Structure**")
        df = pd.DataFrame([
            {"Indicateur": "Dette Totale", "Valeur": format_currency(financials.total_debt, currency)},
            {"Indicateur": "Trésorerie", "Valeur": format_currency(financials.cash_and_equivalents, currency)},
            {"Indicateur": "Actions", "Valeur": f"{financials.shares_outstanding / 1e6:,.1f} M"}
        ])
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Indicateur": cfg_txt, "Valeur": cfg_val})


def _render_fcf_projection_tab_content(result, currency):
    fcfs = result.projected_fcfs
    if not fcfs: return
    years = [f"An {i + 1}" for i in range(len(fcfs))]
    df = pd.DataFrame({"Période": years, "Flux": fcfs, "Actu": result.discount_factors,
                       "VA": [f * d for f, d in zip(fcfs, result.discount_factors)]})
    df.loc[len(df)] = {"Période": "TV", "Flux": result.terminal_value, "Actu": result.discount_factors[-1],
                       "VA": result.discounted_terminal_value}

    c1, c2 = st.columns([1, 2])
    with c1: st.dataframe(df, use_container_width=True, hide_index=True)
    with c2:
        chart = alt.Chart(df[df["Période"] != "TV"]).mark_bar(color="#4c78a8").encode(x='Période', y='VA')
        st.altair_chart(chart, use_container_width=True)


def _render_audit_category_table(details, category):
    items = [d for d in details if d.get('ui_category') == category]
    if not items: return
    st.markdown(f"**{category}**")
    data = [{"Statut": i.get('status', ''), "Test": i.get('test', ''), "Détail": i.get('reason', '')} for i in items]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def _render_audit_tab_content(financials, input_source):
    is_manual = (input_source == InputSource.MANUAL)
    if is_manual:
        st.info("Mode Expert : Contrôle de cohérence mathématique uniquement.")
    else:
        st.markdown(f"### Score : {financials.audit_score:.0f}/100 ({financials.audit_rating})")

    st.markdown("---")
    _render_audit_category_table(financials.audit_details, "Stabilité & Cohérence")
    col_a, col_b = st.columns(2)
    with col_a:
        _render_audit_category_table(financials.audit_details, "Qualité Données")
    with col_b:
        _render_audit_category_table(financials.audit_details, "Spécificité Hypothèses")
    _render_audit_category_table(financials.audit_details, "Adéquation Méthode")


def display_results(financials, params, result, mode, input_source):
    if not isinstance(result, DCFResult): return
    currency = financials.currency
    iv = result.intrinsic_value_per_share
    price = financials.current_price
    upside = (iv - price) / price if price > 0 else 0

    st.subheader(f"Valorisation : {financials.ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Prix Marché", format_currency(price, currency))

    val_label = "Valeur (P50)" if mode == ValuationMode.MONTE_CARLO else "Valeur Intrinsèque"
    c2.metric(val_label, format_currency(iv, currency), delta=f"{iv - price:+.2f}")
    c3.metric("Potentiel", f"{upside:+.1%}")

    st.markdown("---")
    audit_label = "Contrôle Tech." if input_source == InputSource.MANUAL else "Rapport Audit"
    t1, t2, t3, t4 = st.tabs(["Synthèse", "Projections", "Méthodologie", audit_label])

    with t1:
        _render_assumptions_tab_content(financials, params, result, mode, currency)
    with t2:
        _render_fcf_projection_tab_content(result, currency)
    with t3:
        if mode == ValuationMode.SIMPLE_FCFF:
            display_simple_dcf_formula(financials, params)
        elif mode == ValuationMode.FUNDAMENTAL_FCFF:
            display_fundamental_dcf_formula(financials, params)
        elif mode == ValuationMode.MONTE_CARLO:
            display_monte_carlo_formula(financials, params)
    with t4:
        _render_audit_tab_content(financials, input_source)
        if input_source == InputSource.AUTO: display_audit_methodology()