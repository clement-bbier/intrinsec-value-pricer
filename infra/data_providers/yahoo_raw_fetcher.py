"""
infra/data_providers/yahoo_raw_fetcher.py

FETCHER BRUT — YAHOO FINANCE API — VERSION V11.0 (Sprint 4)
Rôle : Appels API yfinance avec discovery de pairs et gestion des erreurs.
Responsabilité unique : Transport de données brutes, aucune logique métier.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

import pandas as pd
import yfinance as yf

from infra.data_providers.extraction_utils import safe_api_call

logger = logging.getLogger(__name__)


@dataclass
class RawFinancialData:
    """Container pour les données brutes extraites de Yahoo Finance pour l'entreprise cible."""

    ticker: str
    info: Dict[str, Any]
    balance_sheet: Optional[pd.DataFrame] = None
    income_stmt: Optional[pd.DataFrame] = None
    cash_flow: Optional[pd.DataFrame] = None
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

    Responsabilité unique : Récupérer les données brutes avec retry.
    Il ne contient aucune logique de calcul ou de normalisation (SOLID).
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def fetch_all(self, ticker: str) -> RawFinancialData:
        """
        Récupère l'intégralité des états financiers et métadonnées pour un ticker cible.
        Utilise safe_api_call pour isoler les défaillances de l'API yfinance.
        """
        logger.debug("[Fetcher] Acquisition des données brutes cibles pour %s", ticker)

        yt = yf.Ticker(ticker)

        # Extraction isolée de chaque segment pour garantir la continuité du workflow en cas d'erreur partielle
        info = safe_api_call(lambda: yt.info, f"Info/{ticker}", self.max_retries) or {}
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

    def fetch_peer_multiples(self, target_ticker: str) -> List[Dict[str, Any]]:
        """
        Découvre les concurrents sectoriels et extrait leurs données brutes (.info).
        Standard de sécurité : Isole chaque appel concurrent pour éviter un échec global.
        """
        logger.info("[Fetcher] Démarrage de la discovery des pairs pour %s", target_ticker)
        target_yt = yf.Ticker(target_ticker)

        # 1. Identification via l'algorithme de recommandation Yahoo (Peers corrélés)
        peers_df = safe_api_call(lambda: target_yt.recommendations, f"PeersDiscovery/{target_ticker}", retries=1)

        peer_tickers: List[str] = []
        if peers_df is not None and not peers_df.empty:
            # On récupère les symboles uniques de la cohorte proposée par Yahoo
            peer_tickers = peers_df.index.unique().tolist()

        if not peer_tickers:
            logger.warning("[Fetcher] Aucune cohorte de pairs identifiée pour %s", target_ticker)
            return []

        # 2. Extraction brute des données .info pour chaque pair
        # On limite à 8 pairs pour garantir des performances acceptables (temps de latence réseau)
        raw_peers_data: List[Dict[str, Any]] = []
        for p_ticker in peer_tickers[:8]:
            p_info = safe_api_call(
                lambda: yf.Ticker(p_ticker).info,
                f"PeerInfo/{p_ticker}",
                retries=1
            )
            if p_info:
                # On s'assure que le ticker est présent dans le dictionnaire pour le mapping futur
                p_info["symbol"] = p_ticker
                raw_peers_data.append(p_info)

        logger.debug("[Fetcher] %d pairs extraits pour %s", len(raw_peers_data), target_ticker)
        return raw_peers_data

    def fetch_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """
        Récupère l'historique des prix pour l'affichage graphique ou l'analyse de volatilité.
        """
        logger.debug("[Fetcher] Fetching price history for %s (%s)", ticker, period)

        try:
            yt = yf.Ticker(ticker)
            hist = yt.history(period=period)

            if hist.empty:
                logger.warning("[Fetcher] Historique de prix vide pour %s", ticker)

            return hist

        except Exception as e:
            logger.error("[Fetcher] Erreur extraction historique pour %s: %s", ticker, e)
            return pd.DataFrame()