"""
tests/unit/test_core_diagnostics.py

UNIT TESTS FOR DIAGNOSTIC SYSTEM
=================================
Role: Validates diagnostic event creation and severity handling.
Coverage: DiagnosticRegistry, DiagnosticEvent, FinancialContext.
Architecture: Core Diagnostics Tests.
Style: Pytest with parametrize for various diagnostic scenarios.
"""

from src.core.diagnostics import (
    DiagnosticRegistry,
    DiagnosticEvent,
    FinancialContext,
    SeverityLevel,
    DiagnosticDomain,
)


class TestDiagnosticRegistryEvents:
    """Test suite for DiagnosticRegistry event creation."""
    
    def test_model_g_divergence_returns_critical_event(self):
        """model_g_divergence should return a CRITICAL severity event."""
        event = DiagnosticRegistry.model_g_divergence(g=0.05, wacc=0.04)
        
        assert event is not None
        assert event.severity == SeverityLevel.CRITICAL
        assert event.code == "MODEL_G_DIVERGENCE"
        assert event.domain == DiagnosticDomain.MODEL
        assert "growth rate" in event.message.lower() or "g" in event.message.lower()
    
    def test_risk_excessive_growth_returns_warning_event(self):
        """risk_excessive_growth should return a WARNING severity event."""
        event = DiagnosticRegistry.risk_excessive_growth(g=0.15)
        
        assert event is not None
        assert event.severity == SeverityLevel.WARNING
        assert event.code == "RISK_EXCESSIVE_GROWTH"
        assert "growth" in event.message.lower()
    
    def test_fcfe_negative_flow_returns_critical_event(self):
        """fcfe_negative_flow should return a CRITICAL severity event."""
        event = DiagnosticRegistry.fcfe_negative_flow(val=-100.0)
        
        assert event is not None
        assert event.severity == SeverityLevel.CRITICAL
        assert event.code == "FCFE_NEGATIVE_FLOW"
        assert "negative" in event.message.lower() or "fcfe" in event.message.lower()


class TestDiagnosticEventBlocking:
    """Test suite for diagnostic event blocking behavior."""
    
    def test_critical_is_blocking(self):
        """CRITICAL severity events should be blocking."""
        event = DiagnosticEvent(
            code="TEST_CRITICAL",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.MODEL,
            message="Test critical event"
        )
        
        assert event.is_blocking is True
    
    def test_error_is_blocking(self):
        """ERROR severity events should be blocking."""
        event = DiagnosticEvent(
            code="TEST_ERROR",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message="Test error event"
        )
        
        assert event.is_blocking is True
    
    def test_warning_not_blocking(self):
        """WARNING severity events should NOT be blocking."""
        event = DiagnosticEvent(
            code="TEST_WARNING",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message="Test warning event"
        )
        
        assert event.is_blocking is False
    
    def test_info_not_blocking(self):
        """INFO severity events should NOT be blocking."""
        event = DiagnosticEvent(
            code="TEST_INFO",
            severity=SeverityLevel.INFO,
            domain=DiagnosticDomain.MODEL,
            message="Test info event"
        )
        
        assert event.is_blocking is False


class TestDiagnosticEventSerialization:
    """Test suite for diagnostic event serialization."""
    
    def test_to_dict_returns_valid_dictionary(self):
        """to_dict() should return a dictionary with expected keys."""
        event = DiagnosticEvent(
            code="TEST_EVENT",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.USER_INPUT,
            message="Test event message"
        )
        
        result = event.to_dict()
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "severity" in result
        assert "domain" in result
        assert "message" in result
        assert "is_blocking" in result
    
    def test_to_dict_values_correct(self):
        """to_dict() should serialize values correctly."""
        event = DiagnosticEvent(
            code="TEST_CODE",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.ENGINE,
            message="Test message"
        )
        
        result = event.to_dict()
        
        assert result["code"] == "TEST_CODE"
        assert result["severity"] == "ERROR"
        assert result["domain"] == "ENGINE"
        assert result["message"] == "Test message"
        assert result["is_blocking"] is True
    
    def test_to_dict_with_financial_context(self):
        """to_dict() should include financial_context when present."""
        context = FinancialContext(
            parameter_name="Test Parameter",
            current_value=0.15,
            typical_range=(0.0, 0.10),
            statistical_risk="Test risk",
            recommendation="Test recommendation"
        )
        
        event = DiagnosticEvent(
            code="TEST_EVENT",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message="Test message",
            financial_context=context
        )
        
        result = event.to_dict()
        
        assert "financial_context" in result
        assert result["financial_context"]["parameter"] == "Test Parameter"
        assert result["financial_context"]["value"] == 0.15
        assert "typical_range" in result["financial_context"]


class TestFinancialContext:
    """Test suite for FinancialContext utility."""
    
    def test_financial_context_creation(self):
        """FinancialContext should be creatable with all fields."""
        context = FinancialContext(
            parameter_name="Market Beta",
            current_value=2.5,
            typical_range=(0.5, 2.0),
            statistical_risk="Beta is unusually high",
            recommendation="Verify calculation with industry peers"
        )
        
        assert context.parameter_name == "Market Beta"
        assert context.current_value == 2.5
        assert context.typical_range == (0.5, 2.0)
        assert context.statistical_risk == "Beta is unusually high"
        assert context.recommendation == "Verify calculation with industry peers"
    
    def test_to_human_readable_returns_string(self):
        """to_human_readable() should return a non-empty string."""
        context = FinancialContext(
            parameter_name="WACC",
            current_value=0.25,
            typical_range=(0.08, 0.15),
            statistical_risk="WACC is exceptionally high",
            recommendation="Review cost of debt and equity assumptions"
        )
        
        result = context.to_human_readable()
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "WACC" in result
        assert "0.25" in result
    
    def test_to_human_readable_includes_all_info(self):
        """to_human_readable() should include all context information."""
        context = FinancialContext(
            parameter_name="Growth Rate",
            current_value=0.20,
            typical_range=(0.02, 0.08),
            statistical_risk="Growth rate is unsustainable",
            recommendation="Reduce to market average"
        )
        
        result = context.to_human_readable()
        
        # Check that key information is present
        assert "Growth Rate" in result
        assert "0.20" in result
        # Should mention typical range
        assert "0.02" in result or "2" in result
        assert "0.08" in result or "8" in result


class TestSeverityLevels:
    """Test suite for SeverityLevel enum."""
    
    def test_severity_levels_defined(self):
        """All required severity levels should be defined."""
        assert SeverityLevel.INFO is not None
        assert SeverityLevel.WARNING is not None
        assert SeverityLevel.ERROR is not None
        assert SeverityLevel.CRITICAL is not None
    
    def test_severity_levels_are_strings(self):
        """Severity level values should be strings."""
        assert isinstance(SeverityLevel.INFO.value, str)
        assert isinstance(SeverityLevel.WARNING.value, str)
        assert isinstance(SeverityLevel.ERROR.value, str)
        assert isinstance(SeverityLevel.CRITICAL.value, str)


class TestDiagnosticDomains:
    """Test suite for DiagnosticDomain enum."""
    
    def test_diagnostic_domains_defined(self):
        """All required diagnostic domains should be defined."""
        assert DiagnosticDomain.CONFIG is not None
        assert DiagnosticDomain.ENGINE is not None
        assert DiagnosticDomain.DATA is not None
        assert DiagnosticDomain.MODEL is not None
        assert DiagnosticDomain.PROVIDER is not None
        assert DiagnosticDomain.USER_INPUT is not None
        assert DiagnosticDomain.SYSTEM is not None
    
    def test_diagnostic_domains_are_strings(self):
        """Diagnostic domain values should be strings."""
        assert isinstance(DiagnosticDomain.MODEL.value, str)
        assert isinstance(DiagnosticDomain.ENGINE.value, str)
        assert isinstance(DiagnosticDomain.USER_INPUT.value, str)
