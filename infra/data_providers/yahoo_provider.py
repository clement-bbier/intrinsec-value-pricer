"""
infra/data_providers/yahoo_provider.py

YAHOO FINANCE DATA PROVIDER
===========================
Orchestrates financial data acquisition with automated fallback systems.
Role: Bridges raw API data with validated domain models (ST-4.1).

Architecture: Provider Pattern with Degraded Mode support.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, Any

import pandas as pd
import streamlit as st
import yfinance as yf
from pydantic import ValidationError

from src.computation.financial_math import (
    calculate_synthetic_cost_of_debt,
    calculate_sustainable_growth,
    calculate_historical_share_growth
)
from src.exceptions import ExternalServiceError, TickerNotFoundError
from src.models import (
    Company,
    Parameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloParameters,
    MultiplesData
)
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData, YahooRawFetcher
from infra.data_providers.financial_normalizer import FinancialDataNormalizer
from infra.data_providers.extraction_utils import calculate_historical_cagr, safe_api_call
from infra.macro.yahoo_macro_provider import MacroContext, YahooMacroProvider
from infra.ref_data.country_matrix import get_country_context
from infra.ref_data.sector_fallback import get_sector_fallback_with_metadata
from src.i18n import StrategySources, WorkflowTexts
from src.config import PeerDefaults

logger = logging.getLogger(__name__)


@dataclass
class DataProviderStatus:
    """Provider state tracker for monitoring data lineage and fallback triggers."""
    is_degraded_mode: bool = False
    degraded_reason: str = ""
    fallback_sources: List[str] = field(default_factory=list)
    confidence_score: float = 1.0

    def add_fallback(self, source: str) -> None:
        """Logs a fallback event and adjusts the reliability confidence score."""
        self.is_degraded_mode = True
        self.fallback_sources.append(source)
        # Reduction penalty per fallback layer used
        self.confidence_score = max(0.5, self.confidence_score - 0.15)


class YahooFinanceProvider(DataProvider):
    """
    Yahoo Finance Orchestrator.

    Integrates localized macro context, SGR (Sustainable Growth Rate) arbitrage,
    and peer cohort management. Implements ST-4.1 automatic fallback logic
    to ensure valuation continuity even during partial API outages.
    """

    MARKET_SUFFIXES: List[str] = [".PA", ".L", ".DE", ".AS", ".MI", ".MC", ".BR"]
    MAX_RETRY_ATTEMPTS: int = 1

    # ST-4.1 Valuation Sanity Thresholds for Peer Discovery
    MIN_PE_RATIO: float = 1.0
    MAX_PE_RATIO: float = 500.0
    MIN_EV_EBITDA: float = 0.5
    MAX_EV_EBITDA: float = 100.0

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider
        self.fetcher = YahooRawFetcher()
        self.normalizer = FinancialDataNormalizer()
        self.last_raw_data: Optional[RawFinancialData] = None
        self.status = DataProviderStatus()

    # =========================================================================
    # PUBLIC INTERFACE (ST-4.1 Implementation)
    # =========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> Company:
        """Fetches and normalizes core financial data for the target entity."""
        normalized_ticker = ticker.upper().strip()
        return _self._fetch_financials_with_fallback(normalized_ticker)

    @st.cache_data(ttl=14400) # 4-hour cache for price history
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Retrieves historical market data for technical validation or backtesting."""
        return _self.fetcher.fetch_price_history(ticker, period)

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_peer_multiples(_self, ticker: str, manual_peers: Optional[List[str]] = None) -> MultiplesData:
        """
        Orchestrates peer discovery and relative valuation triangulation.
        Uses a robust fallback to static sector multiples if discovery fails.
        """
        _max_peers = PeerDefaults.MAX_PEERS_ANALYSIS

        with st.status(WorkflowTexts.STATUS_PEER_DISCOVERY) as status:
            raw_peers = []
            api_failed = False

            try:
                if manual_peers:
                    # Expert mode: specific analyst-defined cohort
                    logger.info(f"[Provider] Using manual analyst cohort for {ticker}")
                    selected_tickers = manual_peers[:_max_peers]
                    total_peers = len(selected_tickers)

                    for i, p_ticker in enumerate(selected_tickers, 1):
                        status.write(WorkflowTexts.STATUS_PEER_FETCHING.format(current=i, total=total_peers))
                        p_info = safe_api_call(lambda: yf.Ticker(p_ticker).info, f"PeerInfo/{p_ticker}", 1)
                        if p_info:
                            p_info["symbol"] = p_ticker
                            raw_peers.append(p_info)
                else:
                    # Automated discovery via yfinance internals
                    logger.debug(f"[Provider] Discovering comparable peers for {ticker}")
                    all_discovered = _self.fetcher.fetch_peer_multiples(ticker)
                    if all_discovered:
                        raw_peers = all_discovered[:_max_peers]
            except (ValueError, RuntimeError) as e:
                logger.warning(f"[Provider] Peer discovery failed for {ticker}: {e}")
                api_failed = True

            # ST-4.1: Seamless transition to Sector Fallback if live data is missing or corrupted
            if not raw_peers or api_failed:
                return _self._fallback_to_sector_multiples(ticker, status)

            multiples_summary = _self.normalizer.normalize_peers(raw_peers)

            # Robustness check: filter out statistical outliers before triangulation
            if not _self._validate_multiples(multiples_summary):
                logger.warning(f"[Provider] Extreme multiples detected for {ticker}, reverting to sector medians.")
                return _self._fallback_to_sector_multiples(ticker, status)

            status.update(label=WorkflowTexts.PEER_SUCCESS, state="complete")
            return multiples_summary

    def get_company_financials_and_parameters(
            self,
            ticker: str,
            projection_years: int
    ) -> Tuple[Company, Parameters]:
        """
        Automated Workflow: High-level orchestration for Pillar 1 (Configuration).
        Combines fundamental financials with dynamic macro-economic rate resolution.
        """
        # 1. Core Data Acquisition
        financials = self.get_company_financials(ticker)
        macro = self._fetch_macro_context(financials)

        # 2. Growth & Dilution Arbitrage
        growth_hist = self._estimate_dynamic_growth(ticker)

        # Historical Share Count analysis for SBC Dilution (Stock-Based Comp)
        shares_history = self.normalizer.extract_shares_history(
            self.last_raw_data.balance_sheet if self.last_raw_data else None
        )
        dilution_auto = calculate_historical_share_growth(shares_history)

        # Sectoral SBC heuristic for Tech/Healthcare if historical data is flat
        if dilution_auto < 0.001:
            sector_map = {"Technology": 0.02, "Healthcare": 0.01}
            dilution_auto = sector_map.get(financials.sector, 0.0)

        # 3. Sustainable Growth Rate (SGR) calculation
        payout = (financials.dividend_share * financials.shares_outstanding) / financials.net_income_ttm \
            if financials.net_income_ttm and financials.net_income_ttm > 0 else 0.0

        roe = financials.net_income_ttm / financials.book_value \
            if financials.book_value and financials.book_value > 0 else 0.0

        growth_sgr = calculate_sustainable_growth(roe, payout)

        # Final growth cap (Prudence principle: min of Historical vs SGR vs 8% ceiling)
        growth_final = max(0.01, min(growth_hist, growth_sgr or 0.05, 0.08))

        # 4. Regional Macro Parameterization (Tax, Rf, MRP)
        country_data = get_country_context(financials.country)

        params = Parameters(
            rates=CoreRateParameters(
                risk_free_rate=macro.risk_free_rate,
                risk_free_source=macro.risk_free_source,
                market_risk_premium=macro.market_risk_premium,
                corporate_aaa_yield=macro.corporate_aaa_yield,
                cost_of_debt=calculate_synthetic_cost_of_debt(
                    macro.risk_free_rate, financials.ebit_ttm,
                    financials.interest_expense, financials.market_cap
                ),
                tax_rate=float(country_data["tax_rate"])
            ),
            growth=GrowthParameters(
                fcf_growth_rate=growth_final,
                perpetual_growth_rate=macro.perpetual_growth_rate,
                projection_years=projection_years,
                annual_dilution_rate=dilution_auto,
                target_equity_weight=financials.market_cap,
                target_debt_weight=financials.total_debt,
                manual_dividend_base=financials.dividend_share
            ),
            monte_carlo=MonteCarloParameters()
        )

        params.normalize_weights()
        return financials, params

    # =========================================================================
    # INTERNAL LOGIC & FALLBACKS (PROTECTED)
    # =========================================================================

    def _validate_multiples(self, multiples: MultiplesData) -> bool:
        """Validates median multiples against institutional sector sanity bounds."""
        if multiples.median_pe > 0:
            if not (self.MIN_PE_RATIO <= multiples.median_pe <= self.MAX_PE_RATIO):
                return False

        if multiples.median_ev_ebitda > 0:
            if not (self.MIN_EV_EBITDA <= multiples.median_ev_ebitda <= self.MAX_EV_EBITDA):
                return False

        return True

    def _fallback_to_sector_multiples(self, ticker: str, status: Any) -> MultiplesData:
        """Switches to Degraded Mode using curated sectoral fallback data (ST-4.1)."""
        sector = "default"
        try:
            ticker_info = safe_api_call(lambda: yf.Ticker(ticker).info, f"SectorInfo/{ticker}", 1)
            if ticker_info:
                sector = ticker_info.get("sector", "default")
        except (ValueError, AttributeError):
            pass

        fallback_result = get_sector_fallback_with_metadata(sector)
        self.status.add_fallback(fallback_result.source_description)
        self.status.degraded_reason = f"API cohort unavailable for {ticker}"

        status.update(
            label=f"{WorkflowTexts.STATUS_DEGRADED_LABEL} ({sector})",
            state="complete"
        )
        logger.info(f"[Provider] Sector fallback activated for {ticker} | sector={sector}")

        return fallback_result.multiples

    def _estimate_dynamic_growth(self, ticker: str) -> float:
        """Estimates Revenue/FCF CAGR with fallback heuristics."""
        try:
            df = safe_api_call(lambda: self.fetcher.fetch_all(ticker).cash_flow, "Hist FCF Growth")
            cagr = calculate_historical_cagr(df)
            return max(0.01, min(cagr or 0.03, 0.10))
        except (ValueError, AttributeError):
            return 0.03

    def _fetch_financials_with_fallback(self, ticker: str, _attempt: int = 0) -> Company:
        """Executes fetching with automatic market-suffix retry (.PA, .L, etc.)."""
        try:
            result = self._fetch_and_normalize(ticker)
            if result is not None:
                return result
            return self._attempt_market_suffix_fallback(ticker, _attempt)
        except TickerNotFoundError:
            raise
        except ValidationError as ve:
            raise ExternalServiceError(provider="Yahoo/Pydantic", error_detail=str(ve)) from ve
        except (RuntimeError, ValueError) as e:
            raise ExternalServiceError(provider="Yahoo Finance", error_detail=str(e)) from e

    def _fetch_and_normalize(self, ticker: str) -> Optional[Company]:
        """Core execution pipeline: Acquisition -> Normalization."""
        self.last_raw_data = self.fetcher.fetch_historical_deep(ticker)
        return self.normalizer.normalize(self.last_raw_data)

    def _attempt_market_suffix_fallback(self, original_ticker: str, current_attempt: int) -> Company:
        """Handles European stock symbols by attempting automatic suffix injection."""
        if current_attempt >= self.MAX_RETRY_ATTEMPTS or any(original_ticker.upper().endswith(s) for s in self.MARKET_SUFFIXES):
            raise TickerNotFoundError(ticker=original_ticker)

        ticker_with_suffix = f"{original_ticker}.PA" # Priority to Euronext Paris
        try:
            logger.debug(f"[Provider] Retrying with suffix: {ticker_with_suffix}")
            result = self._fetch_and_normalize(ticker_with_suffix)
            if result is not None:
                return result
        except (ValueError, AttributeError):
            pass
        raise TickerNotFoundError(ticker=original_ticker)

    def _fetch_macro_context(self, financials: Company) -> MacroContext:
        """Retrieves country-specific macro parameters (Rf, MRP, Inflation)."""
        try:
            return self.macro_provider.get_macro_context(
                date=datetime.now(),
                currency=financials.currency,
                country_name=financials.country
            )
        except (ValueError, RuntimeError) as e:
            logger.error(f"MacroContext failed for {financials.country}: {e}. Using static fallback.")
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

    def map_raw_to_financials(self, raw: RawFinancialData) -> Optional[Company]:
        """Facade for normalization, used primarily in Backtesting temporal loops."""
        return self.normalizer.normalize(raw)