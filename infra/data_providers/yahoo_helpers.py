import logging
from typing import Optional, List, Tuple, Any
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# ALIAS COMMUNS (FCF simple & FCF fondamental)
# -----------------------------------------------------------------------------

# Cash Flow from Operations et Capex pour les calculs TTM / FCFF simple
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

# Compte de Résultat – pour la Méthode 2 (FCFF fondamental)
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

# Bilan – Besoin en Fonds de Roulement (NWC)
AR_ALIASES = [
    "Accounts Receivable",
    "Net Receivables",
    "Receivables",
]
INVENTORY_ALIASES = [
    "Inventory",
    "Total Inventory",
]
AP_ALIASES = [
    "Accounts Payable",
    "Accountspayable",
]


def _safe_get_first(df: Optional[pd.DataFrame], row_names: List[str]) -> Optional[float]:
    """Cherche la première ligne correspondante dans une liste d'alias et retourne sa première valeur."""
    # --- Corps de la fonction _safe_get_first() extrait de yahoo_provider.py ---
    if df is None or df.empty:
        return None

    # Normalisation de l'index pour la recherche
    normalized_df = df.copy()
    normalized_df.index = normalized_df.index.astype(str).str.strip().str.lower()

    for name in row_names:
        clean_name = str(name).strip().lower()
        if clean_name in normalized_df.index:
            try:
                # Prend la première colonne (la donnée la plus récente)
                val = normalized_df.loc[clean_name].iloc[0]
                return float(val)
            except Exception:
                continue
    return None
    # --------------------------------------------------------------------------


def _get_historical_fundamental(
    df_annual: Optional[pd.DataFrame],
    df_quarterly: Optional[pd.DataFrame],
    date: datetime,
    row_names: List[str],
    is_ttm: bool = False,
) -> Tuple[Optional[float], Optional[datetime]]:
    """
    Récupère la donnée fondamentale (le plus souvent) de la dernière publication
    avant ou égale à la date demandée.

    Utilise en priorité les états annuels, puis les trimestriels en fallback.
    """
    # --- Corps de la fonction _get_historical_fundamental() extrait de yahoo_provider.py ---
    # 1. Recherche dans les rapports Annuels (pour Dette, Cash, Shares, etc.)
    if df_annual is not None and not df_annual.empty:
        try:
            # On cherche l'ensemble des rapports publiés avant ou à la date demandée
            valid_reports = df_annual.columns[df_annual.columns <= date]

            if len(valid_reports) > 0:
                # On prend le rapport le plus récent
                latest_report_date = valid_reports[-1]

                # Extraction de la valeur pour cette date
                report_df = df_annual[[latest_report_date]]
                value = _safe_get_first(report_df, row_names)

                if value is not None:
                    return value, latest_report_date
        except Exception:
            pass

    # 2. Recherche dans les rapports Trimestriels (fallback si pas trouvé en annuel)
    if df_quarterly is not None and not df_quarterly.empty:
        try:
            valid_reports = df_quarterly.columns[df_quarterly.columns <= date]

            if len(valid_reports) > 0:
                latest_report_date = valid_reports[-1]
                report_df = df_quarterly[[latest_report_date]]
                value = _safe_get_first(report_df, row_names)

                if value is not None:
                    return value, latest_report_date
        except Exception:
            pass

    return None, None
    # --------------------------------------------------------------------------


def _get_ttm_fcf_historical(
    cashflow_quarterly: pd.DataFrame,
    date: datetime,
) -> Optional[Tuple[float, datetime]]:
    """
    Calcule le FCF TTM (Trailing Twelve Months) en sommant les 4 derniers
    rapports trimestriels publiés avant ou à la date donnée.
    """
    # --- Corps de la fonction _get_ttm_fcf_historical() extrait de yahoo_provider.py ---
    if cashflow_quarterly is None or cashflow_quarterly.empty:
        return None, None

    try:
        # 1) Colonnes converties en Timestamp
        cols_ts = pd.to_datetime(cashflow_quarterly.columns)

        # 2) Version pour comparaison : toujours tz-naive
        if getattr(cols_ts, "tz", None) is not None:
            cols_cmp = cols_ts.tz_convert(None)
        else:
            cols_cmp = cols_ts

        date_ts = pd.Timestamp(date)
        if date_ts.tzinfo is not None:
            date_cmp = date_ts.tz_convert(None)
        else:
            date_cmp = date_ts

        # 3) Filtre des colonnes <= date (sur la version “comparaison”)
        mask = cols_cmp <= date_cmp
        valid_cols = list(cashflow_quarterly.columns[mask])

        if len(valid_cols) < 4:
            logger.warning(
                f"[Hist] Pas assez de données trimestrielles (< 4) avant {date.date()} pour le FCF TTM."
            )
            return None, None

        # 4) On prend les 4 dernières colonnes (labels originaux)
        valid_cols_sorted = sorted(valid_cols, reverse=True)
        ttm_cols = valid_cols_sorted[:4]

        ttm_fcf = 0.0
        cfo_found = True
        capex_found = True

        for col in ttm_cols:
            report_df = cashflow_quarterly[[col]]

            cfo = _safe_get_first(report_df, CFO_ALIASES)
            if cfo is None:
                cfo_found = False
                logger.warning(
                    f"[Hist] FCF TTM: CFO manquant pour le trimestre {col}."
                )
                break

            capex = _safe_get_first(report_df, CAPEX_ALIASES)
            if capex is None:
                capex_found = False
                logger.warning(
                    f"[Hist] FCF TTM: CAPEX manquant pour le trimestre {col}."
                )
                break

            # FCFF simple: CFO + CAPEX (Capex est généralement négatif)
            ttm_fcf += cfo + capex

        if not cfo_found or not capex_found:
            logger.warning(
                f"[Hist] FCF TTM: CFO ou CAPEX manquant dans les 4 derniers rapports avant {date.date()}."
            )
            return None, None

        # La date de publication TTM est la plus récente des 4
        ttm_report_date = pd.to_datetime(ttm_cols[0]).to_pydatetime()

        return float(ttm_fcf), ttm_report_date

    except Exception as e:
        logger.error(f"[Hist] Erreur lors du calcul du FCF TTM pour {date.date()}: {e}")
        return None, None
    # --------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# NOUVELLES FONCTIONS – FCFF FONDAMENTAL (Méthode 2)
# -----------------------------------------------------------------------------


def _calculate_fundamental_fcf_annual(
    income_stmt: pd.DataFrame,
    cashflow_stmt: pd.DataFrame,
    balance_sheet_t: pd.DataFrame,
    balance_sheet_t_minus_1: pd.DataFrame,
    tax_rate_default: float,
) -> Optional[float]:
    """
    Calcule FCFF_t = NOPAT + D&A - Capex - ΔNWC pour une année donnée (t).
    Retourne None si des données critiques (EBIT, Capex) sont manquantes.

    Les DataFrames sont supposés ne contenir qu'une seule colonne (l'année ciblée).
    """

    # 1. NOPAT (Net Operating Profit After Tax)
    ebit = _safe_get_first(income_stmt, EBIT_ALIASES)
    tax_exp = _safe_get_first(income_stmt, TAX_EXPENSE_ALIASES)
    pretax_inc = _safe_get_first(income_stmt, PRETAX_INCOME_ALIASES)

    if ebit is None:
        logger.warning("[FundamentalDCF] EBIT introuvable pour l'année considérée.")
        return None  # EBIT est critique pour le FCFF fondamental

    # Taux d'impôt effectif historique (TIE) si disponible
    tax_rate = tax_rate_default
    if tax_exp is not None and pretax_inc not in (None, 0):
        try:
            eff_rate = tax_exp / pretax_inc
            # clamp entre 0 % et 100 %
            tax_rate = max(0.0, min(1.0, eff_rate))
        except Exception:
            logger.warning(
                "[FundamentalDCF] Impossible de calculer le taux d'impôt effectif, "
                f"utilisation du taux par défaut {tax_rate_default:.2%}"
            )

    nopat = ebit * (1 - tax_rate)

    # 2. D&A (on accepte qu'il soit nul si la ligne n'existe pas)
    da = _safe_get_first(income_stmt, DA_ALIASES)
    if da is None:
        da = 0.0

    # 3. Capex – critique pour FCFF
    capex = _safe_get_first(cashflow_stmt, CAPEX_ALIASES)
    if capex is None:
        logger.warning(
            "[FundamentalDCF] Capex introuvable pour l'année considérée – FCFF fondamental non calculable."
        )
        return None

    # 4. ΔNWC – Variation du Besoin en Fonds de Roulement
    try:
        # NWC_t = AR_t + Inventory_t - AP_t
        ar_t = _safe_get_first(balance_sheet_t, AR_ALIASES) or 0.0
        inv_t = _safe_get_first(balance_sheet_t, INVENTORY_ALIASES) or 0.0
        ap_t = _safe_get_first(balance_sheet_t, AP_ALIASES) or 0.0
        nwc_t = ar_t + inv_t - ap_t

        # NWC_{t-1}
        ar_t_1 = _safe_get_first(balance_sheet_t_minus_1, AR_ALIASES) or 0.0
        inv_t_1 = _safe_get_first(balance_sheet_t_minus_1, INVENTORY_ALIASES) or 0.0
        ap_t_1 = _safe_get_first(balance_sheet_t_minus_1, AP_ALIASES) or 0.0
        nwc_t_1 = ar_t_1 + inv_t_1 - ap_t_1

        delta_nwc = nwc_t - nwc_t_1

    except Exception as e:
        logger.warning(
            f"[FundamentalDCF] Impossible de calculer ΔNWC pour l'année considérée ({e}). "
            "ΔNWC supposé = 0."
        )
        delta_nwc = 0.0

    # 5. FCFF = NOPAT + D&A - Capex - ΔNWC
    # Dans yfinance, Capex est généralement un flux négatif (cash-out),
    # d'où l'implémentation suivante : NOPAT + D&A + Capex (car Capex<0) - ΔNWC.
    fcff = nopat + da + capex - delta_nwc

    logger.debug(
        "[FundamentalDCF] FCFF_t calculé: %.2f (NOPAT: %.2f, D&A: %.2f, Capex: %.2f, ΔNWC: %.2f)",
        fcff,
        nopat,
        da,
        capex,
        delta_nwc,
    )

    return float(fcff)


def get_fundamental_fcf_historical(
    income_annual: pd.DataFrame,
    cashflow_annual: pd.DataFrame,
    balance_annual: pd.DataFrame,
    tax_rate_default: float,
    nb_years: int = 3,
) -> List[float]:
    """
    Retourne la liste des FCFF fondamentaux (NOPAT + D&A - Capex - ΔNWC)
    pour les nb_years dernières années disponibles.

    On suppose que les colonnes des DataFrames sont ordonnées de la plus récente
    à la plus ancienne (comme retourné par yfinance). On a besoin de nb_years+1
    bilans pour pouvoir calculer ΔNWC sur nb_years années.
    """

    if (
        income_annual is None
        or income_annual.empty
        or cashflow_annual is None
        or cashflow_annual.empty
        or balance_annual is None
        or balance_annual.empty
    ):
        logger.warning(
            "[FundamentalDCF] États financiers annuels incomplets – FCFF fondamental non calculable."
        )
        return []

    # Nombre minimal de colonnes disponibles sur les trois états
    min_cols = min(
        len(income_annual.columns),
        len(cashflow_annual.columns),
        len(balance_annual.columns),
    )

    required_cols = nb_years + 1  # pour nb_years FCFF, il faut nb_years+1 bilans

    if min_cols < required_cols:
        logger.warning(
            "[FundamentalDCF] Données historiques insuffisantes pour FCFF fondamental "
            f"(disponibles: {min_cols}, requis: {required_cols})."
        )
        return []

    fcf_list: List[float] = []

    # On itère sur les années k = 0 (plus récente), 1, 2, ...
    for k in range(nb_years):
        try:
            # income/cashflow/balance pour l'année t (k)
            income_t = income_annual.iloc[:, k : k + 1]
            cashflow_t = cashflow_annual.iloc[:, k : k + 1]
            balance_t = balance_annual.iloc[:, k : k + 1]

            # bilan pour l'année t-1 (k+1)
            balance_t_minus_1 = balance_annual.iloc[:, k + 1 : k + 2]

            fcff_t = _calculate_fundamental_fcf_annual(
                income_stmt=income_t,
                cashflow_stmt=cashflow_t,
                balance_sheet_t=balance_t,
                balance_sheet_t_minus_1=balance_t_minus_1,
                tax_rate_default=tax_rate_default,
            )

            if fcff_t is not None:
                fcf_list.append(fcff_t)
            else:
                logger.warning(
                    "[FundamentalDCF] FCFF fondamental non calculable pour l'année d'index %d (manque EBIT/Capex).",
                    k,
                )

        except IndexError:
            # Ne devrait pas arriver grâce au check min_cols, mais on sécurise
            logger.warning(
                "[FundamentalDCF] IndexError lors de la construction de l'historique FCFF fondamental "
                f"(k={k})."
            )
            break

    return fcf_list
