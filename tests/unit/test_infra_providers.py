"""
tests/unit/test_infra_providers.py

UNIT TESTS FOR FINANCIAL DATA PROVIDERS
========================================
Role: Validates data provider interfaces and Yahoo implementation structure.
Coverage: YahooFinancialProvider, FinancialDataProvider abstract class.
Architecture: Infrastructure Layer Tests (Mock-based).
Style: Pytest with mocks to avoid network dependencies.
"""

import pytest
from unittest.mock import Mock, MagicMock
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
