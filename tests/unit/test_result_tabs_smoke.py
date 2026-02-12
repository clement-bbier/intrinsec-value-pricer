"""
tests/unit/test_result_tabs_smoke.py

Smoke tests for result tab rendering (Phase 4).

Validates:
- Each tab's is_visible() method works correctly
- No import errors in tab modules
- Tab ordering is consistent
"""

import pytest
from unittest.mock import patch, MagicMock

from src.domain.models import (
    CompanyFinancials,
    DCFParameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    SOTPParameters,
    ScenarioParameters,
    ValuationMode,
    InputSource,
    ValuationRequest,
    DCFValuationResult,
    BacktestResult,
    MultiplesData,
    MultiplesValuationResult,
)
from src.domain.models.scenarios import ScenarioSynthesis, ScenarioResult


@pytest.fixture
def sample_financials():
    """Minimal financials for tab testing."""
    return CompanyFinancials(
        ticker="TEST",
        currency="USD",
        current_price=100.0,
        shares_outstanding=1_000_000,
    )


@pytest.fixture
def sample_params():
    """Minimal params for tab testing."""
    return DCFParameters(
        rates=CoreRateParameters(risk_free_rate=0.04, market_risk_premium=0.05),
        growth=GrowthParameters(fcf_growth_rate=0.05, perpetual_growth_rate=0.02, projection_years=5),
        monte_carlo=MonteCarloConfig(enable_monte_carlo=False),
        sotp=SOTPParameters(enabled=False),
        scenarios=ScenarioParameters(enabled=False),
    )


@pytest.fixture
def base_result(sample_financials, sample_params):
    """Basic DCF result for testing tab visibility."""
    request = ValuationRequest(
        ticker="TEST",
        projection_years=5,
        mode=ValuationMode.FCFF_STANDARD,
        input_source=InputSource.AUTO,
        manual_params=sample_params,
    )
    return DCFValuationResult(
        request=request,
        financials=sample_financials,
        params=sample_params,
        intrinsic_value_per_share=120.0,
        market_price=100.0,
        wacc=0.10,
        projected_fcfs=[10.0, 10.5, 11.0, 11.5, 12.0],
        enterprise_value=150_000_000.0,
        equity_value=130_000_000.0,
    )


class TestTabImports:
    """Verify all tab modules can be imported without errors."""

    def test_import_executive_summary(self):
        from app.ui.results.core.executive_summary import ExecutiveSummaryTab
        assert ExecutiveSummaryTab is not None

    def test_import_inputs_summary(self):
        from app.ui.results.core.inputs_summary import InputsSummaryTab
        assert InputsSummaryTab is not None

    def test_import_calculation_proof(self):
        from app.ui.results.core.calculation_proof import CalculationProofTab
        assert CalculationProofTab is not None

    def test_import_audit_report(self):
        from app.ui.results.core.audit_report import AuditReportTab
        assert AuditReportTab is not None

    def test_import_peer_multiples(self):
        from app.ui.results.optional.peer_multiples import PeerMultiplesTab
        assert PeerMultiplesTab is not None

    def test_import_sotp_breakdown(self):
        from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab
        assert SOTPBreakdownTab is not None

    def test_import_scenario_analysis(self):
        from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
        assert ScenarioAnalysisTab is not None

    def test_import_historical_backtest(self):
        from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
        assert HistoricalBacktestTab is not None

    def test_import_monte_carlo(self):
        from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab
        assert MonteCarloDistributionTab is not None


class TestTabVisibility:
    """Test is_visible() logic for each tab."""

    def test_core_tabs_always_visible(self, base_result):
        """Core tabs should always be visible for a valid result."""
        from app.ui.results.core.executive_summary import ExecutiveSummaryTab
        from app.ui.results.core.inputs_summary import InputsSummaryTab
        from app.ui.results.core.calculation_proof import CalculationProofTab

        assert ExecutiveSummaryTab().is_visible(base_result) is True
        assert InputsSummaryTab().is_visible(base_result) is True
        assert CalculationProofTab().is_visible(base_result) is True

    def test_monte_carlo_not_visible_without_simulations(self, base_result):
        """MC tab should not be visible when no simulations exist."""
        from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab

        assert base_result.simulation_results is None
        assert MonteCarloDistributionTab().is_visible(base_result) is False

    def test_monte_carlo_visible_with_simulations(self, base_result):
        """MC tab should be visible when simulations exist."""
        from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab

        base_result.simulation_results = [100.0, 110.0, 120.0, 90.0, 105.0]
        assert MonteCarloDistributionTab().is_visible(base_result) is True

    def test_scenario_not_visible_without_synthesis(self, base_result):
        """Scenario tab should not be visible when no synthesis exists."""
        from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab

        assert base_result.scenario_synthesis is None
        assert ScenarioAnalysisTab().is_visible(base_result) is False

    def test_scenario_visible_with_synthesis(self, base_result):
        """Scenario tab should be visible when synthesis with variants exists."""
        from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab

        base_result.scenario_synthesis = ScenarioSynthesis(
            variants=[
                ScenarioResult(label="Bull", intrinsic_value=150.0, probability=0.25, growth_used=0.08, margin_used=0.0),
                ScenarioResult(label="Base", intrinsic_value=120.0, probability=0.50, growth_used=0.05, margin_used=0.0),
                ScenarioResult(label="Bear", intrinsic_value=90.0, probability=0.25, growth_used=0.02, margin_used=0.0),
            ],
            expected_value=120.0,
            max_upside=150.0,
            max_downside=90.0,
        )
        assert ScenarioAnalysisTab().is_visible(base_result) is True

    def test_backtest_not_visible_without_report(self, base_result):
        """Backtest tab should not be visible when no backtest report exists."""
        from app.ui.results.optional.historical_backtest import HistoricalBacktestTab

        assert base_result.backtest_report is None
        assert HistoricalBacktestTab().is_visible(base_result) is False

    def test_peer_multiples_not_visible_without_triangulation(self, base_result):
        """Peer multiples tab should not be visible without triangulation data."""
        from app.ui.results.optional.peer_multiples import PeerMultiplesTab

        assert base_result.multiples_triangulation is None
        assert PeerMultiplesTab().is_visible(base_result) is False

    def test_sotp_not_visible_without_results(self, base_result):
        """SOTP tab should not be visible without SOTP results."""
        from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab

        assert base_result.sotp_results is None
        assert SOTPBreakdownTab().is_visible(base_result) is False


class TestTabOrdering:
    """Test tab ordering consistency."""

    def test_tab_order_values(self):
        """All tabs should have positive ORDER values."""
        from app.ui.results.core.executive_summary import ExecutiveSummaryTab
        from app.ui.results.core.inputs_summary import InputsSummaryTab
        from app.ui.results.core.calculation_proof import CalculationProofTab
        from app.ui.results.core.audit_report import AuditReportTab
        from app.ui.results.optional.peer_multiples import PeerMultiplesTab
        from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab
        from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
        from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
        from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab

        tabs = [
            ExecutiveSummaryTab(),
            InputsSummaryTab(),
            CalculationProofTab(),
            AuditReportTab(),
            PeerMultiplesTab(),
            SOTPBreakdownTab(),
            ScenarioAnalysisTab(),
            HistoricalBacktestTab(),
            MonteCarloDistributionTab(),
        ]

        orders = [t.ORDER for t in tabs]
        assert all(o > 0 for o in orders), "Tab ORDER values must be positive"
        assert len(tabs) == 9, "All 9 tabs should be present"

    def test_core_tabs_ordered_before_optional(self):
        """Core tabs should have lower ORDER values than optional tabs."""
        from app.ui.results.core.executive_summary import ExecutiveSummaryTab
        from app.ui.results.core.audit_report import AuditReportTab
        from app.ui.results.optional.peer_multiples import PeerMultiplesTab

        assert ExecutiveSummaryTab.ORDER < PeerMultiplesTab.ORDER
        assert AuditReportTab.ORDER < PeerMultiplesTab.ORDER


class TestOrchestratorConstruction:
    """Test ResultTabOrchestrator construction."""

    def test_orchestrator_creates_all_tabs(self):
        """Orchestrator should instantiate all 9 tabs."""
        from app.ui.results.orchestrator import ResultTabOrchestrator

        orch = ResultTabOrchestrator()
        assert len(orch._tabs) == 9

    def test_orchestrator_visible_count(self, base_result):
        """Orchestrator should count visible tabs correctly for a basic result."""
        from app.ui.results.orchestrator import ResultTabOrchestrator

        orch = ResultTabOrchestrator()
        # Base result has no MC, no scenarios, no backtest, no peers, no SOTP
        # Only core tabs (executive, inputs, calculation, audit) are visible
        visible = orch.get_visible_count(base_result)
        assert visible == 4, f"Expected 4 core tabs visible, got {visible}"
