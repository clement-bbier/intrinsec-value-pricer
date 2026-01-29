from typing import Any
import streamlit as st
from src.models import ValuationResult
from src.i18n import PillarLabels, KPITexts
from app.ui.results.base_result import ResultTabBase

# Import des "Spokes" (Composants spécialisés)
from app.ui.results.optional.peer_multiples import PeerMultiples
from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab

class MarketAnalysisTab(ResultTabBase):
    """
    Pillar 5: Market Analysis & Segments (SOTP).
    Hub orchestrating peer comparison and business unit decomposition.
    """
    TAB_ID = "market_analysis"
    LABEL = PillarLabels.PILLAR_5_MARKET
    ORDER = 5
    IS_CORE = True

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible if either peer multiples or SOTP data is available."""
        peer_view = PeerMultiples()
        sotp_view = SOTPBreakdownTab()
        return peer_view.is_visible(result) or sotp_view.is_visible(result)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Coordinated rendering of Pillar 5 components."""
        # --- PILLAR HEADER ---
        st.markdown(f"### {PillarLabels.PILLAR_5_MARKET}")
        st.caption(KPITexts.RELATIVE_VAL_DESC)
        st.write("")

        # 1. BLOC MULTIPLES (Spoke 1)
        peer_view = PeerMultiples()
        if peer_view.is_visible(result):
            peer_view.render(result, **kwargs)

        # 2. BLOC SOTP (Spoke 2)
        sotp_view = SOTPBreakdownTab()
        if sotp_view.is_visible(result):
            # Ajout d'un séparateur si les deux blocs sont présents
            if peer_view.is_visible(result):
                st.divider()
            sotp_view.render(result, **kwargs)