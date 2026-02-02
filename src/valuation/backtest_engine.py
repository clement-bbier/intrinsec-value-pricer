"""
infra/auditing/backtester.py

HISTORICAL VALIDATION ENGINE — Point-in-Time Isolation.
======================================================
Role: Simulates past valuations by freezing raw data at a specific fiscal date.
Prevents look-ahead bias by ensuring the engine only sees data available at that time.

Architecture: Auditing Infrastructure.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from src.i18n import DiagnosticTexts
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Engine responsible for historical data isolation.
    It "freezes" raw financial datasets to simulate past analytical environments.
    """

    @staticmethod
    def freeze_data_at_fiscal_year(raw_data: RawFinancialData, target_year: int) -> Optional[RawFinancialData]:
        """
        Creates a Point-in-Time snapshot of RawFinancialData for a specific fiscal year.

        Parameters
        ----------
        raw_data : RawFinancialData
            The full multi-year raw dataset from the provider.
        target_year : int
            The fiscal year to isolate (e.g., 2023).

        Returns
        -------
        Optional[RawFinancialData]
            A "frozen" object containing only data columns up to the target year.
        """
        logger.debug("[Backtest] Attempting Point-in-Time isolation for FY %s", target_year)

        # 1. Isolate specific fiscal year columns in financial statements
        frozen_bs = BacktestEngine._filter_df_by_year(raw_data.balance_sheet, target_year)
        frozen_is = BacktestEngine._filter_df_by_year(raw_data.income_stmt, target_year)
        frozen_cf = BacktestEngine._filter_df_by_year(raw_data.cash_flow, target_year)

        # Validation: Ensure all core statements are available for the target year
        if frozen_bs is None or frozen_is is None or frozen_cf is None:
            logger.warning(
                DiagnosticTexts.DATA_FIELD_MISSING_YEAR.format(
                    ticker=raw_data.ticker, field="Financial Statements", year=target_year
                )
            )
            return None

        # 2. Construct the "Frozen" object
        # The isolated columns are injected as the primary dataset (TTM)
        # so existing providers can process them without modification.
        return RawFinancialData(
            ticker=raw_data.ticker,
            info=raw_data.info.copy(),  # Note: Historical market price injected separately
            balance_sheet=frozen_bs,
            income_stmt=frozen_is,
            cash_flow=frozen_cf,
            quarterly_income_stmt=None,  # Quarterly data ignored for annual backtesting
            quarterly_cash_flow=None
        )

    @staticmethod
    def _filter_df_by_year(df: Optional[pd.DataFrame], year: int) -> Optional[pd.DataFrame]:
        """
        Extracts the column corresponding to the specified fiscal year.
        Yahoo Finance typically uses Datetime objects as column indexes.
        """
        if df is None or df.empty:
            return None

        # Lookup column matching the target_year
        target_col = None
        for col in df.columns:
            if hasattr(col, 'year') and col.year == year:
                target_col = col
                break

        if target_col is None:
            return None

        # Returns a DataFrame with a single column (the frozen snapshot)
        return df[[target_col]]

    @staticmethod
    def get_historical_price_at(price_hist: pd.DataFrame, target_year: int) -> float:
        """
        Retrieves the actual market closing price at the end of the target fiscal year.
        Used as the benchmark to compare calculated Intrinsic Value (IV) against market reality.
        """
        if price_hist.empty:
            return 0.0

        # Filter for the specific year
        year_mask = price_hist.index.year == target_year
        year_prices = price_hist[year_mask]

        if year_prices.empty:
            return 0.0

        # Retrieve the last available closing price of the year
        return float(year_prices['Close'].iloc[-1])