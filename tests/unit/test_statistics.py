"""
tests/unit/test_statistics.py

COMPREHENSIVE TEST SUITE FOR STATISTICS MODULE
==============================================
Role: Tests all functions and classes in src/computation/statistics.py
Coverage Target: ≥90% line coverage
Standards: pytest + unittest.mock + numpy testing
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.computation.statistics import (
    MonteCarloEngine,
    StochasticOutput,
    generate_independent_samples,
    generate_multivariate_samples,
)
from src.models import ValuationMethodology

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_valuation_result_dcf():
    """Mock ValuationResult for DCF model."""
    result = Mock()
    result.intrinsic_value_per_share = 150.0

    # Mock request
    request = Mock()
    request.mode = ValuationMethodology.FCFF_STANDARD
    result.request = request

    # Mock results structure
    strategy_results = Mock()
    strategy_results.projected_flows = [100, 110, 120, 130, 140]
    strategy_results.discounted_terminal_value = 500

    capital_results = Mock()
    capital_results.net_debt_resolved = 1_000_000
    capital_results.enterprise_value = 2_000_000

    common_results = Mock()
    common_results.capital = capital_results

    results = Mock()
    results.strategy = strategy_results
    results.common = common_results

    result.results = results

    return result


@pytest.fixture
def mock_valuation_result_graham():
    """Mock ValuationResult for Graham model."""
    result = Mock()
    result.intrinsic_value_per_share = 100.0

    request = Mock()
    request.mode = ValuationMethodology.GRAHAM
    result.request = request

    strategy_results = Mock()
    strategy_results.eps_used = 5.0
    strategy_results.aaa_yield_used = 0.05

    results = Mock()
    results.strategy = strategy_results

    result.results = results

    return result


@pytest.fixture
def mock_params_mc_enabled():
    """Mock Parameters with Monte Carlo enabled."""
    params = Mock()

    # Monte Carlo config
    mc_config = Mock()
    mc_config.enabled = True
    mc_config.iterations = 1000

    shocks = Mock()
    shocks.beta_volatility = 0.10
    shocks.growth_volatility = 0.02
    shocks.eps_volatility = 0.10
    mc_config.shocks = shocks

    extensions = Mock()
    extensions.monte_carlo = mc_config
    params.extensions = extensions

    # Common rates
    rates = Mock()
    rates.beta = 1.2
    rates.risk_free_rate = 0.03
    rates.market_risk_premium = 0.07
    common = Mock()
    common.rates = rates
    common.capital = Mock()
    common.capital.shares_outstanding = 1_000_000
    params.common = common

    # Strategy
    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5
    params.strategy = strategy

    return params


@pytest.fixture
def mock_params_mc_disabled():
    """Mock Parameters with Monte Carlo disabled."""
    params = Mock()
    mc_config = Mock()
    mc_config.enabled = False
    extensions = Mock()
    extensions.monte_carlo = mc_config
    params.extensions = extensions
    return params


# ============================================================================
# TEST generate_multivariate_samples
# ============================================================================


def test_generate_multivariate_samples_basic():
    """Test basic multivariate sample generation."""
    betas, growths = generate_multivariate_samples(
        mu_beta=1.0, sigma_beta=0.15, mu_growth=0.05, sigma_growth=0.02, rho=0.5, num_simulations=1000, seed=42
    )

    assert len(betas) == 1000
    assert len(growths) == 1000

    # Check means are approximately correct
    assert np.mean(betas) == pytest.approx(1.0, abs=0.05)
    assert np.mean(growths) == pytest.approx(0.05, abs=0.01)

    # Check standard deviations
    assert np.std(betas) == pytest.approx(0.15, abs=0.02)
    assert np.std(growths) == pytest.approx(0.02, abs=0.005)


def test_generate_multivariate_samples_correlation():
    """Test that samples have correct correlation."""
    betas, growths = generate_multivariate_samples(
        mu_beta=1.0,
        sigma_beta=0.20,
        mu_growth=0.06,
        sigma_growth=0.03,
        rho=0.7,  # High correlation
        num_simulations=5000,
        seed=42,
    )

    # Calculate actual correlation
    correlation = np.corrcoef(betas, growths)[0, 1]
    assert correlation == pytest.approx(0.7, abs=0.05)


def test_generate_multivariate_samples_negative_correlation():
    """Test with negative correlation."""
    betas, growths = generate_multivariate_samples(
        mu_beta=1.0,
        sigma_beta=0.10,
        mu_growth=0.05,
        sigma_growth=0.02,
        rho=-0.5,  # Negative correlation
        num_simulations=2000,
        seed=42,
    )

    correlation = np.corrcoef(betas, growths)[0, 1]
    assert correlation == pytest.approx(-0.5, abs=0.08)


def test_generate_multivariate_samples_zero_correlation():
    """Test with zero correlation (independent)."""
    betas, growths = generate_multivariate_samples(
        mu_beta=1.0, sigma_beta=0.15, mu_growth=0.05, sigma_growth=0.02, rho=0.0, num_simulations=2000, seed=42
    )

    correlation = np.corrcoef(betas, growths)[0, 1]
    assert abs(correlation) < 0.1  # Should be near zero


def test_generate_multivariate_samples_invalid_rho():
    """Test that invalid rho raises ValueError."""
    with pytest.raises(ValueError, match="correlation coefficient"):
        generate_multivariate_samples(
            mu_beta=1.0,
            sigma_beta=0.10,
            mu_growth=0.05,
            sigma_growth=0.02,
            rho=1.5,  # Invalid: > 1
            num_simulations=100,
        )


def test_generate_multivariate_samples_negative_simulations():
    """Test that negative simulations raises ValueError."""
    with pytest.raises(ValueError, match="strictly positive"):
        generate_multivariate_samples(
            mu_beta=1.0, sigma_beta=0.10, mu_growth=0.05, sigma_growth=0.02, rho=0.5, num_simulations=-100
        )


def test_generate_multivariate_samples_zero_simulations():
    """Test that zero simulations raises ValueError."""
    with pytest.raises(ValueError, match="strictly positive"):
        generate_multivariate_samples(
            mu_beta=1.0, sigma_beta=0.10, mu_growth=0.05, sigma_growth=0.02, rho=0.5, num_simulations=0
        )


def test_generate_multivariate_samples_reproducibility():
    """Test that same seed produces same results."""
    betas1, growths1 = generate_multivariate_samples(
        mu_beta=1.0, sigma_beta=0.10, mu_growth=0.05, sigma_growth=0.02, rho=0.5, num_simulations=100, seed=123
    )

    betas2, growths2 = generate_multivariate_samples(
        mu_beta=1.0, sigma_beta=0.10, mu_growth=0.05, sigma_growth=0.02, rho=0.5, num_simulations=100, seed=123
    )

    np.testing.assert_array_equal(betas1, betas2)
    np.testing.assert_array_equal(growths1, growths2)


# ============================================================================
# TEST generate_independent_samples
# ============================================================================


def test_generate_independent_samples_basic():
    """Test basic independent sample generation."""
    samples = generate_independent_samples(mean=0.10, sigma=0.02, num_simulations=1000, seed=42)

    assert len(samples) == 1000
    assert np.mean(samples) == pytest.approx(0.10, abs=0.005)
    assert np.std(samples) == pytest.approx(0.02, abs=0.003)


def test_generate_independent_samples_with_clipping():
    """Test sample generation with clipping."""
    samples = generate_independent_samples(
        mean=0.10, sigma=0.05, num_simulations=1000, clip_min=0.05, clip_max=0.15, seed=42
    )

    # All samples should be within bounds
    assert np.all(samples >= 0.05)
    assert np.all(samples <= 0.15)


def test_generate_independent_samples_min_clip_only():
    """Test with only minimum clipping."""
    samples = generate_independent_samples(mean=0.05, sigma=0.03, num_simulations=1000, clip_min=0.01, seed=42)

    # All values should be >= minimum
    assert np.all(samples >= 0.01)


def test_generate_independent_samples_max_clip_only():
    """Test with only maximum clipping."""
    samples = generate_independent_samples(mean=0.15, sigma=0.05, num_simulations=1000, clip_max=0.20, seed=42)

    # No values above max
    assert np.all(samples <= 0.20)


def test_generate_independent_samples_reproducibility():
    """Test reproducibility with seed."""
    samples1 = generate_independent_samples(mean=0.08, sigma=0.02, num_simulations=100, seed=999)

    samples2 = generate_independent_samples(mean=0.08, sigma=0.02, num_simulations=100, seed=999)

    np.testing.assert_array_equal(samples1, samples2)


# ============================================================================
# TEST MonteCarloEngine.simulate_from_result
# ============================================================================


def test_simulate_from_result_disabled(mock_valuation_result_dcf, mock_params_mc_disabled):
    """Test that disabled MC returns empty output."""
    output = MonteCarloEngine.simulate_from_result(mock_valuation_result_dcf, mock_params_mc_disabled)

    assert isinstance(output, StochasticOutput)
    assert len(output.values) == 0
    assert len(output.quantiles) == 0


def test_simulate_from_result_dcf_enabled(mock_valuation_result_dcf, mock_params_mc_enabled):
    """Test DCF Monte Carlo simulation."""
    output = MonteCarloEngine.simulate_from_result(mock_valuation_result_dcf, mock_params_mc_enabled)

    assert isinstance(output, StochasticOutput)
    assert len(output.values) > 0

    # Check quantiles
    assert "p10" in output.quantiles
    assert "p50" in output.quantiles
    assert "p90" in output.quantiles
    assert "std" in output.quantiles
    assert "cv" in output.quantiles

    # Check ordering
    assert output.quantiles["p10"] <= output.quantiles["p50"]
    assert output.quantiles["p50"] <= output.quantiles["p90"]


def test_simulate_from_result_graham_enabled(mock_valuation_result_graham, mock_params_mc_enabled):
    """Test Graham Monte Carlo simulation."""
    output = MonteCarloEngine.simulate_from_result(mock_valuation_result_graham, mock_params_mc_enabled)

    assert len(output.values) > 0
    assert "p50" in output.quantiles

    # Values should be positive
    assert all(v > 0 for v in output.values)


def test_simulate_from_result_fcff_growth(mock_params_mc_enabled):
    """Test with FCFF Growth methodology."""
    result = Mock()
    result.intrinsic_value_per_share = 120.0
    request = Mock()
    request.mode = ValuationMethodology.FCFF_GROWTH
    result.request = request

    strategy_results = Mock()
    strategy_results.projected_flows = [100, 110, 120, 130, 140]
    strategy_results.discounted_terminal_value = 400

    capital_results = Mock()
    capital_results.net_debt_resolved = 500_000
    capital_results.enterprise_value = 1_500_000

    common_results = Mock()
    common_results.capital = capital_results

    results = Mock()
    results.strategy = strategy_results
    results.common = common_results

    result.results = results

    output = MonteCarloEngine.simulate_from_result(result, mock_params_mc_enabled)

    assert len(output.values) > 0


def test_simulate_from_result_fcff_normalized(mock_params_mc_enabled):
    """Test with FCFF Normalized methodology."""
    result = Mock()
    result.intrinsic_value_per_share = 110.0
    request = Mock()
    request.mode = ValuationMethodology.FCFF_NORMALIZED
    result.request = request

    strategy_results = Mock()
    strategy_results.projected_flows = [90, 95, 100, 105, 110]
    strategy_results.discounted_terminal_value = 350

    capital_results = Mock()
    capital_results.net_debt_resolved = 300_000
    capital_results.enterprise_value = 1_200_000

    common_results = Mock()
    common_results.capital = capital_results

    results = Mock()
    results.strategy = strategy_results
    results.common = common_results

    result.results = results

    output = MonteCarloEngine.simulate_from_result(result, mock_params_mc_enabled)

    assert len(output.values) > 0


def test_simulate_from_result_unsupported_model(mock_params_mc_enabled):
    """Test with unsupported model (fallback to generic volatility)."""
    result = Mock()
    result.intrinsic_value_per_share = 200.0
    request = Mock()
    request.mode = "SOME_OTHER_MODEL"  # Not in supported list
    result.request = request

    output = MonteCarloEngine.simulate_from_result(result, mock_params_mc_enabled)

    # Should use generic fallback
    assert len(output.values) > 0


def test_simulate_from_result_missing_shocks():
    """Test when shocks config is None (uses defaults)."""
    params = Mock()
    mc_config = Mock()
    mc_config.enabled = True
    mc_config.iterations = 500
    mc_config.shocks = None  # Missing
    extensions = Mock()
    extensions.monte_carlo = mc_config
    params.extensions = extensions

    rates = Mock()
    rates.beta = 1.0
    rates.risk_free_rate = 0.03
    rates.market_risk_premium = 0.07
    common = Mock()
    common.rates = rates
    common.capital = Mock()
    common.capital.shares_outstanding = 1_000_000
    params.common = common

    strategy = Mock()
    strategy.growth_rate_p1 = 0.06
    strategy.projection_years = 5
    params.strategy = strategy

    result = Mock()
    result.intrinsic_value_per_share = 100.0
    request = Mock()
    request.mode = "UNSUPPORTED"
    result.request = request

    output = MonteCarloEngine.simulate_from_result(result, params)

    # Should use default volatilities
    assert len(output.values) > 0


def test_simulate_from_result_filters_invalid_values(mock_valuation_result_dcf):
    """Test that invalid values (NaN, negative) are filtered out."""
    params = Mock()
    mc_config = Mock()
    mc_config.enabled = True
    mc_config.iterations = 100
    shocks = Mock()
    shocks.beta_volatility = 0.50  # High vol to potentially create negatives
    shocks.growth_volatility = 0.10
    shocks.eps_volatility = 0.20
    mc_config.shocks = shocks
    extensions = Mock()
    extensions.monte_carlo = mc_config
    params.extensions = extensions

    rates = Mock()
    rates.beta = 0.8
    rates.risk_free_rate = 0.03
    rates.market_risk_premium = 0.07
    common = Mock()
    common.rates = rates
    common.capital = Mock()
    common.capital.shares_outstanding = 1_000_000
    params.common = common

    strategy = Mock()
    strategy.growth_rate_p1 = 0.08
    strategy.projection_years = 5
    params.strategy = strategy

    output = MonteCarloEngine.simulate_from_result(mock_valuation_result_dcf, params)

    # All returned values should be valid and positive
    assert all(np.isfinite(v) for v in output.values)
    assert all(v > 0 for v in output.values)


def test_simulate_from_result_all_invalid_returns_empty():
    """Test that all invalid simulations return empty output."""
    # Create scenario that produces all invalid values (unlikely but test edge case)
    result = Mock()
    result.intrinsic_value_per_share = 0.0  # Base IV is 0
    request = Mock()
    request.mode = "UNSUPPORTED"
    result.request = request

    params = Mock()
    mc_config = Mock()
    mc_config.enabled = True
    mc_config.iterations = 10
    mc_config.shocks = None
    extensions = Mock()
    extensions.monte_carlo = mc_config
    params.extensions = extensions

    rates = Mock()
    rates.beta = 1.0
    rates.risk_free_rate = 0.03
    rates.market_risk_premium = 0.07
    common = Mock()
    common.rates = rates
    common.capital = Mock()
    common.capital.shares_outstanding = 1_000_000
    params.common = common

    strategy = Mock()
    strategy.growth_rate_p1 = 0.05
    strategy.projection_years = 5
    params.strategy = strategy

    # Force the generic simulation to create invalid values
    with (
        patch("src.computation.statistics.generate_multivariate_samples") as mock_samples,
        patch("src.computation.statistics.np.random.default_rng") as mock_rng,
    ):
        # Mock the multivariate samples to return valid arrays
        mock_samples.return_value = (np.array([np.nan] * 10), np.array([np.nan] * 10))
        # Mock RNG for generic fallback (shouldn't be reached with mocked samples)
        mock_gen = Mock()
        mock_gen.normal.return_value = np.array([np.nan] * 10)
        mock_rng.return_value = mock_gen

        output = MonteCarloEngine.simulate_from_result(result, params)

        # Should return empty due to invalid (NaN) values
        assert len(output.values) == 0
        assert len(output.quantiles) == 0


# ============================================================================
# TEST MonteCarloEngine._simulate_dcf_vector
# ============================================================================


def test_simulate_dcf_vector_basic(mock_valuation_result_dcf, mock_params_mc_enabled):
    """Test DCF vectorized simulation."""
    betas = np.array([1.0, 1.1, 0.9, 1.2, 0.8])
    growths = np.array([0.05, 0.06, 0.04, 0.07, 0.03])

    iv_vector = MonteCarloEngine._simulate_dcf_vector(mock_valuation_result_dcf, mock_params_mc_enabled, betas, growths)

    assert len(iv_vector) == 5
    # Should produce varying IVs
    assert not np.all(iv_vector == iv_vector[0])


def test_simulate_dcf_vector_missing_flows():
    """Test DCF simulation when flows are missing."""
    result = Mock()
    request = Mock()
    request.mode = ValuationMethodology.FCFF_STANDARD
    result.request = request

    strategy_results = Mock()
    strategy_results.projected_flows = []  # Empty
    strategy_results.discounted_terminal_value = 500_000

    capital_results = Mock()
    capital_results.enterprise_value = 1_000_000
    capital_results.net_debt_resolved = 0

    common_results = Mock()
    common_results.capital = capital_results

    results = Mock()
    results.strategy = strategy_results
    results.common = common_results
    result.results = results

    params = Mock()
    common = Mock()
    capital = Mock()
    capital.shares_outstanding = 1_000_000
    common.capital = capital
    rates = Mock()
    rates.risk_free_rate = 0.03
    rates.market_risk_premium = 0.07
    common.rates = rates
    params.common = common
    strategy = Mock()
    strategy.projection_years = 5
    params.strategy = strategy

    betas = np.array([1.0, 1.1])
    growths = np.array([0.05, 0.06])

    # Should handle gracefully (base_fcf becomes 0)
    iv_vector = MonteCarloEngine._simulate_dcf_vector(result, params, betas, growths)
    assert len(iv_vector) == 2


# ============================================================================
# TEST MonteCarloEngine._simulate_graham_vector
# ============================================================================


def test_simulate_graham_vector_basic(mock_valuation_result_graham):
    """Test Graham vectorized simulation."""
    growths = np.array([0.08, 0.10, 0.06, 0.12, 0.05])
    eps_vol = 0.10
    n = 5

    iv_vector = MonteCarloEngine._simulate_graham_vector(mock_valuation_result_graham, growths, eps_vol, n)

    assert len(iv_vector) == 5
    # Should produce varying IVs
    assert not np.all(iv_vector == iv_vector[0])


def test_simulate_graham_vector_missing_anchors():
    """Test Graham simulation with missing anchors."""
    result = Mock()
    result.intrinsic_value_per_share = 100.0
    request = Mock()
    request.mode = ValuationMethodology.GRAHAM
    result.request = request

    # Create a results structure that will raise AttributeError
    # when trying to access eps_used or aaa_yield_used
    results = Mock(spec=[])  # Empty spec so accessing any attribute raises AttributeError
    result.results = results

    growths = np.array([0.08, 0.10])
    eps_vol = 0.10
    n = 2

    # Should use defaults and handle gracefully
    iv_vector = MonteCarloEngine._simulate_graham_vector(result, growths, eps_vol, n)
    assert len(iv_vector) == 2
    assert all(np.isfinite(v) for v in iv_vector)


# ============================================================================
# TEST StochasticOutput
# ============================================================================


def test_stochastic_output_creation():
    """Test StochasticOutput creation."""
    values = [100.0, 110.0, 120.0, 130.0, 140.0]
    quantiles = {"p10": 105.0, "p50": 120.0, "p90": 135.0, "std": 15.0, "cv": 0.125}

    output = StochasticOutput(values=values, quantiles=quantiles)

    assert output.values == values
    assert output.quantiles == quantiles
    assert output.quantiles["p50"] == 120.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_full_monte_carlo_workflow_dcf(mock_valuation_result_dcf, mock_params_mc_enabled):
    """Integration test: Full MC workflow for DCF."""
    output = MonteCarloEngine.simulate_from_result(mock_valuation_result_dcf, mock_params_mc_enabled)

    # Should produce valid distribution
    assert len(output.values) > 500  # Most simulations should be valid

    # Check statistical consistency
    assert output.quantiles["p10"] < output.quantiles["p50"] < output.quantiles["p90"]
    assert output.quantiles["std"] > 0
    assert output.quantiles["cv"] >= 0

    # Median should be reasonable (could be affected by mock structure)
    assert output.quantiles["p50"] > 0


def test_full_monte_carlo_workflow_graham(mock_valuation_result_graham, mock_params_mc_enabled):
    """Integration test: Full MC workflow for Graham."""
    output = MonteCarloEngine.simulate_from_result(mock_valuation_result_graham, mock_params_mc_enabled)

    assert len(output.values) > 500
    assert output.quantiles["p50"] > 0
    assert output.quantiles["std"] > 0


def test_monte_carlo_with_different_iteration_counts(mock_valuation_result_dcf, mock_params_mc_enabled):
    """Test MC with different iteration counts."""
    # Small iteration count
    mock_params_mc_enabled.extensions.monte_carlo.iterations = 100
    output_small = MonteCarloEngine.simulate_from_result(mock_valuation_result_dcf, mock_params_mc_enabled)

    # Large iteration count
    mock_params_mc_enabled.extensions.monte_carlo.iterations = 5000
    output_large = MonteCarloEngine.simulate_from_result(mock_valuation_result_dcf, mock_params_mc_enabled)

    # Both should produce valid results
    assert len(output_small.values) > 0
    assert len(output_large.values) > len(output_small.values)
