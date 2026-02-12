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
            total_ev = sum(seg.enterprise_value for seg in sotp.segments)
            for seg in sotp.segments:
                if seg.contribution_pct is not None:
                    contribution = seg.contribution_pct
                elif total_ev > 0:
                    contribution = seg.enterprise_value / total_ev
                else:
                    contribution = 0.0

                segments_data.append({
                    "Segment": seg.name,
                    "Revenu": format_smart_number(seg.revenue, currency) if seg.revenue else "—",
                    "Méthode": seg.method.value if hasattr(seg.method, 'value') else str(seg.method),
                    "Valeur": format_smart_number(seg.enterprise_value, currency),
                    "Contribution": f"{contribution:.1%}",
                })
            
            df = pd.DataFrame(segments_data)
            st.dataframe(df, hide_index=True, width='stretch')
        
        # Synthèse
        with st.container(border=True):
            gross_value = total_ev
            discount = sotp.conglomerate_discount
            net_value = gross_value * (1.0 - discount)

            col1, col2, col3 = st.columns(3)
            
            col1.metric(
                "Valeur Brute SOTP",
                format_smart_number(gross_value, currency)
            )
            col2.metric(
                "Décote Holding",
                f"{discount:.1%}"
            )
            col3.metric(
                "Valeur Nette SOTP",
                format_smart_number(net_value, currency)
            )
    
    def get_display_label(self) -> str:
        return self.LABEL
