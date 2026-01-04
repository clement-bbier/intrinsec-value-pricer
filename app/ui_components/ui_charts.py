"""
app/ui_components/ui_charts.py
VISUALISATIONS — VALEUR, RISQUE & INCERTITUDE
Version : V3.2 — Légendes Explicites & Pédagogie

Changements :
- Ajout d'une légende textuelle claire pour Monte Carlo.
- Amélioration de la lisibilité des graphiques.
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
    """Affiche l'historique de prix avec une ligne simple et propre."""
    if price_history is None or price_history.empty:
        st.info(f"Historique de prix indisponible pour {ticker}.")
        return

    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.reset_index()

    # Détection intelligente des colonnes
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
        tooltip=[alt.Tooltip('Date:T', format='%d %b %Y'), alt.Tooltip('Prix:Q', format=',.2f')]
    ).properties(height=300, title=f"Historique de marché : {ticker}").interactive()

    st.altair_chart(chart, use_container_width=True)


# ============================================================================
# 2. MONTE CARLO (AVEC LÉGENDE EXPLICITE)
# ============================================================================

def display_simulation_chart(simulation_results: List[float], market_price: float, currency: str) -> None:
    """Affiche l'histogramme Monte Carlo et une synthèse technique factuelle."""
    if not simulation_results:
        st.warning("Pas de données de simulation disponibles.")
        return

    values = np.array([v for v in simulation_results if v is not None and not np.isnan(v)])
    if len(values) == 0: return

    p50 = np.median(values)
    p10 = np.percentile(values, 10)
    p90 = np.percentile(values, 90)

    df_sim = pd.DataFrame({"Valeur": values})

    # --- Graphique ---
    hist = alt.Chart(df_sim).mark_bar(color="#546E7A", opacity=0.7).encode(
        x=alt.X("Valeur:Q", bin=alt.Bin(maxbins=50), title=f"Valeur Intrinsèque ({currency})"),
        y=alt.Y("count()", title="Fréquence")
    )
    rule_p50 = alt.Chart(pd.DataFrame({'x': [p50]})).mark_rule(color="#2E7D32", strokeWidth=3).encode(x='x')
    rule_quantiles = alt.Chart(pd.DataFrame({'x': [p10, p90]})).mark_rule(color="#90A4AE", strokeDash=[4, 4]).encode(
        x='x')

    layers = [hist, rule_p50, rule_quantiles]
    if market_price > 0:
        layers.append(alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(color="#D32F2F", strokeWidth=2,
                                                                               strokeDash=[5, 2]).encode(x='x'))

    st.altair_chart(alt.layer(*layers).properties(height=320), use_container_width=True)

    # --- Synthèse Technique (Sans Emojis) ---
    st.markdown(f"""
    **Synthèse de la distribution ({len(values)} scénarios) :**
    * Valeur centrale (P50) : {p50:,.2f} {currency}
    * Prix de marché : {market_price:,.2f} {currency}
    * Intervalle de confiance (P10-P90) : {p10:,.2f} à {p90:,.2f} (80% de probabilité)
    """)

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

    # Heatmap interactif
    base = alt.Chart(df).encode(
        x=alt.X('Growth:O', title="Croissance (g)", axis=alt.Axis(format='.2%')),
        y=alt.Y('WACC:O', title="WACC / Ke", axis=alt.Axis(format='.2%'))
    )

    heatmap = base.mark_rect().encode(
        color=alt.Color('Valeur:Q', scale=alt.Scale(scheme='yellowgreenblue'), legend=None),
        tooltip=[
            alt.Tooltip('WACC', format='.2%', title="Taux (WACC)"),
            alt.Tooltip('Growth', format='.2%', title="Croissance"),
            alt.Tooltip('Valeur', format=',.2f', title=f"Valeur ({currency})")
        ]
    )

    text = base.mark_text(baseline='middle').encode(
        text=alt.Text('Valeur:Q', format=',.0f'),
        color=alt.condition(
            alt.datum.Valeur > df['Valeur'].quantile(0.5),
            alt.value('white'),
            alt.value('black')
        )
    )

    st.altair_chart((heatmap + text).properties(height=350), use_container_width=True)