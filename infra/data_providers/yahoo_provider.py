import logging
from typing import Optional, Any, Iterable

import numpy as np
import pandas as pd
import yfinance as yf

from core.models import CompanyFinancials, DCFParameters
from core.exceptions import DataProviderError
from infra.data_providers.base_provider import DataProvider

logger = logging.getLogger(__name__)


# =============================
# Helpers
# =============================

def _safe_get_first(df: pd.DataFrame, row_name: str) -> Optional[float]:
    """Robust extraction of a numeric row value from Yahoo DataFrame."""
    if df is None or df.empty:
        logger.debug("[Yahoo] DF empty → cannot find row '%s'", row_name)
        return None

    target = str(row_name).strip().lower()

    # Exact match
    if row_name in df.index:
        raw_label = row_name
        logger.debug("[Yahoo] Exact row match for '%s'", row_name)
    else:
        # Fuzzy match
        normalized = {str(idx).strip().lower(): idx for idx in df.index}
        raw_label = normalized.get(target)
        if raw_label:
            logger.debug("[Yahoo] Fuzzy row match '%s' → '%s'", row_name, raw_label)
        else:
            logger.debug("[Yahoo] No match for '%s'", row_name)
            return None

    row = df.loc[raw_label]

    # Handle Series or DataFrame
    if isinstance(row, pd.DataFrame):
        if row.empty:
            return None
        value = row.iat[0, 0]
    else:
        if row.empty:
            return None
        value = row.iloc[0]

    if isinstance(value, (float, int)) and not np.isnan(value):
        logger.debug("[Yahoo] Value for '%s' = %.2f", row_name, value)
        return float(value)

    return None


def _safe_get_first_any(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[float]:
    """Try multiple row names."""
    for name in candidates:
        v = _safe_get_first(df, name)
        if v is not None:
            logger.debug("[Yahoo] Using alias '%s' = %.2f", name, v)
            return v
    return None


def _build_fcf_series(cashflow: pd.DataFrame, info: dict[str, Any]) -> Optional[pd.Series]:
    """Construct FCF time series."""
    if cashflow is None or cashflow.empty:
        return None

    cfo_row = None
    for name in [
        "Operating Cash Flow",
        "Cash Flow From Continuing Operating Activities",
        "Cash Flow from Continuing Operating Activities",
    ]:
        if name in cashflow.index:
            cfo_row = cashflow.loc[name].astype(float)
            break

    capex_row = None
    for name in [
        "Capital Expenditure",
        "Net PPE Purchase And Sale",
        "Purchase Of PPE",
    ]:
        if name in cashflow.index:
            capex_row = cashflow.loc[name].astype(float)
            break

    if cfo_row is not None and capex_row is not None:
        fcf = (cfo_row + capex_row).dropna()
    else:
        for name in ["Free Cash Flow"]:
            if name in cashflow.index:
                fcf = cashflow.loc[name].astype(float).dropna()
                break
        else:
            return None

    if fcf.empty:
        return None

    try:
        return fcf.sort_index()
    except Exception:
        return fcf


def _compute_cagr_from_series(series: pd.Series, min_points: int = 3) -> Optional[float]:
    """Compute a simple CAGR."""
    if series is None or series.empty:
        return None

    s = series.dropna()
    if len(s) < min_points:
        return None

    first = float(s.iloc[-min_points])
    last = float(s.iloc[-1])

    if first <= 0 or last <= 0:
        return None

    years = min_points - 1
    if years <= 0:
        return None

    return (last / first) ** (1.0 / years) - 1.0


# =============================
# MAIN PROVIDER
# =============================

class YahooFinanceProvider(DataProvider):

    # -----------------------------------------
    # 1) Normalize company financials
    # -----------------------------------------

    def _load_statement(self, stmt):
        """Avoid ambiguous truth value errors."""
        try:
            df = stmt
            if df is None or df.empty:
                return pd.DataFrame()
            return df
        except Exception:
            return pd.DataFrame()

    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        logger.info("=== Fetching company financials for %s ===", ticker)

        try:
            yt = yf.Ticker(ticker)
        except Exception as exc:
            logger.error("[Yahoo] Could not init Ticker('%s'): %s", ticker, exc)
            raise DataProviderError("Failed to initialize Yahoo Ticker", context={"ticker": ticker})

        info = getattr(yt, "info", {}) or {}
        logger.debug("[Yahoo] info keys: %s", list(info.keys()))

        # Price & shares
        price = (info.get("regularMarketPrice")
                 or info.get("currentPrice")
                 or info.get("previousClose"))
        shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        beta = info.get("beta") or 1.0
        currency = info.get("currency") or info.get("financialCurrency") or "USD"

        if price is None or shares is None:
            raise DataProviderError(
                "Missing price or shares from Yahoo",
                context={"ticker": ticker, "price": price, "shares": shares},
            )

        logger.info("[Yahoo] Price=%.2f %s | Shares=%.0f | Beta=%.3f",
                    price, currency, shares, beta)

        # Load statements safely
        balance_sheet = self._load_statement(yt.balance_sheet)
        cashflow = self._load_statement(yt.cashflow)

        # Debt
        total_debt = _safe_get_first_any(balance_sheet, ["Total Debt", "Net Debt"])
        if total_debt is None:
            fallback = info.get("totalDebt")
            if isinstance(fallback, (int, float)):
                total_debt = float(fallback)
                logger.warning("[Yahoo] Debt from info['totalDebt'] = %.2f", total_debt)
        if total_debt is None:
            logger.warning("[Yahoo] Missing Total Debt → 0")
            total_debt = 0.0

        # Cash
        cash = _safe_get_first_any(
            balance_sheet,
            ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
        )
        if cash is None:
            fallback = info.get("totalCash")
            if isinstance(fallback, (int, float)):
                cash = float(fallback)
                logger.warning("[Yahoo] Cash from info['totalCash'] = %.2f", cash)
        if cash is None:
            logger.warning("[Yahoo] Missing Cash → 0")
            cash = 0.0

        # FCF = CFO + CAPEX
        cfo = _safe_get_first_any(
            cashflow,
            [
                "Operating Cash Flow",
                "Cash Flow From Continuing Operating Activities",
                "Cash Flow from Continuing Operating Activities",
            ],
        )
        if cfo is None:
            fallback = info.get("operatingCashflow")
            if isinstance(fallback, (int, float)):
                cfo = float(fallback)
                logger.warning("[Yahoo] CFO from info['operatingCashflow'] = %.2f", cfo)

        capex = _safe_get_first_any(
            cashflow, ["Capital Expenditure", "Net PPE Purchase And Sale", "Purchase Of PPE"]
        )

        fcf_last = None

        if cfo is not None and capex is not None:
            fcf_last = float(cfo) + float(capex)
            logger.info("[Yahoo] FCFF_last = CFO + Capex = %.2f + %.2f = %.2f", cfo, capex, fcf_last)
        else:
            direct = _safe_get_first_any(cashflow, ["Free Cash Flow"])
            if direct is not None:
                fcf_last = float(direct)
                logger.warning("[Yahoo] Using Free Cash Flow = %.2f", fcf_last)
            elif isinstance(info.get("freeCashflow"), (int, float)):
                fcf_last = float(info["freeCashflow"])
                logger.warning("[Yahoo] FCF from info['freeCashflow'] = %.2f", fcf_last)

        if fcf_last is None:
            raise DataProviderError(
                "Missing CFO/Capex/FCF → cannot compute FCFF_last",
                context={"ticker": ticker},
            )

        logger.info(
            "[Yahoo] FINAL Financials: Price=%.2f %s | Shares=%.0f | Debt=%.2f | Cash=%.2f | FCFF_last=%.2f | Beta=%.3f",
            price, currency, shares, total_debt, cash, fcf_last, beta
        )

        return CompanyFinancials(
            ticker=ticker.upper(),
            currency=currency,
            current_price=float(price),
            shares_outstanding=float(shares),
            total_debt=float(total_debt),
            cash_and_equivalents=float(cash),
            fcf_last=float(fcf_last),
            beta=float(beta),
        )

    # -----------------------------------------
    # 2) Price history
    # -----------------------------------------

    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        logger.info("[Yahoo] Fetching price history for %s (%s)", ticker, period)

        try:
            hist = yf.download(ticker, period=period, progress=False, auto_adjust=False)
        except Exception as exc:
            raise DataProviderError(
                "Failed to download price history",
                context={"ticker": ticker, "error": str(exc)},
            )

        if hist is None or hist.empty:
            raise DataProviderError("Empty price history", context={"ticker": ticker})

        if "Close" in hist.columns:
            hist = hist.rename(columns={"Close": "close"})

        if "close" not in hist.columns:
            raise DataProviderError(
                "No close column in price history", context={"columns": list(hist.columns)}
            )

        logger.info("[Yahoo] %d rows of price history loaded", len(hist))
        return hist[["close"]]

    # -----------------------------------------
    # 3) Market context
    # -----------------------------------------

    def get_market_context(self, financials: CompanyFinancials) -> dict[str, float]:
        ticker = financials.ticker
        currency = financials.currency

        logger.info("=== Building market context for %s ===", ticker)

        # Safely reload statements
        try:
            yt = yf.Ticker(ticker)

            cf = self._load_statement(yt.cashflow)
            fs = self._load_statement(yt.financials)
            info = getattr(yt, "info", {}) or {}

        except Exception as exc:
            logger.warning("[Yahoo] Could not reload extra context: %s", exc)
            cf, fs, info = pd.DataFrame(), pd.DataFrame(), {}

        # Risk-free by currency
        risk_free_rate = {"USD": 0.04, "EUR": 0.025, "GBP": 0.035}.get(currency, 0.04)
        market_risk_premium = 0.05

        # Tax
        tax_rate = _safe_get_first_any(fs, ["Tax Rate For Calcs"])
        if tax_rate is None:
            tax_rate = 0.25
            logger.warning("[Tax] fallback = 25%%")

        # Cost of debt
        interest_expense = _safe_get_first_any(fs, ["Interest Expense", "Interest Expense Non Operating"])
        if interest_expense is not None and financials.total_debt > 0:
            cost_of_debt = abs(float(interest_expense)) / financials.total_debt
        else:
            cost_of_debt = risk_free_rate + 0.02
            logger.warning("[Debt] fallback Rd = Rf + 2%% = %.4f", cost_of_debt)

        # FCF CAGR
        fcf_series = _build_fcf_series(cf, info)
        fcf_growth_rate = _compute_cagr_from_series(fcf_series, min_points=3)
        if fcf_growth_rate is None:
            fcf_growth_rate = 0.03
            logger.warning("[Growth] fallback g = 3%%")
        fcf_growth_rate = float(np.clip(fcf_growth_rate, -0.20, 0.20))

        # Long-term growth
        perpetual_growth_rate = {"USD": 0.02, "EUR": 0.015, "GBP": 0.02}.get(currency, 0.02)

        logger.info(
            "[MarketContext] Rf=%.4f | MRP=%.4f | Rd=%.4f | Tax=%.4f | g=%.4f | g∞=%.4f",
            risk_free_rate,
            market_risk_premium,
            cost_of_debt,
            tax_rate,
            fcf_growth_rate,
            perpetual_growth_rate
        )

        return {
            "risk_free_rate": risk_free_rate,
            "market_risk_premium": market_risk_premium,
            "tax_rate": tax_rate,
            "cost_of_debt": cost_of_debt,
            "fcf_growth_rate": fcf_growth_rate,
            "perpetual_growth_rate": perpetual_growth_rate,
        }

    # -----------------------------------------
    # 4) Build DCF parameters for app
    # -----------------------------------------

    def build_dcf_parameters(self, financials: CompanyFinancials, projection_years: int) -> DCFParameters:
        ctx = self.get_market_context(financials)

        params = DCFParameters(
            risk_free_rate=ctx["risk_free_rate"],
            market_risk_premium=ctx["market_risk_premium"],
            cost_of_debt=ctx["cost_of_debt"],
            tax_rate=ctx["tax_rate"],
            fcf_growth_rate=ctx["fcf_growth_rate"],
            perpetual_growth_rate=ctx["perpetual_growth_rate"],
            projection_years=int(projection_years),
        )

        logger.info("[DCFParams] %s", params.to_log_dict())
        return params

    # -----------------------------------------
    # 5) Unified entry point for the app
    # -----------------------------------------

    def get_company_financials_and_parameters(self, ticker: str, projection_years: int):
        logger.info("=== Fetching financials + DCF params for %s ===", ticker)

        financials = self.get_company_financials(ticker)
        logger.info("[Provider] Financials: %s", financials.to_log_dict())

        params = self.build_dcf_parameters(financials, projection_years)
        logger.info("[Provider] Final params: %s", params.to_log_dict())

        return financials, params
