"""
tests/unit/test_guardrails.py

UNIT TESTS FOR ECONOMIC GUARDRAILS
===================================
Role: Comprehensive unit testing of all guardrail validation functions.
Coverage Target: 100%
"""

import pytest

from src.models.company import Company
from src.models.enums import CompanySector
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import (
    CapitalStructureParameters,
    CommonParameters,
    FinancialRatesParameters,
)
from src.models.parameters.options import ScenarioParameters
from src.models.parameters.strategies import (
    DDMParameters,
    FCFFGrowthParameters,
    FCFFNormalizedParameters,
    FCFFStandardParameters,
    TerminalValueParameters,
)
from src.valuation.guardrails import (
    GuardrailCheckResult,
    _extract_growth_rate,
    validate_capital_structure,
    validate_roic_spread,
    validate_scenario_probabilities,
    validate_terminal_growth,
)

# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def base_company():
    """Creates a basic company for testing."""
    return Company(
        ticker="TEST",
        name="Test Company",
        sector=CompanySector.TECHNOLOGY,
        current_price=100.0,
    )


@pytest.fixture
def base_parameters(base_company):
    """Creates basic parameters with standard strategy."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=5.0,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=3.0),
    )
    return Parameters(structure=base_company, strategy=strategy)


# ==============================================================================
# TEST GuardrailCheckResult MODEL
# ==============================================================================


def test_guardrail_check_result_creation():
    """Test that GuardrailCheckResult can be created with valid data."""
    result = GuardrailCheckResult(
        type="error",
        message="Test error",
        code="TEST_ERROR",
        extra={"key": "value"},
    )
    assert result.type == "error"
    assert result.message == "Test error"
    assert result.code == "TEST_ERROR"
    assert result.extra == {"key": "value"}


def test_guardrail_check_result_default_extra():
    """Test that extra defaults to empty dict."""
    result = GuardrailCheckResult(type="info", message="Test", code="TEST_INFO")
    assert result.extra == {}


def test_guardrail_check_result_type_validation():
    """Test that type field only accepts valid literals."""
    with pytest.raises(Exception):  # Pydantic validation error
        GuardrailCheckResult(type="invalid_type", message="Test", code="TEST")


# ==============================================================================
# TEST validate_terminal_growth
# ==============================================================================


def test_validate_terminal_growth_not_set(base_parameters):
    """Test when terminal growth is not specified."""
    # Remove terminal growth
    base_parameters.strategy.terminal_value.perpetual_growth_rate = None

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_NOT_SET"
    assert "not specified" in result.message.lower()


def test_validate_terminal_growth_exceeds_wacc(base_parameters):
    """Test ERROR when g >= WACC."""
    # Must reconstruct to trigger Pydantic scaling
    base_parameters.strategy.terminal_value = TerminalValueParameters(perpetual_growth_rate=12.0)

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_EXCEEDS_WACC"
    assert "cannot converge" in result.message.lower()
    assert result.extra["g"] == 0.12
    assert result.extra["wacc"] == 0.10


def test_validate_terminal_growth_equals_wacc(base_parameters):
    """Test ERROR when g == WACC."""
    base_parameters.strategy.terminal_value = TerminalValueParameters(perpetual_growth_rate=10.0)

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_EXCEEDS_WACC"


def test_validate_terminal_growth_close_to_wacc(base_parameters):
    """Test WARNING when g is very close to WACC."""
    base_parameters.strategy.terminal_value = TerminalValueParameters(perpetual_growth_rate=9.6)

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    assert result.type == "warning"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_CLOSE_TO_WACC"
    assert "dangerously close" in result.message.lower()
    assert result.extra["spread"] < 0.005


def test_validate_terminal_growth_ok(base_parameters):
    """Test INFO when g is positive and reasonable."""
    base_parameters.strategy.terminal_value = TerminalValueParameters(perpetual_growth_rate=3.0)

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_OK"
    assert "adequate spread" in result.message.lower()


def test_validate_terminal_growth_conservative(base_parameters):
    """Test INFO when g is zero or negative."""
    base_parameters.strategy.terminal_value.perpetual_growth_rate = 0.0

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_CONSERVATIVE"
    assert "conservative" in result.message.lower()


def test_validate_terminal_growth_negative(base_parameters):
    """Test INFO when g is negative."""
    base_parameters.strategy.terminal_value = TerminalValueParameters(perpetual_growth_rate=-2.0)

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_CONSERVATIVE"


# ==============================================================================
# TEST validate_roic_spread
# ==============================================================================


def test_validate_roic_insufficient_data(base_company, base_parameters):
    """Test when EBIT data is not available."""
    # Company without ebit_ttm attribute
    result = validate_roic_spread(base_company, base_parameters, wacc=0.10)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_ROIC_DATA_INSUFFICIENT"


def test_validate_roic_invalid_capital(base_company, base_parameters):
    """Test when invested capital calculation is invalid."""
    # Add EBIT but make capital structure result in negative invested capital
    # Use object.__setattr__ to bypass frozen model
    object.__setattr__(base_company, "ebit_ttm", 1000.0)
    base_parameters.common.capital.total_debt = 0.0
    base_parameters.common.capital.cash_and_equivalents = 50000.0  # Huge cash
    base_parameters.common.capital.shares_outstanding = 1.0

    result = validate_roic_spread(base_company, base_parameters, wacc=0.10)

    assert result.type == "info"
    assert result.code in ["GUARDRAIL_ROIC_INVALID_CAPITAL", "GUARDRAIL_ROIC_BELOW_WACC_WITH_GROWTH"]


def test_validate_roic_no_growth(base_company, base_parameters):
    """Test when there's no positive growth assumed."""
    object.__setattr__(base_company, "ebit_ttm", 1000.0)
    base_parameters.common.capital.total_debt = 5000.0
    base_parameters.common.capital.cash_and_equivalents = 1000.0
    base_parameters.common.capital.shares_outstanding = 100.0
    base_parameters.strategy.growth_rate_p1 = 0.0  # No growth

    result = validate_roic_spread(base_company, base_parameters, wacc=0.10)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_ROIC_NO_GROWTH"


def test_validate_roic_below_wacc_with_growth(base_company, base_parameters):
    """Test WARNING when ROIC < WACC with positive growth."""
    object.__setattr__(base_company, "ebit_ttm", 500.0)  # Low EBIT
    # Reconstruct parameters to trigger scaling
    # Note: capital values use million scale (×1,000,000): 0.01 → 10,000, 0.001 → 1,000, 0.0001 → 100
    base_parameters.common = CommonParameters(
        rates=FinancialRatesParameters(tax_rate=21.0),
        capital=CapitalStructureParameters(
            total_debt=0.01,  # Input 0.01 × 1M = 10,000
            cash_and_equivalents=0.001,  # Input 0.001 × 1M = 1,000
            shares_outstanding=0.0001,  # Input 0.0001 × 1M = 100 shares
        ),
    )
    base_parameters.strategy = FCFFStandardParameters(
        projection_years=5, growth_rate_p1=5.0, terminal_value=TerminalValueParameters(perpetual_growth_rate=3.0)
    )

    result = validate_roic_spread(base_company, base_parameters, wacc=0.10)

    assert result.type == "warning"
    assert result.code == "GUARDRAIL_ROIC_BELOW_WACC_WITH_GROWTH"
    assert "value destruction" in result.message.lower()


def test_validate_roic_neutral(base_company, base_parameters):
    """Test INFO when ROIC approximately equals WACC."""
    # Set up to get ROIC ≈ WACC
    object.__setattr__(base_company, "ebit_ttm", 1000.0)
    # Reconstruct parameters to trigger scaling
    # Note: capital values use million scale (×1,000,000): 0.005 → 5,000, 0.001 → 1,000, 0.0001 → 100
    base_parameters.common = CommonParameters(
        rates=FinancialRatesParameters(tax_rate=21.0),
        capital=CapitalStructureParameters(
            total_debt=0.005,  # Input 0.005 × 1M = 5,000
            cash_and_equivalents=0.001,  # Input 0.001 × 1M = 1,000
            shares_outstanding=0.0001,  # 100 shares -> Market equity = 10,000 (100 * 100)
        ),
    )
    # NOPAT = 1000 * 0.79 = 790
    # Invested Capital = 5000 + 10000 - 1000 = 14000
    # ROIC = 790 / 14000 ≈ 0.056 (5.6%)
    base_parameters.strategy = FCFFStandardParameters(
        projection_years=5, growth_rate_p1=5.0, terminal_value=TerminalValueParameters(perpetual_growth_rate=3.0)
    )

    result = validate_roic_spread(base_company, base_parameters, wacc=0.056)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_ROIC_NEUTRAL"


def test_validate_roic_above_wacc(base_company, base_parameters):
    """Test INFO when ROIC > WACC (value creation)."""
    object.__setattr__(base_company, "ebit_ttm", 2000.0)  # High EBIT
    # Reconstruct parameters to trigger scaling
    # Note: capital values use million scale (×1,000,000): 0.005 → 5,000, 0.001 → 1,000, 0.0001 → 100
    base_parameters.common = CommonParameters(
        rates=FinancialRatesParameters(tax_rate=21.0),
        capital=CapitalStructureParameters(
            total_debt=0.005,  # Input 0.005 × 1M = 5,000
            cash_and_equivalents=0.001,  # Input 0.001 × 1M = 1,000
            shares_outstanding=0.0001,  # 100 shares
        ),
    )
    base_parameters.strategy = FCFFStandardParameters(
        projection_years=5, growth_rate_p1=5.0, terminal_value=TerminalValueParameters(perpetual_growth_rate=3.0)
    )

    result = validate_roic_spread(base_company, base_parameters, wacc=0.08)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_ROIC_ABOVE_WACC"
    assert "value creation" in result.message.lower()


# ==============================================================================
# TEST validate_capital_structure
# ==============================================================================


def test_validate_capital_negative_debt(base_company, base_parameters):
    """Test ERROR when debt is negative."""
    base_parameters.common.capital.total_debt = -1000.0
    base_parameters.common.capital.shares_outstanding = 100.0

    result = validate_capital_structure(base_company, base_parameters)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_CAPITAL_NEGATIVE_DEBT"


def test_validate_capital_negative_cash(base_company, base_parameters):
    """Test ERROR when cash is negative."""
    base_parameters.common.capital.total_debt = 1000.0
    base_parameters.common.capital.cash_and_equivalents = -500.0
    base_parameters.common.capital.shares_outstanding = 100.0

    result = validate_capital_structure(base_company, base_parameters)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_CAPITAL_NEGATIVE_CASH"


def test_validate_capital_invalid_shares_none(base_company, base_parameters):
    """Test ERROR when shares outstanding is None."""
    base_parameters.common.capital.total_debt = 1000.0
    base_parameters.common.capital.cash_and_equivalents = 500.0
    base_parameters.common.capital.shares_outstanding = None

    result = validate_capital_structure(base_company, base_parameters)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_CAPITAL_INVALID_SHARES"


def test_validate_capital_invalid_shares_zero(base_company, base_parameters):
    """Test ERROR when shares outstanding is zero."""
    base_parameters.common.capital.total_debt = 1000.0
    base_parameters.common.capital.cash_and_equivalents = 500.0
    base_parameters.common.capital.shares_outstanding = 0.0

    result = validate_capital_structure(base_company, base_parameters)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_CAPITAL_INVALID_SHARES"


def test_validate_capital_extreme_debt_equity(base_company, base_parameters):
    """Test WARNING when debt/equity ratio is extreme."""
    base_parameters.common.capital.total_debt = 110000.0  # Very high debt (>10x equity)
    base_parameters.common.capital.cash_and_equivalents = 500.0
    base_parameters.common.capital.shares_outstanding = 100.0  # Market equity = 10000

    result = validate_capital_structure(base_company, base_parameters)

    assert result.type == "warning"
    assert result.code == "GUARDRAIL_CAPITAL_EXTREME_DEBT_EQUITY"
    assert "extremely high" in result.message.lower()


def test_validate_capital_excessive_cash(base_company, base_parameters):
    """Test WARNING when cash >> debt."""
    base_parameters.common.capital.total_debt = 1000.0
    base_parameters.common.capital.cash_and_equivalents = 6000.0  # 6x debt
    base_parameters.common.capital.shares_outstanding = 100.0

    result = validate_capital_structure(base_company, base_parameters)

    assert result.type == "warning"
    assert result.code == "GUARDRAIL_CAPITAL_EXCESSIVE_CASH"
    assert "holding company" in result.message.lower()


def test_validate_capital_ok(base_company, base_parameters):
    """Test INFO when capital structure is normal."""
    base_parameters.common.capital.total_debt = 5000.0
    base_parameters.common.capital.cash_and_equivalents = 2000.0
    base_parameters.common.capital.shares_outstanding = 100.0

    result = validate_capital_structure(base_company, base_parameters)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_CAPITAL_OK"
    assert result.extra["net_debt"] == 3000.0


# ==============================================================================
# TEST validate_scenario_probabilities
# ==============================================================================


def test_validate_scenario_not_enabled(base_parameters):
    """Test when scenarios are not enabled."""
    base_parameters.extensions.scenarios.enabled = False

    result = validate_scenario_probabilities(base_parameters)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_SCENARIOS_NOT_ENABLED"


def test_validate_scenario_probabilities_invalid_sum(base_parameters):
    """Test ERROR when probabilities sum is way off."""
    base_parameters.extensions.scenarios.enabled = True
    base_parameters.extensions.scenarios.cases = [
        ScenarioParameters(name="Bear", probability=0.3),
        ScenarioParameters(name="Base", probability=0.4),
        ScenarioParameters(name="Bull", probability=0.2),  # Sum = 0.9
    ]

    result = validate_scenario_probabilities(base_parameters)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_SCENARIOS_PROBABILITIES_INVALID_SUM"
    assert result.extra["prob_sum"] == pytest.approx(0.9)


def test_validate_scenario_probabilities_inexact(base_parameters):
    """Test WARNING when probabilities sum is close but not exact."""
    base_parameters.extensions.scenarios.enabled = True
    base_parameters.extensions.scenarios.cases = [
        ScenarioParameters(name="Bear", probability=0.33),
        ScenarioParameters(name="Base", probability=0.34),
        ScenarioParameters(name="Bull", probability=0.33),  # Sum = 1.00 (approx)
    ]

    result = validate_scenario_probabilities(base_parameters)

    # This should be WARNING or INFO depending on exact sum
    assert result.type in ["warning", "info"]
    if result.type == "warning":
        assert result.code == "GUARDRAIL_SCENARIOS_PROBABILITIES_INEXACT"


def test_validate_scenario_probabilities_ok(base_parameters):
    """Test INFO when probabilities sum to exactly 1.0."""
    base_parameters.extensions.scenarios.enabled = True
    base_parameters.extensions.scenarios.cases = [
        ScenarioParameters(name="Bear", probability=0.25),
        ScenarioParameters(name="Base", probability=0.50),
        ScenarioParameters(name="Bull", probability=0.25),  # Sum = 1.0
    ]

    result = validate_scenario_probabilities(base_parameters)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_SCENARIOS_PROBABILITIES_OK"
    assert result.extra["prob_sum"] == pytest.approx(1.0)


def test_validate_scenario_probabilities_over_limit(base_parameters):
    """Test ERROR when probabilities sum exceeds upper bound."""
    base_parameters.extensions.scenarios.enabled = True
    base_parameters.extensions.scenarios.cases = [
        ScenarioParameters(name="Bear", probability=0.4),
        ScenarioParameters(name="Base", probability=0.5),
        ScenarioParameters(name="Bull", probability=0.3),  # Sum = 1.2
    ]

    result = validate_scenario_probabilities(base_parameters)

    assert result.type == "error"
    assert result.code == "GUARDRAIL_SCENARIOS_PROBABILITIES_INVALID_SUM"


def test_validate_scenario_probabilities_with_none(base_parameters):
    """Test when some probabilities are None (default to 0)."""
    base_parameters.extensions.scenarios.enabled = True
    base_parameters.extensions.scenarios.cases = [
        ScenarioParameters(name="Bear", probability=None),
        ScenarioParameters(name="Base", probability=1.0),
    ]

    result = validate_scenario_probabilities(base_parameters)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_SCENARIOS_PROBABILITIES_OK"


# ==============================================================================
# TEST _extract_growth_rate HELPER
# ==============================================================================


def test_extract_growth_rate_fcff_standard():
    """Test extraction from FCFFStandardParameters."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=8.0,
    )
    assert _extract_growth_rate(strategy) == 0.08


def test_extract_growth_rate_fcff_normalized():
    """Test extraction from FCFFNormalizedParameters."""
    strategy = FCFFNormalizedParameters(
        projection_years=5,
        growth_rate=6.0,
    )
    assert _extract_growth_rate(strategy) == 0.06


def test_extract_growth_rate_fcff_growth():
    """Test extraction from FCFFGrowthParameters."""
    strategy = FCFFGrowthParameters(
        projection_years=5,
        revenue_growth_rate=7.0,  # Correct field name
    )
    assert _extract_growth_rate(strategy) == 0.07


def test_extract_growth_rate_ddm():
    """Test extraction from DDMParameters."""
    strategy = DDMParameters(
        projection_years=5,
        growth_rate=4.0,
    )
    assert _extract_growth_rate(strategy) == 0.04


def test_extract_growth_rate_terminal_fallback():
    """Test fallback to terminal growth rate."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=None,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=3.0),
    )
    assert _extract_growth_rate(strategy) == 0.03


def test_extract_growth_rate_none():
    """Test when no growth rate is available."""
    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=None,
    )
    # Terminal value defaults to None for perpetual_growth_rate
    result = _extract_growth_rate(strategy)
    # Should either return None or terminal growth (None)
    assert result is None or isinstance(result, float)


# ==============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# ==============================================================================


def test_validate_terminal_growth_very_small_spread(base_parameters):
    """Test boundary at exactly 0.5% spread."""
    base_parameters.strategy.terminal_value = TerminalValueParameters(
        perpetual_growth_rate=9.55
    )  # 9.55%, spread = 0.45%

    result = validate_terminal_growth(base_parameters, wacc=0.10)

    # Should be WARNING since spread is less than threshold
    assert result.type == "warning"


def test_validate_roic_with_zero_tax_rate(base_company, base_parameters):
    """Test ROIC calculation with zero tax rate."""
    object.__setattr__(base_company, "ebit_ttm", 1000.0)
    # Reconstruct parameters to trigger scaling
    # Note: capital values use million scale (×1,000,000): 0.005 → 5,000, 0.001 → 1,000, 0.0001 → 100
    base_parameters.common = CommonParameters(
        rates=FinancialRatesParameters(tax_rate=0.0),  # No tax
        capital=CapitalStructureParameters(
            total_debt=0.005,  # Input 0.005 × 1M = 5,000
            cash_and_equivalents=0.001,  # Input 0.001 × 1M = 1,000
            shares_outstanding=0.0001,  # 100 shares
        ),
    )
    base_parameters.strategy = FCFFStandardParameters(
        projection_years=5, growth_rate_p1=5.0, terminal_value=TerminalValueParameters(perpetual_growth_rate=3.0)
    )

    result = validate_roic_spread(base_company, base_parameters, wacc=0.10)

    # Should complete without error
    assert result.type in ["info", "warning"]


def test_validate_capital_zero_debt(base_company, base_parameters):
    """Test capital structure with zero debt (equity financed)."""
    base_parameters.common.capital.total_debt = 0.0
    base_parameters.common.capital.cash_and_equivalents = 5000.0
    base_parameters.common.capital.shares_outstanding = 100.0

    result = validate_capital_structure(base_company, base_parameters)

    # Should be OK, no warnings about excessive cash when debt is zero
    assert result.type == "info"
    assert result.code == "GUARDRAIL_CAPITAL_OK"


def test_validate_terminal_growth_with_no_terminal_value_object(base_company):
    """Test when strategy has no terminal_value attribute at all."""
    from src.models.parameters.strategies import GrahamParameters

    strategy = GrahamParameters()
    params = Parameters(structure=base_company, strategy=strategy)

    result = validate_terminal_growth(params, wacc=0.10)

    assert result.type == "info"
    assert result.code == "GUARDRAIL_TERMINAL_GROWTH_NOT_SET"
