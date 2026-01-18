"""
app/ui/result_tabs/optional/historical_backtest.py
Onglet — Backtest Historique

Visible uniquement si un backtest a été exécuté.
"""

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult
from app.ui.base import ResultTabBase


class HistoricalBacktestTab(ResultTabBase):
    """Onglet de validation historique."""
    
    TAB_ID = "historical_backtest"
    LABEL = "Backtest"
    ICON = ""
    ORDER = 7
    IS_CORE = False
    
    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si backtest disponible."""
        return (
            result.backtest_result is not None
            and len(result.backtest_result.periods) > 0
        )
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche les résultats du backtest."""
        bt = result.backtest_result
        
        st.markdown("**VALIDATION HISTORIQUE**")
        st.caption("Performance du modèle sur les périodes passées")
        
        # Métriques globales
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Périodes testées", bt.periods_count)
            col2.metric("Hit Rate", f"{bt.hit_rate:.0%}")
            col3.metric("Erreur Médiane", f"{bt.median_error:.1%}")
            col4.metric("MAE", f"{bt.mae:.1%}")
        
        # Détail par période
        if bt.periods:
            with st.container(border=True):
                st.markdown("**Détail par Période**")
                
                periods_data = []
                for period in bt.periods:
                    periods_data.append({
                        "Date": period.date.strftime("%Y-%m"),
                        "Valeur Prédite": f"{period.predicted_value:,.2f}",
                        "Valeur Réelle": f"{period.actual_value:,.2f}",
                        "Erreur": f"{period.error_pct:+.1%}",
                        "Verdict": "OK" if abs(period.error_pct) < 0.20 else "ECART",
                    })
                
                df = pd.DataFrame(periods_data)
                st.dataframe(df, hide_index=True, width='stretch')
    
    def get_display_label(self) -> str:
        return self.LABEL
