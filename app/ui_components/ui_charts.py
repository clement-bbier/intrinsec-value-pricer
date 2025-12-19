"""
app/ui_components/ui_charts.py

VISUALISATIONS — VALEUR, RISQUE & INCERTITUDE
Version : V2.0 — Chapitres 6 & 7 conformes

STATUT NORMATIF
---------------
Ce module assure exclusivement la restitution VISUELLE des résultats.

Principes non négociables :
- Les graphiques COMPLÈTENT l’audit, ils ne le remplacent jamais
- Aucune visualisation ne doit masquer une incohérence économique
- Monte Carlo = représentation d’INCERTITUDE, pas de prédiction
- Style institutionnel : sobre, lisible, non promotionnel

Les graphiques :
- ne modifient aucun calcul
- n’influencent aucun score
- n’introduisent aucune interprétation implicite
"""

from __future__ import annotations

from typing import List, Optional, Callable

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st


# ============================================================================
# 1. HISTORIQUE DE PRIX — CONTEXTE DE MARCHÉ
# ============================================================================

def display_price_chart(
    ticker: str,
    price_history: Optional[pd.DataFrame],
) -> None:
    """
    Affiche l’évolution historique du prix de marché.

    Rôle :
    - fournir un CONTEXTE de marché
    - ne JAMAIS justifier la valeur intrinsèque
    """

    if price_history is None or price_history.empty:
        st.info("Historique de prix indisponible.")
        return

    df = price_history.copy()

    # Normalisation de la date
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    date_col = next(
        (c for c in df.columns if "date" in c.lower()),
        df.columns[0]
    )

    df = df.rename(columns={date_col: "Date"})

    # Détection robuste du prix
    if "Close" in df.columns:
        df["Prix"] = df["Close"]
    elif "Adj Close" in df.columns:
        df["Prix"] = df["Adj Close"]
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            st.warning("Impossible d’identifier une série de prix.")
            return
        df["Prix"] = df[numeric_cols[0]]

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
        y=alt.Y(
            "Prix:Q",
            scale=alt.Scale(zero=False),
            title="Prix de marché"
        )
    )

    st.altair_chart(
        line.interactive().properties(height=300),
        use_container_width=True
    )


# ============================================================================
# 2. MONTE CARLO — DISTRIBUTION D’INCERTITUDE
# ============================================================================

def display_simulation_chart(
    simulation_results: List[float],
    market_price: float,
    currency: str
) -> None:
    """
    Représentation de la distribution Monte Carlo.

    Rôle :
    - visualiser la DISPERSION des valeurs
    - illustrer la sensibilité aux hypothèses
    - ne jamais suggérer une prédiction de prix
    """

    if not simulation_results:
        st.warning("Aucune simulation Monte Carlo disponible.")
        return

    values = np.array(simulation_results, dtype=float)

    median_val = float(np.median(values))
    p10 = float(np.percentile(values, 10))
    p90 = float(np.percentile(values, 90))

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

    # --- Repères visuels ---
    rules = []

    if market_price and market_price > 0:
        rules.append(
            alt.Chart(pd.DataFrame({"x": [market_price]}))
            .mark_rule(
                color="#C62828",
                strokeWidth=2,
                strokeDash=[4, 2]
            )
            .encode(
                x="x",
                tooltip=[
                    alt.Tooltip("x:Q", format=",.2f", title="Prix de marché")
                ]
            )
        )

    rules.append(
        alt.Chart(pd.DataFrame({"x": [median_val]}))
        .mark_rule(
            color="#2E7D32",
            strokeWidth=2
        )
        .encode(
            x="x",
            tooltip=[
                alt.Tooltip("x:Q", format=",.2f", title="Médiane (P50)")
            ]
        )
    )

    rules.append(
        alt.Chart(pd.DataFrame({"x": [p10, p90]}))
        .mark_rule(
            color="#9E9E9E",
            strokeDash=[2, 2]
        )
        .encode(
            x="x"
        )
    )

    st.subheader("Distribution Monte Carlo")
    st.caption(
        "Visualisation de l’incertitude du modèle. "
        "La dispersion reflète la sensibilité aux hypothèses, "
        "pas une prévision de marché."
    )

    chart = hist
    for r in rules:
        chart += r

    st.altair_chart(
        chart.properties(height=320),
        use_container_width=True
    )


# ============================================================================
# 3. ANALYSE DE SENSIBILITÉ — WACC × CROISSANCE
# ============================================================================

def display_sensitivity_heatmap(
    base_wacc: float,
    base_growth: float,
    calculator_func: Callable[[float, float], Optional[float]],
    currency: str = "EUR"
) -> None:
    """
    Matrice de sensibilité WACC / Croissance terminale.

    Rôle :
    - tester la ROBUSTESSE du modèle
    - mettre en évidence les zones instables
    """

    st.subheader("Analyse de sensibilité (WACC × Croissance)")
    st.caption(
        "Impact de variations raisonnables du WACC et de la croissance "
        "sur la valeur intrinsèque."
    )

    wacc_shifts = [-0.01, -0.005, 0.0, 0.005, 0.01]
    growth_shifts = [-0.005, -0.0025, 0.0, 0.0025, 0.005]

    rows = []

    for dw in wacc_shifts:
        for dg in growth_shifts:
            wacc = base_wacc + dw
            growth = base_growth + dg

            # Invariant économique fondamental
            if wacc <= growth:
                continue

            try:
                value = calculator_func(wacc, growth)
            except Exception:
                value = None

            if value is not None:
                rows.append({
                    "WACC": f"{wacc:.2%}",
                    "Croissance": f"{growth:.2%}",
                    "Valeur": value
                })

    if not rows:
        st.warning("Analyse impossible : incohérence WACC / croissance.")
        return

    df = pd.DataFrame(rows)

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

    labels = heatmap.mark_text(
        baseline="middle",
        color="black"
    ).encode(
        text=alt.Text("Valeur:Q", format=",.0f")
    )

    st.altair_chart(heatmap + labels, use_container_width=True)
