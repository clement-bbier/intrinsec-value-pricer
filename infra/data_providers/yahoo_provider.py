import logging
from typing import Optional, Dict, Tuple, Any, List
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
import numpy as np

from core.models import CompanyFinancials, DCFParameters, FCFSource
from core.exceptions import DataProviderError
from infra.data_providers.base_provider import DataProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.ref_data.country_matrix import get_country_context

# --- IMPORTS HELPERS ---
from infra.data_providers.yahoo_helpers import (
    _safe_get_first,
    _get_ttm_fcf_historical,
    get_fundamental_fcf_historical_weighted,
    get_simple_annual_fcf,
    calculate_historical_cagr,
    calculate_sustainable_growth,
    _get_historical_fundamental,
    INTEREST_EXPENSE_ALIASES
)

from core.computation.discounting import calculate_synthetic_cost_of_debt
from infra.auditing.audit_engine import AuditEngine

logger = logging.getLogger(__name__)

# Profils par défaut (Fallback)
DEFAULT_SECTOR_VALS = {"beta": 1.0, "cost_of_debt": 0.06}
SECTOR_DEFAULTS = {
    "Technology": {"beta": 1.2, "cost_of_debt": 0.05},
    "Consumer Defensive": {"beta": 0.7, "cost_of_debt": 0.045},
}
DEFAULT_RISK_PROFILE = {"beta_vol": 0.10, "g_vol": 0.010}
SECTOR_RISK_PROFILE = {
    "Technology": {"beta_vol": 0.15, "g_vol": 0.020},
    "Healthcare": {"beta_vol": 0.08, "g_vol": 0.010},
}


class YahooFinanceProvider(DataProvider):
    """
    Fournisseur de données Yahoo Finance. Implémentation complète.
    """

    def __init__(self, macro_provider: Optional[YahooMacroProvider] = None):
        self.macro_provider = macro_provider if macro_provider is not None else YahooMacroProvider()
        self._ticker_cache: Dict[str, Any] = {}

    def _get_ticker_data(self, ticker: str) -> Dict[str, Any]:
        """Récupère et met en cache les objets Yahoo."""
        if ticker not in self._ticker_cache:
            try:
                yt = yf.Ticker(ticker)
                data = {
                    "ticker_obj": yt,
                    "balance_sheet": yt.balance_sheet,
                    "cashflow": yt.cashflow,
                    "income_statement": yt.financials,
                    "quarterly_cashflow": yt.quarterly_cashflow,
                    "info": yt.info,
                }
                self._ticker_cache[ticker] = data
            except Exception as e:
                logger.error("[Provider] Erreur Yahoo pour %s: %s", ticker, e)
                raise DataProviderError(f"Données inaccessibles pour {ticker}")
        return self._ticker_cache[ticker]

    # --- MÉTHODES ABSTRAITES OBLIGATOIRES (FIX CRASH) ---

    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """Récupère les données financières actuelles (Implémentation requise)."""
        data = self._get_ticker_data(ticker)
        info = data.get("info", {})
        bs = data["balance_sheet"]
        inc = data["income_statement"]

        # 1. Infos de Marché
        price = float(info.get("regularMarketPrice", 0.0))
        shares = float(info.get("sharesOutstanding") or 0.0)

        if not price or shares <= 0:
            # Fallback si info vide mais histo dispo
            hist = data["ticker_obj"].history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
            else:
                raise DataProviderError(f"Prix ou Actions introuvables pour {ticker}")

        # 2. Bilan & Compte de Résultat
        debt_val = float(_safe_get_first(bs, ["Total Debt", "Long Term Debt"]) or 0.0)
        cash_val = float(_safe_get_first(bs, ["Cash And Cash Equivalents", "Cash"]) or 0.0)

        interest_expense = 0.0
        if not inc.empty:
            val = _safe_get_first(inc, INTEREST_EXPENSE_ALIASES)
            interest_expense = abs(float(val)) if val is not None else 0.0

        # 3. Waterfalls (FCF, Beta)
        fcf_ttm, fcf_weighted, fcf_source = self._compute_fcf_variants(data)
        raw_beta = info.get("beta")
        beta = float(raw_beta) if raw_beta is not None else DEFAULT_SECTOR_VALS["beta"]

        # 4. Instanciation
        fin = CompanyFinancials(
            ticker=ticker, currency=info.get("currency", "USD"), sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"), country=info.get("country", "Unknown"),
            current_price=price, shares_outstanding=shares, total_debt=debt_val,
            cash_and_equivalents=cash_val, interest_expense=interest_expense,
            beta=beta, fcf_last=fcf_ttm, fcf_fundamental_smoothed=fcf_weighted,
            source_fcf=fcf_source
        )
        return fin

    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Récupère l'historique de prix."""
        try:
            return self._get_ticker_data(ticker)["ticker_obj"].history(period=period)[["Close"]]
        except:
            return pd.DataFrame()

    def get_historical_fundamentals_for_date(self, ticker: str, date: datetime) -> Tuple[
        Optional[Dict[str, Any]], List[str]]:
        """Récupère les fondamentaux à une date passée."""
        data = self._get_ticker_data(ticker)
        bs_annual = data.get("balance_sheet")
        bs_quarterly = data.get("quarterly_balance_sheet")

        # Utilisation des helpers pour remonter dans le temps
        DEBT_KEYS = ["Total Debt", "Long Term Debt"]
        CASH_KEYS = ["Cash And Cash Equivalents", "Cash"]
        SHARE_KEYS = ["Share Issued", "Ordinary Shares Number"]

        debt_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, DEBT_KEYS)
        cash_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, CASH_KEYS)
        shares_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, SHARE_KEYS)

        if shares_val is None: shares_val = data.get("info", {}).get("sharesOutstanding")
        if shares_val is None or debt_val is None: return None, ["Données Bilan introuvables."]

        qcf = data.get("quarterly_cashflow")
        fcf_ttm, _ = _get_ttm_fcf_historical(qcf, date)
        if fcf_ttm is None: return None, ["Flux trimestriels insuffisants."]

        beta_val = data.get("info", {}).get("beta", 1.0)

        return {
            "fcf_last": fcf_ttm, "total_debt": debt_val,
            "cash_and_equivalents": cash_val, "shares_outstanding": shares_val,
            "beta": beta_val
        }, []

    def get_company_financials_and_parameters(self, ticker: str, projection_years: int):
        """Méthode unifiée pour le workflow."""
        financials = self.get_company_financials(ticker)
        data = self._get_ticker_data(ticker)

        # 1. Paramètres Macro (via country_matrix)
        ctx = get_country_context(financials.country)

        # 2. Waterfalls
        final_cost_of_debt = self._resolve_cost_of_debt_strategy(ctx["risk_free_rate"], financials)
        base_growth = self._resolve_growth_strategy(data, financials)

        # 3. Croissance (High Growth Years)
        auto_high_growth_years = 0
        if base_growth > 0.15:
            base_growth = 0.15; auto_high_growth_years = 3
        elif base_growth > 0.08:
            auto_high_growth_years = 2

        risk_profile = SECTOR_RISK_PROFILE.get(financials.sector, DEFAULT_RISK_PROFILE)

        params = DCFParameters(
            risk_free_rate=ctx["risk_free_rate"], market_risk_premium=ctx["market_risk_premium"],
            cost_of_debt=final_cost_of_debt, tax_rate=ctx["tax_rate"],
            fcf_growth_rate=base_growth, perpetual_growth_rate=ctx["inflation_rate"],
            projection_years=int(projection_years), high_growth_years=auto_high_growth_years,
            beta_volatility=risk_profile["beta_vol"], growth_volatility=risk_profile["g_vol"]
        )

        # 4. Audit
        audit_res = AuditEngine.compute_audit(financials, params, simulation_results=None)
        financials.audit_score = audit_res.global_score
        financials.audit_rating = audit_res.rating
        financials.audit_details = audit_res.ui_details
        financials.audit_breakdown = audit_res.breakdown

        return financials, params

    # --- LOGIQUE INTERNE ---

    def _compute_fcf_variants(self, data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], str]:
        """Détermine le FCF TTM et Pondéré (Utilise yahoo_helpers)."""
        qcf = data["quarterly_cashflow"]
        inc = data["income_statement"]
        cf = data["cashflow"]

        fcf_ttm, ttm_date = _get_ttm_fcf_historical(qcf, datetime.now())
        if fcf_ttm is not None: return fcf_ttm, fcf_ttm, "ttm"

        fcf_weighted = get_fundamental_fcf_historical_weighted(inc, cf, tax_rate_default=0.25, nb_years=5)
        if fcf_weighted is not None: return fcf_weighted, fcf_weighted, "weighted"

        fcf_simple = get_simple_annual_fcf(cf)
        if fcf_simple is not None: return fcf_simple, fcf_simple, "simple"

        return None, None, "none"

    def _resolve_growth_strategy(self, data: Dict[str, Any], financials: CompanyFinancials) -> float:
        info = data.get("info", {});
        inc = data.get("income_statement");
        bs = data.get("balance_sheet")
        analyst_g = info.get("earningsGrowth") or info.get("revenueGrowth")
        if analyst_g is not None and -0.5 < float(analyst_g) < 0.5: financials.source_growth = "analysts"; return float(
            analyst_g)
        cagr_3y = calculate_historical_cagr(inc, years=3)
        if cagr_3y is not None: financials.source_growth = "cagr"; return max(0.0, min(0.20, cagr_3y * 0.8))
        sust_g = calculate_sustainable_growth(inc, bs)
        if sust_g is not None: financials.source_growth = "sustainable"; return max(0.01, min(0.15, sust_g))
        financials.source_growth = "macro";
        return 0.025

    def _resolve_cost_of_debt_strategy(self, risk_free_rate: float, financials: CompanyFinancials) -> float:
        sector_defaults = SECTOR_DEFAULTS.get(financials.sector, DEFAULT_SECTOR_VALS)
        if financials.total_debt > 0 and financials.interest_expense > 0:
            synthetic_kd = calculate_synthetic_cost_of_debt(risk_free_rate, financials.interest_expense * 3,
                                                            financials.interest_expense,
                                                            financials.current_price * financials.shares_outstanding)
            if risk_free_rate < synthetic_kd < 0.20: financials.source_debt = "synthetic"; return synthetic_kd
        financials.source_debt = "sector";
        return sector_defaults["cost_of_debt"]