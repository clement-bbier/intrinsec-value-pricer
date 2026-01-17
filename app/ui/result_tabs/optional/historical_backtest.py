"""
app/ui/result_tabs/optional/historical_backtest.py
Onglet — Backtest Historique

Migration depuis ui_kpis.py._render_backtest_tab()
Visible uniquement si un backtest a été exécuté.
"""

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult
from core.i18n import BacktestTexts, AuditTexts
from app.ui.base import ResultTabBase


class HistoricalBacktestTab(ResultTabBase):
    """
    Onglet de validation historique.

    Migration exacte de _render_backtest_tab() depuis ui_kpis.py
    pour garantir l'identicité fonctionnelle.
    """

    TAB_ID = "historical_backtest"
    LABEL = BacktestTexts.TITLE
    ICON = ""
    ORDER = 7
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si backtest disponible."""
        return result.backtest_report is not None

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche les résultats du backtest.

        Suit exactement la même logique que _render_backtest_tab dans ui_kpis.py.
        """
        from app.ui_components.ui_charts import display_backtest_convergence_chart

        st.markdown(f"#### {BacktestTexts.TITLE}")

        # SÉCURITÉ : Utilisation de la clé correcte issue de ui_texts.py
        if not result.backtest_report or not result.backtest_report.points:
            st.warning(AuditTexts.MC_NO_DATA)
            return

        # A. Score de fiabilité historique
        report = result.backtest_report
        c1, c2, c3 = st.columns(3)
        c1.metric(BacktestTexts.METRIC_MAE, f"{report.mean_absolute_error:.1%}", help=BacktestTexts.HELP_BACKTEST)
        c2.metric(BacktestTexts.METRIC_ACCURACY, f"{report.model_accuracy_score:.1f}/100")

        # B. Graphique de convergence
        st.markdown(f"**{BacktestTexts.SECTION_CONVERGENCE}**")
        display_backtest_convergence_chart(result)

        # C. Tableau détaillé
        st.markdown(f"**{BacktestTexts.SECTION_DETAILS}**")
        df = pd.DataFrame([
            {
                BacktestTexts.COL_DATE: p.date.strftime("%Y-%m-%d"),
                BacktestTexts.COL_PREDICTED: f"{p.predicted_value:,.2f}",
                BacktestTexts.COL_ACTUAL: f"{p.actual_price:,.2f}",
                BacktestTexts.COL_ERROR: f"{p.prediction_error:.1%}"
            } for p in report.points
        ])
        st.dataframe(df, use_container_width=True)
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
                st.dataframe(df, hide_index=True, use_container_width=True)
    
    def get_display_label(self) -> str:
        return self.LABEL
