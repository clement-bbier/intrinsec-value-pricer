"""
infra/data_providers/extraction_utils.py

ATOMIC EXTRACTION TOOLS & API RESILIENCY
========================================
Role: Pure technical utilities for robust data extraction from DataFrames.
Responsibility: Handle API timeouts, retries, and technical parsing.
Standards: Honest Data (Strict None propagation). No business logic allowed.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, List, Optional, Tuple

import pandas as pd

from src.config.constants import DataExtractionDefaults

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. TECHNICAL ACCOUNTING KEYS (Translation Maps)
# ==============================================================================

OCF_KEYS = ["Operating Cash Flow", "Total Cash From Operating Activities"]
CAPEX_KEYS = ["Capital Expenditure", "Purchase Of PPE"]
DA_KEYS = ["Depreciation And Amortization", "Depreciation", "Amortization"]
DEBT_KEYS = ["Total Debt", "Net Debt", "Long Term Debt", "Current Debt"]

# ==============================================================================
# 2. API RESILIENCY (Infrastructure Layer)
# ==============================================================================

def safe_api_call(
    func: Callable,
    context: str = "API",
    max_retries: int = DataExtractionDefaults.MAX_RETRY_ATTEMPTS
) -> Any:
    """
    Executes an API function with exponential backoff and timeout protection.

    Parameters
    ----------
    func : Callable
        The API call to execute.
    context : str, default="API"
        Label for logging (e.g., Ticker name).
    max_retries : int
        Maximum number of attempts.

    Returns
    -------
    Any
        The API result or None if all attempts fail.
    """
    # DT-022: Enforce strict execution window to prevent Streamlit hanging
    timeout = 10.0
    for i in range(max_retries):
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func)
                return future.result(timeout=timeout)
        except FuturesTimeoutError:
            logger.warning(f"[{context}] Timeout reached (attempt {i+1})")
            continue
        except Exception as e:
            wait = DataExtractionDefaults.RETRY_DELAY_BASE * (2 ** i)
            logger.warning(f"[{context}] Error: {e}. Retry in {wait}s...")
            time.sleep(wait)

    logger.error(f"[{context}] All API retries exhausted.")
    return None

# ==============================================================================
# 3. ATOMIC PARSING (Technical Utilities)
# ==============================================================================

def extract_most_recent_value(df: pd.DataFrame, keys: List[str]) -> Optional[float]:
    """
    Technically extracts the latest non-null value for a set of keys.

    Parameters
    ----------
    df : pd.DataFrame
        The financial statement (Balance Sheet, etc.).
    keys : List[str]
        List of potential aliases for the required field.

    Returns
    -------
    Optional[float]
        The extracted numeric value or None.
    """
    if df is None or df.empty:
        return None

    # Fix: Specific exception handling for chronological sorting
    try:
        # Prioritize TTM or the latest fiscal year data by sorting columns
        df = df.sort_index(axis=1, ascending=False)
    except (AttributeError, TypeError, ValueError) as e:
        logger.debug(f"Index sorting skipped: {e}")

    for key in keys:
        if key in df.index:
            row = df.loc[key]
            # Handle cases where row might be a Series or a single scalar
            values = row.values if hasattr(row, 'values') else [row]
            for val in values:
                if pd.notnull(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        continue
    return None

def normalize_currency_and_price(info: dict) -> Tuple[str, float]:
    """
    Handles technical currency normalization (e.g., GBp to GBP).
    """
    currency = info.get("currency", "USD")
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0.0)

    if currency == "GBp": # British Pence to Pounds
        currency = "GBP"
        price /= 100.0

    return currency, float(price)