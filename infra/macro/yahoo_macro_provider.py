"""
infra/macro/yahoo_macro_provider.py

FOURNISSEUR MACRO — TAUX & RISQUE ()
Rôle : Orchestration des données de marché (Rf, MRP, Yield AAA) avec localisation pays.

Améliorations majeures :
- i18n : Utilisation intégrale de StrategySources pour les labels d'audit.
- Localisation Dynamique : Sélection du Rf via 'country_matrix.py' basée sur le pays.
- Traçabilité Glass Box : Identification de la source du taux via des templates centralisés.
- Maintien du correctif critique EUS=F (Détection Prix vs Rendement).
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
import yfinance as yf

# Importation de la logique de matrice pays et des textes centralisés
from infra.ref_data.country_matrix import get_country_context
# DT-001/002: Import depuis core.i18n
from src.i18n import StrategySources
from src.config.constants import MacroDefaults

logger = logging.getLogger(__name__)

# Tickers de secours par devise (si le pays est inconnu ou absent de la matrice)
RISK_FREE_TICKERS_FALLBACK: Dict[str, str] = {
    "USD": "^TNX",      # US 10Y Treasury
    "EUR": "EUS=F",     # Future €STR (Proxy Taux Court/Long EUR)
    "CAD": "^GSPTSE",   # Canada Proxy
    "GBP": "^GJGB10",   # UK Gilt 10Y
    "JPY": "^JGBS10",   # Japan  Japanese Government Bond 10Y
    "CNY": "^CN10Y",    # China 10Y
}

MARKET_TICKER = "^GSPC"


@dataclass
class MacroContext:
    """Contient les paramètres macro-économiques avec traçabilité d'audit."""
    date: datetime
    currency: str
    risk_free_rate: float
    risk_free_source: str  # Source pour l'audit (utilisant StrategySources)
    market_risk_premium: float
    perpetual_growth_rate: float
    corporate_aaa_yield: float


class YahooMacroProvider:
    """
    Fournit les données macro (Rf, MRP, Yield AAA) via Yahoo Finance.
    Priorise la précision par pays avant de basculer sur des fallbacks monétaires.
    """

    def __init__(self):
        # Cache indexé par Ticker (et non par devise) pour éviter les collisions
        self._rf_cache: Dict[str, pd.Series] = {}
        # Spread par défaut AAA corporate (70 bps)
        self.DEFAULT_AAA_SPREAD = MacroDefaults.DEFAULT_AAA_SPREAD

    @staticmethod
    def _fetch_history_robust(ticker_obj: yf.Ticker) -> pd.DataFrame:
        """Récupère l'historique avec résilience sur les périodes (Fix yfinance)."""
        for period in ["max", "10y", "5y", "1y"]:
            try:
                data = ticker_obj.history(period=period, interval="1d", auto_adjust=False)
                if not data.empty and "Close" in data.columns:
                    return data
            except Exception as e:
                logger.debug(f"[Macro] Echec fetch {ticker_obj.ticker} ({period}): {e}")
                continue
        return pd.DataFrame()

    def _load_risk_free_series(self, ticker: str) -> Optional[pd.Series]:
        """
        Charge l'historique Rf pour un ticker donné.
        Gère la normalisation Prix -> Taux (EUS=F) et Pourcentage -> Décimal.
        """
        if ticker in self._rf_cache:
            return self._rf_cache[ticker]

        logger.info(f"[Macro] Acquisition Rf pour le ticker : {ticker}")

        try:
            yt = yf.Ticker(ticker)
            data = self._fetch_history_robust(yt)

            if data.empty:
                logger.warning(f"[Macro] No data available | ticker={ticker}")
                return None

            # Normalisation temporelle
            idx = pd.to_datetime(data.index)
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            data.index = idx

            # --- LOGIQUE DE CORRECTION DES TAUX ---
            if ticker == "EUS=F":
                # Correctif Critique : Détection format Prix (~96.50) vs Taux (~3.50)
                raw_values = data["Close"].copy()
                is_price_format = raw_values > 20.0
                raw_values.loc[is_price_format] = 100.0 - raw_values.loc[is_price_format]
                series = (raw_values / 100.0).rename("Risk_Free_Rate")
            else:
                # Yield standard (ex: 4.2 pour 4.2%) -> conversion en 0.042
                series = (data["Close"] / 100.0).rename("Risk_Free_Rate")

            self._rf_cache[ticker] = series
            return series

        except Exception as e:
            logger.error(f"[Macro] Critical loading error | ticker={ticker}, error={e}")
            return None

    def _estimate_aaa_yield(self, risk_free_rate: float) -> float:
        """Estime le rendement corporate AAA (Rf + Spread)."""
        return risk_free_rate + self.DEFAULT_AAA_SPREAD

    def get_macro_context(
            self,
            date: datetime,
            currency: str,
            country_name: Optional[str] = None,
            base_mrp: float = MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM,
            base_g_inf: float = MacroDefaults.DEFAULT_INFLATION_RATE,
    ) -> Optional[MacroContext]:
        """
        Génère le contexte macro complet avec une hiérarchie de décision :
        1. Country Matrix (Précision pays)
        2. Fallback Devise (Sécurité monétaire)
        3. Fallback Système (Survie du calcul)
        """
        currency = currency.upper()
        date = date.replace(tzinfo=None)

        # 1. RÉSOLUTION DU TICKER ET DE LA SOURCE (Délégation SOLID + i18n)
        country_data = get_country_context(country_name)

        # On cherche le ticker dans la matrice, sinon fallback devise
        ticker = country_data.get("rf_ticker") if country_name else None

        if ticker:
            source_label = StrategySources.MACRO_MATRIX.format(ticker=ticker)
        else:
            ticker = RISK_FREE_TICKERS_FALLBACK.get(currency, "^TNX")
            source_label = StrategySources.MACRO_CURRENCY_FALLBACK.format(ticker=ticker)

        # 2. ACQUISITION DU TAUX (Rf)
        rf_value = MacroDefaults.FALLBACK_RISK_FREE_RATE_USD if currency != "EUR" else MacroDefaults.FALLBACK_RISK_FREE_RATE_EUR
        rf_series = self._load_risk_free_series(ticker)

        if rf_series is not None:
            past_data = rf_series[rf_series.index <= date]
            if not past_data.empty:
                rf_value = float(past_data.iloc[-1])
                # Protection Gordon : Plancher à 0.1% pour éviter la divergence
                rf_value = max(rf_value, 0.001)
            else:
                # Si l'historique API échoue, on tente la valeur statique de la matrice
                if country_name:
                    rf_value = country_data.get("risk_free_rate", rf_value)
                    source_label = StrategySources.MACRO_STATIC_FALLBACK

        # 3. EXTRACTION DES PARAMÈTRES MRP & INFLATION (Priorité Matrice)
        if country_name:
            base_mrp = country_data.get("market_risk_premium", base_mrp)
            base_g_inf = country_data.get("inflation_rate", base_g_inf)

        # 4. CONSTRUCTION DU CONTEXTE
        return MacroContext(
            date=date,
            currency=currency,
            risk_free_rate=rf_value,
            risk_free_source=source_label,
            market_risk_premium=base_mrp,
            perpetual_growth_rate=base_g_inf,
            corporate_aaa_yield=self._estimate_aaa_yield(rf_value)
        )
