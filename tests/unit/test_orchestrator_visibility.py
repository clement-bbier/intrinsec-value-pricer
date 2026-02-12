"""
tests/unit/test_orchestrator_visibility.py

ORCHESTRATOR VISIBILITY TESTS
==============================
Role: Validate that the orchestrator correctly uses OR logic for
Pillar 4 (Risk) and Pillar 5 (Market) tab visibility.
"""

import pytest

from app.views.results.orchestrator import _is_market_pillar_active, _is_risk_pillar_active
from src.models.company import Company
from src.models.enums import ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CommonParameters, FinancialRatesParameters
from src.models.parameters.options import (
    BacktestParameters,
    ExtensionBundleParameters,
    MCParameters,
    PeersParameters,
    ScenariosParameters,
    SensitivityParameters,
    SOTPParameters,
)
from src.models.parameters.strategies import FCFFStandardParameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import FCFFStandardResults
from src.models.valuation import ValuationRequest, ValuationResult


@pytest.fixture
def make_result():
    """Factory fixture to create a ValuationResult with configurable extensions."""

    def _make(
        mc_enabled: bool = False,
        sens_enabled: bool = False,
        scenario_enabled: bool = False,
        backtest_enabled: bool = False,
        peers_enabled: bool = False,
        sotp_enabled: bool = False,
    ) -> ValuationResult:
        request = ValuationRequest(
            mode=ValuationMethodology.FCFF_STANDARD,
            parameters=Parameters(
                structure=Company(ticker="TEST", current_price=100.0),
                common=CommonParameters(
                    rates=FinancialRatesParameters(
                        risk_free_rate=0.04,
                        market_risk_premium=0.05,
                        beta=1.0,
                        tax_rate=0.21,
                    ),
                ),
                strategy=FCFFStandardParameters(projection_years=5, fcf_anchor=100_000.0),
                extensions=ExtensionBundleParameters(
                    monte_carlo=MCParameters(enabled=mc_enabled),
                    sensitivity=SensitivityParameters(enabled=sens_enabled),
                    scenarios=ScenariosParameters(enabled=scenario_enabled),
                    backtest=BacktestParameters(enabled=backtest_enabled),
                    peers=PeersParameters(enabled=peers_enabled),
                    sotp=SOTPParameters(enabled=sotp_enabled),
                ),
            ),
        )

        results = Results(
            common=CommonResults(
                rates=ResolvedRates(cost_of_equity=0.09, cost_of_debt_after_tax=0.04, wacc=0.08),
                capital=ResolvedCapital(
                    market_cap=1_000_000.0,
                    enterprise_value=1_100_000.0,
                    net_debt_resolved=100_000.0,
                    equity_value_total=1_000_000.0,
                ),
                intrinsic_value_per_share=110.0,
                upside_pct=0.10,
            ),
            strategy=FCFFStandardResults(
                projected_flows=[100_000.0],
                discount_factors=[0.926],
                terminal_value=2_000_000.0,
                discounted_terminal_value=1_500_000.0,
                tv_weight_pct=0.75,
            ),
            extensions=ExtensionBundleResults(),
        )

        return ValuationResult(request=request, results=results)

    return _make


class TestRiskPillarORLogic:
    """Pillar 4 should appear if ANY single risk module is active (OR logic)."""

    def test_all_disabled_hides_pillar(self, make_result):
        """Pillar 4 should be hidden when no risk module is enabled."""
        result = make_result()
        assert not _is_risk_pillar_active(result)

    def test_only_monte_carlo_shows_pillar(self, make_result):
        """Pillar 4 should appear with only Monte Carlo enabled."""
        result = make_result(mc_enabled=True)
        assert _is_risk_pillar_active(result)

    def test_only_sensitivity_shows_pillar(self, make_result):
        """Pillar 4 should appear with only Sensitivity enabled."""
        result = make_result(sens_enabled=True)
        assert _is_risk_pillar_active(result)

    def test_only_scenarios_shows_pillar(self, make_result):
        """Pillar 4 should appear with only Scenarios enabled."""
        result = make_result(scenario_enabled=True)
        assert _is_risk_pillar_active(result)

    def test_only_backtest_shows_pillar(self, make_result):
        """Pillar 4 should appear with only Backtest enabled."""
        result = make_result(backtest_enabled=True)
        assert _is_risk_pillar_active(result)

    def test_multiple_modules_show_pillar(self, make_result):
        """Pillar 4 should appear with multiple risk modules enabled."""
        result = make_result(mc_enabled=True, sens_enabled=True, backtest_enabled=True)
        assert _is_risk_pillar_active(result)


class TestMarketPillarORLogic:
    """Pillar 5 should appear if EITHER SOTP or Peers is active (OR logic)."""

    def test_all_disabled_hides_pillar(self, make_result):
        """Pillar 5 should be hidden when no market module is enabled."""
        result = make_result()
        assert not _is_market_pillar_active(result)

    def test_only_peers_shows_pillar(self, make_result):
        """Pillar 5 should appear with only Peers enabled."""
        result = make_result(peers_enabled=True)
        assert _is_market_pillar_active(result)

    def test_only_sotp_shows_pillar(self, make_result):
        """Pillar 5 should appear with only SOTP enabled."""
        result = make_result(sotp_enabled=True)
        assert _is_market_pillar_active(result)

    def test_both_show_pillar(self, make_result):
        """Pillar 5 should appear with both Peers and SOTP enabled."""
        result = make_result(peers_enabled=True, sotp_enabled=True)
        assert _is_market_pillar_active(result)


class TestPillarIndependence:
    """Verify that risk and market pillars are independent of each other."""

    def test_risk_without_market(self, make_result):
        """Risk pillar can be active while market is not."""
        result = make_result(mc_enabled=True)
        assert _is_risk_pillar_active(result)
        assert not _is_market_pillar_active(result)

    def test_market_without_risk(self, make_result):
        """Market pillar can be active while risk is not."""
        result = make_result(sotp_enabled=True)
        assert not _is_risk_pillar_active(result)
        assert _is_market_pillar_active(result)

    def test_both_active(self, make_result):
        """Both pillars can be active simultaneously."""
        result = make_result(mc_enabled=True, peers_enabled=True)
        assert _is_risk_pillar_active(result)
        assert _is_market_pillar_active(result)
