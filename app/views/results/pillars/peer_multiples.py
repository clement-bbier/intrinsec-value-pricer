"""
app/views/results/pillars/peer_multiples.py

PILLAR 5 — SUB-COMPONENT: PEER MULTIPLES TRIANGULATION
======================================================
Role: Relative valuation using market comparables (Trading Comps).
Architecture: Injectable Grade-A Component (Stateless).
Style: Numpy docstrings.
"""

from typing import Any

import pandas as pd
import streamlit as st

from app.views.components.ui_charts import display_football_field
from app.views.components.ui_kpis import atom_kpi_metric
from src.core.formatting import format_smart_number
from src.i18n import KPITexts, MarketTexts, PeersTexts, QuantTexts
from src.models import ValuationResult


class PeerMultiples:
    """
    Component focused exclusively on peer multiples triangulation.
    Displays implied valuation ranges and comparable metrics.

    Architecture: Stateless Component.
    """

    @staticmethod
    def is_visible(result: ValuationResult) -> bool:
        """
        Visible only if peer data exists and is populated in the results.

        Parameters
        ----------
        result : ValuationResult
            The valuation result object.

        Returns
        -------
        bool
            True if peers are enabled and result data is present.
        """
        has_config = result.request.parameters.extensions.peers.enabled
        has_data = result.results.extensions.peers is not None
        return has_config and has_data

    @staticmethod
    def render(result: ValuationResult, **_kwargs: Any) -> None:
        """
        Renders the relative valuation view: Football Field, Implied Values,
        and Trading Comps table.

        Parameters
        ----------
        result : ValuationResult
            The complete valuation result object.
        **_kwargs : Any
            Unused parameters for compatibility.
        """
        peers_res = result.results.extensions.peers

        if not peers_res:
            st.info(PeersTexts.NO_PEERS_FOUND)
            return

        currency = result.request.parameters.structure.currency

        # --- SECTION HEADER ---
        st.subheader(MarketTexts.MARKET_TITLE)

        # Source & Count Context (Fully i18n)
        peer_count = len(peers_res.peer_valuations)
        caption_txt = MarketTexts.CAPTION_PEERS_COUNT.format(count=peer_count, label=MarketTexts.COL_PEER + "s", source=MarketTexts.SOURCE_DEFAULT)
        st.caption(caption_txt)

        # 1. VISUAL TRIANGULATION (Football Field)
        with st.container(border=True):
            display_football_field(result)
        st.write("")

        # 2. IMPLIED VALUE METRICS (The "Output")
        medians = peers_res.median_multiples_used

        with st.container(border=True):
            c1, c2 = st.columns(2)

            # EV/EBITDA Implied Value
            val_ebitda = peers_res.implied_prices.get("EV/EBITDA", 0.0)
            median_ebitda = medians.get("EV/EBITDA", 0.0)
            help_ebitda = MarketTexts.HELP_IMPLIED_METHOD.format(multiple=f"{median_ebitda:.1f}x") if median_ebitda else ""

            with c1:
                atom_kpi_metric(
                    label=f"{MarketTexts.IMPLIED_VAL_PREFIX} (EV/EBITDA)",
                    value=format_smart_number(val_ebitda, currency),
                    help_text=help_ebitda,
                )

            # P/E Implied Value
            val_pe = peers_res.implied_prices.get("P/E", 0.0)
            median_pe = medians.get("P/E", 0.0)
            help_pe = MarketTexts.HELP_IMPLIED_METHOD.format(multiple=f"{median_pe:.1f}x") if median_pe else ""

            with c2:
                atom_kpi_metric(
                    label=f"{MarketTexts.IMPLIED_VAL_PREFIX} (P/E)",
                    value=format_smart_number(val_pe, currency),
                    help_text=help_pe,
                )

        # 3. PEER VALUATIONS TABLE
        if peers_res.peer_valuations:
            st.write("")
            st.markdown(f"##### {MarketTexts.COL_PEER}s")

            comps_data: list[dict[str, Any]] = [
                {
                    "Name": peer.ticker,
                    KPITexts.LABEL_FOOTBALL_FIELD_PE: peer.intrinsic_value,
                    QuantTexts.COL_UPSIDE: peer.upside_pct,
                }
                for peer in peers_res.peer_valuations
            ]

            df_comps = pd.DataFrame(comps_data)

            column_config = {
                "Name": st.column_config.TextColumn(label=MarketTexts.COL_PEER, width="medium"),
                KPITexts.LABEL_FOOTBALL_FIELD_PE: st.column_config.NumberColumn(label=KPITexts.LABEL_FOOTBALL_FIELD_PE, format=f"%.2f {currency}", width="small"),
                QuantTexts.COL_UPSIDE: st.column_config.NumberColumn(label=QuantTexts.COL_UPSIDE, format="%.1%", width="small"),
            }

            with st.container(border=True):
                st.dataframe(df_comps, hide_index=True, column_config=column_config, width="stretch")

                # Median Summary Line
                summary_txt = MarketTexts.CAPTION_MEDIAN_SUMMARY.format(
                    label=MarketTexts.LBL_SECTOR_MEDIAN,
                    ebitda=f"{median_ebitda:.1f}x" if median_ebitda else "—",
                    pe=f"{median_pe:.1f}x" if median_pe else "—",
                )
                st.caption(summary_txt)
