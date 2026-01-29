"""
app/ui/results/optional/risk_engineering.py

PILLAR 4 — RISK ENGINEERING
===========================
Role: Unifies stochastic simulation (Monte Carlo), scenarios, and backtesting.
Design: Streamlined layout removing redundant headers and activating real-time data integration.

Architecture: ST-4.2 (Risk Hub)
Style: Numpy docstrings
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import PillarLabels, QuantTexts, BacktestTexts
from app.ui.results.base_result import ResultTabBase

# Internal rendering engines
from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab
from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
from app.ui.components.ui_charts import display_backtest_convergence_chart


class RiskEngineeringTab(ResultTabBase):
    """
    Pillar 4: Risk Engineering.
    Coordinates the dynamic display of risk mitigation and validation blocks.
    """

    TAB_ID = "risk_engineering"
    LABEL = PillarLabels.PILLAR_4_RISK
    ORDER = 4
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders risk components with visual cleanup and logical sequencing.
        """

        # --- 1. PILLAR HEADER (Normalized) ---
        st.markdown(f"### {PillarLabels.PILLAR_4_RISK}")
        st.caption(QuantTexts.MC_AUDIT_STOCH)
        st.write("")

        # --- 2. MONTE CARLO BLOCK ---
        # Note: The title "Simulation de Monte Carlo" is not explicitly repeated
        # as it is usually part of the chart header or sub-component.
        mc_tab = MonteCarloDistributionTab()
        if mc_tab.is_visible(result):
            mc_tab.render(result, **kwargs)
            st.divider()

        # --- 3. SCENARIO BLOCK (DETERMINISTIC) ---
        sc_tab = ScenarioAnalysisTab()
        if sc_tab.is_visible(result):
            st.markdown(f"#### {QuantTexts.SCENARIO_TITLE}")
            sc_tab.render(result, **kwargs)
            st.divider()

        # --- 4. BACKTESTING BLOCK (HISTORICAL VALIDATION) ---
        st.markdown(f"#### {BacktestTexts.TITLE}")

        # Verification of actual backtest data presence
        if result.backtest_report and result.backtest_report.points:
            # Direct rendering of convergence chart (Predicted vs Actual)
            display_backtest_convergence_chart(
                ticker=result.financials.ticker,
                backtest_report=result.backtest_report,
                currency=result.financials.currency
            )
            # Render accuracy metrics (MAE, Alpha) via the sub-component
            bt_tab = HistoricalBacktestTab()
            bt_tab.render(result, **kwargs)
        else:
            # Educational fallback message if historical data is missing (e.g., recent IPO)
            st.info(BacktestTexts.HELP_BACKTEST)

    def is_visible(self, result: ValuationResult) -> bool:
        """The tab is always visible to centralize risk analysis management."""
        p = result.params
        has_mc = p.monte_carlo.enable_monte_carlo if p.monte_carlo else False
        has_scenarios = p.scenarios.enabled if p.scenarios else False
        has_backtest = result.backtest_report is not None

        return has_mc or has_scenarios or has_backtest