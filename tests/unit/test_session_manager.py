"""
tests/unit/test_session_manager.py

SESSION MANAGER UNIT TESTS
==========================
Role: Validate session lifecycle management, atomic clear_results(),
and state flush behavior on critical input changes.
"""

from unittest.mock import MagicMock, patch

from app.state.store import AppState


class TestAppStateClearResults:
    """Tests the atomic clear_results() method on AppState."""

    def test_clear_results_resets_last_result(self):
        """After clear, last_result must be None."""
        state = AppState()
        state.last_result = MagicMock()
        state.clear_results()
        assert state.last_result is None

    def test_clear_results_resets_result_hash(self):
        """After clear, result_hash must be None."""
        state = AppState()
        state.result_hash = "abc123"
        state.clear_results()
        assert state.result_hash is None

    def test_clear_results_clears_technical_cache(self):
        """After clear, technical_cache must be empty."""
        state = AppState()
        state.technical_cache["mc_stats"] = [1, 2, 3]
        state.clear_results()
        assert len(state.technical_cache) == 0

    def test_clear_results_resets_error_message(self):
        """After clear, error_message must be None."""
        state = AppState()
        state.error_message = "Something failed"
        state.clear_results()
        assert state.error_message is None

    def test_clear_results_preserves_ticker(self):
        """Clear should NOT reset the ticker configuration."""
        state = AppState()
        state.ticker = "GOOGL"
        state.last_result = MagicMock()
        state.clear_results()
        assert state.ticker == "GOOGL"

    def test_clear_results_preserves_methodology(self):
        """Clear should NOT reset the methodology."""
        from src.models.enums import ValuationMethodology

        state = AppState()
        state.selected_methodology = ValuationMethodology.DDM
        state.last_result = MagicMock()
        state.clear_results()
        assert state.selected_methodology == ValuationMethodology.DDM

    def test_clear_results_preserves_projection_years(self):
        """Clear should NOT reset projection_years."""
        state = AppState()
        state.projection_years = 10
        state.last_result = MagicMock()
        state.clear_results()
        assert state.projection_years == 10

    def test_clear_results_is_atomic(self):
        """All fields must be cleared in a single call — no partial state."""
        state = AppState()
        state.last_result = MagicMock()
        state.result_hash = "hash"
        state.technical_cache["key"] = "value"
        state.error_message = "error"

        state.clear_results()

        assert state.last_result is None
        assert state.result_hash is None
        assert len(state.technical_cache) == 0
        assert state.error_message is None


class TestAppStateSetResult:
    """Tests the set_result() method on AppState."""

    def test_set_result_stores_result(self):
        """set_result should store the result object."""
        state = AppState()
        mock_result = MagicMock()
        state.set_result(mock_result)
        assert state.last_result is mock_result

    def test_set_result_clears_run_flag(self):
        """set_result should set should_run_valuation to False."""
        state = AppState()
        state.should_run_valuation = True
        state.set_result(MagicMock())
        assert state.should_run_valuation is False

    def test_set_result_clears_error(self):
        """set_result should clear any existing error message."""
        state = AppState()
        state.error_message = "previous error"
        state.set_result(MagicMock())
        assert state.error_message is None


class TestSessionManagerMethods:
    """Tests the SessionManager static methods."""

    @patch("app.state.session_manager.get_state")
    def test_reset_valuation_calls_clear_results(self, mock_get_state):
        """reset_valuation should invoke clear_results on the state."""
        from app.state.session_manager import SessionManager

        mock_state = MagicMock()
        mock_get_state.return_value = mock_state

        SessionManager.reset_valuation()
        mock_state.clear_results.assert_called_once()

    @patch("app.state.session_manager.get_state")
    def test_set_error_stores_message(self, mock_get_state):
        """set_error should store the error message on the state."""
        from app.state.session_manager import SessionManager

        mock_state = MagicMock()
        mock_get_state.return_value = mock_state

        SessionManager.set_error("Test error")
        assert mock_state.error_message == "Test error"

    @patch("app.state.session_manager.get_state")
    def test_set_error_clears_on_empty_string(self, mock_get_state):
        """set_error with empty string should clear to None."""
        from app.state.session_manager import SessionManager

        mock_state = MagicMock()
        mock_get_state.return_value = mock_state

        SessionManager.set_error("")
        assert mock_state.error_message is None

    @patch("app.state.session_manager.get_state")
    def test_initialize_session_calls_get_state(self, mock_get_state):
        """initialize_session should call get_state to bootstrap."""
        from app.state.session_manager import SessionManager

        SessionManager.initialize_session()
        mock_get_state.assert_called_once()
