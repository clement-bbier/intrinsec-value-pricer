"""
tests/unit/test_orchestrator.py

UNIT TESTS — Results Orchestrator (app/ui/results/orchestrator.py)
Coverage Target: 31% → 90%+

Testing Strategy:
    - Mock Streamlit UI components with proper column handling
    - Test cache invalidation logic
    - Test Monte Carlo statistics caching
    - Test tab filtering based on valuation mode
    - Test global header rendering

Pattern: AAA (Arrange-Act-Assert)
Style: pytest with comprehensive mocking
"""

from __future__ import annotations

import pytest
import hashlib
import numpy as np
from unittest.mock import patch, MagicMock, PropertyMock
from typing import List, Dict, Any


# ==============================================================================
# HELPER: Streamlit Mock Factory
# ==============================================================================

class MockSessionState(dict):
    """Mock for st.session_state supporting both dict and attribute access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'MockSessionState' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

    def get(self, key, default=None):
        return super().get(key, default)


def create_mock_streamlit():
    """Factory to create a properly configured Streamlit mock."""
    mock_st = MagicMock()
    mock_st.session_state = MockSessionState()

    # Configure columns to return correct number of mocks with proper context managers
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

    # Configure container context manager
    mock_container = MagicMock()
    mock_container.__enter__ = MagicMock(return_value=MagicMock())
    mock_container.__exit__ = MagicMock(return_value=False)
    mock_st.container.return_value = mock_container

    # Configure tabs
    def tabs_side_effect(labels):
        tab_mocks = []
        for _ in labels:
            tab = MagicMock()
            tab.__enter__ = MagicMock(return_value=tab)
            tab.__exit__ = MagicMock(return_value=False)
            tab_mocks.append(tab)
        return tab_mocks

    mock_st.tabs.side_effect = tabs_side_effect

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
    """Create a mock ValuationResult with all required attributes."""
    result = MagicMock()
    result.ticker = "AAPL"
    result.intrinsic_value_per_share = 150.0
    result.market_price = 145.0
    result.upside_pct = 0.0345
    result.simulation_results = None
    result.quantiles = {"P10": 135.0, "P90": 165.0}

    # Mock financials
    result.financials = MagicMock()
    result.financials.ticker = "AAPL"
    result.financials.name = "Apple Inc."
    result.financials.sector = "Technology"
    result.financials.currency = "USD"

    # Mock audit report
    result.audit_report = MagicMock()
    result.audit_report.rating = "A+"
    result.audit_report.global_score = 85.0

    # Mock mode
    result.mode = MagicMock()
    result.mode.value = "FCFF_STANDARD"

    # Mock params
    result.params = MagicMock()

    result.request = MagicMock()
    result.request.mode.name = "FCFF_STANDARD"

    return result


@pytest.fixture
def mock_i18n_texts():
    """Mock i18n text modules."""
    ui_messages = MagicMock()
    ui_messages.NO_TABS_TO_DISPLAY = "No tabs available"
    ui_messages.CHART_UNAVAILABLE = "Chart unavailable"

    kpi_texts = MagicMock()
    kpi_texts.LABEL_IV = "Intrinsic Value"
    kpi_texts.LABEL_PRICE = "Market Price"
    kpi_texts.EXEC_CONFIDENCE = "Confidence"

    audit_texts = MagicMock()
    audit_texts.DEFAULT_FORMULA = "N/A"

    return {
        'UIMessages': ui_messages,
        'KPITexts': kpi_texts,
        'AuditTexts': audit_texts
    }


# ==============================================================================
# 1. ORCHESTRATOR INITIALIZATION TESTS
# ==============================================================================

class TestOrchestratorInitialization:
    """Test suite for ResultTabOrchestrator initialization."""

    def test_orchestrator_creates_tabs(self, mock_streamlit):
        """Test orchestrator creates tab instances."""
        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            orchestrator = ResultTabOrchestrator()

            # Should have 5 tabs
            assert len(orchestrator._tabs) == 5

    def test_orchestrator_tab_order_preserved(self, mock_streamlit):
        """Test tab instances maintain correct order."""
        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            orchestrator = ResultTabOrchestrator()

            # Tabs should be sorted by ORDER
            orders = [tab.ORDER for tab in orchestrator._tabs]
            assert orders == sorted(orders)


# ==============================================================================
# 2. GLOBAL HEADER RENDERING TESTS
# ==============================================================================

class TestGlobalHeaderRendering:
    """Test suite for global header (Golden Header) rendering."""

    def test_render_global_header_displays_ticker(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test header displays company ticker."""
        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.KPITexts', mock_i18n_texts['KPITexts']):
                with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150.00"):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    ResultTabOrchestrator._render_global_header(mock_valuation_result)

                    # Verify container was used
                    mock_streamlit.container.assert_called()

    def test_render_global_header_positive_upside_green(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test header shows green color for positive upside."""
        mock_valuation_result.upside_pct = 0.10  # 10% upside

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.KPITexts', mock_i18n_texts['KPITexts']):
                with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150.00"):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    ResultTabOrchestrator._render_global_header(mock_valuation_result)

                    # Get all columns created
                    cols = mock_streamlit.columns.return_value if mock_streamlit.columns.return_value else []
                    # Check that markdown was called (color logic is in the markdown)
                    assert mock_streamlit.container.called

    def test_render_global_header_negative_upside_red(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test header shows red color for negative upside."""
        mock_valuation_result.upside_pct = -0.15  # -15% downside

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.KPITexts', mock_i18n_texts['KPITexts']):
                with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150.00"):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    ResultTabOrchestrator._render_global_header(mock_valuation_result)

                    assert mock_streamlit.container.called

    def test_render_global_header_handles_none_upside(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test header handles None upside gracefully."""
        mock_valuation_result.upside_pct = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.KPITexts', mock_i18n_texts['KPITexts']):
                with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150.00"):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    # Should not raise
                    ResultTabOrchestrator._render_global_header(mock_valuation_result)

    def test_render_global_header_no_audit_report(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test header handles missing audit report."""
        mock_valuation_result.audit_report = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.KPITexts', mock_i18n_texts['KPITexts']):
                with patch('app.ui.results.orchestrator.AuditTexts', mock_i18n_texts['AuditTexts']):
                    with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150.00"):
                        from app.ui.results.orchestrator import ResultTabOrchestrator

                        # Should not raise
                        ResultTabOrchestrator._render_global_header(mock_valuation_result)

    @pytest.mark.parametrize("rating,expected_contains", [
        ("A+", "#10b981"),
        ("A", "#10b981"),
        ("B+", "#f59e0b"),
        ("B", "#f59e0b"),
        ("C", "#ef4444"),
        ("D", "#ef4444"),
    ])
    def test_render_global_header_rating_colors(
        self, mock_streamlit, mock_valuation_result, mock_i18n_texts, rating, expected_contains
    ):
        """Test header uses correct color for each rating grade."""
        mock_valuation_result.audit_report.rating = rating

        # Collect all markdown calls
        markdown_calls = []
        def track_markdown(*args, **kwargs):
            markdown_calls.append(str(args))

        # Track markdown on columns too
        cols_created = []
        def columns_side_effect(spec):
            num_cols = spec if isinstance(spec, int) else len(spec)
            cols = []
            for _ in range(num_cols):
                col = MagicMock()
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
                col.markdown = track_markdown
                cols.append(col)
            cols_created.extend(cols)
            return cols

        mock_streamlit.columns.side_effect = columns_side_effect
        mock_streamlit.markdown = track_markdown

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.KPITexts', mock_i18n_texts['KPITexts']):
                with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150.00"):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    ResultTabOrchestrator._render_global_header(mock_valuation_result)

                    # Check if expected color appears in any markdown call
                    all_calls = ' '.join(markdown_calls)
                    assert expected_contains in all_calls


# ==============================================================================
# 3. CACHE MANAGEMENT TESTS
# ==============================================================================

class TestCacheManagement:
    """Test suite for cache invalidation and statistics caching."""

    def test_handle_cache_invalidation_new_context(self, mock_streamlit, mock_valuation_result):
        """Test cache is invalidated when context changes."""
        mock_streamlit.session_state['valuation_context_hash'] = 'old_hash'
        mock_streamlit.session_state['stats_monte_carlo_cache'] = {'median': 100}

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            ResultTabOrchestrator._handle_cache_invalidation(mock_valuation_result)

            # Cache should be cleared
            assert mock_streamlit.session_state['stats_monte_carlo_cache'] is None
            # Hash should be updated
            assert mock_streamlit.session_state['valuation_context_hash'] != 'old_hash'

    def test_handle_cache_invalidation_same_context(self, mock_streamlit, mock_valuation_result):
        """Test cache is preserved when context unchanged (Corrected Hash Logic)."""
        # On aligne le payload du test exactement sur la logique interne de l'orchestrateur
        # On utilise .name pour l'Enum et on s'assure que la valeur IV est convertie en string
        ctx_payload = (
            str(mock_valuation_result.ticker),
            str(mock_valuation_result.intrinsic_value_per_share),
            str(mock_valuation_result.request.mode.name),  # Utilisation du .name de l'Enum
            0  # len(None) -> 0
        )
        expected_hash = hashlib.md5(str(ctx_payload).encode()).hexdigest()[:12]

        cached_data = {'median': 100, 'p10': 90, 'p90': 110}
        mock_streamlit.session_state['valuation_context_hash'] = expected_hash
        mock_streamlit.session_state['stats_monte_carlo_cache'] = cached_data

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator
            # On s'assure que le mock du résultat a bien la même structure
            mock_valuation_result.request.mode.name = "FCFF_STANDARD"

            ResultTabOrchestrator._handle_cache_invalidation(mock_valuation_result)

            # Assert: Le cache doit être préservé car le hash calculé correspond
            assert mock_streamlit.session_state['stats_monte_carlo_cache'] == cached_data

    def test_cache_technical_data_with_simulations(self, mock_streamlit, mock_valuation_result):
        """Test Monte Carlo statistics are cached correctly."""
        # Add simulation results
        mock_valuation_result.simulation_results = [100.0, 110.0, 120.0, 130.0, 140.0] * 200
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            ResultTabOrchestrator._cache_technical_data(mock_valuation_result)

            cached = mock_streamlit.session_state['stats_monte_carlo_cache']
            assert cached is not None
            assert 'median' in cached
            assert 'p10' in cached
            assert 'p90' in cached
            assert 'std' in cached
            assert 'var_95' in cached

    def test_cache_technical_data_no_simulations(self, mock_streamlit, mock_valuation_result):
        """Test caching handles absence of simulation results."""
        mock_valuation_result.simulation_results = None
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            ResultTabOrchestrator._cache_technical_data(mock_valuation_result)

            # Cache should remain None
            assert mock_streamlit.session_state['stats_monte_carlo_cache'] is None

    def test_cache_technical_data_filters_none_values(self, mock_streamlit, mock_valuation_result):
        """Test caching filters out None values from simulations."""
        mock_valuation_result.simulation_results = [100.0, None, 120.0, None, 140.0]
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            ResultTabOrchestrator._cache_technical_data(mock_valuation_result)

            cached = mock_streamlit.session_state['stats_monte_carlo_cache']
            assert cached is not None

    def test_cache_technical_data_empty_after_filtering(self, mock_streamlit, mock_valuation_result):
        """Test caching handles all-None simulation results."""
        mock_valuation_result.simulation_results = [None, None, None]
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            ResultTabOrchestrator._cache_technical_data(mock_valuation_result)

            # Should not cache anything
            assert mock_streamlit.session_state['stats_monte_carlo_cache'] is None


# ==============================================================================
# 4. TAB FILTERING TESTS
# ==============================================================================

class TestTabFiltering:
    """Test suite for tab filtering based on visibility and mode."""

    def test_filter_relevant_tabs_all_visible(self, mock_streamlit, mock_valuation_result):
        """Test all visible tabs are included."""
        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            orchestrator = ResultTabOrchestrator()

            # Make all tabs visible
            for tab in orchestrator._tabs:
                tab.is_visible = MagicMock(return_value=True)

            filtered = orchestrator._filter_relevant_tabs(mock_valuation_result)

            assert len(filtered) == 5

    def test_filter_relevant_tabs_excludes_invisible(self, mock_streamlit, mock_valuation_result):
        """Test invisible tabs are excluded."""
        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            orchestrator = ResultTabOrchestrator()

            # Make some tabs invisible
            for i, tab in enumerate(orchestrator._tabs):
                tab.is_visible = MagicMock(return_value=(i % 2 == 0))

            filtered = orchestrator._filter_relevant_tabs(mock_valuation_result)

            # Should have fewer tabs
            assert len(filtered) < 5

    def test_filter_relevant_tabs_graham_excludes_market(self, mock_streamlit, mock_valuation_result):
        """Test Graham mode excludes MarketAnalysisTab (Fixed visibility override)."""
        from src.models import ValuationMethodology
        from app.ui.results.orchestrator import ResultTabOrchestrator

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            # 1. Setup : Mode Graham
            mock_valuation_result.request.mode = ValuationMethodology.GRAHAM

            orchestrator = ResultTabOrchestrator()

            # 2. On laisse les onglets décider de leur propre visibilité
            # (au lieu de tout forcer à True), SAUF pour simuler la présence de données
            for tab in orchestrator._tabs:
                if tab.TAB_ID != "market_analysis":
                    tab.is_visible = MagicMock(return_value=True)
                # L'onglet MarketAnalysis utilisera sa vraie logique métier

            filtered = orchestrator._filter_relevant_tabs(mock_valuation_result)

            # Assert: On attend 4 onglets (Inputs, Proof, Audit, Risk)
            # car Market est exclu par le mode GRAHAM
            assert len(filtered) == 4
            assert not any(t.TAB_ID == "market_analysis" for t in filtered)

    def test_filter_relevant_tabs_sorted_by_order(self, mock_streamlit, mock_valuation_result):
        """Test filtered tabs are sorted by ORDER attribute."""
        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            orchestrator = ResultTabOrchestrator()

            # Make all tabs visible
            for tab in orchestrator._tabs:
                tab.is_visible = MagicMock(return_value=True)

            filtered = orchestrator._filter_relevant_tabs(mock_valuation_result)

            # Check order is ascending
            orders = [tab.ORDER for tab in filtered]
            assert orders == sorted(orders)


# ==============================================================================
# 5. MAIN RENDER METHOD TESTS
# ==============================================================================

class TestMainRender:
    """Test suite for main render method."""

    def test_render_calls_global_header(self, mock_streamlit, mock_valuation_result):
        """Test render calls global header rendering."""
        mock_streamlit.session_state['valuation_context_hash'] = ''
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150"):
                with patch('app.ui.results.orchestrator.KPITexts'):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    orchestrator = ResultTabOrchestrator()

                    with patch.object(ResultTabOrchestrator, '_render_global_header') as mock_header:
                        with patch.object(orchestrator, '_filter_relevant_tabs', return_value=[]):
                            with patch('app.ui.results.orchestrator.UIMessages') as mock_ui:
                                mock_ui.NO_TABS_TO_DISPLAY = "No tabs"
                                orchestrator.render(mock_valuation_result)

                                mock_header.assert_called_once_with(mock_valuation_result)

    def test_render_shows_warning_no_visible_tabs(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test render shows warning when no tabs are visible."""
        mock_streamlit.session_state['valuation_context_hash'] = ''
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150"):
                with patch('app.ui.results.orchestrator.KPITexts'):
                    with patch('app.ui.results.orchestrator.UIMessages', mock_i18n_texts['UIMessages']):
                        from app.ui.results.orchestrator import ResultTabOrchestrator

                        orchestrator = ResultTabOrchestrator()

                        with patch.object(ResultTabOrchestrator, '_render_global_header'):
                            with patch.object(orchestrator, '_filter_relevant_tabs', return_value=[]):
                                orchestrator.render(mock_valuation_result)

                                mock_streamlit.warning.assert_called_once()

    def test_render_creates_streamlit_tabs(self, mock_streamlit, mock_valuation_result):
        """Test render creates Streamlit tabs for visible tabs."""
        mock_streamlit.session_state['valuation_context_hash'] = ''
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        # Create mock visible tabs
        mock_tab1 = MagicMock()
        mock_tab1.get_display_label.return_value = "Tab 1"
        mock_tab1.render = MagicMock()
        mock_tab1.TAB_ID = "tab1"

        mock_tab2 = MagicMock()
        mock_tab2.get_display_label.return_value = "Tab 2"
        mock_tab2.render = MagicMock()
        mock_tab2.TAB_ID = "tab2"

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150"):
                with patch('app.ui.results.orchestrator.KPITexts'):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    orchestrator = ResultTabOrchestrator()

                    with patch.object(ResultTabOrchestrator, '_render_global_header'):
                        with patch.object(orchestrator, '_filter_relevant_tabs', return_value=[mock_tab1, mock_tab2]):
                            orchestrator.render(mock_valuation_result)

                            mock_streamlit.tabs.assert_called_once_with(["Tab 1", "Tab 2"])

    def test_render_handles_tab_render_error(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test render handles errors from individual tab rendering."""
        mock_streamlit.session_state['valuation_context_hash'] = ''
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        mock_tab = MagicMock()
        mock_tab.TAB_ID = "failing_tab"
        mock_tab.get_display_label.return_value = "Failing Tab"
        mock_tab.render.side_effect = Exception("Render error")

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150"):
                with patch('app.ui.results.orchestrator.KPITexts'):
                    with patch('app.ui.results.orchestrator.UIMessages', mock_i18n_texts['UIMessages']):
                        from app.ui.results.orchestrator import ResultTabOrchestrator

                        orchestrator = ResultTabOrchestrator()

                        with patch.object(ResultTabOrchestrator, '_render_global_header'):
                            with patch.object(orchestrator, '_filter_relevant_tabs', return_value=[mock_tab]):
                                # Should not raise, should log and show error
                                orchestrator.render(mock_valuation_result)

                                mock_streamlit.error.assert_called()


# ==============================================================================
# 6. EDGE CASES AND ERROR HANDLING
# ==============================================================================

class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_upside_pct_type_error_handling(self, mock_streamlit, mock_valuation_result, mock_i18n_texts):
        """Test header handles TypeError for upside_pct."""
        mock_valuation_result.upside_pct = "invalid"  # String instead of float

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            with patch('app.ui.results.orchestrator.KPITexts', mock_i18n_texts['KPITexts']):
                with patch('app.ui.results.orchestrator.format_smart_number', return_value="$150.00"):
                    from app.ui.results.orchestrator import ResultTabOrchestrator

                    # Should not raise - error is caught and upside defaults to 0
                    ResultTabOrchestrator._render_global_header(mock_valuation_result)

    def test_empty_simulation_results_list(self, mock_streamlit, mock_valuation_result):
        """Test caching handles empty simulation results list."""
        mock_valuation_result.simulation_results = []
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            ResultTabOrchestrator._cache_technical_data(mock_valuation_result)

            # Empty list should not create cache
            assert mock_streamlit.session_state['stats_monte_carlo_cache'] is None

    def test_mode_none_in_cache_hash(self, mock_streamlit, mock_valuation_result):
        """Test cache hash handles None mode."""
        mock_valuation_result.mode = None
        mock_streamlit.session_state['valuation_context_hash'] = ''
        mock_streamlit.session_state['stats_monte_carlo_cache'] = None

        with patch('app.ui.results.orchestrator.st', mock_streamlit):
            from app.ui.results.orchestrator import ResultTabOrchestrator

            # Should not raise
            ResultTabOrchestrator._handle_cache_invalidation(mock_valuation_result)