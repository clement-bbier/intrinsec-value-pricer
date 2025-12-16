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
    Formulaire Mode Automatique (Sidebar).
    Configure la requête sans demander de paramètres financiers complexes.
    L'utilisateur choisit juste le Ticker et la Stratégie.
    """
    st.sidebar.subheader("Configuration (Auto)")

    # 1. Ticker
    ticker = st.sidebar.text_input(
        "Symbole (Ticker)",
        value=default_ticker,
        help=TOOLTIPS["ticker"]
    ).upper().strip()

    # 2. Horizon
    years = st.sidebar.number_input(
        "Horizon (Années)",
        min_value=3, max_value=15, value=int(default_years),
        help=TOOLTIPS["years"]
    )

    # 3. Sélecteur de Stratégie (Mappage User-Friendly)
    strategies_map = {
        "Standard (FCF TTM)": ValuationMode.SIMPLE_FCFF,
        "Avancé (Fondamental)": ValuationMode.FUNDAMENTAL_FCFF,
        "Tech / Growth (Revenu)": ValuationMode.GROWTH_TECH,
        "Banque / Dividendes (DDM)": ValuationMode.DDM_BANKS,
        "Graham (Value Invest)": ValuationMode.GRAHAM_VALUE,
        "Monte Carlo (Probabiliste)": ValuationMode.MONTE_CARLO
    }

    selected_label = st.sidebar.selectbox(
        "Méthode de Valorisation",
        options=list(strategies_map.keys()),
        index=1,  # Par défaut : Fondamental
        help="Choisissez la stratégie adaptée au secteur de l'entreprise."
    )
    mode = strategies_map[selected_label]

    # 4. Options Spécifiques (Monte Carlo uniquement)
    options: Dict[str, Any] = {}

    if mode == ValuationMode.MONTE_CARLO:
        st.sidebar.markdown("---")
        st.sidebar.caption("Paramètres Simulation")
        sims = st.sidebar.select_slider(
            "Nombre de Simulations",
            options=[1000, 2000, 5000, 10000],
            value=2000
        )
        # On passe cette option via le dictionnaire générique de la requête
        options["num_simulations"] = sims

    st.sidebar.markdown("---")

    # 5. Validation
    # En mode Auto, le bouton est dans la sidebar pour être toujours accessible
    submitted = st.sidebar.button("Lancer l'analyse", type="primary", use_container_width=True)

    if not submitted:
        return None

    if not ticker:
        st.sidebar.error("Le ticker est requis.")
        return None

    # Construction de la requête simplifiée
    # InputSource.AUTO signale au Workflow d'utiliser le Provider pour tout remplir
    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.AUTO,
        manual_params=None,
        options=options
    )