"""
tests/unit/test_quant_logger_pipeline.py

PIPELINE STAGE LOGGING TESTS
==============================
Role: Validates the new descriptive pipeline stage logging methods.
Coverage Target: >85% for quant_logger.py pipeline methods.
"""

from unittest.mock import patch

import pytest

from src.core.quant_logger import LogDomain, QuantLogger


@pytest.fixture
def mock_logger():
    """Mock the internal quant logger."""
    with patch('src.core.quant_logger._logger') as mock_log:
        yield mock_log


class TestLogDomainExtensions:
    """Tests the new LogDomain enum values."""

    def test_resolver_domain_exists(self):
        """RESOLVER domain must be available."""
        assert LogDomain.RESOLVER.value == "RESOLVER"

    def test_extension_domain_exists(self):
        """EXTENSION domain must be available."""
        assert LogDomain.EXTENSION.value == "EXTENSION"

    def test_pipeline_domain_exists(self):
        """PIPELINE domain must be available."""
        assert LogDomain.PIPELINE.value == "PIPELINE"


class TestLogStageStart:
    """Tests the log_stage_start method."""

    def test_logs_stage_start(self, mock_logger):
        """Stage start must log with INFO level and STARTED status."""
        QuantLogger.log_stage_start("AAPL", "DATA_FETCHING")
        assert mock_logger.info.call_count == 1
        msg = mock_logger.info.call_args[0][0]
        assert "[PIPELINE][INFO]" in msg
        assert "Ticker: AAPL" in msg
        assert "Stage: DATA_FETCHING" in msg
        assert "Status: STARTED" in msg

    def test_logs_stage_start_with_context(self, mock_logger):
        """Stage start must include additional context."""
        QuantLogger.log_stage_start("MSFT", "RESOLUTION", provider="Yahoo")
        msg = mock_logger.info.call_args[0][0]
        assert "Provider: Yahoo" in msg


class TestLogStageComplete:
    """Tests the log_stage_complete method."""

    def test_logs_stage_complete(self, mock_logger):
        """Stage complete must log with SUCCESS level."""
        QuantLogger.log_stage_complete("AAPL", "DATA_FETCHING", duration_ms=250)
        assert mock_logger.info.call_count == 1
        msg = mock_logger.info.call_args[0][0]
        assert "[PIPELINE][SUCCESS]" in msg
        assert "Status: COMPLETED" in msg
        assert "Duration: 250ms" in msg

    def test_logs_stage_complete_without_duration(self, mock_logger):
        """Stage complete without duration must not include Duration field."""
        QuantLogger.log_stage_complete("AAPL", "EXECUTION")
        msg = mock_logger.info.call_args[0][0]
        assert "Duration" not in msg


class TestLogStageError:
    """Tests the log_stage_error method."""

    def test_logs_stage_error(self, mock_logger):
        """Stage error must log with ERROR level."""
        QuantLogger.log_stage_error("AAPL", "DATA_FETCHING", "Network timeout")
        assert mock_logger.error.call_count == 1
        msg = mock_logger.error.call_args[0][0]
        assert "[PIPELINE][ERROR]" in msg
        assert "Status: FAILED" in msg
        assert "Error: Network timeout" in msg

    def test_logs_stage_error_with_exception(self, mock_logger):
        """Stage error must handle Exception objects."""
        exc = ValueError("Invalid ticker")
        QuantLogger.log_stage_error("BAD", "DATA_FETCHING", exc)
        msg = mock_logger.error.call_args[0][0]
        assert "Error: Invalid ticker" in msg


class TestLogDataFetching:
    """Tests the log_data_fetching method."""

    def test_logs_data_fetching_default_provider(self, mock_logger):
        """Data fetching must default to Yahoo Finance provider."""
        QuantLogger.log_data_fetching("AAPL")
        msg = mock_logger.info.call_args[0][0]
        assert "[DATA][INFO]" in msg
        assert "Stage: DATA_FETCHING" in msg
        assert "Provider: Yahoo Finance" in msg

    def test_logs_data_fetching_custom_provider(self, mock_logger):
        """Data fetching must support custom provider name."""
        QuantLogger.log_data_fetching("AAPL", provider="Bloomberg")
        msg = mock_logger.info.call_args[0][0]
        assert "Provider: Bloomberg" in msg


class TestLogParameterResolution:
    """Tests the log_parameter_resolution method."""

    def test_logs_resolution(self, mock_logger):
        """Parameter resolution must log resolved fields."""
        QuantLogger.log_parameter_resolution(
            "AAPL", "FCFF_STANDARD",
            wacc_rate=0.08, growth_rate=0.05
        )
        msg = mock_logger.info.call_args[0][0]
        assert "[RESOLVER][INFO]" in msg
        assert "Stage: PARAMETER_RESOLUTION" in msg
        assert "Model: FCFF_STANDARD" in msg


class TestLogStrategyExecution:
    """Tests the log_strategy_execution method."""

    def test_logs_execution(self, mock_logger):
        """Strategy execution must log the strategy name."""
        QuantLogger.log_strategy_execution("AAPL", "StandardFCFF")
        msg = mock_logger.info.call_args[0][0]
        assert "[ENGINE][INFO]" in msg
        assert "Stage: STRATEGY_EXECUTION" in msg
        assert "Strategy: StandardFCFF" in msg


class TestLogExtensionProcessing:
    """Tests the log_extension_processing method."""

    def test_logs_extension(self, mock_logger):
        """Extension processing must log the extension name."""
        QuantLogger.log_extension_processing("AAPL", "MONTE_CARLO", iterations=5000)
        msg = mock_logger.info.call_args[0][0]
        assert "[EXTENSION][INFO]" in msg
        assert "Stage: EXTENSION_PROCESSING" in msg
        assert "Extension: MONTE_CARLO" in msg

    def test_logs_sensitivity_extension(self, mock_logger):
        """Sensitivity extension must be loggable."""
        QuantLogger.log_extension_processing("MSFT", "SENSITIVITY")
        msg = mock_logger.info.call_args[0][0]
        assert "Extension: SENSITIVITY" in msg


class TestLogFinalPackaging:
    """Tests the log_final_packaging method."""

    def test_logs_final_packaging(self, mock_logger):
        """Final packaging must log the intrinsic value."""
        QuantLogger.log_final_packaging("AAPL", intrinsic_value=165.50)
        msg = mock_logger.info.call_args[0][0]
        assert "[PIPELINE][SUCCESS]" in msg
        assert "Stage: FINAL_PACKAGING" in msg
        assert "IntrinsicValue: 165.50" in msg

    def test_logs_final_packaging_with_context(self, mock_logger):
        """Final packaging must include additional context."""
        QuantLogger.log_final_packaging(
            "AAPL", intrinsic_value=165.50,
            audit_score=88.0
        )
        msg = mock_logger.info.call_args[0][0]
        assert "AuditScore: 88.0%" in msg


class TestPipelineIntegration:
    """Integration test for full pipeline logging flow."""

    def test_full_pipeline_flow(self, mock_logger):
        """Full pipeline flow must produce correct sequence of logs."""
        QuantLogger.log_stage_start("AAPL", "FULL_PIPELINE")
        QuantLogger.log_data_fetching("AAPL")
        QuantLogger.log_parameter_resolution("AAPL", "FCFF_STANDARD")
        QuantLogger.log_strategy_execution("AAPL", "StandardFCFF")
        QuantLogger.log_extension_processing("AAPL", "MONTE_CARLO")
        QuantLogger.log_final_packaging("AAPL", intrinsic_value=165.50)
        QuantLogger.log_stage_complete("AAPL", "FULL_PIPELINE", duration_ms=1500)

        # All stages should log via info
        assert mock_logger.info.call_count == 7
        assert mock_logger.error.call_count == 0
