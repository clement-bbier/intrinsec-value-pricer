from typing import Sequence
from datetime import datetime

import streamlit as st
import pandas as pd
import altair as alt


def _get_sample_dates(df_price: pd.DataFrame, freq: str = "6ME") -> Sequence[datetime]:
    """
    Fonction utilitaire pour définir les dates auxquelles nous recalculons la valeur
    intrinsèque historique (par défaut : tous les 6 mois, basés sur les données de prix).
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

    # 2) Fusion des prix de marché avec l'historique de la VI
    df_plot = df_price.copy()

    if hist_iv_df is not None and not hist_iv_df.empty:
        # Assurer que la colonne Date est bien formatée pour la fusion
        hist_iv_df["Date"] = pd.to_datetime(hist_iv_df["Date"])
        df_plot = df_plot.merge(
            hist_iv_df[["Date", "Intrinsic Value"]], on="Date", how="outer"
        )

    # Remplir les valeurs de prix pour les dates de VI qui n'ont pas de prix (devrait être rare)
    df_plot = df_plot.sort_values("Date").ffill().dropna(subset=["Date"])

    # 4) NOUVEAU : Création du DataFrame pour le point unique de la VI Actuelle
    df_current_iv = pd.DataFrame()  # DataFrame vide par défaut

    if current_iv is not None and not df_price.empty:
        # Récupérer la dernière date du prix de marché pour aligner le point
        latest_date = df_price["Date"].max()

        df_current_iv = pd.DataFrame(
            {
                "Date": [latest_date],
                "Price": [current_iv],
                "Series": ["Current IV (Actuel)"]  # Libellé pour la légende
            }
        )
        # Assurez-vous que le type de données de la colonne Date correspond pour l'union
        df_current_iv["Date"] = pd.to_datetime(df_current_iv["Date"])

    # 5) Reshape en format long pour Altair et fusion avec le point actuel
    # On ne garde que les séries historiques à 'melter' : Market Price et Intrinsic Value Historique
    value_cols = [c for c in ["Market Price", "Intrinsic Value"] if c in df_plot.columns]

    if "Date" not in df_plot.columns or len(value_cols) == 0:
        st.warning(
            "Données insuffisantes pour tracer le graphique marché vs valeur intrinsèque."
        )
        return

    # Reshape des séries historiques (Prix et VI Historique)
    df_long = df_plot.melt(
        id_vars="Date",
        value_vars=value_cols,
        var_name="Series",
        value_name="Price",
    )

    # ⭐️ Fusion avec le point unique de la VI Actuelle
    if not df_current_iv.empty:
        df_long = pd.concat([df_long, df_current_iv], ignore_index=True)

    # Filtrer les NaN
    df_long = df_long.dropna(subset=["Price"])

    if df_long.empty:
        st.warning("Aucune donnée exploitable pour le graphique.")
        return

    # 6) Graphique Altair
    # La base sert pour l'encodage X, Y et le tooltip
    base = alt.Chart(df_long).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Price:Q", title="Price per share"),
        tooltip=[
            alt.Tooltip("Date:T", format="%Y-%m-%d"),
            "Series:N",
            alt.Tooltip("Price:Q", format=",.2f")
        ],
    )

    # Lignes pour les séries historiques (Market Price et Intrinsic Value Historique)
    line_chart = base.transform_filter(
        alt.FieldOneOfPredicate(field="Series", oneOf=["Market Price", "Intrinsic Value"])
    ).mark_line(point=True).encode(  # point=True ajoute les points pour les lignes historiques
        color=alt.Color("Series:N", title="Série"),
    )

    # Point unique pour la Valeur Intrinsèque Actuelle (très voyant)
    point_chart = base.transform_filter(
        alt.FieldEqualPredicate(field="Series", equal="Current IV (Actuel)")
    ).mark_point(
        size=150,  # Grande taille
        filled=True,
        strokeWidth=2,  # Contour épais
        stroke='#FFD700',  # Couleur Or pour le contour
        shape='diamond'  # Forme de diamant pour se démarquer
    ).encode(
        color=alt.value("#0000FF"),  # Couleur bleu foncé pour le remplissage
        shape=alt.Shape("Series:N", title="Série"),
    )

    # La fusion des deux calques (lignes + point)
    chart = (line_chart + point_chart).properties(
        title=f"Historique du prix de marché vs valeur intrinsèque estimée - {ticker}",
        height=400,
    ).interactive()

    st.altair_chart(chart, use_container_width=True)