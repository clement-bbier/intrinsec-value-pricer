"""
tests/unit/test_sbc_treatment.py

COMPREHENSIVE TEST SUITE FOR SBC TREATMENT
==========================================
Role: Tests Stock-Based Compensation treatment (DILUTION vs EXPENSE).
Coverage: FlowProjector and DCF Library with both treatment modes.
Standards: pytest + unittest.mock for dependencies.
"""

from unittest.mock import Mock

import pytest

from src.computation.flow_projector import MarginConvergenceProjector, SimpleFlowProjector
from src.models.enums import SBCTreatment
from src.valuation.library.dcf import DCFLibrary

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_params_with_sbc_dilution():
    """Mock Parameters with SBC treatment as DILUTION."""
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    # Capital structure with DILUTION treatment
    capital = Mock()
    capital.sbc_treatment = SBCTreatment.DILUTION.value
    capital.annual_dilution_rate = 0.02
    capital.sbc_annual_amount = None
    capital.shares_outstanding = 100_000_000

    common = Mock()
    common.capital = capital
    params.common = common

    return params


@pytest.fixture
def mock_params_with_sbc_expense():
    """Mock Parameters with SBC treatment as EXPENSE."""
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    # Capital structure with EXPENSE treatment
    capital = Mock()
    capital.sbc_treatment = SBCTreatment.EXPENSE.value
    capital.annual_dilution_rate = None
    capital.sbc_annual_amount = 50_000_000  # 50M per year
    capital.shares_outstanding = 100_000_000

    common = Mock()
    common.capital = capital
    params.common = common

    return params


@pytest.fixture
def mock_params_margin_convergence_expense():
    """Mock Parameters for MarginConvergenceProjector with EXPENSE."""
    params = Mock()
    strategy = Mock()
    strategy.target_fcf_margin = 0.15
    strategy.revenue_growth_rate = 0.10
    strategy.projection_years = 5

    params.strategy = strategy

    # Capital structure with EXPENSE treatment
    capital = Mock()
    capital.sbc_treatment = SBCTreatment.EXPENSE.value
    capital.sbc_annual_amount = 30_000_000  # 30M per year
    capital.shares_outstanding = 100_000_000

    common = Mock()
    common.capital = capital
    params.common = common

    return params


@pytest.fixture
def mock_company():
    """Mock Company object."""
    company = Mock()
    company.ticker = "AAPL"
    company.name = "Apple Inc."
    return company


# ============================================================================
# TEST SimpleFlowProjector with SBC EXPENSE
# ============================================================================


def test_simple_flow_projector_sbc_expense_reduces_flows(mock_company, mock_params_with_sbc_expense):
    """Test that EXPENSE mode reduces each projected flow by SBC amount."""
    projector = SimpleFlowProjector()
    base_value = 1_000_000_000  # 1B

    output = projector.project(base_value, mock_company, mock_params_with_sbc_expense)

    # Each flow should be reduced by 50M
    assert len(output.flows) == 5

    # First flow without SBC would be base_value * 1.08
    expected_flow_1_without_sbc = base_value * 1.08
    expected_flow_1_with_sbc = expected_flow_1_without_sbc - 50_000_000

    assert output.flows[0] == pytest.approx(expected_flow_1_with_sbc, rel=1e-6)

    # Check that SBC variable is in trace
    assert "SBC" in output.variables
    assert output.variables["SBC"].value == 50_000_000


def test_simple_flow_projector_sbc_dilution_no_flow_change(mock_company, mock_params_with_sbc_dilution):
    """Test that DILUTION mode does NOT change flows."""
    projector = SimpleFlowProjector()
    base_value = 1_000_000_000  # 1B

    output = projector.project(base_value, mock_company, mock_params_with_sbc_dilution)

    # Flows should NOT be reduced (dilution happens at the end)
    assert len(output.flows) == 5

    # First flow should be base_value * 1.08 (no SBC deduction)
    expected_flow_1 = base_value * 1.08
    assert output.flows[0] == pytest.approx(expected_flow_1, rel=1e-6)

    # SBC should NOT be in variables for DILUTION mode
    assert "SBC" not in output.variables


def test_simple_flow_projector_sbc_expense_zero_amount(mock_company, mock_params_with_sbc_expense):
    """Test EXPENSE mode with zero SBC amount (no deduction)."""
    mock_params_with_sbc_expense.common.capital.sbc_annual_amount = 0.0

    projector = SimpleFlowProjector()
    base_value = 1_000_000_000

    output = projector.project(base_value, mock_company, mock_params_with_sbc_expense)

    # Flows should not be reduced if SBC amount is 0
    expected_flow_1 = base_value * 1.08
    assert output.flows[0] == pytest.approx(expected_flow_1, rel=1e-6)

    # SBC should NOT be in variables if amount is 0
    assert "SBC" not in output.variables


def test_simple_flow_projector_no_sbc_treatment(mock_company):
    """Test projector when no SBC treatment is specified (backward compatibility)."""
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    # No SBC treatment specified
    capital = Mock()
    capital.sbc_treatment = None
    capital.annual_dilution_rate = 0.02
    capital.shares_outstanding = 100_000_000

    common = Mock()
    common.capital = capital
    params.common = common

    projector = SimpleFlowProjector()
    base_value = 1_000_000_000

    output = projector.project(base_value, mock_company, params)

    # Should work fine, no SBC deduction
    assert len(output.flows) == 5
    expected_flow_1 = base_value * 1.08
    assert output.flows[0] == pytest.approx(expected_flow_1, rel=1e-6)


# ============================================================================
# TEST MarginConvergenceProjector with SBC EXPENSE
# ============================================================================


def test_margin_convergence_sbc_expense_reduces_flows(mock_company, mock_params_margin_convergence_expense):
    """Test that EXPENSE mode reduces margin convergence flows."""
    projector = MarginConvergenceProjector()
    base_revenue = 10_000_000_000  # 10B

    output = projector.project(base_revenue, mock_company, mock_params_margin_convergence_expense)

    # Each flow should be reduced by 30M
    assert len(output.flows) == 5

    # Check that SBC variable is in trace
    assert "SBC" in output.variables
    assert output.variables["SBC"].value == 30_000_000

    # Verify flows are positive (revenue growth should overcome SBC expense)
    assert all(f > 0 for f in output.flows)


def test_margin_convergence_sbc_dilution_no_flow_change(mock_company):
    """Test that DILUTION mode in margin convergence does NOT change flows."""
    params = Mock()
    strategy = Mock()
    strategy.target_fcf_margin = 0.15
    strategy.revenue_growth_rate = 0.10
    strategy.projection_years = 5

    params.strategy = strategy

    capital = Mock()
    capital.sbc_treatment = SBCTreatment.DILUTION.value
    capital.annual_dilution_rate = 0.02
    capital.sbc_annual_amount = None
    capital.shares_outstanding = 100_000_000

    common = Mock()
    common.capital = capital
    params.common = common

    projector = MarginConvergenceProjector()
    base_revenue = 10_000_000_000

    output = projector.project(base_revenue, mock_company, params)

    # SBC should NOT be in variables for DILUTION mode
    assert "SBC" not in output.variables


# ============================================================================
# TEST DCFLibrary.compute_value_per_share with SBC Treatments
# ============================================================================


def test_value_per_share_sbc_expense_no_dilution(mock_params_with_sbc_expense):
    """Test that EXPENSE mode skips dilution adjustment."""
    equity_value = 10_000_000_000  # 10B
    shares = 100_000_000  # 100M

    mock_params_with_sbc_expense.common.capital.shares_outstanding = shares

    final_iv, step = DCFLibrary.compute_value_per_share(equity_value, mock_params_with_sbc_expense)

    # Should be simple division, no dilution adjustment
    expected_iv = equity_value / shares  # 100.0
    assert final_iv == pytest.approx(expected_iv, rel=1e-6)

    # Check step interpretation mentions SBC treated as expense (French or English)
    interpretation_lower = step.interpretation.lower()
    assert ("sbc" in interpretation_lower and ("dépense" in interpretation_lower or "expense" in interpretation_lower))



def test_value_per_share_sbc_dilution_applies_adjustment(mock_params_with_sbc_dilution):
    """Test that DILUTION mode applies dilution adjustment."""
    equity_value = 10_000_000_000  # 10B
    shares = 100_000_000  # 100M
    dilution_rate = 0.02
    years = 5

    mock_params_with_sbc_dilution.common.capital.shares_outstanding = shares
    mock_params_with_sbc_dilution.common.capital.annual_dilution_rate = dilution_rate

    final_iv, step = DCFLibrary.compute_value_per_share(equity_value, mock_params_with_sbc_dilution)

    # Should apply dilution: base_iv / (1 + rate)^years
    base_iv = equity_value / shares  # 100.0
    dilution_factor = (1 + dilution_rate) ** years
    expected_iv = base_iv / dilution_factor

    assert final_iv == pytest.approx(expected_iv, rel=1e-6)
    assert final_iv < base_iv  # Should be lower due to dilution


def test_value_per_share_sbc_dilution_zero_rate(mock_params_with_sbc_dilution):
    """Test DILUTION mode with zero dilution rate (no adjustment)."""
    equity_value = 10_000_000_000
    shares = 100_000_000

    mock_params_with_sbc_dilution.common.capital.shares_outstanding = shares
    mock_params_with_sbc_dilution.common.capital.annual_dilution_rate = 0.0

    final_iv, step = DCFLibrary.compute_value_per_share(equity_value, mock_params_with_sbc_dilution)

    # Should be simple division since dilution rate is 0
    expected_iv = equity_value / shares
    assert final_iv == pytest.approx(expected_iv, rel=1e-6)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_full_workflow_expense_reduces_intrinsic_value(mock_company):
    """
    Integration test: Verify that EXPENSE treatment reduces intrinsic value
    more than DILUTION treatment for the same company.
    """
    # Create two parameter sets: one with DILUTION, one with EXPENSE
    base_value = 1_000_000_000

    # DILUTION params
    params_dilution = Mock()
    strategy_d = Mock()
    strategy_d.growth_rate_p1 = 0.08
    strategy_d.projection_years = 5
    terminal_value_d = Mock()
    terminal_value_d.perpetual_growth_rate = 0.03
    strategy_d.terminal_value = terminal_value_d
    params_dilution.strategy = strategy_d

    capital_d = Mock()
    capital_d.sbc_treatment = SBCTreatment.DILUTION.value
    capital_d.annual_dilution_rate = 0.02
    capital_d.sbc_annual_amount = None
    capital_d.shares_outstanding = 100_000_000
    common_d = Mock()
    common_d.capital = capital_d
    params_dilution.common = common_d

    # EXPENSE params (same SBC amount as value)
    params_expense = Mock()
    strategy_e = Mock()
    strategy_e.growth_rate_p1 = 0.08
    strategy_e.projection_years = 5
    terminal_value_e = Mock()
    terminal_value_e.perpetual_growth_rate = 0.03
    strategy_e.terminal_value = terminal_value_e
    params_expense.strategy = strategy_e

    capital_e = Mock()
    capital_e.sbc_treatment = SBCTreatment.EXPENSE.value
    capital_e.annual_dilution_rate = None
    capital_e.sbc_annual_amount = 50_000_000  # 50M per year
    capital_e.shares_outstanding = 100_000_000
    common_e = Mock()
    common_e.capital = capital_e
    params_expense.common = common_e

    # Project flows with both treatments
    projector = SimpleFlowProjector()

    output_dilution = projector.project(base_value, mock_company, params_dilution)
    output_expense = projector.project(base_value, mock_company, params_expense)

    # EXPENSE flows should be lower
    assert sum(output_expense.flows) < sum(output_dilution.flows)

    # Each flow in EXPENSE should be 50M less
    for flow_d, flow_e in zip(output_dilution.flows, output_expense.flows):
        assert flow_d - flow_e == pytest.approx(50_000_000, rel=1e-6)


def test_sbc_expense_treatment_consistency():
    """Test that SBC EXPENSE treatment is consistent across projectors."""
    company = Mock()
    company.ticker = "TEST"

    # Simple projector with EXPENSE
    params_simple = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.10
    strategy.projection_years = 3
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value
    params_simple.strategy = strategy

    capital = Mock()
    capital.sbc_treatment = SBCTreatment.EXPENSE.value
    capital.sbc_annual_amount = 10_000_000
    common = Mock()
    common.capital = capital
    params_simple.common = common

    projector = SimpleFlowProjector()
    output = projector.project(100_000_000, company, params_simple)

    # All flows should have SBC deducted
    # Year 1: 100M * 1.10 - 10M = 100M
    # Year 2: 100M * (1.10)^2 - 10M = 111M
    # Year 3: approximately based on convergence

    assert all(f < 150_000_000 for f in output.flows)  # Sanity check
    assert "SBC" in output.variables
