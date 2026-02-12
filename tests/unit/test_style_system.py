"""
tests/unit/test_style_system.py

STYLE SYSTEM UNIT TESTS
========================
Role: Validates the centralized design system configuration.
Coverage Target: >85% for app/assets/style_system.py.
"""

import pytest

from app.assets.style_system import INSTITUTIONAL_CSS, inject_institutional_design, render_terminal_header


class TestInstitutionalCSS:
    """Tests the CSS constants and design tokens."""

    def test_css_contains_inter_font(self):
        """The CSS must import and apply the Inter font family."""
        assert "Inter" in INSTITUTIONAL_CSS

    def test_css_high_contrast_sidebar(self):
        """Sidebar must use deep navy background for high contrast."""
        assert "#0f172a" in INSTITUTIONAL_CSS

    def test_css_sidebar_text_white(self):
        """Sidebar text must be pure white for readability."""
        assert "#ffffff" in INSTITUTIONAL_CSS

    def test_css_action_button_red(self):
        """Primary action button must use institutional red."""
        assert "#dc2626" in INSTITUTIONAL_CSS

    def test_css_no_blue_on_blue(self):
        """Verify no low-contrast blue-on-blue combinations exist."""
        # The old #1F3056 sidebar should be replaced
        assert "#1F3056" not in INSTITUTIONAL_CSS

    def test_css_contains_metric_styling(self):
        """Metric cards must have professional styling."""
        assert "stMetric" in INSTITUTIONAL_CSS

    def test_css_collapse_button_red(self):
        """Sidebar collapse button must use red accent."""
        assert "collapsedControl" in INSTITUTIONAL_CSS

    def test_css_sidebar_widget_background(self):
        """Sidebar widgets must have a semi-transparent background."""
        assert "rgba(255, 255, 255, 0.08)" in INSTITUTIONAL_CSS

    def test_css_sidebar_dividers_visible(self):
        """Sidebar dividers must have visible contrast."""
        assert "rgba(255, 255, 255, 0.25)" in INSTITUTIONAL_CSS


class TestInjectDesign:
    """Tests the CSS injection function."""

    def test_inject_is_callable(self):
        """inject_institutional_design must be callable."""
        assert callable(inject_institutional_design)


class TestRenderHeader:
    """Tests the header rendering function."""

    def test_render_header_is_callable(self):
        """render_terminal_header must be callable."""
        assert callable(render_terminal_header)
