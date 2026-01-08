"""
infra/data_providers/yahoo_helpers.py

OUTILS D'EXTRACTION & SÉCURITÉ API
Version : V3.6 — Deep Fetch (None-Safe & Honest Zero)

Changelog :
- Amélioration : 'extract_most_recent_value' accepte désormais le 0.0 comme donnée valide.
- Nettoyage : Standardisation des tests 'is not None' pour éviter les faux négatifs.
- Sécurité : Maintien du Retry Policy avec backoff exponentiel.
"""

import logging
import time
from functools import wraps
from typing import Optional, Tuple, Callable, List, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. SÉCURITÉ API (RETRY PATTERN)
# ==============================================================================

def safe_api_call(func: Callable, context: str = "API", max_retries: int = 3):
    """
    Exécute une fonction lambda avec des tentatives multiples.
    Indispensable pour stabiliser les instabilités réseau de yfinance.
    """
    last_error = None
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            wait = 0.5 * (2 ** i)  # Backoff exponentiel (0.5s, 1s, 2s)
            logger.warning(f"[{context}] Tentative {i + 1}/{max_retries} échouée : {e}. Pause {wait}s.")
            time.sleep(wait)

    logger.error(f"[{context}] Échec définitif après {max_retries} tentatives.")
    return None


# ==============================================================================
# 2. OUTILS D'EXTRACTION FINANCIÈRE (DEEP FETCH)
# ==============================================================================

def extract_most_recent_value(df: pd.DataFrame, keys: List[str]) -> Optional[float]:
    """
    Cherche la valeur la plus récente dans un DataFrame financier.

    RÈGLE D'OR (Standard Hedge Fund) :
    - On accepte le 0.0 s'il est explicitement reporté (ex: Dette = 0).
    - On ignore le NaN (Donnée manquante) et on cherche dans l'historique (T-1, T-2).
    """
    if df is None or df.empty:
        return None

    # 1. Alignement temporel : On veut la colonne la plus récente en premier
    try:
        df = df.sort_index(axis=1, ascending=False)
    except:
        pass

    # 2. Scan des alias de comptes comptables
    for key in keys:
        if key in df.index:
            row = df.loc[key]

            # 3. Parcours de la série temporelle
            for val in row.values:
                # Modifié : On ne rejette plus le 0.0. Seul le NaN/None est ignoré.
                if pd.notnull(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        continue

    return None


def _safe_get_first(df: pd.DataFrame, aliases: List[str]) -> Optional[float]:
    """Alias pour rétro-compatibilité avec d'anciens modules."""
    return extract_most_recent_value(df, aliases)


# ==============================================================================
# 3. HELPERS MÉTIER (FLUX & CROISSANCE)
# ==============================================================================

def get_simple_annual_fcf(cashflow_df: pd.DataFrame) -> Optional[float]:
    """
    Calcule le FCF = Operating Cash Flow - CapEx.
    Version 'Honest Data' : respecte les valeurs nulles.
    """
    if cashflow_df is None or cashflow_df.empty:
        return None

    # Extraction robuste
    ocf = extract_most_recent_value(cashflow_df, [
        "Operating Cash Flow",
        "Total Cash From Operating Activities"
    ])

    capex = extract_most_recent_value(cashflow_df, [
        "Capital Expenditure",
        "Net PPE Purchase And Sale",
        "Purchase Of PPE",
        "Purchase Of Property Plant And Equipment"
    ])

    if ocf is not None:
        # Si le CapEx est None, on suppose 0.0 (Secteurs non-intensifs en capital)
        # Mais si le CapEx est 0.0, on l'utilise tel quel.
        safe_capex = capex if capex is not None else 0.0
        return ocf + safe_capex

    return None


def calculate_historical_cagr(income_stmt: pd.DataFrame, years: int = 3) -> Optional[float]:
    """
    Calcule le taux de croissance moyen (CAGR) du Chiffre d'Affaires.
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

    end_val = rev_vals[0]
    start_val = rev_vals[years]

    # Sécurité mathématique : On ne peut pas calculer un CAGR sur des valeurs négatives ou nulles
    if pd.isnull(start_val) or pd.isnull(end_val) or start_val <= 0 or end_val <= 0:
        return None

    return (end_val / start_val) ** (1 / years) - 1.0


def normalize_currency_and_price(info: dict) -> Tuple[str, float]:
    """
    Normalise les devises et ajuste le prix (ex: Pence Londoniens).
    """
    currency = info.get("currency", "USD")
    price = info.get("currentPrice")

    if price is None:
        price = info.get("regularMarketPrice", 0.0)

    # Correction Londres : GBp (Pence) vers GBP (Livre)
    if currency == "GBp":
        currency = "GBP"
        price = price / 100.0

    return currency, float(price)