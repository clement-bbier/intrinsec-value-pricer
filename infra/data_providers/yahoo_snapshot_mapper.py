"""
infra/data_providers/yahoo_snapshot_mapper.py

YAHOO SNAPSHOT MAPPER — Data Translation Layer
==============================================
Role: Specialized mapper that extracts and reconstructs financial metrics
      from raw Yahoo DataFrames into the CompanySnapshot DTO.
Responsibility: Technical mapping and TTM reconstruction. No business logic.

Architecture: Data Mapper Pattern.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging

import pandas as pd

from infra.data_providers.extraction_utils import (
    CAPEX_KEYS,
    DEBT_KEYS,
    OCF_KEYS,
    extract_most_recent_value,
    normalize_currency_and_price,
)
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData
from src.models.company import CompanySnapshot

logger = logging.getLogger(__name__)


class YahooSnapshotMapper:
    """
    Handles the technical conversion between raw Yahoo payloads and
    the standardized CompanySnapshot DTO.
    """

    def map_to_snapshot(self, raw: RawFinancialData) -> CompanySnapshot:
        """
        Extracts and reconstructs financial metrics from raw DataFrames.

        Parameters
        ----------
        raw : RawFinancialData
            The raw data container containing info and DataFrames.

        Returns
        -------
        CompanySnapshot
            A populated transport object for the Resolver.
        """
        info = raw.info
        currency, current_price = normalize_currency_and_price(info)

        snapshot = CompanySnapshot(
            ticker=raw.ticker,
            name=str(info.get("shortName", raw.ticker)),
            country=str(info.get("country", "Unknown")),
            sector=str(info.get("sector", "Unknown")),
            industry=str(info.get("industry", "Unknown")),
            currency=currency,
            current_price=current_price,
        )

        # Extraction Micro (Pillar 2)
        bs = raw.balance_sheet
        snapshot.total_debt = extract_most_recent_value(bs, DEBT_KEYS)
        snapshot.cash_and_equivalents = extract_most_recent_value(bs, ["Cash And Cash Equivalents"])
        snapshot.minority_interests = extract_most_recent_value(bs, ["Minority Interest"])
        snapshot.pension_provisions = extract_most_recent_value(bs, ["Long Term Provisions"])
        snapshot.lease_liabilities = extract_most_recent_value(bs, ["Long Term Lease Liabilities"])
        snapshot.pension_liabilities = extract_most_recent_value(
            bs, ["Pension And Other Post Retirement Benefit Plans"]
        )
        snapshot.shares_outstanding = float(info.get("sharesOutstanding") or 1.0)
        snapshot.interest_expense = extract_most_recent_value(raw.income_stmt, ["Interest Expense"])  # For Cost of Debt

        # TTM Reconstruction (Pillar 3) - Current Year
        snapshot.revenue_ttm = self._sum_last_4_quarters(raw.quarterly_income_stmt, ["Total Revenue"]) or info.get(
            "totalRevenue"
        )
        snapshot.ebit_ttm = self._sum_last_4_quarters(raw.quarterly_income_stmt, ["EBIT"]) or info.get(
            "operatingCashflow"
        )
        snapshot.net_income_ttm = self._sum_last_4_quarters(raw.quarterly_income_stmt, ["Net Income"]) or info.get(
            "netIncomeToCommon"
        )

        ocf = self._sum_last_4_quarters(raw.quarterly_cash_flow, OCF_KEYS)
        capex = self._sum_last_4_quarters(raw.quarterly_cash_flow, CAPEX_KEYS)
        snapshot.fcf_ttm = (ocf + capex) if (ocf is not None and capex is not None) else info.get("freeCashflow")

        snapshot.eps_ttm = info.get("trailingEps")
        snapshot.dividend_share = info.get("dividendRate")
        snapshot.book_value_ps = info.get("bookValue")
        snapshot.beta = float(info.get("beta") or 1.0)

        # Additional TTM metrics for Piotroski calculation
        snapshot.total_assets_ttm = self._extract_value_at_position(bs, ["Total Assets"], position=0)
        snapshot.current_assets_ttm = self._extract_value_at_position(bs, ["Current Assets"], position=0)
        snapshot.current_liabilities_ttm = self._extract_value_at_position(bs, ["Current Liabilities"], position=0)
        snapshot.gross_profit_ttm = self._sum_last_4_quarters(raw.quarterly_income_stmt, ["Gross Profit"])

        # Historical Data (N-1) - Previous Year for Year-over-Year Comparisons
        snapshot.net_income_prev = self._sum_quarters_with_offset(raw.quarterly_income_stmt, ["Net Income"], offset=4)
        snapshot.total_assets_prev = self._extract_value_at_position(bs, ["Total Assets"], position=1)
        snapshot.long_term_debt_prev = self._extract_value_at_position(bs, ["Long Term Debt"], position=1)
        snapshot.current_assets_prev = self._extract_value_at_position(bs, ["Current Assets"], position=1)
        snapshot.current_liabilities_prev = self._extract_value_at_position(bs, ["Current Liabilities"], position=1)
        snapshot.gross_profit_prev = self._sum_quarters_with_offset(
            raw.quarterly_income_stmt, ["Gross Profit"], offset=4
        )
        snapshot.revenue_prev = self._sum_quarters_with_offset(raw.quarterly_income_stmt, ["Total Revenue"], offset=4)
        snapshot.shares_outstanding_prev = self._extract_value_at_position(bs, ["Share Issued"], position=1)

        # --- Historical WCR Ratio Calculation ---
        snapshot.historical_wcr_ratio = self._calculate_historical_wcr_ratio(raw)

        return snapshot

    # =========================================================================
    # TECHNICAL HELPERS
    # =========================================================================

    @staticmethod
    def _sum_last_4_quarters(df: pd.DataFrame | None, keys: list[str]) -> float | None:
        """
        Aggregates the last 4 quarters for a given metric to build TTM values.

        Parameters
        ----------
        df : pd.DataFrame, optional
            The quarterly financial statement.
        keys : List[str]
            List of accounting keys to search for.

        Returns
        -------
        float, optional
            The sum of the last 4 quarters or None.
        """
        if df is None or df.empty:
            return None

        for key in keys:
            if key in df.index:
                # Yahoo delivers Newest-to-Oldest
                last_4 = df.loc[key].iloc[:4]
                if len(last_4) == 4 and not last_4.isnull().any():
                    return float(last_4.sum())
        return None

    @staticmethod
    def _sum_quarters_with_offset(df: pd.DataFrame | None, keys: list[str], offset: int) -> float | None:
        """
        Aggregates 4 quarters starting from a specified offset to build historical TTM.

        This method is used to calculate previous year TTM values by offsetting
        the starting quarter position.

        Parameters
        ----------
        df : pd.DataFrame, optional
            The quarterly financial statement.
        keys : List[str]
            List of accounting keys to search for.
        offset : int
            Number of quarters to offset from most recent (e.g., 4 for previous year).

        Returns
        -------
        float, optional
            The sum of the 4 quarters at the offset position or None.

        Examples
        --------
        >>> # Get previous year net income (quarters 4-7)
        >>> prev_ni = _sum_quarters_with_offset(df, ["Net Income"], offset=4)
        """
        if df is None or df.empty:
            return None

        for key in keys:
            if key in df.index:
                # Yahoo delivers Newest-to-Oldest, so offset from start
                values = df.loc[key].iloc[offset : offset + 4]
                if len(values) == 4 and not values.isnull().any():
                    return float(values.sum())
        return None

    @staticmethod
    def _extract_value_at_position(df: pd.DataFrame | None, keys: list[str], position: int) -> float | None:
        """
        Extracts value at a specific chronological position (e.g., 0=latest, 1=previous year).

        Centralizes the extraction logic for balance sheet items at different time periods,
        following DRY principles.

        Parameters
        ----------
        df : pd.DataFrame, optional
            The financial statement (typically Balance Sheet).
        keys : List[str]
            List of potential aliases for the required field.
        position : int
            Chronological position (0=most recent, 1=previous year, etc.).

        Returns
        -------
        float, optional
            The extracted numeric value at the specified position or None.

        Examples
        --------
        >>> # Get current year total assets
        >>> assets_current = _extract_value_at_position(bs, ["Total Assets"], position=0)
        >>> # Get previous year total assets
        >>> assets_prev = _extract_value_at_position(bs, ["Total Assets"], position=1)
        """
        if df is None or df.empty:
            return None

        for key in keys:
            if key in df.index:
                row = df.loc[key]
                # Handle cases where row might be a Series or a single scalar
                values = row.values if hasattr(row, "values") else [row]
                if position < len(values) and pd.notnull(values[position]):
                    try:
                        return float(values[position])
                    except (ValueError, TypeError):
                        continue
        return None

    def _calculate_historical_wcr_ratio(self, raw: RawFinancialData) -> float | None:
        """
        Calculate historical Working Capital Requirement to Revenue ratio.

        Computes the average WCR/Revenue ratio over the last 3 fiscal years where:
        WCR = (Inventory + Accounts Receivable) - Accounts Payable

        Parameters
        ----------
        raw : RawFinancialData
            Raw financial data containing balance sheet and income statement.

        Returns
        -------
        float, optional
            Average historical WCR to revenue ratio (as decimal, e.g., 0.05 for 5%),
            or None if insufficient data is available.

        Notes
        -----
        This method handles missing data gracefully and only computes the ratio
        when all required components are available for a given year.
        Division by zero is avoided by checking revenue > 0.

        Examples
        --------
        >>> # If WCR averages 5M over 3 years with revenue of 100M
        >>> # Returns 0.05 (5%)
        """
        bs = raw.balance_sheet
        income_stmt = raw.income_stmt

        if bs is None or bs.empty or income_stmt is None or income_stmt.empty:
            return None

        # Keys for balance sheet components
        inventory_keys = ["Inventory"]
        receivables_keys = ["Accounts Receivable", "Receivables"]
        payables_keys = ["Accounts Payable", "Payables"]
        revenue_keys = ["Total Revenue"]

        wcr_ratios = []

        # Calculate WCR ratio for up to 3 most recent fiscal years
        for year_offset in range(3):
            # Extract components for this year
            inventory = self._extract_value_at_position(bs, inventory_keys, position=year_offset)
            receivables = self._extract_value_at_position(bs, receivables_keys, position=year_offset)
            payables = self._extract_value_at_position(bs, payables_keys, position=year_offset)
            revenue = self._extract_value_at_position(income_stmt, revenue_keys, position=year_offset)

            # Only calculate if all components are available and revenue is positive
            if all(v is not None for v in [inventory, receivables, payables, revenue]) and revenue > 0:
                # WCR = (Inventory + Receivables) - Payables
                wcr = (inventory + receivables) - payables
                ratio = wcr / revenue
                wcr_ratios.append(ratio)

        # Return average if we have at least one valid ratio
        if wcr_ratios:
            avg_ratio = sum(wcr_ratios) / len(wcr_ratios)
            logger.info(
                f"Calculated historical WCR ratio: {avg_ratio:.4f} "
                f"({len(wcr_ratios)} years available)"
            )
            return avg_ratio

        logger.warning("Insufficient data to calculate historical WCR ratio")
        return None
