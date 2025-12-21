from __future__ import annotations
from typing import Optional, Dict, Any
import streamlit as st

from core.models import InputSource, ValuationMode, ValuationRequest
from core.methodology.texts import TOOLTIPS


def display_auto_inputs(
    default_ticker: str,
    default_years: int,
) -> Optional[ValuationRequest]:
    """
    MODE AUTO — Estimation standardisée et prudente.

    Principes :
    - Hypothèses normatives
    - Proxies autorisés
    - Audit complet et pénalisant
    - Responsabilité portée par le système
    """

    st.sidebar.subheader("Configuration — Mode AUTO")

    # ------------------------------------------------------------------
    # À PROPOS DU MODE AUTO
    # ------------------------------------------------------------------
    with st.sidebar.expander("ℹ️ À propos du mode AUTO", expanded=True):
        st.markdown(
            """
            **Mode AUTO = estimation standardisée et prudente**

            - Hypothèses financières **déduites automatiquement**
            - Utilisation de **proxies normatifs**
            - **Audit strict et pénalisant**
            - Résultats fournis **à titre indicatif**

            👉 Pour un contrôle total des hypothèses, utilisez le **mode EXPERT**.
            """
        )

    st.sidebar.markdown("---")

    # ------------------------------------------------------------------
    # 1. TICKER
    # ------------------------------------------------------------------
    ticker = st.sidebar.text_input(
        "Symbole boursier (Ticker)",
        value=default_ticker,
        help=TOOLTIPS.get("ticker")
    ).upper().strip()

    # ------------------------------------------------------------------
    # 2. HORIZON DE PROJECTION
    # ------------------------------------------------------------------
    years = st.sidebar.number_input(
        "Horizon de projection (années)",
        min_value=3,
        max_value=15,
        value=int(default_years),
        help=TOOLTIPS.get("years")
    )

    # ------------------------------------------------------------------
    # 3. MÉTHODE DE VALORISATION (UI → ENUM OFFICIEL)
    # ------------------------------------------------------------------
    strategies_map = {
        # DCF
        "Standard — DCF FCFF (Two-Stage)": ValuationMode.FCFF_TWO_STAGE,
        "Fondamental — FCFF normalisé": ValuationMode.FCFF_NORMALIZED,
        "Croissance / Tech — FCFF revenu": ValuationMode.FCFF_REVENUE_DRIVEN,

        # Modèles alternatifs
        "Graham — Value (1974)": ValuationMode.GRAHAM_1974_REVISED,
        "Banques — Residual Income Model (RIM)": ValuationMode.RESIDUAL_INCOME_MODEL,

        # Extension probabiliste
        "Monte Carlo — Analyse de risque": ValuationMode.FCFF_TWO_STAGE,
    }

    selected_label = st.sidebar.selectbox(
        "Méthode de valorisation",
        options=list(strategies_map.keys()),
        index=0,
        help="Sélectionnez une méthode adaptée au profil de l’entreprise."
    )

    mode = strategies_map[selected_label]

    # ------------------------------------------------------------------
    # 4. OPTIONS SPÉCIFIQUES (MONTE CARLO)
    # ------------------------------------------------------------------
    options: Dict[str, Any] = {}

    if "Monte Carlo" in selected_label:
        st.sidebar.markdown("---")
        st.sidebar.caption("⚠️ Extension probabiliste (non normative)")

        st.sidebar.markdown(
            """
            La simulation Monte Carlo **n’est pas une méthode de valorisation**.

            Elle permet uniquement :
            - l’analyse de **sensibilité**
            - l’étude de la **dispersion des scénarios**
            """
        )

        sims = st.sidebar.select_slider(
            "Nombre de simulations",
            options=[1000, 2000, 5000, 10000],
            value=2000
        )

        options["enable_monte_carlo"] = True
        options["num_simulations"] = sims

    st.sidebar.markdown("---")

    # ------------------------------------------------------------------
    # 5. VALIDATION
    # ------------------------------------------------------------------
    submitted = st.sidebar.button(
        "Lancer l’estimation",
        type="primary",
        use_container_width=True
    )

    if not submitted:
        return None

    if not ticker:
        st.sidebar.error("Le ticker est requis.")
        return None

    # ------------------------------------------------------------------
    # CONSTRUCTION DE LA REQUÊTE AUTO
    # ------------------------------------------------------------------
    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.AUTO,
        manual_params=None,
        options=options
    )
