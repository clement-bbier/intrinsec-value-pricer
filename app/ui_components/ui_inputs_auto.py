"""
app/ui_components/ui_inputs_auto.py — VERSION FINALE V7.6
Rôle : Masquage strict et dynamique de la section Risque pour Graham.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
import streamlit as st

from core.models import InputSource, ValuationMode, ValuationRequest
from core.methodology.texts import TOOLTIPS

def display_auto_inputs(default_ticker: str, default_years: int) -> Optional[ValuationRequest]:
    st.sidebar.subheader("Configuration : Mode AUTO")

    with st.sidebar.expander("Note méthodologique", expanded=False):
        st.markdown("- Hypothèses déduites automatiquement.\n- Audit de fiabilité strict.")

    st.sidebar.divider()

    # 1. IDENTIFICATION
    ticker = st.sidebar.text_input("Ticker", value=default_ticker, help=TOOLTIPS.get("ticker")).upper().strip()

    # 2. HORIZON
    years = st.sidebar.number_input("Horizon (années)", min_value=3, max_value=15, value=int(default_years))

    # 3. MÉTHODE DE VALORISATION
    strategies_map = {
        "Standard : DCF FCFF": ValuationMode.FCFF_TWO_STAGE,
        "Fondamental : FCFF lissé": ValuationMode.FCFF_NORMALIZED,
        "Croissance : FCFF Growth": ValuationMode.FCFF_REVENUE_DRIVEN,
        "Value : Modèle de Graham": ValuationMode.GRAHAM_1974_REVISED,
        "Banques : Modèle RIM": ValuationMode.RESIDUAL_INCOME_MODEL,
    }

    selected_label = st.sidebar.selectbox("Méthode de valorisation", options=list(strategies_map.keys()), index=0)
    mode = strategies_map[selected_label]

    # ------------------------------------------------------------------
    # 4. ANALYSE DE RISQUE (BLOC DYNAMIQUE)
    # ------------------------------------------------------------------
    options: Dict[str, Any] = {"enable_monte_carlo": False}

    # Utilisation de la propriété centralisée pour le masquage
    if mode.supports_monte_carlo:
        st.sidebar.divider()
        st.sidebar.markdown("#### 5. Analyse de Risque")
        enable_mc = st.sidebar.toggle("Activer Monte Carlo", value=False)

        if enable_mc:
            sims = st.sidebar.select_slider(
                "Itérations de la simulation",
                options=[1000, 2000, 5000, 10000],
                value=2000
            )
            options = {"enable_monte_carlo": True, "num_simulations": sims}

    st.sidebar.divider()

    # 5. BOUTON DE LANCEMENT
    if st.sidebar.button("Lancer l'estimation", type="primary", width="stretch"):
        if not ticker:
            st.sidebar.error("Le ticker est requis.")
            return None

        return ValuationRequest(
            ticker=ticker,
            projection_years=int(years),
            mode=mode,
            input_source=InputSource.AUTO,
            manual_params=None,
            options=options
        )
    return None