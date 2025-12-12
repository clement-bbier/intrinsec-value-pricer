import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import logging
import streamlit as st

from app.workflow import run_workflow_and_display
from app.ui_components.ui_inputs_auto import display_auto_inputs
from app.ui_components.ui_inputs_expert import display_expert_request
from core.exceptions import ApplicationStartupError
from core.models import InputSource, ValuationRequest


logger = logging.getLogger("app.main")

DEFAULT_PROJECTION_YEARS = 5
DEFAULT_TICKER = "PM"


def _configure_logging() -> None:
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
    if not hasattr(st, "session_state"):
        raise ApplicationStartupError("Streamlit session_state is not available")


def _select_input_source() -> InputSource:
    st.sidebar.header("Configuration")
    label = st.sidebar.radio(
        "Source des Hypothèses",
        ["Automatique (Marché)", "Manuelle (Expert)"],
        index=0,
        key="main_mode_selector",
    )
    return InputSource.AUTO if label == "Automatique (Marché)" else InputSource.MANUAL


def main() -> None:
    _configure_logging()
    st.set_page_config(page_title="IV Pricer", layout="wide", initial_sidebar_state="expanded")

    try:
        _startup_self_check()
    except ApplicationStartupError as exc:
        logger.critical("STARTUP ERROR: %s", exc, exc_info=True)
        st.error(f"[STARTUP ERROR] {exc}")
        st.stop()

    st.title("Intrinsic Value Pricer")
    st.markdown("Plateforme de valorisation d'entreprise par actualisation des flux de trésorerie (DCF).")

    input_source = _select_input_source()

    request: ValuationRequest | None
    if input_source == InputSource.AUTO:
        request = display_auto_inputs(DEFAULT_TICKER, DEFAULT_PROJECTION_YEARS)
    else:
        request = display_expert_request(DEFAULT_TICKER, DEFAULT_PROJECTION_YEARS)

    if request is None:
        st.info("Configurez les inputs puis lancez l'analyse.")
        return

    run_workflow_and_display(request)


if __name__ == "__main__":
    main()
