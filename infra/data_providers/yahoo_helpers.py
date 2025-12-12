import logging
import time
from functools import wraps
from typing import Optional, List, Tuple, Any, Callable
from datetime import datetime

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# --- RETRY DECORATOR (Rate-Limit Protection) ---

def safe_api_call(max_retries: int = 3, delay: int = 1):
    """
    Décorateur pour gérer les rate-limits Yahoo et les erreurs réseau transitoires.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    # Backoff exponentiel léger : 1s, 2s, 3s...
                    wait_time = delay * (i + 1)
                    logger.warning(f"API attempt {i + 1}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)

            logger.error(f"API failed after {max_retries} retries.")
            raise last_exception

        return wrapper

    return decorator


# --- NORMALISATION ---

def normalize_currency_and_price(price: float, currency: str) -> Tuple[float, str]:
    """
    Gère le cas spécifique GBp (Pence) vs GBP (Livres) sur le LSE.
    Yahoo retourne souvent le prix en pence (GBp) mais les états financiers en Livres (GBP).
    """
    if currency == "GBp":
        # Conversion Pence -> Livres
        return price / 100.0, "GBP"
    return price, currency


def _safe_get_first(df: Optional[pd.DataFrame], row_names: List[str]) -> Optional[float]:
    """
    Cherche la première ligne correspondante dans un DataFrame, insensible à la casse.
    Gère les NaN/None/Inf proprement.
    """
    if df is None or df.empty:
        return None

    # Normalisation de l'index pour recherche insensible à la casse
    # Création d'un map { "nom_minuscule": "Nom_Reel" }
    normalized_index = {str(idx).strip().lower(): idx for idx in df.index}

    for name in row_names:
        clean_name = str(name).strip().lower()
        if clean_name in normalized_index:
            real_index = normalized_index[clean_name]
            try:
                # On prend la colonne la plus récente (iloc[0]) si non spécifié
                val = df.loc[real_index].iloc[0]

                # Vérification de validité numérique
                if pd.isna(val) or val is None:
                    continue
                return float(val)
            except Exception:
                continue
    return None


# --- ALIAS COMPTABLES ---

CFO_ALIASES = ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
               "Total Cash From Operating Activities"]
CAPEX_ALIASES = ["Capital Expenditure", "Net PPE Purchase And Sale", "Purchase Of PPE", "Capital Expenditures"]
EBIT_ALIASES = ["Operating Income", "EBIT", "Earnings Before Interest And Taxes"]
PRETAX_INCOME_ALIASES = ["Pretax Income", "Income Before Tax", "Earnings Before Tax"]
TAX_EXPENSE_ALIASES = ["Income Tax Expense", "Provision For Income Taxes"]
DA_ALIASES = ["Depreciation & Amortization", "Depreciation And Amortization", "Depreciation"]
CHANGE_IN_WORKING_CAPITAL_ALIASES = ["Change In Working Capital", "Changes In Cash", "Other Non Cash Items"]
INTEREST_EXPENSE_ALIASES = ["Interest Expense", "Interest Expense Non Operating", "Total Interest Expenses",
                            "Financial Expenses"]
REVENUE_ALIASES = ["Total Revenue", "Revenue", "Sales"]
NET_INCOME_ALIASES = ["Net Income", "Net Income Common Stockholders"]
EQUITY_ALIASES = ["Total Stockholder Equity", "Total Equity", "Stockholders Equity"]


# --- CALCULATORS ROBUSTES ---

def _get_ttm_fcf_historical(cashflow_quarterly: pd.DataFrame, date: datetime) -> Optional[Tuple[float, datetime]]:
    """Calcule le FCF TTM à une date donnée."""
    if cashflow_quarterly is None or cashflow_quarterly.empty:
        return None, None
    try:
        # Conversion timezone-naive pour comparaison fiable
        cols_ts = pd.to_datetime(cashflow_quarterly.columns)
        if cols_ts.tz is not None:
            cols_ts = cols_ts.tz_localize(None)

        date_cmp = date.replace(tzinfo=None)

        # Mapping: nom_colonne -> datetime_objet
        col_map = {}
        for original_col in cashflow_quarterly.columns:
            dt = pd.to_datetime(original_col)
            if dt.tz is not None: dt = dt.tz_localize(None)
            col_map[original_col] = dt

        valid_cols = [c for c, dt in col_map.items() if dt <= date_cmp]
        valid_cols.sort(key=lambda x: col_map[x], reverse=True)

        if len(valid_cols) < 4: return None, None

        ttm_fcf = 0.0
        for col in valid_cols[:4]:
            report_df = cashflow_quarterly[[col]]
            cfo = _safe_get_first(report_df, CFO_ALIASES)
            capex = _safe_get_first(report_df, CAPEX_ALIASES)
            if cfo is None or capex is None: return None, None
            ttm_fcf += (cfo + capex)

        last_date = col_map[valid_cols[0]].to_pydatetime()
        return float(ttm_fcf), last_date
    except Exception:
        return None, None


def get_simple_annual_fcf(cashflow_annual: pd.DataFrame) -> Optional[float]:
    """Récupère le FCF de la dernière année fiscale."""
    if cashflow_annual is None or cashflow_annual.empty: return None
    report_df = cashflow_annual.iloc[:, 0:1]
    cfo = _safe_get_first(report_df, CFO_ALIASES)
    capex = _safe_get_first(report_df, CAPEX_ALIASES)
    if cfo is None or capex is None: return None
    return float(cfo + capex)


def get_fundamental_fcf_historical_weighted(
        income_annual: pd.DataFrame,
        cashflow_annual: pd.DataFrame,
        tax_rate_default: float,
        nb_years: int = 5,
) -> Optional[float]:
    """Calcule une moyenne pondérée du FCFF normatif."""
    if income_annual is None or income_annual.empty: return None
    if cashflow_annual is None or cashflow_annual.empty: return None

    cols_inc = len(income_annual.columns)
    cols_cf = len(cashflow_annual.columns)
    limit = min(cols_inc, cols_cf, nb_years)

    if limit == 0: return None

    weighted_sum = 0.0
    total_weight = 0.0
    max_weight = float(limit)

    for k in range(limit):
        try:
            current_weight = max_weight - k
            inc_t = income_annual.iloc[:, k: k + 1]
            cf_t = cashflow_annual.iloc[:, k: k + 1]

            # Calcul atomique FCFF_t
            ebit = _safe_get_first(inc_t, EBIT_ALIASES)
            if ebit is None: continue

            tax_exp = _safe_get_first(inc_t, TAX_EXPENSE_ALIASES)
            pretax = _safe_get_first(inc_t, PRETAX_INCOME_ALIASES)

            tax_rate = tax_rate_default
            if tax_exp is not None and pretax and abs(pretax) > 0:
                calc_rate = tax_exp / pretax
                tax_rate = max(0.0, min(0.40, calc_rate))  # Bornage 0-40%

            nopat = ebit * (1 - tax_rate)
            da = _safe_get_first(cf_t, DA_ALIASES) or _safe_get_first(inc_t, DA_ALIASES) or 0.0
            capex = _safe_get_first(cf_t, CAPEX_ALIASES)
            wc = _safe_get_first(cf_t, CHANGE_IN_WORKING_CAPITAL_ALIASES) or 0.0

            if capex is None: continue

            fcff_t = nopat + da + capex + wc
            weighted_sum += fcff_t * current_weight
            total_weight += current_weight
        except Exception:
            continue

    if total_weight == 0: return None
    return float(weighted_sum / total_weight)


def calculate_historical_cagr(income_annual: pd.DataFrame, years: int = 3) -> Optional[float]:
    """Calcule le CAGR revenus."""
    if income_annual is None or income_annual.empty: return None
    try:
        if len(income_annual.columns) < years + 1: return None
        latest = _safe_get_first(income_annual.iloc[:, 0:1], REVENUE_ALIASES)
        oldest = _safe_get_first(income_annual.iloc[:, years:years + 1], REVENUE_ALIASES)
        if latest and oldest and oldest > 0 and latest > 0:
            return (latest / oldest) ** (1 / years) - 1
        return None
    except Exception:
        return None


def calculate_sustainable_growth(income_annual: pd.DataFrame, bs_annual: pd.DataFrame) -> Optional[float]:
    """Estime g = ROE * Retention."""
    try:
        ni = _safe_get_first(income_annual.iloc[:, 0:1], NET_INCOME_ALIASES)
        eq = _safe_get_first(bs_annual.iloc[:, 0:1], EQUITY_ALIASES)
        if ni and eq and eq > 0:
            roe = max(-0.5, min(0.5, ni / eq))
            return roe * 0.60  # Retention par défaut
        return None
    except Exception:
        return None


def _get_historical_fundamental(
        df_annual: Optional[pd.DataFrame],
        df_quarterly: Optional[pd.DataFrame],
        date: datetime,
        row_names: List[str],
) -> Tuple[Optional[float], Optional[datetime]]:
    """Récupère une donnée fondamentale historique (Annuel ou Trimestriel)."""
    # Logique de repli : Trimestriel > Annuel
    for df in [df_quarterly, df_annual]:
        if df is not None and not df.empty:
            try:
                # Création mapping dates
                col_map = {}
                for col in df.columns:
                    dt = pd.to_datetime(col)
                    if dt.tz is not None: dt = dt.tz_localize(None)
                    col_map[col] = dt

                date_cmp = date.replace(tzinfo=None)
                valid_cols = [c for c, dt in col_map.items() if dt <= date_cmp]
                valid_cols.sort(key=lambda x: col_map[x], reverse=True)

                if valid_cols:
                    val = _safe_get_first(df[[valid_cols[0]]], row_names)
                    if val is not None:
                        return val, col_map[valid_cols[0]].to_pydatetime()
            except Exception:
                continue
    return None, None