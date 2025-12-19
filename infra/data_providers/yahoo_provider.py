import logging
from datetime import datetime
from typing import Tuple

import pandas as pd
import yfinance as yf

# Assurez-vous que core/computation/financial_math.py existe bien
from core.computation.financial_math import calculate_synthetic_cost_of_debt
from core.exceptions import TickerNotFoundError
from core.models import CompanyFinancials, DCFParameters
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_helpers import (
    INTEREST_EXPENSE_ALIASES,
    _safe_get_first,
    get_simple_annual_fcf,
    normalize_currency_and_price,
    safe_api_call
)
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)


class YahooFinanceProvider(DataProvider):
    """
    Implémentation concrète via yfinance.
    Classe renommée pour alignement avec main.py
    """

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider

    @safe_api_call(max_retries=3)
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        ticker_obj = yf.Ticker(ticker)

        try:
            info = ticker_obj.info
            if not info or "regularMarketPrice" not in info:
                raise TickerNotFoundError(f"Ticker introuvable : {ticker}")
        except Exception as e:
            logger.error(f"Erreur fetch info {ticker}: {e}")
            raise TickerNotFoundError(f"Erreur accès Yahoo pour {ticker}")

        try:
            bs = ticker_obj.balance_sheet
            is_stmt = ticker_obj.financials
            cf = ticker_obj.cashflow
        except:
            bs, is_stmt, cf = None, None, None

        currency = info.get("currency", "USD")
        price = info.get("regularMarketPrice", 0.0)
        price, currency = normalize_currency_and_price(price, currency)

        # Récupération sécurisée du Beta
        raw_beta = info.get("beta")
        beta = float(raw_beta) if raw_beta is not None else 1.0

        # Données Dette/Cash
        total_debt = info.get("totalDebt")
        if total_debt is None and bs is not None:
            total_debt = _safe_get_first(bs, ["Total Debt", "Long Term Debt"]) or 0

        cash = info.get("totalCash")
        if cash is None and bs is not None:
            cash = _safe_get_first(bs, ["Cash And Cash Equivalents", "Cash"]) or 0

        int_exp = None
        if is_stmt is not None:
            int_exp = _safe_get_first(is_stmt, INTEREST_EXPENSE_ALIASES)

        fcf = get_simple_annual_fcf(cf)

        # Données Spécifiques Graham/RIM
        bv_share = info.get("bookValue")
        eps = info.get("trailingEps") or info.get("forwardEps")
        div = info.get("dividendRate") or info.get("trailingAnnualDividendRate")

        return CompanyFinancials(
            ticker=ticker,
            currency=currency,
            sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"),
            country=info.get("country", "Unknown"),
            current_price=price,
            shares_outstanding=info.get("sharesOutstanding", 0),
            total_debt=float(total_debt) if total_debt else 0.0,
            cash_and_equivalents=float(cash) if cash else 0.0,
            interest_expense=float(int_exp) if int_exp else 0.0,
            beta=beta,
            # Optionnels
            book_value_per_share=float(bv_share) if bv_share else None,
            eps_ttm=float(eps) if eps else None,
            last_dividend=float(div) if div else None,
            revenue_ttm=info.get("totalRevenue"),
            fcf_last=fcf,
            fcf_fundamental_smoothed=fcf,
            source_fcf="yahoo"
        )

    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        return yf.Ticker(ticker).history(period=period)

    def get_company_financials_and_parameters(
            self, ticker: str, projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:

        financials = self.get_company_financials(ticker)

        macro_ctx = self.macro_provider.get_macro_context(
            date=datetime.now(),
            currency=financials.currency
        )

        kd_synthetic = calculate_synthetic_cost_of_debt(
            rf=macro_ctx.risk_free_rate,
            ebit=financials.fcf_last or 1.0,
            interest_expense=financials.interest_expense,
            market_cap=financials.current_price * financials.shares_outstanding
        )

        params = DCFParameters(
            risk_free_rate=macro_ctx.risk_free_rate,
            market_risk_premium=macro_ctx.market_risk_premium,
            corporate_aaa_yield=macro_ctx.corporate_aaa_yield,
            cost_of_debt=kd_synthetic,
            tax_rate=0.25,
            fcf_growth_rate=0.05,  # Simplification V1
            projection_years=projection_years,
            perpetual_growth_rate=macro_ctx.perpetual_growth_rate
        )

        return financials, params