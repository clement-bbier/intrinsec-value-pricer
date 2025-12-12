import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import logging
from typing import Optional, Tuple

import streamlit as st

from app.ui_components.ui_inputs_auto import display_auto_inputs
from app.ui_components.ui_inputs_expert import display_expert_request
from app.workflow import run_workflow_and_display
from core.exceptions import ApplicationStartupError
from core.models import InputSource, ValuationRequest

logger = logging.getLogger("app.main")

DEFAULT_PROJECTION_YEARS = 5
DEFAULT_TICKER = "PM"

_EXEC_SIG_KEY = "_last_execution_signature"


def _configure_logging() -> None:
    """
    Configure deterministic console logging for Streamlit.
    Safe to call at each rerun (force=True).
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
    No network calls.
    """
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


def _execution_signature(request: ValuationRequest) -> Tuple[str, int, str, str]:
    """
    Computes a stable signature for de-duplicating executions during Streamlit reruns.
    Keep it minimal and deterministic.
    """
    return (
        request.ticker,
        int(request.projection_years),
        request.mode.value,
        request.input_source.value,
    )


def _should_execute(request: ValuationRequest) -> bool:
    """
    Prevent double execution when Streamlit reruns after a submit.
    If the same request signature is already executed in this session, skip.
    """
    sig = _execution_signature(request)
    last_sig = st.session_state.get(_EXEC_SIG_KEY)
    if last_sig == sig:
        logger.info("EXECUTION SKIPPED (duplicate rerun) | sig=%s", sig)
        return False
    st.session_state[_EXEC_SIG_KEY] = sig
    return True


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

    request: Optional[ValuationRequest]
    if input_source == InputSource.AUTO:
        request = display_auto_inputs(DEFAULT_TICKER, DEFAULT_PROJECTION_YEARS)
    else:
        request = display_expert_request(DEFAULT_TICKER, DEFAULT_PROJECTION_YEARS)

    if request is None:
        st.info("Configurez les inputs puis lancez l'analyse.")
        return

    if not _should_execute(request):
        return

    logger.info(
        "EXECUTION START | ticker=%s | years=%s | mode=%s | source=%s",
        request.ticker,
        request.projection_years,
        request.mode.value,
        request.input_source.value,
    )
    run_workflow_and_display(request)


if __name__ == "__main__":
    main()
