import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf
import streamlit as st

from core.exceptions import (
    DataProviderError,
    TickerNotFoundError,
    DataInsufficientError,
    ExternalServiceError
)
from core.models import CompanyFinancials, DCFParameters
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_helpers import (
    INTEREST_EXPENSE_ALIASES,
    _get_historical_fundamental,
    _get_ttm_fcf_historical,
    _safe_get_first,
    calculate_historical_cagr,
    calculate_sustainable_growth,
    get_fundamental_fcf_historical_weighted,
    get_simple_annual_fcf,
    normalize_currency_and_price,
    safe_api_call
)
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.ref_data.country_matrix import get_country_context

logger = logging.getLogger(__name__)

DEFAULT_RISK_PROFILE = {"beta_vol": 0.10, "g_vol": 0.010}


# --- CACHED FETCHING LOGIC (STANDALONE) ---

@st.cache_data(ttl=300, show_spinner=False)
@safe_api_call(max_retries=2, delay=1)
def fetch_yahoo_data_cached(ticker: str) -> Dict[str, Any]:
    """
    Récupère les données brutes Yahoo.
    Retourne UNIQUEMENT des types serialisables (Dict, DataFrame).
    """
    try:
        yt = yf.Ticker(ticker)

        # Appel réseau pour info (déclenche la validation)
        info = yt.info

        # Vérification d'existence
        if not info or info.get('symbol') is None:
            if 'regularMarketPrice' not in info and 'currentPrice' not in info:
                raise TickerNotFoundError(f"Ticker '{ticker}' introuvable ou radié.")

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


# --- PROVIDER CLASS ---

class YahooFinanceProvider(DataProvider):
    """
    Implémentation Production-Grade du provider Yahoo.
    Gère: Caching, Retry, Erreurs Typées, Normalisation.
    """

    def __init__(self, macro_provider: Optional[YahooMacroProvider] = None) -> None:
        self.macro_provider = macro_provider or YahooMacroProvider()

    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        # 1. Récupération Données (Cachées - Pure Data)
        data = fetch_yahoo_data_cached(ticker)
        info = data["info"]

        # 2. Validation & Normalisation Prix/Actions
        raw_price = info.get("currentPrice") or info.get("regularMarketPrice")
        raw_currency = info.get("currency", "USD")

        if raw_price is None:
            # Fallback : On réinstancie un objet Ticker léger juste pour l'historique prix
            try:
                hist = yf.Ticker(ticker).history(period="1d")
                if not hist.empty:
                    raw_price = float(hist["Close"].iloc[-1])
                else:
                    raise DataInsufficientError(f"Prix de marché indisponible pour {ticker}")
            except Exception:
                raise DataInsufficientError(f"Prix de marché indisponible pour {ticker}")

        shares = info.get("sharesOutstanding")
        if shares is None:
            # Fallback Bilan
            shares = _safe_get_first(data["balance_sheet"], ["Share Issued", "Ordinary Shares Number"])
            if shares is None:
                raise DataInsufficientError(f"Nombre d'actions indisponible pour {ticker}")

        # Correction GBp -> GBP si nécessaire
        price, currency = normalize_currency_and_price(float(raw_price), raw_currency)

        # 3. Extraction Comptable
        bs = data["balance_sheet"]
        inc = data["income_statement"]

        total_debt = _safe_get_first(bs, ["Total Debt", "Long Term Debt"]) or 0.0
        cash = _safe_get_first(bs, ["Cash And Cash Equivalents", "Cash"]) or 0.0

        interest_expense = 0.0
        if inc is not None and not inc.empty:
            val = _safe_get_first(inc, INTEREST_EXPENSE_ALIASES)
            interest_expense = abs(float(val)) if val is not None else 0.0

        # 4. Calcul FCF & Beta
        fcf_ttm, fcf_weighted, fcf_source = self._compute_fcf_variants(data)

        beta = info.get("beta")
        if beta is None:
            beta = 1.0  # Valeur par défaut neutre

        return CompanyFinancials(
            ticker=ticker,
            currency=currency,
            sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"),
            country=info.get("country", "Unknown"),
            current_price=price,
            shares_outstanding=float(shares),
            total_debt=float(total_debt),
            cash_and_equivalents=float(cash),
            interest_expense=float(interest_expense),
            beta=float(beta),
            fcf_last=fcf_ttm,
            fcf_fundamental_smoothed=fcf_weighted,
            source_fcf=fcf_source,
        )

    def get_company_financials_and_parameters(self, ticker: str, projection_years: int):
        """
        Workflow unifié : Récupère les données + Calcule les paramètres Auto.
        """
        # Récupération Financials
        financials = self.get_company_financials(ticker)

        # Contexte Macro & Pays
        ctx = get_country_context(financials.country)

        # Récupération des données brutes (Hit Cache rapide)
        data = fetch_yahoo_data_cached(ticker)

        base_growth = self._resolve_growth_strategy(data, financials)
        cost_debt = self._resolve_cost_of_debt_strategy(ctx["risk_free_rate"], financials)

        # Logique High Growth (Plateau)
        high_growth_years = 0
        if base_growth > 0.15:
            base_growth = 0.15
            high_growth_years = 3
        elif base_growth > 0.08:
            high_growth_years = 2

        params = DCFParameters(
            risk_free_rate=ctx["risk_free_rate"],
            market_risk_premium=ctx["market_risk_premium"],
            cost_of_debt=cost_debt,
            tax_rate=ctx["tax_rate"],
            fcf_growth_rate=base_growth,
            perpetual_growth_rate=ctx["inflation_rate"],
            projection_years=int(projection_years),
            high_growth_years=high_growth_years,
            beta_volatility=DEFAULT_RISK_PROFILE["beta_vol"],
            growth_volatility=DEFAULT_RISK_PROFILE["g_vol"],
            terminal_growth_volatility=DEFAULT_RISK_PROFILE["g_vol"] / 2.0
        )

        # Audit Auto (Pré-audit pour avoir un score immédiat, le vrai audit est refait dans le workflow)
        audit = AuditEngine.compute_audit(financials, params)
        financials.audit_score = int(audit.global_score)
        financials.audit_rating = audit.rating

        # [CORRECTION] Suppression de l'assignation ui_details qui n'existe plus
        # Les détails de l'audit sont maintenant portés par l'objet AuditReport retourné par le workflow
        financials.audit_breakdown = audit.breakdown

        return financials, params

    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        try:
            yt = yf.Ticker(ticker)
            hist = yt.history(period=period)
            if hist is None or hist.empty: return pd.DataFrame()
            return hist[["Close"]]
        except Exception:
            return pd.DataFrame()

    def get_historical_fundamentals_for_date(self, ticker: str, date: datetime) -> Tuple[
        Optional[Dict[str, Any]], List[str]]:
        try:
            data = fetch_yahoo_data_cached(ticker)

            bs_annual = data.get("balance_sheet")
            bs_quarterly = data.get("quarterly_balance_sheet")

            # Extraction Historique
            debt, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, ["Total Debt", "Long Term Debt"])
            cash, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, ["Cash And Cash Equivalents", "Cash"])
            shares, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date,
                                                    ["Share Issued", "Ordinary Shares Number"])

            if shares is None: shares = data["info"].get("sharesOutstanding")
            if shares is None or debt is None:
                return None, ["Données Bilan insuffisantes pour cette date"]

            qcf = data.get("quarterly_cashflow")
            fcf, _ = _get_ttm_fcf_historical(qcf, date)

            return {
                "fcf_last": fcf,
                "total_debt": debt,
                "cash_and_equivalents": cash,
                "shares_outstanding": shares,
                "beta": data["info"].get("beta", 1.0)
            }, []
        except Exception as e:
            return None, [str(e)]

    # --- STRATEGIES INTERNES ---

    def _compute_fcf_variants(self, data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], str]:
        qcf = data.get("quarterly_cashflow")
        inc = data.get("income_statement")
        cf = data.get("cashflow")

        fcf_ttm, _ = _get_ttm_fcf_historical(qcf, datetime.now())
        if fcf_ttm: return fcf_ttm, fcf_ttm, "ttm"

        fcf_weighted = get_fundamental_fcf_historical_weighted(inc, cf, 0.25, 5)
        if fcf_weighted: return fcf_weighted, fcf_weighted, "weighted"

        fcf_simple = get_simple_annual_fcf(cf)
        if fcf_simple: return fcf_simple, fcf_simple, "simple"

        return None, None, "none"

    def _resolve_growth_strategy(self, data: Dict[str, Any], financials: CompanyFinancials) -> float:
        info = data["info"]
        analyst = info.get("earningsGrowth") or info.get("revenueGrowth")

        # 1. Analystes
        if analyst and -0.5 < float(analyst) < 0.5:
            financials.source_growth = "analysts"
            return float(analyst)

        # 2. Historique (CAGR)
        cagr = calculate_historical_cagr(data["income_statement"])
        if cagr:
            financials.source_growth = "cagr"
            return max(0.0, min(0.20, cagr * 0.8))

        # 3. Macro (PIB)
        financials.source_growth = "macro"
        return 0.025

    def _resolve_cost_of_debt_strategy(self, rf: float, f: CompanyFinancials) -> float:
        if f.total_debt > 0 and f.interest_expense > 0:
            approx_ebit_proxy = f.fcf_last if f.fcf_last else 0.0
            icr = approx_ebit_proxy / f.interest_expense

            if icr > 5:
                spread = 0.015
            elif icr > 2:
                spread = 0.03
            else:
                spread = 0.06

            f.source_debt = "synthetic"
            return rf + spread

        f.source_debt = "sector"
        return 0.06