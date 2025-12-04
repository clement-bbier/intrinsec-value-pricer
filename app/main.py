import os
import sys
import logging
from pathlib import Path

# --------------------------------------------------------------------------
# 🚨 BLOC CRITIQUE : Ajoutez la racine du projet à la liste des chemins (sys.path)
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]  # remonte de app/ vers le répertoire racine
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --------------------------------------------------------------------------


# --- Imports de librairies externes ---
import streamlit as st
import pandas as pd


# --------------------------------------------------------------------------
# ✅ IMPORTS LOCAUX (MAINTENANT AVEC L'IMPORT ABSOLU)
# Note : 'app' est le répertoire racine dans sys.path, donc 'app.workflow' fonctionne
# --------------------------------------------------------------------------
from app.workflow import run_workflow_and_display
from core.models import ValuationMode

# -------------------------------------------------
# Logging configuration
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("app.main")

# Silence yfinance logs
logging.getLogger("yfinance").setLevel(logging.ERROR)

# -------------------------------------------------
# Valuation modes – labels shown to the end-user
# -------------------------------------------------
MODE_LABELS = {
    ValuationMode.SIMPLE_FCFF: (
        "Méthode 1 – DCF Simple "
        "(Valeur d'entreprise basée sur le FCFF et le CAPEX)"
    ),
    ValuationMode.FUNDAMENTAL_FCFF: (
        "Méthode 2 – DCF Détaillé "
        "(FCFF construit à partir du compte de résultat, bilan et tableau des flux)"
    ),
    ValuationMode.MARKET_MULTIPLES: (
        "Méthode 3 – Comparables de Marché "
        "(valorisation par multiples: P/E, EV/EBITDA, etc.)"
    ),
    ValuationMode.ADVANCED_SIMULATION: (
        "Méthode 4 – Scénarios et Simulations "
        "(tests de stress, Monte Carlo, modèles LBO)"
    ),
}
LABEL_TO_MODE = {v: k for k, v in MODE_LABELS.items()}

# -------------------------------------------------
# Global config
# -------------------------------------------------
DEFAULT_PROJECTION_YEARS = 5


def main() -> None:
    st.set_page_config(
        page_title="Calculateur de Valeur Intrinsèque (DCF)",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🔎 Calculateur de Valeur Intrinsèque (DCF)")

    # Inputs de la barre latérale
    st.sidebar.header("Paramètres")

    ticker = (
        st.sidebar.text_input(
            "Symbole Boursier (Ticker)",
            value="AAPL",
            help="Exemple: AAPL, MSFT, TSLA",
        )
        .upper()
        .strip()
    )

    projection_years = st.sidebar.number_input(
        "Années de projection (n)",
        min_value=3,
        max_value=10,
        value=DEFAULT_PROJECTION_YEARS,
        step=1,
        help="Horizon de projection du DCF (en années).",
    )

    # Selectbox du mode de valorisation
    mode_label = st.sidebar.selectbox(
        "Méthode de valorisation",
        options=list(MODE_LABELS.values()),
        index=0,
        help="Choisissez la méthode utilisée pour calculer la valeur intrinsèque.",
    )
    mode = LABEL_TO_MODE[mode_label]
    logger.info("Mode de valorisation sélectionné dans l'interface : %s", mode.value)

    st.sidebar.markdown("---")
    run_button = st.sidebar.button("Lancer le Calcul", type="primary")

    if run_button:
        if not ticker:
            st.error("Veuillez entrer un symbole boursier (Ticker).")
        else:
            # Appel de la fonction déplacée dans app/workflow.py
            run_workflow_and_display(ticker, int(projection_years), mode)
    else:
        st.info(
            "Entrez un ticker et un horizon de projection à gauche, "
            "puis cliquez sur Lancer le Calcul."
        )


if __name__ == "__main__":
    main()