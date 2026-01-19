"""
infra/auditing/backtester.py

MOTEUR DE VALIDATION HISTORIQUE — VERSION V13.0 (Sprint 6)
Rôle : Isolation temporelle (Point-in-Time) et simulation de valorisation passée.
Standards : SOLID, Prévention du biais d'anticipation, i18n Secured.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

# DT-001/002: Import depuis core.i18n
from src.i18n import DiagnosticTexts
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Moteur responsable de la simulation historique (ST 3.2).
    Il "gèle" les données brutes à une date précise pour simuler une analyse passée.
    """

    @staticmethod
    def freeze_data_at_fiscal_year(raw_data: RawFinancialData, target_year: int) -> Optional[RawFinancialData]:
        """
        Crée une copie de RawFinancialData contenant uniquement les données
        disponibles pour l'année fiscale cible (ST 3.2).
        """
        logger.debug("[Backtest] Tentative d'isolation Point-in-Time pour %s", target_year)

        # 1. Isolation des colonnes dans les états financiers
        frozen_bs = BacktestEngine._filter_df_by_year(raw_data.balance_sheet, target_year)
        frozen_is = BacktestEngine._filter_df_by_year(raw_data.income_stmt, target_year)
        frozen_cf = BacktestEngine._filter_df_by_year(raw_data.cash_flow, target_year)

        if frozen_bs is None or frozen_is is None or frozen_cf is None:
            logger.warning(
                DiagnosticTexts.DATA_FIELD_MISSING_YEAR.format(
                    ticker=raw_data.ticker, field="Financial Statements", year=target_year
                )
            )
            return None

        # 2. Construction de l'objet "gelé"
        # On injecte les colonnes isolées comme étant les données courantes (TTM)
        # pour que les providers existants puissent les traiter sans modification.
        return RawFinancialData(
            ticker=raw_data.ticker,
            info=raw_data.info.copy(),  # Note: Le prix historique devra être injecté séparément
            balance_sheet=frozen_bs,
            income_stmt=frozen_is,
            cash_flow=frozen_cf,
            quarterly_income_stmt=None,  # On ignore le trimestriel pour le backtest annuel
            quarterly_cash_flow=None
        )

    @staticmethod
    def _filter_df_by_year(df: Optional[pd.DataFrame], year: int) -> Optional[pd.DataFrame]:
        """
        Extrait la colonne correspondant à l'année fiscale spécifiée.
        Yahoo utilise des objets Datetime en index de colonnes.
        """
        if df is None or df.empty:
            return None

        # Recherche de la colonne dont l'année correspond au target_year
        # Les colonnes de yfinance sont des Timestamp
        target_col = None
        for col in df.columns:
            if hasattr(col, 'year') and col.year == year:
                target_col = col
                break

        if target_col is None:
            return None

        # On retourne un DataFrame avec une seule colonne (la data gelée)
        return df[[target_col]]

    @staticmethod
    def get_historical_price_at(price_hist: pd.DataFrame, target_year: int) -> float:
        """
        Récupère le prix de clôture réel à la fin de l'année fiscale cible.
        Utilisé pour comparer l'IV calculée au prix du marché de l'époque.
        """
        if price_hist.empty:
            return 0.0

        # On cherche le dernier jour de bourse de l'année cible
        year_mask = price_hist.index.year == target_year
        year_prices = price_hist[year_mask]

        if year_prices.empty:
            return 0.0

        # On prend le dernier prix disponible (Close) de l'année
        return float(year_prices['Close'].iloc[-1])
