"""
tests/unit/test_flow_projector.py

COMPREHENSIVE TEST SUITE FOR FLOW PROJECTOR
===========================================
Role: Tests all classes and methods in src/computation/flow_projector.py
Coverage Target: ≥90% line coverage
Standards: pytest + unittest.mock for dependencies
"""

import pytest
from unittest.mock import Mock

from src.computation.flow_projector import (
    FlowProjector,
    SimpleFlowProjector,
    MarginConvergenceProjector,
    ProjectionOutput,
    project_flows
)
from src.models import VariableSource


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_company():
    """Mock Company object."""
    company = Mock()
    company.ticker = "AAPL"
    company.name = "Apple Inc."
    return company


@pytest.fixture
def mock_params_simple():
    """Mock Parameters for SimpleFlowProjector."""
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5
    
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value
    
    params.strategy = strategy
    return params


@pytest.fixture
def mock_params_ddm():
    """Mock Parameters for DDM (uses growth_rate instead of growth_rate_p1)."""
    params = Mock()
    strategy = Mock(spec=['growth_rate', 'projection_years', 'terminal_value'])
    strategy.growth_rate = 0.06
    strategy.projection_years = 5
    
    terminal_value = Mock(spec=['perpetual_growth_rate'])
    terminal_value.perpetual_growth_rate = 0.025
    strategy.terminal_value = terminal_value
    
    params.strategy = strategy
    return params


@pytest.fixture
def mock_params_margin_convergence():
    """Mock Parameters for MarginConvergenceProjector."""
    params = Mock()
    strategy = Mock()
    strategy.target_fcf_margin = 0.15
    strategy.revenue_growth_rate = 0.10
    strategy.projection_years = 5
    params.strategy = strategy
    return params


# ============================================================================
# TEST project_flows (atomic function)
# ============================================================================

def test_project_flows_basic():
    """Test basic flow projection with fade-down."""
    base_flow = 1_000_000
    years = 5
    g_start = 0.10
    g_term = 0.03
    high_growth_years = 5
    
    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)
    
    assert len(flows) == 5
    assert all(f > 0 for f in flows)
    # First flow should be base * (1 + g_start)
    assert flows[0] == pytest.approx(base_flow * 1.10, rel=1e-6)


def test_project_flows_with_plateau():
    """Test projection with high growth plateau then fade-down."""
    base_flow = 1_000_000
    years = 5
    g_start = 0.15
    g_term = 0.03
    high_growth_years = 2  # 2 years high growth, then fade
    
    flows = project_flows(base_flow, years, g_start, g_term, high_growth_years)
    
    # First 2 years should use g_start
    assert flows[0] == pytest.approx(base_flow * 1.15, rel=1e-6)
    assert flows[1] == pytest.approx(base_flow * (1.15 ** 2), rel=1e-6)
    
    # After year 2, growth should fade
    growth_2_to_3 = (flows[2] / flows[1]) - 1
    assert growth_2_to_3 < g_start


def test_project_flows_zero_years():
    """Test projection with zero years."""
    flows = project_flows(1_000_000, 0, 0.10, 0.03, 0)
    assert len(flows) == 0


def test_project_flows_single_year():
    """Test projection with single year."""
    base_flow = 500_000
    flows = project_flows(base_flow, 1, 0.08, 0.03, 1)
    
    assert len(flows) == 1
    assert flows[0] == pytest.approx(base_flow * 1.08, rel=1e-6)


def test_project_flows_negative_years():
    """Test projection with negative years (edge case)."""
    flows = project_flows(1_000_000, -5, 0.10, 0.03, 5)
    assert len(flows) == 0


def test_project_flows_zero_growth():
    """Test projection with zero growth rates."""
    base_flow = 1_000_000
    flows = project_flows(base_flow, 5, 0.0, 0.0, 5)
    
    # All flows should equal base flow
    for flow in flows:
        assert flow == pytest.approx(base_flow, rel=1e-6)


def test_project_flows_negative_growth():
    """Test projection with negative growth (decline)."""
    base_flow = 1_000_000
    flows = project_flows(base_flow, 5, -0.05, -0.02, 5)
    
    # Flows should decline
    assert all(flows[i] < flows[i-1] for i in range(1, len(flows)))


def test_project_flows_high_growth_none():
    """Test projection when high_growth_years is None (default to full period)."""
    base_flow = 1_000_000
    flows = project_flows(base_flow, 5, 0.10, 0.03, None)
    
    assert len(flows) == 5
    # Should default to full period high growth
    assert flows[0] == pytest.approx(base_flow * 1.10, rel=1e-6)


def test_project_flows_high_growth_exceeds_years():
    """Test when high_growth_years exceeds total years."""
    base_flow = 1_000_000
    flows = project_flows(base_flow, 5, 0.10, 0.03, 10)  # 10 > 5
    
    # Should cap at 5 years
    assert len(flows) == 5


# ============================================================================
# TEST SimpleFlowProjector
# ============================================================================

def test_simple_flow_projector_basic(mock_company, mock_params_simple):
    """Test SimpleFlowProjector with standard FCFF parameters."""
    projector = SimpleFlowProjector()
    base_value = 1_000_000
    
    output = projector.project(base_value, mock_company, mock_params_simple)
    
    assert isinstance(output, ProjectionOutput)
    assert len(output.flows) == 5
    assert all(f > 0 for f in output.flows)
    
    # Check metadata
    assert output.method_label
    assert output.theoretical_formula
    assert output.actual_calculation
    assert len(output.variables) > 0


def test_simple_flow_projector_ddm_fallback(mock_company, mock_params_ddm):
    """Test SimpleFlowProjector with DDM parameters (fallback to growth_rate)."""
    projector = SimpleFlowProjector()
    base_value = 50.0
    
    output = projector.project(base_value, mock_company, mock_params_ddm)
    
    assert len(output.flows) == 5
    # Should use growth_rate = 0.06
    assert "g" in output.variables
    assert output.variables["g"].value == 0.06


def test_simple_flow_projector_no_terminal_value():
    """Test SimpleFlowProjector when terminal_value is missing."""
    projector = SimpleFlowProjector()
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5
    strategy.terminal_value = None  # Missing
    params.strategy = strategy
    
    output = projector.project(1_000_000, company, params)
    
    # Should use default terminal growth
    assert len(output.flows) == 5


def test_simple_flow_projector_missing_years():
    """Test SimpleFlowProjector with missing projection years."""
    projector = SimpleFlowProjector()
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = None  # Missing
    
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value
    params.strategy = strategy
    
    output = projector.project(1_000_000, company, params)
    
    # Should use default (5 years)
    assert len(output.flows) == 5


def test_simple_flow_projector_trace_variables(mock_company, mock_params_simple):
    """Test that SimpleFlowProjector creates proper trace variables."""
    projector = SimpleFlowProjector()
    
    output = projector.project(1_000_000, mock_company, mock_params_simple)
    
    # Check variable structure
    assert "g" in output.variables
    assert "g_n" in output.variables
    assert "n" in output.variables
    
    # Check values
    assert output.variables["g"].value == 0.08
    assert output.variables["g_n"].value == 0.03
    assert output.variables["n"].value == 5.0


def test_simple_flow_projector_formatted_values(mock_company, mock_params_simple):
    """Test that variables have proper formatting."""
    projector = SimpleFlowProjector()
    
    output = projector.project(1_000_000, mock_company, mock_params_simple)
    
    # Growth rates should be formatted as percentages
    assert "%" in output.variables["g"].formatted_value
    assert "%" in output.variables["g_n"].formatted_value


# ============================================================================
# TEST MarginConvergenceProjector
# ============================================================================

def test_margin_convergence_basic(mock_company, mock_params_margin_convergence):
    """Test MarginConvergenceProjector with basic parameters."""
    projector = MarginConvergenceProjector()
    base_revenue = 10_000_000
    
    output = projector.project(base_revenue, mock_company, mock_params_margin_convergence)
    
    assert isinstance(output, ProjectionOutput)
    assert len(output.flows) == 5
    
    # Flows should increase (revenue growth + margin expansion)
    assert output.flows[-1] > output.flows[0]


def test_margin_convergence_margin_interpolation(mock_company, mock_params_margin_convergence):
    """Test that margins interpolate linearly from current to target."""
    projector = MarginConvergenceProjector()
    base_revenue = 5_000_000
    
    output = projector.project(base_revenue, mock_company, mock_params_margin_convergence)
    
    # Manually calculate expected for year 1
    # curr_margin starts at 0.0 (code assumption when no anchor)
    # Linear ramp: applied_margin = 0 + (0.15 - 0) * (1/5) = 0.03
    # Revenue Y1 = 5M * 1.10 = 5.5M
    # FCF Y1 = 5.5M * 0.03 = 165k
    expected_fcf_y1 = 5_000_000 * 1.10 * (0.15 * 1/5)
    assert output.flows[0] == pytest.approx(expected_fcf_y1, rel=1e-6)


def test_margin_convergence_zero_years():
    """Test MarginConvergenceProjector with zero projection years (defaults to 5)."""
    projector = MarginConvergenceProjector()
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.target_fcf_margin = 0.15
    strategy.revenue_growth_rate = 0.10
    strategy.projection_years = 0  # Will default to 5 due to 'or 5' fallback
    params.strategy = strategy
    
    output = projector.project(10_000_000, company, params)
    
    # Code treats 0 as falsy and defaults to 5 years
    assert len(output.flows) == 5


def test_margin_convergence_missing_params():
    """Test MarginConvergenceProjector with missing parameters."""
    projector = MarginConvergenceProjector()
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.target_fcf_margin = None
    strategy.revenue_growth_rate = None
    strategy.projection_years = None
    params.strategy = strategy
    
    output = projector.project(5_000_000, company, params)
    
    # Should use defaults
    assert len(output.flows) == 5  # Default years


def test_margin_convergence_trace_variables(mock_company, mock_params_margin_convergence):
    """Test that MarginConvergenceProjector creates trace variables."""
    projector = MarginConvergenceProjector()
    
    output = projector.project(10_000_000, mock_company, mock_params_margin_convergence)
    
    assert "m_target" in output.variables
    assert "g_rev" in output.variables
    assert output.variables["m_target"].value == 0.15
    assert output.variables["g_rev"].value == 0.10


def test_margin_convergence_high_target_margin():
    """Test with high target margin."""
    projector = MarginConvergenceProjector()
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.target_fcf_margin = 0.30  # Very high
    strategy.revenue_growth_rate = 0.08
    strategy.projection_years = 5
    params.strategy = strategy
    
    output = projector.project(20_000_000, company, params)
    
    # Final year should approach target margin
    # Revenue Y5 ≈ 20M * (1.08^5) ≈ 29.4M
    # FCF Y5 ≈ 29.4M * 0.30 ≈ 8.8M
    assert output.flows[-1] > 8_000_000


def test_margin_convergence_negative_revenue_growth():
    """Test with negative revenue growth (decline)."""
    projector = MarginConvergenceProjector()
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.target_fcf_margin = 0.12
    strategy.revenue_growth_rate = -0.05  # Declining
    strategy.projection_years = 3
    params.strategy = strategy
    
    output = projector.project(10_000_000, company, params)
    
    # Revenue should decline despite margin expansion
    assert len(output.flows) == 3


# ============================================================================
# TEST FlowProjector._build_trace_variable (static helper)
# ============================================================================

def test_build_trace_variable_manual_override():
    """Test trace variable with manual override."""
    var = FlowProjector._build_trace_variable(
        symbol="g",
        value=0.08,
        manual_value=0.08,
        provider_value=0.05,
        description="Growth Rate",
        is_pct=True
    )
    
    assert var.symbol == "g"
    assert var.value == 0.08
    assert var.source == VariableSource.MANUAL_OVERRIDE
    assert var.is_overridden is True
    assert var.original_value == 0.05
    assert "%" in var.formatted_value


def test_build_trace_variable_provider_value():
    """Test trace variable from provider (no override)."""
    var = FlowProjector._build_trace_variable(
        symbol="eps",
        value=5.00,
        manual_value=None,
        provider_value=5.00,
        description="EPS",
        is_pct=False
    )
    
    assert var.source == VariableSource.YAHOO_FINANCE
    assert var.is_overridden is False


def test_build_trace_variable_default():
    """Test trace variable with default value (no manual or provider)."""
    var = FlowProjector._build_trace_variable(
        symbol="r",
        value=0.10,
        manual_value=None,
        provider_value=None,
        description="Rate",
        is_pct=True
    )
    
    assert var.source == VariableSource.DEFAULT
    assert var.is_overridden is False


def test_build_trace_variable_percentage_formatting():
    """Test percentage formatting."""
    var = FlowProjector._build_trace_variable(
        symbol="g",
        value=0.0825,
        manual_value=0.0825,
        provider_value=None,
        description="Growth",
        is_pct=True
    )
    
    assert var.formatted_value == "8.25%"


def test_build_trace_variable_number_formatting():
    """Test number formatting."""
    var = FlowProjector._build_trace_variable(
        symbol="FCF",
        value=1_234_567.89,
        manual_value=None,
        provider_value=1_234_567.89,
        description="Free Cash Flow",
        is_pct=False
    )
    
    # Should use format_smart_number
    assert var.formatted_value


# ============================================================================
# TEST ProjectionOutput model
# ============================================================================

def test_projection_output_creation():
    """Test ProjectionOutput creation and defaults."""
    output = ProjectionOutput(
        flows=[100, 110, 120, 130, 140],
        method_label="Test Method",
        theoretical_formula="FCF × (1+g)^t",
        actual_calculation="100 × (1.10)^5",
        interpretation="Test interpretation",
        variables={}
    )
    
    assert len(output.flows) == 5
    assert output.method_label == "Test Method"
    assert len(output.variables) == 0


def test_projection_output_defaults():
    """Test ProjectionOutput with default values."""
    output = ProjectionOutput(flows=[100, 110])
    
    assert output.method_label == ""
    assert output.theoretical_formula == ""
    assert output.actual_calculation == ""
    assert output.interpretation == ""
    assert output.variables == {}


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_simple_projector_full_workflow(mock_company, mock_params_simple):
    """Integration test: SimpleFlowProjector full workflow."""
    projector = SimpleFlowProjector()
    base_fcf = 1_500_000
    
    output = projector.project(base_fcf, mock_company, mock_params_simple)
    
    # Validate output
    assert len(output.flows) == 5
    assert all(f > 0 for f in output.flows)
    
    # Flows should generally increase (positive growth)
    assert output.flows[-1] > output.flows[0]
    
    # Metadata should be complete
    assert output.method_label
    assert output.theoretical_formula
    assert output.variables
    
    # Variables should have proper structure
    for var_info in output.variables.values():
        assert var_info.symbol
        assert var_info.source


def test_margin_projector_full_workflow(mock_company, mock_params_margin_convergence):
    """Integration test: MarginConvergenceProjector full workflow."""
    projector = MarginConvergenceProjector()
    base_revenue = 50_000_000
    
    output = projector.project(base_revenue, mock_company, mock_params_margin_convergence)
    
    # Validate output
    assert len(output.flows) == 5
    assert all(f >= 0 for f in output.flows)
    
    # FCFs should increase (revenue growth + margin expansion)
    assert output.flows[-1] > output.flows[0]
    
    # Check trace
    assert "m_target" in output.variables
    assert "g_rev" in output.variables


def test_multiple_projectors_independence():
    """Test that multiple projector instances are independent."""
    projector1 = SimpleFlowProjector()
    projector2 = SimpleFlowProjector()
    
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.10
    strategy.projection_years = 5
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value
    params.strategy = strategy
    
    output1 = projector1.project(1_000_000, company, params)
    output2 = projector2.project(2_000_000, company, params)
    
    # Should produce independent results
    assert output1.flows[0] != output2.flows[0]
    assert output1.flows[0] * 2 == pytest.approx(output2.flows[0], rel=1e-6)


def test_projector_with_extreme_values():
    """Test projectors with extreme input values."""
    projector = SimpleFlowProjector()
    company = Mock()
    params = Mock()
    strategy = Mock()
    strategy.growth_rate_p1 = 0.50  # Extreme growth
    strategy.projection_years = 10
    terminal_value = Mock()
    terminal_value.perpetual_growth_rate = 0.03
    strategy.terminal_value = terminal_value
    params.strategy = strategy
    
    base_value = 100
    output = projector.project(base_value, company, params)
    
    # Should handle extreme growth
    assert len(output.flows) == 10
    assert output.flows[-1] > base_value * 10  # Significant growth
