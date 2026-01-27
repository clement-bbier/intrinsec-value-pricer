"""
infra/data_providers/yahoo_raw_fetcher.py

RAW FETCHER — YAHOO FINANCE API
Role: Multi-temporal extraction (TTM & Historical) for Backtesting.
Standards: SOLID (Interface Segregation), Pydantic Rigor, safe_api_call.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, List

import pandas as pd
import yfinance as yf
from pydantic import BaseModel, ConfigDict, Field

from infra.data_providers.extraction_utils import safe_api_call
from src.config.constants import DataExtractionDefaults

logger = logging.getLogger(__name__)


class RawFinancialData(BaseModel):
    """
    Pydantic container for raw financial data.
    Supports arbitrary types to encapsulate Pandas DataFrames.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ticker: str
    info: Dict[str, Any] = Field(default_factory=dict)

    # Annual financial statements (Full 3-4 year history for Backtesting)
    balance_sheet: Optional[pd.DataFrame] = None
    income_stmt: Optional[pd.DataFrame] = None
    cash_flow: Optional[pd.DataFrame] = None

    # Quarterly statements (Indispensable for precise TTM calculations)
    quarterly_income_stmt: Optional[pd.DataFrame] = None
    quarterly_cash_flow: Optional[pd.DataFrame] = None

    @property
    def is_valid(self) -> bool:
        """Verifies if minimal data required for valuation is present."""
        if not self.info:
            return False
        return "currentPrice" in self.info or "regularMarketPrice" in self.info


class YahooRawFetcher:
    """
    Low-level fetcher for the Yahoo Finance API.
    Single Responsibility: Multi-temporal acquisition with retry (SOLID).
    """

    def __init__(self, max_retries: int = DataExtractionDefaults.YAHOO_RAW_MAX_RETRIES):
        self.max_retries = max_retries

    # =========================================================================
    # 1. PUBLIC INTERFACES (Interface Segregation)
    # =========================================================================

    def fetch_ttm_snapshot(self, ticker: str) -> RawFinancialData:
        """Retrieves most recent data for immediate analysis."""
        logger.debug("[Fetcher] TTM Snapshot for %s", ticker)
        return self._execute_fetch(ticker)

    def fetch_historical_deep(self, ticker: str) -> RawFinancialData:
        """
        Retrieves full history (3-4 years) of financial statements.
        Required for comparing past IV with historical price.
        """
        logger.info("[Fetcher] Deep Historical Fetch for %s", ticker)
        return self._execute_fetch(ticker)

    def fetch_all(self, ticker: str) -> RawFinancialData:
        """
        Backward compatibility. Redirects to Deep Fetch to ensure data completeness.
        """
        return self.fetch_historical_deep(ticker)

    # =========================================================================
    # 2. EXTRACTION ENGINE (Core Logic)
    # =========================================================================

    def _execute_fetch(self, ticker: str) -> RawFinancialData:
        """
        Centralized execution engine.
        Retrieves all financial statements via safe_api_call.
        """
        yt = yf.Ticker(ticker)

        # Isolated extraction of each segment for workflow continuity
        info = safe_api_call(lambda: yt.info, f"Info/{ticker}", self.max_retries) or {}

        # Acquisition of financial statements (yfinance returns history by default)
        bs = safe_api_call(lambda: yt.balance_sheet, f"BS/{ticker}", self.max_retries)
        is_ = safe_api_call(lambda: yt.income_stmt, f"IS/{ticker}", self.max_retries)
        cf = safe_api_call(lambda: yt.cash_flow, f"CF/{ticker}", self.max_retries)

        q_is = safe_api_call(lambda: yt.quarterly_income_stmt, f"QIS/{ticker}", self.max_retries)
        q_cf = safe_api_call(lambda: yt.quarterly_cash_flow, f"QCF/{ticker}", self.max_retries)

        return RawFinancialData(
            ticker=ticker,
            info=info,
            balance_sheet=bs,
            income_stmt=is_,
            cash_flow=cf,
            quarterly_income_stmt=q_is,
            quarterly_cash_flow=q_cf,
        )

    # =========================================================================
    # 3. ANNEX SERVICES (Peers & Price History)
    # =========================================================================

    @staticmethod
    def fetch_peer_multiples(target_ticker: str) -> List[Dict[str, Any]]:
        """Discovers sectoral peers and extracts raw info data."""
        logger.info("[Fetcher] Peer discovery started | target=%s", target_ticker)

        target_yt = yf.Ticker(target_ticker)
        target_info = safe_api_call(lambda: target_yt.info, f"TargetInfo/{target_ticker}", 1)

        peer_tickers = target_info.get("relatedTickers", []) if target_info else []

        if not peer_tickers:
            logger.warning("[Fetcher] No peers identified dynamically for %s", target_ticker)
            return []

        raw_peers_data: List[Dict[str, Any]] = []
        for p_ticker in peer_tickers[:5]:
            p_info = safe_api_call(lambda: yf.Ticker(p_ticker).info, f"PeerInfo/{p_ticker}", 1)
            if p_info:
                p_info["symbol"] = p_ticker
                raw_peers_data.append(p_info)

        logger.debug("[Fetcher] %d peers extracted for %s", len(raw_peers_data), target_ticker)
        return raw_peers_data

    @staticmethod
    def fetch_price_history(ticker: str, period: str = "5y") -> pd.DataFrame:
        """Retrieves price history for historical validation."""
        logger.debug("[Fetcher] Fetching price history for %s (%s)", ticker, period)
        try:
            yt = yf.Ticker(ticker)
            return yt.history(period=period)
        except (RuntimeError, ValueError) as e:
            logger.error("[Fetcher] Historical price extraction failed | ticker=%s, error=%s", ticker, e)
            return pd.DataFrame()