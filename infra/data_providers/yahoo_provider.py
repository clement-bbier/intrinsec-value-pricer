"""
infra/data_providers/yahoo_provider.py

FOURNISSEUR DE DONNÉES — YAHOO FINANCE
Version : V9.0 — Clean Architecture (Découplé)
Rôle : Orchestration et interface publique avec cache.

Architecture :
- YahooRawFetcher : Appels API bruts
- FinancialDataNormalizer :  Reconstruction des métriques
- YahooFinanceProvider :  Orchestration + cache + fallback
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st
import yfinance as yf
from pydantic import ValidationError

from core.computation.financial_math import calculate_synthetic_cost_of_debt
from core.exceptions import ExternalServiceError, TickerNotFoundError
from core.models import CompanyFinancials, DCFParameters
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_raw_fetcher import YahooRawFetcher
from infra.data_providers.financial_normalizer import FinancialDataNormalizer
from infra.data_providers.extraction_utils import calculate_historical_cagr, safe_api_call
from infra.macro.yahoo_macro_provider import MacroContext, YahooMacroProvider
from infra.ref_data.country_matrix import COUNTRY_CONTEXT, DEFAULT_COUNTRY

logger = logging.getLogger(__name__)


class YahooFinanceProvider(DataProvider):
    """
    Fournisseur de données Yahoo Finance avec architecture découplée.

    Compose :
    - YahooRawFetcher : Transport des données brutes
    - FinancialDataNormalizer :  Transformation en CompanyFinancials

    Responsabilités :
    - Cache Streamlit
    - Fallback suffixes de marché
    - Orchestration du workflow Auto-Mode
    """

    MARKET_SUFFIXES:  List[str] = [".PA", ".L", ".DE", ".AS", ".MI", ".MC", ".BR"]
    MAX_RETRY_ATTEMPTS: int = 1

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider
        self.fetcher = YahooRawFetcher()
        self.normalizer = FinancialDataNormalizer()

    # =========================================================================
    # INTERFACE PUBLIQUE (DataProvider)
    # =========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        """
        Récupère et normalise les états financiers.
        Point d'entrée public avec cache Streamlit.
        """
        normalized_ticker = ticker.upper().strip()
        return _self._fetch_financials_with_fallback(normalized_ticker)

    @st.cache_data(ttl=3600 * 4)
    def get_price_history(_self, ticker: str, period:  str = "5y") -> pd.DataFrame:
        """Récupère l'historique des prix pour les graphiques."""
        return _self.fetcher.fetch_price_history(ticker, period)

    def get_company_financials_and_parameters(
        self,
        ticker: str,
        projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """Workflow Auto-Mode :  récupère financials et paramètres."""
        financials = self.get_company_financials(ticker)
        macro = self._fetch_macro_context(financials)

        growth_estimated = self._estimate_dynamic_growth(ticker)
        tax_rate = float(
            COUNTRY_CONTEXT.get(financials.country, DEFAULT_COUNTRY)["tax_rate"]
        )

        cost_of_debt = calculate_synthetic_cost_of_debt(
            rf=macro.risk_free_rate,
            ebit=financials.ebit_ttm or 1.0,
            interest_expense=financials.interest_expense,
            market_cap=financials.market_cap
        )

        params = DCFParameters(
            risk_free_rate=macro.risk_free_rate,
            market_risk_premium=macro.market_risk_premium,
            corporate_aaa_yield=macro.corporate_aaa_yield,
            cost_of_debt=cost_of_debt,
            tax_rate=tax_rate,
            fcf_growth_rate=growth_estimated,
            perpetual_growth_rate=macro.perpetual_growth_rate,
            projection_years=projection_years,
            target_equity_weight=financials.market_cap,
            target_debt_weight=financials.total_debt
        )
        params.normalize_weights()

        return financials, params

    # =========================================================================
    # LOGIQUE DE FETCH AVEC FALLBACK
    # =========================================================================

    def _fetch_financials_with_fallback(
        self,
        ticker: str,
        _attempt: int = 0
    ) -> CompanyFinancials:
        """
        Fetch avec fallback contrôlé sur les suffixes de marché.

        Garanties :
        - Maximum 1 retry avec suffixe
        - Pas de retry si le ticker a déjà un suffixe connu
        """
        logger.info("[Yahoo] Fetching financials for %s.. .", ticker)

        try:
            result = self._fetch_and_normalize(ticker)
            if result is not None:
                return result

            return self._attempt_market_suffix_fallback(ticker, _attempt)

        except TickerNotFoundError:
            raise
        except ValidationError as ve:
            raise ExternalServiceError(provider="Yahoo/Pydantic", error_detail=str(ve)) from ve
        except (ConnectionError, TimeoutError, KeyError) as e:
            raise ExternalServiceError(provider="Yahoo Finance", error_detail=str(e)) from e

    def _fetch_and_normalize(self, ticker: str) -> Optional[CompanyFinancials]:
        """Fetch brut + normalisation."""
        raw_data = self.fetcher.fetch_all(ticker)
        return self.normalizer.normalize(raw_data)

    def _attempt_market_suffix_fallback(
        self,
        original_ticker: str,
        current_attempt: int
    ) -> CompanyFinancials:
        """
        Tente un fallback avec suffixe de marché européen.

        Règles strictes :
        1. Maximum MAX_RETRY_ATTEMPTS tentatives
        2. Pas de retry si le ticker a déjà un suffixe connu
        3. Lève TickerNotFoundError si échec
        """
        if current_attempt >= self.MAX_RETRY_ATTEMPTS:
            logger.warning("[Yahoo] Retry limit reached for %s", original_ticker)
            raise TickerNotFoundError(ticker=original_ticker)

        if self._has_market_suffix(original_ticker):
            logger.warning("[Yahoo] Ticker %s with suffix not found", original_ticker)
            raise TickerNotFoundError(ticker=original_ticker)

        ticker_with_suffix = f"{original_ticker}.PA"
        logger.info("[Yahoo] Trying fallback:  %s -> %s", original_ticker, ticker_with_suffix)

        try:
            result = self._fetch_and_normalize(ticker_with_suffix)
            if result is not None:
                return result
        except (ValidationError, ConnectionError, KeyError) as e:
            logger.debug("[Yahoo] Fallback failed for %s: %s", ticker_with_suffix, e)

        raise TickerNotFoundError(ticker=original_ticker)

    def _has_market_suffix(self, ticker: str) -> bool:
        """Vérifie si le ticker possède déjà un suffixe de marché."""
        return any(ticker.upper().endswith(suffix) for suffix in self.MARKET_SUFFIXES)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _fetch_macro_context(self, financials: CompanyFinancials) -> MacroContext:
        """Récupère le contexte macro avec fallback sécurisé."""
        try:
            return self.macro_provider.get_macro_context(
                date=datetime.now(),
                currency=financials.currency
            )
        except (ValueError, KeyError, ConnectionError):
            country_data = COUNTRY_CONTEXT.get(financials.country, DEFAULT_COUNTRY)
            return MacroContext(
                date=datetime.now(),
                currency=financials.currency,
                risk_free_rate=float(country_data["risk_free_rate"]),
                market_risk_premium=float(country_data["market_risk_premium"]),
                perpetual_growth_rate=float(country_data["inflation_rate"]),
                corporate_aaa_yield=float(country_data["risk_free_rate"] + 0.01)
            )

    def _estimate_dynamic_growth(self, ticker: str) -> float:
        """Estime la croissance via CAGR historique."""
        try:
            yt = yf.Ticker(ticker)
            hist_cf = safe_api_call(lambda:  yt.cash_flow, "Hist Growth")
            cagr = calculate_historical_cagr(hist_cf, "Free Cash Flow")
            return max(0.01, min(cagr or 0.03, 0.10))
        except (ValueError, KeyError, ZeroDivisionError):
            return 0.03