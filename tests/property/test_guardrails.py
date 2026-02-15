"""
tests/property/test_guardrails.py

PROPERTY-BASED TESTS FOR ECONOMIC GUARDRAILS
============================================
Role: Uses Hypothesis to test guardrails with random inputs to discover edge cases.
Framework: Hypothesis for property-based testing.
Coverage: Invariants and mathematical properties that must hold for all inputs.
"""

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import (
    CapitalStructureParameters,
    CommonParameters,
)
from src.models.parameters.options import ScenarioParameters
from src.models.parameters.strategies import FCFFStandardParameters, TerminalValueParameters
from src.valuation.guardrails import (
    validate_capital_structure,
    validate_roic_spread,
    validate_scenario_probabilities,
    validate_terminal_growth,
)

# ==============================================================================
# HYPOTHESIS STRATEGIES
# ==============================================================================

# Generate valid growth rates (typically -5% to 15%, but as whole numbers for percentage fields)
growth_rate_strategy = st.floats(min_value=-5.0, max_value=15.0, allow_nan=False, allow_infinity=False)

# Generate valid WACC (typically 5% to 25%, as whole numbers for percentage fields)
wacc_strategy = st.floats(min_value=5.0, max_value=25.0, allow_nan=False, allow_infinity=False)

# Generate valid probabilities (0 to 1)
probability_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Generate positive floats for financial data
positive_float_strategy = st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False)

# Generate financial amounts (can be zero or positive, in millions)
financial_amount_strategy = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)

# Generate share counts (positive, typically millions)
shares_strategy = st.floats(min_value=1.0, max_value=1e5, allow_nan=False, allow_infinity=False)


# ==============================================================================
# PROPERTY: Terminal Growth Must Always Return Error/Warning if g >= WACC
# ==============================================================================


@given(g=growth_rate_strategy, wacc=wacc_strategy)
@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_terminal_growth_divergence_always_caught(g, wacc):
    """
    Property: If g >= WACC, validate_terminal_growth MUST return error.

    This ensures the guardrail never allows model divergence.
    """
    # Create minimal parameters with terminal growth
    company = Company(ticker="TEST", name="Test", current_price=100.0)
    strategy = FCFFStandardParameters(
        projection_years=5,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=g),  # Will be scaled to g/100
    )
    params = Parameters(structure=company, strategy=strategy)

    # WACC is passed directly to the function, so we need to convert it to decimal
    wacc_decimal = wacc / 100.0
    result = validate_terminal_growth(params, wacc=wacc_decimal)

    # After scaling, g becomes g/100, so we compare g/100 with wacc/100
    g_decimal = g / 100.0

    # INVARIANT: If g >= WACC, must be ERROR
    if g_decimal >= wacc_decimal:
        assert result.type == "error", (
            f"Failed: g={g_decimal}, wacc={wacc_decimal} should be ERROR but got {result.type}"
        )
        assert result.code == "GUARDRAIL_TERMINAL_GROWTH_EXCEEDS_WACC"

    # Additional check: result should always be valid
    assert result.type in ["error", "warning", "info"]
    assert isinstance(result.message, str)
    assert isinstance(result.code, str)


# ==============================================================================
# PROPERTY: Terminal Growth Monotonicity
# ==============================================================================


@given(g=growth_rate_strategy, wacc1=wacc_strategy, wacc2=wacc_strategy)
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_terminal_growth_monotonicity(g, wacc1, wacc2):
    """
    Property: For increasing WACC, the severity should decrease (more lenient).

    If wacc1 < wacc2:
    - If ERROR at wacc1, should be ERROR or less severe at wacc2
    - If WARNING at wacc1, should be WARNING/INFO at wacc2
    """
    assume(wacc1 < wacc2)  # Ensure ordered
    assume(wacc2 - wacc1 > 1.0)  # Significant difference (1% as whole number)

    company = Company(ticker="TEST", name="Test", current_price=100.0)
    strategy = FCFFStandardParameters(
        projection_years=5,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=g),
    )
    params = Parameters(structure=company, strategy=strategy)

    # Convert WACC values to decimals
    wacc1_decimal = wacc1 / 100.0
    wacc2_decimal = wacc2 / 100.0

    result1 = validate_terminal_growth(params, wacc=wacc1_decimal)
    result2 = validate_terminal_growth(params, wacc=wacc2_decimal)

    # Map severity to numeric values for comparison
    severity_map = {"error": 3, "warning": 2, "info": 1}

    sev1 = severity_map.get(result1.type, 0)
    sev2 = severity_map.get(result2.type, 0)

    # INVARIANT: Increasing WACC should not increase severity
    assert sev2 <= sev1, (
        f"Monotonicity violated: g={g / 100}, wacc1={wacc1_decimal} ({result1.type}), wacc2={wacc2_decimal} ({result2.type})"
    )


# ==============================================================================
# PROPERTY: Scenario Probabilities Must Block or Warn if Sum != 1.0
# ==============================================================================


@given(probs=st.lists(probability_strategy, min_size=1, max_size=5))
@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_scenario_probabilities_validation(probs):
    """
    Property: If scenario probabilities don't sum to 1.0 (±0.01), must return error or warning.
    """
    # Create parameters with scenario probabilities
    company = Company(ticker="TEST", name="Test", current_price=100.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)

    # Enable scenarios and set probabilities
    params.extensions.scenarios.enabled = True
    params.extensions.scenarios.cases = [
        ScenarioParameters(name=f"Case{i}", probability=p) for i, p in enumerate(probs)
    ]

    result = validate_scenario_probabilities(params)

    prob_sum = sum(probs)
    tolerance = 0.01

    # INVARIANT: If sum is outside [0.99, 1.01], must be ERROR
    if prob_sum < (1.0 - tolerance) or prob_sum > (1.0 + tolerance):
        assert result.type == "error", f"Failed: prob_sum={prob_sum} should be ERROR"
        assert result.code == "GUARDRAIL_SCENARIOS_PROBABILITIES_INVALID_SUM"

    # INVARIANT: If sum is within tolerance but not exact, may be WARNING
    elif prob_sum != 1.0:
        assert result.type in ["warning", "info"], f"Unexpected type for prob_sum={prob_sum}: {result.type}"

    # INVARIANT: If sum is exactly 1.0, must be INFO (OK)
    else:
        assert result.type == "info"
        assert result.code == "GUARDRAIL_SCENARIOS_PROBABILITIES_OK"


# ==============================================================================
# PROPERTY: No Division by Zero in All Guardrails
# ==============================================================================


@given(
    total_debt=financial_amount_strategy,
    cash=financial_amount_strategy,
    shares=shares_strategy,
    price=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
    wacc=wacc_strategy,
    g=growth_rate_strategy,
)
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_no_division_by_zero(total_debt, cash, shares, price, wacc, g):
    """
    Property: Guardrail functions should never crash with division by zero.

    Tests with various edge cases including zero values.
    """
    # Create company and parameters
    company = Company(ticker="TEST", name="Test", current_price=price)

    strategy = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=g,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=g * 0.6),  # Terminal g < projection g
    )

    params = Parameters(
        structure=company,
        strategy=strategy,
        common=CommonParameters(
            capital=CapitalStructureParameters(
                total_debt=total_debt,
                cash_and_equivalents=cash,
                shares_outstanding=shares,
            )
        ),
    )

    # All these should complete without exceptions (no division by zero)
    try:
        # Note: wacc needs to be converted to decimal since it's passed as raw float, not through Pydantic
        wacc_decimal = wacc / 100.0
        result1 = validate_terminal_growth(params, wacc=wacc_decimal)
        assert result1.type in ["error", "warning", "info"]

        result2 = validate_capital_structure(company, params)
        assert result2.type in ["error", "warning", "info"]

        result3 = validate_roic_spread(company, params, wacc=wacc_decimal)
        assert result3.type in ["error", "warning", "info"]

    except ZeroDivisionError:
        pytest.fail("Division by zero occurred in guardrail validation")
    except Exception as e:
        # Other exceptions might be acceptable (e.g., validation errors)
        # But not arithmetic errors
        if "division" in str(e).lower() or "divide" in str(e).lower():
            pytest.fail(f"Division error occurred: {e}")


# ==============================================================================
# PROPERTY: Capital Structure Always Returns Structured Result
# ==============================================================================


@given(
    total_debt=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    cash=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    shares=st.floats(min_value=-100.0, max_value=1e5, allow_nan=False, allow_infinity=False) | st.none(),
)
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_capital_structure_always_structured_result(total_debt, cash, shares):
    """
    Property: validate_capital_structure always returns a valid GuardrailCheckResult.

    Even with invalid/negative inputs, should return structured error, not crash.
    """
    company = Company(ticker="TEST", name="Test", current_price=100.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(
        structure=company,
        strategy=strategy,
        common=CommonParameters(
            capital=CapitalStructureParameters(
                total_debt=total_debt,
                cash_and_equivalents=cash,
                shares_outstanding=shares,
            )
        ),
    )

    result = validate_capital_structure(company, params)

    # INVARIANT: Always returns a structured result
    assert hasattr(result, "type")
    assert hasattr(result, "message")
    assert hasattr(result, "code")
    assert result.type in ["error", "warning", "info"]
    assert isinstance(result.message, str)
    assert len(result.message) > 0
    assert isinstance(result.code, str)
    assert result.code.startswith("GUARDRAIL_")


# ==============================================================================
# PROPERTY: ROIC Spread Handles Missing/Invalid Data Gracefully
# ==============================================================================


@given(
    ebit=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False) | st.none(),
    total_debt=financial_amount_strategy,
    cash=financial_amount_strategy,
    shares=shares_strategy,
    price=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
    wacc=wacc_strategy,
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_roic_handles_missing_data(ebit, total_debt, cash, shares, price, wacc):
    """
    Property: validate_roic_spread handles missing or invalid EBIT gracefully.

    Should return INFO when data is insufficient, not crash.
    """
    company = Company(ticker="TEST", name="Test", current_price=price)
    if ebit is not None:
        # Use object.__setattr__ to bypass frozen model
        object.__setattr__(company, "ebit_ttm", ebit)

    strategy = FCFFStandardParameters(projection_years=5, growth_rate_p1=5.0)  # 5%
    params = Parameters(
        structure=company,
        strategy=strategy,
        common=CommonParameters(
            capital=CapitalStructureParameters(
                total_debt=total_debt,
                cash_and_equivalents=cash,
                shares_outstanding=shares,
            )
        ),
    )

    # Convert wacc to decimal
    wacc_decimal = wacc / 100.0
    result = validate_roic_spread(company, params, wacc=wacc_decimal)

    # INVARIANT: Never crashes, always returns structured result
    assert result.type in ["error", "warning", "info"]
    assert isinstance(result.code, str)

    # If EBIT is None or invalid, should return INFO with insufficient data code
    if ebit is None or ebit <= 0:
        assert result.type == "info"
        assert "ROIC" in result.code


# ==============================================================================
# PROPERTY: All Guardrail Extra Fields Are JSON-Serializable
# ==============================================================================


@given(
    g=growth_rate_strategy,
    wacc=wacc_strategy,
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_extra_fields_json_serializable(g, wacc):
    """
    Property: All extra fields in GuardrailCheckResult must be JSON-serializable.

    This ensures the results can be logged and transmitted.
    """
    import json

    company = Company(ticker="TEST", name="Test", current_price=100.0)
    strategy = FCFFStandardParameters(
        projection_years=5,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=g),
    )
    params = Parameters(structure=company, strategy=strategy)

    # Convert wacc to decimal
    wacc_decimal = wacc / 100.0
    result = validate_terminal_growth(params, wacc=wacc_decimal)

    # INVARIANT: Extra dict must be JSON-serializable
    try:
        json.dumps(result.extra)
    except (TypeError, ValueError) as e:
        pytest.fail(f"Extra fields are not JSON-serializable: {e}")


# ==============================================================================
# PROPERTY: Terminal Growth Threshold Boundary (0.5%)
# ==============================================================================


@given(
    base_wacc=st.floats(min_value=8.0, max_value=20.0, allow_nan=False, allow_infinity=False),
    epsilon=st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_terminal_growth_threshold_boundary(base_wacc, epsilon):
    """
    Property: The 0.5% threshold for WARNING is correctly applied.

    Tests the boundary around WACC - 0.005 to ensure classification is correct.
    """
    # Set g to be just above or below the threshold
    threshold = 0.5  # 0.5% as a whole number for percentage field
    g = base_wacc - threshold + epsilon

    company = Company(ticker="TEST", name="Test", current_price=100.0)
    strategy = FCFFStandardParameters(
        projection_years=5,
        terminal_value=TerminalValueParameters(perpetual_growth_rate=g),
    )
    params = Parameters(structure=company, strategy=strategy)

    # WACC needs to be converted to decimal since it's passed directly to the function
    wacc_decimal = base_wacc / 100.0
    result = validate_terminal_growth(params, wacc=wacc_decimal)

    # After scaling, the values will be divided by 100
    # So g and base_wacc entered as whole numbers become decimals
    # spread calculation needs to account for this
    g_decimal = g / 100.0
    spread = wacc_decimal - g_decimal
    threshold_decimal = 0.005  # 0.5% as decimal

    # INVARIANT: Classification must be consistent with spread
    if g_decimal >= wacc_decimal:
        assert result.type == "error"
    elif 0 <= spread < threshold_decimal:
        assert result.type == "warning"
    elif g_decimal > 0:
        assert result.type == "info"
        assert result.code == "GUARDRAIL_TERMINAL_GROWTH_OK"
    else:
        assert result.type == "info"
        assert result.code == "GUARDRAIL_TERMINAL_GROWTH_CONSERVATIVE"


# ==============================================================================
# PROPERTY: Scenario Probability Sum Tolerance (±1%)
# ==============================================================================


@given(
    base_prob=st.floats(min_value=0.95, max_value=1.05, allow_nan=False, allow_infinity=False),
    num_scenarios=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_property_scenario_probability_tolerance(base_prob, num_scenarios):
    """
    Property: The ±1% tolerance for scenario probabilities is correctly enforced.

    Tests boundary cases around the 0.99-1.01 range.
    """
    # Distribute base_prob across num_scenarios
    probs = [base_prob / num_scenarios] * num_scenarios

    company = Company(ticker="TEST", name="Test", current_price=100.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)

    params.extensions.scenarios.enabled = True
    params.extensions.scenarios.cases = [
        ScenarioParameters(name=f"Case{i}", probability=p) for i, p in enumerate(probs)
    ]

    result = validate_scenario_probabilities(params)

    prob_sum = sum(probs)
    tolerance = 0.01

    # INVARIANT: Tolerance enforcement is consistent
    if prob_sum < (1.0 - tolerance) or prob_sum > (1.0 + tolerance):
        assert result.type == "error"
    elif abs(prob_sum - 1.0) < 1e-10:  # Essentially 1.0 (floating point precision)
        assert result.type == "info"
    else:
        # Within tolerance but not exact
        assert result.type in ["warning", "info"]
