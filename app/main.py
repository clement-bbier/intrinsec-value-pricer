"""
app/main.py

APPLICATION ENTRY POINT — USER INTERFACE
========================================
Centralized Registry System (DT-007/008/009).
This module orchestrates the sidebar inputs and the main content area,
supporting both automated and expert-led valuation workflows.

Architecture: ST-4.0 (Centralized Orchestration)
Style: Numpy docstrings
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable, Dict

import streamlit as st

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================

_FILE_PATH = Path(__file__).resolve()
_ROOT_PATH = _FILE_PATH.parent.parent

if str(_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(_ROOT_PATH))

# ==============================================================================
# APPLICATION IMPORTS
# ==============================================================================

from app.assets.style_system import inject_institutional_design
from app.workflow import run_workflow_and_display
from src.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    SOTPParameters
)

# I18N TEXTUAL REFERENTIAL
from src.i18n import (
    CommonTexts,
    SidebarTexts,
    OnboardingTexts,
    FeedbackMessages
)

# CENTRALIZED REGISTRY (DT-008)
from src.valuation.registry import get_display_names

# EXPERT FACTORY
from app.ui.expert.factory import create_expert_terminal

# ==============================================================================
# LOGGING & CONFIGURATION
# ==============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION REGISTRIES (FACADE TO CENTRAL REGISTRY)
# ==============================================================================

# Valuation display names mapped from the central registry
VALUATION_DISPLAY_NAMES: Dict[ValuationMode, str] = get_display_names()

def _expert_render_wrapper(mode: ValuationMode, ticker: str):
    """
    Wrapper to render the expert terminal via the factory.

    Parameters
    ----------
    mode : ValuationMode
        The selected valuation methodology.
    ticker : str
        The target company ticker.
    """
    return create_expert_terminal(mode, ticker).render()

# Expert UI Registry for dynamic component injection
EXPERT_UI_REGISTRY: Dict[ValuationMode, Callable] = {
    mode: _expert_render_wrapper for mode in ValuationMode
}

# ==============================================================================
# UI CONSTANTS (DT-011: Centralized in core/config)
# ==============================================================================

from src.config import MonteCarloDefaults, SystemDefaults

_DEFAULT_TICKER = CommonTexts.DEFAULT_TICKER
_DEFAULT_PROJECTION_YEARS = SystemDefaults.DEFAULT_PROJECTION_YEARS
_MIN_PROJECTION_YEARS = SystemDefaults.MIN_PROJECTION_YEARS
_MAX_PROJECTION_YEARS = SystemDefaults.MAX_PROJECTION_YEARS
_MIN_MC_SIMULATIONS = MonteCarloDefaults.MIN_SIMULATIONS
_MAX_MC_SIMULATIONS = MonteCarloDefaults.MAX_SIMULATIONS
_DEFAULT_MC_SIMULATIONS = MonteCarloDefaults.DEFAULT_SIMULATIONS
_MC_SIMULATIONS_STEP = MonteCarloDefaults.STEP_SIMULATIONS


# ==============================================================================
# SESSION STATE MANAGEMENT
# ==============================================================================

def _init_session_state() -> None:
    """Initializes session variables if absent."""
    defaults = {
        "active_request": None,
        "last_config": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_on_config_change(current_config: str) -> None:
    """
    Resets the active request if the configuration (ticker/mode) has changed.
    """
    if st.session_state.last_config != current_config:
        st.session_state.active_request = None
        st.session_state.last_config = current_config


def _set_active_request(request: ValuationRequest) -> None:
    """Registers the active request and triggers a UI rerun."""
    st.session_state.active_request = request
    st.rerun()


# ==============================================================================
# PAGE SETUP
# ==============================================================================

def _setup_page() -> None:
    """Configures the Streamlit page with institutional branding."""
    st.set_page_config(
        page_title=CommonTexts.APP_TITLE,
        page_icon="📊",
        layout="wide",
    )
    inject_institutional_design()

# ==============================================================================
# SIDEBAR — USER INPUTS
# ==============================================================================

def _render_sidebar_ticker() -> str:
    """Renders the ticker input field."""
    st.header(SidebarTexts.SEC_1_COMPANY)
    ticker = st.text_input(SidebarTexts.TICKER_LABEL, value=_DEFAULT_TICKER)
    st.divider()
    return ticker.strip().upper()


def _render_sidebar_methodology() -> ValuationMode:
    """Renders the methodology selector."""
    st.header(SidebarTexts.SEC_2_METHODOLOGY)
    selected_name = st.selectbox(
        SidebarTexts.METHOD_LABEL,
        options=list(VALUATION_DISPLAY_NAMES.values()),
    )
    st.divider()
    return next(
        mode for mode, name in VALUATION_DISPLAY_NAMES.items()
        if name == selected_name
    )


def _render_sidebar_source() -> bool:
    """
    Renders the data source selector.
    Returns True if Expert Mode is selected.
    """
    st.header(SidebarTexts.SEC_3_SOURCE)
    input_mode = st.radio(
        SidebarTexts.STRATEGY_LABEL,
        options=SidebarTexts.SOURCE_OPTIONS,
    )
    st.divider()
    return input_mode == SidebarTexts.SOURCE_OPTIONS[1]


def _render_sidebar_auto_options(_mode: ValuationMode) -> Dict:
    """Renders options specific to the Automated (Standard) mode."""
    st.header(SidebarTexts.SEC_4_HORIZON)
    years = st.slider(
        SidebarTexts.YEARS_LABEL,
        min_value=_MIN_PROJECTION_YEARS,
        max_value=_MAX_PROJECTION_YEARS,
        value=_DEFAULT_PROJECTION_YEARS,
    )
    st.divider()
    return {
        "years": years,
        "enable_mc": False,
        "mc_sims": _DEFAULT_MC_SIMULATIONS
    }


def _render_sidebar_footer() -> None:
    """Renders the institutional sidebar footer."""
    st.markdown(
        f"""
        <div style="margin-top: 2rem; font-size: 0.8rem; color: #94a3b8; 
                    border-top: 0.5px solid #334155; padding-top: 1rem;">
            {CommonTexts.DEVELOPED_BY} <br>
            <a href="https://www.linkedin.com/in/cl%C3%A9ment-barbier-409a341b6/" 
               target="_blank" 
               style="color: #6366f1; text-decoration: none; font-weight: 600;">
               {CommonTexts.AUTHOR_NAME}
            </a><br>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# CONTENT — MAIN DISPLAY
# ==============================================================================

def _render_onboarding_guide() -> None:
    """
    Onboarding Guide — Homogeneous institutional design.
    Uses bordered containers for all key methodology and process sections.
    """
    # 1. HEADER & COMPLIANCE
    st.header(CommonTexts.APP_TITLE)
    st.markdown(OnboardingTexts.INTRO_INFO)
    st.caption(OnboardingTexts.COMPLIANCE_BODY)
    st.divider()

    # 2. VALUATION METHODOLOGIES (Grid with formulas)
    st.subheader(OnboardingTexts.TITLE_METHODS)
    st.markdown(OnboardingTexts.DESC_METHODS)



    m_cols = st.columns(4)
    methods = [
        (OnboardingTexts.MODEL_DCF_TITLE, r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}",
         OnboardingTexts.MODEL_DCF_DESC),
        (OnboardingTexts.MODEL_EQUITY_TITLE, r"P = \sum_{t=1}^{n} \frac{FCFE_t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}",
         OnboardingTexts.MODEL_EQUITY_DESC),
        (OnboardingTexts.MODEL_RIM_TITLE, r"V_0 = BV_0 + \sum \frac{NI_t - (k_e \cdot BV_{t-1})}{(1+k_e)^t}",
         OnboardingTexts.MODEL_RIM_DESC),
        (OnboardingTexts.MODEL_GRAHAM_TITLE, r"V_0 = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}",
         OnboardingTexts.MODEL_GRAHAM_DESC)
    ]
    for col, (title, latex, desc) in zip(m_cols, methods):
        with col:
            with st.container(border=True):
                st.markdown(title)
                st.latex(latex)
                st.markdown(f"<div style='min-height: 100px;'><small style='color: #64748b;'>{desc}</small></div>",
                            unsafe_allow_html=True)
    st.divider()

    # 3. DATA WORKFLOWS
    st.subheader(OnboardingTexts.TITLE_PROCESS)
    p_cols = st.columns(3)
    processes = [
        (OnboardingTexts.STRATEGY_ACQUISITION_TITLE, OnboardingTexts.STRATEGY_ACQUISITION_DESC),
        (OnboardingTexts.STRATEGY_MANUAL_TITLE, OnboardingTexts.STRATEGY_MANUAL_DESC),
        (OnboardingTexts.STRATEGY_FALLBACK_TITLE, OnboardingTexts.STRATEGY_FALLBACK_DESC)
    ]
    for col, (title, desc) in zip(p_cols, processes):
        with col:
            with st.container(border=True):
                st.markdown(title)
                st.markdown(
                    f"<div style='min-height: 110px;'><small style='color: #64748b;'>{desc}</small></div>",
                    unsafe_allow_html=True)
    st.divider()

    # 4. RESULTS ARCHITECTURE (The 5 Pillars)
    st.subheader(OnboardingTexts.TITLE_RESULTS)
    st.markdown(OnboardingTexts.DESC_RESULTS)



    r_cols = st.columns(5)
    results_pillars = [
        (OnboardingTexts.TAB_1_TITLE, OnboardingTexts.TAB_1_DESC),
        (OnboardingTexts.TAB_2_TITLE, OnboardingTexts.TAB_2_DESC),
        (OnboardingTexts.TAB_3_TITLE, OnboardingTexts.TAB_3_DESC),
        (OnboardingTexts.TAB_4_TITLE, OnboardingTexts.TAB_4_DESC),
        (OnboardingTexts.TAB_5_TITLE, OnboardingTexts.TAB_5_DESC)
    ]
    for col, (title, desc) in zip(r_cols, results_pillars):
        with col:
            with st.container(border=True):
                st.markdown(title)
                st.markdown(
                    f"<div style='min-height: 110px;'><small style='color: #64748b;'>{desc}</small></div>",
                    unsafe_allow_html=True)
    st.divider()

    # 5. DIAGNOSTIC SYSTEM (Footer)
    st.subheader(OnboardingTexts.DIAGNOSTIC_HEADER)
    d1, d2, d3 = st.columns(3)
    d1.error(OnboardingTexts.DIAGNOSTIC_BLOQUANT)
    d2.warning(OnboardingTexts.DIAGNOSTIC_WARN)
    d3.info(OnboardingTexts.DIAGNOSTIC_INFO)

def _handle_expert_mode(ticker: str, mode: ValuationMode, external_launch: bool = False) -> None:
    """
    Handles expert terminal rendering and valuation triggering.

    Parameters
    ----------
    ticker : str
        Stock symbol.
    mode : ValuationMode
        Selected methodology.
    external_launch : bool, optional
        Indicates if calculation is triggered from a secondary UI element (e.g. Sidebar).
    """
    if not ticker:
        st.warning(FeedbackMessages.TICKER_REQUIRED_SIDEBAR)
        return

    # Use factory to create the dedicated expert terminal
    terminal = create_expert_terminal(mode, ticker)

    # Widgets persist in st.session_state via the render call
    terminal.render()

    # If external launch (sidebar button), build the final request
    if external_launch:
        request = terminal.build_request()
        if request:
            _set_active_request(request)


def _handle_auto_launch(ticker: str, mode: ValuationMode, options: Dict) -> None:
    """Handles automated analysis launch with default risk parameters."""
    if not ticker:
        st.warning(FeedbackMessages.TICKER_INVALID)
        return

    options.setdefault("manual_peers", [])

    from src.models import ScenarioParameters

    # Standard configuration with Scenarios disabled for Auto Mode
    config_params = DCFParameters(
        rates=CoreRateParameters(),
        growth=GrowthParameters(projection_years=options["years"]),
        monte_carlo=MonteCarloConfig(
            enable_monte_carlo=options["enable_mc"],
            num_simulations=options["mc_sims"]
        ),
        scenarios=ScenarioParameters(enabled=False),
        sotp=SOTPParameters(enabled=False)
    )

    request = ValuationRequest(
        ticker=ticker,
        projection_years=options["years"],
        mode=mode,
        input_source=InputSource.AUTO,
        manual_params=config_params,
        options=options
    )

    _set_active_request(request)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main() -> None:
    """Main application entry point."""
    _setup_page()
    _init_session_state()

    # =========================================================================
    # SIDEBAR — Input Collection
    # =========================================================================
    with st.sidebar:
        ticker = _render_sidebar_ticker()
        selected_mode = _render_sidebar_methodology()
        is_expert = _render_sidebar_source()

        # Check for config changes to reset previous results
        current_config = f"{ticker}_{is_expert}_{selected_mode.value}"
        _reset_on_config_change(current_config)

        # UI Branching for Auto/Expert parameters
        auto_options = {}
        launch_analysis = False

        if not is_expert:
            auto_options = _render_sidebar_auto_options(selected_mode)

        launch_analysis = st.button(
            CommonTexts.RUN_BUTTON,
            type="primary",
            use_container_width=True
        )

        _render_sidebar_footer()

    # =========================================================================
    # CONTENT — Main Rendering Logic
    # =========================================================================
    if st.session_state.active_request:
        # Launch valuation engine and display results via workflow
        run_workflow_and_display(st.session_state.active_request)

    elif is_expert:
        # Delegate to specific expert terminal
        _handle_expert_mode(ticker, selected_mode, external_launch=launch_analysis)

    elif launch_analysis:
        # Trigger automated data acquisition and calculation
        _handle_auto_launch(ticker, selected_mode, auto_options)

    else:
        # Display initial fact sheet
        _render_onboarding_guide()


# ==============================================================================
# EXECUTION
# ==============================================================================

if __name__ == "__main__":
    main()