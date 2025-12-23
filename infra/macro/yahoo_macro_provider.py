"""
infra/macro/yahoo_macro_provider.py

FOURNISSEUR MACRO — TAUX & RISQUE
Version : V3.4 — Fix Critique EUS=F (Price vs Yield)

Correctif :
- Détection intelligente du format des Futures (Prix vs Taux).
- Empêche la génération de taux aberrants (ex: 96%) si Yahoo change de format.
- Maintien de la compatibilité totale avec les versions précédentes.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
import yfinance as yf

# On garde cet import pour la compatibilité de type si besoin dans d'autres modules
from core.models import DCFParameters

logger = logging.getLogger(__name__)

# Tickers pour les taux sans risque (Yields / Futures)
# ^TNX  = Treasury Yield 10 Years (en %, donc 4.5 = 4.5% -> doit être converti en 0.045)
# EUS=F = Future sur EURO SHORT-TERM RATE (€STR)
#         Peut être coté en PRIX (~96.50) ou en TAUX (~3.50) selon le bon vouloir de Yahoo.
RISK_FREE_TICKERS: Dict[str, str] = {
    "USD": "^TNX",
    "EUR": "EUS=F",
    "CAD": "^GSPTSE",
    "GBP": "^FTSE",
}

MARKET_TICKER = "^GSPC"


@dataclass
class MacroContext:
    """Contient les paramètres macro-économiques à une date donnée."""
    date: datetime
    currency: str
    risk_free_rate: float
    market_risk_premium: float
    perpetual_growth_rate: float
    corporate_aaa_yield: float


class YahooMacroProvider:
    """
    Fournit les données macro (Rf, MRP, Yield AAA) via Yahoo Finance.
    Intègre des fallbacks robustes et un cache en mémoire.
    """

    def __init__(self):
        self._rf_cache: Dict[str, pd.Series] = {}
        # Spread par défaut entre taux sans risque et obligations AAA (70 bps)
        self.DEFAULT_AAA_SPREAD = 0.0070

    def _fetch_history_robust(self, ticker_obj: yf.Ticker) -> pd.DataFrame:
        """
        Tente de récupérer l'historique avec des périodes dégressives.
        Contourne le bug 'Period max is invalid' de yfinance sur les futures.
        """
        # Ordre de tentative : Max -> 10 ans -> 5 ans -> 1 an
        periods = ["max", "10y", "5y", "1y"]

        for period in periods:
            try:
                # auto_adjust=False est souvent plus stable pour les index/taux
                data = ticker_obj.history(period=period, interval="1d", auto_adjust=False)

                if not data.empty and "Close" in data.columns:
                    if period != "max":
                        logger.warning(
                            f"[Macro] Fallback sur period='{period}' pour {ticker_obj.ticker} "
                            "(L'historique complet 'max' a échoué)"
                        )
                    return data
            except Exception as e:
                logger.debug(f"[Macro] Echec fetch {ticker_obj.ticker} sur {period}: {e}")
                continue

        # Si tout échoue
        return pd.DataFrame()

    def _load_risk_free_series(self, currency: str) -> Optional[pd.Series]:
        """
        Charge l'historique de rendement sans risque pour une devise donnée.
        Gère intelligemment la conversion Prix -> Taux -> Décimale.
        """
        currency = currency.upper()

        if currency in self._rf_cache:
            return self._rf_cache[currency]

        ticker = RISK_FREE_TICKERS.get(currency)
        if not ticker:
            return None

        logger.info("[Macro] Chargement de l'historique Rf pour %s (%s)...", ticker, currency)

        try:
            yt = yf.Ticker(ticker)

            # --- UTILISATION DE LA MÉTHODE ROBUSTE ---
            data = self._fetch_history_robust(yt)

            if data.empty:
                logger.warning("[Macro] Données vides ou inaccessibles pour %s.", ticker)
                return None

            # Normalisation de l'Index (Date)
            idx = pd.to_datetime(data.index)
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            data.index = idx

            # --- CORRECTION CRITIQUE EUS=F (LE BUG DES 119€) ---
            if ticker == "EUS=F":
                # EUS=F est traître : il peut valoir ~96.5 (Prix) ou ~3.5 (Taux).
                # S'il vaut 3.5 et qu'on fait (100 - 3.5), on obtient 96.5% de taux !

                # Copie pour manipulation sûre
                raw_values = data["Close"].copy()

                # Masque : Quelles lignes sont des PRIX (supposons > 20.0 par sécurité)
                # Un taux Euribor ne sera jamais > 20% dans le contexte actuel.
                is_price_format = raw_values > 20.0

                # Conversion des Prix en Taux % (100 - Prix)
                raw_values.loc[is_price_format] = 100.0 - raw_values.loc[is_price_format]

                # À ce stade, raw_values contient des POURCENTAGES (ex: 3.5 pour 3.5%)
                # On convertit en décimales (ex: 0.035)
                series = (raw_values / 100.0).rename("Risk_Free_Rate")

            else:
                # Yield standard (ex: ^TNX renvoie 4.2 pour 4.2%)
                series = (data["Close"] / 100.0).rename("Risk_Free_Rate")

            # Mise en cache
            self._rf_cache[currency] = series
            logger.info("[Macro] Historique Rf chargé (%d points).", len(series))
            return series

        except Exception as e:
            logger.error("[Macro] Erreur critique lors du chargement de %s: %s", ticker, e)
            return None

    def _estimate_aaa_yield(self, risk_free_rate: float) -> float:
        """
        Estime le rendement des obligations AAA corporate.
        Approche simple : Taux sans risque + Spread fixe.
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
        Utilisé par le provider pour remplir les DCFParameters.
        """
        currency = currency.upper()
        # On retire la timezone pour comparer avec l'index pandas
        date = date.replace(tzinfo=None)

        # Valeurs par défaut (Fallback ultime si l'API échoue totalement)
        # On renvoie bien des décimales (0.04 = 4%)
        rf_value = 0.04 if currency != "EUR" else 0.027

        # 1. Récupération Taux Sans Risque (Rf)
        rf_series = self._load_risk_free_series(currency)

        if rf_series is not None:
            # Filtrage temporel : on prend la dernière valeur connue avant ou à la date
            past_data = rf_series[rf_series.index <= date]

            if not past_data.empty:
                rf_value = float(past_data.iloc[-1])

                # Sanity Check : On évite les taux < 0.1% ou négatifs pour les modèles perpétuels
                # (Sauf si on veut explicitement gérer les taux négatifs, mais Gordon Shapiro n'aime pas ça)
                if rf_value < 0.001:
                    rf_value = 0.001
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