"""
tests/ui/test_pillars.py

PILLAR VISIBILITY SMOKE TESTS
==============================
Role: Validate that is_visible() methods work correctly with a complete
ValuationResult object, and that the V2 model paths are correct.
"""

import pytest

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
from src.models.results.options import (
    BacktestResults,
    ExtensionBundleResults,
    MCResults,
    PeersResults,
    ScenariosResults,
    SensitivityResults,
    SOTPResults,
    ScenarioOutcome,
    HistoricalPoint,
)
from src.models.results.strategies import FCFFStandardResults
from src.models.valuation import ValuationRequest, ValuationResult

from app.views.results.pillars.monte_carlo_distribution import MonteCarloDistributionTab
from app.views.results.pillars.sensitivity import SensitivityAnalysisTab
from app.views.results.pillars.scenario_analysis import ScenarioAnalysisTab
from app.views.results.pillars.historical_backtest import HistoricalBacktestTab
from app.views.results.pillars.peer_multiples import PeerMultiples
from app.views.results.pillars.sotp_breakdown import SOTPBreakdownTab


@pytest.fixture
def base_result():
    """
    Constructs a minimal but complete ValuationResult with all extensions disabled.
    """
    company = Company(ticker="AAPL", name="Apple Inc.", current_price=150.0, currency="USD")

    request = ValuationRequest(
        mode=ValuationMethodology.FCFF_STANDARD,
        parameters=Parameters(
            structure=company,
            common=CommonParameters(
                rates=FinancialRatesParameters(
                    risk_free_rate=0.04,
                    market_risk_premium=0.05,
                    beta=1.2,
                    tax_rate=0.21,
                ),
            ),
            strategy=FCFFStandardParameters(projection_years=5, fcf_anchor=100_000.0),
            extensions=ExtensionBundleParameters(),
        ),
    )

    results = Results(
        common=CommonResults(
            rates=ResolvedRates(
                cost_of_equity=0.10,
                cost_of_debt_after_tax=0.04,
                wacc=0.08,
            ),
            capital=ResolvedCapital(
                market_cap=2_400_000.0,
                enterprise_value=2_500_000.0,
                net_debt_resolved=100_000.0,
                equity_value_total=2_400_000.0,
            ),
            intrinsic_value_per_share=160.0,
            upside_pct=0.067,
        ),
        strategy=FCFFStandardResults(
            projected_flows=[100_000.0, 105_000.0],
            discount_factors=[0.926, 0.857],
            terminal_value=2_000_000.0,
            discounted_terminal_value=1_500_000.0,
            tv_weight_pct=0.75,
        ),
        extensions=ExtensionBundleResults(),
    )

    return ValuationResult(request=request, results=results)


class TestMonteCarloPillarVisibility:
    """Tests Monte Carlo visibility logic."""

    def test_not_visible_when_disabled(self, base_result):
        """MC should not be visible when disabled."""
        assert not MonteCarloDistributionTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        """MC should be visible when enabled and results exist."""
        base_result.request.parameters.extensions.monte_carlo = MCParameters(enabled=True)
        base_result.results.extensions.monte_carlo = MCResults(
            simulation_values=[150.0, 160.0, 170.0],
            quantiles={"P10": 140.0, "P50": 155.0, "P90": 175.0},
            mean=160.0,
            std_dev=10.0,
        )
        assert MonteCarloDistributionTab.is_visible(base_result)

    def test_not_visible_when_enabled_but_no_results(self, base_result):
        """MC should not be visible when enabled but results are None."""
        base_result.request.parameters.extensions.monte_carlo = MCParameters(enabled=True)
        assert not MonteCarloDistributionTab.is_visible(base_result)


class TestSensitivityPillarVisibility:
    """Tests Sensitivity visibility logic."""

    def test_not_visible_when_disabled(self, base_result):
        """Sensitivity should not be visible when disabled."""
        assert not SensitivityAnalysisTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        """Sensitivity should be visible when enabled and results exist."""
        base_result.request.parameters.extensions.sensitivity = SensitivityParameters(enabled=True)
        base_result.results.extensions.sensitivity = SensitivityResults(
            x_axis_name="WACC",
            y_axis_name="Growth",
            x_values=[0.07, 0.08, 0.09],
            y_values=[0.02, 0.03, 0.04],
            values=[[100.0, 110.0, 120.0], [90.0, 100.0, 110.0], [80.0, 90.0, 100.0]],
            center_value=100.0,
            sensitivity_score=12.5,
        )
        assert SensitivityAnalysisTab.is_visible(base_result)


class TestScenarioPillarVisibility:
    """Tests Scenario visibility logic."""

    def test_not_visible_when_disabled(self, base_result):
        """Scenarios should not be visible when disabled."""
        assert not ScenarioAnalysisTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        """Scenarios should be visible when enabled and results exist."""
        base_result.request.parameters.extensions.scenarios = ScenariosParameters(enabled=True)
        base_result.results.extensions.scenarios = ScenariosResults(
            expected_intrinsic_value=155.0,
            outcomes=[
                ScenarioOutcome(label="Bear", intrinsic_value=130.0, upside_pct=-0.13, probability=0.25),
                ScenarioOutcome(label="Base", intrinsic_value=155.0, upside_pct=0.03, probability=0.50),
                ScenarioOutcome(label="Bull", intrinsic_value=180.0, upside_pct=0.20, probability=0.25),
            ],
        )
        assert ScenarioAnalysisTab.is_visible(base_result)


class TestBacktestPillarVisibility:
    """Tests Backtest visibility logic."""

    def test_not_visible_when_disabled(self, base_result):
        """Backtest should not be visible when disabled."""
        assert not HistoricalBacktestTab.is_visible(base_result)

    def test_not_visible_when_enabled_but_no_points(self, base_result):
        """Backtest should not be visible when enabled but no data points."""
        base_result.request.parameters.extensions.backtest = BacktestParameters(enabled=True)
        base_result.results.extensions.backtest = BacktestResults(
            points=[], mean_absolute_error=0.0, accuracy_score=0.0
        )
        assert not HistoricalBacktestTab.is_visible(base_result)

    def test_visible_when_enabled_with_points(self, base_result):
        """Backtest should be visible when enabled and has data points."""
        from datetime import date

        base_result.request.parameters.extensions.backtest = BacktestParameters(enabled=True)
        base_result.results.extensions.backtest = BacktestResults(
            points=[
                HistoricalPoint(
                    valuation_date=date(2023, 6, 30),
                    calculated_iv=155.0,
                    market_price=150.0,
                    error_pct=0.033,
                )
            ],
            mean_absolute_error=0.033,
            accuracy_score=90.0,
        )
        assert HistoricalBacktestTab.is_visible(base_result)


class TestPeersPillarVisibility:
    """Tests Peers visibility logic."""

    def test_not_visible_when_disabled(self, base_result):
        """Peers should not be visible when disabled."""
        assert not PeerMultiples.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        """Peers should be visible when enabled and results exist."""
        base_result.request.parameters.extensions.peers = PeersParameters(enabled=True)
        base_result.results.extensions.peers = PeersResults(
            median_multiples_used={"P/E": 25.0, "EV/EBITDA": 15.0},
            implied_prices={"P/E": 160.0, "EV/EBITDA": 155.0},
            final_relative_iv=157.5,
        )
        assert PeerMultiples.is_visible(base_result)


class TestSOTPPillarVisibility:
    """Tests SOTP visibility logic."""

    def test_not_visible_when_disabled(self, base_result):
        """SOTP should not be visible when disabled."""
        assert not SOTPBreakdownTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        """SOTP should be visible when enabled and results exist."""
        base_result.request.parameters.extensions.sotp = SOTPParameters(enabled=True)
        base_result.results.extensions.sotp = SOTPResults(
            total_enterprise_value=3_000_000.0,
            segment_values={"iPhone": 2_000_000.0, "Services": 1_000_000.0},
            implied_equity_value=2_800_000.0,
            equity_value_per_share=175.0,
        )
        assert SOTPBreakdownTab.is_visible(base_result)


class TestV2DataPaths:
    """Tests that V2 model paths are correct and accessible."""

    def test_result_request_parameters_path(self, base_result):
        """Verify the result.request.parameters path is accessible."""
        params = base_result.request.parameters
        assert params.structure.ticker == "AAPL"
        assert params.structure.currency == "USD"
        assert params.structure.current_price == 150.0

    def test_result_results_common_path(self, base_result):
        """Verify the result.results.common path is accessible."""
        common = base_result.results.common
        assert common.intrinsic_value_per_share == 160.0
        assert common.upside_pct == 0.067
        assert common.rates.wacc == 0.08

    def test_result_results_extensions_path(self, base_result):
        """Verify the result.results.extensions path is accessible."""
        ext = base_result.results.extensions
        assert ext.monte_carlo is None
        assert ext.sensitivity is None
        assert ext.scenarios is None
        assert ext.backtest is None
        assert ext.peers is None
        assert ext.sotp is None
