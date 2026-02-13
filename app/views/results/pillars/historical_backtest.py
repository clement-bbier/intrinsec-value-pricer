"""
app/views/results/pillars/historical_backtest.py
PILLAR 4 — SUB-COMPONENT: HISTORICAL VALIDATION (BACKTEST)
==========================================================
Role: Visual evidence of the model's predictive capacity over past periods.
Architecture: Injectable Grade-A Component.
"""

from typing import Any, Literal

import pandas as pd
import streamlit as st

from app.views.components.ui_charts import display_backtest_convergence_chart
from app.views.components.ui_kpis import atom_kpi_metric
from src.i18n import BacktestTexts, BenchmarkTexts, CommonTexts, QuantTexts
from src.models import ValuationResult


class HistoricalBacktestTab:
    """
    Rendering component for historical backtesting.
    Integrated vertically within the RiskEngineering or specific Backtest tab.
    Architecture: Stateless Component.
    """
    @staticmethod
    def is_visible(result: ValuationResult) -> bool:
        """
        Determines visibility based on configuration and data availability.

        Parameters
        ----------
        result : ValuationResult
            The valuation result to inspect.

        Returns
        -------
        bool
            True if backtest is enabled and contains data points.
        """
        if not result.request.parameters.extensions.backtest.enabled:
             return False
        bt = result.results.extensions.backtest
        return bt is not None and len(bt.points) > 0

    @staticmethod
    def render(result: ValuationResult, **_kwargs: Any) -> None:
        """
        Institutional Backtest rendering with accuracy metrics and convergence chart.

        Parameters
        ----------
        result : ValuationResult
            The valuation result object containing the backtest report.
        **_kwargs : Any
            Unused but required for signature compatibility.
        """
        bt = result.results.extensions.backtest
        if not bt or not bt.points:
            st.info(BacktestTexts.NO_BACKTEST_FOUND)
            return

        currency = result.request.parameters.structure.currency

        # --- SECTION HEADER ---
        st.markdown(f"#### {BacktestTexts.TITLE}")
        st.caption(BacktestTexts.HELP_BACKTEST)
        st.write("")

        # --- 1. PERFORMANCE HUB (Precision KPIs) ---
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)

            # Hit Rate calculation (IV > Market Price historically)
            hits = sum(1 for p in bt.points if p.calculated_iv > p.market_price)
            hit_rate = hits / len(bt.points) if bt.points else 0.0

            with c1:
                atom_kpi_metric(label=BacktestTexts.LBL_PERIODS, value=str(len(bt.points)))

            with c2:
                atom_kpi_metric(label=QuantTexts.LABEL_HIT_RATE, value=f"{hit_rate:.0%}")

            with c3:
                atom_kpi_metric(label=QuantTexts.LABEL_MAE, value=f"{bt.mean_absolute_error:.1%}")

            with c4:
                # Accuracy Status: MAE < 15% is considered 'Compliant' (Green)
                is_optimal = bt.mean_absolute_error < 0.15

                # Use BenchmarkTexts for generic status labels (Aligned vs Deviation)
                status_label = BenchmarkTexts.STATUS_OK if is_optimal else BenchmarkTexts.STATUS_ALERT
                grade_label = BacktestTexts.GRADE_A if is_optimal else BacktestTexts.GRADE_B

                # Explicit typing for linter compliance
                delta_color: Literal["normal", "off", "inverse"] = "normal" if is_optimal else "off"

                atom_kpi_metric(
                    label=BacktestTexts.METRIC_ACCURACY,
                    value=status_label.upper(),
                    delta=grade_label,
                    delta_color=delta_color
                )

        # --- 2. CONVERGENCE CHART ---
        st.write("")
        display_backtest_convergence_chart(
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
                    BacktestTexts.LBL_HIST_IV: point.calculated_iv,
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
