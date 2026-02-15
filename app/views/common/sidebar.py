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
        st.markdown(f"## {SidebarTexts.TITLE}")
        st.divider()

        # --- 2. IDENTITY (TICKER) ---
        st.markdown(f"### {SidebarTexts.SEC_1_COMPANY}")

        # Use st.form to prevent rerun on every keystroke (debounce)
        with st.form("ticker_form", clear_on_submit=False):
            new_ticker = (
                st.text_input(
                    SidebarTexts.TICKER_LABEL,
                    value=state.ticker,
                    help=SidebarTexts.HELP_TICKER_LABEL,
                )
                .upper()
                .strip()
            )

            ticker_submitted = st.form_submit_button(SidebarTexts.BTN_TICKER_CONFIRM, width="stretch")

        # à revoir peut-être
        if ticker_submitted and new_ticker and new_ticker != state.ticker:
            state.ticker = new_ticker
            SessionManager.reset_valuation()
            st.rerun()

        st.divider()

        # --- 3. METHODOLOGY ---
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

        # à revoir peut-être
        if selected_method != state.selected_methodology:
            state.selected_methodology = selected_method
            SessionManager.reset_valuation()
            st.rerun()

        st.divider()

        # --- 4. PROJECTION HORIZON ---
        if state.selected_methodology != ValuationMethodology.GRAHAM:
            st.markdown(f"### {SidebarTexts.SEC_4_HORIZON}")

            new_years = st.slider(
                SidebarTexts.YEARS_LABEL,
                min_value=UIWidgetDefaults.MIN_PROJECTION_YEARS,
                max_value=UIWidgetDefaults.MAX_PROJECTION_YEARS,
                value=state.projection_years,
                step=1,
            )

            # à revoir peut-être
            if new_years != state.projection_years:
                state.projection_years = new_years
                SessionManager.reset_valuation()
                st.rerun()

            st.divider()

        # --- 5. MODE SWITCH (Auto vs Expert) ---
        st.markdown(f"### {SidebarTexts.SETTINGS}")

        # Utilisation d'un radio horizontal pour un look "Terminal"
        mode_label = "Niveau d'analyse"
        options = ["Standard", "Approfondie"]

        current_index = 1 if state.is_expert_mode else 0

        selected_mode = st.radio(
            mode_label,
            options=options,
            index=current_index,
            horizontal=False,
        )

        new_expert_mode = (selected_mode == "Approfondie")

        if new_expert_mode != state.is_expert_mode:
            state.is_expert_mode = new_expert_mode
            st.rerun()

        st.divider()

        # --- 6. EXECUTION ---
        if st.button(CommonTexts.RUN_BUTTON, type="primary", width="stretch"):
            AppController.handle_run_analysis()

        st.divider()

        # --- LANGUAGE CHANGE ---
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"## {SidebarTexts.LANGUAGE}")
        with col2:
            lang = st.selectbox(
                "Lang",
                options=["FR", "EN"],
                index=0,
                label_visibility="collapsed"
            )

        st.divider()

        # --- FOOTER ---
        linkedin_url = "https://www.linkedin.com/in/cl%C3%A9ment-barbier-409a341b6/?locale=en_US"

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
            unsafe_allow_html=True
        )
