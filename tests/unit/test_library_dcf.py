"""
tests/unit/test_library_dcf.py

COMPREHENSIVE TEST SUITE FOR DCF LIBRARY
========================================
Role: Tests all methods in src/valuation/library/dcf.py
Coverage Target: ≥90% line coverage
Standards: pytest + unittest.mock for dependencies
"""

from unittest.mock import Mock

import pytest

from src.config.constants import ModelDefaults
from src.models.enums import TerminalValueMethod
from src.models.parameters.base_parameter import Parameters
from src.valuation.library.dcf import DCFLibrary

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_params_fcff():
    """Mock Parameters object for FCFF with terminal_value and projection_years."""
    params = Mock(spec=Parameters)

    # Mock strategy with all required attributes
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5

    # Mock terminal value params
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    terminal_value.method = TerminalValueMethod.GORDON_GROWTH
    terminal_value.exit_multiple = 10.0
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    # Mock common params for capital structure
    capital = Mock()
    capital.shares_outstanding = 100_000_000
    capital.annual_dilution_rate = 0.02
    common = Mock()
    common.capital = capital
    params.common = common

    return params


@pytest.fixture
def mock_params_ddm():
    """Mock Parameters for DDM (uses growth_rate instead of growth_rate_p1)."""
    params = Mock(spec=Parameters)
    strategy = Mock(spec=["growth_rate", "projection_years", "terminal_value"])
    strategy.growth_rate = 0.06
    strategy.projection_years = 5

    terminal_value = Mock(spec=["perpetual_growth_rate"])
    terminal_value.perpetual_growth_rate = 0.025
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    capital = Mock()
    capital.shares_outstanding = 50_000_000
    capital.annual_dilution_rate = 0.0
    common = Mock()
    common.capital = capital
    params.common = common

    return params


@pytest.fixture
def mock_params_revenue_model():
    """Mock Parameters for Revenue-based projection."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.revenue_growth_rate = 0.10
    strategy.projection_years = 5
    strategy.manual_growth_vector = None

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value

    params.strategy = strategy
    params.common = Mock()

    return params


# ============================================================================
# TEST project_flows_simple
# ============================================================================


def test_project_flows_simple_fcff_standard(mock_params_fcff):
    """Test simple projection with FCFF standard parameters."""
    base_flow = 1_000_000
    flows, step = DCFLibrary.project_flows_simple(base_flow, mock_params_fcff)

    # Should return 5 flows
    assert len(flows) == 5
    assert all(f > 0 for f in flows)

    # Flows should be increasing (positive growth)
    assert flows[0] < flows[-1]

    # Check step structure
    assert step.step_key == "FCF_PROJ"
    assert step.result > 0
    assert "FCF_0" in step.variables_map
    assert "g_start" in step.variables_map
    assert "g_term" in step.variables_map
    assert step.variables_map["g_start"].value == 0.08


def test_project_flows_simple_ddm_fallback(mock_params_ddm):
    """Test simple projection with DDM parameters (fallback to growth_rate)."""
    base_flow = 50.0
    flows, step = DCFLibrary.project_flows_simple(base_flow, mock_params_ddm)

    assert len(flows) == 5
    assert flows[0] > base_flow  # First year should be higher than base
    assert step.variables_map["g_start"].value == 0.06


def test_project_flows_simple_single_year(mock_params_fcff):
    """Test projection with only 1 year (no fade-down)."""
    mock_params_fcff.strategy.projection_years = 1

    base_flow = 1_000_000
    flows, step = DCFLibrary.project_flows_simple(base_flow, mock_params_fcff)

    assert len(flows) == 1
    # Should use g_start directly (no interpolation)
    expected = base_flow * 1.08
    assert flows[0] == pytest.approx(expected, rel=1e-6)


def test_project_flows_simple_convergence(mock_params_fcff):
    """Test that growth converges from g_start to g_term."""
    base_flow = 1_000_000
    flows, _ = DCFLibrary.project_flows_simple(base_flow, mock_params_fcff)

    # Calculate implied growth rates
    growth_rates = [(flows[i] / flows[i - 1]) - 1 for i in range(1, len(flows))]

    # Growth should be decreasing (convergence)
    for i in range(len(growth_rates) - 1):
        assert growth_rates[i] >= growth_rates[i + 1] - 1e-6


def test_project_flows_simple_no_params_defaults():
    """Test projection with missing parameters uses defaults."""
    params = Mock(spec=Parameters)
    strategy = Mock(spec=["terminal_value"])
    # No growth_rate_p1, growth_rate, or projection_years - should use defaults
    terminal_value = Mock(spec=["perpetual_growth_rate"])
    terminal_value.perpetual_growth_rate = None  # Explicitly set to None to trigger default
    strategy.terminal_value = terminal_value
    params.strategy = strategy
    params.common = Mock()

    base_flow = 100.0
    flows, step = DCFLibrary.project_flows_simple(base_flow, params)

    # Should use ModelDefaults
    assert len(flows) == ModelDefaults.DEFAULT_PROJECTION_YEARS


# ============================================================================
# TEST project_flows_manual
# ============================================================================


def test_project_flows_manual_basic():
    """Test manual projection with explicit growth vector."""
    base_flow = 1_000_000
    growth_vector = [0.10, 0.08, 0.06, 0.04, 0.03]

    flows, step = DCFLibrary.project_flows_manual(base_flow, growth_vector)

    assert len(flows) == 5

    # Verify each flow matches expected calculation
    expected = [
        base_flow * 1.10,
        base_flow * 1.10 * 1.08,
        base_flow * 1.10 * 1.08 * 1.06,
        base_flow * 1.10 * 1.08 * 1.06 * 1.04,
        base_flow * 1.10 * 1.08 * 1.06 * 1.04 * 1.03,
    ]

    for i in range(5):
        assert flows[i] == pytest.approx(expected[i], rel=1e-6)

    # Check step
    assert step.step_key == "FCF_PROJ_MANUAL"
    assert "g_avg" in step.variables_map
    assert step.variables_map["g_avg"].value == pytest.approx(0.062, rel=1e-3)


def test_project_flows_manual_empty_vector():
    """Test manual projection with empty growth vector."""
    base_flow = 1_000_000
    growth_vector = []

    flows, step = DCFLibrary.project_flows_manual(base_flow, growth_vector)

    assert len(flows) == 0
    assert step.variables_map["g_avg"].value == 0.0


def test_project_flows_manual_negative_growth():
    """Test manual projection with negative growth rates."""
    base_flow = 1_000_000
    growth_vector = [0.05, 0.02, -0.03, -0.05, -0.02]

    flows, step = DCFLibrary.project_flows_manual(base_flow, growth_vector)

    assert len(flows) == 5
    # Some flows should decrease
    assert flows[2] < flows[1]
    assert flows[3] < flows[2]


# ============================================================================
# TEST project_flows_revenue_model
# ============================================================================


def test_project_flows_revenue_model_basic(mock_params_revenue_model):
    """Test revenue-based projection with margin convergence."""
    base_revenue = 10_000_000
    current_margin = 0.05
    target_margin = 0.15

    fcfs, revenues, margins, step = DCFLibrary.project_flows_revenue_model(
        base_revenue, current_margin, target_margin, mock_params_revenue_model
    )

    assert len(fcfs) == 5
    assert len(revenues) == 5
    assert len(margins) == 5

    # Revenues should grow
    assert revenues[0] < revenues[-1]

    # Margins should converge from current to target
    assert margins[0] > current_margin
    assert margins[-1] == pytest.approx(target_margin, rel=1e-6)

    # FCFs = Revenue * Margin
    for i in range(5):
        assert fcfs[i] == pytest.approx(revenues[i] * margins[i], rel=1e-6)

    # Check step
    assert step.step_key == "REV_MARGIN_CONV"
    assert "Rev_0" in step.variables_map
    assert "M_target" in step.variables_map


def test_project_flows_revenue_model_with_manual_vector(mock_params_revenue_model):
    """Test revenue model with manual growth vector override."""
    mock_params_revenue_model.strategy.manual_growth_vector = [0.15, 0.12, 0.10, 0.08, 0.05]

    base_revenue = 5_000_000
    current_margin = 0.10
    target_margin = 0.12

    fcfs, revenues, margins, step = DCFLibrary.project_flows_revenue_model(
        base_revenue, current_margin, target_margin, mock_params_revenue_model
    )

    # Check first year uses manual vector
    expected_rev_y1 = base_revenue * 1.15
    assert revenues[0] == pytest.approx(expected_rev_y1, rel=1e-6)


def test_project_flows_revenue_model_zero_years(mock_params_revenue_model):
    """Test revenue model with zero projection years (defaults to 5)."""
    mock_params_revenue_model.strategy.projection_years = 0  # Will default to 5 due to 'or' fallback

    base_revenue = 1_000_000

    fcfs, revenues, margins, step = DCFLibrary.project_flows_revenue_model(
        base_revenue, 0.10, 0.15, mock_params_revenue_model
    )

    # Code treats 0 as falsy and defaults to 5 years
    assert len(fcfs) == 5
    assert len(revenues) == 5
    assert len(margins) == 5


# ============================================================================
# TEST compute_terminal_value
# ============================================================================


def test_compute_terminal_value_gordon(mock_params_fcff):
    """Test terminal value using Gordon Growth method."""
    final_flow = 1_500_000
    discount_rate = 0.10

    tv, step = DCFLibrary.compute_terminal_value(final_flow, discount_rate, mock_params_fcff)

    # TV = FCF * (1+g) / (r - g)
    # TV = 1,500,000 * 1.03 / (0.10 - 0.03)
    expected_tv = 1_500_000 * 1.03 / 0.07
    assert tv == pytest.approx(expected_tv, rel=1e-6)

    # Check step
    assert step.step_key == "TV_GORDON"
    assert "g_perp" in step.variables_map
    assert step.variables_map["g_perp"].value == 0.03


def test_compute_terminal_value_exit_multiple(mock_params_fcff):
    """Test terminal value using Exit Multiple method."""
    mock_params_fcff.strategy.terminal_value.method = TerminalValueMethod.EXIT_MULTIPLE

    final_flow = 1_500_000
    discount_rate = 0.10

    tv, step = DCFLibrary.compute_terminal_value(final_flow, discount_rate, mock_params_fcff)

    # TV = FCF * Multiple
    expected_tv = 1_500_000 * 10.0
    assert tv == pytest.approx(expected_tv, rel=1e-6)

    # Check step
    assert step.step_key == "TV_MULTIPLE"
    assert "M" in step.variables_map
    assert step.variables_map["M"].value == 10.0


def test_compute_terminal_value_edge_case_small_spread():
    """Test terminal value with small r-g spread."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    tv_params = Mock()
    tv_params.method = TerminalValueMethod.GORDON_GROWTH
    tv_params.perpetual_growth_rate = 0.095  # Very close to discount rate
    strategy.terminal_value = tv_params
    params.strategy = strategy

    final_flow = 1_000_000
    discount_rate = 0.10

    tv, step = DCFLibrary.compute_terminal_value(final_flow, discount_rate, params)

    # Should still calculate without error
    assert tv > 0
    assert tv > final_flow * 10  # Should be large with small spread


# ============================================================================
# TEST compute_discounting
# ============================================================================


def test_compute_discounting_basic():
    """Test NPV calculation of flows and terminal value."""
    flows = [100, 110, 120, 130, 140]
    terminal_value = 2000
    discount_rate = 0.10

    total_ev, step = DCFLibrary.compute_discounting(flows, terminal_value, discount_rate)

    # Manual calculation
    factors = [(1 / (1 + discount_rate) ** t) for t in range(1, 6)]
    pv_flows = sum(f * d for f, d in zip(flows, factors))
    pv_tv = terminal_value * factors[-1]
    expected_ev = pv_flows + pv_tv

    assert total_ev == pytest.approx(expected_ev, rel=1e-6)

    # Check step
    assert step.step_key == "NPV_CALC"
    assert "ΣPV" in step.variables_map
    assert "PV_TV" in step.variables_map
    assert step.variables_map["r"].value == discount_rate


def test_compute_discounting_zero_discount_rate():
    """Test discounting with zero discount rate (no time value)."""
    flows = [100, 100, 100]
    terminal_value = 1000
    discount_rate = 0.0

    total_ev, step = DCFLibrary.compute_discounting(flows, terminal_value, discount_rate)

    # With 0% discount, PV = FV
    expected_ev = sum(flows) + terminal_value
    assert total_ev == pytest.approx(expected_ev, rel=1e-6)


def test_compute_discounting_high_discount_rate():
    """Test discounting with high discount rate."""
    flows = [100, 100, 100, 100, 100]
    terminal_value = 10_000
    discount_rate = 0.50  # 50%!

    total_ev, step = DCFLibrary.compute_discounting(flows, terminal_value, discount_rate)

    # TV should be heavily discounted
    assert total_ev < sum(flows) + 1000  # TV contribution should be minimal


def test_compute_discounting_single_period():
    """Test discounting with single flow period."""
    flows = [1000]
    terminal_value = 5000
    discount_rate = 0.08

    total_ev, step = DCFLibrary.compute_discounting(flows, terminal_value, discount_rate)

    expected = (1000 + 5000) / 1.08
    assert total_ev == pytest.approx(expected, rel=1e-6)


# ============================================================================
# TEST compute_value_per_share
# ============================================================================


def test_compute_value_per_share_no_dilution(mock_params_fcff):
    """Test per-share calculation without dilution."""
    mock_params_fcff.common.capital.annual_dilution_rate = 0.0

    equity_value = 10_000_000_000  # $10B

    final_iv, step = DCFLibrary.compute_value_per_share(equity_value, mock_params_fcff)

    # IV = Equity / Shares = 10B / 100M = 100
    expected_iv = 10_000_000_000 / 100_000_000
    assert final_iv == pytest.approx(expected_iv, rel=1e-6)

    # Check step
    assert step.step_key == "VALUE_PER_SHARE"
    assert "Shares" in step.variables_map


def test_compute_value_per_share_with_dilution(mock_params_fcff):
    """Test per-share calculation with SBC dilution."""
    equity_value = 10_000_000_000

    final_iv, step = DCFLibrary.compute_value_per_share(equity_value, mock_params_fcff)

    # Base IV = 10B / 100M = 100
    # Dilution factor = (1 + 0.02)^5 = 1.10408
    # Final IV = 100 / 1.10408
    base_iv = 10_000_000_000 / 100_000_000
    dilution_factor = (1 + 0.02) ** 5
    expected_iv = base_iv / dilution_factor

    assert final_iv == pytest.approx(expected_iv, rel=1e-4)

    # Check step includes dilution info
    assert step.step_key == "VALUE_PER_SHARE_DILUTED"
    assert "Dilution" in step.variables_map


def test_compute_value_per_share_high_dilution():
    """Test per-share with aggressive dilution rate."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.projection_years = 10
    params.strategy = strategy

    capital = Mock()
    capital.shares_outstanding = 1_000_000
    capital.annual_dilution_rate = 0.10  # 10% per year!
    common = Mock()
    common.capital = capital
    params.common = common

    equity_value = 100_000_000

    final_iv, step = DCFLibrary.compute_value_per_share(equity_value, params)

    base_iv = equity_value / 1_000_000
    dilution_factor = (1.10) ** 10
    expected_iv = base_iv / dilution_factor

    assert final_iv == pytest.approx(expected_iv, rel=1e-4)
    # Dilution should significantly reduce value
    assert final_iv < base_iv * 0.5


def test_compute_value_per_share_default_shares():
    """Test per-share when shares_outstanding is None."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.projection_years = 5
    params.strategy = strategy

    capital = Mock()
    capital.shares_outstanding = None  # Trigger default
    capital.annual_dilution_rate = 0.0
    common = Mock()
    common.capital = capital
    params.common = common

    equity_value = 1_000_000

    final_iv, step = DCFLibrary.compute_value_per_share(equity_value, params)

    # Should use ModelDefaults.DEFAULT_SHARES_OUTSTANDING
    expected_iv = equity_value / ModelDefaults.DEFAULT_SHARES_OUTSTANDING
    assert final_iv == pytest.approx(expected_iv, rel=1e-6)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_dcf_full_workflow(mock_params_fcff):
    """Integration test: Full DCF workflow."""
    # 1. Project flows
    base_flow = 1_000_000
    flows, proj_step = DCFLibrary.project_flows_simple(base_flow, mock_params_fcff)
    assert len(flows) == 5

    # 2. Calculate terminal value
    final_flow = flows[-1]
    discount_rate = 0.10
    tv, tv_step = DCFLibrary.compute_terminal_value(final_flow, discount_rate, mock_params_fcff)
    assert tv > 0

    # 3. Discount everything
    total_ev, disc_step = DCFLibrary.compute_discounting(flows, tv, discount_rate)
    assert total_ev > 0

    # 4. Calculate per-share value
    final_iv, iv_step = DCFLibrary.compute_value_per_share(total_ev, mock_params_fcff)
    assert final_iv > 0

    # All steps should have valid structure
    for step in [proj_step, tv_step, disc_step, iv_step]:
        assert step.step_key
        assert step.result >= 0
        assert len(step.variables_map) > 0


def test_dcf_revenue_model_workflow(mock_params_revenue_model):
    """Integration test: Revenue model workflow."""
    base_revenue = 50_000_000
    current_margin = 0.08
    target_margin = 0.15

    # Project using revenue model
    fcfs, revenues, margins, step = DCFLibrary.project_flows_revenue_model(
        base_revenue, current_margin, target_margin, mock_params_revenue_model
    )

    assert len(fcfs) == 5
    assert all(f > 0 for f in fcfs)

    # Verify consistency
    for i in range(5):
        expected_fcf = revenues[i] * margins[i]
        assert fcfs[i] == pytest.approx(expected_fcf, rel=1e-6)
