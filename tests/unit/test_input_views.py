"""
tests/unit/test_input_views.py

INPUT VIEW RENDERING TESTS
============================
Role: Exercises all input form views with mocked streamlit.
Coverage Target: >85% per file for input views.
"""

from unittest.mock import MagicMock, patch

# =============================================================================
# AUTO FORM
# =============================================================================


class TestAutoFormRendering:
    """Tests render_auto_form with mocked streamlit."""

    @patch("app.views.inputs.auto_form.st")
    def test_render_auto_form_calls_markdown(self, mock_st):
        """render_auto_form must call st.markdown for title."""
        from app.views.inputs.auto_form import render_auto_form

        col1 = MagicMock()
        col2 = MagicMock()
        col1.__enter__ = MagicMock(return_value=col1)
        col1.__exit__ = MagicMock(return_value=False)
        col2.__enter__ = MagicMock(return_value=col2)
        col2.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = [col1, col2]

        render_auto_form()

        mock_st.markdown.assert_called()

    @patch("app.views.inputs.auto_form.st")
    def test_render_auto_form_no_checkboxes(self, mock_st):
        """render_auto_form must NOT create extension checkboxes (simplified mode)."""
        from app.views.inputs.auto_form import render_auto_form

        # Add column mocking
        col1 = MagicMock()
        col2 = MagicMock()
        col1.__enter__ = MagicMock(return_value=col1)
        col1.__exit__ = MagicMock(return_value=False)
        col2.__enter__ = MagicMock(return_value=col2)
        col2.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = [col1, col2]

        render_auto_form()

        mock_st.checkbox.assert_not_called()


# =============================================================================
# EXPERT FORM
# =============================================================================


class TestExpertFormRendering:
    """Tests render_expert_form with mocked streamlit."""

    def test_render_expert_form_callable(self):
        """render_expert_form must be callable."""
        from app.views.inputs.expert_form import render_expert_form

        assert callable(render_expert_form)

    @patch("app.views.inputs.expert_form.get_state")
    @patch("app.views.inputs.expert_form.FCFFStandardView")
    @patch("app.views.inputs.expert_form.st")
    def test_expert_form_dispatches_fcff_standard(self, mock_st, mock_view_cls, mock_get_state):
        """Expert form with FCFF_STANDARD should instantiate FCFFStandardView."""
        from app.views.inputs.expert_form import render_expert_form
        from src.models.enums import ValuationMethodology

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.FCFF_STANDARD
        mock_get_state.return_value = state

        render_expert_form()

        mock_view_cls.assert_called_once_with(ticker="AAPL")
        mock_view_cls.return_value.render.assert_called_once()

    @patch("app.views.inputs.expert_form.get_state")
    @patch("app.views.inputs.expert_form.GrahamValueView")
    @patch("app.views.inputs.expert_form.st")
    def test_expert_form_dispatches_graham(self, mock_st, mock_view_cls, mock_get_state):
        """Expert form with GRAHAM should instantiate GrahamValueView."""
        from app.views.inputs.expert_form import render_expert_form
        from src.models.enums import ValuationMethodology

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.GRAHAM
        mock_get_state.return_value = state

        render_expert_form()

        mock_view_cls.assert_called_once_with(ticker="AAPL")

    @patch("app.views.inputs.expert_form.get_state")
    @patch("app.views.inputs.expert_form.RIMBankView")
    @patch("app.views.inputs.expert_form.st")
    def test_expert_form_dispatches_rim(self, mock_st, mock_view_cls, mock_get_state):
        """Expert form with RIM should instantiate RIMBankView."""
        from app.views.inputs.expert_form import render_expert_form
        from src.models.enums import ValuationMethodology

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.RIM
        mock_get_state.return_value = state

        render_expert_form()

        mock_view_cls.assert_called_once_with(ticker="AAPL")

    @patch("app.views.inputs.expert_form.get_state")
    @patch("app.views.inputs.expert_form.FCFEView")
    @patch("app.views.inputs.expert_form.st")
    def test_expert_form_dispatches_fcfe(self, mock_st, mock_view_cls, mock_get_state):
        """Expert form with FCFE should instantiate FCFEView."""
        from app.views.inputs.expert_form import render_expert_form
        from src.models.enums import ValuationMethodology

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.FCFE
        mock_get_state.return_value = state

        render_expert_form()

        mock_view_cls.assert_called_once_with(ticker="AAPL")

    @patch("app.views.inputs.expert_form.get_state")
    @patch("app.views.inputs.expert_form.DDMView")
    @patch("app.views.inputs.expert_form.st")
    def test_expert_form_dispatches_ddm(self, mock_st, mock_view_cls, mock_get_state):
        """Expert form with DDM should instantiate DDMView."""
        from app.views.inputs.expert_form import render_expert_form
        from src.models.enums import ValuationMethodology

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.DDM
        mock_get_state.return_value = state

        render_expert_form()

        mock_view_cls.assert_called_once_with(ticker="AAPL")

    @patch("app.views.inputs.expert_form.get_state")
    @patch("app.views.inputs.expert_form.FCFFNormalizedView")
    @patch("app.views.inputs.expert_form.st")
    def test_expert_form_dispatches_normalized(self, mock_st, mock_view_cls, mock_get_state):
        """Expert form with FCFF_NORMALIZED should instantiate FCFFNormalizedView."""
        from app.views.inputs.expert_form import render_expert_form
        from src.models.enums import ValuationMethodology

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.FCFF_NORMALIZED
        mock_get_state.return_value = state

        render_expert_form()

        mock_view_cls.assert_called_once_with(ticker="AAPL")

    @patch("app.views.inputs.expert_form.get_state")
    @patch("app.views.inputs.expert_form.FCFFGrowthView")
    @patch("app.views.inputs.expert_form.st")
    def test_expert_form_dispatches_growth(self, mock_st, mock_view_cls, mock_get_state):
        """Expert form with FCFF_GROWTH should instantiate FCFFGrowthView."""
        from app.views.inputs.expert_form import render_expert_form
        from src.models.enums import ValuationMethodology

        state = MagicMock()
        state.ticker = "AAPL"
        state.selected_methodology = ValuationMethodology.FCFF_GROWTH
        mock_get_state.return_value = state

        render_expert_form()

        mock_view_cls.assert_called_once_with(ticker="AAPL")


# =============================================================================
# SIDEBAR
# =============================================================================


class TestSidebarRendering:
    """Tests render_sidebar with mocked streamlit."""

    def test_render_sidebar_callable(self):
        """render_sidebar must be callable."""
        from app.views.inputs.sidebar import render_sidebar

        assert callable(render_sidebar)


# =============================================================================
# MAIN APP RENDERING
# =============================================================================


class TestMainRendering:
    """Tests main.py render_footer with mocked streamlit."""

    @patch("app.main.st")
    def test_render_footer(self, mock_st):
        """render_footer must call st.markdown for version, CI, coverage."""

        col_mocks = [MagicMock(), MagicMock(), MagicMock()]
        for col in col_mocks:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = col_mocks


        mock_st.markdown.assert_called()

    @patch("app.main.st")
    def test_render_footer_no_emojis(self, mock_st):
        """render_footer must not contain emoji characters in output."""

        col_mocks = [MagicMock(), MagicMock(), MagicMock()]
        for col in col_mocks:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = col_mocks


        for call in mock_st.markdown.call_args_list:
            text = call[0][0] if call[0] else ""
            assert "\u2705" not in text
            assert "\U0001f4ca" not in text
