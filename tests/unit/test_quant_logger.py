"""
tests/unit/test_quant_logger.py

COMPREHENSIVE TEST SUITE FOR QUANT LOGGER
=========================================
Role: Tests all functions and classes in src/core/quant_logger.py
Coverage Target: ≥90% line coverage
Standards: pytest + unittest.mock
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from src.core.quant_logger import (
    QuantLogger,
    LogLevel,
    LogDomain,
    log_valuation
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock the internal logger."""
    with patch('src.core.quant_logger._logger') as mock_log:
        yield mock_log


# ============================================================================
# TEST LogLevel and LogDomain Enums
# ============================================================================

def test_log_level_enum():
    """Test LogLevel enum values."""
    assert LogLevel.SUCCESS.value == "SUCCESS"
    assert LogLevel.WARNING.value == "WARNING"
    assert LogLevel.ERROR.value == "ERROR"
    assert LogLevel.INFO.value == "INFO"
    assert LogLevel.DEBUG.value == "DEBUG"


def test_log_domain_enum():
    """Test LogDomain enum values."""
    assert LogDomain.VALUATION.value == "VALUATION"
    assert LogDomain.DATA.value == "DATA"
    assert LogDomain.AUDIT.value == "AUDIT"
    assert LogDomain.MONTE_CARLO.value == "MC"
    assert LogDomain.PROVIDER.value == "PROVIDER"
    assert LogDomain.ENGINE.value == "ENGINE"


# ============================================================================
# TEST QuantLogger._format_message
# ============================================================================

def test_format_message_basic():
    """Test basic message formatting."""
    msg = QuantLogger._format_message(
        LogDomain.VALUATION,
        LogLevel.SUCCESS,
        "AAPL",
        intrinsic_value=150.50
    )
    
    assert "[VALUATION][SUCCESS]" in msg
    assert "Ticker: AAPL" in msg
    assert "IntrinsicValue: 150.50" in msg


def test_format_message_multiple_fields():
    """Test formatting with multiple fields."""
    msg = QuantLogger._format_message(
        LogDomain.AUDIT,
        LogLevel.INFO,
        "MSFT",
        score=85.5,
        grade="A",
        checks_passed=10,
        checks_failed=2
    )
    
    assert "[AUDIT][INFO]" in msg
    assert "Ticker: MSFT" in msg
    assert "Score: 85.5%" in msg
    assert "Grade: A" in msg
    assert "ChecksPassed: 10" in msg
    assert "ChecksFailed: 2" in msg


def test_format_message_percentage_detection():
    """Test smart formatting for percentage-like fields."""
    msg = QuantLogger._format_message(
        LogDomain.DATA,
        LogLevel.INFO,
        "TSLA",
        accuracy=95.5,
        ratio=0.75,
        score=88.0,
        percent_value=12.5
    )
    
    # Fields with 'score', 'ratio', 'accuracy', 'percent' should have %
    assert "Accuracy: 95.5%" in msg
    assert "Score: 88.0%" in msg
    assert "PercentValue: 12.5%" in msg


def test_format_message_rate_detection():
    """Test smart formatting for rate-like fields."""
    msg = QuantLogger._format_message(
        LogDomain.ENGINE,
        LogLevel.INFO,
        "GOOGL",
        growth_rate=0.08,
        discount_rate=0.10,
        yield_rate=0.045
    )
    
    # Rate fields should show as .2%
    assert "GrowthRate: 8.00%" in msg
    assert "DiscountRate: 10.00%" in msg
    assert "YieldRate: 4.50%" in msg


def test_format_message_large_numbers():
    """Test formatting of large numbers (billions/millions)."""
    msg = QuantLogger._format_message(
        LogDomain.VALUATION,
        LogLevel.SUCCESS,
        "AAPL",
        market_cap=2_500_000_000_000.0,  # $2.5T as float
        revenue=350_000_000_000.0,  # $350B as float
        profit=85_000_000_000.0  # $85B as float
    )
    
    # Should show as B for billions
    assert "Revenue: 350.00B" in msg
    assert "Profit: 85.00B" in msg


def test_format_message_medium_numbers():
    """Test formatting of medium numbers (millions)."""
    msg = QuantLogger._format_message(
        LogDomain.DATA,
        LogLevel.INFO,
        "SQ",
        cash=5_000_000_000.0,  # $5B as float
        debt=2_500_000_000.0  # $2.5B as float
    )
    
    assert "Cash: 5.00B" in msg
    assert "Debt: 2.50B" in msg


def test_format_message_small_numbers():
    """Test formatting of regular numbers."""
    msg = QuantLogger._format_message(
        LogDomain.VALUATION,
        LogLevel.INFO,
        "XYZ",
        price=123.45,
        eps=6.78
    )
    
    assert "Price: 123.45" in msg
    assert "Eps: 6.78" in msg


def test_format_message_none_values_skipped():
    """Test that None values are skipped."""
    msg = QuantLogger._format_message(
        LogDomain.VALUATION,
        LogLevel.INFO,
        "AAPL",
        iv=150.0,
        upside=None,
        score=85.0,
        grade=None
    )
    
    assert "Iv: 150.00" in msg
    assert "Score: 85.0%" in msg
    assert "Upside" not in msg
    assert "Grade" not in msg


def test_format_message_pascal_case_keys():
    """Test that keys are converted to PascalCase."""
    msg = QuantLogger._format_message(
        LogDomain.DATA,
        LogLevel.INFO,
        "TEST",
        some_long_key_name=100.0,  # Convert to float for decimal formatting
        another_field=200.0
    )
    
    assert "SomeLongKeyName: 100.00" in msg
    assert "AnotherField: 200.00" in msg


def test_format_message_pipe_separator():
    """Test that fields are separated by pipes."""
    msg = QuantLogger._format_message(
        LogDomain.AUDIT,
        LogLevel.INFO,
        "TEST",
        field1=1,
        field2=2,
        field3=3
    )
    
    parts = msg.split(" | ")
    assert len(parts) >= 4  # Header + ticker + 3 fields


# ============================================================================
# TEST QuantLogger.log_success
# ============================================================================

def test_log_success_basic(mock_logger):
    """Test basic success logging."""
    QuantLogger.log_success(
        ticker="AAPL",
        mode="FCFF",
        iv=150.0,
        audit_score=85.0,
        upside=25.50,
        duration_ms=1500
    )
    
    # Should call info once
    assert mock_logger.info.call_count == 1
    
    # Check message content
    msg = mock_logger.info.call_args[0][0]
    assert "[VALUATION][SUCCESS]" in msg
    assert "Ticker: AAPL" in msg
    assert "Model: FCFF" in msg
    assert "IntrinsicValue: 150.00" in msg
    assert "AuditScore: 85.0%" in msg
    # Upside is a float but doesn't match special keywords, so it's formatted as regular decimal
    assert "Upside: 25.50" in msg
    assert "ComputeTime: 1500ms" in msg


def test_log_success_without_optionals(mock_logger):
    """Test success logging without optional fields."""
    QuantLogger.log_success(
        ticker="MSFT",
        mode="DDM",
        iv=200.0
    )
    
    msg = mock_logger.info.call_args[0][0]
    assert "Ticker: MSFT" in msg
    assert "Model: DDM" in msg
    assert "IntrinsicValue: 200.00" in msg
    # Optional fields should not appear
    assert "AuditScore" not in msg
    assert "Upside" not in msg
    assert "ComputeTime" not in msg


def test_log_success_with_extra_kwargs(mock_logger):
    """Test success logging with extra keyword arguments."""
    QuantLogger.log_success(
        ticker="TSLA",
        mode="FCFE",
        iv=300.0,
        custom_field="custom_value",
        another_field=123.0  # Convert to float for decimal formatting
    )
    
    msg = mock_logger.info.call_args[0][0]
    assert "CustomField: custom_value" in msg
    assert "AnotherField: 123.00" in msg


# ============================================================================
# TEST QuantLogger.log_audit
# ============================================================================

def test_log_audit_basic(mock_logger):
    """Test audit logging."""
    QuantLogger.log_audit(
        ticker="AAPL",
        score=88.5,
        grade="A-",
        passed=18,
        failed=2
    )
    
    assert mock_logger.info.call_count == 1
    
    msg = mock_logger.info.call_args[0][0]
    assert "[AUDIT][INFO]" in msg
    assert "Ticker: AAPL" in msg
    assert "GlobalScore: 88.5%" in msg
    assert "Rating: A-" in msg
    assert "ChecksPassed: 18" in msg
    assert "ChecksFailed: 2" in msg


def test_log_audit_perfect_score(mock_logger):
    """Test audit logging with perfect score."""
    QuantLogger.log_audit(
        ticker="MSFT",
        score=100.0,
        grade="A+",
        passed=20,
        failed=0
    )
    
    msg = mock_logger.info.call_args[0][0]
    assert "GlobalScore: 100.0%" in msg
    assert "ChecksPassed: 20" in msg
    assert "ChecksFailed: 0" in msg


def test_log_audit_failing_grade(mock_logger):
    """Test audit logging with failing grade."""
    QuantLogger.log_audit(
        ticker="XYZ",
        score=45.0,
        grade="D",
        passed=5,
        failed=15
    )
    
    msg = mock_logger.info.call_args[0][0]
    assert "GlobalScore: 45.0%" in msg
    assert "Rating: D" in msg


# ============================================================================
# TEST QuantLogger.log_error
# ============================================================================

def test_log_error_with_string(mock_logger):
    """Test error logging with string error."""
    QuantLogger.log_error(
        ticker="AAPL",
        error="Data fetch failed"
    )
    
    assert mock_logger.error.call_count == 1
    
    msg = mock_logger.error.call_args[0][0]
    assert "[ENGINE][ERROR]" in msg
    assert "Ticker: AAPL" in msg
    assert "Error: Data fetch failed" in msg


def test_log_error_with_exception(mock_logger):
    """Test error logging with Exception object."""
    exc = ValueError("Invalid parameter")
    
    QuantLogger.log_error(
        ticker="MSFT",
        error=exc
    )
    
    msg = mock_logger.error.call_args[0][0]
    assert "Ticker: MSFT" in msg
    assert "Error: Invalid parameter" in msg


def test_log_error_with_custom_domain(mock_logger):
    """Test error logging with custom domain."""
    QuantLogger.log_error(
        ticker="TSLA",
        error="Provider timeout",
        domain=LogDomain.PROVIDER
    )
    
    msg = mock_logger.error.call_args[0][0]
    assert "[PROVIDER][ERROR]" in msg


def test_log_error_with_context(mock_logger):
    """Test error logging with additional context."""
    QuantLogger.log_error(
        ticker="GOOGL",
        error="Calculation failed",
        domain=LogDomain.VALUATION,
        step="terminal_value",
        value=12345.0  # Convert to float for decimal formatting with commas
    )
    
    msg = mock_logger.error.call_args[0][0]
    assert "[VALUATION][ERROR]" in msg
    assert "Error: Calculation failed" in msg
    assert "Step: terminal_value" in msg
    assert "Value: 12,345.00" in msg


# ============================================================================
# TEST log_valuation decorator
# ============================================================================

def test_log_valuation_decorator_success(mock_logger):
    """Test log_valuation decorator on successful function."""
    @log_valuation
    def mock_valuation_func(request):
        result = Mock()
        result.intrinsic_value_per_share = 150.0
        result.mode = Mock()
        result.mode.value = "FCFF"
        result.audit_report = Mock()
        result.audit_report.global_score = 85.0
        result.upside_pct = 20.0
        return result
    
    request = Mock()
    request.ticker = "AAPL"
    
    result = mock_valuation_func(request)
    
    # Should log success
    assert mock_logger.info.call_count == 1
    msg = mock_logger.info.call_args[0][0]
    assert "[VALUATION][SUCCESS]" in msg
    assert "Ticker: AAPL" in msg


def test_log_valuation_decorator_no_audit(mock_logger):
    """Test decorator when audit report is None."""
    @log_valuation
    def mock_valuation_func(request):
        result = Mock()
        result.intrinsic_value_per_share = 100.0
        result.mode = Mock()
        result.mode.value = "DDM"
        result.audit_report = None  # No audit
        result.upside_pct = 15.0
        return result
    
    request = Mock()
    request.ticker = "MSFT"
    
    result = mock_valuation_func(request)
    
    msg = mock_logger.info.call_args[0][0]
    assert "Ticker: MSFT" in msg
    # Audit score should be None (not in message)
    assert "AuditScore" not in msg


def test_log_valuation_decorator_ticker_from_args(mock_logger):
    """Test decorator extracts ticker from first argument."""
    @log_valuation
    def mock_valuation_func(obj):
        result = Mock()
        result.intrinsic_value_per_share = 200.0
        result.mode = Mock()
        result.mode.value = "RIM"
        result.audit_report = None
        result.upside_pct = None
        return result
    
    obj = Mock()
    obj.ticker = "TSLA"
    
    result = mock_valuation_func(obj)
    
    msg = mock_logger.info.call_args[0][0]
    assert "Ticker: TSLA" in msg


def test_log_valuation_decorator_ticker_from_kwargs(mock_logger):
    """Test decorator extracts ticker from kwargs."""
    @log_valuation
    def mock_valuation_func(request=None):
        result = Mock()
        result.intrinsic_value_per_share = 180.0
        result.mode = Mock()
        result.mode.value = "GRAHAM"
        result.audit_report = None
        result.upside_pct = 10.0
        return result
    
    request = Mock()
    request.ticker = "GOOGL"
    
    result = mock_valuation_func(request=request)
    
    msg = mock_logger.info.call_args[0][0]
    assert "Ticker: GOOGL" in msg


def test_log_valuation_decorator_no_ticker(mock_logger):
    """Test decorator when ticker cannot be resolved."""
    @log_valuation
    def mock_valuation_func():
        result = Mock()
        result.intrinsic_value_per_share = 100.0
        result.mode = Mock()
        result.mode.value = "FCFF"
        result.audit_report = None
        result.upside_pct = None
        return result
    
    result = mock_valuation_func()
    
    msg = mock_logger.info.call_args[0][0]
    assert "Ticker: N/A" in msg


def test_log_valuation_decorator_error(mock_logger):
    """Test decorator logs error on exception."""
    @log_valuation
    def mock_valuation_func(request):
        raise ValueError("Calculation error")
    
    request = Mock()
    request.ticker = "FAIL"
    
    with pytest.raises(ValueError):
        mock_valuation_func(request)
    
    # Should log error
    assert mock_logger.error.call_count == 1
    msg = mock_logger.error.call_args[0][0]
    assert "[VALUATION][ERROR]" in msg
    assert "Ticker: FAIL" in msg
    assert "Error: Calculation error" in msg


def test_log_valuation_decorator_non_result_return(mock_logger):
    """Test decorator when function returns non-result object."""
    @log_valuation
    def mock_valuation_func(request):
        # Returns something without intrinsic_value_per_share
        return {"ticker": "AAPL", "value": 100}
    
    request = Mock()
    request.ticker = "AAPL"
    
    result = mock_valuation_func(request)
    
    # Should not log success (no intrinsic_value_per_share)
    assert mock_logger.info.call_count == 0


def test_log_valuation_decorator_preserves_function():
    """Test that decorator preserves original function."""
    def original_func(x, y):
        """Original docstring."""
        return x + y
    
    decorated = log_valuation(original_func)
    
    # Should preserve name and docstring (via functools.wraps)
    assert decorated.__name__ == "original_func"
    assert decorated.__doc__ == "Original docstring."


def test_log_valuation_decorator_timing(mock_logger):
    """Test that decorator logs execution time."""
    import time
    
    @log_valuation
    def slow_valuation(request):
        time.sleep(0.1)  # 100ms
        result = Mock()
        result.intrinsic_value_per_share = 100.0
        result.mode = Mock()
        result.mode.value = "FCFF"
        result.audit_report = None
        result.upside_pct = None
        return result
    
    request = Mock()
    request.ticker = "SLOW"
    
    result = slow_valuation(request)
    
    msg = mock_logger.info.call_args[0][0]
    assert "ComputeTime:" in msg
    # Should be around 100ms
    assert "ms" in msg


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_logging_workflow(mock_logger):
    """Integration test: Full logging workflow."""
    # 1. Log success
    QuantLogger.log_success(
        ticker="AAPL",
        mode="FCFF",
        iv=150.0,
        audit_score=85.0
    )
    
    # 2. Log audit
    QuantLogger.log_audit(
        ticker="AAPL",
        score=85.0,
        grade="B+",
        passed=17,
        failed=3
    )
    
    # 3. Log error
    QuantLogger.log_error(
        ticker="FAIL",
        error="Test error"
    )
    
    # Should have logged 2 info + 1 error
    assert mock_logger.info.call_count == 2
    assert mock_logger.error.call_count == 1


def test_logging_consistency():
    """Test that logging format is consistent across methods."""
    with patch('src.core.quant_logger._logger') as mock_log:
        QuantLogger.log_success(ticker="T1", mode="M", iv=100.0)
        QuantLogger.log_audit(ticker="T2", score=80.0, grade="B", passed=10, failed=2)
        QuantLogger.log_error(ticker="T3", error="E")
        
        # All messages should follow same format
        for call_obj in mock_log.info.call_args_list + mock_log.error.call_args_list:
            msg = call_obj[0][0]
            # Should start with [DOMAIN][LEVEL]
            assert msg.startswith("[")
            assert "][" in msg
            # Should have ticker
            assert "Ticker:" in msg
            # Should use pipe separators
            assert " | " in msg


def test_logging_with_various_numeric_formats():
    """Test logging with various numeric formats."""
    with patch('src.core.quant_logger._logger') as mock_log:
        QuantLogger.log_success(
            ticker="TEST",
            mode="FCFF",
            iv=150.0,
            small_number=0.0001,
            large_number=1_000_000_000,
            negative_number=-50.0,
            zero_value=0.0,
            rate_field=0.08,
            ratio_value=1.5
        )
        
        msg = mock_log.info.call_args[0][0]
        
        # All numeric fields should be formatted
        assert "IntrinsicValue:" in msg
        assert "SmallNumber:" in msg
        assert "LargeNumber:" in msg
        assert "NegativeNumber:" in msg
        assert "ZeroValue:" in msg
        assert "RateField:" in msg
        assert "RatioValue:" in msg
