import logging
import time
from functools import wraps
from typing import Optional, List, Tuple, Any, Callable
from datetime import datetime

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# --- RETRY DECORATOR (Anti-Fragilité) ---

def safe_api_call(max_retries: int = 3, delay: int = 1):
    """Décorateur pour gérer les rate-limits Yahoo."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait_time = delay * (i + 1)
                    logger.warning(f"API attempt {i + 1} failed: {e}. Retry in {wait_time}s...")
                    time.sleep(wait_time)
            logger.error(f"API failed after {max_retries} retries.")
            raise last_exception

        return wrapper

    return decorator


# --- HELPERS D'EXTRACTION ---

def normalize_currency_and_price(price: float, currency: str) -> Tuple[float, str]:
    """Normalise les centimes (GBp) en livres (GBP)."""
    if currency == "GBp":
        return price / 100.0, "GBP"
    return price, currency


def _safe_get_first(df: pd.DataFrame, aliases: List[str]) -> Optional[float]:
    """Cherche la première colonne existante parmi les alias."""
    if df is None or df.empty:
        return None
    for alias in aliases:
        if alias in df.index:
            try:
                val = df.loc[alias].iloc[0]
                return float(val) if not pd.isna(val) else None
            except:
                continue
    return None


# Listes d'alias pour parser les bilans Yahoo (souvent instables)
REVENUE_ALIASES = ["Total Revenue", "Operating Revenue", "Revenue"]
INTEREST_EXPENSE_ALIASES = ["Interest Expense", "Interest Expense Net", "Finance Costs"]
EQUITY_ALIASES = ["Total Stockholder Equity", "Total Equity", "Stockholders Equity"]


def calculate_historical_cagr(income_stmt: pd.DataFrame, years: int = 3) -> Optional[float]:
    """Calcule le taux de croissance moyen (CAGR) du CA."""
    if income_stmt is None or income_stmt.empty:
        return None
    try:
        rev = None
        # Trouver la ligne Revenue
        for alias in REVENUE_ALIASES:
            if alias in income_stmt.index:
                rev = income_stmt.loc[alias]
                break

        if rev is None or len(rev) < years + 1:
            return None

        # Yahoo met souvent le plus récent à gauche (col 0)
        start_val = rev.iloc[years]
        end_val = rev.iloc[0]

        if start_val <= 0 or end_val <= 0:
            return None

        return (end_val / start_val) ** (1 / years) - 1.0
    except Exception:
        return None


# --- CALCUL DU FCF ---

def get_simple_annual_fcf(cashflow_df: pd.DataFrame) -> Optional[float]:
    """Calcule le FCF = Operating Cash Flow - CapEx."""
    if cashflow_df is None or cashflow_df.empty:
        return None
    try:
        ocf = _safe_get_first(cashflow_df, ["Operating Cash Flow", "Total Cash From Operating Activities"])
        capex = _safe_get_first(cashflow_df, ["Capital Expenditure", "Net PPE Purchase And Sale"])

        if ocf is not None and capex is not None:
            # CapEx est souvent négatif dans Yahoo
            return ocf + capex if capex < 0 else ocf - capex
    except:
        pass
    return None