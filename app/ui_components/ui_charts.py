"""
app/ui_components/ui_charts.py
VISUALISATIONS — VERSION V3.3 (Hedge Fund Standard)
Rôle : Rendu graphique haute précision, alignement responsif et pédagogie.
Changements : Alignement de la matrice de corrélation et conformité Streamlit 2026.
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

    st.altair_chart(chart, width="stretch")


# ============================================================================
# 2. MONTE CARLO (DISTRIBUTION DES VALEURS)
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

    st.altair_chart(alt.layer(*layers).properties(height=320), width="stretch")

    # --- Synthèse Technique ---
    st.markdown(f"""
    **Synthèse de la distribution ({len(values)} scénarios) :**
    * Valeur centrale (P50) : {p50:,.2f} {currency}
    * Prix de marché : {market_price:,.2f} {currency}
    * Intervalle de confiance (P10-P90) : {p10:,.2f} à {p90:,.2f} (80% de probabilité)
    """)

# ============================================================================
# 3. SENSIBILITÉ & CORRÉLATION
# ============================================================================

def display_sensitivity_heatmap(base_wacc: float, base_growth: float, calculator_func: Callable, currency: str = "EUR") -> None:
    """Affiche une matrice de sensibilité bidimensionnelle (WACC vs g)."""
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

    st.altair_chart((heatmap + text).properties(height=350), width="stretch")


def display_correlation_heatmap(rho: float = -0.30) -> None:
    """Rendu de la matrice de corrélation. Fix : Alignement responsif."""
    corr_data = pd.DataFrame([
        {"X": "Beta (β)", "Y": "Beta (β)", "Val": 1.0},
        {"X": "Growth (g)", "Y": "Growth (g)", "Val": 1.0},
        {"X": "Beta (β)", "Y": "Growth (g)", "Val": rho},
        {"X": "Growth (g)", "Y": "Beta (β)", "Val": rho},
    ])

    base = alt.Chart(corr_data).encode(
        x=alt.X('X:N', title=None, axis=alt.Axis(labelAngle=0)), # Alignement horizontal
        y=alt.Y('Y:N', title=None)
    )

    heatmap = base.mark_rect().encode(
        color=alt.Color('Val:Q', scale=alt.Scale(scheme='redblue', domain=[-1, 1]), legend=None),
        tooltip=['X', 'Y', 'Val']
    )

    text = base.mark_text().encode(
        text=alt.Text('Val:Q', format='.2f'),
        color=alt.condition(
            (alt.datum.Val > 0.5) | (alt.datum.Val < -0.5),
            alt.value('white'),
            alt.value('black')
        )
    )

    # Propriétés de taille fixe pour le carré, mais responsive en largeur
    st.altair_chart((heatmap + text).properties(height=180), width="stretch")
    st.caption("Matrice de Corrélation des Inputs (Stochastique)")