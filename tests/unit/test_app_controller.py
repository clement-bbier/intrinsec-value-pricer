"""
tests/unit/test_app_controller.py

APP CONTROLLER UNIT TESTS
==========================
Role: Validates the controller logic, error handling flow, and integration trigger.
Coverage Target: >85% for app/controllers/app_controller.py.
"""

import inspect
from unittest.mock import MagicMock, patch

from app.controllers.app_controller import AppController


class TestAppControllerStructure:
    """Tests the AppController class structure and interface."""

    def test_class_exists(self):
        """AppController must exist as a class."""
        assert inspect.isclass(AppController)

    def test_handle_run_analysis_is_static(self):
        """handle_run_analysis must be a static method."""
        assert isinstance(
            inspect.getattr_static(AppController, "handle_run_analysis"),
            staticmethod,
        )

    def test_handle_run_analysis_is_callable(self):
        """handle_run_analysis must be callable."""
        assert callable(AppController.handle_run_analysis)


class TestAppControllerErrorHandling:
    """Tests error handling branches in handle_run_analysis."""

    @patch("app.controllers.app_controller.st")
    @patch("app.controllers.app_controller.get_state")
    @patch("app.controllers.app_controller.InputFactory")
    @patch("app.controllers.app_controller.YahooFinancialProvider")
    @patch("app.controllers.app_controller.DefaultMacroProvider")
    @patch("app.controllers.app_controller.SessionManager")
    def test_snapshot_none_sets_error(self, mock_sm, mock_macro, mock_yahoo, mock_factory, mock_state, mock_st):
        """When provider returns None, error should be set."""
        state = MagicMock()
        mock_state.return_value = state
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        request = MagicMock()
        request.parameters.structure.ticker = "BADTICKER"
        mock_factory.build_request.return_value = request

        provider_instance = MagicMock()
        provider_instance.get_company_snapshot.return_value = None
        mock_yahoo.return_value = provider_instance

        AppController.handle_run_analysis()

        mock_sm.set_error.assert_called_once()
        error_msg = mock_sm.set_error.call_args[0][0]
        assert "BADTICKER" in error_msg

    @patch("app.controllers.app_controller.st")
    @patch("app.controllers.app_controller.get_state")
    @patch("app.controllers.app_controller.InputFactory")
    @patch("app.controllers.app_controller.YahooFinancialProvider")
    @patch("app.controllers.app_controller.DefaultMacroProvider")
    @patch("app.controllers.app_controller.SessionManager")
    def test_generic_exception_sets_error(self, mock_sm, mock_macro, mock_yahoo, mock_factory, mock_state, mock_st):
        """Generic exceptions should set an error message."""
        state = MagicMock()
        mock_state.return_value = state
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        mock_factory.build_request.side_effect = RuntimeError("Unexpected crash")

        AppController.handle_run_analysis()

        mock_sm.set_error.assert_called_once()
        error_msg = mock_sm.set_error.call_args[0][0]
        assert "Unexpected" in error_msg

    @patch("app.controllers.app_controller.st")
    @patch("app.controllers.app_controller.get_state")
    @patch("app.controllers.app_controller.InputFactory")
    @patch("app.controllers.app_controller.YahooFinancialProvider")
    @patch("app.controllers.app_controller.DefaultMacroProvider")
    @patch("app.controllers.app_controller.ValuationOrchestrator")
    @patch("app.controllers.app_controller.SessionManager")
    def test_success_flow_updates_state(
        self, mock_sm, mock_orch, mock_macro, mock_yahoo, mock_factory, mock_state, mock_st
    ):
        """Successful flow should update state with result."""
        state = MagicMock()
        mock_state.return_value = state
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        request = MagicMock()
        request.parameters.structure.ticker = "AAPL"
        mock_factory.build_request.return_value = request

        snapshot = MagicMock()
        provider_instance = MagicMock()
        provider_instance.get_company_snapshot.return_value = snapshot
        mock_yahoo.return_value = provider_instance

        mock_result = MagicMock()
        engine_instance = MagicMock()
        engine_instance.run.return_value = mock_result
        mock_orch.return_value = engine_instance

        AppController.handle_run_analysis()

        assert state.last_result == mock_result
        assert state.should_run_valuation is False
        assert state.error_message == ""

    @patch("app.controllers.app_controller.st")
    @patch("app.controllers.app_controller.get_state")
    @patch("app.controllers.app_controller.InputFactory")
    @patch("app.controllers.app_controller.DefaultMacroProvider")
    @patch("app.controllers.app_controller.SessionManager")
    def test_ticker_not_found_error(self, mock_sm, mock_macro, mock_factory, mock_state, mock_st):
        """TickerNotFoundError should set a specific error message."""
        from src.core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
        from src.core.exceptions import TickerNotFoundError

        state = MagicMock()
        mock_state.return_value = state
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        diag = DiagnosticEvent(
            code="TICKER_404",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.DATA,
            message="Ticker XYZ not found",
        )
        mock_factory.build_request.side_effect = TickerNotFoundError(diag)

        AppController.handle_run_analysis()

        mock_sm.set_error.assert_called_once()
        error_msg = mock_sm.set_error.call_args[0][0]
        assert "not found" in error_msg.lower() or "Ticker" in error_msg

    @patch("app.controllers.app_controller.st")
    @patch("app.controllers.app_controller.get_state")
    @patch("app.controllers.app_controller.InputFactory")
    @patch("app.controllers.app_controller.DefaultMacroProvider")
    @patch("app.controllers.app_controller.SessionManager")
    def test_valuation_error_sets_error(self, mock_sm, mock_macro, mock_factory, mock_state, mock_st):
        """ValuationError should set a specific error message."""
        from src.core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
        from src.core.exceptions import ValuationError

        state = MagicMock()
        mock_state.return_value = state
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        diag = DiagnosticEvent(
            code="CALC_FAIL",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message="Calculation failed",
        )
        mock_factory.build_request.side_effect = ValuationError(diag)

        AppController.handle_run_analysis()

        mock_sm.set_error.assert_called_once()

    @patch("app.controllers.app_controller.st")
    @patch("app.controllers.app_controller.get_state")
    @patch("app.controllers.app_controller.InputFactory")
    @patch("app.controllers.app_controller.YahooFinancialProvider")
    @patch("app.controllers.app_controller.DefaultMacroProvider")
    @patch("app.controllers.app_controller.SessionManager")
    def test_external_service_error(self, mock_sm, mock_macro, mock_yahoo, mock_factory, mock_state, mock_st):
        """ExternalServiceError should set error via SessionManager."""
        from src.core.exceptions import ExternalServiceError

        state = MagicMock()
        mock_state.return_value = state
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        request = MagicMock()
        request.parameters.structure.ticker = "AAPL"
        mock_factory.build_request.return_value = request

        provider_instance = MagicMock()
        provider_instance.get_company_snapshot.side_effect = ExternalServiceError(
            provider="Yahoo Finance",
            error_detail="API timeout",
        )
        mock_yahoo.return_value = provider_instance

        AppController.handle_run_analysis()

        mock_sm.set_error.assert_called_once()
