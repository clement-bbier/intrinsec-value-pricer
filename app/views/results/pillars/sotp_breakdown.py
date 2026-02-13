"""
app/views/results/pillars/sotp_breakdown.py

PILLAR 5 — SUB-COMPONENT: SOTP BREAKDOWN (Sum-of-the-Parts)
===========================================================
Role: Visualize the value 'cascade' of Business Units and the equity bridge.
Architecture: Injectable Grade-A Component (Stateless).
Style: Numpy docstrings.
"""

from typing import Any

import pandas as pd
import streamlit as st

from app.views.components.ui_charts import display_sotp_waterfall
from src.core.formatting import format_smart_number
from src.i18n import KPITexts, MarketTexts, SOTPTexts
from src.models import ValuationResult


class SOTPBreakdownTab:
    """
    Rendering component for business segment decomposition.
    Integrated vertically within the MarketAnalysis tab (Pillar 5).

    This component is stateless and relies on the ValuationResult object
    passed to its static render method.
    """

    @staticmethod
    def is_visible(result: ValuationResult) -> bool:
        """
        Determines visibility based on configuration and results existence.

        Parameters
        ----------
        result : ValuationResult
            The valuation result object.

        Returns
        -------
        bool
            True if SOTP is enabled and results are computed.
        """
        sotp_config = result.request.parameters.extensions.sotp
        sotp_results = result.results.extensions.sotp
        return sotp_config.enabled and sotp_results is not None

    @staticmethod
    def render(result: ValuationResult, **_kwargs: Any) -> None:
        """
        Renders the value waterfall chart and the contribution detailed table.

        Parameters
        ----------
        result : ValuationResult
            The complete valuation result containing SOTP data.
        **_kwargs : Any
            Unused context parameters (for signature compatibility).
        """
        sotp_res = result.results.extensions.sotp
        if not sotp_res or not sotp_res.segment_values:
            st.info(SOTPTexts.NO_SOTP_FOUND)
            return

        # --- SECTION HEADER ---
        st.markdown(f"#### {SOTPTexts.TITLE}")
        st.caption(MarketTexts.CAPTION_SEGMENTATION)

        # 1. VISUAL CASCADE (Plotly Waterfall)
        display_sotp_waterfall(result)

        # 2. CONTRIBUTION SUMMARY TABLE
        SOTPBreakdownTab._render_contribution_table(result)

        # Institutional analysis note
        st.write("")
        st.caption(f"**{KPITexts.NOTE_ANALYSIS}** : {SOTPTexts.HELP_SOTP}")

    @staticmethod
    def _render_contribution_table(result: ValuationResult) -> None:
        """
        Renders the detailed Business Units table using a DataFrame
        with visual progress bars for relative contribution.
        """
        sotp_res = result.results.extensions.sotp
        if not sotp_res:
            return

        currency = result.request.parameters.structure.currency
        segment_values = sotp_res.segment_values
        raw_ev_sum = sotp_res.total_enterprise_value

        # --- A. Data Preparation ---
        data = []
        for seg_name, seg_value in segment_values.items():
            contribution = (seg_value / raw_ev_sum) if raw_ev_sum > 0 else 0.0
            data.append({
                MarketTexts.COL_SEGMENT: seg_name,
                MarketTexts.COL_VALUE: seg_value,
                MarketTexts.COL_CONTRIBUTION: contribution
            })

        df = pd.DataFrame(data)

        # --- B. Table Configuration (Modern Streamlit UI) ---
        column_config = {
            MarketTexts.COL_SEGMENT: st.column_config.TextColumn(
                label=MarketTexts.COL_SEGMENT,
                width="medium"
            ),
            MarketTexts.COL_VALUE: st.column_config.NumberColumn(
                label=f"{MarketTexts.COL_VALUE} ({currency})",
                format=f"%.2f {currency}",
                width="medium"
            ),
            MarketTexts.COL_CONTRIBUTION: st.column_config.ProgressColumn(
                label=MarketTexts.COL_CONTRIBUTION,
                format="%.1%",
                min_value=0,
                max_value=1,
                width="medium"
            )
        }

        # --- C. Rendering ---
        with st.container(border=True):
            st.dataframe(
                df,
                hide_index=True,
                column_config=column_config,
                width="stretch"
            )

            # Footer: Gross Value Check
            st.divider()
            c1, c2 = st.columns([0.7, 0.3])

            with c1:
                st.markdown(f"**{MarketTexts.METRIC_GROSS_VALUE}**")

            with c2:
                total_fmt = format_smart_number(raw_ev_sum, currency=currency)
                st.markdown(f"<div style='text-align: right;'><b>{total_fmt}</b></div>", unsafe_allow_html=True)
