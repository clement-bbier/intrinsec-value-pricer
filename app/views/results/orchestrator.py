"""
app/views/results/orchestrator.py
ORCHESTRATOR — VALUATION RESULTS
================================
Role: Main entry point for the results view. Manages high-level layout and navigation tabs.
Architecture: Dispatches rendering to specific pillar modules (Inputs, Proof, Benchmark, Risk, Market).
"""

import streamlit as st
from src.models import ValuationResult
from src.i18n import ResultsTexts, PillarLabels

# Import Pillar Modules
from .pillars import (
    executive_summary,  # Pillar 0: Executive Dashboard (NEW)
    inputs_summary,     # Pillar 1: Detailed Inputs (MODIFIED)
    calculation_proof,  # Pillar 2: Glass Box
    benchmark_report,   # Pillar 3: Benchmark (formerly Audit)
    risk_engineering,   # Pillar 4: Risk, Scenarios, Backtest
    market_analysis     # Pillar 5: Market & SOTP
)


def render_valuation_results(result: ValuationResult) -> None:
    """
    Main View Controller for Valuation Results.

    Organizes the six pillars of the valuation into interactive tabs.

    Parameters
    ----------
    result : ValuationResult
        The fully computed valuation object containing inputs, calculated results,
        and metadata.
    """
    # 1. Main Header
    st.title(ResultsTexts.TITLE)

    # 2. Tab Definition
    # Defined in src.i18n.fr.ui.results.PillarLabels
    tabs = st.tabs([
        PillarLabels.PILLAR_0_SUMMARY,     # Executive Dashboard
        PillarLabels.PILLAR_1_CONF,        # Detailed Inputs
        PillarLabels.PILLAR_2_TRACE,       # Glass Box / Math Proof
        PillarLabels.PILLAR_3_BENCHMARK,   # Benchmark / Reliability
        PillarLabels.PILLAR_4_RISK,        # Risk / Scenarios / Backtest
        PillarLabels.PILLAR_5_MARKET       # Market Context / SOTP / Peers
    ])

    # 3. Content Dispatching

    # --- Pillar 0: Executive Summary ---
    with tabs[0]:
        executive_summary.render_dashboard(result)

    # --- Pillar 1: Inputs & Configuration ---
    with tabs[1]:
        inputs_summary.render_detailed_inputs(result)

    # --- Pillar 2: Mathematical Trace (Glass Box) ---
    with tabs[2]:
        calculation_proof.render_glass_box(result)

    # --- Pillar 3: Benchmark & Reliability ---
    # Focuses on benchmarking inputs against industry standards.
    with tabs[3]:
        benchmark_report.render_benchmark_view(result)

    # --- Pillar 4: Risk Engineering ---
    # Includes: Monte Carlo, Sensitivity, Scenarios, and Historical Backtest.
    with tabs[4]:
        risk_engineering.render_risk_analysis(result)

    # --- Pillar 5: Market Analysis ---
    # Includes: Peer Comparison, SOTP, Analyst Consensus.
    with tabs[5]:
        market_analysis.render_market_context(result)