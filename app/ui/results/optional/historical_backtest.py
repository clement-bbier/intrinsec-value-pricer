"""
app/ui/results/optional/historical_backtest.py
PILLIER 4 — SOUS-COMPOSANT : VALIDATION HISTORIQUE (BACKTEST)
============================================================
Rôle : Preuve visuelle de la capacité prédictive du modèle sur le passé.
Architecture : Composant injectable Grade-A.
"""

from __future__ import annotations
from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import QuantTexts, BacktestTexts, CommonTexts, AuditTexts
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric
from app.ui.components.ui_charts import display_backtest_convergence_chart

class HistoricalBacktestTab(ResultTabBase):
    """
    Composant de rendu pour le backtesting historique.
    Intégré verticalement dans l'onglet RiskEngineering.
    """

    TAB_ID = "historical_backtest"
    LABEL = "Backtest"
    ORDER = 4 # Aligné sur le Pilier 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si le moteur a généré au moins un point de comparaison historique."""
        return bool(result.backtest_report and len(result.backtest_report.points) > 0)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu institutionnel du Backtest avec métriques de précision."""
        bt = result.backtest_report
        currency = result.financials.currency

        # --- EN-TÊTE DE SECTION (Standardisé ####) ---
        st.markdown(f"#### {BacktestTexts.TITLE}")
        st.caption(BacktestTexts.HELP_BACKTEST)
        st.write("")

        # --- 1. PERFORMANCE HUB (KPIs de Précision) ---
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)

            # Hit Rate : % de fois où l'IV a correctement prédit une sous-évaluation
            hit_rate = sum(1 for p in bt.points if p.was_undervalued) / len(bt.points) if bt.points else 0

            with c1:
                atom_kpi_metric(label=BacktestTexts.LBL_PERIODS, value=str(len(bt.points)))

            with c2:
                atom_kpi_metric(label=QuantTexts.LABEL_HIT_RATE, value=f"{hit_rate:.0%}")

            with c3:
                atom_kpi_metric(label=QuantTexts.LABEL_MAE, value=f"{bt.mean_absolute_error:.1%}")

            with c4:
                # Suppression du texte en dur : Utilisation des statuts d'audit i18n
                # Un MAE < 15% est considéré comme "Conforme" aux standards financiers
                is_optimal = bt.mean_absolute_error < 0.15
                status_label = AuditTexts.STATUS_OK if is_optimal else AuditTexts.STATUS_ALERT
                atom_kpi_metric(
                    label=BacktestTexts.METRIC_ACCURACY,
                    value=status_label.upper(),
                    delta="Grade A" if is_optimal else "Grade B",
                    delta_color="normal" if is_optimal else "off"
                )

        # --- 2. GRAPHIQUE DE CONVERGENCE (Visualisation IV vs Prix) ---
        st.write("")
        display_backtest_convergence_chart(
            ticker=result.ticker,
            backtest_report=bt,
            currency=currency
        )

        # --- 3. DÉTAIL DES SÉQUENCES (Tableau de transparence) ---
        st.write("")
        with st.expander(BacktestTexts.SEC_RESULTS):
            periods_data = []
            for point in bt.points:
                periods_data.append({
                    "DATE": point.valuation_date.strftime("%Y-%m"),
                    BacktestTexts.LBL_HIST_IV: point.intrinsic_value,
                    BacktestTexts.LBL_REAL_PRICE: point.market_price,
                    BacktestTexts.LBL_ERROR_GAP: point.error_pct
                })

            df = pd.DataFrame(periods_data)

            column_config = {
                BacktestTexts.LBL_HIST_IV: st.column_config.NumberColumn(format=f"%.2f {currency}"),
                BacktestTexts.LBL_REAL_PRICE: st.column_config.NumberColumn(format=f"%.2f {currency}"),
                BacktestTexts.LBL_ERROR_GAP: st.column_config.NumberColumn(format="%.1%+")
            }

            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config=column_config,
                use_container_width=True
            )

            st.caption(f"**{CommonTexts.INTERPRETATION_LABEL}** : {QuantTexts.BACKTEST_INTERPRETATION}")

    def get_display_label(self) -> str:
        return self.LABEL