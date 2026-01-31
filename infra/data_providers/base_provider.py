"""
infra/data_providers/base_provider.py

ABSTRACT BASE INTERFACE — DATA PROVIDERS
========================================
Role: Strict contract for all financial and sectoral data providers.
Ensures that calculation engines remain decoupled from specific data sources.

Architecture: Provider Pattern (Interface Segregation)
Style: Numpy docstrings
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional

import pandas as pd

from src.models import Company, Parameters, MultiplesData


class DataProvider(ABC):
    """
    Strict abstract interface for financial data providers.

    Implementing classes (e.g., YahooFinanceProvider) must fulfill these
    contracts to ensure compatibility with the Audit and Valuation engines.
    """

    @abstractmethod
    def get_company_financials(self, ticker: str) -> Company:
        """
        Retrieves current financial snapshot (Balance Sheet, Income Stmt, Cash Flow)
        for a specific entity.

        Parameters
        ----------
        ticker : str
            The stock symbol to fetch.

        Returns
        -------
        Company
            Mapped and cleaned financial data structure.
        """
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """
        Retrieves historical price data (Adjusted Close) for technical
        and backtesting analysis.

        Parameters
        ----------
        ticker : str
            The stock symbol.
        period : str, default="5y"
            The lookback window (e.g., 1y, 5y, max).

        Returns
        -------
        pd.DataFrame
            Time-series data with 'Close' and 'Volume' columns.
        """
        raise NotImplementedError

    @abstractmethod
    def get_peer_multiples(self, ticker: str, manual_peers: Optional[List[str]] = None) -> MultiplesData:
        """
        Performs peer discovery and returns normalized valuation multiples.
        Used for Pillar 5 (Market Analysis) triangulation.

        Parameters
        ----------
        ticker : str
            Target company ticker for sector identification.
        manual_peers : Optional[List[str]], default=None
            List of specific tickers to override automatic discovery.

        Returns
        -------
        MultiplesData
            Aggregated peer multiples (P/E, EV/EBITDA) and source metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def get_company_financials_and_parameters(
        self,
        ticker: str,
        projection_years: int
    ) -> Tuple[Company, Parameters]:
        """
        'All-in-one' method for Automated Mode workflow.
        Fetches fundamental data and resolves localized macro/risk parameters.

        Parameters
        ----------
        ticker : str
            The stock symbol.
        projection_years : int
            The explicit forecast horizon (t).

        Returns
        -------
        Tuple[Company, Parameters]
            The baseline data required to launch a valuation request.
        """
        raise NotImplementedError