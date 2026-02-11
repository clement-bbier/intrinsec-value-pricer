"""
app/state/store.py

STATE STORE — SINGLE SOURCE OF TRUTH
====================================
Role: Strictly typed definition of the Streamlit Session State.
Architecture: Singleton Pattern via Dataclass.
              Eliminates "magic strings" (e.g., st.session_state["my_key"]).

Standards:
- NumPy style docstrings.
- Type hints for all attributes.
"""

from dataclasses import dataclass, field
from typing import Any

import streamlit as st

from src.models.enums import ValuationMethodology
from src.models.valuation import ValuationResult


@dataclass
class AppState:
    """
    Typed representation of the application's persistent state.

    This class acts as the contract for data persistence across Streamlit reruns.
    Directly modifying st.session_state without going through this class is forbidden.

    Attributes
    ----------
    ticker : str
        The stock symbol currently being analyzed (e.g., "AAPL").
    is_expert_mode : bool
        Toggle between Auto (minimal inputs) and Expert (granular control) modes.
    selected_methodology : ValuationMethodology
        The active valuation strategy (e.g., FCFF, GRAHAM).
    last_result : Optional[ValuationResult]
        The output of the last successful valuation run. None if no run yet.
    result_hash : Optional[str]
        A lightweight hash of the result to detect context changes and invalidate caches.
    technical_cache : Dict[str, Any]
        Storage for expensive computed objects (e.g., Monte Carlo arrays) to avoid re-computation.
    should_run_valuation : bool
        Flag used by controllers to trigger the orchestration pipeline.
    error_message : Optional[str]
        Global error state to display blocking alerts to the user.
    """

    # --- 1. Navigation & Configuration ---
    ticker: str = "AAPL"
    is_expert_mode: bool = False
    selected_methodology: ValuationMethodology = ValuationMethodology.FCFF_STANDARD

    # --- 2. Results & Caching ---
    last_result: ValuationResult | None = None
    result_hash: str | None = None
    technical_cache: dict[str, Any] = field(default_factory=dict)

    # --- 3. Interface Flags (Spinners, Toasts) ---
    should_run_valuation: bool = False
    error_message: str | None = None

    def clear_results(self) -> None:
        """
        Resets the valuation outputs while keeping the configuration.
        Used when the user changes a critical input (like the Ticker).
        """
        self.last_result = None
        self.result_hash = None
        self.technical_cache.clear()
        self.error_message = None

    def set_result(self, result: ValuationResult) -> None:
        """
        Stores a successful valuation result and clears error state.

        Parameters
        ----------
        result : ValuationResult
            The completed valuation output.
        """
        self.last_result = result
        self.should_run_valuation = False
        self.error_message = None


def get_state() -> AppState:
    """
    Global accessor for the typed Application State.

    Returns
    -------
    AppState
        The singleton instance stored in st.session_state.
    """
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()
    return st.session_state.app_state
