"""
ui_charts.py

Visualisations — Chapitre 6
Représentation graphique de la valeur, du risque et de l’incertitude.

Principes :
- Les graphiques complètent l’audit (ils ne le remplacent pas)
- Aucune visualisation ne doit masquer une incohérence
- Style sobre, institutionnel, lisible
"""

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from typing import List, Optional, Callable


# ==============================================================================
# 1. HISTORIQUE DE PRIX — CONTEXTE DE MARCHÉ
# ==============================================================================

def display_price_chart(
    ticker: str,
    price_history: Optional[pd.DataFrame],
) -> None:
    """
    Évolution historique du prix de marché.
    Sert de contexte, pas de justification de la valeur intrinsèque.
    """

    if price_history is None or price_history.empty:
        st.info("Historique de prix indisponible.")
        return

    df = price_history.copy()

    # Normalisation Date
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    date_col = next(
        (c for c in df.columns if "date" in c.lower()),
        df.columns[0]
    )

    df = df.rename(columns={date_col: "Date"})
    if "Close" in df.columns:
        df["Prix"] = df["Close"]
    elif "Adj Close" in df.columns:
        df["Prix"] = df["Adj Close"]
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if numeric_cols.any():
            df["Prix"] = df[numeric_cols[0]]
        else:
            st.warning("Impossible d’identifier la série de prix.")
            return

    base = alt.Chart(df).encode(
        x=alt.X("Date:T", axis=alt.Axis(title=None)),
        tooltip=[
            alt.Tooltip("Date:T", title="Date"),
            alt.Tooltip("Prix:Q", format=",.2f", title="Prix")
        ]
    )

    line = base.mark_line(
        color="#1E88E5",
        strokeWidth=1.8
    ).encode(
        y=alt.Y("Prix:Q", scale=alt.Scale(zero=False), title="Prix de marché")
    )

    st.altair_chart(
        line.interactive().properties(height=300),
        use_container_width=True
    )


# ==============================================================================
# 2. MONTE CARLO — DISTRIBUTION D’INCERTITUDE
# ==============================================================================

def display_simulation_chart(
    simulation_results: List[float],
    market_price: float,
    currency: str
) -> None:
    """
    Distribution des valeurs intrinsèques simulées.
    Visualisation de l’incertitude (pas une prédiction).
    """

    if not simulation_results:
        st.warning("Aucune simulation Monte Carlo disponible.")
        return

    values = np.array(simulation_results)
    median_val = np.median(values)

    df = pd.DataFrame({"Valeur": values})

    hist = alt.Chart(df).mark_bar(
        color="#546E7A",
        opacity=0.75
    ).encode(
        x=alt.X(
            "Valeur:Q",
            bin=alt.Bin(maxbins=50),
            title=f"Valeur intrinsèque simulée ({currency})"
        ),
        y=alt.Y("count()", title="Fréquence"),
        tooltip=["count()"]
    )

    price_line = alt.Chart(
        pd.DataFrame({"x": [market_price]})
    ).mark_rule(
        color="#C62828",
        strokeWidth=2,
        strokeDash=[4, 2]
    ).encode(
        x="x",
        tooltip=[alt.Tooltip("x:Q", format=",.2f", title="Prix de marché")]
    )

    median_line = alt.Chart(
        pd.DataFrame({"x": [median_val]})
    ).mark_rule(
        color="#2E7D32",
        strokeWidth=2
    ).encode(
        x="x",
        tooltip=[alt.Tooltip("x:Q", format=",.2f", title="Médiane (P50)")]
    )

    st.subheader("Distribution Monte Carlo")
    st.caption(
        "Représentation de l’incertitude du modèle. "
        "La dispersion reflète la sensibilité aux hypothèses."
    )

    st.altair_chart(
        (hist + price_line + median_line).properties(height=320),
        use_container_width=True
    )


# ==============================================================================
# 3. SENSIBILITÉ WACC × CROISSANCE — ROBUSTESSE DU MODÈLE
# ==============================================================================

def display_sensitivity_heatmap(
    base_wacc: float,
    base_growth: float,
    calculator_func: Callable[[float, float], float],
    currency: str = "EUR"
) -> None:
    """
    Matrice de sensibilité WACC / Croissance terminale.

    Objectif :
    - tester la robustesse du modèle
    - visualiser les zones instables
    """

    st.subheader("Analyse de sensibilité (WACC × Croissance)")
    st.caption(
        "Impact des variations raisonnables du WACC et de la croissance "
        "sur la valeur intrinsèque."
    )

    wacc_shifts = [-0.01, -0.005, 0.0, 0.005, 0.01]
    growth_shifts = [-0.005, -0.0025, 0.0, 0.0025, 0.005]

    data = []

    for dw in wacc_shifts:
        for dg in growth_shifts:
            w = base_wacc + dw
            g = base_growth + dg

            if w <= g:
                continue

            try:
                value = calculator_func(w, g)
            except Exception:
                value = None

            if value is not None:
                data.append({
                    "WACC": f"{w:.2%}",
                    "Croissance": f"{g:.2%}",
                    "Valeur": value
                })

    if not data:
        st.warning("Analyse impossible : incohérence WACC / croissance.")
        return

    df = pd.DataFrame(data)

    heatmap = alt.Chart(df).mark_rect().encode(
        x=alt.X("Croissance:O", title="Croissance terminale (g)"),
        y=alt.Y("WACC:O", title="WACC"),
        color=alt.Color(
            "Valeur:Q",
            scale=alt.Scale(scheme="yellowgreenblue"),
            legend=None
        ),
        tooltip=[
            "WACC",
            "Croissance",
            alt.Tooltip("Valeur:Q", format=",.2f", title="Valeur")
        ]
    ).properties(height=350)

    text = heatmap.mark_text(
        baseline="middle",
        color="black"
    ).encode(
        text=alt.Text("Valeur:Q", format=",.0f")
    )

    st.altair_chart(heatmap + text, use_container_width=True)
