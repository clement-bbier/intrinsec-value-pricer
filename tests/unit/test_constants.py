"""
tests/unit/test_constants.py

CONSTANTS VALIDATION TESTS
==========================
Role: Verifies src/config/constants.py structure and values.
Coverage: ValuationEngineDefaults, MacroDefaults, ModelDefaults, etc.
"""

import pytest
from src.config.constants import (
    ValuationEngineDefaults,
    MacroDefaults,
    ModelDefaults,
    MonteCarloDefaults,
    SensitivityDefaults
)


@pytest.mark.unit
def test_spreads_large_cap_structure():
    """Test SPREADS_LARGE_CAP is a tuple of tuples with correct structure."""
    spreads = ValuationEngineDefaults.SPREADS_LARGE_CAP
    
    assert isinstance(spreads, tuple)
    assert len(spreads) > 0
    
    # Check each element is a tuple with 2 values (threshold, spread)
    for item in spreads:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], (int, float))  # threshold
        assert isinstance(item[1], (int, float))  # spread


@pytest.mark.unit
def test_spreads_large_cap_sorted_descending():
    """Test SPREADS_LARGE_CAP is sorted in descending order by threshold."""
    spreads = ValuationEngineDefaults.SPREADS_LARGE_CAP
    
    thresholds = [item[0] for item in spreads]
    assert thresholds == sorted(thresholds, reverse=True)


@pytest.mark.unit
def test_spreads_small_mid_cap_structure():
    """Test SPREADS_SMALL_MID_CAP has same structure as SPREADS_LARGE_CAP."""
    spreads = ValuationEngineDefaults.SPREADS_SMALL_MID_CAP
    
    assert isinstance(spreads, tuple)
    assert len(spreads) > 0
    
    for item in spreads:
        assert isinstance(item, tuple)
        assert len(item) == 2


@pytest.mark.unit
def test_spreads_small_mid_cap_sorted_descending():
    """Test SPREADS_SMALL_MID_CAP is sorted in descending order."""
    spreads = ValuationEngineDefaults.SPREADS_SMALL_MID_CAP
    
    thresholds = [item[0] for item in spreads]
    assert thresholds == sorted(thresholds, reverse=True)


@pytest.mark.unit
def test_macro_defaults_risk_free_rate():
    """Test MacroDefaults has DEFAULT_RISK_FREE_RATE."""
    assert hasattr(MacroDefaults, 'DEFAULT_RISK_FREE_RATE')
    assert isinstance(MacroDefaults.DEFAULT_RISK_FREE_RATE, float)
    assert 0.0 <= MacroDefaults.DEFAULT_RISK_FREE_RATE <= 0.20


@pytest.mark.unit
def test_macro_defaults_market_risk_premium():
    """Test MacroDefaults has DEFAULT_MARKET_RISK_PREMIUM."""
    assert hasattr(MacroDefaults, 'DEFAULT_MARKET_RISK_PREMIUM')
    assert isinstance(MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM, float)
    assert 0.0 <= MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM <= 0.20


@pytest.mark.unit
def test_macro_defaults_tax_rate():
    """Test MacroDefaults has DEFAULT_TAX_RATE."""
    assert hasattr(MacroDefaults, 'DEFAULT_TAX_RATE')
    assert isinstance(MacroDefaults.DEFAULT_TAX_RATE, float)
    assert 0.0 <= MacroDefaults.DEFAULT_TAX_RATE <= 0.50


@pytest.mark.unit
def test_model_defaults_beta():
    """Test ModelDefaults has DEFAULT_BETA."""
    assert hasattr(ModelDefaults, 'DEFAULT_BETA')
    assert isinstance(ModelDefaults.DEFAULT_BETA, float)
    assert ModelDefaults.DEFAULT_BETA == pytest.approx(1.0)


@pytest.mark.unit
def test_monte_carlo_defaults_min_simulations():
    """Test MonteCarloDefaults has MIN_SIMULATIONS."""
    assert hasattr(MonteCarloDefaults, 'MIN_SIMULATIONS')
    assert isinstance(MonteCarloDefaults.MIN_SIMULATIONS, int)
    assert MonteCarloDefaults.MIN_SIMULATIONS >= 100


@pytest.mark.unit
def test_monte_carlo_defaults_max_simulations():
    """Test MonteCarloDefaults has MAX_SIMULATIONS."""
    assert hasattr(MonteCarloDefaults, 'MAX_SIMULATIONS')
    assert isinstance(MonteCarloDefaults.MAX_SIMULATIONS, int)
    assert MonteCarloDefaults.MAX_SIMULATIONS <= 100_000


@pytest.mark.unit
def test_monte_carlo_defaults_default_simulations():
    """Test MonteCarloDefaults has DEFAULT_SIMULATIONS within bounds."""
    assert hasattr(MonteCarloDefaults, 'DEFAULT_SIMULATIONS')
    assert (
        MonteCarloDefaults.MIN_SIMULATIONS
        <= MonteCarloDefaults.DEFAULT_SIMULATIONS
        <= MonteCarloDefaults.MAX_SIMULATIONS
    )


@pytest.mark.unit
def test_sensitivity_defaults_steps():
    """Test SensitivityDefaults has DEFAULT_STEPS."""
    assert hasattr(SensitivityDefaults, 'DEFAULT_STEPS')
    assert isinstance(SensitivityDefaults.DEFAULT_STEPS, int)
    assert 3 <= SensitivityDefaults.DEFAULT_STEPS <= 9


@pytest.mark.unit
def test_sensitivity_defaults_wacc_span():
    """Test SensitivityDefaults has DEFAULT_WACC_SPAN."""
    assert hasattr(SensitivityDefaults, 'DEFAULT_WACC_SPAN')
    assert isinstance(SensitivityDefaults.DEFAULT_WACC_SPAN, float)
    assert 0.0 < SensitivityDefaults.DEFAULT_WACC_SPAN <= 0.10


@pytest.mark.unit
def test_sensitivity_defaults_growth_span():
    """Test SensitivityDefaults has DEFAULT_GROWTH_SPAN."""
    assert hasattr(SensitivityDefaults, 'DEFAULT_GROWTH_SPAN')
    assert isinstance(SensitivityDefaults.DEFAULT_GROWTH_SPAN, float)
    assert 0.0 < SensitivityDefaults.DEFAULT_GROWTH_SPAN <= 0.10
