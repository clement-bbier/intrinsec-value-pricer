"""
tests/unit/test_multiples_strategy.py

Tests corrigés pour src/valuation/strategies/multiples.py.
Valide la triangulation des multiples et la gestion de l'Equity Bridge.
"""

import pytest
from unittest.mock import patch

from src.valuation.strategies.multiples import MarketMultiplesStrategy
from src.models import (
    MultiplesData, MultiplesValuationResult,
    PeerMetric
)


class TestMarketMultiplesStrategy:
    """Tests de la stratégie de valorisation par multiples sectoriels."""

    def test_execute_success_path(self, sample_financials, sample_params):
        """Test du chemin nominal complet (Calcul des 3 signaux)."""
        # Setup multiples data
        multiples_data = MultiplesData(
            peers=[
                PeerMetric(ticker="PEER1", name="P1", pe_ratio=20.0, ev_to_ebitda=15.0),
            ],
            median_pe=22.5,
            median_ev_ebitda=16.5,
            median_ev_rev=8.0
        )

        # Configuration des financials (Sans modifier net_debt qui est Read-Only)
        sample_financials.net_income_ttm = 100e6
        sample_financials.ebitda_ttm = 150e6
        sample_financials.revenue_ttm = 400e6
        sample_financials.shares_outstanding = 10e6
        sample_financials.total_debt = 60e6
        sample_financials.cash_and_equivalents = 10e6 # net_debt sera 50e6
        sample_financials.minority_interests = 5e6
        sample_financials.pension_provisions = 10e6

        strategy = MarketMultiplesStrategy(multiples_data, glass_box_enabled=True)
        result = strategy.execute(sample_financials, sample_params)

        assert isinstance(result, MultiplesValuationResult)
        assert result.intrinsic_value_per_share > 0
        assert result.pe_based_price > 0
        assert result.ebitda_based_price > 0
        assert result.rev_based_price > 0
        assert len(result.calculation_trace) >= 3

    def test_execute_missing_financial_data(self, sample_financials, sample_params):
        """Vérifie que les signaux sont à 0 si les données sont absentes."""
        multiples_data = MultiplesData(peers=[], median_pe=20.0, median_ev_ebitda=15.0, median_ev_rev=8.0)

        # Simuler données manquantes
        sample_financials.net_income_ttm = None
        sample_financials.ebitda_ttm = None
        sample_financials.shares_outstanding = 10e6

        strategy = MarketMultiplesStrategy(multiples_data)
        result = strategy.execute(sample_financials, sample_params)

        assert result.pe_based_price == 0.0
        assert result.ebitda_based_price == 0.0

    def test_triangulation_with_mixed_signals(self, sample_financials, sample_params):
        """Vérifie que la triangulation ignore les signaux nuls ou négatifs."""
        multiples_data = MultiplesData(peers=[], median_pe=20.0, median_ev_ebitda=15.0, median_ev_rev=5.0)

        # Setup : P/E valide, EBITDA invalide, Rev valide
        sample_financials.net_income_ttm = 100e6 
        sample_financials.ebitda_ttm = None # Doit donner 0.0
        sample_financials.revenue_ttm = 500e6
        sample_financials.shares_outstanding = 10e6
        sample_financials.total_debt = 0
        sample_financials.cash_and_equivalents = 0

        strategy = MarketMultiplesStrategy(multiples_data)
        result = strategy.execute(sample_financials, sample_params)

        assert result.pe_based_price > 0
        assert result.ebitda_based_price == 0.0
        assert result.rev_based_price > 0
        
        # Moyenne attendue sur les 2 signaux valides uniquement
        expected = (result.pe_based_price + result.rev_based_price) / 2
        assert result.intrinsic_value_per_share == pytest.approx(expected)

    def test_record_steps_pe_details(self, sample_financials, sample_params):
        """Vérifie que les détails du calcul P/E sont correctement tracés."""
        multiples_data = MultiplesData(peers=[], median_pe=25.0, median_ev_ebitda=10.0, median_ev_rev=5.0)
        sample_financials.net_income_ttm = 100e6
        sample_financials.shares_outstanding = 10e6

        strategy = MarketMultiplesStrategy(multiples_data, glass_box_enabled=True)
        result = strategy.execute(sample_financials, sample_params)

        pe_step = next((s for s in result.calculation_trace if s.step_key == "RELATIVE_PE"), None)
        assert pe_step is not None
        assert "25.0" in pe_step.interpretation
        # (100M * 25) / 10M = 250
        assert pe_step.result == pytest.approx(250.0)

    def test_equity_bridge_deductions(self, sample_financials, sample_params):
        """Vérifie que la dette et les minoritaires sont bien déduits pour l'EV."""
        multiples_data = MultiplesData(peers=[], median_pe=10.0, median_ev_ebitda=10.0, median_ev_rev=10.0)
        
        # EV = EBITDA (100) * Multiple (10) = 1000
        sample_financials.ebitda_ttm = 100e6
        sample_financials.total_debt = 400e6 # Dette énorme
        sample_financials.cash_and_equivalents = 0
        sample_financials.shares_outstanding = 1e6

        strategy = MarketMultiplesStrategy(multiples_data)
        result = strategy.execute(sample_financials, sample_params)

        # Equity Value = 1000 - 400 = 600. Prix = 600
        assert result.ebitda_based_price == pytest.approx(600.0)

    def test_verify_output_contract_called(self, sample_financials, sample_params):
        """Vérifie l'appel au contrat de validation de sortie."""
        multiples_data = MultiplesData(peers=[], median_pe=20.0, median_ev_ebitda=15.0, median_ev_rev=8.0)
        sample_financials.net_income_ttm = 100e6
        sample_financials.shares_outstanding = 10e6

        strategy = MarketMultiplesStrategy(multiples_data)

        # Correction : Utilisation de patch.object sur l'instance de strategy
        with patch.object(strategy, 'verify_output_contract') as mock_verify:
            strategy.execute(sample_financials, sample_params)
            mock_verify.assert_called_once()