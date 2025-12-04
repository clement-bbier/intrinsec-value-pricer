import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
import yfinance as yf

from core.exceptions import DataProviderError

logger = logging.getLogger(__name__)

# Tickers pour les taux sans risque (Yields / Futures)
# ^TNX  = Treasury Yield 10 Years (en %, donc 4.5 = 4.5% -> doit être converti en 0.045)
# EUS=F = Future sur EURO SHORT-TERM RATE (€STR) coté en prix ~ 100 - taux(%)
RISK_FREE_TICKERS: Dict[str, str] = {
    "USD": "^TNX",     # Taux sans risque USD (10Y)
    "EUR": "EUS=F",    # Future €STR (proxy OIS risk-free court terme)
    "CAD": "^GSPTSE",  # Proxy pour le marché canadien (à raffiner plus tard)
}

# Ticker pour le marché (S&P 500) – pas encore utilisé dans cette V1.
MARKET_TICKER = "^GSPC"


@dataclass
class MacroContext:
    """Contient les paramètres macro-économiques à une date donnée."""
    date: datetime
    currency: str
    risk_free_rate: float        # ex: 0.04 pour 4%
    market_risk_premium: float   # ex: 0.05 pour 5%
    perpetual_growth_rate: float # ex: 0.02 pour 2%


class YahooMacroProvider:
    """
    Fournit les données macro (Rf, MRP) historiques via Yahoo Finance.
    Utilise un cache simple pour éviter de retélécharger l'historique à chaque point.
    """

    def __init__(self):
        # Cache pour les séries historiques de taux sans risque (Rf)
        # Clé: devise (str), Valeur: pd.Series (Index: date, Name: 'Risk_Free_Rate')
        self._rf_cache: Dict[str, pd.Series] = {}

    def _load_risk_free_series(self, currency: str) -> Optional[pd.Series]:
        """
        Charge l'historique de rendement sans risque pour une devise donnée, en utilisant le cache.
        Convertit le rendement de % à décimal (ex: 4.5 -> 0.045).
        Normalise aussi l'index en datetime **sans timezone** pour éviter
        les erreurs de comparaison tz-naive / tz-aware.
        """
        currency = currency.upper()

        # 1) Cache
        if currency in self._rf_cache:
            return self._rf_cache[currency]

        # 2) Ticker associé à la devise
        ticker = RISK_FREE_TICKERS.get(currency)
        if not ticker:
            logger.warning("[Macro] Ticker de taux sans risque inconnu pour la devise %s", currency)
            return None

        logger.info("[Macro] Chargement de l'historique Rf pour %s (%s)...", ticker, currency)

        try:
            # Utilisation de Ticker().history au lieu de yf.download pour éviter le bug
            yt = yf.Ticker(ticker)
            data = yt.history(period="max", interval="1d", auto_adjust=False)

            if data.empty or "Close" not in data.columns:
                logger.error("[Macro] Données vides ou colonne 'Close' manquante pour %s.", ticker)
                return None

            # 🔧 Normalisation de l'index : datetime tz-naive
            idx = pd.to_datetime(data.index)
            if isinstance(idx, pd.DatetimeIndex) and idx.tz is not None:
                # on enlève la timezone (America/Chicago, Europe/Berlin, etc.)
                idx = idx.tz_localize(None)
            data.index = idx

            # Conversion en taux selon le type de ticker
            if ticker == "EUS=F":
                # Future sur €STR : Price ≈ 100 - taux(%)  => taux(%) = 100 - Price
                # Exemple : Price = 98.70 => taux ≈ 1.30% => 0.013 en décimal
                implied_rate_pct = 100.0 - data["Close"]
                series = (implied_rate_pct / 100.0).rename("Risk_Free_Rate")
            else:
                # Cas standard : Close déjà en % (ex: 4.5) => 0.045 en décimal
                series = (data["Close"] / 100.0).rename("Risk_Free_Rate")

            self._rf_cache[currency] = series

            logger.info("[Macro] Historique Rf chargé. %d points.", len(series))
            return series

        except Exception as e:
            logger.error("[Macro] Erreur lors du chargement de %s: %s", ticker, e)
            return None

    def get_macro_context(
        self,
        date: datetime,
        currency: str,
        base_mrp: float = 0.05,
        base_g_inf: float = 0.02,
    ) -> Optional[MacroContext]:
        """
        Retourne le contexte macro (Rf, MRP, g∞) à une date précise.
        Pour Rf, prend la donnée la plus récente avant ou égale à cette date.
        """

        # Normalisation devise + date (tz-naive)
        currency = currency.upper()
        date = date.replace(tzinfo=None)

        # --- Fallbacks par devise ---
        DEFAULT_RF = 0.04       # fallback générique (4%)
        DEFAULT_RF_EUR = 0.027  # fallback spécifique EUR (2.7% ~ Bund 10Y moyen)

        # 1. Taux sans risque historique (Rf)
        rf_series = self._load_risk_free_series(currency)

        # Valeur par défaut suivant la devise
        rf_value = DEFAULT_RF_EUR if currency == "EUR" else DEFAULT_RF

        if rf_series is not None:
            # (sécurité) s'assurer que l'index est bien tz-naive
            if isinstance(rf_series.index, pd.DatetimeIndex) and rf_series.index.tz is not None:
                rf_series = rf_series.copy()
                rf_series.index = rf_series.index.tz_localize(None)

            # On garde les valeurs <= date
            try:
                past_data = rf_series[rf_series.index <= date]
            except TypeError as e:
                logger.error(
                    "[Macro] Erreur de comparaison dates (rf_series.index vs %s): %s",
                    date,
                    e,
                )
                past_data = rf_series

            if not past_data.empty:
                rf_value = float(past_data.iloc[-1])

                # ⛔ Cas particulier EUR : taux négatif ou aberrant → fallback 2.7 %
                if currency == "EUR" and rf_value < 0.0:
                    logger.warning(
                        "[Macro] Rendement €STR/Bund proxy négatif pour EUR à la date %s — "
                        "fallback 2.7%% utilisé comme Rf stable.",
                        date.date(),
                    )
                    rf_value = DEFAULT_RF_EUR
            else:
                # Pas de data historique utilisable
                if currency == "EUR":
                    logger.warning(
                        "[Macro] Pas de taux sans risque trouvé avant %s pour EUR. "
                        "Fallback 2.7%% (proxy Bund 10Y moyen).",
                        date.date(),
                    )
                    rf_value = DEFAULT_RF_EUR
                else:
                    logger.warning(
                        "[Macro] Pas de taux sans risque trouvé avant %s pour %s. "
                        "Utilisation défaut (4%%).",
                        date.date(),
                        currency,
                    )
                    rf_value = DEFAULT_RF
        else:
            # rf_series = None (échec complet du chargement)
            if currency == "EUR":
                logger.warning(
                    "[Macro] Impossible de charger une série Rf pour EUR. "
                    "Fallback 2.7%% (proxy Bund 10Y moyen)."
                )
                rf_value = DEFAULT_RF_EUR
            else:
                logger.warning(
                    "[Macro] Impossible de charger une série Rf pour %s. "
                    "Fallback générique 4%%.",
                    currency,
                )
                rf_value = DEFAULT_RF

        # 2. Market Risk Premium (MRP) – constant en V1
        mrp_value = base_mrp

        # 3. Taux de croissance perpétuel (g∞) – constant en V1
        g_inf_value = base_g_inf

        logger.info(
            "[Macro] Contexte pour %s (currency=%s): Rf=%.4f, MRP=%.4f, g∞=%.4f",
            date.date(),
            currency,
            rf_value,
            mrp_value,
            g_inf_value,
        )

        return MacroContext(
            date=date,
            currency=currency,
            risk_free_rate=rf_value,
            market_risk_premium=mrp_value,
            perpetual_growth_rate=g_inf_value,
        )
