"""
tests/unit/test_infra_macro.py

UNIT TESTS FOR MACRO DATA PROVIDERS
====================================
Role: Validates macro data provider interfaces and implementations.
Coverage: DefaultMacroProvider, MacroDataProvider abstract class.
Architecture: Infrastructure Layer Tests.
Style: Pytest with fixtures for snapshot creation.
"""

import pytest

from infra.macro.base_macro_provider import MacroDataProvider
from infra.macro.default_macro_provider import DefaultMacroProvider
from src.models.company import CompanySnapshot


class TestDefaultMacroProvider:
    """Test suite for DefaultMacroProvider implementation."""

    @pytest.fixture
    def provider(self):
        """Returns a DefaultMacroProvider instance."""
        return DefaultMacroProvider()

    @pytest.fixture
    def base_snapshot(self):
        """Returns a minimal CompanySnapshot for testing."""
        return CompanySnapshot(
            ticker="TEST", name="Test Company", sector="Technology", current_price=100.0, country="United States"
        )

    def test_hydrate_macro_data_fills_all_fields(self, provider, base_snapshot):
        """hydrate_macro_data() fills all required macro fields on the snapshot."""
        result = provider.hydrate_macro_data(base_snapshot)

        # Check that all macro fields are populated
        assert result.risk_free_rate is not None
        assert result.market_risk_premium is not None
        assert result.tax_rate is not None
        assert result.perpetual_growth_rate is not None

    def test_hydrate_macro_data_values_in_institutional_ranges(self, provider, base_snapshot):
        """After hydration, all values should be within institutional ranges."""
        result = provider.hydrate_macro_data(base_snapshot)

        # Risk-free rate: 0% to 20%
        assert 0.0 <= result.risk_free_rate <= 0.20

        # Market risk premium: 2% to 15%
        assert 0.02 <= result.market_risk_premium <= 0.15

        # Tax rate: 0% to 60%
        assert 0.0 <= result.tax_rate <= 0.60

        # Perpetual growth (inflation): 0% to 30%
        assert 0.0 <= result.perpetual_growth_rate <= 0.30

    def test_hydrate_with_none_country_uses_fallback(self, provider):
        """Hydration with snapshot where country=None should use fallback."""
        snapshot = CompanySnapshot(
            ticker="TEST", name="Test Company", sector="Technology", current_price=100.0, country=None
        )

        result = provider.hydrate_macro_data(snapshot)

        # Should still populate with default US values
        assert result.risk_free_rate is not None
        assert result.market_risk_premium is not None
        assert result.tax_rate is not None

    def test_hydrate_with_united_states_gives_us_rates(self, provider):
        """Hydration with country='United States' gives US-specific rates."""
        snapshot = CompanySnapshot(
            ticker="AAPL", name="Apple Inc.", sector="Technology", current_price=150.0, country="United States"
        )

        result = provider.hydrate_macro_data(snapshot)

        # Verify it's using US context (tax rate should be 0.21)
        assert result.tax_rate == 0.21
        assert result.risk_free_rate is not None
        assert result.market_risk_premium is not None

    def test_hydrate_with_france_gives_french_rates(self, provider):
        """Hydration with country='France' gives France-specific rates."""
        snapshot = CompanySnapshot(
            ticker="MC", name="LVMH", sector="Consumer Cyclical", current_price=800.0, country="France"
        )

        result = provider.hydrate_macro_data(snapshot)

        # Verify it's using French context (different from US)
        assert result.tax_rate != 0.21  # France has different tax rate
        assert result.risk_free_rate is not None

    def test_hydrate_preserves_existing_snapshot_fields(self, provider, base_snapshot):
        """Hydration should not overwrite non-macro fields."""
        original_ticker = base_snapshot.ticker
        original_price = base_snapshot.current_price

        result = provider.hydrate_macro_data(base_snapshot)

        assert result.ticker == original_ticker
        assert result.current_price == original_price


class TestMacroDataProviderAbstract:
    """Test suite for MacroDataProvider abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """MacroDataProvider is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            MacroDataProvider()

        # The error message should indicate it's an abstract class
        assert "abstract" in str(exc_info.value).lower() or "instantiate" in str(exc_info.value).lower()

    def test_default_macro_provider_is_subclass(self):
        """DefaultMacroProvider should be a proper subclass of MacroDataProvider."""
        assert issubclass(DefaultMacroProvider, MacroDataProvider)

    def test_default_macro_provider_implements_hydrate_method(self):
        """DefaultMacroProvider must implement the hydrate_macro_data method."""
        provider = DefaultMacroProvider()

        assert hasattr(provider, "hydrate_macro_data")
        assert callable(getattr(provider, "hydrate_macro_data"))
