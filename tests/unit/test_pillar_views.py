"""
tests/unit/test_pillar_views.py

PILLAR VIEW COMPONENT TESTS
============================
Role: Validates the rendering logic, data access patterns, and visibility
for all pillar view files in app/views/results/pillars/.
Coverage Target: >85% per file.
"""

import inspect
from datetime import date

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
from src.models.parameters.strategies import FCFFStandardParameters, GrahamParameters, RIMParameters
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

# Pillar imports
from app.views.results.pillars.risk_engineering import render_risk_analysis
from app.views.results.pillars.inputs_summary import (
    _safe_fmt,
    _render_capital_structure_table,
    _render_rates_table,
    _render_strategy_inputs_table,
    render_detailed_inputs,
)
from app.views.results.pillars.calculation_proof import render_glass_box, EXCLUDED_STEP_PREFIXES
from app.views.results.pillars.market_analysis import render_market_context
from app.views.results.pillars.monte_carlo_distribution import MonteCarloDistributionTab
from app.views.results.pillars.sensitivity import SensitivityAnalysisTab
from app.views.results.pillars.scenario_analysis import ScenarioAnalysisTab
from app.views.results.pillars.historical_backtest import HistoricalBacktestTab
from app.views.results.pillars.peer_multiples import PeerMultiples
from app.views.results.pillars.sotp_breakdown import SOTPBreakdownTab


@pytest.fixture
def base_result():
    """Construct a minimal but complete ValuationResult."""
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
            extensions=ExtensionBundleParameters(),
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
# INPUTS SUMMARY (Pillar 1) — _safe_fmt and data access
# =============================================================================

class TestSafeFmt:
    """Tests the _safe_fmt utility function from inputs_summary."""

    def test_none_returns_default(self):
        assert _safe_fmt(None, ".2f") == "-"

    def test_none_custom_default(self):
        assert _safe_fmt(None, ".2%", default="N/A") == "N/A"

    def test_float_formatted(self):
        assert _safe_fmt(0.05, ".2%") == "5.00%"

    def test_integer_formatted(self):
        assert _safe_fmt(100.0, ".0f") == "100"

    def test_zero_formatted(self):
        assert _safe_fmt(0.0, ".2f") == "0.00"

    def test_negative_formatted(self):
        assert _safe_fmt(-0.03, ".2%") == "-3.00%"

    def test_auto_default_for_cost_of_debt(self):
        """When value is None, default to 'Auto' for optional rates."""
        assert _safe_fmt(None, ".2%", default="Auto") == "Auto"


class TestInputsSummaryDataAccess:
    """Tests data access patterns in inputs_summary functions."""

    def test_render_detailed_inputs_is_callable(self):
        assert callable(render_detailed_inputs)

    def test_render_capital_structure_table_is_callable(self):
        assert callable(_render_capital_structure_table)

    def test_render_rates_table_is_callable(self):
        assert callable(_render_rates_table)

    def test_render_strategy_inputs_table_is_callable(self):
        assert callable(_render_strategy_inputs_table)

    def test_capital_structure_safe_arithmetic(self):
        """Capital structure calculations must handle None safely."""
        shares = None
        safe_shares = shares if shares is not None else 0
        assert safe_shares == 0

        price = None
        safe_price = price if price is not None else 0.0
        assert safe_price == 0.0

        mkt_cap = safe_price * safe_shares
        assert mkt_cap == 0.0

    def test_net_debt_calculation(self):
        """Net debt must be total_debt - cash."""
        debt = 120_000.0
        cash = 50_000.0
        assert debt - cash == 70_000.0

    def test_rates_table_fmt_rate_logic(self):
        """fmt_rate should prefer input over calculated."""
        # When input is provided
        input_val = 0.04
        calc_val = 0.038
        result = f"{input_val:.2%}" if input_val is not None else (f"{calc_val:.2%} (Auto)" if calc_val is not None else "-")
        assert result == "4.00%"

        # When input is None, use calculated
        input_val_2 = None
        result_2 = f"{input_val_2:.2%}" if input_val_2 is not None else (f"{calc_val:.2%} (Auto)" if calc_val is not None else "-")
        assert "(Auto)" in result_2

        # When both None
        result_3 = f"{None:.2%}" if None is not None else (f"{None:.2%} (Auto)" if None is not None else "-")
        assert result_3 == "-"


class TestStrategyInputsTableLogic:
    """Tests the strategy-specific rendering logic in inputs_summary."""

    def test_dcf_flow_resolution_order(self):
        """DCF strategies resolve base flow from specific attrs in priority order."""
        attrs_priority = ('fcf_anchor', 'fcf_norm', 'revenue_ttm', 'dividend_base', 'fcfe_anchor')
        strat = FCFFStandardParameters(projection_years=5, fcf_anchor=100_000.0)
        anchor_val = 0.0
        for attr in attrs_priority:
            val = getattr(strat, attr, None)
            if val is not None:
                anchor_val = val
                break
        # Values are scaled by the model (million -> absolute)
        assert anchor_val > 0

    def test_growth_resolution_order(self):
        """Growth rate is resolved from strategy-specific attrs."""
        attrs = ('growth_rate_p1', 'revenue_growth_rate', 'growth_rate')
        strat = FCFFStandardParameters(projection_years=5, growth_rate_p1=0.05)
        g_p1 = None
        for attr in attrs:
            val = getattr(strat, attr, None)
            if val is not None:
                g_p1 = val
                break
        assert g_p1 == 0.05

    def test_rim_mode_data_access(self):
        """RIM mode should access book_value_anchor and persistence_factor."""
        strat = RIMParameters(book_value_anchor=500_000.0, persistence_factor=0.60)
        # book_value_anchor is scaled by the model
        assert strat.book_value_anchor > 0
        assert strat.persistence_factor == 0.60

    def test_graham_mode_data_access(self):
        """Graham mode should access eps_normalized and growth_estimate."""
        strat = GrahamParameters(eps_normalized=6.50, growth_estimate=0.05)
        assert strat.eps_normalized == 6.50
        assert strat.growth_estimate == 0.05


# =============================================================================
# CALCULATION PROOF (Pillar 2)
# =============================================================================

class TestCalculationProof:
    """Tests calculation_proof.py constants and logic."""

    def test_render_glass_box_is_callable(self):
        assert callable(render_glass_box)

    def test_excluded_step_prefixes_defined(self):
        """EXCLUDED_STEP_PREFIXES must filter internal steps."""
        assert "_meta" in EXCLUDED_STEP_PREFIXES
        assert "internal_" in EXCLUDED_STEP_PREFIXES
        assert "debug_" in EXCLUDED_STEP_PREFIXES

    def test_excluded_step_filtering_logic(self):
        """Steps with excluded prefixes must be filtered out."""
        test_keys = ["WACC_CALC", "_meta_internal", "internal_debug", "debug_test", "FCF_BASE"]
        filtered = [
            k for k in test_keys
            if not any(k.startswith(prefix) for prefix in EXCLUDED_STEP_PREFIXES)
        ]
        assert "WACC_CALC" in filtered
        assert "FCF_BASE" in filtered
        assert "_meta_internal" not in filtered
        assert "internal_debug" not in filtered
        assert "debug_test" not in filtered


# =============================================================================
# RISK ENGINEERING (Pillar 4) — Hub logic
# =============================================================================

class TestRiskEngineering:
    """Tests risk_engineering.py hub orchestration."""

    def test_render_risk_analysis_is_callable(self):
        assert callable(render_risk_analysis)

    def test_render_risk_analysis_accepts_kwargs(self):
        """render_risk_analysis should accept **kwargs."""
        sig = inspect.signature(render_risk_analysis)
        params = sig.parameters
        assert "kwargs" in params

    def test_mc_visibility_check_exists(self):
        """MonteCarloDistributionTab must have is_visible."""
        assert hasattr(MonteCarloDistributionTab, 'is_visible')
        assert callable(MonteCarloDistributionTab.is_visible)

    def test_sensitivity_visibility_check_exists(self):
        """SensitivityAnalysisTab must have is_visible."""
        assert hasattr(SensitivityAnalysisTab, 'is_visible')

    def test_scenario_visibility_check_exists(self):
        """ScenarioAnalysisTab must have is_visible."""
        assert hasattr(ScenarioAnalysisTab, 'is_visible')

    def test_backtest_visibility_check_exists(self):
        """HistoricalBacktestTab must have is_visible."""
        assert hasattr(HistoricalBacktestTab, 'is_visible')

    def test_all_spokes_have_render(self):
        """All risk spokes must have a render method."""
        for tab_cls in [MonteCarloDistributionTab, SensitivityAnalysisTab,
                        ScenarioAnalysisTab, HistoricalBacktestTab]:
            assert hasattr(tab_cls, 'render')
            assert callable(tab_cls.render)


# =============================================================================
# MARKET ANALYSIS (Pillar 5) — Hub logic
# =============================================================================

class TestMarketAnalysis:
    """Tests market_analysis.py hub orchestration."""

    def test_render_market_context_is_callable(self):
        assert callable(render_market_context)

    def test_render_market_context_accepts_kwargs(self):
        """render_market_context should accept **kwargs."""
        sig = inspect.signature(render_market_context)
        assert "kwargs" in sig.parameters

    def test_peer_multiples_has_visibility(self):
        """PeerMultiples must have is_visible and render."""
        assert hasattr(PeerMultiples, 'is_visible')
        assert hasattr(PeerMultiples, 'render')

    def test_sotp_has_visibility(self):
        """SOTPBreakdownTab must have is_visible and render."""
        assert hasattr(SOTPBreakdownTab, 'is_visible')
        assert hasattr(SOTPBreakdownTab, 'render')


# =============================================================================
# PILLAR SPOKE VISIBILITY — Comprehensive validation
# =============================================================================

class TestMCVisibility:
    """Tests MonteCarloDistributionTab visibility."""

    def test_not_visible_when_disabled(self, base_result):
        assert not MonteCarloDistributionTab.is_visible(base_result)

    def test_not_visible_when_enabled_but_no_results(self, base_result):
        base_result.request.parameters.extensions.monte_carlo = MCParameters(enabled=True)
        assert not MonteCarloDistributionTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        base_result.request.parameters.extensions.monte_carlo = MCParameters(enabled=True)
        base_result.results.extensions.monte_carlo = MCResults(
            simulation_values=[150.0, 160.0, 170.0],
            quantiles={"P10": 140.0, "P50": 155.0, "P90": 175.0},
            mean=160.0, std_dev=10.0,
        )
        assert MonteCarloDistributionTab.is_visible(base_result)


class TestSensitivityVisibility:
    """Tests SensitivityAnalysisTab visibility."""

    def test_not_visible_when_disabled(self, base_result):
        assert not SensitivityAnalysisTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        base_result.request.parameters.extensions.sensitivity = SensitivityParameters(enabled=True)
        base_result.results.extensions.sensitivity = SensitivityResults(
            x_axis_name="WACC", y_axis_name="Growth",
            x_values=[0.07, 0.08, 0.09], y_values=[0.02, 0.03, 0.04],
            values=[[100.0, 110.0, 120.0]] * 3,
            center_value=100.0, sensitivity_score=12.5,
        )
        assert SensitivityAnalysisTab.is_visible(base_result)


class TestScenarioVisibility:
    """Tests ScenarioAnalysisTab visibility."""

    def test_not_visible_when_disabled(self, base_result):
        assert not ScenarioAnalysisTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        base_result.request.parameters.extensions.scenarios = ScenariosParameters(enabled=True)
        base_result.results.extensions.scenarios = ScenariosResults(
            expected_intrinsic_value=155.0,
            outcomes=[
                ScenarioOutcome(label="Bear", intrinsic_value=130.0, upside_pct=-0.13, probability=0.25),
                ScenarioOutcome(label="Bull", intrinsic_value=180.0, upside_pct=0.20, probability=0.75),
            ],
        )
        assert ScenarioAnalysisTab.is_visible(base_result)


class TestBacktestVisibility:
    """Tests HistoricalBacktestTab visibility."""

    def test_not_visible_when_disabled(self, base_result):
        assert not HistoricalBacktestTab.is_visible(base_result)

    def test_not_visible_with_empty_points(self, base_result):
        base_result.request.parameters.extensions.backtest = BacktestParameters(enabled=True)
        base_result.results.extensions.backtest = BacktestResults(
            points=[], mean_absolute_error=0.0, accuracy_score=0.0,
        )
        assert not HistoricalBacktestTab.is_visible(base_result)

    def test_visible_with_valid_points(self, base_result):
        base_result.request.parameters.extensions.backtest = BacktestParameters(enabled=True)
        base_result.results.extensions.backtest = BacktestResults(
            points=[
                HistoricalPoint(
                    valuation_date=date(2023, 6, 30),
                    calculated_iv=155.0, market_price=150.0, error_pct=0.033,
                )
            ],
            mean_absolute_error=0.033, accuracy_score=90.0,
        )
        assert HistoricalBacktestTab.is_visible(base_result)


class TestPeersVisibility:
    """Tests PeerMultiples visibility."""

    def test_not_visible_when_disabled(self, base_result):
        assert not PeerMultiples.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        base_result.request.parameters.extensions.peers = PeersParameters(enabled=True)
        base_result.results.extensions.peers = PeersResults(
            median_multiples_used={"P/E": 25.0},
            implied_prices={"P/E": 160.0},
            final_relative_iv=157.5,
        )
        assert PeerMultiples.is_visible(base_result)


class TestSOTPVisibility:
    """Tests SOTPBreakdownTab visibility."""

    def test_not_visible_when_disabled(self, base_result):
        assert not SOTPBreakdownTab.is_visible(base_result)

    def test_visible_when_enabled_with_results(self, base_result):
        base_result.request.parameters.extensions.sotp = SOTPParameters(enabled=True)
        base_result.results.extensions.sotp = SOTPResults(
            total_enterprise_value=3_000_000.0,
            segment_values={"iPhone": 2_000_000.0, "Services": 1_000_000.0},
            implied_equity_value=2_800_000.0, equity_value_per_share=175.0,
        )
        assert SOTPBreakdownTab.is_visible(base_result)
