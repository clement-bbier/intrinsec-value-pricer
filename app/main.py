import logging
import sys
from typing import Optional

import streamlit as st

from app.workflow import run_workflow_and_display
from app.ui_components.ui_inputs_expert import ExpertReturn, display_expert_inputs
from core.exceptions import ApplicationStartupError
from core.models import InputSource, ValuationMode

logger = logging.getLogger("app.main")

MODE_LABELS_AUTO = {
    ValuationMode.SIMPLE_FCFF: "Méthode 1 : DCF Simple (Snapshot)",
    ValuationMode.FUNDAMENTAL_FCFF: "Méthode 2 : DCF Fondamental (Normatif)",
    ValuationMode.MONTE_CARLO: "Méthode 3 : Monte Carlo (Probabiliste)",
}
LABEL_TO_MODE_AUTO = {label: mode for mode, label in MODE_LABELS_AUTO.items()}

DEFAULT_PROJECTION_YEARS = 5
DEFAULT_TICKER = "PM"


def _configure_logging() -> None:
    """
    Configure deterministic console logging for Streamlit execution.
    Must not depend on runtime state or external resources.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
        force=True,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _startup_self_check() -> None:
    """
    Deterministic startup checks.
    No network calls, no provider instantiation.
    """
    if not hasattr(st, "session_state"):
        raise ApplicationStartupError("Streamlit session_state is not available")


def _render_header() -> None:
    st.title("Intrinsic Value Pricer")
    st.markdown("Plateforme de valorisation d'entreprise par actualisation des flux de trésorerie (DCF).")


def _render_sidebar_mode_selector() -> InputSource:
    st.sidebar.header("Configuration")
    mode_source = st.sidebar.radio(
        "Source des Hypothèses",
        ["Automatique (Marché)", "Manuelle (Expert)"],
        index=0,
        key="main_mode_selector",
    )
    return InputSource.AUTO if mode_source == "Automatique (Marché)" else InputSource.MANUAL


def _run_auto_mode() -> None:
    st.sidebar.divider()
    st.sidebar.subheader("Paramètres")

    ticker = st.sidebar.text_input("Symbole (Ticker)", value=DEFAULT_TICKER).upper().strip()
    projection_years = st.sidebar.number_input(
        "Horizon (Années)", min_value=3, max_value=15, value=DEFAULT_PROJECTION_YEARS
    )
    mode_label = st.sidebar.selectbox("Méthode", options=list(LABEL_TO_MODE_AUTO.keys()), index=1)
    selected_mode = LABEL_TO_MODE_AUTO[mode_label]

    st.sidebar.divider()

    if st.sidebar.button("Lancer l'analyse", type="primary", use_container_width=True):
        if not ticker:
            st.warning("Ticker invalide.")
            return

        logger.info("Launch AUTO | Ticker=%s | Mode=%s", ticker, selected_mode.value)
        run_workflow_and_display(
            ticker=ticker,
            projection_years=int(projection_years),
            mode=selected_mode,
            input_source=InputSource.AUTO,
            manual_params=None,
            manual_beta=None,
        )
    else:
        st.info("Saisissez un ticker pour démarrer.")


def _run_manual_mode() -> None:
    st.sidebar.divider()
    st.sidebar.info("Le mode manuel active le module fondamental avec contrôle total des inputs.")

    expert_input: Optional[ExpertReturn] = display_expert_inputs(DEFAULT_TICKER, DEFAULT_PROJECTION_YEARS)
    if expert_input is None:
        return

    ticker, years, params, beta, mode, is_submitted = expert_input
    if not is_submitted:
        return

    logger.info("Launch MANUAL | Ticker=%s | Mode=%s", ticker, mode.value)
    run_workflow_and_display(
        ticker=ticker,
        projection_years=years,
        mode=mode,
        input_source=InputSource.MANUAL,
        manual_params=params,
        manual_beta=beta,
    )


def main() -> None:
    """
    Streamlit application entrypoint.
    Must remain deterministic at import time.
    """
    _configure_logging()

    st.set_page_config(page_title="IV Pricer", layout="wide", initial_sidebar_state="expanded")

    try:
        _startup_self_check()
    except ApplicationStartupError as exc:
        logger.critical("STARTUP ERROR: %s", exc, exc_info=True)
        st.error(f"[STARTUP ERROR] {exc}")
        st.stop()

    _render_header()
    input_source = _render_sidebar_mode_selector()

    try:
        if input_source == InputSource.AUTO:
            _run_auto_mode()
        else:
            _run_manual_mode()
    except Exception as exc:
        logger.critical("CRITICAL FAILURE: %s", exc, exc_info=True)
        st.error("Une erreur critique est survenue.")
        st.exception(exc)


if __name__ == "__main__":
    main()
