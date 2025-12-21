"""
app/ui_components/ui_charts.py
VISUALISATIONS — VALEUR, RISQUE & INCERTITUDE
Version : V2.2 — Bugfix & Clean
"""

from __future__ import annotations

from typing import List, Optional, Callable
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

# ============================================================================
# 1. HISTORIQUE DE PRIX
# ============================================================================

def display_price_chart(ticker: str, price_history: Optional[pd.DataFrame]) -> None:
    if price_history is None or price_history.empty:
        st.info(f"Historique de prix indisponible pour {ticker}.")
        return

    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.reset_index()

    date_col = next((c for c in df.columns if str(c).lower() in ['date', 'index']), None)
    if not date_col:
        return

    cols = df.columns.tolist()
    price_col = "Close" if "Close" in cols else ("Adj Close" if "Adj Close" in cols else None)
    if not price_col and len(df.select_dtypes(include=[np.number]).columns) > 0:
        price_col = df.select_dtypes(include=[np.number]).columns[0]

    if not price_col:
        return

    df = df.rename(columns={date_col: "Date", price_col: "Prix"}).dropna(subset=["Date", "Prix"])

    chart = alt.Chart(df).mark_line(color='#1E88E5', strokeWidth=1.5).encode(
        x=alt.X('Date:T', title=None, axis=alt.Axis(format='%Y-%m')),
        y=alt.Y('Prix:Q', scale=alt.Scale(zero=False), title=None),
        tooltip=[alt.Tooltip('Date:T', format='%d %b %Y'), alt.Tooltip('Prix:Q', format=',.2f')]
    ).properties(height=300, title=f"Historique : {ticker}").interactive()

    # Utilisation de la nouvelle API Streamlit si possible, sinon fallback
    st.altair_chart(chart, use_container_width=True)


# ============================================================================
# 2. MONTE CARLO
# ============================================================================

def display_simulation_chart(simulation_results: List[float], market_price: float, currency: str) -> None:
    if not simulation_results:
        st.warning("Pas de données de simulation.")
        return

    values = np.array([v for v in simulation_results if v is not None and not np.isnan(v)])
    if len(values) == 0:
        return

    p50 = np.median(values)
    p10 = np.percentile(values, 10)
    p90 = np.percentile(values, 90)

    df_sim = pd.DataFrame({"Valeur": values})

    hist = alt.Chart(df_sim).mark_bar(color="#546E7A", opacity=0.8).encode(
        x=alt.X("Valeur:Q", bin=alt.Bin(maxbins=60), title=f"Valeur ({currency})"),
        y=alt.Y("count()", title=None),
        tooltip=[alt.Tooltip("count()", title="Nb Scénarios")]
    )

    rule_p50 = alt.Chart(pd.DataFrame({'x': [p50]})).mark_rule(color="#2E7D32", strokeWidth=3).encode(x='x')
    rule_quantiles = alt.Chart(pd.DataFrame({'x': [p10, p90]})).mark_rule(color="#90A4AE", strokeDash=[4, 4]).encode(x='x')

    layers = [hist, rule_p50, rule_quantiles]
    if market_price and market_price > 0:
        rule_market = alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(
            color="#D32F2F", strokeWidth=2, strokeDash=[5, 2]
        ).encode(x='x')
        layers.append(rule_market)

    st.subheader("Monte Carlo (Distribution)")
    st.altair_chart(alt.layer(*layers).properties(height=300), use_container_width=True)
    st.caption(f"P10: {p10:,.2f} | Médiane: {p50:,.2f} | P90: {p90:,.2f} {currency}")


# ============================================================================
# 3. SENSIBILITÉ (HEATMAP)
# ============================================================================

def display_sensitivity_heatmap(base_wacc: float, base_growth: float, calculator_func: Callable, currency: str = "EUR") -> None:
    st.subheader("Sensibilité (WACC / Croissance)")

    wacc_steps = [-0.010, -0.005, 0.0, 0.005, 0.010]
    growth_steps = [-0.005, -0.0025, 0.0, 0.0025, 0.005]
    data = []

    for dw in wacc_steps:
        for dg in growth_steps:
            w = base_wacc + dw
            g = base_growth + dg
            if w <= g + 0.001: continue
            try:
                val = calculator_func(w, g)
                if val and val > 0:
                    data.append({"WACC": w, "Growth": g, "Valeur": round(val, 2)})
            except: continue

    if not data:
        st.warning("Matrice impossible (WACC trop proche de g).")
        return

    df = pd.DataFrame(data)
    heatmap = alt.Chart(df).mark_rect().encode(
        x=alt.X('Growth:O', title="Croissance (g)", axis=alt.Axis(format='.2%')),
        y=alt.Y('WACC:O', title="WACC", axis=alt.Axis(format='.2%')),
        color=alt.Color('Valeur:Q', scale=alt.Scale(scheme='yellowgreenblue'), legend=None),
        tooltip=[alt.Tooltip('WACC', format='.2%'), alt.Tooltip('Valeur', format=',.0f')]
    ).properties(height=350)

    text = heatmap.mark_text(baseline='middle').encode(
        text=alt.Text('Valeur:Q', format=',.0f'),
        color=alt.value('black')
    )

    st.altair_chart(heatmap + text, use_container_width=True)