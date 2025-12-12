from __future__ import annotations

from typing import Optional

import streamlit as st

from core.models import InputSource, ValuationMode, ValuationRequest
from core.methodology.texts import TOOLTIPS


def display_auto_inputs(
        default_ticker: str,
        default_years: int,
) -> Optional[ValuationRequest]:
    """
    Formulaire Mode Automatique.
    """
    st.sidebar.subheader("Configuration (Auto)")

    ticker = st.sidebar.text_input(
        "Symbole (Ticker)",
        value=default_ticker,
        help=TOOLTIPS["ticker"]
    ).upper().strip()

    years = st.sidebar.number_input(
        "Horizon (Années)",
        min_value=3, max_value=15, value=int(default_years),
        help=TOOLTIPS["years"]
    )

    mode = st.sidebar.selectbox(
        "Méthode de Valorisation",
        options=[ValuationMode.SIMPLE_FCFF, ValuationMode.FUNDAMENTAL_FCFF, ValuationMode.MONTE_CARLO],
        format_func=lambda m: m.value,
        index=1,
    )

    # Options spécifiques Monte Carlo
    mc_options = {}
    if mode == ValuationMode.MONTE_CARLO:
        sims = st.sidebar.select_slider(
            "Nombre de Simulations",
            options=[1000, 2000, 5000, 10000],
            value=2000
        )
        mc_options["num_simulations"] = sims

    st.sidebar.markdown("---")

    submitted = st.sidebar.button("Lancer l'analyse", type="primary", use_container_width=True)

    if not submitted:
        return None

    if not ticker:
        st.sidebar.error("Le ticker est requis.")
        return None

    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.AUTO,
        options=mc_options
    )