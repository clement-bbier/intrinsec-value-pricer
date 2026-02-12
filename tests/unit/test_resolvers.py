"""
tests/unit/test_resolvers.py

Tests for the ParameterResolver (Phase 2 — Data Integrity).

Validates:
- Cascade priority: Override > Snapshot > Fallback > Default
- No None output on critical fields (WACC inputs, growth rates)
- apply_resolved_params produces engine-safe parameters
"""

import pytest

from src.domain.models import (
    CompanyFinancials,
    DCFParameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    SOTPParameters,
    ScenarioParameters,
)
from src.valuation.resolvers.parameter_resolver import (
    ParameterResolver,
    ResolvedRates,
    ResolvedGrowth,
    _resolve,
)
from src.config.constants import SystemDefaults, MacroDefaults


@pytest.fixture
def bare_financials():
    """Financials with minimal data (many fields missing)."""
    return CompanyFinancials(
        ticker="BARE",
        currency="USD",
        current_price=50.0,
        shares_outstanding=1_000_000,
    )


@pytest.fixture
def full_financials():
    """Financials with complete data."""
    return CompanyFinancials(
        ticker="FULL",
        currency="USD",
        current_price=100.0,
        shares_outstanding=1_000_000,
        beta=1.3,
        total_debt=20_000_000,
        cash_and_equivalents=5_000_000,
        interest_expense=1_000_000,
    )


@pytest.fixture
def empty_params():
    """Parameters with all optional rates/growth as None."""
    return DCFParameters(
        rates=CoreRateParameters(),
        growth=GrowthParameters(projection_years=5),
        monte_carlo=MonteCarloConfig(enable_monte_carlo=False),
        sotp=SOTPParameters(enabled=False),
        scenarios=ScenarioParameters(enabled=False),
    )


@pytest.fixture
def full_params():
    """Parameters with all rates/growth explicitly set."""
    return DCFParameters(
        rates=CoreRateParameters(
            risk_free_rate=0.035,
            market_risk_premium=0.06,
            cost_of_debt=0.045,
            tax_rate=0.30,
            manual_beta=1.5,
        ),
        growth=GrowthParameters(
            fcf_growth_rate=0.08,
            perpetual_growth_rate=0.025,
            projection_years=7,
        ),
        monte_carlo=MonteCarloConfig(enable_monte_carlo=False),
        sotp=SOTPParameters(enabled=False),
        scenarios=ScenarioParameters(enabled=False),
    )


class TestResolveCascadeFunction:
    """Tests for the _resolve cascade helper."""

    def test_override_takes_priority(self):
        """Override (level 1) should take priority over all others."""
        result = _resolve(0.05, 0.04, 0.03, 0.02, "test_field")
        assert result == 0.05

    def test_snapshot_used_when_no_override(self):
        """Snapshot (level 2) should be used when override is None."""
        result = _resolve(None, 0.04, 0.03, 0.02, "test_field")
        assert result == 0.04

    def test_fallback_used_when_no_override_or_snapshot(self):
        """Fallback (level 3) should be used when override and snapshot are None."""
        result = _resolve(None, None, 0.03, 0.02, "test_field")
        assert result == 0.03

    def test_default_used_as_last_resort(self):
        """Default (level 4) should be used when all others are None."""
        result = _resolve(None, None, None, 0.02, "test_field")
        assert result == 0.02

    def test_zero_is_valid_override(self):
        """Zero should be treated as a valid value, not None."""
        result = _resolve(0.0, 0.04, 0.03, 0.02, "test_field")
        assert result == 0.0

    def test_return_type_is_float(self):
        """Result should always be a float."""
        result = _resolve(None, None, None, 0.05, "test_field")
        assert isinstance(result, float)


class TestResolveRates:
    """Tests for ParameterResolver.resolve_rates()."""

    def test_returns_resolved_rates_object(self, empty_params, bare_financials):
        """Should return a ResolvedRates dataclass."""
        result = ParameterResolver.resolve_rates(empty_params, bare_financials)
        assert isinstance(result, ResolvedRates)

    def test_no_none_in_resolved_rates(self, empty_params, bare_financials):
        """All fields in ResolvedRates should be non-None."""
        result = ParameterResolver.resolve_rates(empty_params, bare_financials)
        assert result.risk_free_rate is not None
        assert result.market_risk_premium is not None
        assert result.beta is not None
        assert result.cost_of_debt is not None
        assert result.tax_rate is not None

    def test_defaults_are_financially_sane(self, empty_params, bare_financials):
        """Default resolved values should be within sane financial ranges."""
        result = ParameterResolver.resolve_rates(empty_params, bare_financials)
        assert 0.0 < result.risk_free_rate < 0.15
        assert 0.0 < result.market_risk_premium < 0.15
        assert 0.0 < result.beta < 5.0
        assert 0.0 < result.cost_of_debt < 0.20
        assert 0.0 < result.tax_rate < 0.60

    def test_override_takes_priority(self, full_params, full_financials):
        """Expert overrides should take priority over snapshot data."""
        result = ParameterResolver.resolve_rates(full_params, full_financials)
        assert result.risk_free_rate == 0.035
        assert result.market_risk_premium == 0.06
        assert result.beta == 1.5  # manual_beta override
        assert result.cost_of_debt == 0.045
        assert result.tax_rate == 0.30

    def test_snapshot_beta_used_when_no_override(self, empty_params, full_financials):
        """Company beta from financials should be used when no manual override."""
        result = ParameterResolver.resolve_rates(empty_params, full_financials)
        assert result.beta == 1.3  # From financials.beta

    def test_default_beta_when_no_data(self, empty_params, bare_financials):
        """System default beta should be used when no data available."""
        result = ParameterResolver.resolve_rates(empty_params, bare_financials)
        assert result.beta == SystemDefaults.DEFAULT_BETA

    def test_system_defaults_match_constants(self, empty_params, bare_financials):
        """Resolved defaults should match SystemDefaults constants."""
        result = ParameterResolver.resolve_rates(empty_params, bare_financials)
        assert result.tax_rate == SystemDefaults.DEFAULT_TAX_RATE
        assert result.cost_of_debt == SystemDefaults.DEFAULT_COST_OF_DEBT


class TestResolveGrowth:
    """Tests for ParameterResolver.resolve_growth()."""

    def test_returns_resolved_growth_object(self, empty_params, bare_financials):
        """Should return a ResolvedGrowth dataclass."""
        result = ParameterResolver.resolve_growth(empty_params, bare_financials)
        assert isinstance(result, ResolvedGrowth)

    def test_no_none_in_resolved_growth(self, empty_params, bare_financials):
        """All fields in ResolvedGrowth should be non-None."""
        result = ParameterResolver.resolve_growth(empty_params, bare_financials)
        assert result.fcf_growth_rate is not None
        assert result.perpetual_growth_rate is not None

    def test_override_takes_priority(self, full_params, full_financials):
        """Expert overrides should take priority."""
        result = ParameterResolver.resolve_growth(full_params, full_financials)
        assert result.fcf_growth_rate == 0.08
        assert result.perpetual_growth_rate == 0.025

    def test_defaults_are_financially_sane(self, empty_params, bare_financials):
        """Default growth rates should be conservative."""
        result = ParameterResolver.resolve_growth(empty_params, bare_financials)
        assert -0.05 <= result.fcf_growth_rate <= 0.25
        assert 0.0 <= result.perpetual_growth_rate <= 0.05


class TestApplyResolvedParams:
    """Tests for ParameterResolver.apply_resolved_params()."""

    def test_returns_dcf_parameters(self, empty_params, bare_financials):
        """Should return a DCFParameters object."""
        result = ParameterResolver.apply_resolved_params(empty_params, bare_financials)
        assert isinstance(result, DCFParameters)

    def test_does_not_mutate_original(self, empty_params, bare_financials):
        """Original params should not be mutated."""
        original_rf = empty_params.rates.risk_free_rate
        ParameterResolver.apply_resolved_params(empty_params, bare_financials)
        assert empty_params.rates.risk_free_rate == original_rf

    def test_fills_none_rates(self, empty_params, bare_financials):
        """None rates should be replaced with resolved defaults."""
        result = ParameterResolver.apply_resolved_params(empty_params, bare_financials)
        assert result.rates.risk_free_rate is not None
        assert result.rates.market_risk_premium is not None
        assert result.rates.tax_rate is not None

    def test_fills_none_growth(self, empty_params, bare_financials):
        """None growth rates should be replaced with resolved defaults."""
        result = ParameterResolver.apply_resolved_params(empty_params, bare_financials)
        assert result.growth.fcf_growth_rate is not None
        assert result.growth.perpetual_growth_rate is not None

    def test_preserves_explicit_values(self, full_params, full_financials):
        """Explicitly set values should not be overwritten."""
        result = ParameterResolver.apply_resolved_params(full_params, full_financials)
        assert result.rates.risk_free_rate == 0.035
        assert result.rates.market_risk_premium == 0.06
        assert result.growth.fcf_growth_rate == 0.08
        assert result.growth.perpetual_growth_rate == 0.025

    def test_engine_safe_output(self, empty_params, bare_financials):
        """Output should be safe for engine consumption (no None on critical fields)."""
        result = ParameterResolver.apply_resolved_params(empty_params, bare_financials)

        # These are the critical fields that the engine accesses
        assert result.rates.risk_free_rate is not None
        assert result.rates.market_risk_premium is not None
        assert result.rates.tax_rate is not None
        assert result.growth.fcf_growth_rate is not None
        assert result.growth.perpetual_growth_rate is not None
        assert result.growth.projection_years > 0
