"""
app/ui/results/optional/historical_backtest.py

PILLAR 4 — SUB-COMPONENT: HISTORICAL VALIDATION (BACKTEST)
==========================================================
Role: Visual evidence of the model's predictive capacity over past periods.
Architecture: Injectable Grade-A Component.
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
    Rendering component for historical backtesting.
    Integrated vertically within the RiskEngineering or specific Backtest tab.
    """

    TAB_ID = "historical_backtest"
    LABEL = BacktestTexts.LABEL
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible only if the engine generated at least one historical comparison point."""
        return result.params.backtest.enabled

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Institutional Backtest rendering with accuracy metrics and convergence chart."""
        if not result.backtest_report or not result.backtest_report.points:
            st.info(BacktestTexts.NO_BACKTEST_FOUND)
            return
        bt = result.backtest_report
        currency = result.financials.currency

        # --- SECTION HEADER (Standardized ####) ---
        st.markdown(f"#### {BacktestTexts.TITLE}")
        st.caption(BacktestTexts.HELP_BACKTEST)
        st.write("")

        # --- 1. PERFORMANCE HUB (Precision KPIs) ---
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)

            # Hit Rate: percentage of times IV correctly predicted undervaluation
            hit_rate = sum(1 for p in bt.points if p.was_undervalued) / len(bt.points) if bt.points else 0

            with c1:
                atom_kpi_metric(label=BacktestTexts.LBL_PERIODS, value=str(len(bt.points)))

            with c2:
                atom_kpi_metric(label=QuantTexts.LABEL_HIT_RATE, value=f"{hit_rate:.0%}")

            with c3:
                atom_kpi_metric(label=QuantTexts.LABEL_MAE, value=f"{bt.mean_absolute_error:.1%}")

            with c4:
                # Accuracy Status: MAE < 15% is considered 'Compliant' by financial standards
                is_optimal = bt.mean_absolute_error < 0.15
                status_label = AuditTexts.STATUS_OK if is_optimal else AuditTexts.STATUS_ALERT

                # Dynamic grade labels from i18n
                grade_label = BacktestTexts.GRADE_A if is_optimal else BacktestTexts.GRADE_B

                atom_kpi_metric(
                    label=BacktestTexts.METRIC_ACCURACY,
                    value=status_label.upper(),
                    delta=grade_label,
                    delta_color="normal" if is_optimal else "off"
                )

        # --- 2. CONVERGENCE CHART (IV vs Price Visualization) ---
        st.write("")
        display_backtest_convergence_chart(
            ticker=result.financials.ticker,
            backtest_report=bt,
            currency=currency
        )

        # --- 3. SEQUENCE DETAILS (Transparency Dataframe) ---

        st.write("")
        with st.expander(BacktestTexts.SEC_RESULTS):
            periods_data = []
            for point in bt.points:
                periods_data.append({
                    BacktestTexts.LBL_DATE: point.valuation_date.strftime("%Y-%m"),
                    BacktestTexts.LBL_HIST_IV: point.intrinsic_value,
                    BacktestTexts.LBL_REAL_PRICE: point.market_price,
                    BacktestTexts.LBL_ERROR_GAP: point.error_pct
                })

            df = pd.DataFrame(periods_data)

            # Institutional column configuration
            column_config = {
                BacktestTexts.LBL_HIST_IV: st.column_config.NumberColumn(format=f"%.2f {currency}"),
                BacktestTexts.LBL_REAL_PRICE: st.column_config.NumberColumn(format=f"%.2f {currency}"),
                BacktestTexts.LBL_ERROR_GAP: st.column_config.NumberColumn(format="%.1%+")
            }

            st.dataframe(
                df,
                hide_index=True,
                column_config=column_config,
                width="stretch"
            )

            st.caption(f"**{CommonTexts.INTERPRETATION_LABEL}** : {QuantTexts.BACKTEST_INTERPRETATION}")