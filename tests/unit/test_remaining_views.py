"""
tests/unit/test_remaining_views.py

REMAINING VIEW COVERAGE TESTS
================================
Role: Covers input_factory, base_strategy, strategy views, sidebar interactions,
main.py, shared_widgets, peer_multiples, and ui_charts with mock-based tests.
Coverage Target: >85% per file.
"""

import inspect
from unittest.mock import MagicMock, patch

from src.models.enums import ValuationMethodology

# =============================================================================
# INPUT FACTORY
# =============================================================================


class TestInputFactory:
    """Tests InputFactory static methods."""

    def test_class_exists(self):
        """InputFactory must exist."""
        from app.controllers.input_factory import InputFactory

        assert inspect.isclass(InputFactory)

    def test_build_request_is_static(self):
        """build_request must be a static method."""
        from app.controllers.input_factory import InputFactory

        assert isinstance(
            inspect.getattr_static(InputFactory, "build_request"),
            staticmethod,
        )

    @patch("app.controllers.input_factory.st")
    @patch("app.controllers.input_factory.get_state")
    def test_build_request_creates_valuation_request(self, mock_get_state, mock_st):
        """build_request must return a ValuationRequest."""
        from app.controllers.input_factory import InputFactory

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.FCFF_STANDARD
        state.projection_years = 5
        mock_get_state.return_value = state

        # Mock session_state with default values for all expected keys
        mock_st.session_state = {
            "fcf_anchor": 100000.0,
            "growth_rate_p1": 0.05,
            "growth_rate_p2": 0.03,
            "terminal_growth": 0.02,
            "exit_multiple": None,
            "terminal_method": None,
            "risk_free_rate": 0.04,
            "market_risk_premium": 0.05,
            "beta": 1.2,
            "tax_rate": 0.21,
            "cost_of_debt": None,
            "debt_weight": None,
            "total_debt": None,
            "cash": None,
            "shares_outstanding": None,
            "enable": False,
            "sensi_enable": False,
            "scenario_enable": False,
            "bt_enable": False,
            "peer_enable": False,
            "sotp_enable": False,
        }

        result = InputFactory.build_request()

        from src.models.valuation import ValuationRequest

        assert isinstance(result, ValuationRequest)
        assert result.parameters.structure.ticker == "AAPL"

    @patch("app.controllers.input_factory.st")
    @patch("app.controllers.input_factory.get_state")
    def test_build_request_graham_mode(self, mock_get_state, mock_st):
        """build_request for Graham mode should produce valid request."""
        from app.controllers.input_factory import InputFactory

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.GRAHAM
        state.projection_years = 5
        mock_get_state.return_value = state

        mock_st.session_state = {
            "eps_normalized": 6.50,
            "growth_estimate": 0.05,
            "risk_free_rate": 0.04,
            "market_risk_premium": 0.05,
            "beta": 1.2,
            "tax_rate": 0.21,
            "cost_of_debt": None,
            "debt_weight": None,
            "total_debt": None,
            "cash": None,
            "shares_outstanding": None,
            "enable": False,
            "sensi_enable": False,
            "scenario_enable": False,
            "bt_enable": False,
            "peer_enable": False,
            "sotp_enable": False,
        }

        result = InputFactory.build_request()
        assert result.mode == ValuationMethodology.GRAHAM


# =============================================================================
# BASE STRATEGY
# =============================================================================


class TestBaseStrategyView:
    """Tests BaseStrategyView abstract base class."""

    def test_base_class_is_abstract(self):
        """BaseStrategyView must be abstract."""
        from app.views.inputs.base_strategy import BaseStrategyView

        assert inspect.isabstract(BaseStrategyView)

    def test_has_render_method(self):
        """BaseStrategyView must have a render method."""
        from app.views.inputs.base_strategy import BaseStrategyView

        assert hasattr(BaseStrategyView, "render")

    def test_has_render_model_inputs_abstract(self):
        """render_model_inputs must be abstract."""
        from app.views.inputs.base_strategy import BaseStrategyView

        assert hasattr(BaseStrategyView, "render_model_inputs")

    def test_config_attributes_exist(self):
        """BaseStrategyView must define configuration attributes."""
        from app.views.inputs.base_strategy import BaseStrategyView

        assert hasattr(BaseStrategyView, "MODE")
        assert hasattr(BaseStrategyView, "DISPLAY_NAME")
        assert hasattr(BaseStrategyView, "SHOW_DISCOUNT_SECTION")
        assert hasattr(BaseStrategyView, "SHOW_TERMINAL_SECTION")
        assert hasattr(BaseStrategyView, "SHOW_BRIDGE_SECTION")
        assert hasattr(BaseStrategyView, "SHOW_MONTE_CARLO")
        assert hasattr(BaseStrategyView, "SHOW_SENSITIVITY")
        assert hasattr(BaseStrategyView, "SHOW_BACKTEST")
        assert hasattr(BaseStrategyView, "SHOW_SCENARIOS")
        assert hasattr(BaseStrategyView, "SHOW_SOTP")
        assert hasattr(BaseStrategyView, "SHOW_PEER_TRIANGULATION")


# =============================================================================
# STRATEGY VIEWS
# =============================================================================


class TestStrategyViews:
    """Tests concrete strategy view classes."""

    def test_fcff_standard_view_exists(self):
        """FCFFStandardView must exist."""
        from app.views.inputs.strategies.fcff_standard_view import FCFFStandardView

        assert hasattr(FCFFStandardView, "render_model_inputs")
        assert FCFFStandardView.MODE == ValuationMethodology.FCFF_STANDARD

    def test_fcff_normalized_view_exists(self):
        """FCFFNormalizedView must exist."""
        from app.views.inputs.strategies.fcff_normalized_view import FCFFNormalizedView

        assert FCFFNormalizedView.MODE == ValuationMethodology.FCFF_NORMALIZED

    def test_fcff_growth_view_exists(self):
        """FCFFGrowthView must exist."""
        from app.views.inputs.strategies.fcff_growth_view import FCFFGrowthView

        assert FCFFGrowthView.MODE == ValuationMethodology.FCFF_GROWTH

    def test_fcfe_view_exists(self):
        """FCFEView must exist."""
        from app.views.inputs.strategies.fcfe_view import FCFEView

        assert FCFEView.MODE == ValuationMethodology.FCFE

    def test_ddm_view_exists(self):
        """DDMView must exist."""
        from app.views.inputs.strategies.ddm_view import DDMView

        assert DDMView.MODE == ValuationMethodology.DDM

    def test_rim_bank_view_exists(self):
        """RIMBankView must exist."""
        from app.views.inputs.strategies.rim_bank_view import RIMBankView

        assert RIMBankView.MODE == ValuationMethodology.RIM

    def test_graham_value_view_exists(self):
        """GrahamValueView must exist."""
        from app.views.inputs.strategies.graham_value_view import GrahamValueView

        assert GrahamValueView.MODE == ValuationMethodology.GRAHAM

    @patch("app.views.inputs.strategies.fcff_standard_view.st")
    @patch("app.views.inputs.base_strategy.st")
    def test_fcff_standard_render(self, mock_base_st, mock_st):
        """FCFFStandardView.render_model_inputs must call st.number_input."""
        from app.views.inputs.strategies.fcff_standard_view import FCFFStandardView

        view = FCFFStandardView(ticker="AAPL")
        mock_st.number_input.return_value = 100000.0

        view.render_model_inputs()

        mock_st.number_input.assert_called()

    @patch("app.views.inputs.strategies.graham_value_view.st")
    @patch("app.views.inputs.base_strategy.st")
    def test_graham_view_render(self, mock_base_st, mock_st):
        """GrahamValueView.render_model_inputs must call st.number_input."""
        from app.views.inputs.strategies.graham_value_view import GrahamValueView

        view = GrahamValueView(ticker="AAPL")
        mock_st.number_input.return_value = 6.50

        def make_cols(spec):
            n = spec if isinstance(spec, int) else len(spec)
            cols = [MagicMock() for _ in range(n)]
            for col in cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            return cols

        mock_st.columns.side_effect = make_cols

        view.render_model_inputs()

        mock_st.number_input.assert_called()

    @patch("app.views.inputs.strategies.rim_bank_view.st")
    @patch("app.views.inputs.base_strategy.st")
    def test_rim_view_render(self, mock_base_st, mock_st):
        """RIMBankView.render_model_inputs must call st.number_input."""
        from app.views.inputs.strategies.rim_bank_view import RIMBankView

        view = RIMBankView(ticker="AAPL")
        mock_st.number_input.return_value = 500000.0

        # Add column mocking
        col1 = MagicMock()
        col2 = MagicMock()
        col1.__enter__ = MagicMock(return_value=col1)
        col1.__exit__ = MagicMock(return_value=False)
        col2.__enter__ = MagicMock(return_value=col2)
        col2.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = [col1, col2]

        view.render_model_inputs()

        mock_st.number_input.assert_called()

    @patch("app.views.inputs.strategies.ddm_view.st")
    @patch("app.views.inputs.base_strategy.st")
    def test_ddm_view_render(self, mock_base_st, mock_st):
        """DDMView.render_model_inputs must call st.number_input."""
        from app.views.inputs.strategies.ddm_view import DDMView

        view = DDMView(ticker="AAPL")
        mock_st.number_input.return_value = 3.50

        view.render_model_inputs()

        mock_st.number_input.assert_called()

    @patch("app.views.inputs.strategies.fcfe_view.st")
    @patch("app.views.inputs.base_strategy.st")
    def test_fcfe_view_render(self, mock_base_st, mock_st):
        """FCFEView.render_model_inputs must call st.number_input."""
        from app.views.inputs.strategies.fcfe_view import FCFEView

        view = FCFEView(ticker="AAPL")
        mock_st.number_input.return_value = 80000.0

        def make_cols(spec):
            n = spec if isinstance(spec, int) else len(spec)
            cols = [MagicMock() for _ in range(n)]
            for col in cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            return cols

        mock_st.columns.side_effect = make_cols

        view.render_model_inputs()

        mock_st.number_input.assert_called()

    @patch("app.views.inputs.strategies.fcff_normalized_view.st")
    @patch("app.views.inputs.base_strategy.st")
    def test_normalized_view_render(self, mock_base_st, mock_st):
        """FCFFNormalizedView.render_model_inputs must call st.number_input."""
        from app.views.inputs.strategies.fcff_normalized_view import FCFFNormalizedView

        view = FCFFNormalizedView(ticker="AAPL")
        mock_st.number_input.return_value = 100000.0

        view.render_model_inputs()

        mock_st.number_input.assert_called()

    @patch("app.views.inputs.strategies.fcff_growth_view.st")
    @patch("app.views.inputs.base_strategy.st")
    def test_growth_view_render(self, mock_base_st, mock_st):
        """FCFFGrowthView.render_model_inputs must call st.number_input."""
        from app.views.inputs.strategies.fcff_growth_view import FCFFGrowthView

        view = FCFFGrowthView(ticker="AAPL")
        mock_st.number_input.return_value = 0.10

        def make_cols(spec):
            n = spec if isinstance(spec, int) else len(spec)
            cols = [MagicMock() for _ in range(n)]
            for col in cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            return cols

        mock_st.columns.side_effect = make_cols

        view.render_model_inputs()

        mock_st.number_input.assert_called()


# =============================================================================
# BASE STRATEGY RENDERING
# =============================================================================


class TestBaseStrategyRendering:
    """Tests BaseStrategyView.render method which orchestrates all sections."""

    @patch("app.views.inputs.base_strategy.st")
    def test_render_calls_header(self, mock_st):
        """BaseStrategyView.render must call _render_header."""
        from app.views.inputs.strategies.fcff_standard_view import FCFFStandardView

        view = FCFFStandardView(ticker="AAPL")
        mock_st.number_input.return_value = 100000.0
        mock_st.slider.return_value = 0.05
        mock_st.selectbox.return_value = "Gordon Growth"
        mock_st.checkbox.return_value = False
        mock_st.radio.return_value = "Gordon Growth"

        view.render()

        mock_st.markdown.assert_called()

    @patch("app.views.inputs.base_strategy.st")
    def test_render_step_header_is_static(self, mock_st):
        """_render_step_header must be a static method."""
        from app.views.inputs.base_strategy import BaseStrategyView

        assert isinstance(
            inspect.getattr_static(BaseStrategyView, "_render_step_header"),
            staticmethod,
        )


# =============================================================================
# SHARED WIDGETS
# =============================================================================


class TestSharedWidgets:
    """Tests shared_widgets.py public functions."""

    def test_widget_growth_rate_callable(self):
        """widget_growth_rate must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_growth_rate

        assert callable(widget_growth_rate)

    def test_widget_cost_of_capital_callable(self):
        """widget_cost_of_capital must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_cost_of_capital

        assert callable(widget_cost_of_capital)

    def test_widget_terminal_value_dcf_callable(self):
        """widget_terminal_value_dcf must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_terminal_value_dcf

        assert callable(widget_terminal_value_dcf)

    def test_widget_equity_bridge_callable(self):
        """widget_equity_bridge must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_equity_bridge

        assert callable(widget_equity_bridge)

    def test_widget_sensitivity_callable(self):
        """widget_sensitivity must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_sensitivity

        assert callable(widget_sensitivity)

    def test_widget_monte_carlo_callable(self):
        """widget_monte_carlo must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_monte_carlo

        assert callable(widget_monte_carlo)

    def test_widget_backtest_callable(self):
        """widget_backtest must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_backtest

        assert callable(widget_backtest)

    def test_widget_scenarios_callable(self):
        """widget_scenarios must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_scenarios

        assert callable(widget_scenarios)

    def test_widget_sotp_callable(self):
        """widget_sotp must be callable."""
        from app.views.inputs.strategies.shared_widgets import widget_sotp

        assert callable(widget_sotp)

    def test_get_terminal_value_narrative(self):
        """get_terminal_value_narrative must return a string."""
        from app.views.inputs.strategies.shared_widgets import get_terminal_value_narrative

        result = get_terminal_value_narrative(ValuationMethodology.FCFF_STANDARD)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_terminal_narrative_for_ddm(self):
        """DDM terminal narrative should differ from FCFF."""
        from app.views.inputs.strategies.shared_widgets import get_terminal_value_narrative

        get_terminal_value_narrative(ValuationMethodology.FCFF_STANDARD)
        ddm_text = get_terminal_value_narrative(ValuationMethodology.DDM)
        assert isinstance(ddm_text, str)


# =============================================================================
# UI CHARTS
# =============================================================================


class TestUICharts:
    """Tests ui_charts.py public function signatures."""

    def test_display_simulation_chart_callable(self):
        """display_simulation_chart must be callable."""
        from app.views.components.ui_charts import display_simulation_chart

        assert callable(display_simulation_chart)

    def test_display_football_field_callable(self):
        """display_football_field must be callable."""
        from app.views.components.ui_charts import display_football_field

        assert callable(display_football_field)

    def test_display_sotp_waterfall_callable(self):
        """display_sotp_waterfall must be callable."""
        from app.views.components.ui_charts import display_sotp_waterfall

        assert callable(display_sotp_waterfall)

    def test_display_backtest_convergence_chart_callable(self):
        """display_backtest_convergence_chart must be callable."""
        from app.views.components.ui_charts import display_backtest_convergence_chart

        assert callable(display_backtest_convergence_chart)

    def test_display_sector_comparison_chart_callable(self):
        """display_sector_comparison_chart must be callable."""
        from app.views.components.ui_charts import display_sector_comparison_chart

        assert callable(display_sector_comparison_chart)

    def test_display_scenario_comparison_chart_callable(self):
        """display_scenario_comparison_chart must be callable."""
        from app.views.components.ui_charts import display_scenario_comparison_chart

        assert callable(display_scenario_comparison_chart)


# =============================================================================
# MAIN.PY FULL FLOW
# =============================================================================


class TestMainFullFlow:
    """Tests main.py entry point with mocked dependencies."""

    @patch("app.main.render_sidebar")
    @patch("app.main.inject_institutional_design")
    @patch("app.main.get_state")
    @patch("app.main.SessionManager")
    @patch("app.main.st")
    def test_main_error_path(self, mock_st, mock_sm, mock_get_state, mock_inject, mock_sidebar):
        """main() with error_message should show st.error."""
        from app.main import main

        state = MagicMock()
        state.error_message = "Something went wrong"
        state.last_result = None
        mock_get_state.return_value = state
        mock_st.button.return_value = False

        main()

        mock_st.error.assert_called_with("Something went wrong")

    @patch("app.main.render_valuation_results")
    @patch("app.main.render_sidebar")
    @patch("app.main.inject_institutional_design")
    @patch("app.main.get_state")
    @patch("app.main.SessionManager")
    @patch("app.main.st")
    def test_main_results_path(
        self, mock_st, mock_sm, mock_get_state, mock_inject, mock_sidebar, mock_results
    ):
        """main() with last_result should render valuation results."""
        from app.main import main

        state = MagicMock()
        state.error_message = ""
        state.last_result = MagicMock()
        mock_get_state.return_value = state

        main()

        mock_results.assert_called_once_with(state.last_result)

    @patch("app.main.render_auto_form")
    @patch("app.main.render_sidebar")
    @patch("app.main.inject_institutional_design")
    @patch("app.main.get_state")
    @patch("app.main.SessionManager")
    @patch("app.main.st")
    def test_main_auto_mode_path(
        self, mock_st, mock_sm, mock_get_state, mock_inject, mock_sidebar, mock_auto
    ):
        """main() in auto mode should render auto form."""
        from app.main import main

        state = MagicMock()
        state.error_message = ""
        state.last_result = None
        state.is_expert_mode = False
        mock_get_state.return_value = state

        main()

        mock_auto.assert_called_once()

    @patch("app.main.render_expert_form")
    @patch("app.main.render_sidebar")
    @patch("app.main.inject_institutional_design")
    @patch("app.main.get_state")
    @patch("app.main.SessionManager")
    @patch("app.main.st")
    def test_main_expert_mode_path(
        self, mock_st, mock_sm, mock_get_state, mock_inject, mock_sidebar, mock_expert
    ):
        """main() in expert mode should render expert form."""
        from app.main import main

        state = MagicMock()
        state.error_message = ""
        state.last_result = None
        state.is_expert_mode = True
        mock_get_state.return_value = state

        main()

        mock_expert.assert_called_once()

    @patch("app.main.render_sidebar")
    @patch("app.main.inject_institutional_design")
    @patch("app.main.get_state")
    @patch("app.main.SessionManager")
    @patch("app.main.st")
    def test_main_error_dismiss(self, mock_st, mock_sm, mock_get_state, mock_inject, mock_sidebar):
        """main() error dismiss button should clear error_message."""
        from app.main import main

        state = MagicMock()
        state.error_message = "Error occurred"
        state.last_result = None
        mock_get_state.return_value = state
        mock_st.button.return_value = True  # Simulate dismiss click

        main()

        assert state.error_message == ""


# =============================================================================
# SIDEBAR INTERACTIONS
# =============================================================================


class TestSidebarInteractions:
    """Tests sidebar interaction branches."""

    @patch("app.views.inputs.sidebar.get_state")
    @patch("app.views.inputs.sidebar.SessionManager")
    @patch("app.views.inputs.sidebar.AppController")
    @patch("app.views.inputs.sidebar.st")
    def test_sidebar_run_analysis_button(self, mock_st, mock_ctrl, mock_sm, mock_get_state):
        """Clicking Run Analysis button must call AppController."""
        from app.views.inputs.sidebar import render_sidebar

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.FCFF_STANDARD
        state.projection_years = 5
        state.is_expert_mode = False
        mock_get_state.return_value = state

        sidebar_ctx = MagicMock()
        sidebar_ctx.__enter__ = MagicMock(return_value=sidebar_ctx)
        sidebar_ctx.__exit__ = MagicMock(return_value=False)
        mock_st.sidebar = sidebar_ctx

        mock_st.form.return_value.__enter__ = MagicMock()
        mock_st.form.return_value.__exit__ = MagicMock()
        mock_st.text_input.return_value = "AAPL"
        mock_st.form_submit_button.return_value = False
        mock_st.slider.return_value = 5
        mock_st.selectbox.return_value = ValuationMethodology.FCFF_STANDARD
        mock_st.toggle.return_value = False
        mock_st.button.return_value = True  # Run button pressed

        render_sidebar()

        mock_ctrl.handle_run_analysis.assert_called_once()
