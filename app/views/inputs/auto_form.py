"""
app/views/inputs/auto_form.py
AUTO MODE LANDING VIEW
"""

import streamlit as st

from app.state.store import get_state
from src.i18n import CommonTexts, ExtensionTexts, SidebarTexts
from src.i18n.fr.ui.common import OnboardingTexts


def render_auto_form():
    """
    Renders the minimalist 'Auto Mode' welcome screen.

    Includes extension checkboxes so that optional analytical modules
    (Monte Carlo, Sensitivity, etc.) can be toggled even in Auto mode.
    The checkbox keys match the UIKey suffixes defined in
    ``src.models.parameters.options`` so that ``InputFactory`` can
    read them without any prefix.
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

    # --- Extension Checkboxes ---
    st.divider()
    st.markdown(f"### {ExtensionTexts.TITLE}")

    c1, c2 = st.columns(2)

    with c1:
        st.checkbox(ExtensionTexts.MONTE_CARLO, key="enable", value=False)
        st.checkbox(ExtensionTexts.SENSITIVITY, key="sensi_enable", value=False)
        st.checkbox(ExtensionTexts.SCENARIOS, key="scenario_enable", value=False)

    with c2:
        st.checkbox(ExtensionTexts.BACKTEST, key="bt_enable", value=False)
        st.checkbox(ExtensionTexts.PEERS, key="peer_enable", value=False)
        st.checkbox(ExtensionTexts.SOTP, key="sotp_enable", value=False)
