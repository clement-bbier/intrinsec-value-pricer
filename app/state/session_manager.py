"""
app/state/session_manager.py

SESSION LIFECYCLE MANAGER
=========================
Role: Handles initialization, persistence, and safe resets of the user session.
Architecture: Static Utility Class (Stateless Manager).

Standards:
- English code and comments.
- NumPy style docstrings.
"""

import streamlit as st
from app.state.store import AppState, get_state


class SessionManager:
    """
    Manages the lifecycle of the Streamlit session state.

    Responsibilities:
    1. Initialize the AppState singleton on the first load.
    2. Handle hard resets when critical context changes (e.g. Ticker change).
    3. Provide global error setters.
    """

    @staticmethod
    def initialize_session() -> None:
        """
        Bootstraps the session state on application startup.

        This method must be called at the very top of `main.py`.
        It ensures that `st.session_state.app_state` exists before any view is rendered.
        """
        if "initialized" not in st.session_state:
            # 1. Instantiate the Single Source of Truth
            st.session_state.app_state = AppState()

            # 2. Flag as initialized to prevent overwriting on reruns
            st.session_state.initialized = True

    @staticmethod
    def reset_valuation() -> None:
        """
        Clears previous calculation results to force a fresh state.

        Typically triggered when the user modifies the Ticker or the Valuation Methodology.
        Triggers a `st.rerun()` to refresh the UI immediately.
        """
        state = get_state()
        state.clear_results()
        st.rerun()

    @staticmethod
    def set_error(message: str) -> None:
        """
        Registers a blocking error message in the global state.

        Parameters
        ----------
        message : str
            The localized error message to display to the user.
        """
        state = get_state()
        state.error_message = message