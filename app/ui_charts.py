from typing import Sequence
from datetime import datetime

import streamlit as st
import pandas as pd
import altair as alt


def _get_sample_dates(df_price: pd.DataFrame, freq: str = "1W") -> Sequence[datetime]:
    """
    Fonction utilitaire pour définir les dates auxquelles nous recalculons la valeur
    intrinsèque historique.

    Nouvelle fréquence par défaut : "1W" (Hebdomadaire) pour une haute résolution.
    """
    tmp = (
        df_price.set_index("Date")
        .resample(freq)
        .first()
        .dropna()
    )
    # Convertit l'index de Timestamp en datetime pour la fonction build_intrinsic_value_time_series
    return [dt.to_pydatetime() for dt in tmp.index]


def display_price_chart(
        ticker: str,
        price_history: pd.DataFrame | None,
        hist_iv_df: pd.DataFrame | None,
        current_iv: float | None = None,
) -> None:
    """
    Affiche le graphique prix de marché vs valeur intrinsèque historique.

    Parameters
    ----------
    ticker : str
        Ticker de l'action.
    price_history : pd.DataFrame | None
        Historique des prix, index = dates, colonnes incluant 'Close' ou 'Adj Close'.
    hist_iv_df : pd.DataFrame | None
        Historique des valorisations DCF avec au minimum :
        - une colonne 'Date' (datetime)
        - une colonne 'Intrinsic Value' (float)
        Peut être None (ex: Mode Monte Carlo).
    current_iv : float | None
        Valeur intrinsèque actuelle calculée (point unique).
    """
    # 1) Nettoyage initial et unification des dates
    df_price = pd.DataFrame()

    if price_history is not None and not price_history.empty:
        # Assurer que la colonne 'Date' existe et est de type datetime
        if price_history.index.name == "Date":
            df_price = price_history.reset_index()
        elif "Date" in price_history.columns:
            df_price = price_history.copy()
        else:
            # Assumer que la première colonne est le prix si pas de Date
            df_price = price_history.reset_index()
            df_price.columns = ["Date", "Market Price"]

        # S'assurer que la colonne Date est bien formatée et la colonne de prix renommée
        df_price["Date"] = pd.to_datetime(df_price["Date"])
        # Renomme la colonne de prix pour le graphique, en prenant la première colonne non-Date
        price_col = [c for c in df_price.columns if c.lower() not in ["date", "index"]][0]
        df_price = df_price.rename(columns={price_col: "Market Price"})[["Date", "Market Price"]]

    # 2) Fusion des prix de marché avec l'historique de la VI (si disponible)
    df_plot = df_price.copy()

    if hist_iv_df is not None and not hist_iv_df.empty:
        # Assurer que la colonne Date est bien formatée pour la fusion
        hist_iv_df["Date"] = pd.to_datetime(hist_iv_df["Date"])
        df_plot = df_plot.merge(
            hist_iv_df[["Date", "Intrinsic Value"]], on="Date", how="outer"
        )
        # Remplir les valeurs de prix pour les dates de VI qui n'ont pas de prix
        df_plot = df_plot.sort_values("Date").ffill().dropna(subset=["Date"])
    else:
        # Si pas d'historique VI (Mode Monte Carlo), on s'assure juste d'avoir les dates triées
        if not df_plot.empty:
            df_plot = df_plot.sort_values("Date")

    # 4) Création du DataFrame pour le point unique de la VI Actuelle
    df_current_iv = pd.DataFrame()

    if current_iv is not None and not df_price.empty:
        latest_date = df_price["Date"].max()
        df_current_iv = pd.DataFrame(
            {
                "Date": [latest_date],
                "Price": [current_iv],
                "Series": ["Current IV (Actuel)"]
            }
        )
        df_current_iv["Date"] = pd.to_datetime(df_current_iv["Date"])

    # 5) Reshape en format long pour Altair
    # On détermine quelles colonnes on a vraiment
    available_cols = ["Market Price"]
    if "Intrinsic Value" in df_plot.columns:
        available_cols.append("Intrinsic Value")

    # On filtre pour ne garder que ce qui est présent
    value_cols = [c for c in available_cols if c in df_plot.columns]

    if "Date" not in df_plot.columns or len(value_cols) == 0:
        st.warning(
            "Données insuffisantes pour tracer le graphique marché vs valeur intrinsèque."
        )
        return

    # Reshape
    df_long = df_plot.melt(
        id_vars="Date",
        value_vars=value_cols,
        var_name="Series",
        value_name="Price",
    )

    # Fusion avec le point unique
    if not df_current_iv.empty:
        df_long = pd.concat([df_long, df_current_iv], ignore_index=True)

    df_long = df_long.dropna(subset=["Price"])

    if df_long.empty:
        st.warning("Aucune donnée exploitable pour le graphique.")
        return

    # 6) Graphique Altair
    base = alt.Chart(df_long).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Price:Q", title="Price per share"),
        tooltip=[
            alt.Tooltip("Date:T", format="%Y-%m-%d"),
            "Series:N",
            alt.Tooltip("Price:Q", format=",.2f")
        ],
    )

    # Lignes (Market Price + evt Intrinsic Value Historique)
    line_chart = base.transform_filter(
        alt.FieldOneOfPredicate(field="Series", oneOf=["Market Price", "Intrinsic Value"])
    ).mark_line(point=False).encode(
        color=alt.Color("Series:N", title="Série"),
    )

    # Point unique VI Actuelle
    point_chart = base.transform_filter(
        alt.FieldEqualPredicate(field="Series", equal="Current IV (Actuel)")
    ).mark_point(
        size=150,
        filled=True,
        strokeWidth=2,
        stroke='#FFD700',
        shape='diamond'
    ).encode(
        color=alt.value("#0000FF"),
        shape=alt.Shape("Series:N", title="Série"),
    )

    chart = (line_chart + point_chart).properties(
        title=f"Historique du prix de marché vs valeur intrinsèque - {ticker}",
        height=400,
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


def display_simulation_chart(simulation_results: list[float], current_price: float, currency: str) -> None:
    """
    Affiche un histogramme de la distribution des valeurs intrinsèques simulées (Monte Carlo).
    """
    if not simulation_results:
        return

    st.markdown("### 🎲 Distribution de Probabilité (Monte Carlo)")

    df_sim = pd.DataFrame(simulation_results, columns=["Intrinsic Value"])

    # Calcul des stats
    median_val = df_sim["Intrinsic Value"].median()
    p10_val = df_sim["Intrinsic Value"].quantile(0.10)
    p90_val = df_sim["Intrinsic Value"].quantile(0.90)

    # Histogramme
    hist = alt.Chart(df_sim).mark_bar().encode(
        alt.X("Intrinsic Value:Q", bin=alt.Bin(maxbins=50), title=f"Valeur Intrinsèque ({currency})"),
        y=alt.Y('count()', title='Nombre de Scénarios'),
        tooltip=['count()']
    ).properties(
        height=300
    )

    # Lignes Repères
    rule_price = alt.Chart(pd.DataFrame({'x': [current_price]})).mark_rule(color='red', strokeWidth=3).encode(
        x='x:Q', tooltip=[alt.Tooltip('x:Q', title='Prix Actuel', format=',.2f')]
    )
    rule_median = alt.Chart(pd.DataFrame({'x': [median_val]})).mark_rule(color='green', strokeDash=[5, 5],
                                                                         strokeWidth=3).encode(
        x='x:Q', tooltip=[alt.Tooltip('x:Q', title='Médiane Simulée', format=',.2f')]
    )
    rule_p10 = alt.Chart(pd.DataFrame({'x': [p10_val]})).mark_rule(color='gray', strokeWidth=1).encode(x='x:Q')
    rule_p90 = alt.Chart(pd.DataFrame({'x': [p90_val]})).mark_rule(color='gray', strokeWidth=1).encode(x='x:Q')

    chart = (hist + rule_price + rule_median + rule_p10 + rule_p90).interactive()

    st.altair_chart(chart, use_container_width=True)

    st.caption(
        f"🟥 Prix Actuel ({current_price:.2f}) | "
        f"🟩 Médiane Simulée ({median_val:.2f}) | "
        f"⬜ Zone 80% de confiance ({p10_val:.2f} - {p90_val:.2f})"
    )