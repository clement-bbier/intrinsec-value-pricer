"""
app/ui/result_tabs/optional/scenario_analysis.py
Onglet — Analyse de Scénarios (Bull/Base/Bear)

Visible uniquement si les scénarios sont activés.
"""

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult
from app.ui.base import ResultTabBase
from app.ui.result_tabs.components.kpi_cards import format_smart_number


class ScenarioAnalysisTab(ResultTabBase):
    """Onglet d'analyse de scénarios."""
    
    TAB_ID = "scenario_analysis"
    LABEL = "Scénarios"
    ICON = ""
    ORDER = 6
    IS_CORE = False
    
    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si scénarios disponibles."""
        return (
            result.scenarios is not None
            and len(result.scenarios) > 0
        )
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche l'analyse de scénarios."""
        scenarios = result.scenarios
        currency = result.financials.currency
        
        st.markdown("**ANALYSE DE SCÉNARIOS**")
        st.caption("Valorisation sous différentes hypothèses de croissance")
        
        # Tableau des scénarios
        with st.container(border=True):
            scenario_data = []
            for name, scenario in scenarios.items():
                scenario_data.append({
                    "Scénario": name.upper(),
                    "Probabilité": f"{scenario.probability:.0%}",
                    "Croissance": f"{scenario.growth_rate:.1%}",
                    "Valeur/Action": format_smart_number(scenario.intrinsic_value, currency),
                    "Upside": f"{scenario.upside_pct:+.1%}",
                })
            
            df = pd.DataFrame(scenario_data)
            st.dataframe(df, hide_index=True, use_container_width=True)
        
        # Valeur pondérée
        if hasattr(result, 'weighted_intrinsic_value') and result.weighted_intrinsic_value:
            with st.container(border=True):
                col1, col2 = st.columns(2)
                col1.metric(
                    "Valeur Pondérée",
                    format_smart_number(result.weighted_intrinsic_value, currency)
                )
                col2.metric(
                    "Upside Pondéré",
                    f"{result.weighted_upside_pct:+.1%}" if hasattr(result, 'weighted_upside_pct') else "—"
                )
    
    def get_display_label(self) -> str:
        return self.LABEL