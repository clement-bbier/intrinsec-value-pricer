"""
tests/unit/test_library_graham.py

COMPREHENSIVE TEST SUITE FOR GRAHAM LIBRARY
===========================================
Role: Tests all methods in src/valuation/library/graham.py
Coverage Target: ≥90% line coverage
Standards: pytest + unittest.mock for dependencies
"""

import pytest
from unittest.mock import Mock

from src.valuation.library.graham import GrahamLibrary
from src.models.parameters.base_parameter import Parameters
from src.config.constants import MacroDefaults, ModelDefaults


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_graham_params():
    """Mock Parameters object for Graham Formula."""
    params = Mock(spec=Parameters)
    
    # Mock strategy with Graham-specific attributes
    strategy = Mock()
    strategy.eps_normalized = 5.00
    strategy.growth_estimate = 0.10  # 10% growth
    
    params.strategy = strategy
    
    # Mock common rates
    rates = Mock()
    rates.corporate_aaa_yield = 0.045  # 4.5%
    common = Mock()
    common.rates = rates
    params.common = common
    
    return params


# ============================================================================
# TEST compute_intrinsic_value
# ============================================================================

def test_compute_intrinsic_value_basic(mock_graham_params):
    """Test Graham formula with standard inputs."""
    iv, step = GrahamLibrary.compute_intrinsic_value(mock_graham_params)
    
    # Formula: V = (EPS * (8.5 + 2g) * 4.4) / Y
    # V = (5.00 * (8.5 + 2*10) * 4.4) / 4.5
    # V = (5.00 * 28.5 * 4.4) / 4.5
    eps = 5.00
    g = 10.0  # Graham uses integer growth (10 for 10%)
    y = 4.5   # Graham uses percentage (4.5 for 4.5%)
    expected_iv = (eps * (8.5 + 2 * g) * 4.4) / y
    
    assert iv == pytest.approx(expected_iv, rel=1e-6)
    
    # Check step structure
    assert step.step_key == "GRAHAM_FORMULA"
    assert step.result == iv
    assert "EPS" in step.variables_map
    assert "g" in step.variables_map
    assert "Y" in step.variables_map
    
    # Verify variable values
    assert step.variables_map["EPS"].value == 5.00
    assert step.variables_map["g"].value == 0.10
    assert step.variables_map["Y"].value == 0.045


def test_compute_intrinsic_value_high_eps():
    """Test Graham formula with high EPS."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 25.00
    strategy.growth_estimate = 0.08
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # High EPS should result in high IV
    assert iv > 100
    
    # Formula check
    expected = (25.00 * (8.5 + 2 * 8.0) * 4.4) / 5.0
    assert iv == pytest.approx(expected, rel=1e-6)


def test_compute_intrinsic_value_low_growth():
    """Test Graham formula with low growth rate."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 10.00
    strategy.growth_estimate = 0.02  # Only 2% growth
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.04
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Low growth should use closer to base multiplier (8.5)
    expected = (10.00 * (8.5 + 2 * 2.0) * 4.4) / 4.0
    assert iv == pytest.approx(expected, rel=1e-6)


def test_compute_intrinsic_value_high_growth():
    """Test Graham formula with high growth rate."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 8.00
    strategy.growth_estimate = 0.20  # 20% growth
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # High growth should significantly increase multiplier
    expected = (8.00 * (8.5 + 2 * 20.0) * 4.4) / 5.0
    assert iv == pytest.approx(expected, rel=1e-6)
    assert iv > 300  # Should be substantial


def test_compute_intrinsic_value_zero_growth():
    """Test Graham formula with zero growth."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 6.00
    strategy.growth_estimate = 0.0
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # With zero growth, multiplier is just 8.5
    expected = (6.00 * 8.5 * 4.4) / 5.0
    assert iv == pytest.approx(expected, rel=1e-6)


def test_compute_intrinsic_value_high_yield():
    """Test Graham formula with high AAA yield (reduces value)."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 10.00
    strategy.growth_estimate = 0.10
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.08  # High yield
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # High yield in denominator reduces value
    expected = (10.00 * (8.5 + 2 * 10.0) * 4.4) / 8.0
    assert iv == pytest.approx(expected, rel=1e-6)
    assert iv < 150  # Lower than with standard yield


def test_compute_intrinsic_value_low_yield():
    """Test Graham formula with low AAA yield (increases value)."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 10.00
    strategy.growth_estimate = 0.10
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.02  # Very low yield
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Low yield increases value significantly
    expected = (10.00 * (8.5 + 2 * 10.0) * 4.4) / 2.0
    assert iv == pytest.approx(expected, rel=1e-6)
    assert iv > 500  # Very high due to low discount


def test_compute_intrinsic_value_missing_eps():
    """Test Graham formula with missing EPS (uses default 0.0)."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = None  # Missing
    strategy.growth_estimate = 0.10
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # With EPS=0, IV should be 0
    assert iv == 0.0
    assert step.variables_map["EPS"].value == 0.0


def test_compute_intrinsic_value_missing_growth():
    """Test Graham formula with missing growth (uses default)."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 5.00
    strategy.growth_estimate = None  # Missing
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Should use ModelDefaults.DEFAULT_GROWTH_RATE
    assert step.variables_map["g"].value == ModelDefaults.DEFAULT_GROWTH_RATE
    assert iv > 0


def test_compute_intrinsic_value_missing_yield():
    """Test Graham formula with missing AAA yield (uses default)."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 5.00
    strategy.growth_estimate = 0.10
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = None  # Missing
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Should use MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD
    assert step.variables_map["Y"].value == MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD
    assert iv > 0


def test_compute_intrinsic_value_negative_eps():
    """Test Graham formula with negative EPS."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = -2.00  # Loss-making
    strategy.growth_estimate = 0.10
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Negative EPS should give negative IV (not economically valid, but formula-consistent)
    assert iv < 0


def test_compute_intrinsic_value_negative_growth():
    """Test Graham formula with negative growth rate."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 5.00
    strategy.growth_estimate = -0.05  # Declining
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Negative growth reduces multiplier
    expected = (5.00 * (8.5 + 2 * (-5.0)) * 4.4) / 5.0
    assert iv == pytest.approx(expected, rel=1e-6)
    # Multiplier becomes 8.5 - 10 = -1.5, so IV could be negative
    assert iv < 0


def test_compute_intrinsic_value_fractional_values():
    """Test Graham formula with fractional EPS and growth."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 3.14
    strategy.growth_estimate = 0.0732
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.0456
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Should handle fractional values correctly
    expected = (3.14 * (8.5 + 2 * 7.32) * 4.4) / 4.56
    assert iv == pytest.approx(expected, rel=1e-6)


def test_compute_intrinsic_value_large_eps():
    """Test Graham formula with very large EPS (tech stock)."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 100.00
    strategy.growth_estimate = 0.15
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Large EPS should produce very large IV
    assert iv > 1000
    expected = (100.00 * (8.5 + 2 * 15.0) * 4.4) / 5.0
    assert iv == pytest.approx(expected, rel=1e-6)


def test_compute_intrinsic_value_small_eps():
    """Test Graham formula with very small EPS."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 0.10
    strategy.growth_estimate = 0.08
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Small EPS should produce small IV
    expected = (0.10 * (8.5 + 2 * 8.0) * 4.4) / 5.0
    assert iv == pytest.approx(expected, rel=1e-6)
    assert iv < 3.0


def test_compute_intrinsic_value_formatted_output(mock_graham_params):
    """Test that step includes properly formatted values."""
    iv, step = GrahamLibrary.compute_intrinsic_value(mock_graham_params)
    
    # Check formatted values
    assert step.variables_map["g"].formatted_value == "10.0%"
    assert step.variables_map["Y"].formatted_value == "4.50%"
    
    # Check theoretical formula is present
    assert step.theoretical_formula
    assert step.actual_calculation
    assert step.interpretation


def test_compute_intrinsic_value_variable_sources(mock_graham_params):
    """Test that variables have correct sources."""
    iv, step = GrahamLibrary.compute_intrinsic_value(mock_graham_params)
    
    # EPS comes from system (fetched data)
    from src.models.enums import VariableSource
    assert step.variables_map["EPS"].source == VariableSource.SYSTEM
    
    # Growth is manual override (user input)
    assert step.variables_map["g"].source == VariableSource.MANUAL_OVERRIDE
    
    # Yield is from system (macro data)
    assert step.variables_map["Y"].source == VariableSource.SYSTEM


# ============================================================================
# EDGE CASES AND VALIDATION
# ============================================================================

def test_compute_intrinsic_value_extreme_yield():
    """Test with extreme AAA yield values."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 5.00
    strategy.growth_estimate = 0.10
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.20  # Extremely high
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv, step = GrahamLibrary.compute_intrinsic_value(params)
    
    # Should handle extreme yield
    expected = (5.00 * (8.5 + 2 * 10.0) * 4.4) / 20.0
    assert iv == pytest.approx(expected, rel=1e-6)


def test_compute_intrinsic_value_consistency():
    """Test that multiple calls with same params give same result."""
    params = Mock(spec=Parameters)
    strategy = Mock()
    strategy.eps_normalized = 7.50
    strategy.growth_estimate = 0.12
    params.strategy = strategy
    
    rates = Mock()
    rates.corporate_aaa_yield = 0.05
    common = Mock()
    common.rates = rates
    params.common = common
    
    iv1, step1 = GrahamLibrary.compute_intrinsic_value(params)
    iv2, step2 = GrahamLibrary.compute_intrinsic_value(params)
    
    assert iv1 == iv2
    assert step1.result == step2.result
