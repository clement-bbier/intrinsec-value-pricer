"""
tests/unit/test_multiples_strategy.py
Validation de la Triangulation avec Mocks financiers robustes.
"""

from unittest.mock import patch, MagicMock
from src.valuation.options.multiples import MarketMultiplesStrategy
from src.models import MultiplesData, PeerMetric

class TestMarketMultiplesStrategy:
    def test_execute_success_path(self, sample_financials, sample_params):
        # Setup data
        multiples_data = MultiplesData(
            peers=[PeerMetric(ticker="P1", pe_ratio=15.0, ev_ebitda=10.0)],
            median_pe=15.0, median_ev_ebitda=10.0
        )

        # SÉCURISATION : On remplit les champs requis pour l'audit interne du pipeline
        sample_financials.ebit_ttm = 100.0
        sample_financials.interest_expense = 10.0
        sample_financials.net_income_ttm = 80.0
        sample_financials.ebitda_ttm = 120.0
        sample_financials.shares_outstanding = 10.0
        sample_financials.total_debt = 50.0
        sample_financials.cash_and_equivalents = 20.0

        strategy = MarketMultiplesStrategy(multiples_data)

        # On mock l'audit pour isoler le test de la stratégie
        with patch('infra.auditing.audit_engine.AuditEngine.compute_audit') as mock_audit:
            mock_audit.return_value = MagicMock()
            result = strategy.execute(sample_financials, sample_params)

            assert result.intrinsic_value_per_share > 0
            assert result.ebitda_based_price > 0