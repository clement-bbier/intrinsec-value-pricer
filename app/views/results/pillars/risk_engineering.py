"""
app/views/results/pillars/risk_engineering.py

PILLAR 4 — RISK ENGINEERING (HUB)
=================================
Role: Unifies stochastic simulation (Monte Carlo), deterministic scenarios,
sensitivity analysis, and historical backtesting into a single risk management interface.
Architecture: ST-4.2 Compliant Hub & Spokes logic.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import PillarLabels, QuantTexts, BacktestTexts

# Internal rendering engines (Spokes)
# Note: These components use static methods (_render, _is_visible)
from app.views.results.pillars.monte_carlo_distribution import MonteCarloDistributionTab
from app.views.results.pillars.sensitivity import SensitivityAnalysisTab
from app.views.results.pillars.scenario_analysis import ScenarioAnalysisTab
from app.views.results.pillars.historical_backtest import HistoricalBacktestTab


def render_risk_analysis(result: ValuationResult, **kwargs: Any) -> None:
    """
    Renders Pillar 4: Risk Engineering Hub.

    This function coordinates the dynamic display of risk mitigation and
    validation blocks. It acts as a controller, checking the visibility
    of each sub-component (Monte Carlo, Scenarios, Backtest) and rendering
    them sequentially if active.

    Parameters
    ----------
    result : ValuationResult
        The complete valuation result object containing risk data.
    **kwargs : Any
        Additional rendering context (e.g., cached MC statistics).
    """

    # --- 1. PILLAR HEADER (Institutional Standard) ---
    st.header(PillarLabels.PILLAR_4_RISK)
    st.caption(QuantTexts.MC_AUDIT_STOCH)
    st.divider()

    # --- 2. MONTE CARLO BLOCK (Stochastic Simulation) ---
    # The Hub delegates rendering to the Spoke if the simulation is active.
    if MonteCarloDistributionTab.is_visible(result):
        MonteCarloDistributionTab.render(result, **kwargs)
        st.divider()

    # --- 3. SENSITIVITY BLOCK (Variable Impact) ---
    # Renders the WACC/Growth heatmap if sensitivity analysis was requested.
    if SensitivityAnalysisTab.is_visible(result):
        SensitivityAnalysisTab.render(result, **kwargs)
        st.divider()

    # --- 4. SCENARIO BLOCK (Deterministic Convictions) ---
    # Renders Bull/Bear cases and weighted expectations.
    if ScenarioAnalysisTab.is_visible(result):
        ScenarioAnalysisTab.render(result, **kwargs)
        st.divider()

    # --- 5. BACKTESTING BLOCK (Historical Validation) ---
    # Renders the convergence chart and accuracy metrics.
    if HistoricalBacktestTab.is_visible(result):
        HistoricalBacktestTab.render(result, **kwargs)
    else:
        # Educational fallback message if historical data is missing (e.g., recent IPO)
        # Only show if other risk modules are active to avoid an empty tab,
        # or implies this is the end of the risk section.
        st.markdown(f"#### {BacktestTexts.TITLE}")
        st.info(BacktestTexts.HELP_BACKTEST)