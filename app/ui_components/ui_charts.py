from typing import Sequence
from datetime import datetime
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np


def _get_sample_dates(df_price: pd.DataFrame, freq: str = "1W") -> Sequence[datetime]:
    if isinstance(df_price.index, pd.DatetimeIndex):
        df_tmp = df_price.copy()
    elif "Date" in df_price.columns:
        df_tmp = df_price.set_index("Date")
    else:
        return []
    tmp = df_tmp.resample(freq).first().dropna()
    return [dt.to_pydatetime() for dt in tmp.index]


def display_price_chart(ticker: str, price_history: pd.DataFrame | None, hist_iv_df: pd.DataFrame | None,
                        current_iv: float | None = None) -> None:
    if price_history is None or price_history.empty:
        st.info("Historique indisponible.")
        return

    # 1. Prix
    df_price = price_history.reset_index()
    if "Date" not in df_price.columns: df_price.columns = ["Date", "Close"]
    df_price["Date"] = pd.to_datetime(df_price["Date"])
    df_price = df_price.rename(columns={df_price.columns[1]: "Valeur"})
    df_price["Type"] = "Prix Marché"

    # 2. Valeur (IV)
    df_iv = pd.DataFrame()
    if hist_iv_df is not None and not hist_iv_df.empty:
        hist_iv_df["Date"] = pd.to_datetime(hist_iv_df["Date"])
        df_iv = hist_iv_df[["Date", "Intrinsic Value"]].rename(columns={"Intrinsic Value": "Valeur"})
        df_iv["Type"] = "Valeur Intrinsèque"

    # 3. Continuité (Fusion Actuel + Historique)
    current_point_mark = None
    if current_iv:
        last_market_date = df_price["Date"].max()

        # Coupe nette avant la date actuelle pour éviter les zigzags
        if not df_iv.empty: df_iv = df_iv[df_iv["Date"] < last_market_date]

        # Ajout du point actuel
        df_curr = pd.DataFrame({"Date": [last_market_date], "Valeur": [current_iv], "Type": ["Valeur Intrinsèque"]})
        df_iv = pd.concat([df_iv, df_curr], ignore_index=True)

        # Marqueur Losange
        current_point_mark = alt.Chart(df_curr).mark_point(
            shape="diamond", size=100, filled=True, color="#1f77b4"
        ).encode(
            x="Date:T", y="Valeur:Q", tooltip=[alt.Tooltip("Valeur", format=".2f")]
        )

    # --- RENDER ---
    line_price = alt.Chart(df_price).mark_line(color="#d62728", strokeWidth=1.5).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%Y")),
        y=alt.Y("Valeur:Q", title="Prix / Valeur", scale=alt.Scale(zero=False)),
        tooltip=["Date:T", alt.Tooltip("Valeur", format=".2f"), "Type"]
    )

    line_iv = alt.Chart(df_iv).mark_line(strokeDash=[5, 3], color="#1f77b4", strokeWidth=1.5).encode(
        x="Date:T", y="Valeur:Q", tooltip=["Date:T", alt.Tooltip("Valeur", format=".2f")]
    ) if not df_iv.empty else None

    final_chart = line_price
    if line_iv: final_chart += line_iv
    if current_point_mark: final_chart += current_point_mark

    st.altair_chart(final_chart.properties(height=350, title=f"Historique {ticker}").interactive(),
                    use_container_width=True)


def display_simulation_chart(simulation_results: list[float], current_price: float, currency: str) -> None:
    if not simulation_results: return
    df_sim = pd.DataFrame(simulation_results, columns=["VI"])

    chart = alt.Chart(df_sim).mark_bar(color="#7f97b2").encode(
        x=alt.X("VI:Q", bin=alt.Bin(maxbins=40), title=f"Valeur ({currency})"),
        y=alt.Y('count()', title=None),
        tooltip=['count()']
    ).properties(height=250, title="Distribution des Scénarios")

    rule = alt.Chart(pd.DataFrame({'x': [current_price]})).mark_rule(color='#d62728', strokeWidth=2).encode(x='x')
    st.altair_chart(chart + rule, use_container_width=True)