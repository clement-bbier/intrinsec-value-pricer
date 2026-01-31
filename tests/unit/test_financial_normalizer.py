"""
tests/unit/test_financial_normalizer.py

Tests pour infra/data_providers/financial_normalizer.py.
Couvre la logique de normalisation des données financières brutes.
"""

import pytest
from unittest.mock import Mock, patch

from infra.data_providers.financial_normalizer import FinancialDataNormalizer
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData
from src.models import Company, MultiplesData


class TestFinancialNormalizer:
    """Tests du normalizer de données financières."""

    def test_normalize_invalid_raw_data(self):
        """Test données brutes invalides (lignes 49-51)."""
        normalizer = FinancialDataNormalizer()

        # Mock raw data invalide
        raw = Mock(spec=RawFinancialData)
        raw.is_valid = False
        raw.ticker = "INVALID"

        result = normalizer.normalize(raw)
        assert result is None

    def test_normalize_success_path(self):
        """Test chemin nominal complet (lignes 47-80)."""
        normalizer = FinancialDataNormalizer()

        # Mock raw data valide
        raw = Mock(spec=RawFinancialData)
        raw.is_valid = True
        raw.ticker = "AAPL"
        raw.info = {
            "shortName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "United States",
            "currency": "USD",
            "currentPrice": 150.0
        }
        raw.balance_sheet = Mock()
        raw.income_stmt = Mock()
        raw.cash_flow = Mock()
        raw.quarterly_income_stmt = Mock()
        raw.quarterly_cash_flow = Mock()

        # Mock les méthodes privées
        with patch.object(normalizer, '_reconstruct_shares', return_value=10e9):
            with patch.object(normalizer, '_reconstruct_capital_structure', return_value={
                'total_debt': 100e9, 'interest_expense': 3.5e9, 'market_cap': 1.5e12
            }):
                with patch.object(normalizer, '_reconstruct_profitability', return_value={
                    'ebit_ttm': 100e9, 'fcf_last': 90e9, 'eps_ttm': 6.0
                }):
                    result = normalizer.normalize(raw)

                    assert result is not None
                    assert isinstance(result, Company)
                    assert result.ticker == "AAPL"
                    assert result.name == "Apple Inc."
                    assert result.sector == "Technology"
                    assert result.currency == "USD"
                    assert result.current_price == 150.0

    @patch('infra.data_providers.financial_normalizer.normalize_currency_and_price')
    def test_normalize_currency_handling(self, mock_normalize_currency):
        """Test gestion devise et prix (lignes 54-55)."""
        normalizer = FinancialDataNormalizer()

        mock_normalize_currency.return_value = ("EUR", 100.0)

        raw = Mock(spec=RawFinancialData)
        raw.is_valid = True
        raw.ticker = "TEST"
        raw.info = {}
        raw.balance_sheet = Mock()
        raw.income_stmt = Mock()
        raw.cash_flow = Mock()
        raw.quarterly_income_stmt = Mock()
        raw.quarterly_cash_flow = Mock()

        with patch.object(normalizer, '_reconstruct_shares', return_value=1e9):
            with patch.object(normalizer, '_reconstruct_capital_structure', return_value={}):
                with patch.object(normalizer, '_reconstruct_profitability', return_value={}):
                    result = normalizer.normalize(raw)

                    mock_normalize_currency.assert_called_once_with(raw.info)
                    assert result.currency == "EUR"
                    assert result.current_price == 100.0

    def test_reconstruct_shares_fallback(self):
        """Test reconstruction actions avec fallbacks (lignes 157-165)."""
        normalizer = FinancialDataNormalizer()

        # Test 1: sharesOutstanding disponible dans info
        info_with_shares = {"sharesOutstanding": 1000000.0}
        shares = normalizer._reconstruct_shares(info_with_shares, None, 100.0)
        assert shares == 1000000.0

        # Test 2: Fallback vers balance sheet
        info_without_shares = {}
        mock_bs = Mock()
        with patch('infra.data_providers.financial_normalizer.extract_most_recent_value', return_value=500000.0):
            shares = normalizer._reconstruct_shares(info_without_shares, mock_bs, 100.0)
            assert shares == 500000.0

        # Test 3: Fallback vers calcul marketCap / price
        info_with_mcap = {"marketCap": 10000000.0}
        shares = normalizer._reconstruct_shares(info_with_mcap, None, 100.0)
        assert shares == 100000.0  # 10M / 100 = 100K

        # Test 4: Aucun fallback disponible - valeur par défaut
        empty_info = {}
        shares = normalizer._reconstruct_shares(empty_info, None, 100.0)
        assert shares == 1.0

    def test_normalize_peers_success_path(self):
        """Test normalisation pairs - chemin nominal (lignes 86-120)."""
        normalizer = FinancialDataNormalizer()

        raw_peers = [
            {
                "symbol": "MSFT",
                "shortName": "Microsoft",
                "trailingPE": 25.0,
                "forwardPE": 22.0,
                "pegRatio": 1.8,
                "priceToBook": 12.0,
                "enterpriseValue": 2000000000000,
                "enterpriseToRevenue": 12.5,
                "enterpriseToEbitda": 18.0
            },
            {
                "symbol": "GOOGL",
                "shortName": "Alphabet",
                "trailingPE": 28.0,
                "forwardPE": 24.0,
                "pegRatio": 1.5,
                "priceToBook": 5.0,
                "enterpriseValue": 1500000000000,
                "enterpriseToRevenue": 6.8,
                "enterpriseToEbitda": 15.0
            }
        ]

        result = normalizer.normalize_peers(raw_peers)

        assert isinstance(result, MultiplesData)
        assert len(result.peers) == 2
        assert result.peers[0].ticker == "MSFT"
        assert result.peers[0].pe_ratio == 25.0
        assert result.peers[1].ticker == "GOOGL"
        assert result.peers[1].pe_ratio == 28.0

    def test_normalize_peers_filters_invalid_data(self):
        """Test filtrage données aberrantes (lignes 120-140)."""
        normalizer = FinancialDataNormalizer()

        raw_peers = [
            {
                "symbol": "VALID",
                "trailingPE": 20.0,  # Valide
                "enterpriseToEbitda": 12.0
            },
            {
                "symbol": "INVALID_PE",
                "trailingPE": 200.0,  # Trop élevé
                "enterpriseToEbitda": 15.0
            },
            {
                "symbol": "INVALID_EV",
                "trailingPE": 25.0,
                "enterpriseToEbitda": 200.0  # Trop élevé
            },
            {
                "symbol": "MISSING_DATA",
                # Données manquantes
            }
        ]

        result = normalizer.normalize_peers(raw_peers)

        # Doit filtrer les données invalides
        assert len(result.peers) >= 1  # Au moins le peer valide
        valid_tickers = [p.ticker for p in result.peers]
        assert "VALID" in valid_tickers

    def test_normalize_peers_empty_list(self):
        """Test liste vide de pairs (lignes 91-92)."""
        normalizer = FinancialDataNormalizer()

        result = normalizer.normalize_peers([])
        assert isinstance(result, MultiplesData)
        assert len(result.peers) == 0

    def test_normalize_peers_pydantic_validation_error(self):
        """Test gestion erreurs Pydantic (lignes 95-115)."""
        normalizer = FinancialDataNormalizer()

        # Peer avec données invalides qui feront échouer la validation Pydantic
        raw_peers = [
            {
                "symbol": "INVALID",
                "trailingPE": "not_a_number",  # Devrait être float
                "enterpriseToEbitda": 15.0
            }
        ]

        result = normalizer.normalize_peers(raw_peers)

        # Le peer invalide devrait être filtré
        assert len(result.peers) == 0

    def test_normalize_peers_statistical_filtering(self):
        """Test filtrage statistique des outliers (lignes 145-170)."""
        normalizer = FinancialDataNormalizer()

        # Créer des données avec outliers évidents
        raw_peers = []
        for i in range(10):
            raw_peers.append({
                "symbol": f"PEER{i}",
                "trailingPE": 20.0 + i * 2,  # 20, 22, 24, ..., 38
                "enterpriseToEbitda": 12.0 + i * 0.5,  # 12, 12.5, 13, ..., 16.5
            })

        # Ajouter un outlier
        raw_peers.append({
            "symbol": "OUTLIER",
            "trailingPE": 200.0,  # Très élevé
            "enterpriseToEbitda": 100.0,  # Très élevé
        })

        result = normalizer.normalize_peers(raw_peers)

        # L'outlier devrait être filtré
        assert len(result.peers) == 10  # Les 10 peers normaux
        peer_tickers = [p.ticker for p in result.peers]
        assert "OUTLIER" not in peer_tickers


class TestNormalizerEdgeCases:
    """Tests de cas limites du normalizer."""

    def test_normalize_missing_info_fields(self):
        """Test données info manquantes (lignes 71-74)."""
        normalizer = FinancialDataNormalizer()

        raw = Mock(spec=RawFinancialData)
        raw.is_valid = True
        raw.ticker = "TEST"
        raw.info = {}  # Info vide
        raw.balance_sheet = Mock()
        raw.income_stmt = Mock()
        raw.cash_flow = Mock()
        raw.quarterly_income_stmt = Mock()
        raw.quarterly_cash_flow = Mock()

        with patch.object(normalizer, '_reconstruct_shares', return_value=1e9):
            with patch.object(normalizer, '_reconstruct_capital_structure', return_value={}):
                with patch.object(normalizer, '_reconstruct_profitability', return_value={}):
                    with patch('infra.data_providers.financial_normalizer.normalize_currency_and_price',
                              return_value=("USD", 100.0)):
                        result = normalizer.normalize(raw)

                        # Doit utiliser les valeurs par défaut
                        assert result.name == "TEST"  # Fallback au ticker
                        assert result.sector == "Unknown"
                        assert result.industry == "Unknown"
                        assert result.country == "Unknown"

    def test_normalize_exception_handling(self):
        """Test gestion d'exceptions dans la reconstruction (lignes 47-80)."""
        normalizer = FinancialDataNormalizer()

        raw = Mock(spec=RawFinancialData)
        raw.is_valid = True
        raw.ticker = "TEST"
        raw.info = {"currentPrice": 100.0}
        raw.balance_sheet = Mock()
        raw.income_stmt = Mock()
        raw.cash_flow = Mock()
        raw.quarterly_income_stmt = Mock()
        raw.quarterly_cash_flow = Mock()

        # Simuler une exception dans _reconstruct_capital_structure
        with patch.object(normalizer, '_reconstruct_shares', return_value=1e6):
            with patch.object(normalizer, '_reconstruct_capital_structure', side_effect=Exception("Capital structure failed")):
                with patch.object(normalizer, '_reconstruct_profitability', return_value={}):
                    with patch('infra.data_providers.financial_normalizer.normalize_currency_and_price', return_value=("USD", 100.0)):
                        # Actuellement, les exceptions sont propagées, pas capturées
                        with pytest.raises(Exception, match="Capital structure failed"):
                            normalizer.normalize(raw)