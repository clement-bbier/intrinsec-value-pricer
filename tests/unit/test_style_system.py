"""
tests/unit/test_style_system.py

STYLE SYSTEM UNIT TESTS
========================
Role: Validates the centralized design system configuration.
Coverage Target: >85% for app/assets/style_system.py.
"""

import inspect
from unittest.mock import patch, MagicMock

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

    def test_css_button_hover_state(self):
        """Button hover must use darker red."""
        assert "#b91c1c" in INSTITUTIONAL_CSS

    def test_css_sidebar_caption_color(self):
        """Sidebar captions must have a muted white."""
        assert "#cbd5e1" in INSTITUTIONAL_CSS

    def test_css_contains_style_tags(self):
        """CSS string must be wrapped in style tags."""
        assert "<style>" in INSTITUTIONAL_CSS
        assert "</style>" in INSTITUTIONAL_CSS

    def test_css_app_background(self):
        """Main app background should be light."""
        assert "#f8fafc" in INSTITUTIONAL_CSS

    def test_css_slate_secondary_color(self):
        """Borders and secondary accents must use Slate (#94a3b8)."""
        assert "#94a3b8" in INSTITUTIONAL_CSS

    def test_css_form_submit_button(self):
        """Form submit button must have dedicated styling for visibility."""
        assert "stFormSubmitButton" in INSTITUTIONAL_CSS

    def test_css_no_emojis(self):
        """CSS must contain no emoji characters."""
        forbidden = ["\U0001f4ca", "\u2705", "\U0001f680", "\U0001f525"]
        for emoji in forbidden:
            assert emoji not in INSTITUTIONAL_CSS


class TestInjectDesign:
    """Tests the CSS injection function."""

    def test_inject_is_callable(self):
        """inject_institutional_design must be callable."""
        assert callable(inject_institutional_design)

    @patch("app.assets.style_system.st")
    def test_inject_calls_st_markdown(self, mock_st):
        """inject_institutional_design must call st.markdown with CSS."""
        inject_institutional_design()
        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args
        assert "unsafe_allow_html" in call_args.kwargs or call_args[1].get("unsafe_allow_html")

    @patch("app.assets.style_system.st")
    def test_inject_passes_css_content(self, mock_st):
        """inject_institutional_design must pass the INSTITUTIONAL_CSS content."""
        inject_institutional_design()
        css_arg = mock_st.markdown.call_args[0][0]
        assert "<style>" in css_arg
        assert "#dc2626" in css_arg


class TestRenderHeader:
    """Tests the header rendering function."""

    def test_render_header_is_callable(self):
        """render_terminal_header must be callable."""
        assert callable(render_terminal_header)

    @patch("app.assets.style_system.st")
    def test_render_header_calls_markdown(self, mock_st):
        """render_terminal_header must call st.markdown at least twice (header + compliance)."""
        render_terminal_header()
        assert mock_st.markdown.call_count >= 2

    @patch("app.assets.style_system.st")
    def test_render_header_calls_divider(self, mock_st):
        """render_terminal_header must call st.divider."""
        render_terminal_header()
        mock_st.divider.assert_called_once()

    @patch("app.assets.style_system.st")
    def test_render_header_uses_unsafe_html(self, mock_st):
        """render_terminal_header must pass unsafe_allow_html=True."""
        render_terminal_header()
        for call in mock_st.markdown.call_args_list:
            assert call.kwargs.get("unsafe_allow_html") is True or \
                   (len(call.args) > 1 and call.args[1]) or \
                   call[1].get("unsafe_allow_html") is True

    @patch("app.assets.style_system.st")
    def test_render_header_contains_app_title(self, mock_st):
        """render_terminal_header HTML must reference the app title."""
        from src.i18n import CommonTexts
        render_terminal_header()
        header_html = mock_st.markdown.call_args_list[0][0][0]
        assert CommonTexts.APP_TITLE in header_html

    @patch("app.assets.style_system.st")
    def test_render_header_contains_project_badge(self, mock_st):
        """render_terminal_header HTML must reference the project badge."""
        from src.i18n import CommonTexts
        render_terminal_header()
        header_html = mock_st.markdown.call_args_list[0][0][0]
        assert CommonTexts.PROJECT_BADGE in header_html

    @patch("app.assets.style_system.st")
    def test_render_header_contains_compliance(self, mock_st):
        """render_terminal_header must include compliance text."""
        from src.i18n import LegalTexts
        render_terminal_header()
        compliance_html = mock_st.markdown.call_args_list[1][0][0]
        assert LegalTexts.COMPLIANCE_TITLE in compliance_html
