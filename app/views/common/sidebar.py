"""
app/views/common/sidebar.py

APPLICATION SIDEBAR — CONTROL CENTER
====================================
Role: Global navigation and configuration hub.
Responsibilities:
  - Ticker selection (updates State).
  - Methodology selection.
  - Mode toggling (Auto/Expert).
  - Triggering the Analysis via AppController.

Style: Institutional Design.
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
    Acts as the primary input for the Valuation Request.
    """
    state = get_state()

    with st.sidebar:
        # --- 1. HEADER ---
        st.markdown(f"## {CommonTexts.APP_TITLE}")
        st.caption(CommonTexts.APP_SUBTITLE)
        st.divider()

        # --- 2. IDENTITY (TICKER) ---
        st.markdown(f"### {SidebarTexts.SEC_1_COMPANY}")

        # Use st.form to prevent rerun on every keystroke (debounce)
        with st.form("ticker_form", clear_on_submit=False):
            new_ticker = (
                st.text_input(
                    SidebarTexts.TICKER_LABEL,
                    value=state.ticker,
                    help="Enter a valid Yahoo Finance ticker (e.g. AAPL, MSFT, ^GSPC).",
                )
                .upper()
                .strip()
            )

            ticker_submitted = st.form_submit_button("Confirm Ticker", width="stretch")

        if ticker_submitted and new_ticker and new_ticker != state.ticker:
            state.ticker = new_ticker
            SessionManager.reset_valuation()
            st.rerun()

        # --- 3. PROJECTION HORIZON ---
        st.markdown(f"### {SidebarTexts.SEC_4_HORIZON}")

        new_years = st.slider(
            SidebarTexts.YEARS_LABEL,
            min_value=UIWidgetDefaults.MIN_PROJECTION_YEARS,
            max_value=UIWidgetDefaults.MAX_PROJECTION_YEARS,
            value=state.projection_years,
            step=1,
        )

        if new_years != state.projection_years:
            state.projection_years = new_years
            SessionManager.reset_valuation()
            st.rerun()

        # --- 4. METHODOLOGY ---
        st.markdown(f"### {SidebarTexts.SEC_2_METHODOLOGY}")

        # Use i18n display names from the Registry instead of raw enum values
        display_names = get_display_names()
        method_options = list(ValuationMethodology)

        selected_method = st.selectbox(
            SidebarTexts.METHOD_LABEL,
            options=method_options,
            index=method_options.index(state.selected_methodology),
            format_func=lambda x: display_names.get(x, x.value),
        )

        if selected_method != state.selected_methodology:
            state.selected_methodology = selected_method
            SessionManager.reset_valuation()
            st.rerun()

        # --- 5. MODE SWITCH (Auto vs Expert) ---
        st.divider()
        st.markdown(f"### {SidebarTexts.SETTINGS}")

        is_expert = st.toggle(
            SidebarTexts.SOURCE_EXPERT,
            value=state.is_expert_mode,
            help="Enable detailed manual overrides for all parameters.",
        )

        if is_expert != state.is_expert_mode:
            state.is_expert_mode = is_expert
            st.rerun()

        # --- 6. EXECUTION ---
        st.divider()

        # Primary Action Button
        if st.button(CommonTexts.RUN_BUTTON, type="primary", width="stretch"):
            AppController.handle_run_analysis()

        # --- FOOTER ---
        st.divider()
        st.caption(f"{CommonTexts.PROJECT_BADGE} | {CommonTexts.AUTHOR_NAME}")
