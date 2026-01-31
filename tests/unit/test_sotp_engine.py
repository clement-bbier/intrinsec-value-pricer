"""
tests/unit/test_sotp_engine.py

Tests corrigés pour src/valuation/sotp_engine.py.
Couvre la logique de valorisation par somme des parties (SOTP).
Architecture : Alignée sur Parameters SSOT (V9.0+).
"""

import pytest
from unittest.mock import MagicMock

from src.valuation.sotp_engine import run_sotp_valuation
from src.models import (
    SOTPParameters, CompanyFinancials, BusinessUnit
)

class TestSOTPValuation:
    """Tests de la fonction run_sotp_valuation avec calculs robustes et SSOT."""

    def test_run_sotp_disabled(self):
        """Test SOTP désactivé : doit retourner 0.0 et aucune étape."""
        # On utilise l'alias 'enable_sotp' pour garantir l'initialisation Pydantic
        params = SOTPParameters(enable_sotp=False)
        financials = MagicMock(spec=CompanyFinancials)

        equity_value, steps = run_sotp_valuation(params, financials)

        assert equity_value == 0.0
        assert steps == []

    def test_run_sotp_no_segments(self):
        """Test SOTP activé mais sans segments : doit retourner 0.0."""
        params = SOTPParameters(enable_sotp=True, segments=[])
        financials = MagicMock(spec=CompanyFinancials)

        equity_value, steps = run_sotp_valuation(params, financials)

        assert equity_value == 0.0
        assert steps == []

    def test_run_sotp_single_segment_no_discount(self):
        """Test SOTP segment unique sans décote de conglomérat."""
        segment = BusinessUnit(
            name="Tech Division",
            enterprise_value=1000.0,
            revenue=500.0,
            ebitda_margin=0.2
        )
        # On force enable_sotp=True pour activer la branche logique du moteur
        params = SOTPParameters(enable_sotp=True, segments=[segment], conglomerate_discount=0.0)

        # Mocking des attributs financiers (Bridge)
        financials = MagicMock(spec=CompanyFinancials)
        financials.total_debt = 200.0
        financials.cash_and_equivalents = 50.0
        financials.minority_interests = 10.0
        financials.pension_provisions = 5.0

        equity_value, steps = run_sotp_valuation(params, financials)

        # Calcul : (EV: 1000) - 200 + 50 - 10 - 5 = 835
        assert equity_value == pytest.approx(835.0)
        assert len(steps) == 2

    def test_ev_consolidation_step_details(self):
        """Vérifie la justesse de l'étape 1 : Consolidation de l'EV avec décote."""
        segments = [
            BusinessUnit(name="S1", enterprise_value=100.0, revenue=50.0),
            BusinessUnit(name="S2", enterprise_value=200.0, revenue=100.0)
        ]
        params = SOTPParameters(enable_sotp=True, segments=segments, conglomerate_discount=0.10)

        financials = MagicMock(spec=CompanyFinancials)
        financials.total_debt = 0.0
        financials.cash_and_equivalents = 0.0
        financials.minority_interests = 0.0
        financials.pension_provisions = 0.0

        _, steps = run_sotp_valuation(params, financials)

        assert len(steps) >= 1
        ev_step = steps[0]
        assert ev_step.step_key == "SOTP_EV_CONSOLIDATION"
        # (100 + 200) * (1 - 0.10) = 270.0
        assert ev_step.result == pytest.approx(270.0)
        # Vérification de la présence de la décote dans les hypothèses de trace
        assert any(h.value == 0.10 for h in ev_step.hypotheses)

    def test_equity_bridge_step_details(self):
        """Vérifie la justesse de l'étape 2 : Le passage EV -> Equity (Bridge)."""
        segment = BusinessUnit(name="Unit", enterprise_value=500.0)
        params = SOTPParameters(enable_sotp=True, segments=[segment], conglomerate_discount=0.0)

        financials = MagicMock(spec=CompanyFinancials)
        financials.total_debt = 150.0
        financials.cash_and_equivalents = 75.0
        financials.minority_interests = 25.0
        financials.pension_provisions = 10.0

        equity_value, steps = run_sotp_valuation(params, financials)

        assert len(steps) == 2
        bridge_step = steps[1]
        assert bridge_step.step_key == "SOTP_EQUITY_BRIDGE"
        # 500 (EV) - 150 (Debt) + 75 (Cash) - 25 (Min) - 10 (Pens) = 390.0
        assert bridge_step.result == pytest.approx(390.0)
        assert equity_value == pytest.approx(390.0)

    def test_sotp_with_negative_discount(self):
        """Test SOTP avec une prime de conglomérat (décote négative)."""
        segment = BusinessUnit(name="Premium", enterprise_value=100.0)
        params = SOTPParameters(enable_sotp=True, segments=[segment], conglomerate_discount=-0.10)

        financials = MagicMock(spec=CompanyFinancials)
        financials.total_debt = 20.0
        financials.cash_and_equivalents = 5.0
        financials.minority_interests = 0.0
        financials.pension_provisions = 0.0

        equity_value, _ = run_sotp_valuation(params, financials)

        # EV = 100 * (1 - (-0.1)) = 100 * 1.1 = 110.
        # Equity = 110 - 20 + 5 = 95
        assert equity_value == pytest.approx(95.0)

    def test_sotp_numerical_consistency(self):
        """Vérifie que le résultat final est identique au résultat du dernier step de calcul."""
        segment = BusinessUnit(name="Test", enterprise_value=1000.0)
        params = SOTPParameters(enable_sotp=True, segments=[segment], conglomerate_discount=0.20)

        financials = MagicMock(spec=CompanyFinancials)
        financials.total_debt = 100.0
        financials.cash_and_equivalents = 0.0
        financials.minority_interests = 0.0
        financials.pension_provisions = 0.0

        equity_value, steps = run_sotp_valuation(params, financials)
        
        # EV Consolidé = 1000 * 0.8 = 800
        # Equity = 800 - 100 = 700
        assert equity_value == pytest.approx(700.0)
        assert steps[-1].result == pytest.approx(equity_value)