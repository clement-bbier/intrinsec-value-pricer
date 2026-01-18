"""
app/ui/result_tabs/optional/peer_multiples.py
Onglet — Valorisation Relative (Multiples de Comparables)

Visible uniquement si des données de peers sont disponibles.
"""

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult, MultiplesData
from core.i18n import KPITexts
from app.ui.base import ResultTabBase
from app.ui.result_tabs.components.kpi_cards import format_smart_number


class PeerMultiplesTab(ResultTabBase):
    """Onglet de triangulation par multiples."""

    TAB_ID = "peer_multiples"
    LABEL = "Valorisation Relative"
    ICON = ""
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si des multiples sont disponibles."""
        return (
            result.multiples_data is not None
            and result.multiples_data.peer_count > 0
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche la valorisation par multiples."""
        md = result.multiples_data

        st.markdown("**VALORISATION PAR COMPARABLES**")
        st.caption(f"Panel de {md.peer_count} sociétés comparables")

        # Tableau des multiples
        with st.container(border=True):
            st.markdown("**Multiples du Panel**")

            multiples_df = pd.DataFrame({
                "Multiple": ["EV/EBITDA", "EV/EBIT", "P/E", "P/B"],
                "Médiane": [
                    f"{md.median_ev_ebitda:.1f}x" if md.median_ev_ebitda else "—",
                    f"{md.median_ev_ebit:.1f}x" if md.median_ev_ebit else "—",
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

            st.dataframe(multiples_df, hide_index=True, width='stretch')

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