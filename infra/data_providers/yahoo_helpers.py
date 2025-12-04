import logging
from typing import Optional, List, Tuple, Any
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


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
        date: datetime
) -> Optional[Tuple[float, datetime]]:
    """
    Calcule le FCF TTM (Trailing Twelve Months) en sommant les 4 derniers
    rapports trimestriels publiés avant ou à la date donnée.
    """
    # --- Corps de la fonction _get_ttm_fcf_historical() extrait de yahoo_provider.py ---
    if cashflow_quarterly is None or cashflow_quarterly.empty:
        return None, None

    # Alias pour les lignes de FCF (Flux de trésorerie d'exploitation - Dépenses en capital)
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