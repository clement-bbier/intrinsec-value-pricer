"""
tests/unit/test_audit_report.py

UNIT TESTS — Audit Report Tab (app/ui/results/core/audit_report.py)
Coverage Target: 19% → 90%+

Testing Strategy:
    - Test tab visibility logic
    - Test audit step card rendering with proper column mocking
    - Test rating color mapping
    - Test critical alert handling

Pattern: AAA (Arrange-Act-Assert)
Style: pytest with comprehensive mocking
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from typing import Any


# ==============================================================================
# HELPER: Streamlit Mock Factory
# ==============================================================================

def create_mock_streamlit():
    """Factory to create a properly configured Streamlit mock."""
    mock_st = MagicMock()

    def columns_side_effect(spec):
        num_cols = spec if isinstance(spec, int) else len(spec)
        cols = []
        for _ in range(num_cols):
            col = MagicMock()
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
            cols.append(col)
        return cols

    mock_st.columns.side_effect = columns_side_effect

    mock_container = MagicMock()
    mock_container.__enter__ = MagicMock(return_value=MagicMock())
    mock_container.__exit__ = MagicMock(return_value=False)
    mock_st.container.return_value = mock_container

    return mock_st


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_streamlit():
    """Global Streamlit mock fixture."""
    return create_mock_streamlit()


@pytest.fixture
def mock_valuation_result():
    """Create mock ValuationResult with audit report."""
    result = MagicMock()
    result.ticker = "AAPL"

    result.audit_report = MagicMock()
    result.audit_report.rating = "A+"
    result.audit_report.global_score = 85.0
    result.audit_report.audit_coverage = 0.95
    result.audit_report.audit_steps = []

    return result


@pytest.fixture
def mock_audit_step():
    """Create mock AuditStep."""
    step = MagicMock()
    step.step_key = "test_step"
    step.label = "Test Step"
    step.verdict = True
    step.rule_formula = r"x > 0"
    step.evidence = "Test evidence"
    step.indicator_value = 0.85
    return step


@pytest.fixture
def mock_i18n_texts():
    """Mock i18n audit texts."""
    audit_texts = MagicMock()
    audit_texts.NO_REPORT = "No audit report available"
    audit_texts.CHECK_TABLE = "Audit check table"
    audit_texts.COVERAGE = "Coverage"
    audit_texts.H_INDICATOR = "Tests"
    audit_texts.GLOBAL_SCORE = "Global score: {score}"
    audit_texts.STATUS_ALERT = "Alert"
    audit_texts.STATUS_OK = "OK"
    audit_texts.CRITICAL_VIOLATION_MSG = "{count} critical violations"
    audit_texts.AUDIT_NOTES_EXPANDER = "Detailed Audit Notes"
    audit_texts.H_RULE = "Rule"
    audit_texts.H_EVIDENCE = "Evidence"
    audit_texts.H_VERDICT = "Verdict"
    audit_texts.DEFAULT_FORMULA = "N/A"
    audit_texts.INTERNAL_CALC = "Internal calculation"

    pillar_labels = MagicMock()
    pillar_labels.PILLAR_3_AUDIT = "Reliability Audit"

    return {
        'AuditTexts': audit_texts,
        'PillarLabels': pillar_labels
    }


# ==============================================================================
# 1. TAB VISIBILITY TESTS
# ==============================================================================

class TestTabVisibility:
    """Test suite for tab visibility logic."""

    def test_is_visible_with_audit_report(self, mock_streamlit, mock_valuation_result):
        """Test tab is visible when audit report exists."""
        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            from app.ui.results.core.audit_report import AuditReportTab

            tab = AuditReportTab()
            result = tab.is_visible(mock_valuation_result)

            assert result is True

    def test_is_visible_without_audit_report(self, mock_streamlit, mock_valuation_result):
        """Test tab is not visible when no audit report."""
        mock_valuation_result.audit_report = None

        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            from app.ui.results.core.audit_report import AuditReportTab

            tab = AuditReportTab()
            result = tab.is_visible(mock_valuation_result)

            assert result is False


# ==============================================================================
# 2. TAB RENDERING TESTS
# ==============================================================================

class TestTabRendering:
    """Test suite for main tab rendering."""

    def test_render_shows_info_when_no_report(
        self, mock_streamlit, mock_valuation_result, mock_i18n_texts
    ):
        """Test render shows info message when no audit report."""
        mock_valuation_result.audit_report = None

        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            with patch('app.ui.results.core.audit_report.AuditTexts', mock_i18n_texts['AuditTexts']):
                with patch('app.ui.results.core.audit_report.PillarLabels', mock_i18n_texts['PillarLabels']):
                    from app.ui.results.core.audit_report import AuditReportTab

                    tab = AuditReportTab()
                    tab.render(mock_valuation_result)

                    mock_streamlit.info.assert_called_once()

    def test_render_full_report_workflow(
        self, mock_streamlit, mock_valuation_result, mock_audit_step, mock_i18n_texts
    ):
        """Test render displays full audit report workflow."""
        # Configure the audit step with proper severity mock
        mock_audit_step.severity = MagicMock()
        mock_audit_step.severity.value = "WARNING"
        mock_valuation_result.audit_report.audit_steps = [mock_audit_step]

        # Create mock for AuditSeverity enum
        mock_audit_severity = MagicMock()
        mock_critical = MagicMock()
        mock_critical.value = "CRITICAL"
        mock_audit_severity.CRITICAL = mock_critical

        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            with patch('app.ui.results.core.audit_report.AuditTexts', mock_i18n_texts['AuditTexts']):
                with patch('app.ui.results.core.audit_report.PillarLabels', mock_i18n_texts['PillarLabels']):
                    with patch('app.ui.results.core.audit_report.render_audit_reliability_gauge'):
                        with patch('app.ui.results.core.audit_report.atom_kpi_metric'):
                            with patch('app.ui.results.core.audit_report.get_step_metadata', return_value={'label': 'Test', 'description': 'Desc'}):
                                with patch('app.ui.results.core.audit_report.AuditSeverity', mock_audit_severity):
                                    from app.ui.results.core.audit_report import AuditReportTab

                                    tab = AuditReportTab()
                                    tab.render(mock_valuation_result)

                                    mock_streamlit.markdown.assert_called()


# ==============================================================================
# 3. AUDIT STEP CARD RENDERING TESTS
# ==============================================================================

class TestAuditStepCard:
    """Test suite for individual audit step card rendering."""

    def test_card_renders_passing_step(self, mock_streamlit, mock_audit_step, mock_i18n_texts):
        """Test card renders correctly for passing step."""
        mock_audit_step.verdict = True
        mock_audit_step.severity = MagicMock()
        mock_audit_step.severity.value = "NORMAL"

        # Create mock for AuditSeverity
        mock_audit_severity = MagicMock()
        mock_critical = MagicMock()
        mock_critical.value = "CRITICAL"
        mock_audit_severity.CRITICAL = mock_critical

        markdown_calls = []
        def track_markdown(*args, **kwargs):
            markdown_calls.append(str(args))

        def columns_side_effect(spec):
            num_cols = spec if isinstance(spec, int) else len(spec)
            cols = []
            for _ in range(num_cols):
                col = MagicMock()
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
                col.markdown = track_markdown
                cols.append(col)
            return cols

        mock_streamlit.columns.side_effect = columns_side_effect
        mock_streamlit.markdown = track_markdown

        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            with patch('app.ui.results.core.audit_report.AuditTexts', mock_i18n_texts['AuditTexts']):
                with patch('app.ui.results.core.audit_report.get_step_metadata', return_value={'label': 'Test', 'description': 'Desc'}):
                    with patch('app.ui.results.core.audit_report.AuditSeverity', mock_audit_severity):
                        from app.ui.results.core.audit_report import AuditReportTab

                        AuditReportTab._render_audit_step_card(mock_audit_step)

                        # Check green color for passing
                        all_calls = ' '.join(markdown_calls)
                        assert '#10b981' in all_calls

    def test_card_renders_critical_failure(self, mock_streamlit, mock_audit_step, mock_i18n_texts):
        """Test card renders correctly for critical failure."""
        mock_audit_step.verdict = False

        # Create a severity object that will compare equal to CRITICAL
        mock_severity = MagicMock()
        mock_severity.value = "CRITICAL"
        mock_audit_step.severity = mock_severity

        # Create AuditSeverity mock where CRITICAL equals our severity
        mock_audit_severity = MagicMock()
        mock_audit_severity.CRITICAL = mock_severity  # Same object for equality

        markdown_calls = []
        def track_markdown(*args, **kwargs):
            markdown_calls.append(str(args))

        def columns_side_effect(spec):
            num_cols = spec if isinstance(spec, int) else len(spec)
            cols = []
            for _ in range(num_cols):
                col = MagicMock()
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
                col.markdown = track_markdown
                cols.append(col)
            return cols

        mock_streamlit.columns.side_effect = columns_side_effect
        mock_streamlit.markdown = track_markdown

        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            with patch('app.ui.results.core.audit_report.AuditTexts', mock_i18n_texts['AuditTexts']):
                with patch('app.ui.results.core.audit_report.get_step_metadata', return_value={'label': 'Test', 'description': 'Desc'}):
                    with patch('app.ui.results.core.audit_report.AuditSeverity', mock_audit_severity):
                        from app.ui.results.core.audit_report import AuditReportTab

                        AuditReportTab._render_audit_step_card(mock_audit_step)

                        # Check red color for critical failure
                        all_calls = ' '.join(markdown_calls)
                        assert '#ef4444' in all_calls

    def test_card_renders_warning_failure(self, mock_streamlit, mock_audit_step, mock_i18n_texts):
        """Test card renders correctly for warning failure."""
        mock_audit_step.verdict = False

        # Create a severity that is NOT equal to CRITICAL
        mock_warning_severity = MagicMock()
        mock_warning_severity.value = "WARNING"
        mock_audit_step.severity = mock_warning_severity

        mock_critical_severity = MagicMock()
        mock_critical_severity.value = "CRITICAL"

        mock_audit_severity = MagicMock()
        mock_audit_severity.CRITICAL = mock_critical_severity  # Different object

        markdown_calls = []
        def track_markdown(*args, **kwargs):
            markdown_calls.append(str(args))

        def columns_side_effect(spec):
            num_cols = spec if isinstance(spec, int) else len(spec)
            cols = []
            for _ in range(num_cols):
                col = MagicMock()
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
                col.markdown = track_markdown
                cols.append(col)
            return cols

        mock_streamlit.columns.side_effect = columns_side_effect
        mock_streamlit.markdown = track_markdown

        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            with patch('app.ui.results.core.audit_report.AuditTexts', mock_i18n_texts['AuditTexts']):
                with patch('app.ui.results.core.audit_report.get_step_metadata', return_value={'label': 'Test', 'description': 'Desc'}):
                    with patch('app.ui.results.core.audit_report.AuditSeverity', mock_audit_severity):
                        from app.ui.results.core.audit_report import AuditReportTab

                        AuditReportTab._render_audit_step_card(mock_audit_step)

                        # Check amber/yellow color for warning
                        all_calls = ' '.join(markdown_calls)
                        assert '#f59e0b' in all_calls

    def test_indicator_formatting_percentage(self, mock_streamlit, mock_audit_step, mock_i18n_texts):
        """Test indicator value is formatted as percentage when <= 1."""
        mock_audit_step.verdict = True
        mock_audit_step.indicator_value = 0.85
        mock_audit_step.severity = MagicMock()
        mock_audit_step.severity.value = "NORMAL"

        mock_audit_severity = MagicMock()
        mock_audit_severity.CRITICAL = MagicMock()

        markdown_calls = []
        def track_markdown(*args, **kwargs):
            markdown_calls.append(str(args))

        def columns_side_effect(spec):
            num_cols = spec if isinstance(spec, int) else len(spec)
            cols = []
            for _ in range(num_cols):
                col = MagicMock()
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
                col.markdown = track_markdown
                cols.append(col)
            return cols

        mock_streamlit.columns.side_effect = columns_side_effect
        mock_streamlit.markdown = track_markdown

        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            with patch('app.ui.results.core.audit_report.AuditTexts', mock_i18n_texts['AuditTexts']):
                with patch('app.ui.results.core.audit_report.get_step_metadata', return_value={'label': 'Test', 'description': 'Desc'}):
                    with patch('app.ui.results.core.audit_report.AuditSeverity', mock_audit_severity):
                        from app.ui.results.core.audit_report import AuditReportTab

                        AuditReportTab._render_audit_step_card(mock_audit_step)

                        all_calls = ' '.join(markdown_calls)
                        # Should format as percentage
                        assert '85' in all_calls or '%' in all_calls


# ==============================================================================
# 4. TAB ATTRIBUTES TESTS
# ==============================================================================

class TestTabAttributes:
    """Test suite for tab class attributes."""

    def test_tab_has_required_attributes(self, mock_streamlit):
        """Test tab class has all required attributes."""
        with patch('app.ui.results.core.audit_report.st', mock_streamlit):
            from app.ui.results.core.audit_report import AuditReportTab

            tab = AuditReportTab()

            assert hasattr(tab, 'TAB_ID')
            assert hasattr(tab, 'LABEL')
            assert hasattr(tab, 'ORDER')
            assert hasattr(tab, 'IS_CORE')

            assert tab.TAB_ID == "audit_report"
            assert tab.ORDER == 3
            assert tab.IS_CORE is True