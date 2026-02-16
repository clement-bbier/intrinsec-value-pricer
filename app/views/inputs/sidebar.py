"""
app/views/common/sidebar.py

APPLICATION SIDEBAR — CONTROL CENTER
====================================
Role: Global navigation and configuration hub.
Responsibilities:
  - Ticker selection (updates State).
  - Methodology selection.
  - Mode toggling (Standard/Approfondie).
  - Triggering the Analysis via AppController.

Style: Institutional Design (NumPy Docstrings).
"""

import streamlit as st

from app.controllers.app_controller import AppController
from app.state.session_manager import SessionManager
from app.state.store import get_state
from src.config.constants import UIWidgetDefaults
from src.i18n import CommonTexts, SidebarTexts
from src.models.enums import ValuationMethodology
from src.valuation.registry import get_display_names


def render_sidebar():
    """
    Renders the main sidebar configuration panel.

    This function acts as the primary input gateway for the valuation request.
    It synchronizes the UI widgets with the global application state using
    optimized callbacks to prevent redundant reruns.

    Notes
    -----
    Uses high-contrast institutional design defined in the global CSS.
    """
    state = get_state()

    # --- INTERNAL CALLBACKS ---

    def _on_config_change():
        """Reset valuation results in state whenever a core parameter changes."""
        SessionManager.reset_valuation()

    def _on_mode_change():
        """Update expert mode flag based on the radio selection."""
        state.is_expert_mode = (st.session_state.mode_selector == "Approfondie")
        _on_config_change()

    with st.sidebar:
        # --- 1. HEADER ---
        st.markdown(f"## {SidebarTexts.TITLE}")
        st.divider()

        # --- 2. IDENTITY (TICKER) ---
        st.markdown(f"### {SidebarTexts.SEC_1_COMPANY}")

        # Forms do not support callbacks on every widget change (standard Streamlit behavior)
        with st.form("ticker_form", clear_on_submit=False):
            new_ticker = (
                st.text_input(
                    SidebarTexts.TICKER_LABEL,
                    value=state.ticker,
                )
                .upper()
                .strip()
            )

            ticker_submitted = st.form_submit_button(
                SidebarTexts.BTN_TICKER_CONFIRM, width="stretch"
            )

        if ticker_submitted and new_ticker and new_ticker != state.ticker:
            state.ticker = new_ticker
            _on_config_change()
            st.rerun()

        st.divider()

        # --- 3. METHODOLOGY ---
        st.markdown(f"### {SidebarTexts.SEC_2_METHODOLOGY}")

        display_names = get_display_names()
        method_options = list(ValuationMethodology)

        # Synchronized via session_state key
        st.selectbox(
            SidebarTexts.METHOD_LABEL,
            options=method_options,
            index=method_options.index(state.selected_methodology),
            format_func=lambda x: display_names.get(x, x.value),
            key="selected_methodology",
            on_change=_on_config_change,
        )

        st.divider()

        # --- 4. PROJECTION HORIZON ---
        # Only displayed for DCF-based models (hidden for Graham)
        if state.selected_methodology != ValuationMethodology.GRAHAM:
            st.markdown(f"### {SidebarTexts.SEC_4_HORIZON}")

            st.slider(
                SidebarTexts.YEARS_LABEL,
                min_value=UIWidgetDefaults.MIN_PROJECTION_YEARS,
                max_value=UIWidgetDefaults.MAX_PROJECTION_YEARS,
                value=state.projection_years,
                step=1,
                key="projection_years",
                on_change=_on_config_change,
            )
            st.divider()

        # --- 5. MODE SWITCH (Standard vs Approfondie) ---
        st.markdown(f"### {SidebarTexts.SETTINGS}")

        mode_options = ["Standard", "Approfondie"]
        current_idx = 1 if state.is_expert_mode else 0

        st.radio(
            "Niveau d'analyse",
            options=mode_options,
            index=current_idx,
            horizontal=False,
            key="mode_selector",
            on_change=_on_mode_change,
        )

        st.divider()

        # --- 6. EXECUTION ---
        if st.button(CommonTexts.RUN_BUTTON, type="primary", width="stretch"):
            AppController.handle_run_analysis()

        st.divider()

        # --- LANGUAGE CHANGE (Placeholder for future i18n logic) ---
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"## {SidebarTexts.LANGUAGE}")
        with col2:
            st.selectbox(
                "Lang",
                options=["FR", "EN"],
                index=0,
                key="app_language",
                label_visibility="collapsed",
            )

        st.divider()

        # --- FOOTER ---
        linkedin_url = (
            "https://www.linkedin.com/in/cl%C3%A9ment-barbier-409a341b6/?locale=en_US"
        )

        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 10px; color: #ffffff; font-size: 0.8rem; opacity: 0.8;">
                {CommonTexts.DEVELOPED_BY} 
                <a href="{linkedin_url}" target="_blank" style="
                    color: #dc2626; 
                    text-decoration: none; 
                    font-weight: 600;
                ">
                    {CommonTexts.AUTHOR_NAME}
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )