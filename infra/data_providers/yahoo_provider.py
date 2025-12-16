import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf
import streamlit as st

# Import des maths financières centralisées
from core.computation.financial_math import calculate_synthetic_cost_of_debt

from core.exceptions import DataProviderError, TickerNotFoundError, ExternalServiceError, DataInsufficientError
from core.models import CompanyFinancials, DCFParameters
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_helpers import (
    INTEREST_EXPENSE_ALIASES,
    REVENUE_ALIASES,
    _get_historical_fundamental,
    _get_ttm_fcf_historical,
    _safe_get_first,
    calculate_historical_cagr,
    get_fundamental_fcf_historical_weighted,
    get_simple_annual_fcf,
    normalize_currency_and_price,
    safe_api_call
)
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.ref_data.country_matrix import get_country_context

logger = logging.getLogger(__name__)

DEFAULT_SECTOR_VALS = {"beta": 1.0, "cost_of_debt": 0.06}
SECTOR_RISK_PROFILE = {
    "Technology": {"beta_vol": 0.15, "g_vol": 0.020},
    "Healthcare": {"beta_vol": 0.08, "g_vol": 0.010},
    "Energy": {"beta_vol": 0.12, "g_vol": 0.030},
}
DEFAULT_RISK_PROFILE = {"beta_vol": 0.10, "g_vol": 0.010}


# --- LOGIQUE DE FETCHING AVEC CACHE STREAMLIT ---

@st.cache_data(ttl=300, show_spinner=False)
@safe_api_call(max_retries=2, delay=1)
def fetch_yahoo_data_cached(ticker: str) -> Dict[str, Any]:
    """
    Récupère les données brutes Yahoo (Cache Local).
    Retourne UNIQUEMENT des types serialisables.
    """
    try:
        yt = yf.Ticker(ticker)
        # Force fetch info pour vérifier l'existence
        info = yt.info

        # Validation minimale : si pas de symbole ni de prix, le ticker n'existe probablement pas
        if not info or (info.get('symbol') is None and info.get('regularMarketPrice') is None and info.get(
                'currentPrice') is None):
            # On tente une requête historique pour être sûr (cas des indices ou ETF parfois)
            hist = yt.history(period="1d")
            if hist.empty:
                raise TickerNotFoundError(f"Ticker '{ticker}' introuvable.")

        return {
            "info": info,
            "balance_sheet": yt.balance_sheet,
            "cashflow": yt.cashflow,
            "income_statement": yt.financials,
            "quarterly_cashflow": yt.quarterly_cashflow,
            "quarterly_balance_sheet": yt.quarterly_balance_sheet
        }
    except TickerNotFoundError:
        raise
    except Exception as e:
        raise ExternalServiceError(f"Erreur connexion YahooFinance pour {ticker}: {e}")


class YahooFinanceProvider(DataProvider):
    """Implémentation Production-Grade du provider Yahoo."""

    def __init__(self, macro_provider: Optional[YahooMacroProvider] = None) -> None:
        self.macro_provider = macro_provider or YahooMacroProvider()

    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        # Utilisation de la fonction locale
        data = fetch_yahoo_data_cached(ticker)
        info = data.get("info", {})
        bs = data.get("balance_sheet")
        inc = data.get("income_statement")

        # 1. Prix & Currency
        raw_price = info.get("currentPrice") or info.get("regularMarketPrice")
        raw_currency = info.get("currency", "USD")

        if raw_price is None:
            # Fallback history
            hist = self.get_price_history(ticker, period="1d")
            if not hist.empty:
                raw_price = float(hist["Close"].iloc[-1])
            else:
                raise DataInsufficientError(f"Prix indisponible pour {ticker}")

        price, currency = normalize_currency_and_price(float(raw_price), raw_currency)

        # 2. Shares
        shares = info.get("sharesOutstanding")
        if shares is None:
            shares = _safe_get_first(bs, ["Share Issued", "Ordinary Shares Number"])
            if shares is None:
                raise DataInsufficientError(f"Nombre d'actions indisponible pour {ticker}")

        # 3. Dette & Cash
        debt_val = float(_safe_get_first(bs, ["Total Debt", "Long Term Debt"]) or 0.0)
        cash_val = float(_safe_get_first(bs, ["Cash And Cash Equivalents", "Cash"]) or 0.0)

        interest_expense = 0.0
        if inc is not None and not inc.empty:
            val = _safe_get_first(inc, INTEREST_EXPENSE_ALIASES)
            interest_expense = abs(float(val)) if val is not None else 0.0

        # 4. FCF & Revenue
        fcf_ttm, fcf_weighted, fcf_source = self._compute_fcf_variants(data)

        revenue_ttm = float(info.get("totalRevenue") or 0.0)
        if revenue_ttm == 0.0 and inc is not None and not inc.empty:
            revenue_ttm = float(_safe_get_first(inc.iloc[:, 0:1], REVENUE_ALIASES) or 0.0)

        # 5. Dividendes & Graham Metrics (Champs Optionnels)
        last_div = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
        eps_ttm = info.get("trailingEps")
        book_value = info.get("bookValue")

        # 6. Beta
        raw_beta = info.get("beta")
        beta = float(raw_beta) if raw_beta is not None else DEFAULT_SECTOR_VALS["beta"]

        return CompanyFinancials(
            ticker=ticker,
            currency=currency,
            sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"),
            country=info.get("country", "Unknown"),
            current_price=price,
            shares_outstanding=float(shares),
            total_debt=debt_val,
            cash_and_equivalents=cash_val,
            interest_expense=interest_expense,
            beta=beta,
            fcf_last=fcf_ttm,
            fcf_fundamental_smoothed=fcf_weighted,
            source_fcf=fcf_source,
            revenue_ttm=revenue_ttm,
            # Gestion robuste des optionnels : 0.0 par défaut pour éviter les plantages
            last_dividend=float(last_div) if last_div is not None else 0.0,
            eps_ttm=float(eps_ttm) if eps_ttm is not None else 0.0,
            book_value_per_share=float(book_value) if book_value is not None else 0.0
        )

    def get_company_financials_and_parameters(self, ticker: str, projection_years: int):
        financials = self.get_company_financials(ticker)
        data = fetch_yahoo_data_cached(ticker)

        # Contexte Pays (Risk Free, Tax, Inflation)
        ctx = get_country_context(financials.country)

        # Stratégies Automatiques
        final_cost_of_debt = self._resolve_cost_of_debt_strategy(ctx["risk_free_rate"], financials)
        base_growth = self._resolve_growth_strategy(data, financials)

        # Logique High Growth par défaut
        auto_high_growth_years = 0
        if base_growth > 0.15:
            auto_high_growth_years = 3
        elif base_growth > 0.08:
            auto_high_growth_years = 2

        # Profil de Risque (Monte Carlo)
        risk_profile = SECTOR_RISK_PROFILE.get(financials.sector, DEFAULT_RISK_PROFILE)

        params = DCFParameters(
            risk_free_rate=ctx["risk_free_rate"],
            market_risk_premium=ctx["market_risk_premium"],
            cost_of_debt=final_cost_of_debt,
            tax_rate=ctx["tax_rate"],
            fcf_growth_rate=base_growth,
            perpetual_growth_rate=ctx["inflation_rate"],
            projection_years=int(projection_years),
            high_growth_years=auto_high_growth_years,
            beta_volatility=risk_profile["beta_vol"],
            growth_volatility=risk_profile["g_vol"],
            terminal_growth_volatility=risk_profile["g_vol"] / 2.0
        )

        # Audit Préliminaire (Qualité des données)
        try:
            audit_res = AuditEngine.compute_audit(financials, params)
            financials.audit_score = int(audit_res.global_score)
            financials.audit_rating = audit_res.rating
        except Exception:
            # Fallback silencieux pour l'UX
            financials.audit_score = 50
            financials.audit_rating = "N/A"

        return financials, params

    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        try:
            hist = yf.Ticker(ticker).history(period=period)
            return hist[["Close"]] if hist is not None and not hist.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def get_historical_fundamentals_for_date(self, ticker: str, date: datetime) -> Tuple[
        Optional[Dict[str, Any]], List[str]]:
        try:
            data = fetch_yahoo_data_cached(ticker)
            bs_annual = data.get("balance_sheet")
            bs_quarterly = data.get("quarterly_balance_sheet")

            debt_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, ["Total Debt", "Long Term Debt"])
            cash_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date,
                                                      ["Cash And Cash Equivalents", "Cash"])
            shares_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date,
                                                        ["Share Issued", "Ordinary Shares Number"])

            if shares_val is None:
                shares_val = data.get("info", {}).get("sharesOutstanding")

            if shares_val is None or debt_val is None:
                return None, ["Données Bilan insuffisantes"]

            qcf = data.get("quarterly_cashflow")
            fcf_ttm, _ = _get_ttm_fcf_historical(qcf, date)

            return {
                "fcf_last": fcf_ttm,
                "total_debt": debt_val,
                "cash_and_equivalents": cash_val,
                "shares_outstanding": shares_val,
                "beta": data.get("info", {}).get("beta", 1.0)
            }, []
        except Exception as e:
            return None, [str(e)]

    def _compute_fcf_variants(self, data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], str]:
        qcf = data.get("quarterly_cashflow")
        inc = data.get("income_statement")
        cf = data.get("cashflow")

        fcf_ttm, _ = _get_ttm_fcf_historical(qcf, datetime.now())
        if fcf_ttm is not None: return fcf_ttm, fcf_ttm, "ttm"

        fcf_weighted = get_fundamental_fcf_historical_weighted(inc, cf, 0.25, 5)
        if fcf_weighted is not None: return fcf_weighted, fcf_weighted, "weighted"

        fcf_simple = get_simple_annual_fcf(cf)
        if fcf_simple is not None: return fcf_simple, fcf_simple, "simple"

        return None, None, "none"

    def _resolve_growth_strategy(self, data: Dict[str, Any], financials: CompanyFinancials) -> float:
        info = data.get("info", {})
        analyst = info.get("earningsGrowth") or info.get("revenueGrowth")
        if analyst and -0.5 < float(analyst) < 0.5:
            financials.source_growth = "analysts"
            return float(analyst)

        cagr = calculate_historical_cagr(data.get("income_statement"), years=3)
        if cagr:
            financials.source_growth = "cagr"
            return max(0.0, min(0.20, cagr * 0.8))

        financials.source_growth = "macro"
        return 0.025

    def _resolve_cost_of_debt_strategy(self, rf: float, f: CompanyFinancials) -> float:
        if f.total_debt > 0 and f.interest_expense > 0:
            proxy_ebit = f.fcf_last if f.fcf_last else f.interest_expense * 3
            synthetic = calculate_synthetic_cost_of_debt(
                rf=rf,
                ebit=proxy_ebit,
                interest_expense=f.interest_expense,
                market_cap=f.current_price * f.shares_outstanding
            )
            if rf < synthetic < 0.20:
                f.source_debt = "synthetic"
                return synthetic
        f.source_debt = "sector"
        return 0.06