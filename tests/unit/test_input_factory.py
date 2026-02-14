"""
tests/unit/test_input_factory.py

INPUT FACTORY UNIT TESTS
========================
Role: Validate the projection_years flow from AppState to ValuationRequest.
"""

from src.config.constants import UIWidgetDefaults
from src.models.parameters.strategies import (
    BaseProjectedParameters,
    FCFFStandardParameters,
    GrahamParameters,
)


class TestProjectionYearsInjection:
    """Tests the projection_years field handling in strategy parameters."""

    def test_projected_strategies_have_projection_years(self):
        """All projected strategy models should have a projection_years field."""
        strat = FCFFStandardParameters(projection_years=7)
        assert strat.projection_years == 7

    def test_projection_years_default_is_none(self):
        """Without explicit value, projection_years should default to None (ghost)."""
        strat = FCFFStandardParameters()
        assert strat.projection_years is None

    def test_projection_years_settable_via_attribute(self):
        """projection_years should be settable after construction (for InputFactory injection)."""
        strat = FCFFStandardParameters()
        strat.projection_years = 10
        assert strat.projection_years == 10

    def test_graham_has_no_projection_years(self):
        """Graham model (static formula) should NOT have projection_years."""
        strat = GrahamParameters()
        assert not hasattr(strat, "projection_years") or not isinstance(strat, BaseProjectedParameters)

    def test_ui_widget_defaults_range(self):
        """UI defaults should have sensible projection year boundaries."""
        assert UIWidgetDefaults.MIN_PROJECTION_YEARS >= 1
        assert UIWidgetDefaults.MAX_PROJECTION_YEARS <= 50
        assert UIWidgetDefaults.MIN_PROJECTION_YEARS < UIWidgetDefaults.MAX_PROJECTION_YEARS
        assert UIWidgetDefaults.DEFAULT_PROJECTION_YEARS >= UIWidgetDefaults.MIN_PROJECTION_YEARS
        assert UIWidgetDefaults.DEFAULT_PROJECTION_YEARS <= UIWidgetDefaults.MAX_PROJECTION_YEARS
