"""
app/ui_components/ui_charts.py
VISUALISATIONS — VERSION V3.3 (Hedge Fund Standard)
Rôle : Rendu graphique haute précision utilisant les constantes i18n.
"""

from __future__ import annotations

from typing import List, Optional, Callable
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

from app.ui_components.ui_texts import ChartTexts

# ============================================================================
# 1. HISTORIQUE DE PRIX
# ============================================================================

def display_price_chart(ticker: str, price_history: Optional[pd.DataFrame]) -> None:
    """Affiche l'historique de prix avec les labels centralisés."""
    if price_history is None or price_history.empty:
        st.info(ChartTexts.PRICE_UNAVAILABLE.format(ticker=ticker))
        return

    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.reset_index()

    date_col = next((c for c in df.columns if str(c).lower() in ['date', 'index']), None)
    if not date_col: return

    cols = df.columns.tolist()
    price_col = "Close" if "Close" in cols else ("Adj Close" if "Adj Close" in cols else None)
    if not price_col and len(df.select_dtypes(include=[np.number]).columns) > 0:
        price_col = df.select_dtypes(include=[np.number]).columns[0]

    if not price_col: return

    df = df.rename(columns={date_col: "Date", price_col: "Prix"}).dropna(subset=["Date", "Prix"])

    chart = alt.Chart(df).mark_line(color='#1E88E5', strokeWidth=1.5).encode(
        x=alt.X('Date:T', title=None, axis=alt.Axis(format='%Y-%m')),
        y=alt.Y('Prix:Q', scale=alt.Scale(zero=False), title=None),
        tooltip=[
            alt.Tooltip('Date:T', format=ChartTexts.DATE_FORMAT, title=ChartTexts.TOOLTIP_DATE),
            alt.Tooltip('Prix:Q', format=',.2f', title=ChartTexts.TOOLTIP_PRICE)
        ]
    ).properties(
        height=300,
        title=ChartTexts.PRICE_HISTORY_TITLE.format(ticker=ticker)
    ).interactive()

    st.altair_chart(chart, width="stretch")


# ============================================================================
# 2. MONTE CARLO (DISTRIBUTION DES VALEURS)
# ============================================================================

def display_simulation_chart(simulation_results: List[float], market_price: float, currency: str) -> None:
    """Affiche l'histogramme Monte Carlo avec synthèse technique localisée."""
    if not simulation_results:
        st.warning(ChartTexts.SIM_UNAVAILABLE)
        return

    values = np.array([v for v in simulation_results if v is not None and not np.isnan(v)])
    if len(values) == 0: return

    p50 = np.median(values)
    p10 = np.percentile(values, 10)
    p90 = np.percentile(values, 90)

    df_sim = pd.DataFrame({"Valeur": values})

    hist = alt.Chart(df_sim).mark_bar(color="#546E7A", opacity=0.7).encode(
        x=alt.X("Valeur:Q", bin=alt.Bin(maxbins=50), title=ChartTexts.SIM_AXIS_X.format(currency=currency)),
        y=alt.Y("count()", title=ChartTexts.SIM_AXIS_Y)
    )
    rule_p50 = alt.Chart(pd.DataFrame({'x': [p50]})).mark_rule(color="#2E7D32", strokeWidth=3).encode(x='x')
    rule_quantiles = alt.Chart(pd.DataFrame({'x': [p10, p90]})).mark_rule(color="#90A4AE", strokeDash=[4, 4]).encode(x='x')

    layers = [hist, rule_p50, rule_quantiles]
    if market_price > 0:
        layers.append(alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(color="#D32F2F", strokeWidth=2, strokeDash=[5, 2]).encode(x='x'))

    st.altair_chart(alt.layer(*layers).properties(height=320), width="stretch")

    st.markdown(f"""
    {ChartTexts.SIM_SUMMARY_TITLE.format(count=len(values))}
    * {ChartTexts.SIM_SUMMARY_P50} : {p50:,.2f} {currency}
    * {ChartTexts.SIM_SUMMARY_PRICE} : {market_price:,.2f} {currency}
    * {ChartTexts.SIM_SUMMARY_CI} : {p10:,.2f} à {p90:,.2f} {ChartTexts.SIM_SUMMARY_PROB.format(prob=80)}
    """)

# ============================================================================
# 3. SENSIBILITÉ & CORRÉLATION
# ============================================================================

def display_sensitivity_heatmap(base_wacc: float, base_growth: float, calculator_func: Callable, currency: str = "EUR") -> None:
    """Affiche une matrice de sensibilité avec titres i18n."""
    st.subheader(ChartTexts.SENS_TITLE)

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
        st.warning(ChartTexts.SENS_UNAVAILABLE)
        return

    df = pd.DataFrame(data)

    base = alt.Chart(df).encode(
        x=alt.X('Growth:O', title=ChartTexts.SENS_AXIS_X, axis=alt.Axis(format='.2%')),
        y=alt.Y('WACC:O', title=ChartTexts.SENS_AXIS_Y, axis=alt.Axis(format='.2%'))
    )

    heatmap = base.mark_rect().encode(
        color=alt.Color('Valeur:Q', scale=alt.Scale(scheme='yellowgreenblue'), legend=None),
        tooltip=[
            alt.Tooltip('WACC', format='.2%', title=ChartTexts.SENS_TOOLTIP_WACC),
            alt.Tooltip('Growth', format='.2%', title=ChartTexts.SENS_TOOLTIP_GROWTH),
            alt.Tooltip('Valeur', format=',.2f', title=ChartTexts.SENS_TOOLTIP_VAL.format(currency=currency))
        ]
    )

    text = base.mark_text(baseline='middle').encode(
        text=alt.Text('Valeur:Q', format=',.0f'),
        color=alt.condition(alt.datum.Valeur > df['Valeur'].quantile(0.5), alt.value('white'), alt.value('black'))
    )

    st.altair_chart((heatmap + text).properties(height=350), width="stretch")


def display_correlation_heatmap(rho: float = -0.30) -> None:
    """Rendu de la matrice de corrélation avec légende centralisée."""
    corr_data = pd.DataFrame([
        {"X": "Beta (β)", "Y": "Beta (β)", "Val": 1.0},
        {"X": "Growth (g)", "Y": "Growth (g)", "Val": 1.0},
        {"X": "Beta (β)", "Y": "Growth (g)", "Val": rho},
        {"X": "Growth (g)", "Y": "Beta (β)", "Val": rho},
    ])

    base = alt.Chart(corr_data).encode(
        x=alt.X('X:N', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Y:N', title=None)
    )

    heatmap = base.mark_rect().encode(
        color=alt.Color('Val:Q', scale=alt.Scale(scheme='redblue', domain=[-1, 1]), legend=None),
        tooltip=['X', 'Y', 'Val']
    )

    text = base.mark_text().encode(
        text=alt.Text('Val:Q', format='.2f'),
        color=alt.condition((alt.datum.Val > 0.5) | (alt.datum.Val < -0.5), alt.value('white'), alt.value('black'))
    )

    st.altair_chart((heatmap + text).properties(height=180), width="stretch")
    st.caption(ChartTexts.CORREL_CAPTION)