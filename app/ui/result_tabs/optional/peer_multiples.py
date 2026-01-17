"""
app/ui/result_tabs/optional/peer_multiples.py
Onglet — Valorisation Relative (Multiples de Comparables)

Migration depuis ui_kpis.py._render_relative_valuation_tab()
Visible uniquement si des données de peers sont disponibles.
"""

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult, MultiplesValuationResult
from core.i18n import KPITexts
from app.ui.base import ResultTabBase
from app.ui.result_tabs.components.kpi_cards import format_smart_number


class PeerMultiplesTab(ResultTabBase):
    """
    Onglet de triangulation par multiples.

    Migration exacte de _render_relative_valuation_tab() depuis ui_kpis.py
    pour garantir l'identicité fonctionnelle.
    """

    TAB_ID = "peer_multiples"
    LABEL = KPITexts.SEC_E_RELATIVE
    ICON = ""
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si des multiples sont disponibles."""
        return result.multiples_triangulation is not None

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche la valorisation par multiples.

        Suit exactement la même logique que _render_relative_valuation_tab dans ui_kpis.py.
        """
        rel_result = result.multiples_triangulation

        st.markdown(f"#### {KPITexts.SEC_E_RELATIVE}")
        st.caption(KPITexts.RELATIVE_VAL_DESC)

        m = rel_result.multiples_data
        c1, c2, c3 = st.columns(3)
        c1.metric(KPITexts.LABEL_PE_RATIO, f"{m.median_pe:.1f}x")
        c2.metric(KPITexts.LABEL_EV_EBITDA, f"{m.median_ev_ebitda:.1f}x")
        c3.metric(KPITexts.LABEL_EV_REVENUE, f"{m.median_ev_rev:.1f}x")

        st.divider()

        if m.peers:
            peer_list = []
            for p in m.peers:
                peer_list.append({
                    "Ticker": p.ticker, "Name": p.name, "Mcap": format_smart_number(p.market_cap),
                    "P/E": f"{p.pe_ratio:.1f}x" if p.pe_ratio else "—",
                    "EV/EBITDA": f"{p.ev_ebitda:.1f}x" if p.ev_ebitda else "—",
                    "EV/Rev": f"{p.ev_revenue:.1f}x" if p.ev_revenue else "—"
                })
            st.dataframe(pd.DataFrame(peer_list), hide_index=True, use_container_width=True)

        with st.expander(KPITexts.TAB_CALC, expanded=False):
            from app.ui.result_tabs.components.step_renderer import render_calculation_step
            for idx, step in enumerate(rel_result.calculation_trace, start=1):
                render_calculation_step(idx, step)
                    f"{md.median_pe:.1f}x" if md.median_pe else "—",
                    f"{md.median_pb:.1f}x" if md.median_pb else "—",
                ],
                "Cible": [
                    f"{result.financials.ev_ebitda:.1f}x" if hasattr(result.financials, 'ev_ebitda') and result.financials.ev_ebitda else "—",
                    "—",
                    f"{result.financials.pe_ratio:.1f}x" if result.financials.pe_ratio else "—",
                    f"{result.financials.pb_ratio:.1f}x" if result.financials.pb_ratio else "—",
                ],
            })
            
            st.dataframe(multiples_df, hide_index=True, use_container_width=True)
        
        # Valeurs implicites
        if md.implied_value_ev_ebitda or md.implied_value_pe:
            with st.container(border=True):
                st.markdown("**Valeurs Implicites par Action**")
                
                col1, col2 = st.columns(2)
                
                if md.implied_value_ev_ebitda:
                    col1.metric(
                        "Via EV/EBITDA",
                        format_smart_number(md.implied_value_ev_ebitda, result.financials.currency)
                    )
                
                if md.implied_value_pe:
                    col2.metric(
                        "Via P/E",
                        format_smart_number(md.implied_value_pe, result.financials.currency)
                    )
    
    def get_display_label(self) -> str:
        """Label sans icône."""
        return self.LABEL
