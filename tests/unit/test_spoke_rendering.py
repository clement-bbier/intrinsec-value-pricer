"""
tests/unit/test_spoke_rendering.py

SPOKE COMPONENT RENDERING TESTS
=================================
Role: Exercises all spoke-level pillar components using mocked st.
Coverage Target: >85% per file for all spoke pillar files.
"""

from datetime import date
from unittest.mock import MagicMock, patch, call
from typing import Any

import pytest

from src.models.benchmarks import CompanyStats, MarketContext, SectorMultiples, SectorPerformance
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
    HistoricalPoint,
    MCResults,
    PeersResults,
    ScenarioOutcome,
    ScenariosResults,
    SensitivityResults,
    SOTPResults,
)
from src.models.results.strategies import FCFFStandardResults
from src.models.valuation import ValuationRequest, ValuationResult


def _make_result(**ext_params_kw) -> ValuationResult:
    """Factory for a standard ValuationResult with configurable extensions."""
    company = Company(ticker="AAPL", name="Apple Inc.", current_price=150.0, currency="USD")
    request = ValuationRequest(
        mode=ValuationMethodology.FCFF_STANDARD,
        parameters=Parameters(
            structure=company,
            common=CommonParameters(
                rates=FinancialRatesParameters(
                    risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2, tax_rate=0.21,
                ),
            ),
            strategy=FCFFStandardParameters(projection_years=5, fcf_anchor=100_000.0),
            extensions=ExtensionBundleParameters(**ext_params_kw),
        ),
    )
    results = Results(
        common=CommonResults(
            rates=ResolvedRates(cost_of_equity=0.10, cost_of_debt_after_tax=0.04, wacc=0.08),
            capital=ResolvedCapital(
                market_cap=2_400_000.0, enterprise_value=2_500_000.0,
                net_debt_resolved=100_000.0, equity_value_total=2_400_000.0,
            ),
            intrinsic_value_per_share=160.0, upside_pct=0.067,
        ),
        strategy=FCFFStandardResults(
            projected_flows=[100_000.0], discount_factors=[0.926],
            terminal_value=2_000_000.0, discounted_terminal_value=1_500_000.0, tv_weight_pct=0.75,
        ),
        extensions=ExtensionBundleResults(),
    )
    return ValuationResult(request=request, results=results)


# =============================================================================
# MONTE CARLO DISTRIBUTION
# =============================================================================

class TestMonteCarloRendering:
    """Tests MonteCarloDistributionTab.render with mocked streamlit."""

    @patch("app.views.results.pillars.monte_carlo_distribution.display_simulation_chart")
    @patch("app.views.results.pillars.monte_carlo_distribution.st")
    def test_render_mc_full(self, mock_st, mock_chart):
        """Monte Carlo render must display risk hub and probability analysis."""
        from app.views.results.pillars.monte_carlo_distribution import MonteCarloDistributionTab

        result = _make_result(monte_carlo=MCParameters(enabled=True))
        result.results.extensions.monte_carlo = MCResults(
            simulation_values=[140.0, 150.0, 160.0, 170.0, 180.0],
            quantiles={"P5": 135.0, "P10": 140.0, "P50": 160.0, "P90": 180.0},
            mean=160.0, std_dev=15.0,
        )

        # Mock columns for the risk hub (4 columns)
        cols_4 = [MagicMock() for _ in range(4)]
        # Mock columns for probability analysis (2 columns)
        cols_2 = [MagicMock() for _ in range(2)]
        mock_st.columns.side_effect = [cols_4, cols_2]
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()

        MonteCarloDistributionTab.render(result)

        mock_st.markdown.assert_called()
        mock_chart.assert_called_once()

    @patch("app.views.results.pillars.monte_carlo_distribution.st")
    def test_render_mc_no_data_returns(self, mock_st):
        """Monte Carlo render with no data should return early."""
        from app.views.results.pillars.monte_carlo_distribution import MonteCarloDistributionTab

        result = _make_result(monte_carlo=MCParameters(enabled=True))
        result.results.extensions.monte_carlo = None

        MonteCarloDistributionTab.render(result)

        mock_st.markdown.assert_not_called()

    @patch("app.views.results.pillars.monte_carlo_distribution.display_simulation_chart")
    @patch("app.views.results.pillars.monte_carlo_distribution.st")
    def test_render_mc_with_null_shocks(self, mock_st, mock_chart):
        """Monte Carlo render should handle None shocks gracefully."""
        from app.views.results.pillars.monte_carlo_distribution import MonteCarloDistributionTab

        mc_params = MCParameters(enabled=True)
        mc_params.shocks = None
        result = _make_result(monte_carlo=mc_params)
        result.results.extensions.monte_carlo = MCResults(
            simulation_values=[150.0, 160.0],
            quantiles={"P5": 140.0, "P10": 145.0, "P50": 155.0, "P90": 170.0},
            mean=155.0, std_dev=10.0,
        )

        cols_4 = [MagicMock() for _ in range(4)]
        cols_2 = [MagicMock() for _ in range(2)]
        mock_st.columns.side_effect = [cols_4, cols_2]
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()

        MonteCarloDistributionTab.render(result)

        mock_st.caption.assert_called()


# =============================================================================
# SENSITIVITY ANALYSIS
# =============================================================================

class TestSensitivityRendering:
    """Tests SensitivityAnalysisTab.render with mocked streamlit."""

    @patch("app.views.results.pillars.sensitivity.atom_kpi_metric")
    @patch("app.views.results.pillars.sensitivity.st")
    def test_render_sensitivity_full(self, mock_st, mock_kpi):
        """Sensitivity render must display heatmap and score."""
        from app.views.results.pillars.sensitivity import SensitivityAnalysisTab

        result = _make_result(sensitivity=SensitivityParameters(enabled=True))
        result.results.extensions.sensitivity = SensitivityResults(
            x_axis_name="WACC", y_axis_name="Growth",
            x_values=[0.07, 0.08, 0.09],
            y_values=[0.02, 0.03, 0.04],
            values=[[100.0, 110.0, 120.0], [95.0, 105.0, 115.0], [90.0, 100.0, 110.0]],
            center_value=105.0, sensitivity_score=10.0,
        )

        col_kpi = MagicMock()
        col_chart = MagicMock()
        col_kpi.__enter__ = MagicMock(return_value=col_kpi)
        col_kpi.__exit__ = MagicMock(return_value=False)
        col_chart.__enter__ = MagicMock(return_value=col_chart)
        col_chart.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = [col_kpi, col_chart]

        SensitivityAnalysisTab.render(result)

        mock_kpi.assert_called_once()
        mock_st.altair_chart.assert_called_once()

    @patch("app.views.results.pillars.sensitivity.st")
    def test_render_sensitivity_no_data_returns(self, mock_st):
        """Sensitivity render with no data should return early."""
        from app.views.results.pillars.sensitivity import SensitivityAnalysisTab

        result = _make_result(sensitivity=SensitivityParameters(enabled=True))
        result.results.extensions.sensitivity = None

        SensitivityAnalysisTab.render(result)

        mock_st.markdown.assert_not_called()

    @patch("app.views.results.pillars.sensitivity.atom_kpi_metric")
    @patch("app.views.results.pillars.sensitivity.st")
    def test_render_sensitivity_volatile_score(self, mock_st, mock_kpi):
        """Sensitivity with score 20 should show volatile status."""
        from app.views.results.pillars.sensitivity import SensitivityAnalysisTab

        result = _make_result(sensitivity=SensitivityParameters(enabled=True))
        result.results.extensions.sensitivity = SensitivityResults(
            x_axis_name="WACC", y_axis_name="Growth",
            x_values=[0.08], y_values=[0.03],
            values=[[100.0]], center_value=100.0,
            sensitivity_score=20.0,  # Volatile
        )

        col_kpi = MagicMock()
        col_chart = MagicMock()
        col_kpi.__enter__ = MagicMock(return_value=col_kpi)
        col_kpi.__exit__ = MagicMock(return_value=False)
        col_chart.__enter__ = MagicMock(return_value=col_chart)
        col_chart.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = [col_kpi, col_chart]

        SensitivityAnalysisTab.render(result)

        # Should call with orange color for volatile
        call_kwargs = mock_kpi.call_args[1]
        assert call_kwargs["delta_color"] == "orange"

    @patch("app.views.results.pillars.sensitivity.atom_kpi_metric")
    @patch("app.views.results.pillars.sensitivity.st")
    def test_render_sensitivity_critical_score(self, mock_st, mock_kpi):
        """Sensitivity with score 35 should show critical status."""
        from app.views.results.pillars.sensitivity import SensitivityAnalysisTab

        result = _make_result(sensitivity=SensitivityParameters(enabled=True))
        result.results.extensions.sensitivity = SensitivityResults(
            x_axis_name="WACC", y_axis_name="Growth",
            x_values=[0.08], y_values=[0.03],
            values=[[100.0]], center_value=100.0,
            sensitivity_score=35.0,  # Critical
        )

        col_kpi = MagicMock()
        col_chart = MagicMock()
        col_kpi.__enter__ = MagicMock(return_value=col_kpi)
        col_kpi.__exit__ = MagicMock(return_value=False)
        col_chart.__enter__ = MagicMock(return_value=col_chart)
        col_chart.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = [col_kpi, col_chart]

        SensitivityAnalysisTab.render(result)

        call_kwargs = mock_kpi.call_args[1]
        assert call_kwargs["delta_color"] == "red"


# =============================================================================
# SCENARIO ANALYSIS
# =============================================================================

class TestScenarioRendering:
    """Tests ScenarioAnalysisTab.render with mocked streamlit."""

    @patch("app.views.results.pillars.scenario_analysis.st")
    def test_render_scenario_full(self, mock_st):
        """Scenario render must display outcomes and chart."""
        from app.views.results.pillars.scenario_analysis import ScenarioAnalysisTab

        result = _make_result(scenarios=ScenariosParameters(enabled=True))
        result.results.extensions.scenarios = ScenariosResults(
            expected_intrinsic_value=155.0,
            outcomes=[
                ScenarioOutcome(label="Bear", intrinsic_value=130.0, upside_pct=-0.13, probability=0.25),
                ScenarioOutcome(label="Base", intrinsic_value=155.0, upside_pct=0.03, probability=0.50),
                ScenarioOutcome(label="Bull", intrinsic_value=180.0, upside_pct=0.20, probability=0.25),
            ],
        )

        def make_cols(spec):
            n = len(spec) if isinstance(spec, list) else spec
            cols = [MagicMock() for _ in range(n)]
            for col in cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            return cols

        mock_st.columns.side_effect = make_cols
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()

        ScenarioAnalysisTab.render(result)

        mock_st.markdown.assert_called()

    @patch("app.views.results.pillars.scenario_analysis.st")
    def test_render_scenario_no_data_returns(self, mock_st):
        """Scenario render with no data should return early."""
        from app.views.results.pillars.scenario_analysis import ScenarioAnalysisTab

        result = _make_result(scenarios=ScenariosParameters(enabled=True))
        result.results.extensions.scenarios = None

        ScenarioAnalysisTab.render(result)

        mock_st.markdown.assert_not_called()


# =============================================================================
# HISTORICAL BACKTEST
# =============================================================================

class TestBacktestRendering:
    """Tests HistoricalBacktestTab.render with mocked streamlit."""

    @patch("app.views.results.pillars.historical_backtest.display_backtest_convergence_chart")
    @patch("app.views.results.pillars.historical_backtest.st")
    def test_render_backtest_full(self, mock_st, mock_chart):
        """Backtest render must display accuracy KPIs and convergence chart."""
        from app.views.results.pillars.historical_backtest import HistoricalBacktestTab

        result = _make_result(backtest=BacktestParameters(enabled=True))
        result.results.extensions.backtest = BacktestResults(
            points=[
                HistoricalPoint(
                    valuation_date=date(2023, 6, 30),
                    calculated_iv=155.0, market_price=150.0, error_pct=0.033,
                ),
                HistoricalPoint(
                    valuation_date=date(2023, 9, 30),
                    calculated_iv=160.0, market_price=155.0, error_pct=0.032,
                ),
            ],
            mean_absolute_error=0.033,
            accuracy_score=90.0,
        )

        def make_cols(spec):
            n = len(spec) if isinstance(spec, list) else spec
            cols = [MagicMock() for _ in range(n)]
            for col in cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            return cols

        mock_st.columns.side_effect = make_cols
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()

        HistoricalBacktestTab.render(result)

        mock_st.markdown.assert_called()
        mock_chart.assert_called_once()

    @patch("app.views.results.pillars.historical_backtest.st")
    def test_render_backtest_no_data_returns(self, mock_st):
        """Backtest render with no data should return early."""
        from app.views.results.pillars.historical_backtest import HistoricalBacktestTab

        result = _make_result(backtest=BacktestParameters(enabled=True))
        result.results.extensions.backtest = None

        HistoricalBacktestTab.render(result)

        mock_st.markdown.assert_not_called()


# =============================================================================
# PEER MULTIPLES
# =============================================================================

class TestPeerMultiplesRendering:
    """Tests PeerMultiples.render with mocked streamlit."""

    @patch("app.views.results.pillars.peer_multiples.st")
    def test_render_peers_full(self, mock_st):
        """Peer multiples render must display football field and tables."""
        from app.views.results.pillars.peer_multiples import PeerMultiples

        result = _make_result(peers=PeersParameters(enabled=True))
        result.results.extensions.peers = PeersResults(
            median_multiples_used={"P/E": 25.0, "EV/EBITDA": 15.0},
            implied_prices={"P/E": 160.0, "EV/EBITDA": 155.0},
            final_relative_iv=157.5,
        )

        def make_cols(spec):
            n = len(spec) if isinstance(spec, list) else spec
            cols = [MagicMock() for _ in range(n)]
            for col in cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            return cols

        mock_st.columns.side_effect = make_cols
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()

        PeerMultiples.render(result)

        mock_st.markdown.assert_called()

    @patch("app.views.results.pillars.peer_multiples.st")
    def test_render_peers_no_data_returns(self, mock_st):
        """Peer multiples render with no data should return early."""
        from app.views.results.pillars.peer_multiples import PeerMultiples

        result = _make_result(peers=PeersParameters(enabled=True))
        result.results.extensions.peers = None

        PeerMultiples.render(result)

        mock_st.markdown.assert_not_called()


# =============================================================================
# SOTP BREAKDOWN
# =============================================================================

class TestSOTPRendering:
    """Tests SOTPBreakdownTab.render with mocked streamlit."""

    @patch("app.views.results.pillars.sotp_breakdown.st")
    def test_render_sotp_full(self, mock_st):
        """SOTP render must display waterfall and contribution table."""
        from app.views.results.pillars.sotp_breakdown import SOTPBreakdownTab

        result = _make_result(sotp=SOTPParameters(enabled=True))
        result.results.extensions.sotp = SOTPResults(
            total_enterprise_value=3_000_000.0,
            segment_values={"iPhone": 2_000_000.0, "Services": 1_000_000.0},
            implied_equity_value=2_800_000.0,
            equity_value_per_share=175.0,
        )

        def make_cols(spec):
            n = len(spec) if isinstance(spec, list) else spec
            cols = [MagicMock() for _ in range(n)]
            for col in cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            return cols

        mock_st.columns.side_effect = make_cols
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()

        SOTPBreakdownTab.render(result)

        mock_st.markdown.assert_called()

    @patch("app.views.results.pillars.sotp_breakdown.st")
    def test_render_sotp_no_data_returns(self, mock_st):
        """SOTP render with no data should return early."""
        from app.views.results.pillars.sotp_breakdown import SOTPBreakdownTab

        result = _make_result(sotp=SOTPParameters(enabled=True))
        result.results.extensions.sotp = None

        SOTPBreakdownTab.render(result)

        mock_st.markdown.assert_not_called()
