"""
app/ui/results/optional/peer_multiples.py

PILLAR 5 — MARKET ANALYSIS & SEGMENTS (SOTP)
=============================================
Architecture: Versatile Grade-A Component.
Fusion ST-4.2: Merging Market Relative Analysis and SOTP Decomposition.
"""

from __future__ import annotations
from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import MarketTexts, KPITexts, PillarLabels, SOTPTexts, SharedTexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric
from app.ui.components.ui_charts import display_football_field, display_sotp_waterfall

class MarketAnalysisTab(ResultTabBase):
    """
    Merged Tab: Market Analysis & Sum-of-the-parts.
    Centralizes relative market positioning and operational segmentation.
    """

    TAB_ID = "market_analysis"
    LABEL = PillarLabels.PILLAR_5_MARKET
    ORDER = 5
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible if peers exist OR if SOTP is enabled in parameters."""
        has_peers = (
            result.multiples_triangulation is not None
            and len(result.multiples_triangulation.multiples_data.peers) > 0
        )
        has_sotp = bool(result.params.sotp and result.params.sotp.enabled)
        return has_peers or has_sotp

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Versatile rendering of market relative analysis and business segmentation."""

        # --- HEADER ---
        st.markdown(f"### {PillarLabels.PILLAR_5_MARKET}")
        st.caption(KPITexts.RELATIVE_VAL_DESC)
        st.write("")

        # 1. SECTION: MARKET MULTIPLES (Triangulation)
        if result.multiples_triangulation and result.multiples_triangulation.multiples_data.peers:
            self._render_multiples_section(result)
            # Visual divider if SOTP follows
            if result.params.sotp and result.params.sotp.enabled:
                st.divider()

        # 2. SECTION: SUM-OF-THE-PARTS (SOTP)
        if result.params.sotp and result.params.sotp.enabled:
            self._render_sotp_section(result)

    @staticmethod
    def _render_multiples_section(result: ValuationResult) -> None:
        """Renders the triangulation against market peers."""
        md = result.multiples_triangulation.multiples_data
        currency = result.financials.currency

        st.markdown(f"#### {MarketTexts.MARKET_TITLE}")
        st.caption(f"{len(md.peers)} {MarketTexts.COL_PEER}s | Source: {md.source}")

        # Football Field Chart (Valuation Triangulation)

        display_football_field(result)
        st.write("")

        # Relative Valuation KPIs
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                atom_kpi_metric(
                    label=f"{MarketTexts.IMPLIED_VAL_PREFIX} {KPITexts.LABEL_FOOTBALL_FIELD_EBITDA}",
                    value=format_smart_number(md.implied_value_ev_ebitda, currency)
                )
            with c2:
                atom_kpi_metric(
                    label=f"{MarketTexts.IMPLIED_VAL_PREFIX} {KPITexts.LABEL_FOOTBALL_FIELD_PE}",
                    value=format_smart_number(md.implied_value_pe, currency)
                )

        st.write("")
        # Comparative Multiples Table
        with st.container(border=True):
            st.markdown(f"**{MarketTexts.COL_MULTIPLE}s {SharedTexts.LBL_COMPARATIVE}**")

            comparison_data = [
                {
                    MarketTexts.LBL_RATIO: KPITexts.LABEL_FOOTBALL_FIELD_EBITDA,
                    MarketTexts.LBL_MEDIAN: f"{md.median_ev_ebitda:.1f}x" if md.median_ev_ebitda else "—",
                    MarketTexts.LBL_TARGET: f"{result.financials.ev_ebitda_ratio:.1f}x" if result.financials.ev_ebitda_ratio else "—"
                },
                {
                    MarketTexts.LBL_RATIO: KPITexts.LABEL_FOOTBALL_FIELD_PE,
                    MarketTexts.LBL_MEDIAN: f"{md.median_pe:.1f}x" if md.median_pe else "—",
                    MarketTexts.LBL_TARGET: f"{result.financials.pe_ratio:.1f}x" if result.financials.pe_ratio else "—"
                }
            ]
            st.dataframe(pd.DataFrame(comparison_data), hide_index=True, width="stretch")

    @staticmethod
    def _render_sotp_section(result: ValuationResult) -> None:
        """Renders the value cascade by business segments (Waterfall)."""
        st.markdown(f"#### {SOTPTexts.TITLE}")
        st.caption(SOTPTexts.DESC_SOTP_VALUATION)

        # SOTP Waterfall Chart

        display_sotp_waterfall(result)

    def get_display_label(self) -> str:
        """Returns the localized tab label."""
        return self.LABEL