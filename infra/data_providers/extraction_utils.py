"""
infra/data_providers/extraction_utils.py

OUTILS D'EXTRACTION & SÉCURITÉ API — VERSION V9.0 (DT-022 Resolution)
Rôle :  Normalisation et extraction robuste des données yfinance.
Architecture :  Honest Data avec propagation stricte des None.

DT-022 : Ajout du support timeout sur les appels API.
"""

from __future__ import annotations

import logging
import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, List, Optional, Tuple

import pandas as pd

from core.config import PeerDefaults
from core.config.constants import DataExtractionDefaults

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. RÉFÉRENTIEL DES ALIAS COMPTABLES
# ==============================================================================

OCF_KEYS:  List[str] = [
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

# Aliases pour le Net Borrowing (Variation de la dette)
DEBT_ISSUANCE_KEYS: List[str] = ["Issuance Of Debt", "Long Term Debt Issuance", "Net Issuance Payments Of Debt"]
DEBT_REPAYMENT_KEYS: List[str] = ["Repayment Of Debt", "Long Term Debt Payments", "Net Long Term Debt"]

# ==============================================================================
# 2. SÉCURITÉ API (RETRY PATTERN + TIMEOUT) — DT-022 Resolution
# ==============================================================================

def safe_api_call(
    func: Callable,
    context: str = "API",
    max_retries: int = DataExtractionDefaults.MAX_RETRY_ATTEMPTS,
    timeout_seconds: Optional[float] = None
) -> Any:
    """
    Exécute une fonction API avec backoff exponentiel et timeout optionnel.
    
    DT-022 Resolution : Ajout du support timeout pour éviter les blocages.
    
    Parameters
    ----------
    func : Callable
        La fonction à exécuter.
    context : str
        Contexte pour les logs (ex: "PeerInfo/AAPL").
    max_retries : int
        Nombre maximum de tentatives (défaut: 3).
    timeout_seconds : float, optional
        Timeout en secondes. Si None, utilise PeerDefaults.API_TIMEOUT_SECONDS.
    
    Returns
    -------
    Any
        Le résultat de la fonction ou None en cas d'échec.
    
    Notes
    -----
    Le timeout utilise ThreadPoolExecutor pour une compatibilité cross-platform.
    """
    _timeout = timeout_seconds or PeerDefaults.API_TIMEOUT_SECONDS
    
    for i in range(max_retries):
        try:
            # Exécution avec timeout via ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func)
                try:
                    return future.result(timeout=_timeout)
                except FuturesTimeoutError:
                    logger.warning(
                        f"[{context}] Timeout après {_timeout}s (tentative {i + 1}/{max_retries})."
                    )
                    continue
        except Exception as e:
            wait = DataExtractionDefaults.RETRY_DELAY_BASE * (2 ** i)
            logger.warning(
                f"[{context}] Retry attempt failed | attempt={i + 1}/{max_retries}, error={e}, wait={wait}s"
            )
            time.sleep(wait)

    logger.error(f"[{context}] All retries exhausted | max_retries={max_retries}")
    return None


def safe_api_call_simple(func: Callable, context: str = "API", max_retries: int = 3) -> Any:
    """
    Version simplifiée sans timeout (pour les appels rapides).
    
    Compatibilité ascendante avec l'ancienne signature.
    """
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            wait = DataExtractionDefaults.RETRY_DELAY_BASE * (2 ** i)
            logger.warning(f"[{context}] Retry attempt failed | attempt={i + 1}/{max_retries}, error={e}, wait={wait}s")
            time.sleep(wait)

    logger.error(f"[{context}] All retries exhausted | max_retries={max_retries}")
    return None


# ==============================================================================
# 3. EXTRACTION ROBUSTE (DEEP FETCH)
# ==============================================================================

def extract_most_recent_value(df: pd.DataFrame, keys: List[str]) -> Optional[float]:
    """
    Cherche la valeur la plus récente dans un DataFrame financier.

    RÈGLE D'OR (Honest Data) :
    - Accepte 0.0 comme valeur valide.
    - Ignore NaN/None pour chercher dans l'historique (T-1, T-2).
    - Retourne None si aucune donnée n'est trouvée.
    """
    if df is None or df.empty:
        return None

    # Alignement temporel : colonnes récentes en premier
    try:
        df = df.sort_index(axis=1, ascending=False)
    except Exception:
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
# 4. HELPERS MÉTIER (STRICT NONE-PROPAGATION)
# ==============================================================================

def get_simple_annual_fcf(cashflow_df: pd.DataFrame) -> Optional[float]:
    """
    Calcule le FCF = Operating Cash Flow + Capital Expenditure.

    Note : Capex est généralement négatif dans les états financiers.
    Si l'un des composants est None, retourne None (Honest Data).
    """
    if cashflow_df is None or cashflow_df.empty:
        return None

    ocf = extract_most_recent_value(cashflow_df, OCF_KEYS)
    capex = extract_most_recent_value(cashflow_df, CAPEX_KEYS)

    if ocf is None or capex is None:
        return None

    return ocf + capex


def calculate_historical_cagr(income_stmt: pd.DataFrame, metric: str = "Free Cash Flow", years: int = DataExtractionDefaults.HISTORICAL_CAGR_YEARS) -> Optional[float]:
    """
    Calcule le CAGR historique d'une métrique.
    """
    if income_stmt is None or income_stmt. empty:
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
    Normalise les devises et ajuste le prix.
    Gère le cas Londres :  Pence (GBp) vers Livre (GBP).
    """
    currency = info.get("currency", "USD")
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0.0)

    if currency == "GBp":
        currency = "GBP"
        price /= DataExtractionDefaults.PRICE_FORMAT_MULTIPLIER

    return currency, float(price)