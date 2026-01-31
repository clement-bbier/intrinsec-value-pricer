"""
app/ui/results/optional/risk_engineering.py

PILLAR 4 — RISK ENGINEERING (HUB)
=================================
Role: Unifies stochastic simulation (Monte Carlo), deterministic scenarios,
and historical backtesting into a single risk management interface.
Architecture: ST-4.2 Compliant Hub & Spokes logic.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import PillarLabels, QuantTexts, BacktestTexts
from app.ui.results.base_result import ResultTabBase

# Internal rendering engines (Spokes)
from app.ui.results.core.optional.monte_carlo_distribution import MonteCarloDistributionTab
from app.ui.results.core.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.results.core.optional.historical_backtest import HistoricalBacktestTab
from app.ui.components.ui_charts import display_backtest_convergence_chart


class RiskEngineeringTab(ResultTabBase):
    """
    Pillar 4: Risk Engineering Hub.

    This component coordinates the dynamic display of risk mitigation and
    validation blocks. It ensures a streamlined layout by removing redundant
    headers and activating real-time data integration for risk analysis.
    """

    TAB_ID = "risk_engineering"
    LABEL = PillarLabels.PILLAR_4_RISK
    ORDER = 4
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders risk components with visual cleanup and logical sequencing.

        Parameters
        ----------
        result : ValuationResult
            The complete valuation result object containing risk data.
        **kwargs : Any
            Additional rendering context (e.g., cached MC statistics).
        """

        # --- 1. PILLAR HEADER (Institutional Standard) ---
        st.markdown(f"### {PillarLabels.PILLAR_4_RISK}")
        st.caption(QuantTexts.MC_AUDIT_STOCH)
        st.write("")

        # --- 2. MONTE CARLO BLOCK (Stochastic Simulation) ---
        # Component manages its own internal rendering and visibility
        mc_tab = MonteCarloDistributionTab()
        if mc_tab.is_visible(result):
            mc_tab.render(result, **kwargs)
            st.divider()

        # --- 3. SCENARIO BLOCK (Deterministic Convictions) ---
        sc_tab = ScenarioAnalysisTab()
        if sc_tab.is_visible(result):
            st.markdown(f"#### {QuantTexts.SCENARIO_TITLE}")
            sc_tab.render(result, **kwargs)
            st.divider()

        # --- 4. BACKTESTING BLOCK (Historical Validation) ---
        st.markdown(f"#### {BacktestTexts.TITLE}")

        # Direct rendering of convergence chart if historical data is available
        if result.backtest_report and result.backtest_report.points:
            # Displays the Predicted vs Actual visual alignment
            display_backtest_convergence_chart(
                ticker=result.financials.ticker,
                backtest_report=result.backtest_report,
                currency=result.financials.currency
            )
            # Render specialized accuracy metrics (MAE, Alpha)
            bt_tab = HistoricalBacktestTab()
            bt_tab.render(result, **kwargs)
        else:
            # Educational fallback message if historical data is missing (e.g., recent IPO)
            st.info(BacktestTexts.HELP_BACKTEST)

    def is_visible(self, result: ValuationResult) -> bool:
        """
        Determines if the risk hub should be displayed.

        The tab is visible if any risk tool is activated (MC, Scenarios)
        or if historical backtest data has been successfully generated.

        Parameters
        ----------
        result : ValuationResult
            The result object to inspect for active risk modules.

        Returns
        -------
        bool
            True if at least one risk component is active or has data.
        """
        p = result.params
        return p.monte_carlo.enabled or p.scenarios.enabled or p.backtest.enabled