"""
tests/unit/test_session_manager.py

Tests for the SessionManager (Phase 1 — State Management).

Validates:
- Initialization of session state with defaults
- clear_results() purges all result-related state
- on_config_change() detects changes and triggers clear
- get/set_active_request() type-safe access
"""

import pytest
from unittest.mock import patch, MagicMock

from src.domain.models import (
    ValuationRequest,
    ValuationMode,
    InputSource,
    DCFParameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    SOTPParameters,
    ScenarioParameters,
)


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state as a dictionary."""
    state = {}
    with patch("app.state.session_manager.st") as mock_st:
        mock_st.session_state = state
        mock_st.rerun = MagicMock()
        yield state, mock_st


@pytest.fixture
def sample_request():
    """Minimal valuation request for testing."""
    params = DCFParameters(
        rates=CoreRateParameters(),
        growth=GrowthParameters(projection_years=5),
        monte_carlo=MonteCarloConfig(enable_monte_carlo=False),
        sotp=SOTPParameters(enabled=False),
        scenarios=ScenarioParameters(enabled=False),
    )
    return ValuationRequest(
        ticker="AAPL",
        projection_years=5,
        mode=ValuationMode.FCFF_STANDARD,
        input_source=InputSource.AUTO,
        manual_params=params,
    )


class TestSessionManagerInit:
    """Tests for SessionManager.init()."""

    def test_init_sets_defaults(self, mock_session_state):
        """init() should populate session state with all expected keys."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()

        assert "active_request" in state
        assert "last_config" in state
        assert "result_cache_hash" in state
        assert "cached_monte_carlo_data" in state
        assert "active_result_tab" in state
        assert "render_context_cache" in state

    def test_init_does_not_overwrite_existing(self, mock_session_state):
        """init() should not overwrite existing session state values."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        state["active_request"] = "existing_value"
        SessionManager.init()

        assert state["active_request"] == "existing_value"

    def test_init_is_idempotent(self, mock_session_state):
        """Calling init() multiple times should be safe."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()
        first_state = dict(state)
        SessionManager.init()

        assert state == first_state


class TestSessionManagerClearResults:
    """Tests for SessionManager.clear_results()."""

    def test_clear_results_purges_active_request(self, mock_session_state):
        """clear_results() should set active_request to None."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()
        state["active_request"] = "some_request"
        SessionManager.clear_results()

        assert state["active_request"] is None

    def test_clear_results_purges_cache(self, mock_session_state):
        """clear_results() should purge all result cache keys."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()
        state["result_cache_hash"] = "abc123"
        state["cached_monte_carlo_data"] = {"mean": 100.0}
        state["render_context_cache"] = {"key": "value"}

        SessionManager.clear_results()

        assert state["result_cache_hash"] is None
        assert state["cached_monte_carlo_data"] is None
        assert state["render_context_cache"] == {}


class TestSessionManagerConfigChange:
    """Tests for SessionManager.on_config_change()."""

    def test_config_change_detected(self, mock_session_state):
        """on_config_change() should return True when config differs."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()
        changed = SessionManager.on_config_change("AAPL_False_FCFF_STANDARD_5")

        assert changed is True

    def test_same_config_no_change(self, mock_session_state):
        """on_config_change() should return False when config is same."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()
        SessionManager.on_config_change("AAPL_False_FCFF_STANDARD_5")
        changed = SessionManager.on_config_change("AAPL_False_FCFF_STANDARD_5")

        assert changed is False

    def test_config_change_clears_results(self, mock_session_state, sample_request):
        """on_config_change() should clear results when config changes."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()
        state["active_request"] = sample_request
        state["result_cache_hash"] = "old_hash"

        SessionManager.on_config_change("NEW_CONFIG")

        assert state["active_request"] is None
        assert state["result_cache_hash"] is None


class TestSessionManagerActiveRequest:
    """Tests for get/set active_request."""

    def test_get_active_request_returns_none_initially(self, mock_session_state):
        """get_active_request() should return None when no request is set."""
        from app.state.session_manager import SessionManager
        state, _ = mock_session_state

        SessionManager.init()
        assert SessionManager.get_active_request() is None

    def test_set_active_request_stores_request(self, mock_session_state, sample_request):
        """set_active_request() should store the request in session state."""
        from app.state.session_manager import SessionManager
        state, mock_st = mock_session_state

        SessionManager.init()
        SessionManager.set_active_request(sample_request)

        assert state["active_request"] == sample_request
        mock_st.rerun.assert_called_once()

    def test_set_active_request_triggers_rerun(self, mock_session_state, sample_request):
        """set_active_request() should trigger st.rerun()."""
        from app.state.session_manager import SessionManager
        _, mock_st = mock_session_state

        SessionManager.init()
        SessionManager.set_active_request(sample_request)

        mock_st.rerun.assert_called_once()
