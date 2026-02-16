"""
app/views/results/orchestrator.py

ORCHESTRATOR — VALUATION RESULTS VIEW CONTROLLER
================================================
Role: Master controller for the results page.
Responsibility:
  1. Renders the PERMANENT HEADER (Intrinsic Value vs Market Price).
  2. Manages the TABS navigation (Inputs -> Proof -> Benchmark -> Risk -> Market).
  3. Handles conditional visibility of optional pillars (Risk, SOTP).

Architecture: Central Hub calling specific Pillar Views.
Style: NumPy docstrings.
"""

import streamlit as st

# --- UI Components ---
from app.views.components.ui_kpis import atom_kpi_metric

# --- Pillar Modules (The "Spokes") ---
# These modules must exist in 'app/views/results/pillars/'
# If a file is missing, the import will fail.
from app.views.results.pillars import (
    benchmark_report,  # Pillar 3: Benchmark (formerly benchmark)
    calculation_proof,  # Pillar 2: Glass Box / Trace (formerly glass_box_trace)
    inputs_summary,  # Pillar 1: Configuration
    market_analysis,  # Pillar 5: Market Hub
    risk_engineering,  # Pillar 4: Risk Hub
)
from app.views.results.pillars.inputs_summary import get_display_currency
from src.core.formatting import CurrencyFormatter
from src.i18n import CommonTexts, KPITexts, OnboardingTexts, PillarLabels, UIMessages

# --- Data Models & i18n ---
from src.models import ValuationResult


def render_valuation_results(result: ValuationResult) -> None:
    """
    Main View Controller for Valuation Results.

    Organizes the valuation output into a persistent summary header followed by
    interactive tabs for each analysis pillar.

    Parameters
    ----------
    result : ValuationResult
        The fully computed valuation object containing inputs, calculated results,
        and metadata.
    """

    # ==========================================================================
    # 1. PERMANENT HEADER (EXECUTIVE SUMMARY)
    # ==========================================================================
    # This block is always visible, providing immediate decision metrics.
    _render_permanent_header(result)

    st.divider()

    # ==========================================================================
    # 2. DYNAMIC TAB CONSTRUCTION
    # ==========================================================================

    # Configuration list defining the tabs logic.
    # Structure: (Label, Render Function, Visibility Condition)
    tabs_config = [
        # --- Pillar 1: Configuration & Inputs ---
        (
            PillarLabels.PILLAR_1_CONF,
            lambda: inputs_summary.render_detailed_inputs(result),
            True,  # Always visible
        ),
        # --- Pillar 2: Mathematical Trace (Glass Box) ---
        (
            PillarLabels.PILLAR_2_TRACE,
            lambda: calculation_proof.render_glass_box(result),
            True,  # Always visible
        ),
        # --- Pillar 3: Benchmark & Reliability ---
        (
            PillarLabels.PILLAR_3_BENCHMARK,
            lambda: benchmark_report.render_benchmark_view(result),
            True,  # Always visible (or check if benchmark data exists)
        ),
        # --- Pillar 4: Risk Engineering (Optional) ---
        (
            PillarLabels.PILLAR_4_RISK,
            lambda: risk_engineering.render_risk_analysis(result),
            _is_risk_pillar_active(result),
        ),
        # --- Pillar 5: Market Analysis & SOTP (Optional) ---
        (
            PillarLabels.PILLAR_5_MARKET,
            lambda: market_analysis.render_market_context(result),
            _is_market_pillar_active(result),
        ),
    ]

    # Filter active tabs based on the condition (tuple index 2)
    active_tabs = [t for t in tabs_config if t[2]]

    if not active_tabs:
        st.error(UIMessages.NO_RESULT_MODULES)
        return

    # Create Streamlit tabs
    tab_labels = [t[0] for t in active_tabs]
    streamlit_tabs = st.tabs(tab_labels)

    # Render content into each tab
    for i, tab_obj in enumerate(streamlit_tabs):
        with tab_obj:
            # Execute the lambda function stored in config
            active_tabs[i][1]()


def _render_permanent_header(result: ValuationResult) -> None:
    """
    Renders the 'Always-On' top banner with key decision metrics.

    Focuses on the comparison between Intrinsic Value and Market Price,
    along with the calculated Upside/Downside.

    Parameters
    ----------
    result : ValuationResult
        The valuation data container.
    """
    st.markdown(f"# {CommonTexts.APP_TITLE}")
    st.markdown(
        f"""
                <div style="margin-top: -15px; margin-bottom: 20px;">
                    <p style="font-size: 0.8rem; color: #64748b; font-style: italic; line-height: 1.4;">
                        <strong>{OnboardingTexts.COMPLIANCE_TITLE}</strong> : {OnboardingTexts.COMPLIANCE_BODY}
                    </p>
                </div>
                """,
        unsafe_allow_html=True,
    )
    st.divider()
    # Safe Data Access via V2 Model Structure
    # Using .common namespace as defined in src/models/results/common.py
    intrinsic_val = result.results.common.intrinsic_value_per_share
    current_price = result.request.parameters.structure.current_price

    # Use currency from financial snapshot (Yahoo source of truth)
    currency = get_display_currency(result)

    upside = result.results.common.upside_pct

    # Use CurrencyFormatter for proper symbol placement (e.g., "€" suffix for EUR, "$" prefix for USD)
    formatter = CurrencyFormatter()

    # Layout: 3 centered columns for visual impact
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        # KPI 1: Intrinsic Value (Model Output)
        atom_kpi_metric(
            label=KPITexts.INTRINSIC_PRICE_LABEL,  # "Intrinsic Price"
            value=formatter.format(intrinsic_val, currency, decimals=2, smart_scale=False),
        )

    with c2:
        # KPI 2: Market Price (Reality)
        atom_kpi_metric(
            label=KPITexts.LABEL_PRICE,  # "Market Price"
            value=formatter.format(current_price, currency, decimals=2, smart_scale=False),
        )

    with c3:
        # KPI 3: Upside (Decision)
        # Display upside percentage with appropriate color coding
        atom_kpi_metric(
            label=KPITexts.UPSIDE_LABEL,  # "Upside Potential"
            value=f"{upside:+.1%}",
            delta_color="normal",
        )


def _is_risk_pillar_active(result: ValuationResult) -> bool:
    """
    Determines if the Risk Pillar should be displayed.

    Returns
    -------
    bool
        True if Monte Carlo, Sensitivity, Scenarios, or Backtest is enabled.
    """
    ext = result.request.parameters.extensions
    return ext.monte_carlo.enabled or ext.sensitivity.enabled or ext.scenarios.enabled or ext.backtest.enabled


def _is_market_pillar_active(result: ValuationResult) -> bool:
    """
    Determines if the Market Analysis Pillar should be displayed.

    Returns
    -------
    bool
        True if SOTP or Peer Comparison is enabled.
    """
    ext = result.request.parameters.extensions
    return ext.sotp.enabled or ext.peers.enabled
