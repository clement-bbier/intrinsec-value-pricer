"""
src/valuation/options/backtest.py

BACKTEST RUNNER — HISTORICAL DATA ISOLATION
===========================================
Role: Simulates past analytical environments by "freezing" raw data.
Architecture: Runner Pattern (Stateless).
Logic: Point-in-Time isolation to prevent look-ahead bias during validation.

Standard: SOLID, i18n Secured.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging

import pandas as pd

from infra.data_providers.yahoo_raw_fetcher import RawFinancialData

logger = logging.getLogger(__name__)


class BacktestRunner:
    """
    Orchestrates historical data isolation.

    This Runner acts as a 'Time Machine': it takes a complete raw dataset
    and produces a sliced version restricted to a specific fiscal year.
    """

    @staticmethod
    def isolate_fiscal_year(raw_data: RawFinancialData, target_year: int) -> RawFinancialData | None:
        """
        Creates a Point-in-Time snapshot of RawFinancialData for a specific fiscal year.
        """
        logger.debug("[Backtest] Isolation FY %s pour %s", target_year, raw_data.ticker)

        # 1. Statements Isolation
        frozen_bs = BacktestRunner._filter_df_by_year(raw_data.balance_sheet, target_year)
        frozen_is = BacktestRunner._filter_df_by_year(raw_data.income_stmt, target_year)
        frozen_cf = BacktestRunner._filter_df_by_year(raw_data.cash_flow, target_year)

        if frozen_bs is None or frozen_is is None or frozen_cf is None:
            return None

        # 2. History Isolation (Protection against look-ahead bias)
        # Only keep prices UP TO 12/31 of the target year.
        frozen_history = raw_data.history.copy()
        if not frozen_history.empty:
            # Truncate everything strictly after the target year
            frozen_history = frozen_history[frozen_history.index.year <= target_year]

        return RawFinancialData(
            ticker=raw_data.ticker,
            info=raw_data.info.copy(),
            balance_sheet=frozen_bs,
            income_stmt=frozen_is,
            cash_flow=frozen_cf,
            quarterly_income_stmt=pd.DataFrame(),
            quarterly_cash_flow=pd.DataFrame(),
            history=frozen_history,
            is_valid=True
        )

    @staticmethod
    def get_historical_market_price(price_hist: pd.DataFrame, target_year: int) -> float:
        """
        Retrieves the actual market closing price at the end of the target fiscal year.

        Parameters
        ----------
        price_hist : pd.DataFrame
            DataFrame containing 'Close' prices and a DatetimeIndex.
        target_year : int
            The year to inspect.

        Returns
        -------
        float
            The closing price on the last trading day of that year, or 0.0 if not found.
        """
        if price_hist is None or price_hist.empty:
            return 0.0

        try:
            # Filter for the specific year
            # Optim: Use boolean masking which is faster than string slicing
            year_mask = price_hist.index.year == target_year
            year_prices = price_hist[year_mask]

            if year_prices.empty:
                return 0.0

            # Retrieve the last available closing price of the year
            # Note: We prioritize 'Close' over 'Adj Close' for historical valuation comparison
            col = 'Close' if 'Close' in year_prices.columns else year_prices.columns[0]

            # Use iloc[-1] to get the last trading day (e.g., Dec 29th or 30th)
            return float(year_prices[col].iloc[-1])

        except (KeyError, IndexError, ValueError, AttributeError) as e:
            # [CORRECTION] Catching specific Pandas/Data errors only
            logger.warning("[Backtest] Failed to extract price for year %s: %s", target_year, e)
            return 0.0

    @staticmethod
    def _filter_df_by_year(df: pd.DataFrame | None, year: int) -> pd.DataFrame | None:
        """
        Helper: Extracts the column corresponding to the specified fiscal year.
        """
        if df is None or df.empty:
            return None

        # Lookup column matching the target_year
        target_col = None
        for col in df.columns:
            # Handle standard Datetime objects in columns
            if hasattr(col, 'year') and col.year == year:
                target_col = col
                break
            # Handle string columns if data was parsed differently (fallback)
            elif isinstance(col, str) and str(year) in col:
                target_col = col
                break

        if target_col is None:
            return None

        # Returns a DataFrame with a single column (the frozen snapshot)
        return df[[target_col]]
