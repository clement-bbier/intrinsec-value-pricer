import sys
import logging
from pathlib import Path
from typing import Optional

import streamlit as st
import yaml

# -----------------------------------------------------------------------------
# 1. SETUP PATH & LOGGING
# -----------------------------------------------------------------------------

# Permet l'import des modules core/app même si lancé depuis un sous-dossier
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Configuration du Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("app.main")

# Imports internes (après setup path)
from app.ui_components.ui_inputs_auto import display_auto_inputs
from app.ui_components.ui_inputs_expert import display_expert_request
from app.workflow import run_workflow_and_display
from core.models import InputSource, ValuationRequest

# -----------------------------------------------------------------------------
# 2. CONFIGURATION STREAMLIT
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Intrinsic Value Pricer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Chargement de la config YAML (Best Effort)
def load_config() -> dict:
    try:
        config_path = ROOT / "config" / "settings.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Impossible de charger settings.yaml: {e}")
    return {}


CONFIG = load_config()
DEFAULT_TICKER = CONFIG.get("default_ticker", "AAPL")
DEFAULT_YEARS = CONFIG.get("default_projection_years", 5)


# -----------------------------------------------------------------------------
# 3. APPLICATION PRINCIPALE
# -----------------------------------------------------------------------------

def main():
    st.title("Intrinsic Value Pricer")
    st.markdown(
        """
        **Plateforme de Valorisation Institutionnelle.** Comparez des méthodes de valorisation avancées (DCF, DDM, Graham, Monte Carlo) 
        avec une transparence totale et un audit intégré.
        """
    )

    # A. SÉLECTEUR DE MODE (Sidebar)
    st.sidebar.title("Paramètres")

    # Choix du mode d'entrée : Auto (Rapide) ou Expert (Détaillé)
    mode_input = st.sidebar.radio(
        "Mode de Saisie",
        options=[InputSource.AUTO.value, InputSource.MANUAL.value],
        format_func=lambda x: "🚀 Automatique (Yahoo)" if x == "AUTO" else "🛠️ Expert (Manuel)",
        help="Automatique : Récupère tout depuis Yahoo Finance.\nExpert : Permet de surcharger chaque hypothèse."
    )

    current_source = InputSource(mode_input)

    # B. AFFICHAGE DES INPUTS
    request: Optional[ValuationRequest] = None

    if current_source == InputSource.AUTO:
        # Le mode Auto est dans la sidebar
        request = display_auto_inputs(DEFAULT_TICKER, DEFAULT_YEARS)
    else:
        # Le mode Expert prend la page principale pour l'espace
        request = display_expert_request(DEFAULT_TICKER, DEFAULT_YEARS)

    # C. EXÉCUTION DU WORKFLOW
    # On attend que l'utilisateur ait cliqué sur le bouton dans les sous-composants
    if request:
        logger.info(f"Lancement Analyse : {request.ticker} [{request.mode.value}]")
        run_workflow_and_display(request)
    else:
        # État d'attente (Landing Page)
        if current_source == InputSource.AUTO:
            st.info("👈 Configurez l'analyse dans la barre latérale et cliquez sur 'Lancer'.")
        else:
            st.info("Remplissez les paramètres expert ci-dessus pour démarrer.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("Une erreur critique est survenue lors du démarrage de l'application.")
        logger.critical("App Crash", exc_info=True)
        with st.expander("Détails techniques"):
            st.exception(e)