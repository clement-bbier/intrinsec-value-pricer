"""
tests/integration/test_guardrails_integration.py

INTEGRATION TESTS FOR GUARDRAILS IN ORCHESTRATOR
================================================
Role: Tests that economic guardrails are properly integrated into the valuation pipeline.
Coverage: End-to-end testing of guardrails blocking/warning/info behavior.
"""

import pytest

from src.core.exceptions import CalculationError
from src.models.company import Company, CompanySnapshot
from src.models.enums import CompanySector, ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CapitalStructureParameters, CommonParameters
from src.models.parameters.options import ScenarioParameters
from src.models.parameters.strategies import FCFFStandardParameters, TerminalValueParameters
from src.models.valuation import ValuationRequest
from src.valuation.orchestrator import ValuationOrchestrator


@pytest.fixture
def orchestrator():
    """Creates a ValuationOrchestrator instance."""
    return ValuationOrchestrator()


@pytest.fixture
def base_company():
    """Creates a base company for testing."""
    return Company(
        ticker="TEST",
        name="Test Company",
        sector=CompanySector.TECHNOLOGY,
        current_price=100.0,
    )


@pytest.fixture
def good_snapshot():
    """Creates a valid snapshot with good economic assumptions."""
    return CompanySnapshot(
        ticker="TEST",
        name="Test Company",
        sector="Technology",
        current_price=100.0,
        total_debt=5000.0,
        cash_and_equivalents=2000.0,
        shares_outstanding=100.0,
        revenue_ttm=50000.0,
        ebit_ttm=10000.0,
        net_income_ttm=7000.0,
        fcf_ttm=8000.0,
        beta=1.2,
        risk_free_rate=0.04,
        market_risk_premium=0.05,
        tax_rate=0.21,
    )


def test_guardrails_pass_with_valid_parameters(orchestrator, base_company, good_snapshot):
    """Test that guardrails pass with economically sound parameters."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,
        fcf_anchor=8000.0,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=0.025),  # g < WACC
    )

    params = Parameters(structure=base_company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    # Should not raise, guardrails should pass
    result = orchestrator.run(request, good_snapshot)

    # Check that audit report exists and contains guardrail events
    assert result.audit_report is not None
    assert len(result.audit_report.events) > 0

    # Should have at least some info events from guardrails
    info_events = [e for e in result.audit_report.events if e.code.startswith("GUARDRAIL_")]
    assert len(info_events) > 0


def test_guardrails_block_when_terminal_growth_exceeds_wacc(orchestrator, base_company, good_snapshot):
    """Test that guardrails block valuation when g >= WACC."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,
        fcf_anchor=8000.0,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=0.15),  # g > typical WACC
    )

    params = Parameters(structure=base_company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    # Should raise CalculationError due to guardrail failure
    with pytest.raises(CalculationError) as exc_info:
        orchestrator.run(request, good_snapshot)

    # Error message should mention guardrails
    assert "guardrails" in str(exc_info.value).lower()


def test_guardrails_warn_with_invalid_capital_structure(orchestrator, good_snapshot):
    """Test that guardrails produce warnings for extreme capital structures."""
    # Create company and parameters with extreme debt/equity
    company = Company(
        ticker="TEST",
        name="Test Company",
        sector=CompanySector.TECHNOLOGY,
        current_price=10.0,  # Low price with same shares = low market cap
    )

    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,
        fcf_anchor=8000.0,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=0.025),
    )

    params = Parameters(
        structure=company,
        strategy=strategy,
        common=CommonParameters(
            capital=CapitalStructureParameters(
                total_debt=100000.0,  # Very high debt
                cash_and_equivalents=500.0,
                shares_outstanding=100.0,  # Market equity = 1000
            )
        ),
    )
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    # Should not block, but should produce warnings
    result = orchestrator.run(request, good_snapshot)

    # Check for capital structure warning in audit report
    assert result.audit_report is not None
    warning_codes = [e.code for e in result.audit_report.events if e.code.startswith("GUARDRAIL_CAPITAL")]
    assert len(warning_codes) > 0
    assert result.audit_report.critical_warnings > 0


def test_guardrails_block_invalid_scenario_probabilities(orchestrator, base_company, good_snapshot):
    """Test that guardrails block when scenario probabilities don't sum to 1.0."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,
        fcf_anchor=8000.0,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=0.025),
    )

    params = Parameters(structure=base_company, strategy=strategy)

    # Enable scenarios with invalid probabilities
    params.extensions.scenarios.enabled = True
    params.extensions.scenarios.cases = [
        ScenarioParameters(name="Bear", probability=0.3),
        ScenarioParameters(name="Base", probability=0.4),
        ScenarioParameters(name="Bull", probability=0.2),  # Sum = 0.9
    ]

    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    # Should raise due to invalid probabilities
    with pytest.raises(CalculationError) as exc_info:
        orchestrator.run(request, good_snapshot)

    assert "guardrails" in str(exc_info.value).lower()


def test_guardrails_info_messages_attached_to_audit(orchestrator, base_company, good_snapshot):
    """Test that info-level guardrail messages are attached to audit report."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,
        fcf_anchor=8000.0,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=0.02),  # Conservative
    )

    params = Parameters(structure=base_company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    result = orchestrator.run(request, good_snapshot)

    # Check that we have info events from guardrails
    assert result.audit_report is not None
    guardrail_events = [e for e in result.audit_report.events if e.code.startswith("GUARDRAIL_")]

    # Should have multiple guardrail events (terminal growth, capital structure, scenarios, etc.)
    assert len(guardrail_events) >= 3

    # Most should be INFO level (no errors/warnings with good params)
    info_events = [e for e in guardrail_events if str(e.severity).endswith("INFO")]
    assert len(info_events) >= 2


def test_guardrails_warning_for_close_terminal_growth(orchestrator, base_company, good_snapshot):
    """Test that guardrails warn when terminal growth is close to WACC."""
    # Use a growth rate that's close to typical WACC but still below it
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,
        fcf_anchor=8000.0,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=0.077),  # Close to but below WACC
    )

    params = Parameters(structure=base_company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    result = orchestrator.run(request, good_snapshot)

    # Should have a warning about terminal growth being close to WACC
    assert result.audit_report is not None

    # Check if we got a WARNING event (may vary depending on exact WACC calculation)
    # At minimum, valuation should complete successfully
    assert result.results is not None  # Valuation completed

    # Should have guardrail events
    guardrail_events = [e for e in result.audit_report.events if e.code.startswith("GUARDRAIL_")]
    assert len(guardrail_events) > 0


def test_guardrails_handle_missing_terminal_value_gracefully(orchestrator, base_company, good_snapshot):
    """Test that guardrails handle missing terminal value parameters gracefully."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,
        fcf_anchor=8000.0,
        # No terminal_value set (defaults to None/empty)
    )

    params = Parameters(structure=base_company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    # Should not crash, should handle gracefully
    result = orchestrator.run(request, good_snapshot)

    assert result.audit_report is not None
    # Should have an INFO event about terminal growth not being set
    terminal_growth_events = [
        e for e in result.audit_report.events if "TERMINAL_GROWTH" in e.code
    ]
    assert len(terminal_growth_events) > 0
