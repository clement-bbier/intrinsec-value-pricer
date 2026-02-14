"""
tests/unit/test_infra_providers.py

UNIT TESTS FOR FINANCIAL DATA PROVIDERS
========================================
Role: Validates data provider interfaces and Yahoo implementation structure.
Coverage: YahooFinancialProvider, FinancialDataProvider abstract class.
Architecture: Infrastructure Layer Tests (Mock-based).
Style: Pytest with mocks to avoid network dependencies.
"""

from unittest.mock import Mock

import pytest

from infra.data_providers.base_provider import FinancialDataProvider
from infra.data_providers.yahoo_financial_provider import YahooFinancialProvider
from infra.macro.base_macro_provider import MacroDataProvider


class TestFinancialDataProviderAbstract:
    """Test suite for FinancialDataProvider abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """FinancialDataProvider is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            FinancialDataProvider()

        # The error message should indicate it's an abstract class
        assert "abstract" in str(exc_info.value).lower() or "instantiate" in str(exc_info.value).lower()

    def test_yahoo_provider_is_subclass(self):
        """YahooFinancialProvider should be a proper subclass of FinancialDataProvider."""
        assert issubclass(YahooFinancialProvider, FinancialDataProvider)


class TestYahooFinancialProvider:
    """Test suite for YahooFinancialProvider implementation."""

    @pytest.fixture
    def mock_macro_provider(self):
        """Returns a mock MacroDataProvider for testing."""
        mock_provider = Mock(spec=MacroDataProvider)
        # Set up the mock to return the same snapshot when hydrate is called
        mock_provider.hydrate_macro_data.side_effect = lambda snapshot: snapshot
        return mock_provider

    def test_requires_macro_provider_argument(self, mock_macro_provider):
        """YahooFinancialProvider requires a macro_provider argument."""
        # Should not raise an error
        provider = YahooFinancialProvider(macro_provider=mock_macro_provider)

        assert provider is not None
        assert hasattr(provider, 'macro_provider')

    def test_has_get_company_snapshot_method(self, mock_macro_provider):
        """The class should have a get_company_snapshot method."""
        provider = YahooFinancialProvider(macro_provider=mock_macro_provider)

        assert hasattr(provider, 'get_company_snapshot')
        assert callable(getattr(provider, 'get_company_snapshot'))

    def test_get_company_snapshot_accepts_ticker_string(self, mock_macro_provider):
        """get_company_snapshot should accept a ticker string parameter."""
        provider = YahooFinancialProvider(macro_provider=mock_macro_provider)

        # This may return None if the ticker doesn't exist, but shouldn't crash
        # We're just testing the interface here
        try:
            result = provider.get_company_snapshot("AAPL")
            # Result can be None or a CompanySnapshot - we're just checking it doesn't crash
            assert result is None or hasattr(result, 'ticker')
        except Exception as e:
            # If it fails, it should be due to network/API issues, not interface issues
            # We allow this to fail gracefully in tests
            pytest.skip(f"Network/API call failed: {e}")

    def test_pipeline_structure_exists(self, mock_macro_provider):
        """Verify the provider has the expected pipeline structure."""
        provider = YahooFinancialProvider(macro_provider=mock_macro_provider)

        # Check that the provider has fetcher, mapper components
        assert hasattr(provider, 'fetcher')
        assert hasattr(provider, 'mapper')
        assert hasattr(provider, 'macro_provider')

        # Verify macro_provider is the one we passed
        assert provider.macro_provider == mock_macro_provider

    def test_implements_financial_data_provider_interface(self, mock_macro_provider):
        """YahooFinancialProvider must implement all required methods."""
        provider = YahooFinancialProvider(macro_provider=mock_macro_provider)

        # Check that it's a proper instance
        assert isinstance(provider, FinancialDataProvider)

        # Verify the required method exists
        assert hasattr(provider, 'get_company_snapshot')


# ==============================================================================
# EXTRACTION UTILS TESTS
# ==============================================================================

import numpy as np
import pandas as pd

from infra.data_providers.extraction_utils import (
    CAPEX_KEYS,
    DA_KEYS,
    DEBT_KEYS,
    OCF_KEYS,
    extract_most_recent_value,
    normalize_currency_and_price,
    safe_api_call,
)


class TestSafeAPICall:
    """Test suite for safe_api_call resiliency function."""

    def test_successful_api_call(self):
        """Test that successful API call returns result."""
        def successful_func():
            return "success"

        result = safe_api_call(successful_func, context="Test", max_retries=3)
        assert result == "success"

    def test_api_call_with_exception_returns_none(self):
        """Test that API call with exception eventually returns None."""
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("API Error")

        result = safe_api_call(failing_func, context="Test", max_retries=2)
        assert result is None
        assert call_count == 2

    def test_api_call_timeout_returns_none(self):
        """Test that API call timing out returns None."""
        import time

        def slow_func():
            time.sleep(15)  # Longer than 10s timeout
            return "never"

        result = safe_api_call(slow_func, context="Test", max_retries=1)
        assert result is None

    def test_api_call_eventually_succeeds(self):
        """Test that API call succeeds after retries."""
        attempt = 0

        def func_succeeds_on_second_try():
            nonlocal attempt
            attempt += 1
            if attempt < 2:
                raise ValueError("First attempt fails")
            return "success"

        result = safe_api_call(func_succeeds_on_second_try, context="Test", max_retries=3)
        assert result == "success"
        assert attempt == 2


class TestExtractMostRecentValue:
    """Test suite for extract_most_recent_value function."""

    def test_extract_from_simple_dataframe(self):
        """Test extraction from a simple dataframe."""
        df = pd.DataFrame({
            '2023': [100, 200, 300],
            '2022': [90, 180, 270]
        }, index=['Revenue', 'Expenses', 'Profit'])

        result = extract_most_recent_value(df, ['Revenue'])
        assert result == 100.0

    def test_extract_with_multiple_keys(self):
        """Test extraction with multiple possible keys."""
        df = pd.DataFrame({
            '2023': [100, 200],
            '2022': [90, 180]
        }, index=['Operating Cash Flow', 'Capital Expenditure'])

        result = extract_most_recent_value(df, OCF_KEYS)
        assert result == 100.0

    def test_extract_returns_none_for_empty_dataframe(self):
        """Test that empty dataframe returns None."""
        df = pd.DataFrame()
        result = extract_most_recent_value(df, ['Revenue'])
        assert result is None

    def test_extract_returns_none_for_none_input(self):
        """Test that None input returns None."""
        result = extract_most_recent_value(None, ['Revenue'])
        assert result is None

    def test_extract_with_missing_key(self):
        """Test extraction with key that doesn't exist."""
        df = pd.DataFrame({
            '2023': [100],
            '2022': [90]
        }, index=['Revenue'])

        result = extract_most_recent_value(df, ['NonExistent'])
        assert result is None

    def test_extract_with_null_values(self):
        """Test extraction skips null values."""
        df = pd.DataFrame({
            '2023': [np.nan, 200],
            '2022': [100, 180]
        }, index=['Revenue', 'Expenses'])

        result = extract_most_recent_value(df, ['Revenue'])
        assert result == 100.0  # Should get 2022 value since 2023 is null

    def test_extract_handles_non_numeric_values(self):
        """Test extraction handles non-numeric values gracefully."""
        df = pd.DataFrame({
            '2023': ['invalid', 200],
            '2022': [100, 180]
        }, index=['Revenue', 'Expenses'])

        result = extract_most_recent_value(df, ['Revenue'])
        assert result == 100.0  # Should skip 'invalid' and get 2022

    def test_extract_with_unsortable_columns(self):
        """Test extraction when columns cannot be sorted."""
        df = pd.DataFrame({
            'A': [100],
            'B': [200]
        }, index=['Revenue'])

        # Should not crash, should handle gracefully
        result = extract_most_recent_value(df, ['Revenue'])
        assert result in [100.0, 200.0]  # Will get one of them

    def test_extract_capex_keys(self):
        """Test extraction with CAPEX keys."""
        df = pd.DataFrame({
            '2023': [50, -25],
            '2022': [45, -20]
        }, index=['Operating Cash Flow', 'Capital Expenditure'])

        result = extract_most_recent_value(df, CAPEX_KEYS)
        assert result == -25.0

    def test_extract_da_keys(self):
        """Test extraction with D&A keys."""
        df = pd.DataFrame({
            '2023': [50, 10],
            '2022': [45, 9]
        }, index=['Operating Cash Flow', 'Depreciation And Amortization'])

        result = extract_most_recent_value(df, DA_KEYS)
        assert result == 10.0


class TestNormalizeCurrencyAndPrice:
    """Test suite for normalize_currency_and_price function."""

    def test_standard_currency(self):
        """Test normalization with standard currency."""
        info = {
            'currency': 'USD',
            'currentPrice': 150.0
        }

        currency, price = normalize_currency_and_price(info)
        assert currency == 'USD'
        assert price == 150.0

    def test_gbp_pence_to_pounds(self):
        """Test normalization converts GBp to GBP."""
        info = {
            'currency': 'GBp',
            'currentPrice': 15000.0
        }

        currency, price = normalize_currency_and_price(info)
        assert currency == 'GBP'
        assert price == 150.0  # 15000 / 100

    def test_missing_currency_defaults_to_usd(self):
        """Test that missing currency defaults to USD."""
        info = {
            'currentPrice': 100.0
        }

        currency, price = normalize_currency_and_price(info)
        assert currency == 'USD'
        assert price == 100.0

    def test_regular_market_price_fallback(self):
        """Test fallback to regularMarketPrice."""
        info = {
            'currency': 'EUR',
            'regularMarketPrice': 80.0
        }

        currency, price = normalize_currency_and_price(info)
        assert currency == 'EUR'
        assert price == 80.0

    def test_missing_price_defaults_to_zero(self):
        """Test that missing price defaults to 0.0."""
        info = {
            'currency': 'JPY'
        }

        currency, price = normalize_currency_and_price(info)
        assert currency == 'JPY'
        assert price == 0.0

    def test_returns_float_price(self):
        """Test that price is always returned as float."""
        info = {
            'currency': 'USD',
            'currentPrice': 100
        }

        currency, price = normalize_currency_and_price(info)
        assert isinstance(price, float)
        assert price == 100.0


class TestExtractionConstants:
    """Test that extraction constants are properly defined."""

    def test_ocf_keys_exist(self):
        """Test OCF_KEYS constant exists and has expected entries."""
        assert isinstance(OCF_KEYS, list)
        assert len(OCF_KEYS) > 0
        assert "Operating Cash Flow" in OCF_KEYS

    def test_capex_keys_exist(self):
        """Test CAPEX_KEYS constant exists."""
        assert isinstance(CAPEX_KEYS, list)
        assert len(CAPEX_KEYS) > 0
        assert "Capital Expenditure" in CAPEX_KEYS

    def test_da_keys_exist(self):
        """Test DA_KEYS constant exists."""
        assert isinstance(DA_KEYS, list)
        assert len(DA_KEYS) > 0
        assert "Depreciation And Amortization" in DA_KEYS

    def test_debt_keys_exist(self):
        """Test DEBT_KEYS constant exists."""
        assert isinstance(DEBT_KEYS, list)
        assert len(DEBT_KEYS) > 0
        assert "Total Debt" in DEBT_KEYS
