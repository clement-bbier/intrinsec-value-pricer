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
from typing import List, Optional
import pandas as pd

from src.models.company import CompanySnapshot
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData
from infra.data_providers.extraction_utils import (
    extract_most_recent_value,
    normalize_currency_and_price,
    OCF_KEYS,
    CAPEX_KEYS,
    DEBT_KEYS
)

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
            current_price=current_price
        )

        # Extraction Micro (Pillar 2)
        bs = raw.balance_sheet
        snapshot.total_debt = extract_most_recent_value(bs, DEBT_KEYS)
        snapshot.cash_and_equivalents = extract_most_recent_value(bs, ["Cash And Cash Equivalents"])
        snapshot.minority_interests = extract_most_recent_value(bs, ["Minority Interest"])
        snapshot.pension_provisions = extract_most_recent_value(bs, ["Long Term Provisions"])
        snapshot.shares_outstanding = float(info.get("sharesOutstanding") or 1.0)
        snapshot.interest_expense = extract_most_recent_value(raw.income_stmt, ["Interest Expense"]) # For Cost of Debt

        # TTM Reconstruction (Pillar 3)
        snapshot.revenue_ttm = self._sum_last_4_quarters(raw.quarterly_income_stmt, ["Total Revenue"]) or info.get("totalRevenue")
        snapshot.ebit_ttm = self._sum_last_4_quarters(raw.quarterly_income_stmt, ["EBIT"]) or info.get("operatingCashflow")
        snapshot.net_income_ttm = self._sum_last_4_quarters(raw.quarterly_income_stmt, ["Net Income"]) or info.get("netIncomeToCommon")

        ocf = self._sum_last_4_quarters(raw.quarterly_cash_flow, OCF_KEYS)
        capex = self._sum_last_4_quarters(raw.quarterly_cash_flow, CAPEX_KEYS)
        snapshot.fcf_ttm = (ocf + capex) if (ocf is not None and capex is not None) else info.get("freeCashflow")

        snapshot.eps_ttm = info.get("trailingEps")
        snapshot.dividend_share = info.get("dividendRate")
        snapshot.book_value_ps = info.get("bookValue")
        snapshot.beta = float(info.get("beta") or 1.0)

        return snapshot

    # =========================================================================
    # TECHNICAL HELPERS
    # =========================================================================

    @staticmethod
    def _sum_last_4_quarters(df: Optional[pd.DataFrame], keys: List[str]) -> Optional[float]:
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