import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from typing import List, Optional, Callable


# ==============================================================================
# 1. GRAPHIQUE HISTORIQUE DE PRIX
# ==============================================================================

def display_price_chart(
        ticker: str,
        price_history: Optional[pd.DataFrame],
        valuation_history: Optional[pd.DataFrame] = None
) -> None:
    """Affiche l'évolution du cours de bourse."""
    if price_history is None or price_history.empty:
        st.info("Historique de prix indisponible pour ce ticker.")
        return

    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex) and "Date" not in df.columns:
        df = df.reset_index()

    date_col = None
    for col in df.columns:
        if "date" in str(col).lower():
            date_col = col
            break

    if not date_col and isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        date_col = df.columns[0]

    if not date_col:
        return

    df = df.rename(columns={date_col: "Date", "Close": "Prix", "Adj Close": "Prix"})
    if "Prix" not in df.columns:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            df["Prix"] = df[numeric_cols[0]]
        else:
            return

    base = alt.Chart(df).encode(
        x=alt.X("Date:T", axis=alt.Axis(title=None, format="%Y-%m")),
        tooltip=["Date:T", alt.Tooltip("Prix:Q", format=",.2f")]
    )

    line = base.mark_line(color="#2962FF", strokeWidth=1.5).encode(
        y=alt.Y("Prix:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Prix de Clôture"))
    )

    st.altair_chart(line.interactive(), use_container_width=True)


# ==============================================================================
# 2. DISTRIBUTION MONTE CARLO (HISTOGRAMME)
# ==============================================================================

def display_simulation_chart(
        simulation_results: List[float],
        market_price: float,
        currency: str
) -> None:
    """Affiche la distribution des résultats Monte Carlo."""
    if not simulation_results:
        st.warning("Pas de données de simulation à afficher.")
        return

    df_sim = pd.DataFrame({"Valeur Intrinsèque": simulation_results})
    median_val = np.median(simulation_results)

    base = alt.Chart(df_sim)
    hist = base.mark_bar(color="#455A64", opacity=0.7).encode(
        x=alt.X("Valeur Intrinsèque:Q", bin=alt.Bin(maxbins=50), title=f"Valeur Intrinsèque ({currency})"),
        y=alt.Y("count()", title="Fréquence"),
        tooltip=["count()"]
    )

    price_line = alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(
        color='#D32F2F', strokeWidth=2, strokeDash=[4, 2]
    ).encode(x='x', tooltip=[alt.Tooltip('x', format=",.2f", title="Prix Actuel")])

    median_line = alt.Chart(pd.DataFrame({'x': [median_val]})).mark_rule(
        color='#388E3C', strokeWidth=2
    ).encode(x='x', tooltip=[alt.Tooltip('x', format=",.2f", title="Valeur Médiane (P50)")])

    st.altair_chart((hist + price_line + median_line).properties(height=300), use_container_width=True)


# ==============================================================================
# 3. HEATMAP DE SENSIBILITÉ (NOUVEAU - PHASE D)
# ==============================================================================

def display_sensitivity_heatmap(
        base_wacc: float,
        base_growth: float,
        calculator_func: Callable[[float, float], float],
        currency: str = "EUR"
) -> None:
    """
    Génère une matrice de sensibilité WACC vs Croissance (g).

    Args:
        base_wacc: Le WACC central du modèle.
        base_growth: Le taux de croissance perpétuelle central.
        calculator_func: Fonction lambda (wacc, g) -> intrinsic_value.
    """
    st.subheader("Analyse de Sensibilité")
    st.caption("Impact des variations du WACC et de la Croissance Terminale sur la valorisation.")

    # Création des axes (steps de 0.5% ou 0.25%)
    wacc_steps = [-0.01, -0.005, 0.0, 0.005, 0.01]
    g_steps = [-0.005, -0.0025, 0.0, 0.0025, 0.005]

    data = []
    for dw in wacc_steps:
        for dg in g_steps:
            w = base_wacc + dw
            g = base_growth + dg

            # Safety check (WACC > g)
            if w <= g + 0.001:
                val = None
            else:
                try:
                    val = calculator_func(w, g)
                except:
                    val = None

            if val:
                data.append({
                    "WACC": f"{w:.2%}",
                    "Growth": f"{g:.2%}",
                    "Value": val
                })

    if not data:
        st.warning("Impossible de générer la matrice (incohérence WACC/Croissance).")
        return

    df = pd.DataFrame(data)

    # Heatmap Altair
    heatmap = alt.Chart(df).mark_rect().encode(
        x=alt.X('Growth:O', title="Croissance Perpétuelle (g)"),
        y=alt.Y('WACC:O', title="Coût du Capital (WACC)"),
        color=alt.Color('Value:Q', scale=alt.Scale(scheme='yellowgreenblue'), legend=None),
        tooltip=['WACC', 'Growth', alt.Tooltip('Value:Q', format=",.2f", title="Valeur")]
    ).properties(height=350)

    text = heatmap.mark_text(baseline='middle').encode(
        text=alt.Text('Value:Q', format=",.0f"),
        color=alt.value('black')
    )

    st.altair_chart(heatmap + text, use_container_width=True)