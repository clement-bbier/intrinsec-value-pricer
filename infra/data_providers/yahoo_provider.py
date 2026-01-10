"""
infra/data_providers/yahoo_provider.py

FOURNISSEUR DE DONNÉES — YAHOO FINANCE (ULTIMATE V5.0)
Version : V5.0 — Waterfall Deep Fetch & None-Safe Integration

Changelog :
- Action B3 : Implémentation du Waterfall (TTM Quarterly Sum -> Annual -> Info).
- Action B4 : Suppression des fallbacks "0.0" pour préserver l'intégrité de l'audit (None-Propagation).
- Action B5 : Agrégation intelligente D&A (Somme des composantes si séparées).
- Maintenance : Respect total de l'architecture SOLID et du cache Streamlit.
"""

import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, List

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
    calculate_historical_cagr,
    CAPEX_KEYS,
    DA_KEYS
)
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.ref_data.country_matrix import COUNTRY_CONTEXT, DEFAULT_COUNTRY

logger = logging.getLogger(__name__)

class YahooFinanceProvider(DataProvider):
    """
    Fournisseur de données haute performance avec intelligence de cascade.
    Garantit la récupération des métriques les plus récentes pour l'audit.
    """

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider

    # ==========================================================================
    # 1. POINT D'ENTRÉE PRINCIPAL (CACHE)
    # ==========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        """Récupère et normalise les états financiers via la cascade TTM/Annual."""
        ticker = ticker.upper().strip()
        logger.info(f"[Yahoo] Waterfall Fetch initiation for {ticker}...")

        try:
            yt = yf.Ticker(ticker)
            info = safe_api_call(lambda: yt.info, "Info")

            if not info or ("currentPrice" not in info and "regularMarketPrice" not in info):
                return _self._handle_missing_ticker(ticker)

            currency, current_price = normalize_currency_and_price(info)

            # --- RÉCUPÉRATION MULTI-SOURCES POUR CASCADE ---
            # États Annuels (Standard)
            bs = safe_api_call(lambda: yt.balance_sheet, "Annual BS")
            is_ = safe_api_call(lambda: yt.income_stmt, "Annual IS")
            cf = safe_api_call(lambda: yt.cash_flow, "Annual CF")

            # États Trimestriels (Pour calcul TTM)
            q_is = safe_api_call(lambda: yt.quarterly_income_stmt, "Quarterly IS")
            q_cf = safe_api_call(lambda: yt.quarterly_cash_flow, "Quarterly CF")

            # --- RECONSTRUCTION MODULAIRE ---
            shares = _self._reconstruct_shares(info, bs, current_price)
            debt_data = _self._reconstruct_capital_structure(info, bs, is_)

            # Profitability utilise q_is et q_cf pour tenter le TTM
            profit_data = _self._reconstruct_profitability(info, is_, cf, q_is, q_cf)

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

    @st.cache_data(ttl=3600 * 4)
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """
        Récupère l'historique des prix pour les graphiques.
        Cette méthode est requise par le contrat DataProvider.
        """
        try:
            yt = yf.Ticker(ticker)
            hist = yt.history(period=period)
            if hist.empty:
                logger.warning(f"Aucun historique trouvé pour {ticker}")
            return hist
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique pour {ticker}: {e}")
            return pd.DataFrame()

    # ==========================================================================
    # 2. SEGMENTS LOGIQUES (WATERFALL LOGIC)
    # ==========================================================================

    def _reconstruct_shares(self, info: Dict, bs: pd.DataFrame, price: float) -> float:
        """Reconstruit le nombre d'actions avec fallback intelligent."""
        shares = info.get("sharesOutstanding")
        if not shares and bs is not None:
            shares = extract_most_recent_value(bs, ["Ordinary Shares Number", "Share Issued"])

        if not shares:
            mcap = info.get("marketCap", 0.0)
            if mcap > 0 and price > 0: shares = mcap / price

        return float(shares) if shares else 1.0

    def _reconstruct_capital_structure(self, info: Dict, bs: pd.DataFrame, is_: pd.DataFrame) -> Dict[str, Any]:
        """Analyse la structure de la dette (None-Safe)."""
        debt = info.get("totalDebt")
        if (not debt) and bs is not None:
            debt = extract_most_recent_value(bs, ["Total Debt", "Net Debt"])
            if not debt:
                std = extract_most_recent_value(bs, ["Current Debt", "Current Debt And Lease Obligation"]) or 0
                ltd = extract_most_recent_value(bs, ["Long Term Debt", "Long Term Debt And Lease Obligation"]) or 0
                debt = (std + ltd) if (std + ltd) > 0 else None

        cash = info.get("totalCash")
        if (not cash) and bs is not None:
            cash = extract_most_recent_value(bs, ["Cash And Cash Equivalents", "Cash Financial"])

        minority = extract_most_recent_value(bs, ["Minority Interest", "Non Controlling Interest"]) if bs is not None else 0.0
        pensions = extract_most_recent_value(bs, ["Long Term Provisions", "Pension And Other Postretirement Benefit Plans"]) if bs is not None else 0.0

        interest = extract_most_recent_value(is_, ["Interest Expense", "Interest Expense Non Operating"]) if is_ is not None else None

        return {
            "total_debt": float(debt) if debt is not None else 0.0,
            "cash_and_equivalents": float(cash) if cash is not None else 0.0,
            "minority_interests": float(minority or 0.0),
            "pension_provisions": float(pensions or 0.0),
            "interest_expense": float(abs(interest)) if interest is not None else 0.0
        }

    def _reconstruct_profitability(self, info: Dict, is_a: pd.DataFrame, cf_a: pd.DataFrame,
                                   is_q: pd.DataFrame, cf_q: pd.DataFrame) -> Dict[str, Any]:
        """
        Action B3 & B5 : Extraction TTM via somme trimestrielle avec agrégation D&A.
        """
        # 1. Tentative TTM (Somme des 4 derniers trimestres)
        rev_ttm = _sum_last_4_quarters(is_q, ["Total Revenue", "Revenue"])
        ebit_ttm = _sum_last_4_quarters(is_q, ["EBIT", "Operating Income"])
        ni_ttm = _sum_last_4_quarters(is_q, ["Net Income Common Stockholders", "Net Income"])

        # 2. Fallbacks sur l'annuel ou l'info si TTM échoue
        rev_ttm = rev_ttm or info.get("totalRevenue") or extract_most_recent_value(is_a, ["Total Revenue"])
        ebit_ttm = ebit_ttm or info.get("operatingCashflow") or extract_most_recent_value(is_a, ["EBIT", "Operating Income"])
        ni_ttm = ni_ttm or info.get("netIncomeToCommon") or extract_most_recent_value(is_a, ["Net Income"])

        # 3. Capex & D&A (Action B4 : None si non trouvé pour l'audit)
        fcf = get_simple_annual_fcf(cf_a)
        capex = extract_most_recent_value(cf_a, CAPEX_KEYS)

        # Action B5 : Agrégation D&A
        da = extract_most_recent_value(cf_a, DA_KEYS)
        if da is None and cf_a is not None:
            # Si pas de ligne agrégée, on tente de sommer manuellement
            dep = extract_most_recent_value(cf_a, ["Depreciation"]) or 0
            amo = extract_most_recent_value(cf_a, ["Amortization"]) or 0
            da = (dep + amo) if (dep + amo) > 0 else None

        div_rate = info.get("dividendRate") or (info.get("dividendYield", 0) * info.get("currentPrice", 0))

        return {
            "revenue_ttm": float(rev_ttm) if rev_ttm is not None else None,
            "ebitda_ttm": float(info.get("ebitda") or 0.0),
            "ebit_ttm": float(ebit_ttm) if ebit_ttm is not None else None,
            "net_income_ttm": float(ni_ttm) if ni_ttm is not None else None,
            "eps_ttm": float(info.get("trailingEps") or 0.0),
            "dividend_share": float(div_rate or 0.0),
            "book_value_per_share": float(info.get("bookValue") or 0.0),
            "beta": float(info.get("beta") or 1.0),
            "fcf_last": float(fcf) if fcf is not None else None,
            "fcf_fundamental_smoothed": float(fcf) if fcf is not None else None,
            "capex": float(capex) if capex is not None else None,
            "depreciation_and_amortization": float(da) if da is not None else None
        }

    # ==========================================================================
    # 3. HELPERS DE CALCULS DYNAMIQUES
    # ==========================================================================

    def get_company_financials_and_parameters(self, ticker: str, projection_years: int) -> Tuple[CompanyFinancials, DCFParameters]:
        """Workflow Auto-Mode."""
        f = self.get_company_financials(ticker)
        m = self._fetch_macro_context(f)

        g_estimated = self._estimate_dynamic_growth(ticker)
        tax = float(COUNTRY_CONTEXT.get(f.country, DEFAULT_COUNTRY)["tax_rate"])

        kd = calculate_synthetic_cost_of_debt(
            rf=m.risk_free_rate, ebit=f.ebit_ttm or 1.0,
            interest_expense=f.interest_expense, market_cap=f.market_cap
        )

        p = DCFParameters(
            risk_free_rate=m.risk_free_rate,
            market_risk_premium=m.market_risk_premium,
            corporate_aaa_yield=m.corporate_aaa_yield,
            cost_of_debt=kd, tax_rate=tax,
            fcf_growth_rate=g_estimated,
            perpetual_growth_rate=m.perpetual_growth_rate,
            projection_years=projection_years,
            target_equity_weight=f.market_cap,
            target_debt_weight=f.total_debt
        )
        p.normalize_weights()
        return f, p

    def _fetch_macro_context(self, f: CompanyFinancials):
        """Sécurité fallback macro."""
        try:
            return self.macro_provider.get_macro_context(date=datetime.now(), currency=f.currency)
        except:
            from infra.macro.yahoo_macro_provider import MacroContext
            c = COUNTRY_CONTEXT.get(f.country, DEFAULT_COUNTRY)
            return MacroContext(
                date=datetime.now(), currency=f.currency,
                risk_free_rate=float(c["risk_free_rate"]),
                market_risk_premium=float(c["market_risk_premium"]),
                perpetual_growth_rate=float(c["inflation_rate"]),
                corporate_aaa_yield=float(c["risk_free_rate"] + 0.01)
            )

    def _estimate_dynamic_growth(self, ticker: str) -> float:
        """CAGR historique filtré."""
        try:
            yt = yf.Ticker(ticker)
            hist_cf = safe_api_call(lambda: yt.cash_flow, "Hist Growth")
            g = calculate_historical_cagr(hist_cf, "Free Cash Flow")
            return max(0.01, min(g or 0.03, 0.10))
        except: return 0.03

    def _handle_missing_ticker(self, ticker: str):
        suffixes = [".PA", ".US", ".L", ".DE"]
        if not any(ticker.endswith(s) for s in suffixes):
            return self.get_company_financials(f"{ticker}.PA")
        raise TickerNotFoundError(ticker=ticker)

# ==============================================================================
# 4. FONCTION UTILITAIRE TTM (Somme glissante)
# ==============================================================================

def _sum_last_4_quarters(df: pd.DataFrame, keys: List[str]) -> Optional[float]:
    """Calcule la somme des 4 derniers trimestres pour simuler le TTM."""
    if df is None or df.empty:
        return None
    for key in keys:
        if key in df.index:
            last_4 = df.loc[key].iloc[:4]
            if len(last_4) == 4 and not last_4.isnull().any():
                return float(last_4.sum())
    return None