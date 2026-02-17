"""
tests/unit/test_fade_transition.py

COMPREHENSIVE TEST SUITE FOR FADE TRANSITION FEATURE
====================================================
Role: Tests the fade transition between high growth and perpetual growth.
Coverage Target: ≥95% line coverage for fade transition logic
Standards: pytest + NumPy docstrings (English)
"""

from unittest.mock import Mock

import pytest

from src.computation.flow_projector import SimpleFlowProjector, project_flows


# ============================================================================
# TEST project_flows with fade transition
# ============================================================================


def test_fade_transition_linear_interpolation():
    """
    Test that fade transition uses correct linear interpolation.

    The growth rate should decrease linearly from g_start to g_term
    during the fade period.
    """
    base_flow = 1_000_000
    years = 10
    g_start = 0.15  # 15% high growth
    g_term = 0.03  # 3% terminal growth
    high_growth_years = 5  # 5 years high growth, then 5 years fade

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # First 5 years should use g_start (15%)
    for i in range(5):
        if i == 0:
            expected = base_flow * (1 + g_start)
        else:
            expected = flows[i - 1] * (1 + g_start)
        assert flows[i] == pytest.approx(expected, rel=1e-9)

    # Years 6-10 should fade linearly
    # Year 6: α = 1/5 = 0.2 → g = 0.15 * 0.8 + 0.03 * 0.2 = 0.126
    # Year 7: α = 2/5 = 0.4 → g = 0.15 * 0.6 + 0.03 * 0.4 = 0.102
    # Year 8: α = 3/5 = 0.6 → g = 0.15 * 0.4 + 0.03 * 0.6 = 0.078
    # Year 9: α = 4/5 = 0.8 → g = 0.15 * 0.2 + 0.03 * 0.8 = 0.054
    # Year 10: α = 5/5 = 1.0 → g = 0.15 * 0.0 + 0.03 * 1.0 = 0.030

    expected_growth_rates = [0.126, 0.102, 0.078, 0.054, 0.030]
    for i, expected_g in enumerate(expected_growth_rates, start=5):
        actual_g = (flows[i] / flows[i - 1]) - 1
        assert actual_g == pytest.approx(expected_g, abs=1e-9)


def test_fade_transition_no_fade_when_high_growth_equals_years():
    """
    Test that no fade occurs when high_growth_years equals projection years.
    
    This is the default behavior for backward compatibility.
    """
    base_flow = 1_000_000
    years = 10
    g_start = 0.12
    g_term = 0.02
    high_growth_years = 10  # Same as years, no fade

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # All years should use g_start
    for i in range(years):
        if i == 0:
            expected = base_flow * (1 + g_start)
        else:
            expected = flows[i - 1] * (1 + g_start)
        assert flows[i] == pytest.approx(expected, rel=1e-9)


def test_fade_transition_immediate_fade_from_year_one():
    """
    Test fade starting immediately from year 1 when high_growth_years = 0.
    """
    base_flow = 1_000_000
    years = 5
    g_start = 0.20
    g_term = 0.02
    high_growth_years = 0  # Immediate fade from year 1

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # Year 1: α = 1/5 = 0.2 → g = 0.20 * 0.8 + 0.02 * 0.2 = 0.164
    # Year 2: α = 2/5 = 0.4 → g = 0.20 * 0.6 + 0.02 * 0.4 = 0.128
    # Year 3: α = 3/5 = 0.6 → g = 0.20 * 0.4 + 0.02 * 0.6 = 0.092
    # Year 4: α = 4/5 = 0.8 → g = 0.20 * 0.2 + 0.02 * 0.8 = 0.056
    # Year 5: α = 5/5 = 1.0 → g = 0.20 * 0.0 + 0.02 * 1.0 = 0.020

    expected_growth_rates = [0.164, 0.128, 0.092, 0.056, 0.020]
    
    current_flow = base_flow
    for i, expected_g in enumerate(expected_growth_rates):
        current_flow *= (1 + expected_g)
        assert flows[i] == pytest.approx(current_flow, abs=1e-6)


def test_fade_transition_single_year_fade():
    """
    Test fade with only 1 year of fade period.
    """
    base_flow = 1_000_000
    years = 6
    g_start = 0.18
    g_term = 0.03
    high_growth_years = 5  # 5 years high, 1 year fade

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # First 5 years at g_start
    for i in range(5):
        actual_g = (flows[i] / (flows[i - 1] if i > 0 else base_flow)) - 1
        assert actual_g == pytest.approx(g_start, rel=1e-9)

    # Year 6: α = 1/1 = 1.0 → g = g_term = 0.03
    final_g = (flows[5] / flows[4]) - 1
    assert final_g == pytest.approx(g_term, rel=1e-9)


def test_fade_maintains_cash_flow_continuity():
    """
    Test that cash flows are continuous (no jumps) during fade transition.
    
    Each year's flow should be strictly greater than previous (for positive growth).
    """
    base_flow = 1_000_000
    years = 10
    g_start = 0.10
    g_term = 0.02
    high_growth_years = 5

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # All flows should be increasing (positive growth)
    for i in range(1, len(flows)):
        assert flows[i] > flows[i - 1], f"Flow {i} should be > flow {i-1}"

    # No sudden jumps at transition point
    growth_before_transition = (flows[4] / flows[3]) - 1
    growth_at_transition = (flows[5] / flows[4]) - 1
    
    # Growth at transition should be less than before but not drastically
    assert growth_at_transition < growth_before_transition
    assert growth_at_transition > 0  # Still positive


def test_fade_with_negative_terminal_growth():
    """
    Test fade transition when terminal growth is negative (declining business).
    """
    base_flow = 1_000_000
    years = 8
    g_start = 0.05
    g_term = -0.02  # Declining
    high_growth_years = 4

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # First 4 years positive growth
    for i in range(4):
        assert flows[i] > (flows[i - 1] if i > 0 else base_flow)

    # After year 4, growth should decline and eventually become negative
    final_growth = (flows[-1] / flows[-2]) - 1
    assert final_growth == pytest.approx(g_term, abs=1e-9)


def test_fade_mathematical_correctness():
    """
    Test that the fade formula is mathematically correct for all years.
    
    Verifies the linear interpolation formula:
    g(t) = g_start * (1 - α) + g_term * α
    where α = (t - high_growth_years) / (years - high_growth_years)
    """
    base_flow = 1_000_000
    years = 10
    g_start = 0.12
    g_term = 0.03
    high_growth_years = 6

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # Manually calculate expected flows
    expected_flows = []
    current = base_flow
    
    for t in range(1, years + 1):
        if t <= high_growth_years:
            g = g_start
        else:
            years_remaining = years - high_growth_years
            step_in_fade = t - high_growth_years
            alpha = step_in_fade / years_remaining
            g = g_start * (1 - alpha) + g_term * alpha
        
        current *= (1 + g)
        expected_flows.append(current)

    # Compare with actual flows
    for i, (actual, expected) in enumerate(zip(flows, expected_flows)):
        assert actual == pytest.approx(expected, rel=1e-9), f"Year {i+1} mismatch"


# ============================================================================
# TEST SimpleFlowProjector with fade transition
# ============================================================================


def test_simple_projector_with_fade_parameter():
    """
    Test SimpleFlowProjector correctly uses high_growth_period parameter.
    """
    projector = SimpleFlowProjector()
    company = Mock()
    params = Mock()
    
    strategy = Mock()
    strategy.growth_rate_p1 = 0.10
    strategy.projection_years = 10
    strategy.high_growth_period = 7  # 7 years high growth, 3 years fade
    
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.02
    strategy.terminal_value = terminal_value
    
    params.strategy = strategy

    output = projector.project(1_000_000, company, params)

    assert len(output.flows) == 10
    
    # Verify first 7 years have consistent high growth
    for i in range(1, 7):
        g = (output.flows[i] / output.flows[i - 1]) - 1
        assert g == pytest.approx(0.10, rel=1e-6)
    
    # Verify last 3 years have declining growth (fade)
    growth_8 = (output.flows[7] / output.flows[6]) - 1
    growth_9 = (output.flows[8] / output.flows[7]) - 1
    growth_10 = (output.flows[9] / output.flows[8]) - 1
    
    assert growth_8 < 0.10
    assert growth_9 < growth_8
    assert growth_10 < growth_9
    assert growth_10 == pytest.approx(0.02, abs=1e-9)


def test_simple_projector_backward_compatibility():
    """
    Test that projector works without high_growth_period (backward compatible).
    
    When high_growth_period is not set, should default to projection_years
    (no fade transition).
    """
    projector = SimpleFlowProjector()
    company = Mock()
    params = Mock()
    
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5
    # high_growth_period not set
    
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.02
    strategy.terminal_value = terminal_value
    
    params.strategy = strategy

    output = projector.project(1_000_000, company, params)

    # All years should have the same growth (no fade)
    for i in range(1, 5):
        g = (output.flows[i] / output.flows[i - 1]) - 1
        assert g == pytest.approx(0.08, rel=1e-6)


def test_simple_projector_with_zero_high_growth():
    """
    Test projector when high_growth_period is set to 0 (immediate fade).
    """
    projector = SimpleFlowProjector()
    company = Mock()
    params = Mock()
    
    strategy = Mock()
    strategy.growth_rate_p1 = 0.15
    strategy.projection_years = 5
    strategy.high_growth_period = 0  # Immediate fade
    
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value
    
    params.strategy = strategy

    output = projector.project(1_000_000, company, params)

    # Growth should start high and decline to terminal
    growth_rates = []
    for i in range(len(output.flows)):
        if i == 0:
            g = (output.flows[i] / 1_000_000) - 1
        else:
            g = (output.flows[i] / output.flows[i - 1]) - 1
        growth_rates.append(g)

    # Growth should be strictly decreasing
    for i in range(1, len(growth_rates)):
        assert growth_rates[i] < growth_rates[i - 1]
    
    # Last growth should equal terminal
    assert growth_rates[-1] == pytest.approx(0.03, abs=1e-9)


def test_fade_preserves_present_value_calculation():
    """
    Test that NPV calculation remains mathematically correct with fade.
    
    This ensures that the fade doesn't introduce numerical errors
    that would affect valuation.
    """
    base_flow = 1_000_000
    years = 10
    g_start = 0.10
    g_term = 0.02
    high_growth_years = 6
    wacc = 0.08  # Discount rate

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # Calculate NPV
    npv = sum(flow / ((1 + wacc) ** (i + 1)) for i, flow in enumerate(flows))

    # NPV should be positive and reasonable
    assert npv > 0
    assert npv > base_flow  # Should be worth more than initial flow
    
    # Flows should sum to a reasonable total
    total_undiscounted = sum(flows)
    assert total_undiscounted > base_flow * years


def test_fade_edge_case_one_year_projection():
    """
    Test fade with only 1 year projection.
    """
    base_flow = 1_000_000
    years = 1
    g_start = 0.10
    g_term = 0.02
    high_growth_years = 1

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    assert len(flows) == 1
    # Should use g_start (no fade with 1 year)
    assert flows[0] == pytest.approx(base_flow * 1.10, rel=1e-9)


def test_fade_edge_case_high_growth_exceeds_years():
    """
    Test fade when high_growth_years > projection_years (should cap at years).
    """
    base_flow = 1_000_000
    years = 5
    g_start = 0.10
    g_term = 0.02
    high_growth_years = 10  # Exceeds years

    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)

    # Should behave as if high_growth_years = years (no fade)
    for i in range(years):
        expected_growth = g_start
        if i == 0:
            expected = base_flow * (1 + expected_growth)
        else:
            expected = flows[i - 1] * (1 + expected_growth)
        assert flows[i] == pytest.approx(expected, rel=1e-9)
