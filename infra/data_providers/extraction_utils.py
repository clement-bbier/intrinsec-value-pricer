"""
infra/data_providers/extraction_utils.py

EXTRACTION TOOLS & API RESILIENCY (DT-022 Resolution)
Role: Normalization and robust extraction of financial data from yfinance.
Architecture: Honest Data with strict None propagation.

DT-022: Implementation of timeout support on API calls to prevent thread blocking.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, List, Optional, Tuple

import pandas as pd

from src.config import PeerDefaults
from src.config.constants import DataExtractionDefaults

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. ACCOUNTING ALIAS REFERENCE (ST-2.1)
# ==============================================================================

OCF_KEYS: List[str] = [
    "Operating Cash Flow",
    "Total Cash From Operating Activities",
    "Cash Flow From Continuing Operating Activities"
]

CAPEX_KEYS: List[str] = [
    "Capital Expenditure",
    "Net PPE Purchase And Sale",
    "Purchase Of PPE",
    "Purchase Of Property Plant And Equipment",
    "Capital Expenditure Reporting",
    "Changes In Cash From Investing Activities"
]

DA_KEYS: List[str] = [
    "Depreciation And Amortization",
    "Depreciation",
    "Amortization",
    "Depreciation Amortization Depletion",
    "Amortization Of Intangibles",
    "Depreciation And Amortization In Operating Activities",
    "Depletion"
]

# Aliases for Net Borrowing (Debt variation)
DEBT_ISSUANCE_KEYS: List[str] = ["Issuance Of Debt", "Long Term Debt Issuance", "Net Issuance Payments Of Debt"]
DEBT_REPAYMENT_KEYS: List[str] = ["Repayment Of Debt", "Long Term Debt Payments", "Net Long Term Debt"]

# ==============================================================================
# 2. API RESILIENCY (RETRY PATTERN + TIMEOUT)
# ==============================================================================

def safe_api_call(
    func: Callable,
    context: str = "API",
    max_retries: int = DataExtractionDefaults.MAX_RETRY_ATTEMPTS,
    timeout_seconds: Optional[float] = None
) -> Any:
    """
    Executes an API function with exponential backoff and optional timeout.

    Architecture: Prevents hanging threads in Streamlit by enforcing strict
    execution windows.
    """
    _timeout = timeout_seconds or PeerDefaults.API_TIMEOUT_SECONDS



    for i in range(max_retries):
        try:
            # Execution with timeout via ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func)
                try:
                    return future.result(timeout=_timeout)
                except FuturesTimeoutError:
                    logger.warning(
                        f"[{context}] Timeout reached after {_timeout}s (attempt {i + 1}/{max_retries})."
                    )
                    continue
        except (RuntimeError, ValueError, AttributeError) as e:
            # Handle non-critical business errors with exponential backoff
            wait = DataExtractionDefaults.RETRY_DELAY_BASE * (2 ** i)
            logger.warning(
                f"[{context}] API Error | attempt={i + 1}/{max_retries}, error={e}, wait={wait}s"
            )
            time.sleep(wait)
        except Exception as e:
            # Catch-all for API robustness
            logger.error(f"[{context}] Unexpected error during API call: {e}")
            time.sleep(DataExtractionDefaults.RETRY_DELAY_BASE)

    logger.error(f"[{context}] All retries exhausted | max_retries={max_retries}")
    return None


def safe_api_call_simple(func: Callable, context: str = "API", max_retries: int = 3) -> Any:
    """Simplified retry wrapper without thread-based timeout enforcement."""
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            wait = DataExtractionDefaults.RETRY_DELAY_BASE * (2 ** i)
            logger.warning(f"[{context}] Retry failed | attempt={i + 1}/{max_retries}, error={e}, wait={wait}s")
            time.sleep(wait)

    logger.error(f"[{context}] All retries exhausted | max_retries={max_retries}")
    return None


# ==============================================================================
# 3. ROBUST EXTRACTION (DEEP FETCH)
# ==============================================================================

def extract_most_recent_value(df: pd.DataFrame, keys: List[str]) -> Optional[float]:
    """
    Retrieves the most recent non-null value for a given list of accounting keys.

    Note: Aligns columns chronologically to prioritize TTM or the latest
    fiscal year data.
    """
    if df is None or df.empty:
        return None

    # Temporal alignment: most recent periods first
    try:
        df = df.sort_index(axis=1, ascending=False)
    except (TypeError, ValueError):
        pass

    for key in keys:
        if key in df.index:
            row = df.loc[key]
            for val in row.values:
                if pd.notnull(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        continue

    return None


# ==============================================================================
# 4. BUSINESS LOGIC HELPERS (STRICT NONE-PROPAGATION)
# ==============================================================================

def get_simple_annual_fcf(cashflow_df: pd.DataFrame) -> Optional[float]:
    """
    Calculates Free Cash Flow (FCF) as Operating Cash Flow plus Capital Expenditure.

    Standard: Honest Data principle - returns None if either component is missing
    to prevent biased results.
    """
    if cashflow_df is None or cashflow_df.empty:
        return None

    ocf = extract_most_recent_value(cashflow_df, OCF_KEYS)
    capex = extract_most_recent_value(cashflow_df, CAPEX_KEYS)

    if ocf is None or capex is None:
        return None

    # Note: Capex is typically negative in yfinance datasets
    return ocf + capex


def calculate_historical_cagr(
    income_stmt: pd.DataFrame,
    years: int = DataExtractionDefaults.HISTORICAL_CAGR_YEARS
) -> Optional[float]:
    """
    Calculates the historical Compounded Annual Growth Rate (CAGR) of Revenue.

    Ensures numerical stability by checking for positive start/end values.
    """
    if income_stmt is None or income_stmt.empty:
        return None

    revenue_keys = ["Total Revenue", "Revenue", "Gross Revenue"]
    rev_vals = None

    for key in revenue_keys:
        if key in income_stmt.index:
            rev_vals = income_stmt.loc[key].values
            break

    if rev_vals is None or len(rev_vals) < years + 1:
        return None

    end_val, start_val = rev_vals[0], rev_vals[years]

    if pd.isnull(start_val) or pd.isnull(end_val) or start_val <= 0 or end_val <= 0:
        return None

    return (end_val / start_val) ** (1 / years) - 1.0


def normalize_currency_and_price(info: dict) -> Tuple[str, float]:
    """
    Normalizes currency labels (e.g., GBp to GBP) and adjusts prices accordingly.
    """
    currency = info.get("currency", "USD")
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0.0)

    if currency == "GBp":
        currency = "GBP"
        price /= DataExtractionDefaults.PRICE_FORMAT_MULTIPLIER # Adjusting for pence to pounds

    return currency, float(price)