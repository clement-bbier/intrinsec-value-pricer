import logging
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# 🚨 BLOC CRITIQUE : ajouter la racine du projet à sys.path
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]  # remonte de app/ vers le répertoire racine
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --------------------------------------------------------------------------


# --- Imports de librairies externes ---
import streamlit as st


# --- Imports locaux ---
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
# Valuation modes – labels affichés à l'utilisateur
# -------------------------------------------------
MODE_LABELS = {
    ValuationMode.SIMPLE_FCFF: (
        "Méthode 1 – DCF Simple "
        "(FCFF TTM = CFO - Capex, croissance constante)"
    ),
    ValuationMode.FUNDAMENTAL_FCFF: (
        "Méthode 2 – DCF Fondamental "
        "(FCFF à partir EBIT, D&A, Capex, ΔNWC lissé sur 3 ans)"
    ),
    ValuationMode.MARKET_MULTIPLES: (
        "Méthode 3 – Comparables de Marché "
        "(P/E, EV/EBITDA, etc. – à venir)"
    ),
    ValuationMode.ADVANCED_SIMULATION: (
        "Méthode 4 – Scénarios & Simulations "
        "(Monte Carlo, LBO, stress tests – à venir)"
    ),
}
LABEL_TO_MODE = {v: k for k, v in MODE_LABELS.items()}

DEFAULT_PROJECTION_YEARS = 5


def main() -> None:
    st.set_page_config(
        page_title="Calculateur de Valeur Intrinsèque (DCF)",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🔎 Calculateur de Valeur Intrinsèque (DCF)")
    st.markdown(
        "Estimation de la valeur intrinsèque d'une entreprise cotée à partir de modèles DCF.\n\n"
        "**Attention :** ceci est un outil pédagogique, pas un conseil en investissement."
    )

    # ------------------------------------------------------------------
    # Barre latérale – paramètres d'entrée
    # ------------------------------------------------------------------
    st.sidebar.header("Paramètres")

    ticker = (
        st.sidebar.text_input(
            "Symbole Boursier (Ticker)",
            value="AAPL",
            help="Exemple : AAPL, MSFT, TSLA, OR.PA, MC.PA",
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

    mode_label = st.sidebar.selectbox(
        "Méthode de valorisation",
        options=list(MODE_LABELS.values()),
        index=0,
        help=(
            "Choisissez la méthode utilisée pour calculer la valeur intrinsèque.\n\n"
            "– Méthode 1 : DCF simple basé sur le FCF TTM.\n"
            "– Méthode 2 : DCF fondamental basé sur un FCFF reconstruit à partir des 3 états financiers.\n"
            "– Méthodes 3 & 4 : en cours de développement."
        ),
    )
    mode = LABEL_TO_MODE[mode_label]
    logger.info("Mode de valorisation sélectionné dans l'interface : %s", mode.value)

    st.sidebar.markdown("---")
    run_button = st.sidebar.button("Lancer le Calcul", type="primary")

    if run_button:
        if not ticker:
            st.error("Veuillez entrer un symbole boursier (Ticker).")
        else:
            run_workflow_and_display(
                ticker=ticker,
                projection_years=int(projection_years),
                mode=mode,
            )
    else:
        st.info(
            "Entrez un ticker et un horizon de projection à gauche, choisissez la méthode de valorisation, "
            "puis cliquez sur **Lancer le Calcul**."
        )


if __name__ == "__main__":
    main()
