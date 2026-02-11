"""
infra/data_providers/yahoo_raw_fetcher.py

YAHOO RAW FETCHER — API Extraction & Resilience Layer
=====================================================
Role: Low-level data acquisition from yfinance.
Responsibility: Fetches raw DataFrames and handles market-suffix retries.
Architecture: Infrastructure Layer (Stateless technical service).

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import yfinance as yf

from .extraction_utils import safe_api_call  #

logger = logging.getLogger(__name__)


@dataclass
class RawFinancialData:
    """
    Container for unprocessed financial data directly from the API.

    This DTO ensures that the Mapper receives a structured bundle
    instead of loose variables.
    """
    ticker: str
    info: dict[str, Any] = field(default_factory=dict)
    balance_sheet: pd.DataFrame = field(default_factory=pd.DataFrame)
    income_stmt: pd.DataFrame = field(default_factory=pd.DataFrame)
    cash_flow: pd.DataFrame = field(default_factory=pd.DataFrame)
    quarterly_income_stmt: pd.DataFrame = field(default_factory=pd.DataFrame)
    quarterly_cash_flow: pd.DataFrame = field(default_factory=pd.DataFrame)
    history: pd.DataFrame = field(default_factory=pd.DataFrame)
    is_valid: bool = False


class YahooRawFetcher:
    """
    Technical fetcher for Yahoo Finance data with built-in European resilience.
    """

    # DT-022: Common suffixes for European markets
    MARKET_SUFFIXES = [".PA", ".L", ".DE", ".AS", ".MI", ".MC", ".BR"]

    def fetch_ttm_snapshot(self, ticker: str) -> RawFinancialData:
        """
        Public entry point to fetch a complete raw dataset.
        Implements automatic suffix retry for European symbols.

        Parameters
        ----------
        ticker : str
            The stock symbol (e.g., 'AAPL', 'OR').

        Returns
        -------
        RawFinancialData
            The raw data container, marked as valid or invalid.
        """
        # 1. Attempt with the raw ticker provided
        data = self._execute_fetch(ticker)
        if data.is_valid:
            return data

        # 2. Resiliency: Retry with suffixes if no market suffix is present
        if "." not in ticker:
            for suffix in self.MARKET_SUFFIXES:
                alt_ticker = f"{ticker.upper()}{suffix}"
                logger.info(f"[Fetcher] Retrying with suffix fallback: {alt_ticker}")
                data = self._execute_fetch(alt_ticker)
                if data.is_valid:
                    return data

        return data

    @staticmethod
    def _execute_fetch(ticker: str) -> RawFinancialData:
        """
        Executes individual API calls wrapped in safety layers.

        Note: Marked as @staticmethod because it does not access instance state (self).
        This complies with 'King Code' standards and IDE linter rules.
        """
        try:
            yf_ticker = yf.Ticker(ticker)

            # Use safe_api_call from extraction_utils to handle timeouts
            info = safe_api_call(lambda: yf_ticker.info, f"Info:{ticker}")

            # Minimum requirement for a valid fetch (check identity)
            if not info or "shortName" not in info:
                return RawFinancialData(ticker=ticker, is_valid=False)

            return RawFinancialData(
                ticker=ticker,
                info=info,
                balance_sheet=safe_api_call(lambda: yf_ticker.balance_sheet, f"BS:{ticker}"),
                income_stmt=safe_api_call(lambda: yf_ticker.income_stmt, f"IS:{ticker}"),
                cash_flow=safe_api_call(lambda: yf_ticker.cash_flow, f"CF:{ticker}"),
                quarterly_income_stmt=safe_api_call(lambda: yf_ticker.quarterly_income_stmt, f"QIS:{ticker}"),
                quarterly_cash_flow=safe_api_call(lambda: yf_ticker.quarterly_cash_flow, f"QCF:{ticker}"),
                history=safe_api_call(lambda: yf_ticker.history(period="10y"), f"Hist:{ticker}"),
                is_valid=True
            )

        except Exception as e:
            logger.error(f"[Fetcher] Critical API failure for {ticker}: {e}")
            return RawFinancialData(ticker=ticker, is_valid=False)
