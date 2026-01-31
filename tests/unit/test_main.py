"""
tests/unit/test_main.py

UNIT TESTS — Main Application Entry Point (app/main.py)
Coverage Target: 28% → 90%+

Testing Strategy:
    - Mock ALL Streamlit components to control UI behavior
    - Test session state management
    - Test sidebar rendering functions
    - Test mode selection and workflow triggering
    - Test onboarding guide rendering

Pattern: AAA (Arrange-Act-Assert)
Style: pytest with fixtures and comprehensive mocking
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from typing import Dict, Any


# ==============================================================================
# HELPER: Streamlit Session State Mock
# ==============================================================================

class MockSessionState(dict):
    """
    Mock for st.session_state that supports both dict and attribute access.
    """
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
            raise AttributeError(f"'MockSessionState' object has no attribute '{key}'")


def create_mock_streamlit():
    """Factory to create a properly configured Streamlit mock."""
    mock_st = MagicMock()
    mock_st.session_state = MockSessionState()

    def columns_side_effect(spec):
        if isinstance(spec, int):
            return [MagicMock() for _ in range(spec)]
        elif isinstance(spec, (list, tuple)):
            return [MagicMock() for _ in spec]
        return [MagicMock(), MagicMock()]

    mock_st.columns.side_effect = columns_side_effect

    mock_st.sidebar.__enter__ = MagicMock(return_value=MagicMock())
    mock_st.sidebar.__exit__ = MagicMock(return_value=False)

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
def mock_valuation_mode():
    """Mock ValuationMode enum."""
    mode = MagicMock()
    mode.value = "FCFF_STANDARD"
    mode.supports_monte_carlo = True
    return mode


@pytest.fixture
def mock_i18n_texts():
    """Mock all i18n text modules."""
    common = MagicMock()
    common.APP_TITLE = "Intrinsic Value Pricer"
    common.DEFAULT_TICKER = "AAPL"
    common.RUN_BUTTON = "Run Analysis"
    common.DEVELOPED_BY = "Developed by"
    common.AUTHOR_NAME = "Clément Barbier"

    sidebar = MagicMock()
    sidebar.SEC_1_COMPANY = "Company Selection"
    sidebar.TICKER_LABEL = "Ticker Symbol"
    sidebar.SEC_2_METHODOLOGY = "Methodology"
    sidebar.METHOD_LABEL = "Select Method"
    sidebar.SEC_3_SOURCE = "Data Source"
    sidebar.STRATEGY_LABEL = "Input Strategy"
    sidebar.SOURCE_OPTIONS = ["Automated", "Expert Mode"]
    sidebar.SEC_4_HORIZON = "Projection Horizon"
    sidebar.YEARS_LABEL = "Projection Years"

    onboarding = MagicMock()
    onboarding.INTRO_INFO = "Welcome"
    onboarding.COMPLIANCE_BODY = "Disclaimer"
    onboarding.TITLE_METHODS = "Methodologies"
    onboarding.DESC_METHODS = "Available methods"
    onboarding.MODEL_DCF_TITLE = "DCF"
    onboarding.MODEL_DCF_DESC = "Discounted Cash Flow"
    onboarding.MODEL_EQUITY_TITLE = "Equity"
    onboarding.MODEL_EQUITY_DESC = "Direct Equity"
    onboarding.MODEL_RIM_TITLE = "RIM"
    onboarding.MODEL_RIM_DESC = "Residual Income"
    onboarding.MODEL_GRAHAM_TITLE = "Graham"
    onboarding.MODEL_GRAHAM_DESC = "Benjamin Graham"
    onboarding.TITLE_PROCESS = "Process"
    onboarding.STRATEGY_ACQUISITION_TITLE = "Auto"
    onboarding.STRATEGY_ACQUISITION_DESC = "Automated data"
    onboarding.STRATEGY_MANUAL_TITLE = "Manual"
    onboarding.STRATEGY_MANUAL_DESC = "Expert input"
    onboarding.STRATEGY_FALLBACK_TITLE = "Fallback"
    onboarding.STRATEGY_FALLBACK_DESC = "Hybrid mode"
    onboarding.TITLE_RESULTS = "Results"
    onboarding.DESC_RESULTS = "Five pillars"
    onboarding.TAB_1_TITLE = "Inputs"
    onboarding.TAB_1_DESC = "Data summary"
    onboarding.TAB_2_TITLE = "Calculation"
    onboarding.TAB_2_DESC = "Glass box"
    onboarding.TAB_3_TITLE = "Audit"
    onboarding.TAB_3_DESC = "Reliability"
    onboarding.TAB_4_TITLE = "Risk"
    onboarding.TAB_4_DESC = "Monte Carlo"
    onboarding.TAB_5_TITLE = "Market"
    onboarding.TAB_5_DESC = "Peer analysis"
    onboarding.DIAGNOSTIC_HEADER = "Diagnostics"
    onboarding.DIAGNOSTIC_BLOQUANT = "Critical"
    onboarding.DIAGNOSTIC_WARN = "Warning"
    onboarding.DIAGNOSTIC_INFO = "Info"

    feedback = MagicMock()
    feedback.TICKER_REQUIRED_SIDEBAR = "Please enter a ticker"
    feedback.TICKER_INVALID = "Invalid ticker"

    return {
        'CommonTexts': common,
        'SidebarTexts': sidebar,
        'OnboardingTexts': onboarding,
        'FeedbackMessages': feedback
    }


# ==============================================================================
# 1. SESSION STATE MANAGEMENT TESTS
# ==============================================================================

class TestSessionStateManagement:
    """Test suite for session state initialization and management."""

    def test_init_session_state_creates_defaults(self, mock_streamlit):
        """Test that session state is initialized with default values."""
        with patch('app.main.st', mock_streamlit):
            from app.main import _init_session_state

            _init_session_state()

            assert 'active_request' in mock_streamlit.session_state
            assert 'last_config' in mock_streamlit.session_state
            assert mock_streamlit.session_state['active_request'] is None
            assert mock_streamlit.session_state['last_config'] == ""

    def test_init_session_state_preserves_existing(self, mock_streamlit):
        """Test that existing session state values are preserved."""
        mock_streamlit.session_state['active_request'] = 'existing_request'
        mock_streamlit.session_state['last_config'] = 'existing_config'

        with patch('app.main.st', mock_streamlit):
            from app.main import _init_session_state

            _init_session_state()

            assert mock_streamlit.session_state['active_request'] == 'existing_request'
            assert mock_streamlit.session_state['last_config'] == 'existing_config'

    def test_reset_on_config_change_resets_when_changed(self, mock_streamlit):
        """Test that active request is reset when config changes."""
        mock_streamlit.session_state['active_request'] = MagicMock()
        mock_streamlit.session_state['last_config'] = 'old_config'

        with patch('app.main.st', mock_streamlit):
            from app.main import _reset_on_config_change

            _reset_on_config_change('new_config')

            assert mock_streamlit.session_state.active_request is None
            assert mock_streamlit.session_state.last_config == 'new_config'

    def test_reset_on_config_change_preserves_when_same(self, mock_streamlit):
        """Test that active request is preserved when config unchanged."""
        existing_request = MagicMock()
        mock_streamlit.session_state['active_request'] = existing_request
        mock_streamlit.session_state['last_config'] = 'same_config'

        with patch('app.main.st', mock_streamlit):
            from app.main import _reset_on_config_change

            _reset_on_config_change('same_config')

            assert mock_streamlit.session_state.active_request == existing_request

    def test_set_active_request_triggers_rerun(self, mock_streamlit):
        """Test that setting active request triggers UI rerun."""
        mock_streamlit.session_state['active_request'] = None
        mock_request = MagicMock()

        with patch('app.main.st', mock_streamlit):
            from app.main import _set_active_request

            _set_active_request(mock_request)

            assert mock_streamlit.session_state.active_request == mock_request
            mock_streamlit.rerun.assert_called_once()


# ==============================================================================
# 2. PAGE SETUP TESTS
# ==============================================================================

class TestPageSetup:
    """Test suite for page configuration."""

    def test_setup_page_configures_streamlit(self, mock_streamlit, mock_i18n_texts):
        """Test that page is configured with correct parameters."""
        with patch('app.main.st', mock_streamlit):
            with patch('app.main.CommonTexts', mock_i18n_texts['CommonTexts']):
                with patch('app.main.inject_institutional_design') as mock_inject:
                    from app.main import _setup_page

                    _setup_page()

                    mock_streamlit.set_page_config.assert_called_once()
                    call_kwargs = mock_streamlit.set_page_config.call_args.kwargs
                    assert call_kwargs['page_title'] == "Intrinsic Value Pricer"
                    assert call_kwargs['layout'] == "wide"
                    mock_inject.assert_called_once()


# ==============================================================================
# 3. SIDEBAR RENDERING TESTS
# ==============================================================================

class TestSidebarRendering:
    """Test suite for sidebar component rendering."""

    def test_render_sidebar_ticker_returns_uppercase(self, mock_streamlit, mock_i18n_texts):
        """Test ticker input is sanitized to uppercase."""
        mock_streamlit.text_input.return_value = "  aapl  "

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.SidebarTexts', mock_i18n_texts['SidebarTexts']):
                with patch('app.main._DEFAULT_TICKER', 'AAPL'):
                    from app.main import _render_sidebar_ticker

                    result = _render_sidebar_ticker()

                    assert result == "AAPL"

    def test_render_sidebar_ticker_handles_empty(self, mock_streamlit, mock_i18n_texts):
        """Test empty ticker input is handled."""
        mock_streamlit.text_input.return_value = "   "

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.SidebarTexts', mock_i18n_texts['SidebarTexts']):
                with patch('app.main._DEFAULT_TICKER', 'AAPL'):
                    from app.main import _render_sidebar_ticker

                    result = _render_sidebar_ticker()

                    assert result == ""

    def test_render_sidebar_methodology_returns_mode(self, mock_streamlit, mock_i18n_texts):
        """Test methodology selector returns correct ValuationMode."""
        mock_mode = MagicMock()
        mock_mode.value = "FCFF_STANDARD"

        display_names = {mock_mode: "DCF - Standard"}
        mock_streamlit.selectbox.return_value = "DCF - Standard"

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.SidebarTexts', mock_i18n_texts['SidebarTexts']):
                with patch('app.main.VALUATION_DISPLAY_NAMES', display_names):
                    from app.main import _render_sidebar_methodology

                    result = _render_sidebar_methodology()

                    assert result == mock_mode

    def test_render_sidebar_source_returns_expert_true(self, mock_streamlit, mock_i18n_texts):
        """Test source selector returns True for expert mode."""
        mock_streamlit.radio.return_value = "Expert Mode"

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.SidebarTexts', mock_i18n_texts['SidebarTexts']):
                from app.main import _render_sidebar_source

                result = _render_sidebar_source()

                assert result is True

    def test_render_sidebar_source_returns_expert_false(self, mock_streamlit, mock_i18n_texts):
        """Test source selector returns False for automated mode."""
        mock_streamlit.radio.return_value = "Automated"

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.SidebarTexts', mock_i18n_texts['SidebarTexts']):
                from app.main import _render_sidebar_source

                result = _render_sidebar_source()

                assert result is False

    def test_render_sidebar_auto_options_returns_dict(self, mock_streamlit, mock_i18n_texts):
        """Test auto options returns correct dictionary structure."""
        mock_streamlit.slider.return_value = 7
        mock_mode = MagicMock()

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.SidebarTexts', mock_i18n_texts['SidebarTexts']):
                with patch('app.main._MIN_PROJECTION_YEARS', 1):
                    with patch('app.main._MAX_PROJECTION_YEARS', 15):
                        with patch('app.main._DEFAULT_PROJECTION_YEARS', 5):
                            with patch('app.main._DEFAULT_MC_SIMULATIONS', 10000):
                                from app.main import _render_sidebar_auto_options

                                result = _render_sidebar_auto_options(mock_mode)

                                assert result['years'] == 7
                                assert result['enable_mc'] is False
                                assert 'mc_sims' in result

    def test_render_sidebar_footer_renders_html(self, mock_streamlit, mock_i18n_texts):
        """Test footer renders with author information."""
        with patch('app.main.st', mock_streamlit):
            with patch('app.main.CommonTexts', mock_i18n_texts['CommonTexts']):
                from app.main import _render_sidebar_footer

                _render_sidebar_footer()

                mock_streamlit.markdown.assert_called_once()


# ==============================================================================
# 4. ONBOARDING GUIDE TESTS
# ==============================================================================

class TestOnboardingGuide:
    """Test suite for onboarding guide rendering."""

    def test_render_onboarding_guide_renders_sections(self, mock_streamlit, mock_i18n_texts):
        """Test onboarding guide renders major sections."""
        with patch('app.main.st', mock_streamlit):
            with patch('app.main.CommonTexts', mock_i18n_texts['CommonTexts']):
                with patch('app.main.OnboardingTexts', mock_i18n_texts['OnboardingTexts']):
                    from app.main import _render_onboarding_guide

                    _render_onboarding_guide()

                    assert mock_streamlit.header.called
                    assert mock_streamlit.subheader.called


# ==============================================================================
# 5. EXPERT MODE HANDLING TESTS
# ==============================================================================

class TestExpertModeHandling:
    """Test suite for expert mode handling."""

    def test_handle_expert_mode_warns_empty_ticker(self, mock_streamlit, mock_i18n_texts):
        """Test expert mode shows warning for empty ticker."""
        mock_mode = MagicMock()

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.FeedbackMessages', mock_i18n_texts['FeedbackMessages']):
                with patch('app.main.create_expert_terminal') as mock_factory:
                    from app.main import _handle_expert_mode

                    _handle_expert_mode("", mock_mode)

                    mock_streamlit.warning.assert_called_once()
                    mock_factory.assert_not_called()

    def test_handle_expert_mode_creates_terminal(self, mock_streamlit, mock_i18n_texts):
        """Test expert mode creates and renders terminal."""
        mock_mode = MagicMock()
        mock_terminal = MagicMock()
        mock_terminal.build_request.return_value = None

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.FeedbackMessages', mock_i18n_texts['FeedbackMessages']):
                with patch('app.main.create_expert_terminal', return_value=mock_terminal):
                    from app.main import _handle_expert_mode

                    _handle_expert_mode("AAPL", mock_mode, external_launch=False)

                    mock_terminal.render.assert_called_once()

    def test_handle_expert_mode_builds_request_on_launch(self, mock_streamlit, mock_i18n_texts):
        """Test expert mode builds request when externally launched."""
        mock_streamlit.session_state['active_request'] = None
        mock_mode = MagicMock()
        mock_request = MagicMock()
        mock_terminal = MagicMock()
        mock_terminal.build_request.return_value = mock_request

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.FeedbackMessages', mock_i18n_texts['FeedbackMessages']):
                with patch('app.main.create_expert_terminal', return_value=mock_terminal):
                    with patch('app.main._set_active_request') as mock_set_request:
                        from app.main import _handle_expert_mode

                        _handle_expert_mode("AAPL", mock_mode, external_launch=True)

                        mock_terminal.build_request.assert_called_once()
                        mock_set_request.assert_called_once_with(mock_request)


# ==============================================================================
# 6. AUTO LAUNCH HANDLING TESTS
# ==============================================================================

class TestAutoLaunchHandling:
    """Test suite for automated analysis launch."""

    def test_handle_auto_launch_warns_empty_ticker(self, mock_streamlit, mock_i18n_texts):
        """Test auto launch shows warning for empty ticker."""
        mock_mode = MagicMock()
        options = {'years': 5, 'enable_mc': False, 'mc_sims': 10000}

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.FeedbackMessages', mock_i18n_texts['FeedbackMessages']):
                from app.main import _handle_auto_launch

                _handle_auto_launch("", mock_mode, options)

                mock_streamlit.warning.assert_called_once()

    def test_handle_auto_launch_sets_default_peers(self, mock_streamlit, mock_i18n_texts):
        """Test auto launch sets empty peers list as default."""
        mock_streamlit.session_state['active_request'] = None
        mock_mode = MagicMock()
        options = {'years': 5, 'enable_mc': False, 'mc_sims': 10000}  # No manual_peers

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.FeedbackMessages', mock_i18n_texts['FeedbackMessages']):
                with patch('app.main._set_active_request'):
                    # We need to let the function run and check options is modified
                    # But the function creates real Pydantic models, so we mock the whole flow
                    with patch('app.main.Parameters'):
                        with patch('app.main.ValuationRequest'):
                            from app.main import _handle_auto_launch

                            _handle_auto_launch("AAPL", mock_mode, options)

                            assert 'manual_peers' in options


# ==============================================================================
# 7. MAIN FUNCTION TESTS
# ==============================================================================

class TestMainFunction:
    """Test suite for main entry point."""

    def test_main_initializes_page_and_state(self, mock_streamlit, mock_i18n_texts):
        """Test main function initializes page and session state."""
        mock_streamlit.session_state['active_request'] = None
        mock_streamlit.session_state['last_config'] = ''
        mock_streamlit.button.return_value = False

        with patch('app.main.st', mock_streamlit):
            with patch('app.main._setup_page') as mock_setup:
                with patch('app.main._init_session_state') as mock_init:
                    with patch('app.main._render_sidebar_ticker', return_value="AAPL"):
                        with patch('app.main._render_sidebar_methodology', return_value=MagicMock(value="FCFF")):
                            with patch('app.main._render_sidebar_source', return_value=False):
                                with patch('app.main._render_sidebar_auto_options', return_value={}):
                                    with patch('app.main._render_sidebar_footer'):
                                        with patch('app.main._render_onboarding_guide'):
                                            from app.main import main

                                            main()

                                            mock_setup.assert_called_once()
                                            mock_init.assert_called_once()

    def test_main_shows_onboarding_when_no_request(self, mock_streamlit, mock_i18n_texts):
        """Test main shows onboarding guide when no active request."""
        mock_streamlit.session_state['active_request'] = None
        mock_streamlit.session_state['last_config'] = ''
        mock_streamlit.button.return_value = False

        with patch('app.main.st', mock_streamlit):
            with patch('app.main._setup_page'):
                with patch('app.main._init_session_state'):
                    with patch('app.main._render_sidebar_ticker', return_value="AAPL"):
                        with patch('app.main._render_sidebar_methodology', return_value=MagicMock(value="FCFF")):
                            with patch('app.main._render_sidebar_source', return_value=False):
                                with patch('app.main._render_sidebar_auto_options', return_value={}):
                                    with patch('app.main._render_sidebar_footer'):
                                        with patch('app.main._render_onboarding_guide') as mock_onboard:
                                            from app.main import main

                                            main()

                                            mock_onboard.assert_called_once()


# ==============================================================================
# 8. EXPERT RENDER WRAPPER TESTS
# ==============================================================================

class TestExpertRenderWrapper:
    """Test suite for expert terminal render wrapper."""

    def test_expert_render_wrapper_creates_terminal(self, mock_valuation_mode):
        """Test wrapper creates and renders expert terminal."""
        mock_terminal = MagicMock()
        mock_terminal.render.return_value = "rendered_content"

        with patch('app.main.create_expert_terminal', return_value=mock_terminal):
            from app.main import _expert_render_wrapper

            result = _expert_render_wrapper(mock_valuation_mode, "MSFT")

            mock_terminal.render.assert_called_once()
            assert result == "rendered_content"


# ==============================================================================
# 9. EDGE CASES AND ERROR HANDLING
# ==============================================================================

class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_ticker_with_special_characters(self, mock_streamlit, mock_i18n_texts):
        """Test ticker input with special characters is handled."""
        mock_streamlit.text_input.return_value = "AAPL.O"

        with patch('app.main.st', mock_streamlit):
            with patch('app.main.SidebarTexts', mock_i18n_texts['SidebarTexts']):
                with patch('app.main._DEFAULT_TICKER', 'AAPL'):
                    from app.main import _render_sidebar_ticker

                    result = _render_sidebar_ticker()

                    assert result == "AAPL.O"

    def test_config_change_hash_generation(self, mock_streamlit):
        """Test configuration hash is correctly generated."""
        mock_streamlit.session_state['active_request'] = MagicMock()
        mock_streamlit.session_state['last_config'] = ''

        expected_config = "AAPL_True_FCFF_STANDARD"

        with patch('app.main.st', mock_streamlit):
            from app.main import _reset_on_config_change

            _reset_on_config_change(expected_config)

            assert mock_streamlit.session_state.last_config == expected_config