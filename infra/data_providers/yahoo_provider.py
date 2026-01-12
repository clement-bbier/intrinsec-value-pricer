"""
infra/data_providers/yahoo_provider.py

FOURNISSEUR DE DONNÉES — YAHOO FINANCE
Version :  V8.3 — Waterfall Deep Fetch & None-Safe Integration
Rôle : Récupération et normalisation des données financières via yfinance.
Architecture : Cascade TTM -> Annual -> Info avec propagation stricte des None.

Fix V8.2 : Correction de la boucle infinie sur tickers inconnus.
Fix V8.3 : Clean code (static methods, exceptions typées, paramètres utilisés).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
import yfinance as yf
from pydantic import ValidationError

from core.computation.financial_math import calculate_synthetic_cost_of_debt
from core.exceptions import ExternalServiceError, TickerNotFoundError
from core.models import CompanyFinancials, DCFParameters
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_helpers import (
    CAPEX_KEYS,
    DA_KEYS,
    calculate_historical_cagr,
    extract_most_recent_value,
    get_simple_annual_fcf,
    normalize_currency_and_price,
    safe_api_call,
)
from infra.macro. yahoo_macro_provider import MacroContext, YahooMacroProvider
from infra.ref_data.country_matrix import COUNTRY_CONTEXT, DEFAULT_COUNTRY

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. FONCTIONS STATIQUES DE VALIDATION
# ==============================================================================

def _is_valid_ticker_info(info: Optional[Dict]) -> bool:
    """Vérifie si les données du ticker sont valides."""
    if not info:
        return False
    return "currentPrice" in info or "regularMarketPrice" in info


def _has_market_suffix(ticker: str, suffixes:  List[str]) -> bool:
    """Vérifie si le ticker possède déjà un suffixe de marché."""
    return any(ticker.upper().endswith(suffix) for suffix in suffixes)


# ==============================================================================
# 2. FONCTIONS STATIQUES DE RECONSTRUCTION
# ==============================================================================

def _reconstruct_shares(
    info: Dict,
    bs: Optional[pd. DataFrame],
    price: float
) -> float:
    """Reconstruit le nombre d'actions avec fallback intelligent."""
    shares = info.get("sharesOutstanding")

    if not shares and bs is not None:
        shares = extract_most_recent_value(bs, ["Ordinary Shares Number", "Share Issued"])

    if not shares:
        mcap = info.get("marketCap", 0.0)
        if mcap > 0 and price > 0:
            shares = mcap / price

    return float(shares) if shares else 1.0


def _extract_total_debt(
    info: Dict,
    bs: Optional[pd.DataFrame]
) -> Optional[float]:
    """Extrait la dette totale avec cascade de fallbacks."""
    debt = info. get("totalDebt")

    if not debt and bs is not None:
        debt = extract_most_recent_value(bs, ["Total Debt", "Net Debt"])
        if not debt:
            std = extract_most_recent_value(
                bs, ["Current Debt", "Current Debt And Lease Obligation"]
            ) or 0
            ltd = extract_most_recent_value(
                bs, ["Long Term Debt", "Long Term Debt And Lease Obligation"]
            ) or 0
            debt = (std + ltd) if (std + ltd) > 0 else None

    return debt


def _extract_cash(
    info: Dict,
    bs: Optional[pd.DataFrame]
) -> Optional[float]:
    """Extrait la trésorerie."""
    cash = info.get("totalCash")

    if not cash and bs is not None:
        cash = extract_most_recent_value(
            bs, ["Cash And Cash Equivalents", "Cash Financial"]
        )

    return cash


def _extract_minority_interests(bs: Optional[pd.DataFrame]) -> Optional[float]:
    """Extrait les intérêts minoritaires."""
    if bs is None:
        return 0.0
    return extract_most_recent_value(
        bs, ["Minority Interest", "Non Controlling Interest"]
    )


def _extract_pension_provisions(bs: Optional[pd.DataFrame]) -> Optional[float]:
    """Extrait les provisions retraite."""
    if bs is None:
        return 0.0
    return extract_most_recent_value(
        bs, ["Long Term Provisions", "Pension And Other Postretirement Benefit Plans"]
    )


def _extract_interest_expense(is_:  Optional[pd.DataFrame]) -> Optional[float]:
    """Extrait les charges d'intérêts."""
    if is_ is None:
        return None
    return extract_most_recent_value(
        is_, ["Interest Expense", "Interest Expense Non Operating"]
    )


def _reconstruct_capital_structure(
    info:  Dict,
    bs: Optional[pd.DataFrame],
    is_: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """Analyse la structure de la dette (None-Safe)."""
    debt = _extract_total_debt(info, bs)
    cash = _extract_cash(info, bs)
    minority = _extract_minority_interests(bs)
    pensions = _extract_pension_provisions(bs)
    interest = _extract_interest_expense(is_)

    return {
        "total_debt":  float(debt) if debt is not None else 0.0,
        "cash_and_equivalents": float(cash) if cash is not None else 0.0,
        "minority_interests": float(minority or 0.0),
        "pension_provisions": float(pensions or 0.0),
        "interest_expense":  float(abs(interest)) if interest is not None else 0.0
    }


def _extract_depreciation_amortization(cf_a: Optional[pd. DataFrame]) -> Optional[float]:
    """Extrait D&A avec agrégation si nécessaire."""
    da = extract_most_recent_value(cf_a, DA_KEYS)

    if da is None and cf_a is not None:
        dep = extract_most_recent_value(cf_a, ["Depreciation"]) or 0
        amo = extract_most_recent_value(cf_a, ["Amortization"]) or 0
        da = (dep + amo) if (dep + amo) > 0 else None

    return da


def _sum_last_4_quarters(df: Optional[pd.DataFrame], keys: List[str]) -> Optional[float]:
    """Calcule la somme des 4 derniers trimestres pour simuler le TTM."""
    if df is None or df.empty:
        return None

    for key in keys:
        if key in df. index:
            last_4 = df.loc[key]. iloc[: 4]
            if len(last_4) == 4 and not last_4.isnull().any():
                return float(last_4.sum())

    return None


def _reconstruct_profitability(
    info: Dict,
    is_a: Optional[pd.DataFrame],
    cf_a: Optional[pd.DataFrame],
    is_q: Optional[pd.DataFrame],
    cf_q: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """Extraction TTM via somme trimestrielle avec agrégation D&A."""
    rev_ttm = _sum_last_4_quarters(is_q, ["Total Revenue", "Revenue"])
    ebit_ttm = _sum_last_4_quarters(is_q, ["EBIT", "Operating Income"])
    ni_ttm = _sum_last_4_quarters(is_q, ["Net Income Common Stockholders", "Net Income"])

    rev_ttm = rev_ttm or info.get("totalRevenue") or extract_most_recent_value(
        is_a, ["Total Revenue"]
    )
    ebit_ttm = ebit_ttm or info.get("operatingCashflow") or extract_most_recent_value(
        is_a, ["EBIT", "Operating Income"]
    )
    ni_ttm = ni_ttm or info. get("netIncomeToCommon") or extract_most_recent_value(
        is_a, ["Net Income"]
    )

    fcf = get_simple_annual_fcf(cf_a)
    fcf_ttm = _sum_last_4_quarters(cf_q, ["Free Cash Flow"]) or fcf
    capex = extract_most_recent_value(cf_a, CAPEX_KEYS)
    da = _extract_depreciation_amortization(cf_a)

    div_rate = info.get("dividendRate") or (
        info.get("dividendYield", 0) * info.get("currentPrice", 0)
    )

    return {
        "revenue_ttm": float(rev_ttm) if rev_ttm is not None else None,
        "ebitda_ttm": float(info.get("ebitda") or 0.0),
        "ebit_ttm": float(ebit_ttm) if ebit_ttm is not None else None,
        "net_income_ttm":  float(ni_ttm) if ni_ttm is not None else None,
        "eps_ttm": float(info. get("trailingEps") or 0.0),
        "dividend_share": float(div_rate or 0.0),
        "book_value_per_share": float(info.get("bookValue") or 0.0),
        "beta": float(info.get("beta") or 1.0),
        "fcf_last": float(fcf_ttm) if fcf_ttm is not None else None,
        "fcf_fundamental_smoothed": float(fcf) if fcf is not None else None,
        "capex":  float(capex) if capex is not None else None,
        "depreciation_and_amortization": float(da) if da is not None else None
    }


def _fetch_raw_financials(ticker: str) -> Optional[CompanyFinancials]:
    """
    Tente de récupérer les données brutes pour un ticker.

    Returns:
        CompanyFinancials si trouvé, None sinon.
    """
    yt = yf.Ticker(ticker)
    info = safe_api_call(lambda: yt.info, "Info")

    if not _is_valid_ticker_info(info):
        return None

    currency, current_price = normalize_currency_and_price(info)

    bs = safe_api_call(lambda: yt.balance_sheet, "Annual BS")
    is_ = safe_api_call(lambda: yt.income_stmt, "Annual IS")
    cf = safe_api_call(lambda:  yt.cash_flow, "Annual CF")
    q_is = safe_api_call(lambda: yt. quarterly_income_stmt, "Quarterly IS")
    q_cf = safe_api_call(lambda: yt. quarterly_cash_flow, "Quarterly CF")

    shares = _reconstruct_shares(info, bs, current_price)
    debt_data = _reconstruct_capital_structure(info, bs, is_)
    profit_data = _reconstruct_profitability(info, is_, cf, q_is, q_cf)

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


def _estimate_dynamic_growth(ticker: str) -> float:
    """Estime la croissance via CAGR historique filtré."""
    try:
        yt = yf.Ticker(ticker)
        hist_cf = safe_api_call(lambda: yt.cash_flow, "Hist Growth")
        cagr = calculate_historical_cagr(hist_cf, "Free Cash Flow")
        return max(0.01, min(cagr or 0.03, 0.10))
    except (ValueError, KeyError, ZeroDivisionError):
        return 0.03


# ==============================================================================
# 3. CLASSE PRINCIPALE DU PROVIDER
# ==============================================================================

class YahooFinanceProvider(DataProvider):
    """
    Fournisseur de données haute performance avec intelligence de cascade.
    Garantit la récupération des métriques les plus récentes pour l'audit.
    """

    MARKET_SUFFIXES = [". PA", ".L", ".DE", ".AS", ".MI", ".MC", ".BR"]
    MAX_RETRY_ATTEMPTS = 1

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider

    # ==========================================================================
    # POINT D'ENTRÉE PRINCIPAL (CACHE)
    # ==========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        """
        Récupère et normalise les états financiers via la cascade TTM/Annual.

        Point d'entrée public avec cache Streamlit.
        """
        normalized_ticker = ticker.upper().strip()
        return _self._fetch_financials_with_fallback(normalized_ticker)

    @st.cache_data(ttl=3600 * 4)
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Récupère l'historique des prix pour les graphiques."""
        try:
            yt = yf.Ticker(ticker)
            hist = yt.history(period=period)
            if hist.empty:
                logger.warning("[Yahoo] Aucun historique trouvé pour %s", ticker)
            return hist
        except (ValueError, KeyError, ConnectionError) as e:
            logger.error("[Yahoo] Erreur historique pour %s: %s", ticker, e)
            return pd.DataFrame()

    # ==========================================================================
    # LOGIQUE DE FETCH AVEC FALLBACK CONTRÔLÉ
    # ==========================================================================

    def _fetch_financials_with_fallback(
        self,
        ticker: str,
        _attempt: int = 0
    ) -> CompanyFinancials:
        """
        Fetch avec fallback contrôlé sur les suffixes de marché.

        Garantit qu'on ne boucle jamais infiniment:
        - Maximum 1 retry avec suffixe
        - Pas de retry si le ticker a déjà un suffixe connu
        """
        logger.info("[Yahoo] Waterfall Fetch initiation for %s.. .", ticker)

        try:
            result = _fetch_raw_financials(ticker)
            if result is not None:
                return result

            return self._attempt_market_suffix_fallback(ticker, _attempt)

        except TickerNotFoundError:
            raise
        except ValidationError as ve:
            raise ExternalServiceError(provider="Yahoo/Pydantic", error_detail=str(ve)) from ve
        except (ConnectionError, TimeoutError, KeyError) as e:
            raise ExternalServiceError(provider="Yahoo Finance", error_detail=str(e)) from e

    def _attempt_market_suffix_fallback(
        self,
        original_ticker: str,
        current_attempt: int
    ) -> CompanyFinancials:
        """
        Tente un fallback avec suffixe de marché européen.

        Règles strictes:
        1. Maximum MAX_RETRY_ATTEMPTS tentatives
        2. Pas de retry si le ticker a déjà un suffixe connu
        3. Lève TickerNotFoundError si toutes les tentatives échouent
        """
        if current_attempt >= self.MAX_RETRY_ATTEMPTS:
            logger.warning("[Yahoo] Limite de retries atteinte pour %s", original_ticker)
            raise TickerNotFoundError(ticker=original_ticker)

        if _has_market_suffix(original_ticker, self.MARKET_SUFFIXES):
            logger.warning("[Yahoo] Ticker %s avec suffixe non trouvé", original_ticker)
            raise TickerNotFoundError(ticker=original_ticker)

        ticker_with_suffix = f"{original_ticker}. PA"
        logger.info("[Yahoo] Ticker %s introuvable, tentative avec %s", original_ticker, ticker_with_suffix)

        try:
            result = _fetch_raw_financials(ticker_with_suffix)
            if result is not None:
                return result
        except (ValidationError, ConnectionError, KeyError) as e:
            logger.debug("[Yahoo] Échec fallback %s: %s", ticker_with_suffix, e)

        raise TickerNotFoundError(ticker=original_ticker)

    # ==========================================================================
    # WORKFLOW AUTO-MODE
    # ==========================================================================

    def get_company_financials_and_parameters(
        self,
        ticker: str,
        projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """Workflow Auto-Mode:  récupère financials et paramètres."""
        financials = self.get_company_financials(ticker)
        macro = self._fetch_macro_context(financials)

        growth_estimated = _estimate_dynamic_growth(ticker)
        tax_rate = float(
            COUNTRY_CONTEXT.get(financials.country, DEFAULT_COUNTRY)["tax_rate"]
        )

        cost_of_debt = calculate_synthetic_cost_of_debt(
            rf=macro. risk_free_rate,
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