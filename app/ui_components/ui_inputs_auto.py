from __future__ import annotations

from typing import Optional

import streamlit as st

from core.models import InputSource, ValuationMode, ValuationRequest


def display_auto_inputs(
    default_ticker: str,
    default_years: int,
) -> Optional[ValuationRequest]:
    """
    AUTO mode form.
    Returns ValuationRequest when submitted, else None.
    """
    st.sidebar.subheader("Paramètres (AUTO)")

    ticker = st.sidebar.text_input("Symbole (Ticker)", value=default_ticker).upper().strip()
    years = st.sidebar.number_input("Horizon (Années)", min_value=3, max_value=15, value=int(default_years))

    mode = st.sidebar.selectbox(
        "Méthode",
        options=[ValuationMode.SIMPLE_FCFF, ValuationMode.FUNDAMENTAL_FCFF, ValuationMode.MONTE_CARLO],
        format_func=lambda m: m.value,
        index=1,
    )

    submitted = st.sidebar.button("Lancer l'analyse", type="primary", use_container_width=True)
    if not submitted:
        return None

    if not ticker:
        st.sidebar.error("[INPUT ERROR] ticker is empty")
        return None

    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.AUTO,
    )
