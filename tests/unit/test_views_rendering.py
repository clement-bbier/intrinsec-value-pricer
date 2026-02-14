"""
tests/unit/test_views_rendering.py

VIEW RENDERING TESTS (MOCK-BASED)
===================================
Role: Exercises all Streamlit-dependent view functions using mock st objects.
Coverage Target: >85% per file for all app/views/ files.
"""

from unittest.mock import MagicMock, patch

from src.models.benchmarks import (
    CompanyStats,
    MarketContext,
    SectorMultiples,
    SectorPerformance,
)
from src.models.company import Company
from src.models.enums import ValuationMethodology
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CapitalStructureParameters, CommonParameters, FinancialRatesParameters
from src.models.parameters.options import (
    ExtensionBundleParameters,
    MCParameters,
    SOTPParameters,
)
from src.models.parameters.strategies import (
    FCFFStandardParameters,
    GrahamParameters,
    RIMParameters,
)
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import (
    ExtensionBundleResults,
)
from src.models.results.strategies import FCFFStandardResults
from src.models.valuation import ValuationRequest, ValuationResult


def _make_base_result(**ext_overrides) -> ValuationResult:
    """Factory to create a standard ValuationResult."""
    company = Company(
        ticker="AAPL",
        name="Apple Inc.",
        current_price=150.0,
        currency="USD",
    )
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
                capital=CapitalStructureParameters(
                    shares_outstanding=16_000.0,
                    total_debt=120_000.0,
                    cash_and_equivalents=50_000.0,
                ),
            ),
            strategy=FCFFStandardParameters(projection_years=5, fcf_anchor=100_000.0),
            extensions=ExtensionBundleParameters(**ext_overrides),
        ),
    )
    results = Results(
        common=CommonResults(
            rates=ResolvedRates(cost_of_equity=0.10, cost_of_debt_after_tax=0.04, wacc=0.08),
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


# =============================================================================
# ORCHESTRATOR (render_valuation_results)
# =============================================================================


class TestOrchestratorRendering:
    """Tests render_valuation_results with mocked streamlit."""

    @patch("app.views.results.orchestrator.st")
    @patch("app.views.results.orchestrator.inputs_summary")
    @patch("app.views.results.orchestrator.calculation_proof")
    @patch("app.views.results.orchestrator.benchmark_report")
    @patch("app.views.results.orchestrator.risk_engineering")
    @patch("app.views.results.orchestrator.market_analysis")
    def test_renders_header_and_tabs(self, mock_market, mock_risk, mock_bench, mock_calc, mock_inputs, mock_st):
        """Orchestrator must render permanent header and create tabs."""
        from app.views.results.orchestrator import render_valuation_results

        col_mocks = [MagicMock(), MagicMock(), MagicMock()]
        for col in col_mocks:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = col_mocks

        tab_mocks = [MagicMock() for _ in range(3)]
        for tab in tab_mocks:
            tab.__enter__ = MagicMock(return_value=tab)
            tab.__exit__ = MagicMock(return_value=False)
        mock_st.tabs.return_value = tab_mocks

        result = _make_base_result()
        render_valuation_results(result)

        mock_st.divider.assert_called()
        mock_st.tabs.assert_called_once()

    @patch("app.views.results.orchestrator.st")
    @patch("app.views.results.orchestrator.atom_kpi_metric")
    def test_permanent_header_renders_kpis(self, mock_kpi, mock_st):
        """Permanent header must render 3 KPI cards."""
        from app.views.results.orchestrator import _render_permanent_header

        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        result = _make_base_result()
        _render_permanent_header(result)

        assert mock_kpi.call_count == 3

    @patch("app.views.results.orchestrator.st")
    @patch("app.views.results.orchestrator.inputs_summary")
    @patch("app.views.results.orchestrator.calculation_proof")
    @patch("app.views.results.orchestrator.benchmark_report")
    @patch("app.views.results.orchestrator.risk_engineering")
    @patch("app.views.results.orchestrator.market_analysis")
    def test_risk_tab_shown_when_mc_enabled(self, mock_market, mock_risk, mock_bench, mock_calc, mock_inputs, mock_st):
        """When Monte Carlo is enabled, Risk tab should appear."""
        from app.views.results.orchestrator import render_valuation_results

        result = _make_base_result(monte_carlo=MCParameters(enabled=True))

        col_mocks = [MagicMock(), MagicMock(), MagicMock()]
        for col in col_mocks:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = col_mocks

        # 4 tabs: Inputs, Proof, Benchmark, Risk
        tab_mocks = [MagicMock() for _ in range(4)]
        for tab in tab_mocks:
            tab.__enter__ = MagicMock(return_value=tab)
            tab.__exit__ = MagicMock(return_value=False)
        mock_st.tabs.return_value = tab_mocks

        render_valuation_results(result)
        tab_labels = mock_st.tabs.call_args[0][0]
        assert len(tab_labels) == 4

    @patch("app.views.results.orchestrator.st")
    @patch("app.views.results.orchestrator.inputs_summary")
    @patch("app.views.results.orchestrator.calculation_proof")
    @patch("app.views.results.orchestrator.benchmark_report")
    @patch("app.views.results.orchestrator.risk_engineering")
    @patch("app.views.results.orchestrator.market_analysis")
    def test_market_tab_shown_when_sotp_enabled(
        self, mock_market, mock_risk, mock_bench, mock_calc, mock_inputs, mock_st
    ):
        """When SOTP is enabled, Market tab should appear."""
        from app.views.results.orchestrator import render_valuation_results

        result = _make_base_result(sotp=SOTPParameters(enabled=True))

        col_mocks = [MagicMock(), MagicMock(), MagicMock()]
        for col in col_mocks:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = col_mocks

        tab_mocks = [MagicMock() for _ in range(4)]
        for tab in tab_mocks:
            tab.__enter__ = MagicMock(return_value=tab)
            tab.__exit__ = MagicMock(return_value=False)
        mock_st.tabs.return_value = tab_mocks

        render_valuation_results(result)
        tab_labels = mock_st.tabs.call_args[0][0]
        assert len(tab_labels) == 4


# =============================================================================
# INPUTS SUMMARY (Pillar 1)
# =============================================================================


class TestInputsSummaryRendering:
    """Tests render_detailed_inputs with mocked streamlit."""

    @patch("app.views.results.pillars.inputs_summary.st")
    def test_render_detailed_inputs_calls_st(self, mock_st):
        """render_detailed_inputs must call st.caption and st.divider."""
        from app.views.results.pillars.inputs_summary import render_detailed_inputs

        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value.__enter__ = MagicMock()
        mock_st.expander.return_value.__exit__ = MagicMock()

        result = _make_base_result()
        render_detailed_inputs(result)

        mock_st.caption.assert_called()
        mock_st.divider.assert_called()

    @patch("app.views.results.pillars.inputs_summary.st")
    def test_capital_structure_table_renders(self, mock_st):
        """_render_capital_structure_table must call st.table."""
        from app.views.results.pillars.inputs_summary import _render_capital_structure_table

        result = _make_base_result()
        _render_capital_structure_table(result.request.parameters)

        mock_st.table.assert_called_once()

    @patch("app.views.results.pillars.inputs_summary.st")
    def test_rates_table_renders(self, mock_st):
        """_render_rates_table must call st.table."""
        from app.views.results.pillars.inputs_summary import _render_rates_table

        result = _make_base_result()
        _render_rates_table(result.request.parameters, result.results.common.rates)

        mock_st.table.assert_called_once()

    @patch("app.views.results.pillars.inputs_summary.st")
    def test_strategy_inputs_table_dcf(self, mock_st):
        """_render_strategy_inputs_table for DCF must call st.table."""
        from app.views.results.pillars.inputs_summary import _render_strategy_inputs_table

        result = _make_base_result()
        _render_strategy_inputs_table(result)

        mock_st.table.assert_called_once()

    @patch("app.views.results.pillars.inputs_summary.st")
    def test_strategy_inputs_table_graham(self, mock_st):
        """_render_strategy_inputs_table for Graham must call st.table."""
        from app.views.results.pillars.inputs_summary import _render_strategy_inputs_table

        result = _make_base_result()
        result.request.mode = ValuationMethodology.GRAHAM
        result.request.parameters.strategy = GrahamParameters(eps_normalized=6.50, growth_estimate=0.05)
        _render_strategy_inputs_table(result)

        mock_st.table.assert_called_once()

    @patch("app.views.results.pillars.inputs_summary.st")
    def test_strategy_inputs_table_rim(self, mock_st):
        """_render_strategy_inputs_table for RIM must call st.table."""
        from app.views.results.pillars.inputs_summary import _render_strategy_inputs_table

        result = _make_base_result()
        result.request.mode = ValuationMethodology.RIM
        result.request.parameters.strategy = RIMParameters(book_value_anchor=500.0, persistence_factor=0.6)
        _render_strategy_inputs_table(result)

        mock_st.table.assert_called_once()


# =============================================================================
# BENCHMARK REPORT (Pillar 3)
# =============================================================================


class TestBenchmarkReportRendering:
    """Tests render_benchmark_view with mocked streamlit."""

    @patch("app.views.results.pillars.benchmark_report.st")
    def test_no_market_context_shows_info(self, mock_st):
        """When market_context is None, st.info must be called."""
        from app.views.results.pillars.benchmark_report import render_benchmark_view

        result = _make_base_result()
        result.market_context = None
        render_benchmark_view(result)

        mock_st.info.assert_called()

    @patch("app.views.results.pillars.benchmark_report.display_sector_comparison_chart")
    @patch("app.views.results.pillars.benchmark_report.atom_benchmark_card")
    @patch("app.views.results.pillars.benchmark_report.st")
    def test_full_benchmark_renders(self, mock_st, mock_card, mock_chart):
        """Full benchmark with market_context and company_stats must render."""
        from app.views.results.pillars.benchmark_report import render_benchmark_view

        result = _make_base_result()
        result.market_context = MarketContext(
            reference_ticker="^GSPC",
            sector_name="Technology",
            multiples=SectorMultiples(pe_ratio=25.0, ev_ebitda=15.0, ev_revenue=5.0, pb_ratio=8.0),
            performance=SectorPerformance(fcf_margin=0.20, revenue_growth=0.08, roe=0.30),
            risk_free_rate=0.04,
            equity_risk_premium=0.05,
        )
        result.company_stats = CompanyStats(
            pe_ratio=28.0,
            ev_ebitda=18.0,
            pb_ratio=10.0,
            fcf_margin=0.25,
            roe=0.35,
            revenue_growth=0.10,
            piotroski_score=7,
        )

        # st.columns is called with different numbers throughout the function
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

        render_benchmark_view(result)

        mock_st.header.assert_called()
        mock_card.assert_called()

    @patch("app.views.results.pillars.benchmark_report.st")
    def test_piotroski_section_strong(self, mock_st):
        """Piotroski section with strong score should call st.success."""
        from app.views.results.pillars.benchmark_report import _render_piotroski_section

        stats = CompanyStats(piotroski_score=8)
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        _render_piotroski_section(stats)

        mock_st.success.assert_called()

    @patch("app.views.results.pillars.benchmark_report.st")
    def test_piotroski_section_stable(self, mock_st):
        """Piotroski section with stable score should call st.warning."""
        from app.views.results.pillars.benchmark_report import _render_piotroski_section

        stats = CompanyStats(piotroski_score=5)
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        _render_piotroski_section(stats)

        mock_st.warning.assert_called()

    @patch("app.views.results.pillars.benchmark_report.st")
    def test_piotroski_section_weak(self, mock_st):
        """Piotroski section with weak score should call st.error."""
        from app.views.results.pillars.benchmark_report import _render_piotroski_section

        stats = CompanyStats(piotroski_score=2)
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        _render_piotroski_section(stats)

        mock_st.error.assert_called()


# =============================================================================
# RISK ENGINEERING (Pillar 4)
# =============================================================================


class TestRiskEngineeringRendering:
    """Tests render_risk_analysis with mocked streamlit."""

    @patch("app.views.results.pillars.risk_engineering.HistoricalBacktestTab")
    @patch("app.views.results.pillars.risk_engineering.ScenarioAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.SensitivityAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.MonteCarloDistributionTab")
    @patch("app.views.results.pillars.risk_engineering.st")
    def test_renders_header_always(self, mock_st, mock_mc, mock_sensi, mock_scenario, mock_bt):
        """Risk engineering must always render the pillar header."""
        from app.views.results.pillars.risk_engineering import render_risk_analysis

        mock_mc.is_visible.return_value = False
        mock_sensi.is_visible.return_value = False
        mock_scenario.is_visible.return_value = False
        mock_bt.is_visible.return_value = False

        result = _make_base_result()
        render_risk_analysis(result)

        mock_st.header.assert_called()
        mock_st.divider.assert_called()

    @patch("app.views.results.pillars.risk_engineering.HistoricalBacktestTab")
    @patch("app.views.results.pillars.risk_engineering.ScenarioAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.SensitivityAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.MonteCarloDistributionTab")
    @patch("app.views.results.pillars.risk_engineering.st")
    def test_mc_rendered_when_visible(self, mock_st, mock_mc, mock_sensi, mock_scenario, mock_bt):
        """Monte Carlo render should be called when visible."""
        from app.views.results.pillars.risk_engineering import render_risk_analysis

        mock_mc.is_visible.return_value = True
        mock_sensi.is_visible.return_value = False
        mock_scenario.is_visible.return_value = False
        mock_bt.is_visible.return_value = False

        result = _make_base_result()
        render_risk_analysis(result)

        mock_mc.render.assert_called_once()

    @patch("app.views.results.pillars.risk_engineering.HistoricalBacktestTab")
    @patch("app.views.results.pillars.risk_engineering.ScenarioAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.SensitivityAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.MonteCarloDistributionTab")
    @patch("app.views.results.pillars.risk_engineering.st")
    def test_sensitivity_rendered_when_visible(self, mock_st, mock_mc, mock_sensi, mock_scenario, mock_bt):
        """Sensitivity render should be called when visible."""
        from app.views.results.pillars.risk_engineering import render_risk_analysis

        mock_mc.is_visible.return_value = False
        mock_sensi.is_visible.return_value = True
        mock_scenario.is_visible.return_value = False
        mock_bt.is_visible.return_value = False

        result = _make_base_result()
        render_risk_analysis(result)

        mock_sensi.render.assert_called_once()

    @patch("app.views.results.pillars.risk_engineering.HistoricalBacktestTab")
    @patch("app.views.results.pillars.risk_engineering.ScenarioAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.SensitivityAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.MonteCarloDistributionTab")
    @patch("app.views.results.pillars.risk_engineering.st")
    def test_scenario_rendered_when_visible(self, mock_st, mock_mc, mock_sensi, mock_scenario, mock_bt):
        """Scenario render should be called when visible."""
        from app.views.results.pillars.risk_engineering import render_risk_analysis

        mock_mc.is_visible.return_value = False
        mock_sensi.is_visible.return_value = False
        mock_scenario.is_visible.return_value = True
        mock_bt.is_visible.return_value = False

        result = _make_base_result()
        render_risk_analysis(result)

        mock_scenario.render.assert_called_once()

    @patch("app.views.results.pillars.risk_engineering.HistoricalBacktestTab")
    @patch("app.views.results.pillars.risk_engineering.ScenarioAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.SensitivityAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.MonteCarloDistributionTab")
    @patch("app.views.results.pillars.risk_engineering.st")
    def test_backtest_rendered_when_visible(self, mock_st, mock_mc, mock_sensi, mock_scenario, mock_bt):
        """Backtest render should be called when visible."""
        from app.views.results.pillars.risk_engineering import render_risk_analysis

        mock_mc.is_visible.return_value = False
        mock_sensi.is_visible.return_value = False
        mock_scenario.is_visible.return_value = False
        mock_bt.is_visible.return_value = True

        result = _make_base_result()
        render_risk_analysis(result)

        mock_bt.render.assert_called_once()

    @patch("app.views.results.pillars.risk_engineering.HistoricalBacktestTab")
    @patch("app.views.results.pillars.risk_engineering.ScenarioAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.SensitivityAnalysisTab")
    @patch("app.views.results.pillars.risk_engineering.MonteCarloDistributionTab")
    @patch("app.views.results.pillars.risk_engineering.st")
    def test_backtest_fallback_when_not_visible(self, mock_st, mock_mc, mock_sensi, mock_scenario, mock_bt):
        """When backtest is not visible, fallback info should be shown."""
        from app.views.results.pillars.risk_engineering import render_risk_analysis

        mock_mc.is_visible.return_value = False
        mock_sensi.is_visible.return_value = False
        mock_scenario.is_visible.return_value = False
        mock_bt.is_visible.return_value = False

        result = _make_base_result()
        render_risk_analysis(result)

        mock_st.info.assert_called()


# =============================================================================
# MARKET ANALYSIS (Pillar 5)
# =============================================================================


class TestMarketAnalysisRendering:
    """Tests render_market_context with mocked streamlit."""

    @patch("app.views.results.pillars.market_analysis.SOTPBreakdownTab")
    @patch("app.views.results.pillars.market_analysis.PeerMultiples")
    @patch("app.views.results.pillars.market_analysis.st")
    def test_renders_header(self, mock_st, mock_peers, mock_sotp):
        """Market analysis must render pillar header."""
        from app.views.results.pillars.market_analysis import render_market_context

        mock_peers.is_visible.return_value = False
        mock_sotp.is_visible.return_value = False

        result = _make_base_result()
        render_market_context(result)

        mock_st.header.assert_called()

    @patch("app.views.results.pillars.market_analysis.SOTPBreakdownTab")
    @patch("app.views.results.pillars.market_analysis.PeerMultiples")
    @patch("app.views.results.pillars.market_analysis.st")
    def test_peers_rendered_when_visible(self, mock_st, mock_peers, mock_sotp):
        """PeerMultiples render should be called when visible."""
        from app.views.results.pillars.market_analysis import render_market_context

        mock_peers.is_visible.return_value = True
        mock_sotp.is_visible.return_value = False

        result = _make_base_result()
        render_market_context(result)

        mock_peers.render.assert_called_once()

    @patch("app.views.results.pillars.market_analysis.SOTPBreakdownTab")
    @patch("app.views.results.pillars.market_analysis.PeerMultiples")
    @patch("app.views.results.pillars.market_analysis.st")
    def test_sotp_rendered_when_visible(self, mock_st, mock_peers, mock_sotp):
        """SOTPBreakdownTab render should be called when visible."""
        from app.views.results.pillars.market_analysis import render_market_context

        mock_peers.is_visible.return_value = False
        mock_sotp.is_visible.return_value = True

        result = _make_base_result()
        render_market_context(result)

        mock_sotp.render.assert_called_once()

    @patch("app.views.results.pillars.market_analysis.SOTPBreakdownTab")
    @patch("app.views.results.pillars.market_analysis.PeerMultiples")
    @patch("app.views.results.pillars.market_analysis.st")
    def test_both_visible_with_divider(self, mock_st, mock_peers, mock_sotp):
        """When both peers and SOTP visible, divider should appear between them."""
        from app.views.results.pillars.market_analysis import render_market_context

        mock_peers.is_visible.return_value = True
        mock_sotp.is_visible.return_value = True

        result = _make_base_result()
        render_market_context(result)

        mock_peers.render.assert_called_once()
        mock_sotp.render.assert_called_once()

    @patch("app.views.results.pillars.market_analysis.SOTPBreakdownTab")
    @patch("app.views.results.pillars.market_analysis.PeerMultiples")
    @patch("app.views.results.pillars.market_analysis.st")
    def test_fallback_when_neither_visible(self, mock_st, mock_peers, mock_sotp):
        """When neither visible, fallback info should be shown."""
        from app.views.results.pillars.market_analysis import render_market_context

        mock_peers.is_visible.return_value = False
        mock_sotp.is_visible.return_value = False

        result = _make_base_result()
        render_market_context(result)

        mock_st.info.assert_called()


# =============================================================================
# CALCULATION PROOF (Pillar 2)
# =============================================================================


class TestCalculationProofRendering:
    """Tests render_glass_box with mocked streamlit."""

    @patch("app.views.results.pillars.calculation_proof.render_calculation_step")
    @patch("app.views.results.pillars.calculation_proof.st")
    def test_renders_with_trace_data(self, mock_st, mock_render_step):
        """render_glass_box must render steps when trace data exists."""
        from app.views.results.pillars.calculation_proof import render_glass_box

        result = _make_base_result()
        # Add a calculation step to the strategy trace
        step = CalculationStep(
            step_key="WACC_CALC",
            label="WACC Calculation",
            result=0.08,
            unit="%",
        )
        result.results.strategy.strategy_trace = [step]

        render_glass_box(result)

        mock_render_step.assert_called_once()
        mock_st.subheader.assert_called()

    @patch("app.views.results.pillars.calculation_proof.render_calculation_step")
    @patch("app.views.results.pillars.calculation_proof.st")
    def test_empty_trace_shows_info(self, mock_st, mock_render_step):
        """render_glass_box with empty trace must show info message."""
        from app.views.results.pillars.calculation_proof import render_glass_box

        result = _make_base_result()
        result.results.strategy.strategy_trace = []
        result.results.common.bridge_trace = []

        render_glass_box(result)

        mock_st.info.assert_called()
        mock_render_step.assert_not_called()

    @patch("app.views.results.pillars.calculation_proof.render_calculation_step")
    @patch("app.views.results.pillars.calculation_proof.st")
    def test_excluded_steps_filtered(self, mock_st, mock_render_step):
        """Steps with excluded prefixes must be filtered out."""
        from app.views.results.pillars.calculation_proof import render_glass_box

        result = _make_base_result()
        valid_step = CalculationStep(step_key="WACC_CALC", label="WACC", result=0.08, unit="%")
        internal_step = CalculationStep(step_key="_meta_hash", label="Meta", result=0, unit="")
        result.results.strategy.strategy_trace = [valid_step, internal_step]

        render_glass_box(result)

        # Only the valid step should be rendered
        mock_render_step.assert_called_once()


# =============================================================================
# STEP RENDERER
# =============================================================================


class TestStepRendererRendering:
    """Tests render_calculation_step with mocked streamlit."""

    @patch("app.views.components.step_renderer.st")
    def test_renders_step_with_formula(self, mock_st):
        """render_calculation_step must render label, value, and formula."""
        from app.views.components.step_renderer import render_calculation_step

        step = CalculationStep(
            step_key="WACC_CALC",
            label="WACC Calculation",
            result=0.08,
            unit="%",
            theoretical_formula=r"WACC = Ke \times E/(D+E) + Kd \times D/(D+E)",
        )
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        render_calculation_step(index=1, step=step)

        mock_st.latex.assert_called_once()
        mock_st.divider.assert_called()

    @patch("app.views.components.step_renderer.st")
    def test_renders_step_with_variables(self, mock_st):
        """render_calculation_step with variables_map must show expander."""
        from app.views.components.step_renderer import render_calculation_step

        step = CalculationStep(
            step_key="KE_CALC",
            label="Cost of Equity",
            result=0.10,
            unit="%",
            variables_map={
                "Rf": VariableInfo(
                    symbol="Rf",
                    value=0.04,
                    description="Risk-Free Rate",
                    formatted_value="4.00%",
                ),
            },
        )
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value.__enter__ = MagicMock()
        mock_st.expander.return_value.__exit__ = MagicMock()

        render_calculation_step(index=1, step=step)

        mock_st.expander.assert_called()

    @patch("app.views.components.step_renderer.st")
    def test_renders_step_without_formula(self, mock_st):
        """render_calculation_step without formula should not call st.latex."""
        from app.views.components.step_renderer import render_calculation_step

        step = CalculationStep(
            step_key="BASIC",
            label="Basic Step",
            result=42.0,
            unit="currency",
        )
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        render_calculation_step(index=1, step=step)

        mock_st.latex.assert_not_called()

    @patch("app.views.components.step_renderer.st")
    def test_renders_step_with_interpretation(self, mock_st):
        """render_calculation_step with interpretation should call st.caption."""
        from app.views.components.step_renderer import render_calculation_step

        step = CalculationStep(
            step_key="WACC_CALC",
            label="WACC",
            result=0.08,
            unit="%",
            interpretation="The WACC is used to discount future cash flows.",
        )
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        col1 = MagicMock()
        col2 = MagicMock()
        col1.__enter__ = MagicMock(return_value=col1)
        col1.__exit__ = MagicMock(return_value=False)
        col2.__enter__ = MagicMock(return_value=col2)
        col2.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = [col1, col2]

        render_calculation_step(index=1, step=step)

        # st.caption is called directly inside the `with c1:` block
        mock_st.caption.assert_called_with(step.interpretation)


# =============================================================================
# UI KPIS RENDERING
# =============================================================================


class TestUIKpisRendering:
    """Tests UI KPI components with mocked streamlit."""

    @patch("app.views.components.ui_kpis.st")
    def test_atom_kpi_metric_calls_st_metric(self, mock_st):
        """atom_kpi_metric must call st.metric."""
        from app.views.components.ui_kpis import atom_kpi_metric

        atom_kpi_metric(label="Test", value="100.0")

        mock_st.metric.assert_called_once()

    @patch("app.views.components.ui_kpis.st")
    def test_atom_kpi_metric_with_delta(self, mock_st):
        """atom_kpi_metric with delta must pass delta to st.metric."""
        from app.views.components.ui_kpis import atom_kpi_metric

        atom_kpi_metric(label="Test", value="100.0", delta="+5%", delta_color="green")

        call_kwargs = mock_st.metric.call_args[1]
        assert call_kwargs["delta"] == "+5%"
        assert call_kwargs["delta_color"] == "normal"  # green maps to normal

    @patch("app.views.components.ui_kpis.st")
    def test_atom_kpi_metric_unknown_color(self, mock_st):
        """atom_kpi_metric with unknown color must default to 'off'."""
        from app.views.components.ui_kpis import atom_kpi_metric

        atom_kpi_metric(label="Test", value="100", delta="+5%", delta_color="purple")

        call_kwargs = mock_st.metric.call_args[1]
        assert call_kwargs["delta_color"] == "off"

    @patch("app.views.components.ui_kpis.st")
    def test_render_score_gauge(self, mock_st):
        """render_score_gauge must render progress bar and caption."""
        from app.views.components.ui_kpis import render_score_gauge

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        render_score_gauge(score=75.0, label="Health Score")

        mock_st.progress.assert_called_once()
        mock_st.caption.assert_called()

    @patch("app.views.components.ui_kpis.st")
    def test_atom_benchmark_card_renders(self, mock_st):
        """atom_benchmark_card must render container, columns, and divider."""
        from app.views.components.ui_kpis import atom_benchmark_card

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        atom_benchmark_card(
            label="P/E",
            company_value="28.0x",
            market_value="25.0x",
            status="RETARD",
            status_color="orange",
            description="Test description",
        )

        mock_st.container.assert_called()
        mock_st.divider.assert_called()

    @patch("app.views.components.ui_kpis.st")
    def test_atom_benchmark_card_no_description(self, mock_st):
        """atom_benchmark_card without description should not call st.caption."""
        from app.views.components.ui_kpis import atom_benchmark_card

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)

        atom_benchmark_card(
            label="P/E",
            company_value="28.0x",
            market_value="25.0x",
            status="LEADER",
            status_color="green",
        )

        mock_st.caption.assert_not_called()
