from abc import ABC, abstractmethod
import logging
import pandas as pd

from core.models import CompanyFinancials

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """
    Abstract base class for any market / fundamentals data provider.
    Provides consistent structured logging for all concrete providers.
    """

    @abstractmethod
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """
        Fetch and normalize all financial data required by the DCF engine
        for a given ticker.

        Must raise DataProviderError if:
        - data is missing,
        - ticker is invalid,
        - or fundamental inconsistencies are detected.

        Concrete providers should log:
        - all fields fetched (price, shares, debt, cash, FCF, beta, currency)
        - fallback usage
        - warnings for missing data
        - final normalized CompanyFinancials object
        """
        logger.debug("[BaseProvider] get_company_financials() called for %s", ticker)
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """
        Returns historical price data (DataFrame) with at least:
            - DatetimeIndex
            - 'close' column

        Must raise DataProviderError if:
        - there is no data,
        - missing columns,
        - API failure.

        Concrete providers should log:
        - ticker + period
        - size of returned DataFrame
        - fallback attempts
        """
        logger.debug("[BaseProvider] get_price_history() called for %s", ticker)
        raise NotImplementedError
