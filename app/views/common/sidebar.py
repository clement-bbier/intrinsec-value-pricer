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

from app.state.store import get_state
from app.state.session_manager import SessionManager
from app.controllers.app_controller import AppController
from src.models.enums import ValuationMethodology
from src.i18n import CommonTexts, SidebarTexts


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

        # We use a callback to reset results if the ticker changes
        new_ticker = st.text_input(
            SidebarTexts.TICKER_LABEL,
            value=state.ticker,
            help="Enter a valid Yahoo Finance ticker (e.g. AAPL, MSFT, ^GSPC)."
        ).upper().strip()

        if new_ticker != state.ticker:
            state.ticker = new_ticker
            SessionManager.reset_valuation()

        # --- 3. METHODOLOGY ---
        st.markdown(f"### {SidebarTexts.SEC_2_METHODOLOGY}")

        # Create a mapping for display labels
        # Note: In a real app, use i18n for keys. Here using raw Enums for simplicity.
        method_options = list(ValuationMethodology)

        selected_method = st.selectbox(
            SidebarTexts.METHOD_LABEL,
            options=method_options,
            index=method_options.index(state.selected_methodology),
            format_func=lambda x: x.value  # Could use a dedicated i18n mapper here
        )

        if selected_method != state.selected_methodology:
            state.selected_methodology = selected_method
            SessionManager.reset_valuation()

        # --- 4. MODE SWITCH (Auto vs Expert) ---
        st.divider()
        st.markdown(f"### {SidebarTexts.SETTINGS}")

        is_expert = st.toggle(
            SidebarTexts.SOURCE_EXPERT,
            value=state.is_expert_mode,
            help="Enable detailed manual overrides for all parameters."
        )

        if is_expert != state.is_expert_mode:
            state.is_expert_mode = is_expert
            # We don't necessarily reset valuation here, but it's safer UI behavior
            st.rerun()

        # --- 5. EXECUTION ---
        st.divider()

        # Primary Action Button
        if st.button(
                CommonTexts.RUN_BUTTON,
                type="primary",
                use_container_width=True
        ):
            AppController.handle_run_analysis()

        # --- FOOTER ---
        st.markdown("---")
        st.caption(f"{CommonTexts.PROJECT_BADGE} | {CommonTexts.AUTHOR_NAME}")