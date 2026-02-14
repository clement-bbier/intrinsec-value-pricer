"""
tests/unit/test_extension_resolver.py

EXTENSION RESOLVER UNIT TESTS
==============================
Role: Validate the ExtensionResolver hydration logic for optional modules.
Coverage target: >85% for src/valuation/resolvers/options.py.
"""

import pytest

from src.config.constants import (
    BacktestDefaults,
    MonteCarloDefaults,
    SensitivityDefaults,
    SOTPDefaults,
)
from src.models.parameters.options import (
    BacktestParameters,
    ExtensionBundleParameters,
    MCParameters,
    PeersParameters,
    ScenarioParameters,
    ScenariosParameters,
    SensitivityParameters,
    SOTPParameters,
)
from src.valuation.resolvers.options import ExtensionResolver


@pytest.fixture
def resolver():
    """Returns a fresh ExtensionResolver instance."""
    return ExtensionResolver()


class TestMonteCarloResolution:
    """Tests Monte Carlo parameter resolution."""

    def test_disabled_skips_resolution(self, resolver):
        """When disabled, iterations should keep its default value."""
        params = MCParameters(enabled=False)
        resolver._resolve_monte_carlo(params)
        assert params.iterations == MonteCarloDefaults.DEFAULT_SIMULATIONS

    def test_enabled_keeps_default_iterations(self, resolver):
        """When enabled, default iterations should remain at model default."""
        params = MCParameters(enabled=True)
        resolver._resolve_monte_carlo(params)
        assert params.iterations == MonteCarloDefaults.DEFAULT_SIMULATIONS

    def test_user_iterations_preserved(self, resolver):
        """When user provides iterations, they should be preserved."""
        params = MCParameters(enabled=True, iterations=10_000)
        resolver._resolve_monte_carlo(params)
        assert params.iterations == 10_000


class TestSensitivityResolution:
    """Tests Sensitivity parameter resolution."""

    def test_disabled_keeps_defaults(self, resolver):
        """When disabled, parameters should keep model defaults."""
        params = SensitivityParameters(enabled=False)
        resolver._resolve_sensitivity(params)
        assert params.steps == SensitivityDefaults.DEFAULT_STEPS

    def test_enabled_preserves_defaults(self, resolver):
        """When enabled, default values should remain from model defaults."""
        params = SensitivityParameters(enabled=True)
        resolver._resolve_sensitivity(params)
        assert params.steps == SensitivityDefaults.DEFAULT_STEPS

    def test_default_wacc_span_applied(self, resolver):
        """When enabled, default wacc_span should be present."""
        params = SensitivityParameters(enabled=True)
        resolver._resolve_sensitivity(params)
        assert params.wacc_span == SensitivityDefaults.DEFAULT_WACC_SPAN

    def test_default_growth_span_applied(self, resolver):
        """When enabled, default growth_span should be present."""
        params = SensitivityParameters(enabled=True)
        resolver._resolve_sensitivity(params)
        assert params.growth_span == SensitivityDefaults.DEFAULT_GROWTH_SPAN

    def test_user_values_preserved(self, resolver):
        """User-provided values should not be overwritten."""
        params = SensitivityParameters(enabled=True, steps=7, wacc_span=200.0, growth_span=100.0)
        resolver._resolve_sensitivity(params)
        assert params.steps == 7
        assert params.wacc_span == 2.0
        assert params.growth_span == 1.0


class TestScenariosResolution:
    """Tests Scenarios parameter resolution."""

    def test_disabled_skips_resolution(self, resolver):
        """When disabled, cases should remain empty."""
        params = ScenariosParameters(enabled=False)
        resolver._resolve_scenarios(params)
        assert len(params.cases) == 0

    def test_empty_cases_injects_default(self, resolver):
        """When enabled but empty, a default Base Case should be injected."""
        params = ScenariosParameters(enabled=True, cases=[])
        resolver._resolve_scenarios(params)
        assert len(params.cases) == 1
        assert params.cases[0].name == "Base Case"
        assert params.cases[0].probability == 1.0

    def test_existing_cases_preserved(self, resolver):
        """When enabled with existing cases, they should be preserved."""
        cases = [
            ScenarioParameters(name="Bull", probability=0.3),
            ScenarioParameters(name="Bear", probability=0.7),
        ]
        params = ScenariosParameters(enabled=True, cases=cases)
        resolver._resolve_scenarios(params)
        assert len(params.cases) == 2


class TestBacktestResolution:
    """Tests Backtest parameter resolution."""

    def test_disabled_keeps_defaults(self, resolver):
        """When disabled, lookback_years should keep model default."""
        params = BacktestParameters(enabled=False)
        resolver._resolve_backtest(params)
        assert params.lookback_years == BacktestDefaults.DEFAULT_LOOKBACK_YEARS

    def test_enabled_preserves_defaults(self, resolver):
        """When enabled, default lookback_years should remain."""
        params = BacktestParameters(enabled=True)
        resolver._resolve_backtest(params)
        assert params.lookback_years == BacktestDefaults.DEFAULT_LOOKBACK_YEARS

    def test_user_lookback_preserved(self, resolver):
        """User-provided lookback_years should be preserved."""
        params = BacktestParameters(enabled=True, lookback_years=7)
        resolver._resolve_backtest(params)
        assert params.lookback_years == 7


class TestPeersResolution:
    """Tests Peers parameter resolution."""

    def test_disabled_skips_resolution(self, resolver):
        """When disabled, no warnings should be raised."""
        params = PeersParameters(enabled=False)
        resolver._resolve_peers(params)

    def test_enabled_no_tickers_logs_warning(self, resolver):
        """When enabled without tickers, resolver should handle gracefully."""
        params = PeersParameters(enabled=True, tickers=[])
        resolver._resolve_peers(params)
        assert len(params.tickers) == 0

    def test_enabled_with_tickers_below_minimum(self, resolver):
        """When enabled with few tickers, resolver should handle gracefully."""
        params = PeersParameters(enabled=True, tickers=["MSFT"])
        resolver._resolve_peers(params)
        assert len(params.tickers) == 1

    def test_enabled_with_sufficient_tickers(self, resolver):
        """With enough tickers, no issue should arise."""
        params = PeersParameters(enabled=True, tickers=["MSFT", "GOOGL", "META"])
        resolver._resolve_peers(params)
        assert len(params.tickers) == 3


class TestSOTPResolution:
    """Tests SOTP parameter resolution."""

    def test_disabled_keeps_defaults(self, resolver):
        """When disabled, discount should keep model default."""
        params = SOTPParameters(enabled=False)
        resolver._resolve_sotp(params)
        assert params.conglomerate_discount == SOTPDefaults.DEFAULT_CONGLOMERATE_DISCOUNT

    def test_enabled_preserves_defaults(self, resolver):
        """When enabled, default discount should remain."""
        params = SOTPParameters(enabled=True)
        resolver._resolve_sotp(params)
        assert params.conglomerate_discount == SOTPDefaults.DEFAULT_CONGLOMERATE_DISCOUNT

    def test_user_discount_preserved(self, resolver):
        """User-provided discount should be preserved."""
        params = SOTPParameters(enabled=True, conglomerate_discount=15.0)
        resolver._resolve_sotp(params)
        assert params.conglomerate_discount == 0.15


class TestFullBundleResolution:
    """Tests the full bundle resolution orchestration."""

    def test_resolve_returns_bundle(self, resolver):
        """The resolve method should return the hydrated bundle."""
        bundle = ExtensionBundleParameters()
        result = resolver.resolve(bundle)
        assert result is bundle

    def test_resolve_with_all_enabled(self, resolver):
        """Full resolution with all modules enabled should not raise."""
        bundle = ExtensionBundleParameters(
            monte_carlo=MCParameters(enabled=True),
            sensitivity=SensitivityParameters(enabled=True),
            scenarios=ScenariosParameters(enabled=True),
            backtest=BacktestParameters(enabled=True),
            peers=PeersParameters(enabled=True, tickers=["MSFT", "GOOGL"]),
            sotp=SOTPParameters(enabled=True),
        )
        result = resolver.resolve(bundle)
        assert result.monte_carlo.iterations == MonteCarloDefaults.DEFAULT_SIMULATIONS
        assert result.sensitivity.steps == SensitivityDefaults.DEFAULT_STEPS
        assert result.backtest.lookback_years == BacktestDefaults.DEFAULT_LOOKBACK_YEARS
        assert result.sotp.conglomerate_discount == SOTPDefaults.DEFAULT_CONGLOMERATE_DISCOUNT

    def test_resolve_with_all_disabled(self, resolver):
        """Full resolution with all modules disabled should not raise."""
        bundle = ExtensionBundleParameters()
        result = resolver.resolve(bundle)
        assert result.monte_carlo.enabled is False
        assert result.sensitivity.enabled is False
