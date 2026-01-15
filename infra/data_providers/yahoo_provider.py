"""
infra/data_providers/yahoo_provider.py
FOURNISSEUR DE DONNÉES — YAHOO FINANCE — VERSION V11.0 (Sprint 4)
Rôle : Orchestration, acquisition macro localisée et instanciation des paramètres.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st
import yfinance as yf
from pydantic import ValidationError

from core.computation.financial_math import (
    calculate_synthetic_cost_of_debt,
    calculate_sustainable_growth
)
from core.exceptions import ExternalServiceError, TickerNotFoundError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    ValuationMode
)
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_raw_fetcher import YahooRawFetcher
from infra.data_providers.financial_normalizer import FinancialDataNormalizer
from infra.data_providers.extraction_utils import calculate_historical_cagr, safe_api_call
from infra.macro.yahoo_macro_provider import MacroContext, YahooMacroProvider
from infra.ref_data.country_matrix import get_country_context
from app.ui_components.ui_texts import StrategySources

logger = logging.getLogger(__name__)


class YahooFinanceProvider(DataProvider):
    """
    Orchestrateur de données Yahoo Finance.
    Intègre l'intelligence macro par pays et l'arbitrage de croissance SGR.
    """

    MARKET_SUFFIXES: List[str] = [".PA", ".L", ".DE", ".AS", ".MI", ".MC", ".BR"]
    MAX_RETRY_ATTEMPTS: int = 1

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider
        self.fetcher = YahooRawFetcher()
        self.normalizer = FinancialDataNormalizer()

    # =========================================================================
    # INTERFACE PUBLIQUE
    # =========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        normalized_ticker = ticker.upper().strip()
        return _self._fetch_financials_with_fallback(normalized_ticker)

    @st.cache_data(ttl=3600 * 4)
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
        return _self.fetcher.fetch_price_history(ticker, period)

    def get_company_financials_and_parameters(
        self,
        ticker: str,
        projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """Workflow Auto-Mode : Construit les paramètres avec macro localisée et arbitrage SGR."""
        financials = self.get_company_financials(ticker)

        # 1. ACQUISITION MACRO DYNAMIQUE (Phase 2 : Passage du pays)
        macro = self._fetch_macro_context(financials)

        # 2. Estimation de la croissance hybride (Dividendes vs FCF)
        growth_metric = "Dividends" if financials.dividend_share and financials.dividend_share > 0 else "Free Cash Flow"
        growth_hist = self._estimate_dynamic_growth(ticker, metric=growth_metric)

        # 3. Rigueur SGR (Sustainable Growth Rate)
        payout = (financials.dividend_share * financials.shares_outstanding) / financials.net_income_ttm if financials.net_income_ttm and financials.net_income_ttm > 0 else 0.0
        roe = financials.net_income_ttm / financials.book_value if financials.book_value and financials.book_value > 0 else 0.0
        growth_sgr = calculate_sustainable_growth(roe, payout)

        # Arbitrage AUTO : Conservatisme (max 8% en mode auto)
        growth_final = max(0.01, min(growth_hist, growth_sgr or 0.05, 0.08))

        # 4. Coût de la dette
        cost_of_debt = calculate_synthetic_cost_of_debt(
            rf=macro.risk_free_rate,
            ebit=financials.ebit_ttm,
            interest_expense=financials.interest_expense,
            market_cap=financials.market_cap
        )

        # 5. Récupération du taux d'imposition (Précision pays via Matching Résilient)
        country_data = get_country_context(financials.country)

        params = DCFParameters(
            rates=CoreRateParameters(
                risk_free_rate=macro.risk_free_rate,
                risk_free_source=macro.risk_free_source, # Utilisation de StrategySources via MacroContext
                market_risk_premium=macro.market_risk_premium,
                corporate_aaa_yield=macro.corporate_aaa_yield,
                cost_of_debt=cost_of_debt,
                tax_rate=float(country_data["tax_rate"])
            ),
            growth=GrowthParameters(
                fcf_growth_rate=growth_final,
                perpetual_growth_rate=macro.perpetual_growth_rate,
                projection_years=projection_years,
                target_equity_weight=financials.market_cap,
                target_debt_weight=financials.total_debt,
                manual_dividend_base=financials.dividend_share
            ),
            monte_carlo=MonteCarloConfig()
        )
        params.normalize_weights()
        return financials, params

    # =========================================================================
    # LOGIQUE DE FETCH ET ESTIMATION
    # =========================================================================

    def _estimate_dynamic_growth(self, ticker: str, metric: str = "Free Cash Flow") -> float:
        """Estime la croissance via CAGR historique (FCF ou Dividendes)."""
        try:
            yt = yf.Ticker(ticker)
            if metric == "Free Cash Flow":
                df = safe_api_call(lambda: yt.cash_flow, "Hist FCF Growth")
                cagr = calculate_historical_cagr(df, "Free Cash Flow")
            else:
                divs = safe_api_call(lambda: yt.dividends, "Hist Div Growth")
                if divs is None or divs.empty: return 0.03
                divs_annual = divs.resample('YE').sum()
                if len(divs_annual) < 3: return 0.03
                cagr = (divs_annual.iloc[-1] / divs_annual.iloc[-3]) ** (1 / 2) - 1
            return max(0.01, min(cagr or 0.03, 0.10))
        except Exception:
            return 0.03

    def _fetch_financials_with_fallback(self, ticker: str, _attempt: int = 0) -> CompanyFinancials:
        try:
            result = self._fetch_and_normalize(ticker)
            if result is not None: return result
            return self._attempt_market_suffix_fallback(ticker, _attempt)
        except TickerNotFoundError: raise
        except ValidationError as ve: raise ExternalServiceError(provider="Yahoo/Pydantic", error_detail=str(ve)) from ve
        except Exception as e: raise ExternalServiceError(provider="Yahoo Finance", error_detail=str(e)) from e

    def _fetch_and_normalize(self, ticker: str) -> Optional[CompanyFinancials]:
        raw_data = self.fetcher.fetch_all(ticker)
        return self.normalizer.normalize(raw_data)

    def _attempt_market_suffix_fallback(self, original_ticker: str, current_attempt: int) -> CompanyFinancials:
        if current_attempt >= self.MAX_RETRY_ATTEMPTS or any(original_ticker.upper().endswith(s) for s in self.MARKET_SUFFIXES):
            raise TickerNotFoundError(ticker=original_ticker)
        ticker_with_suffix = f"{original_ticker}.PA"
        try:
            result = self._fetch_and_normalize(ticker_with_suffix)
            if result is not None: return result
        except Exception: pass
        raise TickerNotFoundError(ticker=original_ticker)

    def _fetch_macro_context(self, financials: CompanyFinancials) -> MacroContext:
        """
        Orchestre la récupération du contexte macro.
        Injecte désormais le pays pour une résolution dynamique du Rf.
        """
        try:
            return self.macro_provider.get_macro_context(
                date=datetime.now(),
                currency=financials.currency,
                country_name=financials.country # <--- Activation de l'intelligence pays
            )
        except Exception as e:
            logger.error(f"Echec du MacroContext dynamique pour {financials.country}: {e}")
            # Fallback institutionnel via la matrice locale et i18n
            country_data = get_country_context(financials.country)
            return MacroContext(
                date=datetime.now(),
                currency=financials.currency,
                risk_free_rate=float(country_data["risk_free_rate"]),
                risk_free_source=StrategySources.MACRO_API_ERROR,
                market_risk_premium=float(country_data["market_risk_premium"]),
                perpetual_growth_rate=float(country_data["inflation_rate"]),
                corporate_aaa_yield=float(country_data["risk_free_rate"] + 0.01)
            )