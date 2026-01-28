"""
infra/macro/yahoo_macro_provider.py

MACRO DATA PROVIDER — RATES & RISK PARAMETERS
=============================================
Role: Orchestrates market data acquisition (Rf, MRP, AAA Yield) with country-level localization.

Key Implementations:
- i18n Integration: Uses StrategySources for audit traceability.
- Dynamic Localization: Rf selection based on 'country_matrix.py'.
- Glass Box Traceability: Identifies rate sources via centralized templates.
- EUS=F Critical Fix: Price vs. Yield detection for Eurozone futures.

Architecture: Strategy Pattern (Macro Infrastructure).
Style: Numpy docstrings.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
import yfinance as yf

from infra.ref_data.country_matrix import get_country_context
from src.i18n import StrategySources
from src.config.constants import MacroDefaults

logger = logging.getLogger(__name__)

# Fallback tickers by currency if country-specific data is missing
RISK_FREE_TICKERS_FALLBACK: Dict[str, str] = {
    "USD": "^TNX",      # US 10Y Treasury
    "EUR": "EUS=F",     # Future €STR (Proxy for EUR Long Term)
    "CAD": "^GSPTSE",   # Canada Proxy
    "GBP": "^GJGB10",   # UK Gilt 10Y
    "JPY": "^JGBS10",   # Japan 10Y JGB
    "CNY": "^CN10Y",    # China 10Y
}

MARKET_TICKER = "^GSPC" # S&P 500 for global equity benchmark


@dataclass
class MacroContext:
    """
    Encapsulates macro-economic parameters with audit lineage.

    Attributes
    ----------
    date : datetime
        Reference date for the data snapshot.
    currency : str
        Base currency of the analysis.
    risk_free_rate : float
        Resolved risk-free rate (decimal).
    risk_free_source : str
        Source identifier for audit logs (localized).
    market_risk_premium : float
        Equity Risk Premium (ERP).
    perpetual_growth_rate : float
        Long-term inflation/growth floor (g).
    corporate_aaa_yield : float
        Proxy for low-risk corporate debt yield.
    """
    date: datetime
    currency: str
    risk_free_rate: float
    risk_free_source: str
    market_risk_premium: float
    perpetual_growth_rate: float
    corporate_aaa_yield: float


class YahooMacroProvider:
    """
    Provides macro data (Rf, MRP, AAA Yield) via Yahoo Finance API.
    Prioritizes per-country precision before defaulting to currency fallbacks.
    """

    def __init__(self):
        # Cache indexed by Ticker to prevent currency-based collisions
        self._rf_cache: Dict[str, pd.Series] = {}
        self.DEFAULT_AAA_SPREAD = MacroDefaults.DEFAULT_AAA_SPREAD

    @staticmethod
    def _fetch_history_robust(ticker_obj: yf.Ticker) -> pd.DataFrame:
        """
        Fetches history with resilience across multiple timeframes (yfinance fix).
        """
        for period in ["max", "10y", "5y", "1y"]:
            try:
                data = ticker_obj.history(period=period, interval="1d", auto_adjust=False)
                if not data.empty and "Close" in data.columns:
                    return data
            except Exception as e:
                logger.debug(f"[Macro] Fetch failed for {ticker_obj.ticker} ({period}): {e}")
                continue
        return pd.DataFrame()

    def _load_risk_free_series(self, ticker: str) -> Optional[pd.Series]:
        """
        Loads Rf history and handles normalization (Price -> Rate) for specific tickers.
        """
        if ticker in self._rf_cache:
            return self._rf_cache[ticker]

        logger.info(f"[Macro] Acquiring Risk-Free series for ticker: {ticker}")

        try:
            yt = yf.Ticker(ticker)
            data = self._fetch_history_robust(yt)

            if data.empty:
                logger.warning(f"[Macro] No data available for {ticker}")
                return None

            # Temporal normalization
            idx = pd.to_datetime(data.index)
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            data.index = idx

            # --- RATE CORRECTION LOGIC ---
            if ticker == "EUS=F":
                # Critical Fix: Detect Price format (~96.50) vs Yield format (~3.50)
                # For Eurozone futures, Price = 100 - Rate
                raw_values = data["Close"].copy()
                is_price_format = raw_values > 20.0
                raw_values.loc[is_price_format] = 100.0 - raw_values.loc[is_price_format]
                series = (raw_values / 100.0).rename("Risk_Free_Rate")
            else:
                # Standard Yield (e.g., 4.2 for 4.2%) -> convert to 0.042
                series = (data["Close"] / 100.0).rename("Risk_Free_Rate")

            self._rf_cache[ticker] = series
            return series

        except Exception as e:
            logger.error(f"[Macro] Critical loading error | ticker={ticker}, error={e}")
            return None

    def _estimate_aaa_yield(self, risk_free_rate: float) -> float:
        """Estimates Corporate AAA Yield as Rf + Default AAA Spread."""
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
        Generates a complete macro context using a strict decision hierarchy.
        """
        currency = currency.upper()
        date = date.replace(tzinfo=None)



        # 1. RESOLVE TICKER & SOURCE
        country_data = get_country_context(country_name)
        ticker = country_data.get("rf_ticker") if country_name else None

        if ticker:
            source_label = StrategySources.MACRO_MATRIX.format(ticker=ticker)
        else:
            ticker = RISK_FREE_TICKERS_FALLBACK.get(currency, "^TNX")
            source_label = StrategySources.MACRO_CURRENCY_FALLBACK.format(ticker=ticker)

        # 2. ACQUIRE RISK-FREE RATE (Rf)
        rf_value = MacroDefaults.FALLBACK_RISK_FREE_RATE_USD if currency != "EUR" else MacroDefaults.FALLBACK_RISK_FREE_RATE_EUR
        rf_series = self._load_risk_free_series(ticker)

        if rf_series is not None:
            past_data = rf_series[rf_series.index <= date]
            if not past_data.empty:
                rf_value = float(past_data.iloc[-1])
                # Gordon-Shapiro Safety: Floor at 0.1% to prevent divergence in DCF models
                rf_value = max(rf_value, 0.001)
            else:
                # Fallback to static matrix data if API history fails
                if country_name:
                    rf_value = country_data.get("risk_free_rate", rf_value)
                    source_label = StrategySources.MACRO_STATIC_FALLBACK

        # 3. EXTRACT MRP & INFLATION (Matrix Priority)
        if country_name:
            base_mrp = country_data.get("market_risk_premium", base_mrp)
            base_g_inf = country_data.get("inflation_rate", base_g_inf)

        # 4. CONTEXT CONSTRUCTION
        return MacroContext(
            date=date,
            currency=currency,
            risk_free_rate=rf_value,
            risk_free_source=source_label,
            market_risk_premium=base_mrp,
            perpetual_growth_rate=base_g_inf,
            corporate_aaa_yield=self._estimate_aaa_yield(rf_value)
        )