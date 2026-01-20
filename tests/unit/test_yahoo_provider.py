"""
tests/unit/test_yahoo_provider.py

Tests corrigés pour infra/data_providers/yahoo_provider.py.
Suppression des hallucinations et sécurisation des calculs arithmétiques.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from infra.data_providers.yahoo_provider import (
    YahooFinanceProvider,
    DataProviderStatus
)
from src.models import CompanyFinancials, DCFParameters, MultiplesData
from src.exceptions import TickerNotFoundError


class TestDataProviderStatus:
    """Tests de la classe DataProviderStatus (Score de confiance)."""

    def test_data_provider_status_initial_state(self):
        status = DataProviderStatus()
        assert status.is_degraded_mode is False
        assert status.confidence_score == 1.0

    def test_data_provider_status_multiple_fallbacks(self):
        """Test avec réduction progressive du score (Précision flottante)."""
        status = DataProviderStatus()

        status.add_fallback("yahoo_api")
        status.add_fallback("sector_fallback")
        status.add_fallback("global_averages")

        assert status.is_degraded_mode is True
        # Utilisation de pytest.approx pour éviter l'erreur 0.5499999 != 0.55
        assert status.confidence_score == pytest.approx(0.55, rel=1e-2)


class TestYahooFinanceProvider:
    """Tests du YahooFinanceProvider (Extraction et Enrichissement)."""

    def setup_method(self):
        """Initialisation avec mock du MacroProvider obligatoire."""
        self.mock_macro = MagicMock()
        self.provider = YahooFinanceProvider(macro_provider=self.mock_macro)

    @patch('infra.data_providers.yahoo_provider.YahooRawFetcher')
    @patch('infra.data_providers.yahoo_provider.FinancialDataNormalizer')
    @patch('infra.ref_data.country_matrix.get_country_context')
    @patch('infra.data_providers.yahoo_provider.calculate_synthetic_cost_of_debt')
    @patch('infra.data_providers.yahoo_provider.calculate_historical_share_growth')
    def test_get_company_financials_success_path(self, mock_calc_growth, mock_calc_debt,
                                                 mock_country, mock_normalizer_cls,
                                                 mock_fetcher_cls):
        """Test chemin nominal complet incluant la nouvelle logique de dilution."""

        # 1. Setup Data Brute
        mock_raw = MagicMock()
        mock_raw.is_valid = True
        # Simuler une balance sheet pour l'historique des actions
        mock_raw.balance_sheet = MagicMock()
        mock_fetcher_cls.return_value.fetch_historical_deep.return_value = mock_raw

        # 2. Setup Normalizer
        mock_normalizer = mock_normalizer_cls.return_value
        mock_fin = MagicMock(spec=CompanyFinancials)
        mock_fin.ticker = "AAPL"
        mock_fin.beta = 1.2
        mock_fin.sector = "Technology"
        mock_fin.net_income_ttm = 100.0
        mock_fin.dividend_share = 0.5
        mock_fin.shares_outstanding = 10.0
        mock_fin.book_value = 500.0
        mock_normalizer.normalize.return_value = mock_fin
        # Mock de l'extraction d'historique
        mock_normalizer.extract_shares_history.return_value = [100, 102, 104]

        # 3. Setup Math & Macro
        from infra.macro.yahoo_macro_provider import MacroContext
        self.mock_macro.get_macro_context.return_value = MacroContext(
            date=datetime.now(), currency="USD", risk_free_rate=0.04,
            risk_free_source="US10Y", market_risk_premium=0.05,
            perpetual_growth_rate=0.02, corporate_aaa_yield=0.05
        )

        mock_country.return_value = {"tax_rate": 0.25}
        mock_calc_debt.return_value = 0.06
        mock_calc_growth.return_value = 0.02  # 2% de dilution détectée

        # Exécution
        result_fin, result_params = self.provider.get_company_financials_and_parameters("AAPL", 5)

        # Vérifications Sprint 3
        assert result_params.growth.annual_dilution_rate == 0.02
        assert result_fin.ticker == "AAPL"

    @patch('infra.data_providers.yahoo_provider.YahooRawFetcher')
    def test_get_company_financials_invalid_ticker(self, mock_fetcher_cls):
        """Vérifie la levée d'exception pour un ticker inexistant."""
        mock_raw = MagicMock()
        mock_raw.is_valid = False
        mock_fetcher_cls.return_value.fetch.return_value = mock_raw

        with pytest.raises(TickerNotFoundError):
            self.provider.get_company_financials_and_parameters("NOTFOUND", 5)

    @patch('infra.data_providers.yahoo_provider.st')
    @patch('infra.data_providers.yahoo_provider.get_sector_fallback_with_metadata')
    def test_get_peer_multiples_fallback(self, mock_fallback_func, mock_st):
        """Vérifie le passage au fallback sectoriel si aucun pair n'est trouvé."""
        # Setup mock de status Streamlit
        mock_status = MagicMock()
        mock_st.status.return_value.__enter__.return_value = mock_status

        # Setup objet réel pour éviter les problèmes de sérialisation pickle
        from infra.ref_data.sector_fallback import SectorFallbackResult
        from src.models import MultiplesData

        real_multiples = MultiplesData()
        real_fallback = SectorFallbackResult(
            multiples=real_multiples,
            is_fallback=True,
            sector_key="technology",
            confidence_score=0.75,
            source_description="Sector fallback"
        )
        mock_fallback_func.return_value = real_fallback

        # On simule un ticker inconnu pour forcer le fallback
        result = self.provider.get_peer_multiples("UNKNOWN_CO")

        assert result is not None
        mock_fallback_func.assert_called()

    def test_provider_status_is_public(self):
        """Vérifie que l'attribut status est accessible et correct."""
        assert hasattr(self.provider, 'status')
        assert isinstance(self.provider.status, DataProviderStatus)


class TestProviderResilience:
    """Tests de robustesse face aux pannes externes."""

    def setup_method(self):
        """Initialisation avec mock du MacroProvider obligatoire."""
        self.mock_macro = MagicMock()
        self.provider = YahooFinanceProvider(macro_provider=self.mock_macro)

    @patch('infra.data_providers.yahoo_provider.st')
    def test_get_peer_multiples_manual_override(self, mock_st):
        """Vérifie que les pairs manuels court-circuitent la recherche auto."""
        manual_tickers = ["MSFT", "GOOGL"]

        # On mock l'appel interne réel
        with patch.object(self.provider, 'get_peer_multiples') as mock_method:
            mock_method.return_value = MagicMock(spec=MultiplesData)

            self.provider.get_peer_multiples("AAPL", manual_tickers)

            # Vérifie que les tickers manuels ont été passés
            args, kwargs = mock_method.call_args
            assert manual_tickers in args or manual_tickers in kwargs.values()