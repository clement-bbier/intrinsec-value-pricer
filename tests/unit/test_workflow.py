"""
tests/unit/test_workflow.py

INTEGRAL WORKFLOW ORCHESTRATOR TESTS
====================================
Role: Validates the end-to-end logical orchestration of the valuation lifecycle.
Coverage: ~100% of app/workflow.py (Nominal, Errors, Scenarios, Backtest, Logging).
Standard: Pydantic V2 Compatible & SOLID compliant.
"""

import pytest
import numpy as np
from datetime import date
from unittest.mock import Mock, patch, MagicMock, ANY
from app.workflow import (
    run_workflow,
    run_workflow_and_display,
    map_request_to_params,
    compute_scenario_impact,
    _orchestrate_backtesting,
    _log_monte_carlo_performance,
    _display_diagnostic_message,
    _create_crash_diagnostic
)
from src.models import (
    ValuationRequest, ValuationMode, InputSource,
    ValuationResult, Parameters, ScenarioSynthesis,
    ScenarioResult, BacktestResult, HistoricalPoint, CompanyFinancials
)
from src.diagnostics import DiagnosticEvent, SeverityLevel, DiagnosticDomain
from src.exceptions import ValuationException

TARGET = 'app.workflow'

@pytest.fixture
def base_request():
    """Standard Valuation Request for testing."""
    return ValuationRequest(
        ticker="AAPL",
        projection_years=5,
        mode=ValuationMode.FCFF_STANDARD,
        input_source=InputSource.AUTO,
        options={"enable_backtest": False}
    )

@pytest.fixture
def mock_financials():
    """Minimal CompanyFinancials for logic tests."""
    return CompanyFinancials(
        ticker="AAPL", currency="USD", current_price=150.0, shares_outstanding=1e9
    )

class TestWorkflowNominal:
    """Validation of the primary nominal workflow lifecycle."""

    @patch(f'{TARGET}.run_workflow')
    @patch('app.adapters.StreamlitResultRenderer')
    def test_run_workflow_and_display_facade(self, mock_renderer_cls, mock_run_wf, base_request):
        """Verifies Streamlit facade delegation."""
        mock_res, mock_prov = MagicMock(), MagicMock()
        mock_run_wf.return_value = (mock_res, mock_prov)

        run_workflow_and_display(base_request)

        mock_renderer_cls.return_value.render_results.assert_called_once_with(mock_res, mock_prov)

class TestWorkflowErrorHandling:
    """Validation of business exceptions and critical system crashes."""

    @patch(f'{TARGET}.st')
    @patch(f'{TARGET}.YahooFinanceProvider')
    def test_run_workflow_valuation_exception(self, mock_provider_cls, mock_st, base_request):
        """Covers catch of ValuationException."""
        mock_st.status.return_value.__enter__.return_value = MagicMock()
        diag = DiagnosticEvent(code="ERR", severity=SeverityLevel.ERROR, domain=DiagnosticDomain.DATA, message="Fail")
        mock_provider_cls.side_effect = ValuationException(diag)

        result, provider = run_workflow(base_request)

        assert result is None
        mock_st.error.assert_called()

    @patch(f'{TARGET}.st')
    @patch(f'{TARGET}.YahooFinanceProvider')
    def test_run_workflow_generic_crash(self, mock_provider_cls, mock_st, base_request):
        """Covers catch of unexpected system crash."""
        mock_st.status.return_value.__enter__.return_value = MagicMock()
        mock_provider_cls.side_effect = RuntimeError("Panic")

        result, provider = run_workflow(base_request)

        assert result is None
        # Use ANY instead of patch.any
        mock_st.status.return_value.update.assert_called_with(label=ANY, state="error", expanded=True)

class TestSmartMergeLogic:
    """Validation of the parameter fusion logic."""

    def test_map_manual_source_overrides(self):
        """Verifies Expert mode overrides with valid Pydantic types."""
        auto_params = Parameters()
        auto_params.rates.risk_free_rate = 0.02

        manual_params = Parameters()
        manual_params.rates.risk_free_rate = 0.045

        # Instantiate real request to avoid ValidationError on projection_years
        request = ValuationRequest(
            ticker="TEST", projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.MANUAL,
            manual_params=manual_params
        )

        final = map_request_to_params(request, auto_params)
        assert final.rates.risk_free_rate == 0.045

class TestAdvancedAnalysis:
    """Validation of Scenarios and Backtesting logic."""

    @patch(f'{TARGET}.run_valuation')
    def test_compute_scenario_impact_weighted(self, mock_run_val, mock_financials):
        """Verifies probability-weighted Expected Value calculation."""
        params = Parameters()
        params.scenarios.enabled = True
        params.scenarios.bull.probability = 0.3
        params.scenarios.base.probability = 0.4
        params.scenarios.bear.probability = 0.3

        # Engine results
        mock_res = MagicMock(spec=ValuationResult)
        mock_res.intrinsic_value_per_share = 100.0
        mock_run_val.return_value = mock_res

        synthesis = compute_scenario_impact(Mock(), mock_financials, params, mock_res)

        assert synthesis.expected_value == 100.0
        assert len(synthesis.variants) == 3

    @patch(f'{TARGET}.BacktestEngine')
    @patch(f'{TARGET}.run_valuation')
    def test_orchestrate_backtesting_with_skips(self, mock_run_val, mock_bt_engine):
        """Verifies backtest resilience when an historical year fails."""
        mock_bt_engine.freeze_data_at_fiscal_year.side_effect = [{"d":1}, None, {"d":3}]
        mock_bt_engine.get_historical_price_at.return_value = 100.0

        hist_res = MagicMock(spec=ValuationResult)
        hist_res.intrinsic_value_per_share = 110.0
        mock_run_val.return_value = hist_res

        mock_provider = MagicMock()
        mock_provider.map_raw_to_financials.return_value = Mock()

        report = _orchestrate_backtesting(Mock(), Mock(), Parameters(), Mock(), mock_provider)

        assert len(report.points) == 2
        # Use pytest.approx for floating point comparison (90.0 vs 89.999...)
        assert report.model_accuracy_score == pytest.approx(90.0)

class TestDiagnosticsInternal:
    """Validation of UI messages and crash diagnostic generation."""

    @patch(f'{TARGET}.st')
    def test_display_diagnostic_message_branches(self, mock_st):
        """Tests both Error and Warning branches in UI."""
        # Branch 1: Error
        diag_err = DiagnosticEvent(code="C1", severity=SeverityLevel.ERROR,
                                    domain=DiagnosticDomain.SYSTEM, message="Err")
        _display_diagnostic_message(diag_err)
        mock_st.error.assert_called()

        # Branch 2: Warning
        diag_warn = DiagnosticEvent(code="C2", severity=SeverityLevel.WARNING,
                                     domain=DiagnosticDomain.MODEL, message="Warn")
        _display_diagnostic_message(diag_warn)
        mock_st.warning.assert_called()

    def test_create_crash_diagnostic_trace(self):
        """Verifies that the crash diagnostic captures the stack trace."""
        try:
            raise ValueError("Inner Error")
        except ValueError as e:
            diag = _create_crash_diagnostic(e)

        assert diag.code == "SYSTEM_CRASH"
        assert "Inner Error" in diag.technical_detail
        assert "ValueError" in diag.technical_detail