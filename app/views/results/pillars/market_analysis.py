"""
app/views/results/pillars/market_analysis.py

PILLAR 5 — MARKET ANALYSIS & SEGMENTS (HUB)
===========================================
Role: Orchestrates relative market valuation (Peers) and business
segmentation (SOTP) into a unified market analysis interface.
Architecture: ST-4.2 Compliant Hub & Spokes logic.
"""

from typing import Any

import streamlit as st

# Internal rendering engines (Spokes)
# These components must implement static methods: .is_visible() and .render()
from app.views.results.pillars.peer_multiples import PeerMultiples
from app.views.results.pillars.sotp_breakdown import SOTPBreakdownTab
from src.i18n import KPITexts, MarketTexts, PillarLabels
from src.models import ValuationResult


def render_market_context(result: ValuationResult, **kwargs: Any) -> None:
    """
    Renders Pillar 5: Market Analysis Hub.

    This function coordinates the dynamic display of relative valuation
    multiples and Sum-of-the-Parts (SOTP) breakdowns. It centralizes
    market-based perspectives to complement fundamental DCF analysis.

    Parameters
    ----------
    result : ValuationResult
        The complete valuation result object containing market data.
    **kwargs : Any
        Additional rendering context.
    """

    # --- 1. PILLAR HEADER (Institutional Standard) ---
    st.header(PillarLabels.PILLAR_5_MARKET)
    st.caption(KPITexts.RELATIVE_VAL_DESC)
    st.divider()

    # --- 2. PEER MULTIPLES (Relative Valuation Spoke) ---
    # We delegate the rendering to the Spoke if peer data is available.
    # Architecture: Stateless call to static methods.
    if PeerMultiples.is_visible(result):
        PeerMultiples.render(result, **kwargs)

    # --- 3. SOTP BREAKDOWN (Segmental Decomposition Spoke) ---
    # We render the SOTP waterfall if segments are defined.
    if SOTPBreakdownTab.is_visible(result):
        # Visual separation only if both components are active to avoid clustering
        if PeerMultiples.is_visible(result):
            st.divider()

        SOTPBreakdownTab.render(result, **kwargs)

    # --- 4. FALLBACK (Empty State) ---
    # If neither module is active, we display a helpful message.
    if not PeerMultiples.is_visible(result) and not SOTPBreakdownTab.is_visible(result):
        st.info(MarketTexts.NO_MARKET_DATA)
