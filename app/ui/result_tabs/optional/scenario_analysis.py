"""
app/ui/result_tabs/optional/scenario_analysis.py
Onglet — Analyse de Scénarios (Bull/Base/Bear)

Migration depuis ui_kpis.py._render_scenarios_tab()
Visible uniquement si les scénarios sont activés.
"""

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult
from core.i18n import KPITexts, ExpertTerminalTexts
from app.ui.base import ResultTabBase


class ScenarioAnalysisTab(ResultTabBase):
    """
    Onglet d'analyse de scénarios.

    Migration exacte de _render_scenarios_tab() depuis ui_kpis.py
    pour garantir l'identicité fonctionnelle.
    """

    TAB_ID = "scenario_analysis"
    LABEL = KPITexts.TAB_SCENARIOS
    ICON = ""
    ORDER = 6
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si scénarios disponibles."""
        return result.scenario_synthesis is not None

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche l'analyse de scénarios.

        Suit exactement la même logique que _render_scenarios_tab dans ui_kpis.py.
        """
        synthesis = result.scenario_synthesis
        currency = result.financials.currency

        st.markdown(f"#### {KPITexts.TAB_SCENARIOS}")
        st.caption(KPITexts.SUB_SCENARIO_WEIGHTS)

        rows = []
        labels_map = {"Bull": ExpertTerminalTexts.LABEL_SCENARIO_BULL,
                      "Base": ExpertTerminalTexts.LABEL_SCENARIO_BASE,
                      "Bear": ExpertTerminalTexts.LABEL_SCENARIO_BEAR}

        for v in synthesis.variants:
            rows.append({
                "Scénario": labels_map.get(v.label, v.label),
                "Probabilité": f"{v.probability:.0%}",
                "Croissance (g)": f"{v.growth_used:.2%}",
                "Marge FCF": f"{v.margin_used:.1%}" if v.margin_used is not None and v.margin_used != 0 else ("Base"),
                "Valeur par Action": f"{v.intrinsic_value:,.2f} {currency}"
            })

        st.table(pd.DataFrame(rows))
        st.info(f"**{KPITexts.LABEL_SCENARIO_RANGE}** : {synthesis.max_downside:,.2f} à {synthesis.max_upside:,.2f} {currency}")
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
