import pytest

from infra.data_providers.yahoo_provider import YahooFinanceProvider
from core.models import CompanyFinancials
from core.exceptions import DataProviderError


@pytest.mark.integration
def test_yahoo_provider_company_financials_aapl():
    provider = YahooFinanceProvider()

    try:
        cf = provider.get_company_financials("AAPL")
    except DataProviderError as exc:
        pytest.skip(f"Skipping: Yahoo data incomplete for AAPL ({exc})")

    assert isinstance(cf, CompanyFinancials)
    assert cf.ticker == "AAPL"
    assert cf.current_price > 0
    assert cf.shares_outstanding > 0


@pytest.mark.integration
def test_yahoo_provider_price_history_aapl():
    provider = YahooFinanceProvider()

    try:
        hist = provider.get_price_history("AAPL")
    except DataProviderError as exc:
        pytest.skip(f"Skipping: Yahoo price history unavailable for AAPL ({exc})")

    assert not hist.empty
    assert "close" in hist.columns
