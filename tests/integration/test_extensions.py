"""
tests/integration/test_extensions.py

EXTENSIONS SUITE INTEGRATION TEST
=================================
Role: Stress-test all 6 auxiliary engines (Risk, Market, History).
Scope: Orchestrator -> Extensions -> Results.
"""

import pytest

from src.models.parameters.options import BusinessUnit, ScenarioParameters
from src.valuation.orchestrator import ValuationOrchestrator


class TestExtensionsSuite:
    @pytest.fixture
    def orchestrator(self):
        return ValuationOrchestrator()

    def test_1_monte_carlo_execution(self, orchestrator, fcff_request_standard, mock_apple_snapshot):
        """Test: Monte Carlo simulation (Stochastic)."""
        req = fcff_request_standard.model_copy(deep=True)
        req.parameters.extensions.monte_carlo.enabled = True
        req.parameters.extensions.monte_carlo.iterations = 100

        result = orchestrator.run(req, mock_apple_snapshot)

        mc_res = result.results.extensions.monte_carlo
        assert mc_res is not None
        assert len(mc_res.simulation_values) == 100
        assert mc_res.quantiles["P50"] > 0
        print(f"\n[MC] P50: {mc_res.quantiles['P50']:.2f}")

    def test_2_sensitivity_heatmap(self, orchestrator, fcff_request_standard, mock_apple_snapshot):
        """Test: Sensitivity Analysis (2D Matrix)."""
        req = fcff_request_standard.model_copy(deep=True)
        req.parameters.extensions.sensitivity.enabled = True

        result = orchestrator.run(req, mock_apple_snapshot)

        sensi_res = result.results.extensions.sensitivity
        assert sensi_res is not None
        assert len(sensi_res.x_values) > 0
        assert len(sensi_res.y_values) > 0
        assert len(sensi_res.values) == len(sensi_res.y_values)

    def test_3_scenarios_analysis(self, orchestrator, fcff_request_standard, mock_apple_snapshot):
        """Test: Scenarios (Bull/Bear/Base)."""
        req = fcff_request_standard.model_copy(deep=True)
        req.parameters.extensions.scenarios.enabled = True

        req.parameters.extensions.scenarios.cases = [
            ScenarioParameters(name="Bear Case", probability=0.25, growth_override=0.01),
            ScenarioParameters(name="Base Case", probability=0.50, growth_override=0.05),
            ScenarioParameters(name="Bull Case", probability=0.25, growth_override=0.08),
        ]

        result = orchestrator.run(req, mock_apple_snapshot)

        scen_res = result.results.extensions.scenarios
        assert scen_res is not None
        assert len(scen_res.outcomes) >= 3

        labels = [o.label for o in scen_res.outcomes]
        assert "Base Case" in labels

    def test_4_sotp_breakdown(self, orchestrator, fcff_request_standard, mock_apple_snapshot):
        """Test: Sum of the Parts (SOTP)."""
        req = fcff_request_standard.model_copy(deep=True)
        req.parameters.extensions.sotp.enabled = True

        req.parameters.extensions.sotp.segments = [
            BusinessUnit(name="Hardware", value=1500000.0),
            BusinessUnit(name="Services", value=500000.0),
        ]

        result = orchestrator.run(req, mock_apple_snapshot)

        sotp_res = result.results.extensions.sotp
        assert sotp_res is not None

        assert sotp_res.total_enterprise_value == 2000000.0

    def test_5_peers_multiples(self, orchestrator, fcff_request_standard, mock_apple_snapshot):
        """Test: Peers Analysis."""
        req = fcff_request_standard.model_copy(deep=True)
        req.parameters.extensions.peers.enabled = True

        try:
            orchestrator.run(req, mock_apple_snapshot)
        except Exception as e:
            pytest.fail(f"Peers module caused a crash: {str(e)}")

    def test_6_backtest_historical(self, orchestrator, fcff_request_standard, mock_apple_snapshot):
        """Test: Historical Backtest."""
        req = fcff_request_standard.model_copy(deep=True)
        req.parameters.extensions.backtest.enabled = True

        try:
            orchestrator.run(req, mock_apple_snapshot)
        except Exception as e:
            pytest.fail(f"Backtest module caused a crash: {str(e)}")

    def test_7_full_stress_test(self, orchestrator, fcff_request_standard, mock_apple_snapshot):
        """STRESS TEST: Enable ALL extensions simultaneously."""
        req = fcff_request_standard.model_copy(deep=True)

        req.parameters.extensions.monte_carlo.enabled = True
        req.parameters.extensions.monte_carlo.iterations = 50
        req.parameters.extensions.sensitivity.enabled = True
        req.parameters.extensions.scenarios.enabled = True
        req.parameters.extensions.sotp.enabled = True

        req.parameters.extensions.scenarios.cases = [
            ScenarioParameters(name="Stress Bear", probability=1.0, growth_override=0.0)
        ]
        req.parameters.extensions.sotp.segments = [BusinessUnit(name="Stress Unit", value=100.0)]

        print("\n[Stress Test] Launching comprehensive valuation...")
        result = orchestrator.run(req, mock_apple_snapshot)

        assert result.results.extensions.monte_carlo is not None
        assert result.results.extensions.sensitivity is not None
        assert result.results.extensions.scenarios is not None
        assert result.results.extensions.sotp is not None

        print(f"[Stress Test] Success. IV: {result.results.common.intrinsic_value_per_share:.2f}")
