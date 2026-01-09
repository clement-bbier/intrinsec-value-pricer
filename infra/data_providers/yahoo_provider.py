"""
infra/data_providers/yahoo_provider.py

FOURNISSEUR DE DONNÉES — YAHOO FINANCE (ULTIMATE V4.0)
Version : V4.0 — Refactored Modular Architecture (Clean Code)

Changelog :
- Refactoring : Décomposition du 'Deep Fetch' en segments logiques (Dette, Action, Profits).
- Stabilité : Centralisation de la logique de normalisation des prix et devises.
- Maintenance : Isolation de la logique de calcul CAGR et Fiscalité.
- Maintien intégral des fonctionnalités V3.8 et du cache Streamlit.
"""

import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import yfinance as yf
import streamlit as st
from pydantic import ValidationError

from core.computation.financial_math import calculate_synthetic_cost_of_debt
from core.exceptions import TickerNotFoundError, ExternalServiceError
from core.models import CompanyFinancials, DCFParameters
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_helpers import (
    safe_api_call,
    get_simple_annual_fcf,
    normalize_currency_and_price,
    extract_most_recent_value,
    calculate_historical_cagr
)
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.ref_data.country_matrix import COUNTRY_CONTEXT, DEFAULT_COUNTRY

logger = logging.getLogger(__name__)

class YahooFinanceProvider(DataProvider):
    """
    Fournisseur de données haute performance utilisant yfinance.
    Architecture modulaire pour faciliter l'audit des données extraites.
    """

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider

    # ==========================================================================
    # 1. POINT D'ENTRÉE PRINCIPAL (CACHE)
    # ==========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        """Récupère et normalise les états financiers via la stratégie Deep Fetch."""
        ticker = ticker.upper().strip()
        logger.info(f"[Yahoo] Deep Fetch initiation for {ticker}...")

        try:
            yt = yf.Ticker(ticker)
            info = safe_api_call(lambda: yt.info, "Info")

            # Validation du Ticker (Gestion des suffixes boursiers)
            if not info or ("currentPrice" not in info and "regularMarketPrice" not in info):
                return _self._handle_missing_ticker(ticker)

            # 1. Extraction des fondations (Prix & Devise)
            currency, current_price = normalize_currency_and_price(info)

            # 2. Acquisition des trois états financiers
            bs = safe_api_call(lambda: yt.balance_sheet, "Balance Sheet")
            is_ = safe_api_call(lambda: yt.income_stmt, "Income Stmt")
            cf = safe_api_call(lambda: yt.cash_flow, "Cash Flow")

            # 3. Reconstruction modulaire (Clean Code)
            shares = _self._reconstruct_shares(info, bs, current_price)
            debt_data = _self._reconstruct_capital_structure(info, bs, is_)
            profit_data = _self._reconstruct_profitability(info, is_, cf)

            return CompanyFinancials(
                ticker=ticker,
                name=str(info.get("shortName", ticker)),
                sector=str(info.get("sector", "Unknown")),
                industry=str(info.get("industry", "Unknown")),
                country=str(info.get("country", "Unknown")),
                currency=currency,
                current_price=float(current_price),
                shares_outstanding=shares,
                **debt_data,
                **profit_data
            )

        except TickerNotFoundError: raise
        except ValidationError as ve:
            raise ExternalServiceError(provider="Yahoo/Pydantic", error_detail=str(ve))
        except Exception as e:
            raise ExternalServiceError(provider="Yahoo Finance", error_detail=str(e))

    # ==========================================================================
    # 2. SEGMENTS LOGIQUES DU DEEP FETCH (PRIVATE HELPERS)
    # ==========================================================================

    def _reconstruct_shares(self, info: Dict, bs: pd.DataFrame, price: float) -> float:
        """Reconstruit le nombre d'actions en circulation."""
        shares = info.get("sharesOutstanding")
        if not shares and bs is not None:
            shares = extract_most_recent_value(bs, ["Ordinary Shares Number", "Share Issued"])

        if not shares: # Fallback par Market Cap
            mcap = info.get("marketCap", 0.0)
            if mcap > 0 and price > 0: shares = mcap / price

        return float(shares) if shares else 1.0

    def _reconstruct_capital_structure(self, info: Dict, bs: pd.DataFrame, is_: pd.DataFrame) -> Dict[str, Any]:
        """Analyse la structure de la dette et du cash."""
        # Dette
        debt = info.get("totalDebt")
        if (not debt or debt == 0) and bs is not None:
            debt = extract_most_recent_value(bs, ["Total Debt", "Net Debt"])
            if not debt:
                std = extract_most_recent_value(bs, ["Current Debt", "Current Debt And Lease Obligation"]) or 0
                ltd = extract_most_recent_value(bs, ["Long Term Debt", "Long Term Debt And Lease Obligation"]) or 0
                debt = std + ltd

        # Cash & Provisions
        cash = info.get("totalCash")
        if (not cash or cash == 0) and bs is not None:
            cash = extract_most_recent_value(bs, ["Cash And Cash Equivalents", "Cash Financial"])

        minority = 0.0
        pensions = 0.0
        if bs is not None:
            minority = extract_most_recent_value(bs, ["Minority Interest", "Non Controlling Interest"]) or 0.0
            pensions = extract_most_recent_value(bs, ["Pension And Other Postretirement Benefit Plans", "Long Term Provisions"]) or 0.0

        # Intérêts
        interest = 0.0
        if is_ is not None:
            val = extract_most_recent_value(is_, ["Interest Expense", "Interest Expense Non Operating"])
            interest = float(abs(val)) if val else 0.0

        return {
            "total_debt": float(debt or 0.0),
            "cash_and_equivalents": float(cash or 0.0),
            "minority_interests": float(minority),
            "pension_provisions": float(pensions),
            "interest_expense": interest
        }

    def _reconstruct_profitability(self, info: Dict, is_: pd.DataFrame, cf: pd.DataFrame) -> Dict[str, Any]:
        """Extrait les métriques de rentabilité et de flux."""
        fcf = get_simple_annual_fcf(cf) or 0.0

        # Dividendes
        div_rate = info.get("dividendRate")
        if div_rate is None:
            dy = info.get("dividendYield", 0.0)
            div_rate = dy * info.get("currentPrice", 0.0) if dy else 0.0

        return {
            "revenue_ttm": float(info.get("totalRevenue") or 0.0),
            "ebitda_ttm": float(info.get("ebitda") or 0.0),
            "net_income_ttm": float(info.get("netIncomeToCommon") or 0.0),
            "eps_ttm": float(info.get("trailingEps") or 0.0),
            "dividend_share": float(div_rate),
            "book_value_per_share": float(info.get("bookValue", 0.0)),
            "beta": float(info.get("beta", 1.0) or 1.0),
            "fcf_last": float(fcf),
            "fcf_fundamental_smoothed": float(fcf)
        }

    def _handle_missing_ticker(self, ticker: str):
        """Gestion intelligente des suffixes boursiers manquants."""
        suffixes = [".PA", ".US", ".L", ".DE"]
        if not any(ticker.endswith(s) for s in suffixes):
            return self.get_company_financials(f"{ticker}.PA")
        raise TickerNotFoundError(ticker=ticker)

    # ==========================================================================
    # 3. WORKFLOW AUTO MODE (PARAM BUILDING)
    # ==========================================================================

    def get_company_financials_and_parameters(
            self, ticker: str, projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """Orchestrateur pour le mode AUTOMATIQUE."""
        financials = self.get_company_financials(ticker)

        # 1. Contexte Macro
        macro_ctx = self._fetch_macro_context(financials)

        # 2. Calculs Dynamiques (g et kd)
        growth_assumption = self._estimate_dynamic_growth(ticker)
        effective_tax_rate = float(COUNTRY_CONTEXT.get(financials.country, DEFAULT_COUNTRY)["tax_rate"])

        kd_synthetic = calculate_synthetic_cost_of_debt(
            rf=macro_ctx.risk_free_rate,
            ebit=financials.fcf_last or 1.0,
            interest_expense=financials.interest_expense,
            market_cap=financials.market_cap
        )

        # 3. Construction des Paramètres
        params = DCFParameters(
            risk_free_rate=macro_ctx.risk_free_rate,
            market_risk_premium=macro_ctx.market_risk_premium,
            corporate_aaa_yield=macro_ctx.corporate_aaa_yield,
            cost_of_debt=kd_synthetic,
            tax_rate=effective_tax_rate,
            fcf_growth_rate=growth_assumption,
            perpetual_growth_rate=macro_ctx.perpetual_growth_rate,
            projection_years=projection_years,
            target_equity_weight=financials.market_cap,
            target_debt_weight=financials.total_debt,
            beta_volatility=0.10,
            growth_volatility=0.015,
            terminal_growth_volatility=0.005,
            correlation_beta_growth=-0.30
        )
        params.normalize_weights()
        return financials, params

    def _fetch_macro_context(self, financials: CompanyFinancials):
        """Récupère le contexte macro avec sécurité fallback pays."""
        try:
            return self.macro_provider.get_macro_context(date=datetime.now(), currency=financials.currency)
        except Exception:
            from infra.macro.yahoo_macro_provider import MacroContext
            c = COUNTRY_CONTEXT.get(financials.country, DEFAULT_COUNTRY)
            return MacroContext(
                date=datetime.now(), currency=financials.currency,
                risk_free_rate=float(c["risk_free_rate"]),
                market_risk_premium=float(c["market_risk_premium"]),
                perpetual_growth_rate=float(c["inflation_rate"]),
                corporate_aaa_yield=float(c["risk_free_rate"] + 0.01)
            )

    def _estimate_dynamic_growth(self, ticker: str) -> float:
        """Estime g via le CAGR historique filtré."""
        try:
            yt = yf.Ticker(ticker)
            hist_cf = safe_api_call(lambda: yt.cash_flow, "Growth History")
            g = calculate_historical_cagr(hist_cf, "Free Cash Flow")
            return max(0.01, min(g, 0.10))
        except Exception:
            return 0.03

    @st.cache_data(ttl=3600 * 4)
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Récupère l'historique de prix pour les graphiques."""
        try:
            return yf.Ticker(ticker).history(period=period)
        except Exception:
            return pd.DataFrame()