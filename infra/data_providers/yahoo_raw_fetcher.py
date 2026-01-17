"""
infra/data_providers/yahoo_raw_fetcher.py

FETCHER BRUT — YAHOO FINANCE API — VERSION V13.0 (Sprint 6)
Rôle : Extraction multi-temporelle (TTM & Historique) pour Backtesting.
Standards : SOLID (Interface Segregation), Pydantic Rigueur, safe_api_call.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, List

import pandas as pd
import yfinance as yf
from pydantic import BaseModel, ConfigDict, Field

from infra.data_providers.extraction_utils import safe_api_call

logger = logging.getLogger(__name__)


class RawFinancialData(BaseModel):
    """
    Container Pydantic pour les données brutes (ST 3.1).
    Supporte désormais les types arbitraires pour encapsuler les DataFrames Pandas.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ticker: str
    info: Dict[str, Any] = Field(default_factory=dict)

    # États financiers annuels (Historique complet 3-4 ans pour le Backtesting)
    balance_sheet: Optional[pd.DataFrame] = None
    income_stmt: Optional[pd.DataFrame] = None
    cash_flow: Optional[pd.DataFrame] = None

    # États trimestriels (Indispensables pour les calculs TTM précis)
    quarterly_income_stmt: Optional[pd.DataFrame] = None
    quarterly_cash_flow: Optional[pd.DataFrame] = None

    @property
    def is_valid(self) -> bool:
        """Vérifie si les données minimales nécessaires à une valorisation sont présentes."""
        if not self.info:
            return False
        # Un prix de marché est le pré-requis absolu pour comparer IV et Prix
        return "currentPrice" in self.info or "regularMarketPrice" in self.info


class YahooRawFetcher:
    """
    Fetcher bas niveau pour l'API Yahoo Finance.
    Responsabilité unique : Acquisition multi-temporelle avec retry (SOLID).
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    # =========================================================================
    # 1. INTERFACES PUBLIQUES (Interface Segregation)
    # =========================================================================

    def fetch_ttm_snapshot(self, ticker: str) -> RawFinancialData:
        """Récupère les données les plus récentes pour une analyse immédiate."""
        logger.debug("[Fetcher] Snapshot TTM pour %s", ticker)
        return self._execute_fetch(ticker, historical=False)

    def fetch_historical_deep(self, ticker: str) -> RawFinancialData:
        """
        Récupère l'historique complet (3-4 ans) des états financiers (ST 3.1).
        Indispensable pour comparer l'IV passée au prix réel de l'époque.
        """
        logger.info("[Fetcher] Deep Fetch Historique pour %s", ticker)
        return self._execute_fetch(ticker, historical=True)

    def fetch_all(self, ticker: str) -> RawFinancialData:
        """
        Rétrocompatibilité avec les Sprints 1-5.
        Redirige vers le Deep Fetch pour garantir la complétude des données.
        """
        return self.fetch_historical_deep(ticker)

    # =========================================================================
    # 2. MOTEUR D'EXTRACTION (Cœur de la logique)
    # =========================================================================

    def _execute_fetch(self, ticker: str, historical: bool = True) -> RawFinancialData:
        """
        Moteur d'exécution centralisé.
        Récupère l'intégralité des états financiers via safe_api_call.
        """
        yt = yf.Ticker(ticker)

        # Extraction isolée de chaque segment pour garantir la continuité du workflow (V11.0 Style)
        info = safe_api_call(lambda: yt.info, f"Info/{ticker}", self.max_retries) or {}

        # Note : En yfinance, .balance_sheet, .income_stmt et .cash_flow
        # contiennent l'historique annuel par défaut (généralement 4 ans).
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
    # 3. SERVICES ANNEXES (Pairs & Historique Prix)
    # =========================================================================

    def fetch_peer_multiples(self, target_ticker: str) -> List[Dict[str, Any]]:
        """Découvre les concurrents sectoriels et extrait leurs données brutes (.info)."""
        logger.info("[Fetcher] Peer discovery started | target=%s", target_ticker)

        target_yt = yf.Ticker(target_ticker)
        target_info = safe_api_call(lambda: target_yt.info, f"TargetInfo/{target_ticker}", 1)

        # Yahoo stocke souvent les concurrents dans 'relatedTickers'
        peer_tickers = target_info.get("relatedTickers", []) if target_info else []

        if not peer_tickers:
            logger.warning("[Fetcher] Aucun pair identifié dynamiquement pour %s", target_ticker)
            return []

        raw_peers_data: List[Dict[str, Any]] = []
        # Limitation à 5 pour optimiser les temps de réponse API (Sprint 5)
        for p_ticker in peer_tickers[:5]:
            p_info = safe_api_call(lambda: yf.Ticker(p_ticker).info, f"PeerInfo/{p_ticker}", 1)
            if p_info:
                p_info["symbol"] = p_ticker
                raw_peers_data.append(p_info)

        logger.debug("[Fetcher] %d pairs extraits pour %s", len(raw_peers_data), target_ticker)
        return raw_peers_data

    def fetch_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Récupère l'historique des prix (Indispensable pour valider l'IV historique)."""
        logger.debug("[Fetcher] Fetching price history for %s (%s)", ticker, period)
        try:
            yt = yf.Ticker(ticker)
            return yt.history(period=period)
        except Exception as e:
            logger.error("[Fetcher] Historical price extraction failed | ticker=%s, error=%s", ticker, e)
            return pd.DataFrame()