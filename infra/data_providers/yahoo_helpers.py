"""
infra/data_providers/yahoo_helpers.py

OUTILS D'EXTRACTION & SÉCURITÉ API
Version : V3.5 — Deep Fetch Helpers

Rôle :
- Sécuriser les appels API (Retry policy).
- Fournir des outils d'extraction robustes pour les DataFrames financiers (Bilans).
C'est ici que réside la logique pour "fouiller" dans les bilans quand le résumé est vide.
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
    Indispensable pour yfinance qui peut timeout aléatoirement.
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
    Cherche la valeur la plus récente dans un DataFrame financier (Bilan/Compte de résultat).

    Cette fonction est CRITIQUE pour les banques (BNP) et les actions EU :
    Elle scanne plusieurs alias (ex: 'Total Equity', 'Stockholder Equity')
    et prend la donnée la plus récente non nulle.
    """
    if df is None or df.empty:
        return None

    # 1. Sécurisation de l'ordre des colonnes (Dates)
    # On veut la colonne la plus récente en premier (index 0)
    try:
        # Si les colonnes sont des dates, on trie décroissant (2024, 2023...)
        df = df.sort_index(axis=1, ascending=False)
    except:
        pass  # Si ce n'est pas des dates, on garde l'ordre par défaut de Yahoo (souvent déjà trié)

    # 2. Recherche par clé
    for key in keys:
        if key in df.index:
            # On extrait la ligne correspondante
            row = df.loc[key]

            # 3. Recherche de la première valeur valide dans le temps
            # (Si 2024 est vide/NaN, on regarde 2023)
            for val in row.values:
                if pd.notnull(val) and val != 0:
                    try:
                        return float(val)
                    except ValueError:
                        continue

    return None


def _safe_get_first(df: pd.DataFrame, aliases: List[str]) -> Optional[float]:
    """
    Alias pour rétro-compatibilité avec d'anciens modules.
    Redirige vers la nouvelle logique robuste.
    """
    return extract_most_recent_value(df, aliases)


# ==============================================================================
# 3. HELPERS MÉTIER (FLUX & CROISSANCE)
# ==============================================================================

def get_simple_annual_fcf(cashflow_df: pd.DataFrame) -> Optional[float]:
    """
    Calcule le FCF = Operating Cash Flow - CapEx.
    Utilise le Deep Fetch pour trouver les lignes même si elles changent de nom.
    """
    if cashflow_df is None or cashflow_df.empty:
        return None

    # Recherche robuste du Cash Flow Opérationnel
    ocf = extract_most_recent_value(cashflow_df, [
        "Operating Cash Flow",
        "Total Cash From Operating Activities"
    ])

    # Recherche robuste du CapEx (Souvent nommé 'Purchase of PPE')
    # CapEx est souvent négatif dans Yahoo, on l'additionne algébriquement
    capex = extract_most_recent_value(cashflow_df, [
        "Capital Expenditure",
        "Net PPE Purchase And Sale",
        "Purchase Of PPE",
        "Purchase Of Property Plant And Equipment"
    ])

    if ocf is not None:
        # Si Capex manquant, on suppose 0 (prudence, ou secteur services)
        return ocf + (capex if capex else 0.0)

    return None


def calculate_historical_cagr(income_stmt: pd.DataFrame, years: int = 3) -> Optional[float]:
    """
    Calcule le taux de croissance moyen (CAGR) du Chiffre d'Affaires.
    """
    if income_stmt is None or income_stmt.empty:
        return None

    revenue_keys = ["Total Revenue", "Revenue", "Gross Revenue"]
    rev_vals = None

    # Extraction de la série temporelle complète
    for key in revenue_keys:
        if key in income_stmt.index:
            rev_vals = income_stmt.loc[key].values
            break

    if rev_vals is None or len(rev_vals) < years + 1:
        return None

    # rev_vals[0] = Année N (Récent), rev_vals[years] = Année N-years (Passé)
    end_val = rev_vals[0]
    start_val = rev_vals[years]

    if start_val <= 0 or end_val <= 0:
        return None

    # Formule du CAGR
    return (end_val / start_val) ** (1 / years) - 1.0


def normalize_currency_and_price(info: dict) -> Tuple[str, float]:
    """
    Normalise les devises (ex: GBp -> GBP) et ajuste le prix en conséquence.
    Gère les cas spécifiques comme Londres (Pence).
    """
    currency = info.get("currency", "USD")
    price = info.get("currentPrice", 0.0)

    # Cas spécifique Londres : Prix en Pence (GBp), Bilan en Livres (GBP)
    if currency == "GBp":
        currency = "GBP"
        price = price / 100.0

    return currency, price