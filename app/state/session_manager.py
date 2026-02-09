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

from app.state.store import get_state


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
        It delegates to `get_state()` which already handles the singleton
        creation, avoiding double-initialization.
        """
        # Delegate to the single source of truth — get_state() creates
        # the AppState if it doesn't exist yet.
        get_state()

    @staticmethod
    def reset_valuation() -> None:
        """
        Clears previous calculation results to force a fresh state.

        Typically triggered when the user modifies the Ticker or the Valuation
        Methodology. Does NOT call st.rerun() — the caller is responsible
        for controlling the rerun flow to prevent infinite loops.
        """
        state = get_state()
        state.clear_results()

    @staticmethod
    def set_error(message: str) -> None:
        """
        Registers a blocking error message in the global state.

        Parameters
        ----------
        message : str
            The localized error message to display to the user.
            Pass None to clear the error.
        """
        state = get_state()
        state.error_message = message if message else None