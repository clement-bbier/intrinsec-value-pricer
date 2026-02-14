"""
tests/unit/test_risk_engines.py

COMPREHENSIVE RISK ENGINEERING TESTING
======================================
Role: Validates diagnostics, exceptions, and formatting in src/core/
Coverage: DiagnosticEvent, Exceptions, FinancialContext, Formatting.
"""

import pytest

from src.core.diagnostics import (
    DiagnosticEvent,
    FinancialContext,
    SeverityLevel,
    DiagnosticDomain,
    DiagnosticRegistry
)
from src.core.exceptions import (
    ValuationError,
    CalculationError,
    TickerNotFoundError,
    ExternalServiceError,
    DataMissingError,
    ModelDivergenceError,
    MonteCarloInstabilityError,
    InvalidParameterError,
    ConfigurationError
)
from src.core.formatting import format_smart_number, get_delta_color


# ==============================================================================
# 1. DIAGNOSTIC EVENT
# ==============================================================================

@pytest.mark.unit
def test_diagnostic_event_creation():
    """Test DiagnosticEvent creation with all fields."""
    event = DiagnosticEvent(
        code="TEST_001",
        severity=SeverityLevel.WARNING,
        domain=DiagnosticDomain.MODEL,
        message="Test warning message",
        technical_detail="Some technical details",
        remediation_hint="Fix the issue",
        financial_context=None
    )
    
    assert event.code == "TEST_001"
    assert event.severity == SeverityLevel.WARNING
    assert event.domain == DiagnosticDomain.MODEL
    assert event.message == "Test warning message"


@pytest.mark.unit
def test_diagnostic_event_is_blocking_true():
    """Test is_blocking property returns True for ERROR and CRITICAL."""
    error_event = DiagnosticEvent(
        code="ERR_001",
        severity=SeverityLevel.ERROR,
        domain=DiagnosticDomain.ENGINE,
        message="Error"
    )
    critical_event = DiagnosticEvent(
        code="CRIT_001",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.CONFIG,
        message="Critical"
    )
    
    assert error_event.is_blocking is True
    assert critical_event.is_blocking is True


@pytest.mark.unit
def test_diagnostic_event_is_blocking_false():
    """Test is_blocking property returns False for INFO and WARNING."""
    info_event = DiagnosticEvent(
        code="INFO_001",
        severity=SeverityLevel.INFO,
        domain=DiagnosticDomain.DATA,
        message="Info"
    )
    warning_event = DiagnosticEvent(
        code="WARN_001",
        severity=SeverityLevel.WARNING,
        domain=DiagnosticDomain.USER_INPUT,
        message="Warning"
    )
    
    assert info_event.is_blocking is False
    assert warning_event.is_blocking is False


@pytest.mark.unit
def test_diagnostic_event_to_dict():
    """Test to_dict() serialization."""
    event = DiagnosticEvent(
        code="TEST_002",
        severity=SeverityLevel.INFO,
        domain=DiagnosticDomain.SYSTEM,
        message="Test message"
    )
    
    result = event.to_dict()
    
    assert isinstance(result, dict)
    assert result["code"] == "TEST_002"
    assert result["severity"] == "INFO"
    assert result["domain"] == "SYSTEM"
    assert result["message"] == "Test message"


# ==============================================================================
# 2. FINANCIAL CONTEXT
# ==============================================================================

@pytest.mark.unit
def test_financial_context_creation():
    """Test FinancialContext creation."""
    context = FinancialContext(
        parameter_name="Beta",
        current_value=2.5,
        typical_range=(0.5, 2.0),
        statistical_risk="Value is abnormally high",
        recommendation="Review sector benchmark"
    )
    
    assert context.parameter_name == "Beta"
    assert context.current_value == 2.5
    assert context.typical_range == (0.5, 2.0)


@pytest.mark.unit
def test_financial_context_to_human_readable():
    """Test to_human_readable() output formatting."""
    context = FinancialContext(
        parameter_name="Market Beta",
        current_value=3.0,
        typical_range=(0.5, 2.0),
        statistical_risk="Suggests extreme volatility",
        recommendation="Verify data source"
    )
    
    output = context.to_human_readable()
    
    assert "Market Beta" in output
    assert "3.00" in output
    assert "0.50 - 2.00" in output
    assert "extreme volatility" in output
    assert "Verify data source" in output


# ==============================================================================
# 3. DIAGNOSTIC REGISTRY
# ==============================================================================

@pytest.mark.unit
def test_diagnostic_registry_model_g_divergence():
    """Test model_g_divergence() returns correct event."""
    event = DiagnosticRegistry.model_g_divergence(g=0.08, wacc=0.07)
    
    assert event.code == "MODEL_G_DIVERGENCE"
    assert event.severity == SeverityLevel.CRITICAL
    assert "8.00%" in event.message
    assert "7.00%" in event.message


@pytest.mark.unit
def test_diagnostic_registry_mc_instability():
    """Test model_mc_instability() with below threshold ratio."""
    event = DiagnosticRegistry.model_mc_instability(valid_ratio=0.65, threshold=0.75)
    
    assert event.code == "MODEL_MC_INSTABILITY"
    assert event.severity == SeverityLevel.ERROR
    assert "65%" in event.message


@pytest.mark.unit
def test_diagnostic_registry_risk_excessive_growth():
    """Test risk_excessive_growth() for unrealistic growth."""
    event = DiagnosticRegistry.risk_excessive_growth(g=0.25)
    
    assert event.code == "RISK_EXCESSIVE_GROWTH"
    assert event.severity == SeverityLevel.WARNING
    assert "25.0%" in event.message


@pytest.mark.unit
def test_diagnostic_registry_fcfe_negative_flow():
    """Test fcfe_negative_flow() diagnostic."""
    event = DiagnosticRegistry.fcfe_negative_flow(val=-500_000_000.0)
    
    assert event.code == "FCFE_NEGATIVE_FLOW"
    assert event.severity == SeverityLevel.CRITICAL
    assert "negative" in event.message.lower()


@pytest.mark.unit
def test_diagnostic_registry_risk_missing_sbc_dilution():
    """Test risk_missing_sbc_dilution() for tech sector."""
    event = DiagnosticRegistry.risk_missing_sbc_dilution(
        sector="TECHNOLOGY",
        rate=0.0
    )
    
    assert event.code == "RISK_MISSING_SBC_DILUTION"
    assert event.severity == SeverityLevel.WARNING
    assert "dilution" in event.message.lower()


# ==============================================================================
# 4. CUSTOM EXCEPTIONS
# ==============================================================================

@pytest.mark.unit
def test_valuation_exception_base():
    """Test ValuationError base class."""
    event = DiagnosticEvent(
        code="TEST_FAIL",
        severity=SeverityLevel.ERROR,
        domain=DiagnosticDomain.ENGINE,
        message="Test failure"
    )
    
    exc = ValuationError(event)
    
    assert exc.diagnostic == event
    assert str(exc) == "Test failure"


@pytest.mark.unit
def test_calculation_error():
    """Test CalculationError exception."""
    exc = CalculationError("Invalid discount rate")
    
    assert isinstance(exc, ValuationError)
    assert "Invalid discount rate" in str(exc)
    assert exc.diagnostic.severity == SeverityLevel.ERROR
    assert exc.diagnostic.domain == DiagnosticDomain.MODEL


@pytest.mark.unit
def test_ticker_not_found_error():
    """Test TickerNotFoundError exception."""
    exc = TickerNotFoundError("INVALID")
    
    assert isinstance(exc, ValuationError)
    assert "INVALID" in str(exc)
    assert exc.diagnostic.severity == SeverityLevel.CRITICAL


@pytest.mark.unit
def test_external_service_error():
    """Test ExternalServiceError exception."""
    exc = ExternalServiceError("Yahoo Finance", "Timeout after 30s")
    
    assert isinstance(exc, ValuationError)
    assert "Yahoo Finance" in str(exc)
    assert exc.diagnostic.technical_detail == "Timeout after 30s"


@pytest.mark.unit
def test_data_missing_error():
    """Test DataMissingError exception."""
    exc = DataMissingError("total_debt", "AAPL")
    
    assert isinstance(exc, ValuationError)
    assert "total_debt" in str(exc)
    assert "AAPL" in str(exc)
    assert exc.diagnostic.severity == SeverityLevel.ERROR


@pytest.mark.unit
def test_model_divergence_error():
    """Test ModelDivergenceError exception."""
    exc = ModelDivergenceError(g=0.08, wacc=0.07)
    
    assert isinstance(exc, ValuationError)
    assert "8.00%" in str(exc)
    assert "7.00%" in str(exc)


@pytest.mark.unit
def test_monte_carlo_instability_error():
    """Test MonteCarloInstabilityError exception."""
    exc = MonteCarloInstabilityError(valid_ratio=0.45, threshold=0.75)
    
    assert isinstance(exc, ValuationError)
    assert "45%" in str(exc)


@pytest.mark.unit
def test_invalid_parameter_error():
    """Test InvalidParameterError exception."""
    exc = InvalidParameterError("projection_years", 100, (1, 50))
    
    assert isinstance(exc, ValuationError)
    assert "projection_years" in str(exc)
    assert exc.diagnostic.domain == DiagnosticDomain.CONFIG


@pytest.mark.unit
def test_configuration_error():
    """Test ConfigurationError exception."""
    exc = ConfigurationError("/path/to/config.yaml", "File not found")
    
    assert isinstance(exc, ValuationError)
    assert "config.yaml" in str(exc)
    assert exc.diagnostic.severity == SeverityLevel.CRITICAL


# ==============================================================================
# 5. FORMATTING FUNCTIONS
# ==============================================================================

@pytest.mark.unit
def test_format_smart_number_none():
    """Test format_smart_number() with None returns dash."""
    assert format_smart_number(None) == "-"


@pytest.mark.unit
def test_format_smart_number_nan():
    """Test format_smart_number() with NaN returns dash."""
    assert format_smart_number(float('nan')) == "-"


@pytest.mark.unit
def test_format_smart_number_percentage():
    """Test format_smart_number() with percentage formatting."""
    result = format_smart_number(0.0575, is_pct=True, decimals=2)
    assert result == "5.75%"


@pytest.mark.unit
def test_format_smart_number_millions():
    """Test format_smart_number() with millions scaling (M)."""
    result = format_smart_number(5_500_000, decimals=2)
    assert "5.50M" in result


@pytest.mark.unit
def test_format_smart_number_billions():
    """Test format_smart_number() with billions scaling (B)."""
    result = format_smart_number(12_300_000_000, decimals=2)
    assert "12.30B" in result


@pytest.mark.unit
def test_format_smart_number_trillions():
    """Test format_smart_number() with trillions scaling (T)."""
    result = format_smart_number(3_450_000_000_000, decimals=2)
    assert "3.45T" in result


@pytest.mark.unit
def test_format_smart_number_currency_suffix():
    """Test format_smart_number() with currency suffix."""
    result = format_smart_number(1_500_000_000, currency="USD", decimals=2)
    assert "1.50B USD" == result


@pytest.mark.unit
def test_format_smart_number_small_value():
    """Test format_smart_number() with small value (no scaling)."""
    result = format_smart_number(12345.67, decimals=2)
    assert "12,345.67" == result


@pytest.mark.unit
def test_format_smart_number_negative():
    """Test format_smart_number() with negative value."""
    result = format_smart_number(-2_500_000_000, decimals=2)
    assert "-2.50B" in result


@pytest.mark.unit
def test_get_delta_color_positive():
    """Test get_delta_color() returns green for positive values."""
    color = get_delta_color(0.15)
    assert color == "#22C55E"  # Green


@pytest.mark.unit
def test_get_delta_color_negative():
    """Test get_delta_color() returns red for negative values."""
    color = get_delta_color(-0.10)
    assert color == "#EF4444"  # Red


@pytest.mark.unit
def test_get_delta_color_zero():
    """Test get_delta_color() returns neutral for zero."""
    color = get_delta_color(0.0)
    assert color == "#808080"  # Neutral gray


@pytest.mark.unit
def test_get_delta_color_inverse_mode():
    """Test get_delta_color() with inverse=True reverses logic."""
    # Positive value with inverse should return red (negative)
    color = get_delta_color(0.05, inverse=True)
    assert color == "#EF4444"  # Red
    
    # Negative value with inverse should return green (positive)
    color = get_delta_color(-0.05, inverse=True)
    assert color == "#22C55E"  # Green


@pytest.mark.unit
def test_format_smart_number_zero_decimals():
    """Test format_smart_number() with zero decimal places."""
    result = format_smart_number(1_234_567_890, decimals=0)
    assert "1B" in result


@pytest.mark.unit
def test_format_smart_number_high_precision():
    """Test format_smart_number() with high decimal precision."""
    result = format_smart_number(1_234_567.891234, decimals=4)
    assert "1.2346M" in result
