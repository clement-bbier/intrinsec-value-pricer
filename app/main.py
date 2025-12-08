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
    force=True  # Force la reconfiguration si Streamlit l'a déjà fait
)
logger = logging.getLogger("app.main")

# Silence yfinance logs (trop verbeux)
logging.getLogger("yfinance").setLevel(logging.ERROR)

# -------------------------------------------------
# Valuation modes – labels affichés à l'utilisateur
# -------------------------------------------------
MODE_LABELS = {
    ValuationMode.SIMPLE_FCFF: (
        "Méthode 1 – DCF Simple "
        "(FCFF TTM, croissance constante)"
    ),
    ValuationMode.FUNDAMENTAL_FCFF: (
        "Méthode 2 – DCF Fondamental "
        "(3-Statement Light, FCFF lissé sur 3 ans)"
    ),
    ValuationMode.MONTE_CARLO: (
        "Méthode 3 – Simulation Monte Carlo "
        "(Distribution de probabilités, gestion du risque)"
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
        "Estimation de la valeur intrinsèque d'une entreprise cotée selon plusieurs méthodologies.\n\n"
        "**Attention :** ceci est un outil d'aide à la décision, pas un conseil en investissement."
    )

    # ------------------------------------------------------------------
    # Barre latérale – paramètres d'entrée
    # ------------------------------------------------------------------
    st.sidebar.header("Paramètres de l'Analyse")

    ticker = (
        st.sidebar.text_input(
            "Symbole Boursier (Ticker)",
            value="AAPL",
            help="Exemple : AAPL (Apple), MSFT (Microsoft), O (Realty Income), MC.PA (LVMH)",
        )
        .upper()
        .strip()
    )

    projection_years = st.sidebar.number_input(
        "Années de projection (n)",
        min_value=3,
        max_value=15,
        value=DEFAULT_PROJECTION_YEARS,
        step=1,
        help="Horizon de projection des flux de trésorerie (en années).",
    )

    mode_label = st.sidebar.selectbox(
        "Méthode de valorisation",
        options=list(MODE_LABELS.values()),
        index=0,
        help=(
            "**Méthode 1 (Simple)** : Rapide. Utilise les derniers flux connus (TTM). Idéal pour une première estimation.\n\n"
            "**Méthode 2 (Fondamentale)** : Robuste. Reconstruit les flux à partir du résultat opérationnel (EBIT) et du bilan, lissés sur 3 ans. Plus stable.\n\n"
            "**Méthode 3 (Monte Carlo)** : Avancée (Hedge Fund). Simule 2000 scénarios en faisant varier la croissance et le risque pour donner une fourchette de probabilité."
        ),
    )
    mode = LABEL_TO_MODE[mode_label]
    logger.info("Mode de valorisation sélectionné dans l'interface : %s", mode.value)

    st.sidebar.markdown("---")

    # Bouton d'action principal
    run_button = st.sidebar.button("Lancer l'Analyse", type="primary")

    # Zone principale
    if run_button:
        if not ticker:
            st.error("Veuillez entrer un symbole boursier (Ticker) valide.")
        else:
            # Appel au chef d'orchestre (Workflow)
            run_workflow_and_display(
                ticker=ticker,
                projection_years=int(projection_years),
                mode=mode,
            )
    else:
        # Message d'accueil par défaut
        st.info(
            "👈 **Mode d'emploi :**\n"
            "1. Entrez un ticker (ex: `NVDA`).\n"
            "2. Choisissez une méthode (commencez par la **Méthode 1** ou **2**).\n"
            "3. Cliquez sur **Lancer l'Analyse**.\n\n"
            "Pour une analyse de risque approfondie, utilisez la **Méthode 3**."
        )


if __name__ == "__main__":
    main()