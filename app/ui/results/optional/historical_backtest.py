"""
app/ui/results/optional/historical_backtest.py
Pillier 4 — Ingénierie du Risque : Validation Historique.
Rôle : Preuve par l'image de la capacité prédictive du modèle.
"""

from __future__ import annotations
from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import QuantTexts, BacktestTexts, CommonTexts
from src.config.constants import TechnicalDefaults
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric
from app.ui.components.ui_charts import display_backtest_convergence_chart # Branchement de votre nouveau fichier

class HistoricalBacktestTab(ResultTabBase):
    """
    Onglet de validation historique.
    Utilise le moteur 'backtester.py' pour comparer IV vs Prix de Marché.
    """

    TAB_ID = "historical_backtest"
    LABEL = "Backtest"
    ORDER = 7
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        return bool(result.backtest_report and len(result.backtest_report.points) > 0)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu institutionnel du Backtest."""
        bt = result.backtest_report
        currency = result.financials.currency

        st.markdown(f"**{BacktestTexts.TITLE}**")
        st.caption(BacktestTexts.HELP_BACKTEST)

        # --- 1. PERFORMANCE HUB (VOTRE MOTEUR) ---
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)

            # Hit Rate : Capacité à détecter une sous-valorisation
            hit_rate = sum(1 for p in bt.points if p.was_undervalued) / len(bt.points) if bt.points else 0

            with c1: atom_kpi_metric(label=BacktestTexts.LBL_PERIODS, value=str(len(bt.points)))
            with c2: atom_kpi_metric(label=QuantTexts.LABEL_HIT_RATE, value=f"{hit_rate:.0%}")
            with c3: atom_kpi_metric(label=QuantTexts.LABEL_MAE, value=f"{bt.mean_absolute_error:.1%}")
            with c4:
                # Statut de fiabilité basé sur le MAE (Standard McKinsey)
                status = "OPTIMAL" if bt.mean_absolute_error < 0.15 else "ACCEPTABLE"
                atom_kpi_metric(label=BacktestTexts.METRIC_ACCURACY, value=status)

        # --- 2. GRAPHIQUE DE CONVERGENCE (VISUEL) ---
        # Branchement direct sur votre fonction @st.fragment
        st.write("")
        display_backtest_convergence_chart(bt, currency)

        # --- 3. DÉTAIL DES SÉQUENCES (VOTRE TABLEAU DÉPOUILLÉ) ---
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
            st.dataframe(df, hide_index=True, use_container_width=True, column_config=column_config)

            st.caption(f"**{CommonTexts.INTERPRETATION_LABEL}** : {QuantTexts.BACKTEST_INTERPRETATION}")