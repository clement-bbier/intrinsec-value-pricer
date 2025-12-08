import logging
from typing import Optional, List, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# ALIAS COMMUNS
# -----------------------------------------------------------------------------

CFO_ALIASES = [
    "Operating Cash Flow",
    "Cash Flow From Continuing Operating Activities",
    "Cash Flow From Operating Activities",
    "Total Cash From Operating Activities",
]
CAPEX_ALIASES = [
    "Capital Expenditure",
    "Net PPE Purchase And Sale",
    "Purchase Of PPE",
    "Capital Expenditures",
]
EBIT_ALIASES = [
    "Operating Income",
    "EBIT",
    "Ebit",
    "Earnings Before Interest And Taxes",
]
PRETAX_INCOME_ALIASES = [
    "Pretax Income",
    "Income Before Tax",
    "Earnings Before Tax",
]
TAX_EXPENSE_ALIASES = [
    "Income Tax Expense",
    "Provision For Income Taxes",
]
DA_ALIASES = [
    "Depreciation & Amortization",
    "Depreciation And Amortization",
    "Depreciation",
]
CHANGE_IN_WORKING_CAPITAL_ALIASES = [
    "Change In Working Capital",
    "Changes In Cash",
    "Other Non Cash Items",
]
INTEREST_EXPENSE_ALIASES = [
    "Interest Expense",
    "Interest Expense Non Operating",
    "Total Interest Expenses",
    "Financial Expenses",
    "Interest And Debt Expense",
    "Interest Expense, Net"
]
REVENUE_ALIASES = [
    "Total Revenue",
    "Revenue",
    "Sales"
]
NET_INCOME_ALIASES = [
    "Net Income",
    "Net Income Common Stockholders",
    "Net Income Applicable To Common Shares"
]
EQUITY_ALIASES = [
    "Total Stockholder Equity",
    "Total Equity",
    "Stockholders Equity"
]


def _safe_get_first(df: Optional[pd.DataFrame], row_names: List[str]) -> Optional[float]:
    """
    Cherche la première ligne correspondante.
    BLINDAGE : Retourne None si la valeur trouvée est NaN ou vide.
    """
    if df is None or df.empty:
        return None

    normalized_df = df.copy()
    normalized_df.index = normalized_df.index.astype(str).str.strip().str.lower()

    for name in row_names:
        clean_name = str(name).strip().lower()
        if clean_name in normalized_df.index:
            try:
                val = normalized_df.loc[clean_name].iloc[0]
                if pd.isna(val) or val is None:
                    continue
                return float(val)
            except Exception:
                continue
    return None


# -----------------------------------------------------------------------------
# WATERFALL 1 : FCF CALCULATORS
# -----------------------------------------------------------------------------

def _get_ttm_fcf_historical(
        cashflow_quarterly: pd.DataFrame,
        date: datetime,
) -> Optional[Tuple[float, datetime]]:
    """Calcule le FCF TTM (Trailing Twelve Months)."""
    if cashflow_quarterly is None or cashflow_quarterly.empty:
        return None, None
    try:
        cols_ts = pd.to_datetime(cashflow_quarterly.columns)
        if getattr(cols_ts, "tz", None) is not None:
            cols_cmp = cols_ts.tz_convert(None)
        else:
            cols_cmp = cols_ts

        date_ts = pd.Timestamp(date)
        date_cmp = date_ts.tz_convert(None) if date_ts.tzinfo else date_ts

        mask = cols_cmp <= date_cmp
        valid_cols = list(cashflow_quarterly.columns[mask])

        if len(valid_cols) < 4: return None, None

        valid_cols_sorted = sorted(valid_cols, reverse=True)
        ttm_cols = valid_cols_sorted[:4]

        ttm_fcf = 0.0
        for col in ttm_cols:
            report_df = cashflow_quarterly[[col]]
            cfo = _safe_get_first(report_df, CFO_ALIASES)
            capex = _safe_get_first(report_df, CAPEX_ALIASES)

            if cfo is None or capex is None: return None, None
            ttm_fcf += cfo + capex

        ttm_report_date = pd.to_datetime(ttm_cols[0]).to_pydatetime()
        return float(ttm_fcf), ttm_report_date
    except Exception:
        return None, None


def _calculate_fundamental_fcf_annual(
        income_stmt: pd.DataFrame,
        cashflow_stmt: pd.DataFrame,
        tax_rate_default: float,
) -> Optional[float]:
    """Calcule FCFF_t = NOPAT + D&A - Capex + ChangeInWC."""
    ebit = _safe_get_first(income_stmt, EBIT_ALIASES)
    if ebit is None: return None

    tax_exp = _safe_get_first(income_stmt, TAX_EXPENSE_ALIASES)
    pretax_inc = _safe_get_first(income_stmt, PRETAX_INCOME_ALIASES)

    tax_rate = tax_rate_default
    if tax_exp is not None and pretax_inc and pretax_inc != 0:
        eff_rate = tax_exp / pretax_inc
        tax_rate = max(0.0, min(0.40, eff_rate))

    nopat = ebit * (1 - tax_rate)

    da = _safe_get_first(cashflow_stmt, DA_ALIASES)
    if da is None:
        da = _safe_get_first(income_stmt, DA_ALIASES) or 0.0

    capex = _safe_get_first(cashflow_stmt, CAPEX_ALIASES)
    if capex is None: return None

    change_wc = _safe_get_first(cashflow_stmt, CHANGE_IN_WORKING_CAPITAL_ALIASES)
    if change_wc is None: change_wc = 0.0

    fcff = nopat + da + capex + change_wc
    return float(fcff)


def get_fundamental_fcf_historical_weighted(
        income_annual: pd.DataFrame,
        cashflow_annual: pd.DataFrame,
        tax_rate_default: float,
        nb_years: int = 5,
) -> Optional[float]:
    """Moyenne pondérée normative."""
    if income_annual is None or income_annual.empty: return None
    if cashflow_annual is None or cashflow_annual.empty: return None

    cols_inc = len(income_annual.columns)
    cols_cf = len(cashflow_annual.columns)
    available_years = min(cols_inc, cols_cf)

    if available_years == 0: return None

    limit = min(available_years, nb_years)
    weighted_sum = 0.0
    total_weight = 0.0
    max_weight = nb_years

    for k in range(limit):
        try:
            current_weight = max_weight - k
            if current_weight <= 0: continue

            inc_t = income_annual.iloc[:, k: k + 1]
            cf_t = cashflow_annual.iloc[:, k: k + 1]

            val = _calculate_fundamental_fcf_annual(inc_t, cf_t, tax_rate_default)

            if val is not None and not np.isnan(val):
                weighted_sum += val * current_weight
                total_weight += current_weight
        except Exception:
            continue

    if total_weight == 0: return None
    return float(weighted_sum / total_weight)


def get_simple_annual_fcf(cashflow_annual: pd.DataFrame) -> Optional[float]:
    """Fallback : Dernier FCF annuel simple."""
    if cashflow_annual is None or cashflow_annual.empty:
        return None

    report_df = cashflow_annual.iloc[:, 0:1]
    cfo = _safe_get_first(report_df, CFO_ALIASES)
    capex = _safe_get_first(report_df, CAPEX_ALIASES)

    if cfo is None or capex is None: return None
    return cfo + capex


# -----------------------------------------------------------------------------
# WATERFALL 2 : GROWTH CALCULATORS (Nouveau)
# -----------------------------------------------------------------------------

def calculate_historical_cagr(
        income_annual: pd.DataFrame,
        years: int = 3
) -> Optional[float]:
    """Calcule le CAGR des revenus sur X années."""
    if income_annual is None or income_annual.empty: return None

    try:
        if len(income_annual.columns) < years + 1:
            return None  # Pas assez d'historique

        # Colonne 0 = Plus récente, Colonne N = Plus vieille
        latest_rev = _safe_get_first(income_annual.iloc[:, 0:1], REVENUE_ALIASES)
        oldest_rev = _safe_get_first(income_annual.iloc[:, years:years + 1], REVENUE_ALIASES)

        if latest_rev is None or oldest_rev is None or oldest_rev <= 0 or latest_rev <= 0:
            return None

        # Formule CAGR : (End/Start)^(1/n) - 1
        cagr = (latest_rev / oldest_rev) ** (1 / years) - 1
        return float(cagr)
    except Exception:
        return None


def calculate_sustainable_growth(
        income_annual: pd.DataFrame,
        balance_sheet_annual: pd.DataFrame
) -> Optional[float]:
    """Calcule le taux soutenable : ROE * (1 - PayoutRatio)."""
    if income_annual is None or balance_sheet_annual is None: return None

    try:
        # Données de la dernière année
        net_income = _safe_get_first(income_annual.iloc[:, 0:1], NET_INCOME_ALIASES)
        equity = _safe_get_first(balance_sheet_annual.iloc[:, 0:1], EQUITY_ALIASES)

        # Payout (dividendes) souvent dans Cashflow, mais on peut estimer Retention via (Income - Div)
        # Simplification robuste : Utiliser le ROE moyen * Retention Rate standard (souvent 0.5 si inconnu)
        # Ici on fait simple : ROE * 0.5 (Hypothèse conservatrice si pas de donnée dividendes)

        if net_income and equity and equity > 0:
            roe = net_income / equity
            # On borne le ROE pour éviter les aberrations
            roe = max(-0.5, min(0.5, roe))

            # Hypothèse : Retention Rate par défaut de 60% (Entreprise de croissance) ou calcul plus fin si on avait les dividendes
            retention_rate = 0.60
            return roe * retention_rate

    except Exception:
        pass
    return None


# -----------------------------------------------------------------------------
# HELPERS HISTORIQUES
# -----------------------------------------------------------------------------
def _get_historical_fundamental(
        df_annual: Optional[pd.DataFrame],
        df_quarterly: Optional[pd.DataFrame],
        date: datetime,
        row_names: List[str],
) -> Tuple[Optional[float], Optional[datetime]]:
    """Récupère une donnée fondamentale à une date précise."""
    # 1. Essai Trimestriel
    if df_quarterly is not None and not df_quarterly.empty:
        try:
            cols_ts = pd.to_datetime(df_quarterly.columns)
            if getattr(cols_ts, "tz", None) is not None: cols_ts = cols_ts.tz_convert(None)
            date_ts = pd.Timestamp(date).tz_convert(None) if pd.Timestamp(date).tzinfo else pd.Timestamp(date)
            mask = cols_ts <= date_ts
            valid_cols = df_quarterly.columns[mask]
            if len(valid_cols) > 0:
                valid_cols_sorted = sorted(valid_cols, key=lambda x: pd.to_datetime(x), reverse=True)
                latest_col = valid_cols_sorted[0]
                report_df = df_quarterly[[latest_col]]
                val = _safe_get_first(report_df, row_names)
                if val is not None:
                    return val, pd.to_datetime(latest_col).to_pydatetime()
        except Exception:
            pass

    # 2. Essai Annuel
    if df_annual is not None and not df_annual.empty:
        try:
            cols_ts = pd.to_datetime(df_annual.columns)
            if getattr(cols_ts, "tz", None) is not None: cols_ts = cols_ts.tz_convert(None)
            date_ts = pd.Timestamp(date).tz_convert(None) if pd.Timestamp(date).tzinfo else pd.Timestamp(date)
            mask = cols_ts <= date_ts
            valid_cols = df_annual.columns[mask]
            if len(valid_cols) > 0:
                valid_cols_sorted = sorted(valid_cols, key=lambda x: pd.to_datetime(x), reverse=True)
                latest_col = valid_cols_sorted[0]
                report_df = df_annual[[latest_col]]
                val = _safe_get_first(report_df, row_names)
                if val is not None:
                    return val, pd.to_datetime(latest_col).to_pydatetime()
        except Exception:
            pass

    return None, None