import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
import yfinance as yf

from core.models import DCFParameters  # Utilisation potentielle future

logger = logging.getLogger(__name__)

# Tickers pour les taux sans risque (Yields / Futures)
# ^TNX  = Treasury Yield 10 Years (en %, donc 4.5 = 4.5% -> doit être converti en 0.045)
# EUS=F = Future sur EURO SHORT-TERM RATE (€STR) coté en prix ~ 100 - taux(%)
RISK_FREE_TICKERS: Dict[str, str] = {
    "USD": "^TNX",  # Taux sans risque USD (10Y)
    "EUR": "EUS=F",  # Future €STR (proxy OIS risk-free court terme) ou Bund si dispo
    "CAD": "^GSPTSE",  # Proxy simplifié
    "GBP": "^FTSE",  # Placeholder, à affiner
}

# Ticker pour le marché (S&P 500) – pas encore utilisé intensivement
MARKET_TICKER = "^GSPC"


@dataclass
class MacroContext:
    """Contient les paramètres macro-économiques à une date donnée."""
    date: datetime
    currency: str
    risk_free_rate: float  # ex: 0.04 pour 4%
    market_risk_premium: float  # ex: 0.05 pour 5%
    perpetual_growth_rate: float  # ex: 0.02 pour 2%
    corporate_aaa_yield: float  # ex: 0.047 (Nouveau: Requis pour Graham 1974)


class YahooMacroProvider:
    """
    Fournit les données macro (Rf, MRP, Yield AAA) via Yahoo Finance.
    Intègre des fallbacks robustes et un cache en mémoire.
    """

    def __init__(self):
        # Cache pour les séries historiques
        self._rf_cache: Dict[str, pd.Series] = {}

        # Spread de crédit moyen pour les obligations AAA vs Taux Sans Risque (10Y)
        # Historiquement entre 0.60% et 1.00%
        self.DEFAULT_AAA_SPREAD = 0.0070

    def _load_risk_free_series(self, currency: str) -> Optional[pd.Series]:
        """
        Charge l'historique de rendement sans risque pour une devise donnée.
        """
        currency = currency.upper()

        # 1) Cache Check
        if currency in self._rf_cache:
            return self._rf_cache[currency]

        # 2) Résolution Ticker
        ticker = RISK_FREE_TICKERS.get(currency)
        if not ticker:
            # Silence warning pour devises exotiques, fallback géré plus haut
            return None

        logger.info("[Macro] Chargement de l'historique Rf pour %s (%s)...", ticker, currency)

        try:
            yt = yf.Ticker(ticker)
            # Fetch historique max pour couvrir les dates passées
            data = yt.history(period="max", interval="1d", auto_adjust=False)

            if data.empty or "Close" not in data.columns:
                logger.warning("[Macro] Données vides pour %s.", ticker)
                return None

            # Normalisation Index (Timezone Naive)
            idx = pd.to_datetime(data.index)
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            data.index = idx

            # Normalisation Valeur (Conversion en décimal)
            if ticker == "EUS=F":
                # Future Rate = 100 - Price
                implied_rate = 100.0 - data["Close"]
                series = (implied_rate / 100.0).rename("Risk_Free_Rate")
            else:
                # Yield standard (ex: 4.2 -> 0.042)
                series = (data["Close"] / 100.0).rename("Risk_Free_Rate")

            self._rf_cache[currency] = series
            logger.info("[Macro] Historique Rf chargé (%d points).", len(series))
            return series

        except Exception as e:
            logger.error("[Macro] Erreur lors du chargement de %s: %s", ticker, e)
            return None

    def _estimate_aaa_yield(self, risk_free_rate: float) -> float:
        """
        Estime le rendement des obligations corporatives AAA.
        Y_aaa = Rf + Spread_AAA
        """
        return risk_free_rate + self.DEFAULT_AAA_SPREAD

    def get_macro_context(
            self,
            date: datetime,
            currency: str,
            base_mrp: float = 0.05,
            base_g_inf: float = 0.02,
    ) -> Optional[MacroContext]:
        """
        Retourne le contexte macro complet à une date précise.
        """
        currency = currency.upper()
        date = date.replace(tzinfo=None)

        # Valeurs par défaut (Fallback ultime)
        rf_value = 0.04 if currency != "EUR" else 0.027

        # 1. Récupération Taux Sans Risque (Rf)
        rf_series = self._load_risk_free_series(currency)

        if rf_series is not None:
            # Filtrage temporel : on prend la dernière valeur connue avant ou à la date
            past_data = rf_series[rf_series.index <= date]

            if not past_data.empty:
                rf_value = float(past_data.iloc[-1])

                # Sanity check pour l'Euro (taux négatifs passés ou erreur future)
                if currency == "EUR" and rf_value < 0.0:
                    rf_value = 0.025  # Fallback conservateur
            else:
                logger.warning(f"[Macro] Pas de donnée historique Rf pour {currency} avant {date.date()}")

        # 2. Estimation du Yield AAA (Pour Graham)
        aaa_yield = self._estimate_aaa_yield(rf_value)

        # 3. Construction du Contexte
        return MacroContext(
            date=date,
            currency=currency,
            risk_free_rate=rf_value,
            market_risk_premium=base_mrp,
            perpetual_growth_rate=base_g_inf,
            corporate_aaa_yield=aaa_yield
        )