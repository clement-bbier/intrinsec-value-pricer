"""
app/ui/results/orchestrator.py

ORCHESTRATOR — 5 PILLARS RESULTS MANAGEMENT
===========================================
Role: Coordinates the Golden Header and distributes data across thematic tabs.
Fusion ST-4.2: Integrated Market Analysis & SOTP.

Architecture: Senior Grade Orchestration.
Style: Numpy docstrings.
"""

from __future__ import annotations
import hashlib
import logging
import numpy as np
from typing import List, Any, Type

import streamlit as st

from src.models import ValuationResult, ValuationMode
from src.i18n import UIMessages, KPITexts, AuditTexts
from src.utilities.formatting import format_smart_number
from .base_result import ResultTabBase

# --- CORE PILLARS ---
from app.ui.results.core.inputs_summary import InputsSummaryTab
from app.ui.results.core.calculation_proof import CalculationProofTab
from app.ui.results.core.audit_report import AuditReportTab

# --- OPTIONAL & VERSATILE PILLARS ---
from app.ui.results.optional.risk_engineering import RiskEngineeringTab
from app.ui.results.optional.peer_multiples import MarketAnalysisTab

logger = logging.getLogger(__name__)

SESSION_KEY_RESULT_HASH = "valuation_context_hash"
SESSION_KEY_MC_DATA = "stats_monte_carlo_cache"

class ResultTabOrchestrator:
    """
    Orchestrator for the valuation results interface.
    Manages the institutional hierarchy of the restructured 5 Pillars.
    """

    # Reading sequence follows professional analyst logic
    _THEMATIC_TABS_CLASSES: List[Type[ResultTabBase]] = [
        InputsSummaryTab,        # Pillar 1: Input Data & Hypotheses
        CalculationProofTab,     # Pillar 2: Calculation Proof (Glass Box)
        AuditReportTab,          # Pillar 3: Reliability Audit
        RiskEngineeringTab,      # Pillar 4: Risk Engineering
        MarketAnalysisTab        # Pillar 5: Market Analysis & SOTP
    ]

    def __init__(self):
        """Initializes tab instances for rendering."""
        self._tabs = [TabClass() for TabClass in self._THEMATIC_TABS_CLASSES]

    @staticmethod
    def _render_global_header(result: ValuationResult) -> None:
        """
        Renders the fixed identity band (Golden Header).
        Displays critical metrics: Ticker, Name, Sector, IV vs Price, and Confidence.
        """
        f = result.financials
        currency = f.currency

        with st.container(border=True):
            col_id, col_val, col_audit = st.columns([2, 2.5, 1.5])

            with col_id:
                # Identity Block
                st.markdown(f"### {f.ticker}")
                st.caption(f"{f.name} | {f.sector}")

            with col_val:
                # Valuation Synthesis Block
                try:
                    upside = float(result.upside_pct) if result.upside_pct is not None else 0.0
                except (TypeError, ValueError):
                    upside = 0.0

                color = "green" if upside >= 0 else "red"

                st.markdown(f"**{KPITexts.LABEL_IV}**")
                val_str = format_smart_number(result.intrinsic_value_per_share, currency=currency)
                diff_str = f"{upside:+.1%}"

                st.markdown(f"## {val_str} (:{color}[{diff_str}])")
                st.caption(f"{KPITexts.LABEL_PRICE} : {result.market_price:,.2f} {currency}")

            with col_audit:
                # Confidence/Reliability Block
                if result.audit_report:
                    rating = result.audit_report.rating
                    # Institutional color mapping
                    badge_color = "#10b981" if rating.startswith("A") else "#f59e0b" if rating.startswith("B") else "#ef4444"

                    st.markdown(f"<div style='text-align:right;'>{KPITexts.EXEC_CONFIDENCE}</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='text-align:right; font-size: 2.5rem; font-weight: bold; color: {badge_color};'>"
                        f"{rating}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<div style='text-align:right;'>{AuditTexts.DEFAULT_FORMULA}</div>", unsafe_allow_html=True)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Coordinates the dynamic rendering of tabs with technical cache management.
        """
        self._render_global_header(result)
        st.write("")

        # 1. Technical Cache Management
        self._handle_cache_invalidation(result)
        self._cache_technical_data(result)

        # Inject cached stats into tab context
        mc_stats = st.session_state.get(SESSION_KEY_MC_DATA)
        if mc_stats:
            kwargs["mc_stats"] = mc_stats

        # 2. Filtering & Rendering
        visible_tabs = self._filter_relevant_tabs(result)
        if not visible_tabs:
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
            return

        # Render labels via i18n
        tab_labels = [tab.get_display_label() for tab in visible_tabs]
        st_tabs = st.tabs(tab_labels)

        for st_tab, tab_instance in zip(st_tabs, visible_tabs):
            with st_tab:
                try:
                    tab_instance.render(result, **kwargs)
                except Exception as e:
                    logger.error(f"Render Error [{tab_instance.TAB_ID}]: {str(e)}")
                    st.error(f"{UIMessages.CHART_UNAVAILABLE}")

    def _filter_relevant_tabs(self, result: ValuationResult) -> List[ResultTabBase]:
        """
        Filters tabs based on valuation mode and visibility constraints.
        E. g., Graham excludes relative market analysis (Pillar 5).
        """
        filtered = []
        mode = result.request.mode if result.request else None
        is_graham = (mode == ValuationMode.GRAHAM)

        for tab in self._tabs:
            if not tab.is_visible(result):
                continue

            # Specific exclusion for Graham screening model
            if is_graham and isinstance(tab, MarketAnalysisTab):
                continue

            filtered.append(tab)

        return sorted(filtered, key=lambda t: t.ORDER)

    @staticmethod
    def _handle_cache_invalidation(result: ValuationResult) -> None:
        """
        Invalidates the internal statistics cache if the valuation context changes.
        """
        ctx_payload = (
            str(result.financials.ticker),
            str(result.intrinsic_value_per_share),
            str(result.request.mode.value if result.request else "NONE"),
            int(len(result.simulation_results) if result.simulation_results else 0)
        )

        # Generate lightweight context hash
        current_hash = hashlib.md5(str(ctx_payload).encode()).hexdigest()[:12]

        if st.session_state.get(SESSION_KEY_RESULT_HASH) != current_hash:
            st.session_state[SESSION_KEY_RESULT_HASH] = current_hash
            st.session_state[SESSION_KEY_MC_DATA] = None

    @staticmethod
    def _cache_technical_data(result: ValuationResult) -> None:
        """
        Calculates and caches Monte Carlo statistics to optimize UI performance.
        """
        if result.simulation_results and not st.session_state.get(SESSION_KEY_MC_DATA):
            data = np.array([r for r in result.simulation_results if r is not None])
            if data.size > 0:
                st.session_state[SESSION_KEY_MC_DATA] = {
                    "median": np.median(data),
                    "p10": np.percentile(data, 10),
                    "p90": np.percentile(data, 90),
                    "std": np.std(data),
                    "var_95": np.percentile(data, 5) # Value at Risk (5th percentile)
                }