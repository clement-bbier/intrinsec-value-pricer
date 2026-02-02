"""
tests/unit/test_backtester.py

Tests pour infra/auditing/backtester.py.
Couvre UNIQUEMENT les fonctions réelles : freeze_data_at_fiscal_year, _filter_df_by_year, get_historical_price_at.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd

from src.valuation.backtest_engine import BacktestEngine
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData


class TestBacktestEngine:
    """Tests du BacktestEngine - fonctions réelles uniquement."""

    def test_freeze_data_at_fiscal_year_success(self):
        """Test isolation temporelle réussie (lignes 30-61)."""
        # Créer des données mock avec les attributs requis
        raw_data = Mock(spec=RawFinancialData)
        raw_data.ticker = "AAPL"
        raw_data.info = {"some": "data"}
        raw_data.balance_sheet = Mock()  # Attributs requis par la fonction
        raw_data.income_stmt = Mock()
        raw_data.cash_flow = Mock()

        # Mock des dataframes avec colonnes d'années
        mock_bs = pd.DataFrame({'2022-12-31': [100, 200]})
        mock_is = pd.DataFrame({'2022-12-31': [50, 75]})
        mock_cf = pd.DataFrame({'2022-12-31': [25, 30]})

        with patch.object(BacktestEngine, '_filter_df_by_year') as mock_filter:
            mock_filter.side_effect = [mock_bs, mock_is, mock_cf]

            result = BacktestEngine.freeze_data_at_fiscal_year(raw_data, 2022)

            assert result is not None
            assert result.ticker == "AAPL"
            assert result.info == {"some": "data"}
            assert result.balance_sheet.equals(mock_bs)
            assert result.income_stmt.equals(mock_is)
            assert result.cash_flow.equals(mock_cf)

    def test_freeze_data_missing_financials(self):
        """Test données financières manquantes (lignes 42-48)."""
        raw_data = Mock(spec=RawFinancialData)
        raw_data.ticker = "MISSING"
        raw_data.balance_sheet = Mock()  # Attributs requis
        raw_data.income_stmt = Mock()
        raw_data.cash_flow = Mock()

        with patch.object(BacktestEngine, '_filter_df_by_year') as mock_filter:
            mock_filter.return_value = None  # Simuler données manquantes pour BS

            result = BacktestEngine.freeze_data_at_fiscal_year(raw_data, 2021)

            assert result is None

    def test_filter_df_by_year_with_timestamp_column(self):
        """Test filtrage DataFrame avec colonne Timestamp (lignes 64-84)."""
        # Créer un DataFrame avec colonnes Timestamp (comme Yahoo Finance)
        data = {
            pd.Timestamp('2022-12-31'): [100, 200, 300],
            pd.Timestamp('2021-12-31'): [90, 180, 270],
            pd.Timestamp('2020-12-31'): [80, 160, 240]
        }
        df = pd.DataFrame(data, index=['A', 'B', 'C'])

        result = BacktestEngine._filter_df_by_year(df, 2021)

        assert result is not None
        # Devrait contenir une seule colonne pour 2021
        assert len(result.columns) == 1
        assert result.columns[0].year == 2021

    def test_filter_df_by_year_no_matching_year(self):
        """Test filtrage DataFrame - année non trouvée (ligne 80-81)."""
        data = {
            pd.Timestamp('2022-12-31'): [100, 200],
            pd.Timestamp('2021-12-31'): [90, 180]
        }
        df = pd.DataFrame(data, index=['A', 'B'])

        result = BacktestEngine._filter_df_by_year(df, 2023)  # Année non présente

        assert result is None

    def test_filter_df_by_year_none_input(self):
        """Test filtrage DataFrame - input None (lignes 69-70)."""
        result = BacktestEngine._filter_df_by_year(None, 2022)
        assert result is None

    def test_filter_df_by_year_empty_dataframe(self):
        """Test filtrage DataFrame vide (lignes 69-70)."""
        df = pd.DataFrame()
        result = BacktestEngine._filter_df_by_year(df, 2022)
        assert result is None

    def test_get_historical_price_at_success(self):
        """Test récupération prix historique (lignes 87-103)."""
        # Créer un DataFrame de prix historiques
        dates = pd.date_range('2021-01-01', '2021-12-31', freq='D')
        prices = pd.DataFrame({
            'Close': [100 + i * 0.1 for i in range(len(dates))]
        }, index=dates)

        result = BacktestEngine.get_historical_price_at(prices, 2021)

        assert result > 0
        # Devrait être le dernier prix de 2021
        expected_last_price = prices['Close'].iloc[-1]
        assert result == pytest.approx(expected_last_price, rel=1e-10)

    def test_get_historical_price_at_empty_dataframe(self):
        """Test récupération prix - DataFrame vide (lignes 92-93)."""
        df = pd.DataFrame()
        result = BacktestEngine.get_historical_price_at(df, 2021)
        assert result == 0.0

    def test_get_historical_price_at_no_data_for_year(self):
        """Test récupération prix - aucune donnée pour l'année (lignes 96-100)."""
        # DataFrame avec des données mais pas pour l'année demandée
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        prices = pd.DataFrame({
            'Close': [100 + i * 0.1 for i in range(len(dates))]
        }, index=dates)

        result = BacktestEngine.get_historical_price_at(prices, 2021)  # Année sans données
        assert result == 0.0


class TestBacktestIntegration:
    """Tests d'intégration du backtester."""

    def test_complete_freeze_workflow(self):
        """Test workflow complet de freezing des données."""
        # Créer des données complètes
        raw_data = Mock(spec=RawFinancialData)
        raw_data.ticker = "INTEGRATION_TEST"
        raw_data.info = {"company": "Test Company"}

        # DataFrames avec colonnes d'années appropriées
        bs_data = pd.DataFrame({
            pd.Timestamp('2022-12-31'): [1000, 500],
            pd.Timestamp('2021-12-31'): [900, 450]
        })
        is_data = pd.DataFrame({
            pd.Timestamp('2022-12-31'): [200, 100],
            pd.Timestamp('2021-12-31'): [180, 90]
        })
        cf_data = pd.DataFrame({
            pd.Timestamp('2022-12-31'): [150, 50],
            pd.Timestamp('2021-12-31'): [130, 40]
        })

        raw_data.balance_sheet = bs_data
        raw_data.income_stmt = is_data
        raw_data.cash_flow = cf_data

        result = BacktestEngine.freeze_data_at_fiscal_year(raw_data, 2022)

        assert result is not None
        assert result.ticker == "INTEGRATION_TEST"
        assert len(result.balance_sheet.columns) == 1
        assert len(result.income_stmt.columns) == 1
        assert len(result.cash_flow.columns) == 1
        # Vérifier que c'est bien l'année 2022
        assert result.balance_sheet.columns[0].year == 2022