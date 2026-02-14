"""
tests/integration/test_backtest.py

TEST SUITE: Backtest Runner (Historical Data Isolation)
======================================================
Role: Validates point-in-time data freezing & look-ahead bias prevention.
Coverage Target: src/valuation/options/backtest.py (0% → 90%+)
"""

import pandas as pd

from infra.data_providers.yahoo_raw_fetcher import RawFinancialData
from src.valuation.options.backtest import BacktestRunner


class TestBacktestRunner:
    """Test suite for BacktestRunner historical data isolation."""

    def setup_method(self):
        """Setup test fixtures for each test."""
        # Create sample financial DataFrames with year columns
        self.year_2021 = pd.Timestamp('2021-12-31')
        self.year_2022 = pd.Timestamp('2022-12-31')
        self.year_2023 = pd.Timestamp('2023-12-31')

        # Sample balance sheet with multiple years
        self.sample_bs = pd.DataFrame({
            self.year_2021: [100.0, 200.0],
            self.year_2022: [110.0, 220.0],
            self.year_2023: [120.0, 240.0]
        }, index=['Assets', 'Liabilities'])

        # Sample income statement
        self.sample_is = pd.DataFrame({
            self.year_2021: [1000.0, 100.0],
            self.year_2022: [1100.0, 110.0],
            self.year_2023: [1200.0, 120.0]
        }, index=['Revenue', 'Net Income'])

        # Sample cash flow statement
        self.sample_cf = pd.DataFrame({
            self.year_2021: [90.0, 10.0],
            self.year_2022: [100.0, 11.0],
            self.year_2023: [110.0, 12.0]
        }, index=['Operating CF', 'Capex'])

        # Sample price history with datetime index
        dates = pd.date_range('2021-01-01', '2023-12-31', freq='D')
        prices = [150.0 + i * 0.1 for i in range(len(dates))]
        self.sample_history = pd.DataFrame({
            'Close': prices,
            'Volume': [1000000] * len(dates)
        }, index=dates)

    def test_isolate_fiscal_year_valid_year(self):
        """Test isolation with valid year - all statements present."""
        raw_data = RawFinancialData(
            ticker="AAPL",
            info={"symbol": "AAPL"},
            balance_sheet=self.sample_bs,
            income_stmt=self.sample_is,
            cash_flow=self.sample_cf,
            quarterly_income_stmt=pd.DataFrame(),
            quarterly_cash_flow=pd.DataFrame(),
            history=self.sample_history,
            is_valid=True
        )

        result = BacktestRunner.isolate_fiscal_year(raw_data, 2022)

        assert result is not None
        assert result.ticker == "AAPL"
        assert result.is_valid is True

        # Check that only 2022 column is present in statements
        assert len(result.balance_sheet.columns) == 1
        assert result.balance_sheet.columns[0].year == 2022

        # Check history is truncated to 2022 and earlier
        assert result.history.index.max().year <= 2022
        assert result.history.index.min().year >= 2021

    def test_isolate_fiscal_year_missing_balance_sheet(self):
        """Test isolation when balance sheet is missing for target year."""
        # Create balance sheet without 2022
        bs_partial = pd.DataFrame({
            self.year_2021: [100.0, 200.0],
            self.year_2023: [120.0, 240.0]
        }, index=['Assets', 'Liabilities'])

        raw_data = RawFinancialData(
            ticker="AAPL",
            info={"symbol": "AAPL"},
            balance_sheet=bs_partial,
            income_stmt=self.sample_is,
            cash_flow=self.sample_cf,
            quarterly_income_stmt=pd.DataFrame(),
            quarterly_cash_flow=pd.DataFrame(),
            history=self.sample_history,
            is_valid=True
        )

        result = BacktestRunner.isolate_fiscal_year(raw_data, 2022)
        assert result is None

    def test_isolate_fiscal_year_missing_income_statement(self):
        """Test isolation when income statement is missing for target year."""
        # Create income statement without 2022
        is_partial = pd.DataFrame({
            self.year_2021: [1000.0, 100.0],
            self.year_2023: [1200.0, 120.0]
        }, index=['Revenue', 'Net Income'])

        raw_data = RawFinancialData(
            ticker="AAPL",
            info={"symbol": "AAPL"},
            balance_sheet=self.sample_bs,
            income_stmt=is_partial,
            cash_flow=self.sample_cf,
            quarterly_income_stmt=pd.DataFrame(),
            quarterly_cash_flow=pd.DataFrame(),
            history=self.sample_history,
            is_valid=True
        )

        result = BacktestRunner.isolate_fiscal_year(raw_data, 2022)
        assert result is None

    def test_isolate_fiscal_year_missing_cash_flow(self):
        """Test isolation when cash flow is missing for target year."""
        # Create cash flow without 2022
        cf_partial = pd.DataFrame({
            self.year_2021: [90.0, 10.0],
            self.year_2023: [110.0, 12.0]
        }, index=['Operating CF', 'Capex'])

        raw_data = RawFinancialData(
            ticker="AAPL",
            info={"symbol": "AAPL"},
            balance_sheet=self.sample_bs,
            income_stmt=self.sample_is,
            cash_flow=cf_partial,
            quarterly_income_stmt=pd.DataFrame(),
            quarterly_cash_flow=pd.DataFrame(),
            history=self.sample_history,
            is_valid=True
        )

        result = BacktestRunner.isolate_fiscal_year(raw_data, 2022)
        assert result is None

    def test_isolate_fiscal_year_empty_history(self):
        """Test isolation with empty price history."""
        raw_data = RawFinancialData(
            ticker="AAPL",
            info={"symbol": "AAPL"},
            balance_sheet=self.sample_bs,
            income_stmt=self.sample_is,
            cash_flow=self.sample_cf,
            quarterly_income_stmt=pd.DataFrame(),
            quarterly_cash_flow=pd.DataFrame(),
            history=pd.DataFrame(),  # Empty history
            is_valid=True
        )

        result = BacktestRunner.isolate_fiscal_year(raw_data, 2022)

        assert result is not None
        assert result.history.empty

    def test_get_historical_market_price_valid_year(self):
        """Test retrieving price for valid year."""
        price = BacktestRunner.get_historical_market_price(self.sample_history, 2022)

        # Should return the last closing price of 2022
        assert price > 0.0
        assert isinstance(price, float)

        # Verify it's from 2022
        year_2022_prices = self.sample_history[self.sample_history.index.year == 2022]
        expected_price = float(year_2022_prices['Close'].iloc[-1])
        assert price == expected_price

    def test_get_historical_market_price_empty_dataframe(self):
        """Test price retrieval with empty DataFrame."""
        empty_df = pd.DataFrame()
        price = BacktestRunner.get_historical_market_price(empty_df, 2022)
        assert price == 0.0

    def test_get_historical_market_price_none_dataframe(self):
        """Test price retrieval with None DataFrame."""
        price = BacktestRunner.get_historical_market_price(None, 2022)
        assert price == 0.0

    def test_get_historical_market_price_missing_year(self):
        """Test price retrieval for year not in data."""
        price = BacktestRunner.get_historical_market_price(self.sample_history, 2019)
        assert price == 0.0

    def test_get_historical_market_price_no_close_column(self):
        """Test price retrieval when 'Close' column is missing."""
        # Create DataFrame without 'Close' column
        dates = pd.date_range('2022-01-01', '2022-12-31', freq='D')
        df_no_close = pd.DataFrame({
            'AdjClose': [100.0] * len(dates),
            'Volume': [1000000] * len(dates)
        }, index=dates)

        price = BacktestRunner.get_historical_market_price(df_no_close, 2022)

        # Should use first available column
        assert price > 0.0
        assert price == 100.0

    def test_filter_df_by_year_valid(self):
        """Test filtering DataFrame by valid year."""
        result = BacktestRunner._filter_df_by_year(self.sample_bs, 2022)

        assert result is not None
        assert len(result.columns) == 1
        assert result.columns[0].year == 2022

        # Check values
        assert result.loc['Assets'].iloc[0] == 110.0
        assert result.loc['Liabilities'].iloc[0] == 220.0

    def test_filter_df_by_year_none_dataframe(self):
        """Test filtering with None DataFrame."""
        result = BacktestRunner._filter_df_by_year(None, 2022)
        assert result is None

    def test_filter_df_by_year_empty_dataframe(self):
        """Test filtering with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = BacktestRunner._filter_df_by_year(empty_df, 2022)
        assert result is None

    def test_filter_df_by_year_missing_year(self):
        """Test filtering for year not in DataFrame."""
        result = BacktestRunner._filter_df_by_year(self.sample_bs, 2019)
        assert result is None

    def test_filter_df_by_year_string_columns(self):
        """Test filtering with string column names containing year."""
        # Create DataFrame with string columns
        df_string = pd.DataFrame({
            '2021-12-31': [100.0, 200.0],
            '2022-12-31': [110.0, 220.0],
            '2023-12-31': [120.0, 240.0]
        }, index=['Assets', 'Liabilities'])

        result = BacktestRunner._filter_df_by_year(df_string, 2022)

        # Should still find the column with '2022' in it
        assert result is not None
        assert len(result.columns) == 1
        assert '2022' in result.columns[0]

    def test_isolate_fiscal_year_look_ahead_prevention(self):
        """Test that future data is properly excluded (look-ahead bias prevention)."""
        raw_data = RawFinancialData(
            ticker="AAPL",
            info={"symbol": "AAPL"},
            balance_sheet=self.sample_bs,
            income_stmt=self.sample_is,
            cash_flow=self.sample_cf,
            quarterly_income_stmt=pd.DataFrame(),
            quarterly_cash_flow=pd.DataFrame(),
            history=self.sample_history,
            is_valid=True
        )

        # Isolate to 2021
        result = BacktestRunner.isolate_fiscal_year(raw_data, 2021)

        assert result is not None

        # History should not contain any 2022 or 2023 data
        assert result.history.index.max().year <= 2021

        # Should have 2021 data
        assert (result.history.index.year == 2021).any()

        # Should NOT have 2022 or 2023 data
        assert not (result.history.index.year == 2022).any()
        assert not (result.history.index.year == 2023).any()
