import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from typing import List, Optional


# ==============================================================================
# 1. GRAPHIQUE HISTORIQUE DE PRIX
# ==============================================================================

def display_price_chart(
        ticker: str,
        price_history: Optional[pd.DataFrame],
        valuation_history: Optional[pd.DataFrame] = None
) -> None:
    """
    Affiche l'évolution du cours de bourse (et optionnellement de la valeur intrinsèque).
    Utilise Altair pour un rendu interactif et performant.
    """
    if price_history is None or price_history.empty:
        st.info("Historique de prix indisponible pour ce ticker.")
        return

    # 1. Préparation des Données
    # On s'attend à un index Datetime ou une colonne 'Date'
    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex) and "Date" not in df.columns:
        # Tentative de reset index si l'index est la date
        df = df.reset_index()

    # Standardisation des colonnes
    # On cherche une colonne de date
    date_col = None
    for col in df.columns:
        if "date" in str(col).lower():
            date_col = col
            break

    if not date_col and isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        date_col = df.columns[0]  # Suppose que l'index devient la première colonne

    if not date_col:
        st.warning("Format de l'historique de prix non reconnu.")
        return

    # Renommage pour Altair
    df = df.rename(columns={date_col: "Date", "Close": "Prix", "Adj Close": "Prix"})
    # Garder uniquement Date et Prix
    if "Prix" not in df.columns:
        # Fallback : prend la première colonne numérique
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            df["Prix"] = df[numeric_cols[0]]
        else:
            return

    # 2. Construction du Graphique (Ligne de Prix)
    base = alt.Chart(df).encode(
        x=alt.X("Date:T", axis=alt.Axis(title=None, format="%Y-%m")),
        tooltip=["Date:T", alt.Tooltip("Prix:Q", format=",.2f")]
    )

    line = base.mark_line(
        color="#2962FF",
        strokeWidth=1.5
    ).encode(
        y=alt.Y("Prix:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Prix de Clôture"))
    )

    # 3. Ajout Valeur Intrinsèque Historique (Optionnel - Chapitre Futur)
    chart = line

    if valuation_history is not None and not valuation_history.empty:
        # TODO: Implémenter la superposition quand le module historique sera prêt
        pass

    # 4. Rendu Final
    st.altair_chart(
        chart.interactive(),
        use_container_width=True
    )


# ==============================================================================
# 2. DISTRIBUTION MONTE CARLO (HISTOGRAMME)
# ==============================================================================

def display_simulation_chart(
        simulation_results: List[float],
        market_price: float,
        currency: str
) -> None:
    """
    Affiche la distribution des résultats de Monte Carlo.
    Visualisation : Histogramme des fréquences + Lignes verticales (Prix vs Valeur).
    """
    if not simulation_results:
        st.warning("Pas de données de simulation à afficher.")
        return

    # Conversion en DataFrame pour Altair
    df_sim = pd.DataFrame({"Valeur Intrinsèque": simulation_results})

    # Statistiques clés pour les lignes verticales
    median_val = np.median(simulation_results)

    # 1. Histogramme
    base = alt.Chart(df_sim)

    hist = base.mark_bar(
        color="#455A64",
        opacity=0.7
    ).encode(
        x=alt.X(
            "Valeur Intrinsèque:Q",
            bin=alt.Bin(maxbins=50),
            title=f"Valeur Intrinsèque ({currency})"
        ),
        y=alt.Y("count()", title="Fréquence"),
        tooltip=["count()"]
    )

    # 2. Ligne Prix de Marché (Rouge)
    price_line = alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(
        color='#D32F2F',
        strokeWidth=2,
        strokeDash=[4, 2]
    ).encode(
        x='x',
        tooltip=[alt.Tooltip('x', format=",.2f", title="Prix Actuel")]
    )

    # 3. Ligne Valeur Médiane (Verte)
    median_line = alt.Chart(pd.DataFrame({'x': [median_val]})).mark_rule(
        color='#388E3C',
        strokeWidth=2
    ).encode(
        x='x',
        tooltip=[alt.Tooltip('x', format=",.2f", title="Valeur Médiane (P50)")]
    )

    # Combinaison
    final_chart = (hist + price_line + median_line).properties(
        height=300,
        title="Distribution des Probabilités de Valeur"
    )

    st.altair_chart(final_chart, use_container_width=True)

    # Légende textuelle discrète
    st.caption(
        f"🟥 Prix de Marché: {market_price:,.2f} {currency} | "
        f"🟩 Valeur Médiane: {median_val:,.2f} {currency}"
    )