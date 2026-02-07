"""
tests/unit/test_engines.py

UNIT TESTS — Valuation Engines (src/valuation/engines.py)
========================================================
Architecture: Aligned with Parameters SSOT and Linear Workflow.
Status: 100% Pass Rate with new 'Parameters' Pydantic model.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from src.models import Parameters, ValuationMethodology, ParametersSource

# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_valuation_request():
    """Create a mock ValuationRequest compatible with the new architecture."""
    request = MagicMock()
    request.ticker = "AAPL"
    request.mode.value = "FCFF_STANDARD"
    request.mode.name = "FCFF_STANDARD"
    request.mode = MagicMock(spec=ValuationMethodology)
    request.mode.supports_monte_carlo = True
    request.input_source = ParametersSource.MANUAL
    request.options = {}
    return request


@pytest.fixture
def mock_company_financials():
    """Create a mock CompanyFinancials with REAL numeric values."""
    financials = MagicMock()
    financials.ticker = "AAPL"
    financials.current_price = 150.0
    financials.shares_outstanding = 1000000.0
    financials.total_debt = 50000000.0
    financials.cash_and_equivalents = 10000000.0
    financials.minority_interests = 0.0
    financials.pension_provisions = 0.0
    financials.ebit_ttm = 20000000.0
    financials.fcf = 100000000.0
    financials.net_debt = 40000000.0
    return financials


@pytest.fixture
def mock_parameters():
    """Create a mock Parameters object with the new segmented SSOT structure."""
    params = MagicMock(spec=Parameters)

    params.rates = MagicMock()
    params.rates.risk_free_rate = 0.04
    params.rates.market_risk_premium = 0.05
    params.rates.manual_beta = 1.1

    params.growth = MagicMock()
    params.growth.fcf_growth_rate = 0.05

    params.monte_carlo = MagicMock()
    params.monte_carlo.enabled = False
    params.monte_carlo.num_simulations = 2000

    params.scenarios = MagicMock()
    params.scenarios.enabled = False

    params.model_copy = MagicMock(return_value=params)
    return params


@pytest.fixture
def mock_valuation_result():
    """Create a mock ValuationResult with proper numeric values for formatting."""
    result = MagicMock()
    result.ticker = "AAPL"
    result.intrinsic_value_per_share = 150.0
    result.market_price = 145.0
    result.upside_pct = 0.0345
    result.multiples_triangulation = None

    # FIX: global_score DOIT être un float réel, sinon f-string {score:.1f} crash
    result.audit_report = MagicMock()
    result.audit_report.global_score = 85.0

    return result


# ==============================================================================
# 1. STRATEGY RESOLUTION TESTS
# ==============================================================================

class TestStrategyResolution:
    """Test suite for strategy resolution via registry."""

    def test_run_valuation_raises_for_unknown_strategy(
        self, mock_valuation_request, mock_company_financials, mock_parameters
    ):
        """Test run_valuation raises exception for unknown strategy."""
        with patch('src.valuation.engines.get_strategy', return_value=None):
            from src.valuation.engines import run_valuation, ValuationException

            with pytest.raises(ValuationException):
                run_valuation(
                    mock_valuation_request,
                    mock_company_financials,
                    mock_parameters
                )

    def test_run_valuation_resolves_strategy_and_executes(
        self, mock_valuation_request, mock_company_financials, mock_parameters
    ):
        """Test run_valuation resolves correct strategy and executes."""
        # FIX: On s'assure que le résultat et son audit report ont des valeurs numériques réelles
        mock_result = MagicMock()
        mock_result.audit_report = MagicMock()
        mock_result.audit_report.global_score = 80.0 # float réel

        mock_strategy_cls = MagicMock()
        mock_strategy_cls.return_value.execute.return_value = mock_result
        mock_strategy_cls.return_value.verify_output_contract = MagicMock()

        with patch('src.valuation.engines.get_strategy', return_value=mock_strategy_cls):
            with patch('src.valuation.engines.QuantLogger'):
                with patch('src.valuation.engines.logger'):
                    # FIX: On force le retour d'un audit report avec un score float
                    mock_audit = MagicMock()
                    mock_audit.global_score = 80.0
                    with patch('infra.auditing.audit_engine.AuditEngine.compute_audit', return_value=mock_audit):
                        from src.valuation.engines import run_valuation

                        result = run_valuation(
                            mock_valuation_request,
                            mock_company_financials,
                            mock_parameters
                        )

                        assert result is not None
                        mock_strategy_cls.return_value.execute.assert_called_once()


# ==============================================================================
# 2. MONTE CARLO INJECTION TESTS
# ==============================================================================

class TestMonteCarloInjection:
    """Test suite for Monte Carlo strategy wrapping."""

    def test_monte_carlo_injection_when_enabled(
        self, mock_valuation_request, mock_company_financials, mock_parameters
    ):
        """Test Monte Carlo strategy is used when enabled in Parameters."""
        mock_parameters.monte_carlo.enabled = True
        # FIX: mock_valuation_request.mode est déjà un mock (voir fixture), donc pas de pb de setter
        mock_valuation_request.mode.supports_monte_carlo = True

        mock_strategy_cls = MagicMock()
        mock_strategy_cls.return_value.execute.return_value = MagicMock()

        with patch('src.valuation.engines.get_strategy', return_value=mock_strategy_cls):
            with patch('src.valuation.engines.MonteCarloGenericStrategy') as mock_mc:
                mock_mc_instance = MagicMock()
                mock_mc_instance.execute.return_value = MagicMock()
                mock_mc_instance.verify_output_contract = MagicMock()
                mock_mc.return_value = mock_mc_instance

                from src.valuation.engines import run_valuation
                run_valuation(mock_valuation_request, mock_company_financials, mock_parameters)

                mock_mc.assert_called_once()

    def test_no_monte_carlo_when_disabled(
        self, mock_valuation_request, mock_company_financials, mock_parameters
    ):
        """Test deterministic strategy when MC is disabled."""
        mock_parameters.monte_carlo.enabled = False

        mock_strategy_cls = MagicMock()
        mock_strategy_cls.return_value.execute.return_value = MagicMock()

        with patch('src.valuation.engines.get_strategy', return_value=mock_strategy_cls):
            with patch('src.valuation.engines.MonteCarloGenericStrategy') as mock_mc:
                from src.valuation.engines import run_valuation
                run_valuation(mock_valuation_request, mock_company_financials, mock_parameters)

                mock_mc.assert_not_called()

    def test_no_monte_carlo_when_mode_unsupported(
        self, mock_valuation_request, mock_company_financials, mock_parameters
    ):
        """Test no MC injection when mode doesn't support it."""
        mock_parameters.monte_carlo.enabled = True
        # FIX: On utilise le mock de mode pour simuler l'absence de support
        mock_valuation_request.mode.supports_monte_carlo = False

        mock_strategy_cls = MagicMock()
        with patch('src.valuation.engines.get_strategy', return_value=mock_strategy_cls):
            with patch('src.valuation.engines.MonteCarloGenericStrategy') as mock_mc:
                from src.valuation.engines import run_valuation
                run_valuation(mock_valuation_request, mock_company_financials, mock_parameters)

                mock_mc.assert_not_called()


# ==============================================================================
# 3. REVERSE DCF TESTS
# ==============================================================================

class TestReverseDCF:
    """Test suite for reverse DCF solver."""

    def test_run_reverse_dcf_returns_none_negative_price(self, mock_company_financials, mock_parameters):
        from src.valuation.engines import run_reverse_dcf
        result = run_reverse_dcf(mock_company_financials, mock_parameters, market_price=-10.0)
        assert result is None

    def test_run_reverse_dcf_returns_none_zero_price(self, mock_company_financials, mock_parameters):
        from src.valuation.engines import run_reverse_dcf
        result = run_reverse_dcf(mock_company_financials, mock_parameters, market_price=0.0)
        assert result is None

    def test_run_reverse_dcf_attempts_convergence(self, mock_company_financials, mock_parameters):
        """Test reverse DCF attempts to find implied growth rate."""
        market_price = 150.0
        mock_strategy = MagicMock()
        res = MagicMock()
        res.intrinsic_value_per_share = 150.0
        mock_strategy.execute.return_value = res

        with patch('src.valuation.engines.FundamentalFCFFStrategy', return_value=mock_strategy):
            from src.valuation.engines import run_reverse_dcf
            run_reverse_dcf(mock_company_financials, mock_parameters, market_price, max_iterations=5)
            assert mock_strategy.execute.called

    def test_run_reverse_dcf_handles_calculation_error(self, mock_company_financials, mock_parameters):
        """Test reverse DCF handles calculation errors gracefully."""
        mock_strategy = MagicMock()
        mock_strategy.execute.side_effect = ValueError("Calculation error")

        with patch('src.valuation.engines.FundamentalFCFFStrategy', return_value=mock_strategy):
            from src.valuation.engines import run_reverse_dcf
            result = run_reverse_dcf(mock_company_financials, mock_parameters, market_price=150.0)
            assert result is None


# ==============================================================================
# 4. CONTEXT INJECTION TESTS
# ==============================================================================

class TestContextInjection:
    """Test suite for context injection into results."""

    def test_inject_context_sets_request(self, mock_valuation_result, mock_valuation_request):
        from src.valuation.engines import _inject_context
        _inject_context(mock_valuation_result, mock_valuation_request)
        assert mock_valuation_result.request == mock_valuation_request

    def test_inject_context_uses_object_setattr_on_error(self, mock_valuation_request):
        """Test context injection fallback mechanism."""
        # FIX: Au lieu de patcher __setattr__ (interdit), on crée une classe qui lève une erreur
        class BadResult:
            def __setattr__(self, name, value):
                if name == 'request':
                    raise AttributeError("Propriété verrouillée")
                super().__setattr__(name, value)

        bad_obj = BadResult()
        from src.valuation.engines import _inject_context

        # Ne doit pas crash car _inject_context utilise object.__setattr__ en fallback
        _inject_context(bad_obj, mock_valuation_request)
        assert bad_obj.request == mock_valuation_request


# ==============================================================================
# 5. TRIANGULATION TESTS
# ==============================================================================

class TestTriangulation:
    """Test suite for peer multiples triangulation."""

    def test_apply_triangulation_no_peers(
        self, mock_valuation_result, mock_valuation_request,
        mock_company_financials, mock_parameters
    ):
        """Test triangulation is skipped when no peers are provided."""
        mock_valuation_request.options = {}
        from src.valuation.engines import _apply_triangulation
        _apply_triangulation(mock_valuation_result, mock_valuation_request, mock_company_financials, mock_parameters)

    def test_apply_triangulation_empty_peers_list(
        self, mock_valuation_result, mock_valuation_request,
        mock_company_financials, mock_parameters
    ):
        """Test triangulation is skipped when peers list is empty."""
        mock_multiples_data = MagicMock()
        mock_multiples_data.peers = []
        mock_valuation_request.options = {"multiples_data": mock_multiples_data}

        from src.valuation.engines import _apply_triangulation
        _apply_triangulation(mock_valuation_result, mock_valuation_request, mock_company_financials, mock_parameters)


# ==============================================================================
# 6. ERROR HANDLING TESTS
# ==============================================================================

class TestErrorHandling:
    """Test suite for error handling and exception propagation."""

    def test_handle_calculation_error(self):
        from src.valuation.engines import _handle_calculation_error
        from src.core.exceptions import CalculationError
        err = _handle_calculation_error(CalculationError("Error"))
        assert err is not None

    def test_handle_system_crash(self):
        from src.valuation.engines import _handle_system_crash
        err = _handle_system_crash(Exception("System crash"))
        assert err is not None

    def test_raise_unknown_strategy(self):
        mock_mode = MagicMock()
        mock_mode.value = "UNKNOWN"
        from src.valuation.engines import _raise_unknown_strategy
        err = _raise_unknown_strategy(mock_mode)
        assert err is not None


# ==============================================================================
# 7. LOGGING TESTS
# ==============================================================================

class TestLogging:
    """Test suite for logging behavior."""

    def test_log_final_status_success(self, mock_valuation_request, mock_valuation_result):
        """Test successful completion is logged with proper quant logger."""
        with patch('src.valuation.engines.QuantLogger') as mock_logger:
            with patch('src.valuation.engines.logger'):
                from src.valuation.engines import _log_final_status
                _log_final_status(mock_valuation_request, mock_valuation_result)
                mock_logger.log_success.assert_called_once()

    def test_log_final_status_no_audit_report(self, mock_valuation_request, mock_valuation_result):
        """Test logging handles results without audit reports."""
        mock_valuation_result.audit_report = None
        with patch('src.valuation.engines.QuantLogger') as mock_logger:
            with patch('src.valuation.engines.logger'):
                from src.valuation.engines import _log_final_status
                _log_final_status(mock_valuation_request, mock_valuation_result)
                mock_logger.log_success.assert_called_once()


# ==============================================================================
# 8. REGISTRY TESTS
# ==============================================================================

class TestLegacyRegistry:
    """Test suite for registry integrity."""

    def test_strategy_registry_module_level(self):
        from src.valuation.engines import STRATEGY_REGISTRY
        assert isinstance(STRATEGY_REGISTRY, dict)

    def test_strategy_registry_has_modes(self):
        from src.valuation.engines import STRATEGY_REGISTRY
        assert len(STRATEGY_REGISTRY) > 0