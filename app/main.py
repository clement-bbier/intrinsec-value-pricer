import logging
import sys
from pathlib import Path
from typing import Optional

# Configuration PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from app.workflow import run_workflow_and_display
from core.models import ValuationMode, InputSource
from app.ui_components.ui_inputs_expert import display_expert_inputs, ExpertReturn

# Logging Config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
    force=True,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("app.main")
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Constantes
MODE_LABELS_AUTO = {
    ValuationMode.SIMPLE_FCFF: "Méthode 1 : DCF Simple (Snapshot)",
    ValuationMode.FUNDAMENTAL_FCFF: "Méthode 2 : DCF Fondamental (Normatif)",
    ValuationMode.MONTE_CARLO: "Méthode 3 : Monte Carlo (Probabiliste)",
}
LABEL_TO_MODE_AUTO = {v: k for k, v in MODE_LABELS_AUTO.items()}
DEFAULT_PROJECTION_YEARS = 5
DEFAULT_TICKER = "PM"


def main() -> None:
    """Point d'entrée principal."""
    st.set_page_config(
        page_title="IV Pricer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Intrinsic Value Pricer")
    st.markdown(
        """
        Plateforme de valorisation d'entreprise par actualisation des flux de trésorerie (DCF).
        """
    )

    try:
        # --- SIDEBAR (PILOTAGE) ---
        st.sidebar.header("Configuration")

        mode_source = st.sidebar.radio(
            "Source des Hypothèses",
            ["Automatique (Marché)", "Manuelle (Expert)"],
            index=0,
            key="main_mode_selector"
        )

        # MODE AUTOMATIQUE
        if mode_source == "Automatique (Marché)":
            st.sidebar.divider()
            st.sidebar.subheader("Paramètres")

            ticker = st.sidebar.text_input("Symbole (Ticker)", value=DEFAULT_TICKER).upper().strip()

            projection_years = st.sidebar.number_input(
                "Horizon (Années)", min_value=3, max_value=15, value=DEFAULT_PROJECTION_YEARS
            )

            mode_label = st.sidebar.selectbox(
                "Méthode",
                options=list(MODE_LABELS_AUTO.values()),
                index=1
            )
            selected_mode = LABEL_TO_MODE_AUTO[mode_label]

            st.sidebar.divider()

            if st.sidebar.button("Lancer l'analyse", type="primary", use_container_width=True):
                if not ticker:
                    st.warning("Ticker invalide.")
                else:
                    logger.info(f"Launch AUTO | Ticker: {ticker} | Mode: {selected_mode.value}")
                    run_workflow_and_display(
                        ticker=ticker,
                        projection_years=int(projection_years),
                        mode=selected_mode,
                        input_source=InputSource.AUTO,
                        manual_params=None,
                        manual_beta=None
                    )
            else:
                st.info("Saisissez un ticker pour démarrer.")

        # MODE MANUEL
        else:
            st.sidebar.divider()
            st.sidebar.info("Le mode manuel active le module fondamental avec contrôle total des inputs.")

            # Appel du formulaire expert (qui contient son propre bouton)
            expert_input: Optional[ExpertReturn] = display_expert_inputs(
                DEFAULT_TICKER, DEFAULT_PROJECTION_YEARS
            )

            if expert_input is not None:
                ticker, years, params, beta, mode, is_submitted = expert_input

                if is_submitted:
                    logger.info(f"Launch MANUAL | Ticker: {ticker}")
                    run_workflow_and_display(
                        ticker=ticker,
                        projection_years=years,
                        mode=mode,
                        input_source=InputSource.MANUAL,
                        manual_params=params,
                        manual_beta=beta
                    )

    except Exception as main_e:
        logger.critical(f"CRITICAL FAILURE: {main_e}", exc_info=True)
        st.error("Une erreur critique est survenue.")
        st.exception(main_e)


if __name__ == "__main__":
    main()