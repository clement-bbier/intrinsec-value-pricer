"""
app/ui/results/core/market_analysis.py

PILLAR 5 — MARKET ANALYSIS & SEGMENTS (HUB)
===========================================
Role: Orchestrates relative market valuation (Peers) and business
segmentation (SOTP) into a unified market analysis interface.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import PillarLabels, KPITexts
from app.ui.results.base_result import ResultTabBase

# Internal rendering engines (Spokes)
from app.views.results.pillars.peer_multiples import PeerMultiples
from app.views.results.pillars.sotp_breakdown import SOTPBreakdownTab


class MarketAnalysisTab(ResultTabBase):
    """
    Pillar 5: Market Analysis Hub.

    This component coordinates the dynamic display of relative valuation
    multiples and Sum-of-the-Parts (SOTP) breakdowns. It centralizes
    market-based perspectives to complement fundamental DCF analysis.
    """

    TAB_ID = "market_analysis"
    LABEL = PillarLabels.PILLAR_5_MARKET
    ORDER = 5
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Coordinated rendering of Pillar 5 components.

        Parameters
        ----------
        result : ValuationResult
            The complete valuation result object containing market data.
        **kwargs : Any
            Additional rendering context.
        """
        # --- 1. PILLAR HEADER (Institutional Standard) ---
        st.markdown(f"### {PillarLabels.PILLAR_5_MARKET}")
        st.caption(KPITexts.RELATIVE_VAL_DESC)
        st.write("")

        # 2. BLOC MULTIPLES (Market Triangulation Spoke)
        # PeerMultiples handles its own data check internally
        peer_view = PeerMultiples()
        if peer_view.is_visible(result):
            peer_view.render(result, **kwargs)

        # 3. BLOC SOTP (Segmental Decomposition Spoke)
        sotp_view = SOTPBreakdownTab()
        if sotp_view.is_visible(result):
            # Add visual separation only if both components are rendered
            if peer_view.is_visible(result):
                st.divider()
            sotp_view.render(result, **kwargs)

    def is_visible(self, result: ValuationResult) -> bool:
        """
        Determines if the market analysis hub should be displayed.

        The hub is visible if either the peer triangulation engine found
        comparable companies OR if the SOTP model was explicitly enabled.

        Parameters
        ----------
        result : ValuationResult
            The result object to inspect for active market modules.

        Returns
        -------
        bool
            True if Multiples or SOTP data is available for rendering.
        """
        p = result.params
        return p.peers.enabled or p.sotp.enabled