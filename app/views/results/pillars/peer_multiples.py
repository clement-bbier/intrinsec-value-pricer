"""
app/views/results/pillars/peer_multiples.py

PILLAR 5 — SUB-COMPONENT: PEER MULTIPLES TRIANGULATION
======================================================
Role: Relative valuation using market comparables (Trading Comps).
Architecture: Injectable Grade-A Component (Stateless).
Style: Numpy docstrings.
"""

from typing import Any, List, Dict
import pandas as pd
import streamlit as st

from src.models import ValuationResult
from src.i18n import MarketTexts, KPITexts, PeersTexts
from src.core.formatting import format_smart_number
from app.views.components.ui_kpis import atom_kpi_metric
from app.views.components.ui_charts import display_football_field


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
        # Check configuration AND data existence
        has_config = result.params.extensions.peers.enabled
        has_data = (
                result.results.extensions.peers is not None
                and result.results.extensions.peers.multiples_data is not None
        )
        return has_config and has_data

    @staticmethod
    def render(result: ValuationResult, **_kwargs: Any) -> None:
        """
        Renders the relative valuation view: Football Field, Implied Values, and Trading Comps table.

        Parameters
        ----------
        result : ValuationResult
            The complete valuation result object.
        **_kwargs : Any
            Unused parameters for compatibility.
        """
        peers_res = result.results.extensions.peers

        # Double check data integrity
        if not peers_res or not peers_res.multiples_data or not peers_res.multiples_data.peers:
            st.info(PeersTexts.NO_PEERS_FOUND)
            return

        md = peers_res.multiples_data
        currency = result.financials.currency
        ticker = result.request.ticker

        # --- SECTION HEADER ---
        st.markdown(f"#### {MarketTexts.MARKET_TITLE}")

        # Source & Count Context (Fully i18n)
        source_lbl = md.source if md.source else MarketTexts.SOURCE_DEFAULT
        caption_txt = MarketTexts.CAPTION_PEERS_COUNT.format(
            count=len(md.peers),
            label=MarketTexts.COL_PEER + "s",
            source=source_lbl
        )
        st.caption(caption_txt)

        # 1. VISUAL TRIANGULATION (Football Field)
        # This chart compares Intrinsic Value vs Relative Value ranges
        display_football_field(result)
        st.write("")

        # 2. IMPLIED VALUE METRICS (The "Output")
        with st.container(border=True):
            c1, c2 = st.columns(2)

            # Helper function to format the tooltip string safely
            def _get_help_text(val: float) -> str:
                if not val:
                    return ""
                return MarketTexts.HELP_IMPLIED_METHOD.format(multiple=f"{val:.1f}x")

            # EV/EBITDA Implied Value
            val_ebitda = peers_res.implied_prices.get("EV/EBITDA", 0.0)
            help_ebitda = _get_help_text(md.median_ev_ebitda)

            with c1:
                atom_kpi_metric(
                    label=f"{MarketTexts.IMPLIED_VAL_PREFIX} (EV/EBITDA)",
                    value=format_smart_number(val_ebitda, currency),
                    help_text=help_ebitda
                )

            # P/E Implied Value
            val_pe = peers_res.implied_prices.get("P/E", 0.0)
            help_pe = _get_help_text(md.median_pe)

            with c2:
                atom_kpi_metric(
                    label=f"{MarketTexts.IMPLIED_VAL_PREFIX} (P/E)",
                    value=format_smart_number(val_pe, currency),
                    help_text=help_pe
                )

                # 3. TRADING COMPS TABLE (Detailed View)
                st.write("")
                st.markdown(f"##### {MarketTexts.COL_MULTIPLE}s & {MarketTexts.COL_PEER}s")

                # Remplacement de l'initialisation multi-étapes par un List Literal
                comps_data: List[Dict[str, Any]] = [
                    # Target Row (First element)
                    {
                        "Name": f"{ticker} ({MarketTexts.LBL_TARGET})",
                        "EV/EBITDA": result.financials.ev_ebitda_ratio or 0.0,
                        "P/E": result.financials.pe_ratio or 0.0,
                    },
                    # Expansion des Peer Rows via une List Comprehension
                    *[
                        {
                            "Name": peer.ticker,
                            "EV/EBITDA": peer.ev_ebitda or 0.0,
                            "P/E": peer.pe_ratio or 0.0,
                        }
                        for peer in md.peers
                    ]
                ]

                df_comps = pd.DataFrame(comps_data)

        # Column Configuration
        column_config = {
            "Name": st.column_config.TextColumn(
                label=MarketTexts.COL_PEER,
                width="medium"
            ),
            "EV/EBITDA": st.column_config.NumberColumn(
                label=KPITexts.LABEL_FOOTBALL_FIELD_EBITDA,
                format="%.1fx",
                width="small"
            ),
            "P/E": st.column_config.NumberColumn(
                label=KPITexts.LABEL_FOOTBALL_FIELD_PE,
                format="%.1fx",
                width="small"
            )
        }

        with st.container(border=True):
            st.dataframe(
                df_comps,
                hide_index=True,
                column_config=column_config,
                use_container_width=True
            )

            # Median Summary Line (Bottom)
            summary_txt = MarketTexts.CAPTION_MEDIAN_SUMMARY.format(
                label=MarketTexts.LBL_SECTOR_MEDIAN,
                ebitda=f"{md.median_ev_ebitda:.1f}x" if md.median_ev_ebitda else "—",
                pe=f"{md.median_pe:.1f}x" if md.median_pe else "—"
            )
            st.caption(summary_txt)