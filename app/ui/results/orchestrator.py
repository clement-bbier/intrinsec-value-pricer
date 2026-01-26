"""
app/ui/results/orchestrator.py
ORCHESTRATEUR — GESTION DES 5 PILIERS DE RÉSULTATS
==========================================================
"""

from __future__ import annotations
import hashlib
import logging
import numpy as np
from typing import List, Any, Dict, Type

import streamlit as st

from src.models import ValuationResult, ValuationMode
from src.i18n import UIMessages, PillarLabels, KPITexts
from src.utilities.formatting import format_smart_number
from .base_result import ResultTabBase

# --- PILLIERS CORE & OPTIONNELS ---
from app.ui.results.core.executive_summary import ExecutiveSummaryTab
from app.ui.results.core.inputs_summary import InputsSummaryTab
from app.ui.results.core.calculation_proof import CalculationProofTab
from app.ui.results.core.audit_report import AuditReportTab
from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab
from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
from app.ui.results.optional.peer_multiples import PeerMultiplesTab
from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab

logger = logging.getLogger(__name__)

SESSION_KEY_RESULT_HASH = "valuation_context_hash"
SESSION_KEY_MC_DATA = "stats_monte_carlo_cache"

class ResultTabOrchestrator:
    _THEMATIC_TABS_CLASSES: List[Type[ResultTabBase]] = [
        ExecutiveSummaryTab, InputsSummaryTab, CalculationProofTab,
        AuditReportTab, MonteCarloDistributionTab, ScenarioAnalysisTab,
        HistoricalBacktestTab, PeerMultiplesTab, SOTPBreakdownTab
    ]

    def __init__(self):
        self._tabs = [TabClass() for TabClass in self._THEMATIC_TABS_CLASSES]

    def _render_global_header(self, result: ValuationResult) -> None:
        """Rendu du bandeau d'identité fixe (Golden Header)."""
        f = result.financials
        currency = f.currency  # Accès sécurisé via financials

        with st.container(border=True):
            col_id, col_val, col_audit = st.columns([2, 2.5, 1.5])

            with col_id:
                st.markdown(f"### {f.ticker}")
                st.caption(f"{f.name} | {f.sector}")

            with col_val:
                # Correction Naming : upside_pct au lieu de upside
                upside = result.upside_pct or 0.0
                color = "green" if upside > 0 else "red"

                st.markdown(f"**{KPITexts.LABEL_IV}**")
                # Correction Naming : intrinsic_value_per_share
                val_str = f"{format_smart_number(result.intrinsic_value_per_share, currency=currency)}"
                diff_str = f"{upside:+.1%}"

                st.markdown(f"## {val_str} (:{color}[{diff_str}])")
                st.caption(f"{KPITexts.LABEL_PRICE} : {result.market_price:,.2f} {currency}")

            with col_audit:
                if result.audit_report:
                    rating = result.audit_report.rating
                    badge_color = "green" if rating.startswith("A") else "orange" if rating.startswith("B") else "red"
                    st.markdown(f"<div style='text-align:right;'>{KPITexts.EXEC_CONFIDENCE}</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='text-align:right; font-size: 2.5rem; font-weight: bold; color: {badge_color};'>"
                        f"{rating}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<div style='text-align:right;'>N/A</div>", unsafe_allow_html=True)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Coordonne le rendu dynamique des onglets."""

        # --- PHASE 1 : AFFICHAGE DU HEADER FIXE ---
        self._render_global_header(result)
        st.write("") # Espacement léger

        # 1. Gestion du Cache
        self._handle_cache_invalidation(result)
        self._cache_technical_data(result)
        mc_stats = st.session_state.get(SESSION_KEY_MC_DATA)
        if mc_stats:
            kwargs["mc_stats"] = mc_stats

        # 2. Filtrage & Rendu des Onglets
        visible_tabs = self._filter_relevant_tabs(result)
        if not visible_tabs:
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
            return

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
        filtered = []
        is_graham = (result.mode == ValuationMode.GRAHAM)
        for tab in self._tabs:
            if not tab.is_visible(result): continue
            if is_graham and isinstance(tab, (MonteCarloDistributionTab, PeerMultiplesTab)): continue
            filtered.append(tab)
        return sorted(filtered, key=lambda t: t.ORDER)

    def _handle_cache_invalidation(self, result: ValuationResult) -> None:
        ctx_payload = (result.ticker, result.intrinsic_value_per_share,
                       result.mode.value if result.mode else "NONE",
                       len(result.simulation_results) if result.simulation_results else 0)
        current_hash = hashlib.md5(str(ctx_payload).encode()).hexdigest()[:12]
        if st.session_state.get(SESSION_KEY_RESULT_HASH) != current_hash:
            st.session_state[SESSION_KEY_RESULT_HASH] = current_hash
            st.session_state[SESSION_KEY_MC_DATA] = None

    def _cache_technical_data(self, result: ValuationResult) -> None:
        if result.simulation_results and not st.session_state.get(SESSION_KEY_MC_DATA):
            data = np.array([r for r in result.simulation_results if r is not None])
            if data.size > 0:
                st.session_state[SESSION_KEY_MC_DATA] = {
                    "median": np.median(data), "p10": np.percentile(data, 10),
                    "p90": np.percentile(data, 90), "std": np.std(data),
                    "var_95": np.percentile(data, 5)
                }