"""
tests/unit/test_dcf_fade_integration.py

INTEGRATION TEST FOR DCF LIBRARY FADE TRANSITION
================================================
Role: Verifies that DCFLibrary correctly uses the fade transition logic
      with high_growth_period parameter.
Coverage: Integration between DCFLibrary and flow_projector module.
Standards: pytest + NumPy docstrings (English)
"""

from unittest.mock import Mock

import pytest

from src.valuation.library.dcf import DCFLibrary


def test_dcf_library_simple_with_fade_transition():
    """
    Test that DCFLibrary.project_flows_simple respects high_growth_period.

    Verifies the integration between DCFLibrary and the centralized
    project_flows function.
    """
    # Create mock parameters with high_growth_period
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.12  # 12% high growth
    strategy.projection_years = 10
    strategy.high_growth_period = 6  # 6 years high, then fade

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.02  # 2% terminal
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    base_flow = 1_000_000

    # Execute projection
    flows, step = DCFLibrary.project_flows_simple(base_flow, params)

    # Verify we get 10 years of flows
    assert len(flows) == 10

    # Verify first 6 years have constant 12% growth
    for i in range(6):
        if i == 0:
            expected = base_flow * 1.12
        else:
            expected = flows[i - 1] * 1.12
        assert flows[i] == pytest.approx(expected, rel=1e-9)

    # Verify years 7-10 have declining growth rates (fade)
    growth_rates = []
    for i in range(6, 10):
        g = (flows[i] / flows[i - 1]) - 1
        growth_rates.append(g)

    # Growth rates should be strictly decreasing during fade
    for i in range(1, len(growth_rates)):
        assert growth_rates[i] < growth_rates[i - 1]

    # Last growth rate should equal terminal rate
    assert growth_rates[-1] == pytest.approx(0.02, abs=1e-9)

    # Verify Glass Box variables include n_high
    assert "n_high" in step.variables_map
    assert step.variables_map["n_high"].value == 6.0


def test_dcf_library_simple_without_fade_backward_compatibility():
    """
    Test backward compatibility when high_growth_period is not set.

    Should default to no fade (constant growth until terminal value).
    """
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.10
    strategy.projection_years = 5
    # high_growth_period not set (None)

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.02
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    base_flow = 1_000_000

    flows, step = DCFLibrary.project_flows_simple(base_flow, params)

    assert len(flows) == 5

    # With default behavior (high_growth_period = years),
    # all years should have constant high growth
    for i in range(5):
        if i == 0:
            expected = base_flow * 1.10
        else:
            expected = flows[i - 1] * 1.10
        assert flows[i] == pytest.approx(expected, rel=1e-9)

    # Verify n_high defaults to n
    assert step.variables_map["n_high"].value == 5.0


def test_dcf_library_revenue_model_with_fade():
    """
    Test that revenue model projection respects high_growth_period.
    """
    params = Mock()
    strategy = Mock()
    strategy.revenue_growth_rate = 0.15  # 15% revenue growth
    strategy.projection_years = 8
    strategy.high_growth_period = 5  # 5 years high, then fade
    strategy.manual_growth_vector = None  # No manual vector

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    base_revenue = 10_000_000
    current_margin = 0.05
    target_margin = 0.15

    revenues, margins, fcfs, step = DCFLibrary.project_flows_revenue_model(
        base_revenue, current_margin, target_margin, params
    )

    # Verify 8 years of projections
    assert len(revenues) == 8
    assert len(margins) == 8
    assert len(fcfs) == 8

    # Check first 5 years have constant 15% revenue growth
    current_rev = base_revenue
    for i in range(5):
        current_rev *= 1.15
        assert revenues[i] == pytest.approx(current_rev, rel=1e-9)

    # Check years 6-8 have declining growth rates
    growth_rates = []
    for i in range(5, 8):
        g = (revenues[i] / revenues[i - 1]) - 1
        growth_rates.append(g)

    # Growth should decline
    for i in range(1, len(growth_rates)):
        assert growth_rates[i] < growth_rates[i - 1]

    # Last growth should equal terminal
    assert growth_rates[-1] == pytest.approx(0.03, abs=1e-9)


def test_dcf_library_revenue_model_manual_vector_precedence():
    """
    Test that manual growth vector takes precedence over fade.

    When a manual vector is provided, it should be used instead
    of the automatic fade transition logic.
    """
    params = Mock()
    strategy = Mock()
    strategy.revenue_growth_rate = 0.15  # Would be used if no manual vector
    strategy.projection_years = 5
    strategy.high_growth_period = 3  # Would create fade if no manual vector
    strategy.manual_growth_vector = [0.20, 0.18, 0.16, 0.14, 0.12]  # Manual override

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    base_revenue = 10_000_000
    current_margin = 0.05
    target_margin = 0.15

    revenues, margins, fcfs, step = DCFLibrary.project_flows_revenue_model(
        base_revenue, current_margin, target_margin, params
    )

    # Verify manual vector is used exactly as specified
    manual_vector = [0.20, 0.18, 0.16, 0.14, 0.12]
    current_rev = base_revenue
    for i, g in enumerate(manual_vector):
        current_rev *= 1 + g
        assert revenues[i] == pytest.approx(current_rev, rel=1e-9)


def test_dcf_library_simple_with_ddm_parameters():
    """
    Test that fade works with DDM parameters (growth_rate instead of growth_rate_p1).
    """
    params = Mock()
    strategy = Mock(spec=["growth_rate", "projection_years", "high_growth_period", "terminal_value"])
    # DDM uses 'growth_rate' instead of 'growth_rate_p1'
    # By using spec, growth_rate_p1 won't exist at all
    strategy.growth_rate = 0.08
    strategy.projection_years = 7
    strategy.high_growth_period = 4

    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.025
    strategy.terminal_value = terminal_value

    params.strategy = strategy

    base_flow = 500_000

    flows, step = DCFLibrary.project_flows_simple(base_flow, params)

    assert len(flows) == 7

    # First 4 years at 8%
    for i in range(4):
        if i == 0:
            expected = base_flow * 1.08
        else:
            expected = flows[i - 1] * 1.08
        assert flows[i] == pytest.approx(expected, rel=1e-9)

    # Years 5-7 should fade to 2.5%
    final_g = (flows[-1] / flows[-2]) - 1
    assert final_g == pytest.approx(0.025, abs=1e-9)
