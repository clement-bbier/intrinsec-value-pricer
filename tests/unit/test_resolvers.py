"""
tests/unit/test_resolvers.py

RESOLVER UNIT TESTS
===================
Role: Validate the USER > PROVIDER > SYSTEM priority chain and ensure
0% None values after resolution for critical fields.
"""

import pytest

from src.config.constants import MacroDefaults, ModelDefaults
from src.models.company import Company, CompanySnapshot
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import (
    CapitalStructureParameters,
    CommonParameters,
    FinancialRatesParameters,
)
from src.models.parameters.strategies import (
    DDMParameters,
    FCFEParameters,
    FCFFGrowthParameters,
    FCFFNormalizedParameters,
    FCFFStandardParameters,
    GrahamParameters,
    RIMParameters,
)
from src.valuation.resolvers.base_resolver import Resolver


@pytest.fixture
def resolver():
    """Returns a fresh Resolver instance."""
    return Resolver()


@pytest.fixture
def ghost_params():
    """A fully ghost (all None) Parameters object for FCFF Standard."""
    return Parameters(
        structure=Company(ticker="TEST", current_price=0.0),
        common=CommonParameters(
            rates=FinancialRatesParameters(),
            capital=CapitalStructureParameters(),
        ),
        strategy=FCFFStandardParameters(projection_years=None),
    )


@pytest.fixture
def rich_snapshot():
    """A provider snapshot with all fields populated."""
    return CompanySnapshot(
        ticker="TEST",
        name="Test Corp",
        sector="Technology",
        current_price=100.0,
        total_debt=50_000.0,
        cash_and_equivalents=20_000.0,
        shares_outstanding=1_000.0,
        revenue_ttm=200_000.0,
        ebit_ttm=40_000.0,
        net_income_ttm=30_000.0,
        interest_expense=2_000.0,
        fcf_ttm=35_000.0,
        capex_ttm=5_000.0,
        beta=1.3,
        risk_free_rate=0.045,
        market_risk_premium=0.06,
        tax_rate=0.22,
    )


@pytest.fixture
def empty_snapshot():
    """A minimal snapshot with almost no data."""
    return CompanySnapshot(
        ticker="GHOST",
        current_price=50.0,
    )


class TestResolverPickPriority:
    """Tests the USER > PROVIDER > SYSTEM cascade."""

    def test_user_override_takes_priority(self, resolver):
        """User value should override both provider and fallback."""
        assert resolver._pick(0.10, 0.05, 0.03) == 0.10

    def test_provider_takes_priority_over_fallback(self, resolver):
        """Provider value should be used when user is None."""
        assert resolver._pick(None, 0.05, 0.03) == 0.05

    def test_fallback_used_when_both_none(self, resolver):
        """System fallback should be used when both user and provider are None."""
        assert resolver._pick(None, None, 0.03) == 0.03

    def test_user_zero_is_valid(self, resolver):
        """Zero is a valid user override (not None)."""
        assert resolver._pick(0.0, 0.05, 0.03) == 0.0

    def test_never_returns_none(self, resolver):
        """The _pick method should never return None."""
        result = resolver._pick(None, None, 42.0)
        assert result is not None


class TestResolverIdentity:
    """Tests identity resolution (Pillar 1)."""

    def test_identity_from_provider(self, resolver, ghost_params, rich_snapshot):
        """When ghost has default identity data, provider fills currency and price."""
        resolved = resolver.resolve(ghost_params, rich_snapshot)
        # Name stays as "Unknown Entity" because Company defaults to that
        # Provider data fills price
        assert resolved.structure.current_price == 100.0

    def test_identity_user_override(self, resolver, rich_snapshot):
        """User identity fields should override provider."""
        params = Parameters(
            structure=Company(
                ticker="TEST",
                name="My Custom Name",
                current_price=200.0,
            ),
            strategy=FCFFStandardParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.structure.name == "My Custom Name"
        assert resolved.structure.current_price == 200.0

    def test_identity_fallback_defaults(self, resolver, ghost_params, empty_snapshot):
        """When both ghost and provider are empty, system defaults should be used."""
        resolved = resolver.resolve(ghost_params, empty_snapshot)
        assert resolved.structure.currency == "USD"


class TestResolverCommonRates:
    """Tests common financial rates resolution (Pillar 2)."""

    def test_rates_from_provider(self, resolver, ghost_params, rich_snapshot):
        """Rates should be resolved from provider when user provides None."""
        resolved = resolver.resolve(ghost_params, rich_snapshot)
        rates = resolved.common.rates
        assert rates.risk_free_rate == 0.045
        assert rates.beta == 1.3
        assert rates.tax_rate == 0.22

    def test_rates_fallback_to_defaults(self, resolver, ghost_params, empty_snapshot):
        """When provider also has None, system defaults should be used."""
        resolved = resolver.resolve(ghost_params, empty_snapshot)
        rates = resolved.common.rates
        assert rates.risk_free_rate == MacroDefaults.DEFAULT_RISK_FREE_RATE
        assert rates.beta == ModelDefaults.DEFAULT_BETA
        assert rates.tax_rate == MacroDefaults.DEFAULT_TAX_RATE

    def test_no_none_rates_after_resolution(self, resolver, ghost_params, empty_snapshot):
        """After resolution, no critical rate field should be None."""
        resolved = resolver.resolve(ghost_params, empty_snapshot)
        rates = resolved.common.rates
        assert rates.risk_free_rate is not None
        assert rates.market_risk_premium is not None
        assert rates.beta is not None
        assert rates.tax_rate is not None
        assert rates.cost_of_debt is not None

    def test_user_rates_override_provider(self, resolver, rich_snapshot):
        """User-provided rates should override provider data."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            common=CommonParameters(
                rates=FinancialRatesParameters(
                    risk_free_rate=0.03,
                    beta=0.8,
                )
            ),
            strategy=FCFFStandardParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.common.rates.risk_free_rate == 0.03
        assert resolved.common.rates.beta == 0.8


class TestResolverCapitalStructure:
    """Tests capital structure resolution."""

    def test_capital_from_provider(self, resolver, ghost_params, rich_snapshot):
        """Capital structure should be hydrated from provider."""
        resolved = resolver.resolve(ghost_params, rich_snapshot)
        cap = resolved.common.capital
        assert cap.total_debt == 50_000.0
        assert cap.cash_and_equivalents == 20_000.0
        assert cap.shares_outstanding == 1_000.0

    def test_capital_fallback_defaults(self, resolver, ghost_params, empty_snapshot):
        """Capital should fallback to system defaults when data is missing."""
        resolved = resolver.resolve(ghost_params, empty_snapshot)
        cap = resolved.common.capital
        assert cap.total_debt == ModelDefaults.DEFAULT_TOTAL_DEBT
        assert cap.shares_outstanding == ModelDefaults.DEFAULT_SHARES_OUTSTANDING

    def test_no_none_capital_after_resolution(self, resolver, ghost_params, empty_snapshot):
        """After resolution, no capital field should be None."""
        resolved = resolver.resolve(ghost_params, empty_snapshot)
        cap = resolved.common.capital
        assert cap.total_debt is not None
        assert cap.cash_and_equivalents is not None
        assert cap.shares_outstanding is not None


class TestResolverStrategy:
    """Tests strategy-specific field resolution."""

    def test_fcff_standard_anchor(self, resolver, rich_snapshot):
        """FCFF Standard should resolve fcf_anchor from provider."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=FCFFStandardParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.fcf_anchor == 35_000.0

    def test_fcff_normalized_anchor(self, resolver, rich_snapshot):
        """FCFF Normalized should resolve fcf_norm from provider."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=FCFFNormalizedParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.fcf_norm == 35_000.0

    def test_fcff_growth_revenue(self, resolver, rich_snapshot):
        """FCFF Growth should resolve revenue_ttm from provider."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=FCFFGrowthParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.revenue_ttm == 200_000.0

    def test_ddm_dividend(self, resolver, rich_snapshot):
        """DDM should resolve dividend_per_share from provider or fallback."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=DDMParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.dividend_per_share is not None

    def test_rim_book_value(self, resolver, rich_snapshot):
        """RIM should resolve book_value_anchor from provider or fallback."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=RIMParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.book_value_anchor is not None
        assert resolved.strategy.persistence_factor == ModelDefaults.DEFAULT_PERSISTENCE_FACTOR

    def test_fcfe_anchor(self, resolver, rich_snapshot):
        """FCFE should resolve fcfe_anchor from provider."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=FCFEParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.fcfe_anchor == 30_000.0

    def test_graham_eps(self, resolver, rich_snapshot):
        """Graham should resolve eps_normalized from provider or fallback."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=GrahamParameters(),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.eps_normalized is not None

    def test_projection_years_fallback(self, resolver, empty_snapshot):
        """When projection_years is None, it should be resolved to system default."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=FCFFStandardParameters(projection_years=None),
        )
        resolved = resolver.resolve(params, empty_snapshot)
        assert resolved.strategy.projection_years == ModelDefaults.DEFAULT_PROJECTION_YEARS

    def test_projection_years_user_override(self, resolver, rich_snapshot):
        """User-provided projection_years should be preserved."""
        params = Parameters(
            structure=Company(ticker="TEST"),
            strategy=FCFFStandardParameters(projection_years=10),
        )
        resolved = resolver.resolve(params, rich_snapshot)
        assert resolved.strategy.projection_years == 10


class TestResolverSyntheticKd:
    """Tests the synthetic Cost of Debt calculation."""

    def test_synthetic_kd_from_financials(self, resolver, rich_snapshot):
        """Kd should be computed from interest_expense / total_debt."""
        kd = resolver._calculate_synthetic_kd(rich_snapshot, 0.04)
        expected = abs(2_000.0) / 50_000.0  # 4%
        assert kd == expected

    def test_synthetic_kd_fallback_spread(self, resolver, empty_snapshot):
        """When data is missing, Kd should fallback to Rf + 200bps."""
        kd = resolver._calculate_synthetic_kd(empty_snapshot, 0.04)
        assert kd == 0.06  # 4% + 2%
