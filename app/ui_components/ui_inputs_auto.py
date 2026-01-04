"""
app/ui_components/ui_inputs_auto.py
MODE AUTO — ESTIMATION STANDARDISÉE ET PRUDENTE (V7.1)
Rôle : Configuration assistée avec hypothèses normatives et audit strict.
Version : Épurée (Zéro Émoji).
"""

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
    Rendu du terminal de saisie pour le mode automatique.
    Principes : Hypothèses déduites, audit complet, responsabilité système.
    """

    st.sidebar.subheader("Configuration : Mode AUTO")

    # ------------------------------------------------------------------
    # NOTE MÉTHODOLOGIQUE
    # ------------------------------------------------------------------
    with st.sidebar.expander("Note méthodologique", expanded=True):
        st.markdown(
            """
            **Estimation standardisée et prudente**

            - Hypothèses financières déduites automatiquement.
            - Utilisation de proxies normatifs et sécurisés.
            - Audit de fiabilité strict et pénalisant.
            - Résultats fournis à titre indicatif uniquement.

            Note : Pour un contrôle total des variables (Rf, Beta, MRP), utilisez le **mode EXPERT**.
            """
        )

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # 1. IDENTIFICATION DU TITRE
    # ------------------------------------------------------------------
    ticker = st.sidebar.text_input(
        "Symbole boursier (Ticker)",
        value=default_ticker,
        help=TOOLTIPS.get("ticker")
    ).upper().strip()

    # ------------------------------------------------------------------
    # 2. HORIZON TEMPOREL
    # ------------------------------------------------------------------
    years = st.sidebar.number_input(
        "Horizon de projection (années)",
        min_value=3,
        max_value=15,
        value=int(default_years),
        help=TOOLTIPS.get("years")
    )

    # ------------------------------------------------------------------
    # 3. MÉTHODE DE VALORISATION (MAPPING ENUM)
    # ------------------------------------------------------------------
    strategies_map = {
        "Standard : DCF FCFF (Two-Stage)": ValuationMode.FCFF_TWO_STAGE,
        "Fondamental : FCFF normalisé": ValuationMode.FCFF_NORMALIZED,
        "Croissance : FCFF revenu (Growth)": ValuationMode.FCFF_REVENUE_DRIVEN,
        "Value : Modèle de Graham (1974)": ValuationMode.GRAHAM_1974_REVISED,
        "Banques : Residual Income Model (RIM)": ValuationMode.RESIDUAL_INCOME_MODEL,
        "Analyse de risque : Monte Carlo": ValuationMode.FCFF_TWO_STAGE,
    }

    selected_label = st.sidebar.selectbox(
        "Méthode de valorisation",
        options=list(strategies_map.keys()),
        index=0,
        help="Sélectionnez une méthode adaptée au profil de l'entreprise."
    )

    mode = strategies_map[selected_label]

    # ------------------------------------------------------------------
    # 4. ANALYSE DE RISQUE (STOCHASTIQUE)
    # ------------------------------------------------------------------
    options: Dict[str, Any] = {}

    if "Monte Carlo" in selected_label:
        st.sidebar.divider()
        st.sidebar.caption("Note : Extension probabiliste")

        st.sidebar.markdown(
            """
            La simulation Monte Carlo est un complément d'analyse permettant d'évaluer 
            la dispersion des scénarios et la sensibilité du modèle aux variables clés.
            """
        )

        sims = st.sidebar.select_slider(
            "Itérations de la simulation",
            options=[1000, 2000, 5000, 10000],
            value=2000
        )

        options["enable_monte_carlo"] = True
        options["num_simulations"] = sims

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # 5. VALIDATION DE LA REQUÊTE
    # ------------------------------------------------------------------
    submitted = st.sidebar.button(
        "Lancer l'estimation",
        type="primary",
        use_container_width=True
    )

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
        manual_params=None,
        options=options
    )