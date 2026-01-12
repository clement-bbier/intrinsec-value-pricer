"""
infra/data_providers/yahoo_raw_fetcher.py

FETCHER BRUT — YAHOO FINANCE API
Version : V1.0
Rôle : Appels API yfinance avec retry et gestion des erreurs.
Responsabilité unique : Transport de données brutes, aucune logique métier.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf

from infra.data_providers.extraction_utils import safe_api_call

logger = logging.getLogger(__name__)


@dataclass
class RawFinancialData:
    """Container pour les données brutes extraites de Yahoo Finance."""

    ticker: str
    info: Dict[str, Any]
    balance_sheet: Optional[pd.DataFrame] = None
    income_stmt: Optional[pd.DataFrame] = None
    cash_flow: Optional[pd.DataFrame] = None
    quarterly_income_stmt: Optional[pd.DataFrame] = None
    quarterly_cash_flow: Optional[pd.DataFrame] = None

    @property
    def is_valid(self) -> bool:
        """Vérifie si les données minimales sont présentes."""
        if not self.info:
            return False
        return "currentPrice" in self.info or "regularMarketPrice" in self.info


class YahooRawFetcher:
    """
    Fetcher bas niveau pour l'API Yahoo Finance.

    Responsabilité unique : Récupérer les données brutes avec retry.
    Aucune transformation ni logique métier.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def fetch_all(self, ticker: str) -> RawFinancialData:
        """
        Récupère toutes les données financières brutes pour un ticker.

        Args:
            ticker: Symbole boursier (ex: AAPL, LVMH.PA)

        Returns:
            RawFinancialData contenant toutes les données brutes
        """
        logger.debug("[Fetcher] Fetching raw data for %s", ticker)

        yt = yf.Ticker(ticker)

        info = safe_api_call(lambda: yt.info, f"Info/{ticker}", self.max_retries)

        return RawFinancialData(
            ticker=ticker,
            info=info or {},
            balance_sheet=safe_api_call(lambda: yt.balance_sheet, f"BS/{ticker}", self.max_retries),
            income_stmt=safe_api_call(lambda:  yt.income_stmt, f"IS/{ticker}", self.max_retries),
            cash_flow=safe_api_call(lambda: yt.cash_flow, f"CF/{ticker}", self.max_retries),
            quarterly_income_stmt=safe_api_call(lambda: yt.quarterly_income_stmt, f"QIS/{ticker}", self.max_retries),
            quarterly_cash_flow=safe_api_call(lambda: yt.quarterly_cash_flow, f"QCF/{ticker}", self.max_retries),
        )

    def fetch_price_history(self, ticker: str, period:  str = "5y") -> pd.DataFrame:
        """
        Récupère l'historique des prix.

        Args:
            ticker:  Symbole boursier
            period: Période (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

        Returns:
            DataFrame avec l'historique des prix (ou vide si erreur)
        """
        logger.debug("[Fetcher] Fetching price history for %s (%s)", ticker, period)

        try:
            yt = yf.Ticker(ticker)
            hist = yt.history(period=period)

            if hist.empty:
                logger.warning("[Fetcher] No price history found for %s", ticker)

            return hist

        except Exception as e:
            logger.error("[Fetcher] Price history error for %s: %s", ticker, e)
            return pd.DataFrame()