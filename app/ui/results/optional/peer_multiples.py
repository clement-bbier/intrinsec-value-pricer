from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import MarketTexts, KPITexts, SharedTexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric
from app.ui.components.ui_charts import display_football_field

class PeerMultiples(ResultTabBase):
    """Component focused exclusively on peer multiples triangulation."""

    TAB_ID = "peer_multiples_view"
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible only if peer data exists and is populated."""
        return bool(
            result.multiples_triangulation is not None
            and len(result.multiples_triangulation.multiples_data.peers) > 0
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        md = result.multiples_triangulation.multiples_data
        currency = result.financials.currency

        # --- SECTION HEADER ---
        st.markdown(f"#### {MarketTexts.MARKET_TITLE}")
        st.caption(f"{len(md.peers)} {MarketTexts.COL_PEER}s | Source: {md.source}")

        # 1. Visual Chart
        display_football_field(result)
        st.write("")

        # 2. Key Metrics
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

        # 3. Data Table
        st.write("")
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