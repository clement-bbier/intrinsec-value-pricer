"""
app/views/inputs/auto_form.py
AUTO MODE LANDING VIEW
"""

import streamlit as st

from app.state.store import get_state
from src.i18n import CommonTexts, SidebarTexts
from src.i18n.fr.ui.common import OnboardingTexts


def render_auto_form():
    """
    Renders the minimalist 'Auto Mode' welcome screen.

    Auto mode displays only the basic company and methodology information.
    It generates the first 3 result tabs (Configuration, Proof, Benchmark)
    without any extension toggles. Extensions are exclusive to Expert mode.
    """
    state = get_state()

    st.markdown(f"# {CommonTexts.APP_TITLE}")
    st.markdown(f"### {SidebarTexts.SOURCE_AUTO}")

    st.info(f"""
        **{SidebarTexts.SEC_1_COMPANY}:** {state.ticker}
        **{SidebarTexts.METHOD_LABEL}:** {state.selected_methodology.value}

        {OnboardingTexts.STRATEGY_ACQUISITION_DESC}

        **{CommonTexts.RUN_BUTTON}**
        """)
