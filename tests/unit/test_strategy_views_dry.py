"""
tests/unit/test_strategy_views_dry.py

STRATEGY VIEWS DRY COMPLIANCE TESTS
=====================================
Role: Validates that strategy views no longer contain duplicate projection
year sliders or captions, ensuring DRY compliance with the sidebar.
"""

import inspect

import pytest

from app.views.inputs.strategies.ddm_view import DDMView
from app.views.inputs.strategies.fcfe_view import FCFEView
from app.views.inputs.strategies.fcff_growth_view import FCFFGrowthView
from app.views.inputs.strategies.fcff_normalized_view import FCFFNormalizedView
from app.views.inputs.strategies.fcff_standard_view import FCFFStandardView
from app.views.inputs.strategies.graham_value_view import GrahamValueView
from app.views.inputs.strategies.rim_bank_view import RIMBankView
from src.models.enums import ValuationMethodology


ALL_VIEWS = [
    FCFFStandardView,
    FCFFNormalizedView,
    FCFFGrowthView,
    FCFEView,
    DDMView,
    RIMBankView,
    GrahamValueView,
]

DCF_VIEWS = [
    FCFFStandardView,
    FCFFNormalizedView,
    FCFFGrowthView,
    FCFEView,
    DDMView,
    RIMBankView,
]


class TestNoDuplicateProjectionYears:
    """Ensures no strategy view contains a projection year slider or caption."""

    @pytest.mark.parametrize("view_cls", ALL_VIEWS, ids=lambda v: v.__name__)
    def test_no_projection_years_caption(self, view_cls):
        """Strategy views must NOT display a projection years caption."""
        source = inspect.getsource(view_cls)
        assert "projection_years" not in source, (
            f"{view_cls.__name__} still references 'projection_years' — "
            "this must be managed solely by the sidebar."
        )

    @pytest.mark.parametrize("view_cls", ALL_VIEWS, ids=lambda v: v.__name__)
    def test_no_sidebar_texts_import(self, view_cls):
        """Strategy views must NOT import SidebarTexts (DRY violation)."""
        source = inspect.getsource(view_cls)
        assert "SidebarTexts" not in source, (
            f"{view_cls.__name__} imports SidebarTexts — "
            "projection configuration belongs exclusively in the sidebar."
        )

    @pytest.mark.parametrize("view_cls", ALL_VIEWS, ids=lambda v: v.__name__)
    def test_no_get_state_import(self, view_cls):
        """Strategy views should NOT import get_state (state is sidebar-managed)."""
        source = inspect.getsource(view_cls)
        assert "get_state" not in source, (
            f"{view_cls.__name__} imports get_state — "
            "state access for projection years should be in the sidebar only."
        )


class TestSharedWidgetsDRY:
    """Ensures shared_widgets.py does not define widget_projection_years."""

    def test_no_widget_projection_years(self):
        """The widget_projection_years function must be removed from shared_widgets."""
        from app.views.inputs.strategies import shared_widgets
        assert not hasattr(shared_widgets, 'widget_projection_years'), (
            "widget_projection_years still exists in shared_widgets.py — must be removed."
        )


class TestStrategyViewConfiguration:
    """Tests that each strategy view has correct configuration."""

    @pytest.mark.parametrize("view_cls,expected_mode", [
        (FCFFStandardView, ValuationMethodology.FCFF_STANDARD),
        (FCFFNormalizedView, ValuationMethodology.FCFF_NORMALIZED),
        (FCFFGrowthView, ValuationMethodology.FCFF_GROWTH),
        (FCFEView, ValuationMethodology.FCFE),
        (DDMView, ValuationMethodology.DDM),
        (RIMBankView, ValuationMethodology.RIM),
        (GrahamValueView, ValuationMethodology.GRAHAM),
    ], ids=lambda v: v.__name__ if isinstance(v, type) else str(v))
    def test_mode_assignment(self, view_cls, expected_mode):
        """Each view must be correctly bound to its methodology."""
        assert view_cls.MODE == expected_mode

    @pytest.mark.parametrize("view_cls", DCF_VIEWS, ids=lambda v: v.__name__)
    def test_dcf_views_show_monte_carlo(self, view_cls):
        """All DCF views must enable Monte Carlo simulation."""
        assert view_cls.SHOW_MONTE_CARLO is True

    @pytest.mark.parametrize("view_cls", DCF_VIEWS, ids=lambda v: v.__name__)
    def test_dcf_views_show_backtest(self, view_cls):
        """All DCF views must enable historical backtesting."""
        assert view_cls.SHOW_BACKTEST is True

    def test_graham_disables_sensitivity(self):
        """Graham formula has no WACC vs g — sensitivity must be disabled."""
        assert GrahamValueView.SHOW_SENSITIVITY is False

    def test_graham_disables_sotp(self):
        """Graham is per-share intrinsic — SOTP must be disabled."""
        assert GrahamValueView.SHOW_SOTP is False

    def test_fcfe_disables_sotp(self):
        """FCFE is equity-based — SOTP (EV-based) must be disabled."""
        assert FCFEView.SHOW_SOTP is False

    def test_ddm_disables_sotp(self):
        """DDM is per-share — SOTP must be disabled."""
        assert DDMView.SHOW_SOTP is False

    def test_fcfe_no_bridge(self):
        """FCFE is direct equity — bridge section must be disabled."""
        assert FCFEView.SHOW_BRIDGE_SECTION is False

    def test_ddm_no_bridge(self):
        """DDM is direct equity — bridge section must be disabled."""
        assert DDMView.SHOW_BRIDGE_SECTION is False

    def test_graham_no_discount_section(self):
        """Graham has no WACC/Ke — discount section must be disabled."""
        assert GrahamValueView.SHOW_DISCOUNT_SECTION is False

    def test_graham_no_terminal_section(self):
        """Graham is all-in-one formula — terminal section must be disabled."""
        assert GrahamValueView.SHOW_TERMINAL_SECTION is False

    def test_graham_no_bridge_section(self):
        """Graham gives direct price — bridge section must be disabled."""
        assert GrahamValueView.SHOW_BRIDGE_SECTION is False


class TestViewDocstrings:
    """Ensures all strategy views have proper docstrings."""

    @pytest.mark.parametrize("view_cls", ALL_VIEWS, ids=lambda v: v.__name__)
    def test_class_has_docstring(self, view_cls):
        """Each strategy view class must have a docstring."""
        assert view_cls.__doc__ is not None, f"{view_cls.__name__} lacks a class docstring."

    @pytest.mark.parametrize("view_cls", ALL_VIEWS, ids=lambda v: v.__name__)
    def test_render_method_has_docstring(self, view_cls):
        """Each render_model_inputs method must have a docstring."""
        method = view_cls.render_model_inputs
        assert method.__doc__ is not None, (
            f"{view_cls.__name__}.render_model_inputs lacks a docstring."
        )
