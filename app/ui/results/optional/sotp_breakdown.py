"""
app/ui/results/optional/sotp_breakdown.py

PILLAR 5 — SUB-COMPONENT: SOTP BREAKDOWN (Sum-of-the-Parts)
===========================================================
Role: Visualize the value 'cascade' of Business Units and the equity bridge.
Architecture: Injectable Grade-A Component.

Style: Numpy docstrings
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import MarketTexts, SOTPTexts, KPITexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_charts import display_sotp_waterfall

class SOTPBreakdownTab(ResultTabBase):
    """
    Rendering component for business segment decomposition.
    Integrated vertically within the MarketAnalysis tab (Pillar 5).
    """

    TAB_ID = "sotp_breakdown"
    LABEL = MarketTexts.TITLE_SEGMENTATION
    ORDER = 5 # Aligned with Pillar 5
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible only if SOTP mode is enabled and contains valid segments."""
        return result.params.sotp.enabled

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Renders the value waterfall chart and the contribution detailed table."""
        if not result.params.sotp.segments:
            st.info(SOTPTexts.NO_SOTP_FOUND)
            return

        # --- SECTION HEADER (Standardized ####) ---
        st.markdown(f"#### {SOTPTexts.TITLE}")
        st.caption(MarketTexts.CAPTION_SEGMENTATION)

        # 1. VISUAL CASCADE (Plotly Waterfall)

        display_sotp_waterfall(result)

        # 2. CONTRIBUTION SUMMARY TABLE
        self._render_contribution_table(result)

        # Institutional analysis note
        st.write("")
        st.caption(f"**{KPITexts.NOTE_ANALYSIS}** : {SOTPTexts.HELP_SOTP}")

    @staticmethod
    def _render_contribution_table(result: ValuationResult) -> None:
        """Renders the detailed Business Units table (Static Method)."""
        segments = result.params.sotp.segments
        currency = result.financials.currency

        with st.container(border=True):
            # Headers styled via i18n labels
            h1, h2, h3 = st.columns([2, 2, 1])
            h1.markdown(f"<small style='color: #64748b;'>{MarketTexts.COL_SEGMENT}</small>", unsafe_allow_html=True)
            h2.markdown(f"<small style='color: #64748b; text-align: right;'>{MarketTexts.COL_VALUE}</small>", unsafe_allow_html=True)
            h3.markdown(f"<small style='color: #64748b; text-align: right;'>{MarketTexts.COL_CONTRIBUTION}</small>", unsafe_allow_html=True)
            st.divider()

            raw_ev_sum = sum(seg.enterprise_value for seg in segments)

            for seg in segments:
                c1, c2, c3 = st.columns([2, 2, 1])

                # Segment Name
                c1.markdown(f"**{seg.name}**")

                # Formatted Enterprise Value
                val_formatted = format_smart_number(seg.enterprise_value, currency=currency)
                c2.markdown(f"<div style='text-align: right;'>{val_formatted}</div>", unsafe_allow_html=True)

                # Relative contribution to Gross EV
                contrib = (seg.enterprise_value / raw_ev_sum) if raw_ev_sum > 0 else 0
                c3.markdown(f"<div style='text-align: right;'>{contrib:.1%}")

            # Sum Line (Audit/Gross Value Check)
            if len(segments) > 1:
                st.divider()
                f1, f2, f3 = st.columns([2, 2, 1])
                f1.markdown(f"*{MarketTexts.METRIC_GROSS_VALUE}*")
                f2.markdown(f"<div style='text-align: right;'><b>{format_smart_number(raw_ev_sum, currency=currency)}</b></div>", unsafe_allow_html=True)
                f3.markdown("<div style='text-align: right;'>100%</div>", unsafe_allow_html=True)