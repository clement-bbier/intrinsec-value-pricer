"""
app/ui/result_tabs/optional/sotp_breakdown.py
Onglet — Sum-of-the-Parts (SOTP)

Visible uniquement si une valorisation SOTP est disponible.
"""

from typing import Any

import streamlit as st
import pandas as pd

from src.domain.models import ValuationResult
from app.ui.base import ResultTabBase
from src.utilities.formatting import format_smart_number


class SOTPBreakdownTab(ResultTabBase):
    """Onglet de décomposition SOTP."""
    
    TAB_ID = "sotp_breakdown"
    LABEL = "Sum-of-the-Parts"
    ICON = ""
    ORDER = 5
    IS_CORE = False
    
    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si SOTP disponible."""
        return (
            result.sotp_results is not None
            and len(result.sotp_results.segments) > 0
        )
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche la décomposition SOTP."""
        sotp = result.sotp_results
        currency = result.financials.currency
        
        st.markdown("**VALORISATION PAR SEGMENTS**")
        st.caption("Somme des parties avec multiples sectoriels")
        
        # Tableau des segments
        with st.container(border=True):
            segments_data = []
            for seg in sotp.segments:
                segments_data.append({
                    "Segment": seg.name,
                    "Revenu": format_smart_number(seg.revenue, currency),
                    "Multiple": f"{seg.multiple:.1f}x",
                    "Valeur": format_smart_number(seg.value, currency),
                    "Contribution": f"{seg.contribution_pct:.1%}",
                })
            
            df = pd.DataFrame(segments_data)
            st.dataframe(df, hide_index=True, width='stretch')
        
        # Synthèse
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            
            col1.metric(
                "Valeur Brute SOTP",
                format_smart_number(sotp.gross_value, currency)
            )
            col2.metric(
                "Décote Holding",
                f"{sotp.holding_discount:.1%}"
            )
            col3.metric(
                "Valeur Nette SOTP",
                format_smart_number(sotp.net_value, currency)
            )
    
    def get_display_label(self) -> str:
        return self.LABEL
