"""
app/ui/results/orchestrator.py

ORCHESTRATEUR — GESTION CENTRALISÉE DES ONGLETS DE RÉSULTATS

Version : V2.1 — PDF Export Removed
Rôle : Coordination et rendu des onglets de résultats post-calcul
Pattern : Mediator (GoF) + Factory Method + Session State Cache
"""

from __future__ import annotations

import hashlib
from typing import List, Any, Optional, Dict

import streamlit as st

from src.models import ValuationResult
# Import PitchbookData supprimé car lié à l'export PDF
from app.ui.base import ResultTabBase
from src.i18n import UIMessages

# Import des onglets core
from app.ui.results.core.executive_summary import ExecutiveSummaryTab
from app.ui.results.core.inputs_summary import InputsSummaryTab
from app.ui.results.core.calculation_proof import CalculationProofTab
from app.ui.results.core.audit_report import AuditReportTab

# Import des onglets optionnels
from app.ui.results.optional.peer_multiples import PeerMultiplesTab
from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab
from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab


# ============================================================================
# CONSTANTES DE SESSION (ST-3.4)
# ============================================================================

SESSION_KEY_RESULT_HASH = "result_cache_hash"
SESSION_KEY_MC_DATA = "cached_monte_carlo_data"
SESSION_KEY_ACTIVE_TAB = "active_result_tab"
SESSION_KEY_RENDER_CONTEXT = "render_context_cache"


def _compute_result_hash(result: ValuationResult) -> str:
    """Calcule un hash unique pour détecter si le résultat a changé."""
    key_components = (
        result.ticker,
        result.intrinsic_value_per_share,
        result.market_price,
        result.mode.value if result.mode else "UNKNOWN_MODE",
        len(result.simulation_results) if result.simulation_results else 0,
    )
    hash_input = str(key_components).encode('utf-8')
    return hashlib.md5(hash_input).hexdigest()[:16]


def _init_session_cache() -> None:
    """Initialise les clés de cache de session si absentes."""
    if SESSION_KEY_RESULT_HASH not in st.session_state:
        st.session_state[SESSION_KEY_RESULT_HASH] = None
    if SESSION_KEY_MC_DATA not in st.session_state:
        st.session_state[SESSION_KEY_MC_DATA] = None
    if SESSION_KEY_ACTIVE_TAB not in st.session_state:
        st.session_state[SESSION_KEY_ACTIVE_TAB] = 0
    if SESSION_KEY_RENDER_CONTEXT not in st.session_state:
        st.session_state[SESSION_KEY_RENDER_CONTEXT] = {}


def _should_invalidate_cache(result: ValuationResult) -> bool:
    """Détermine si le cache doit être invalidé."""
    current_hash = _compute_result_hash(result)
    cached_hash = st.session_state.get(SESSION_KEY_RESULT_HASH)

    if cached_hash != current_hash:
        st.session_state[SESSION_KEY_RESULT_HASH] = current_hash
        st.session_state[SESSION_KEY_MC_DATA] = None
        st.session_state[SESSION_KEY_RENDER_CONTEXT] = {}
        return True
    return False


def cache_monte_carlo_data(result: ValuationResult) -> None:
    """Met en cache les données Monte Carlo pour éviter les recalculs."""
    if result.simulation_results and not st.session_state.get(SESSION_KEY_MC_DATA):
        import numpy as np
        values = result.simulation_results
        st.session_state[SESSION_KEY_MC_DATA] = {
            "count": len(values),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "p10": float(np.percentile(values, 10)),
            "p25": float(np.percentile(values, 25)),
            "p75": float(np.percentile(values, 75)),
            "p90": float(np.percentile(values, 90)),
        }


def get_cached_mc_stats() -> Optional[Dict[str, float]]:
    """Récupère les statistiques MC depuis le cache."""
    return st.session_state.get(SESSION_KEY_MC_DATA)


class ResultTabOrchestrator:
    """Orchestrateur centralisé des onglets de résultats sans export PDF."""

    _ALL_TABS: List[type] = [
        ExecutiveSummaryTab,
        InputsSummaryTab,
        CalculationProofTab,
        AuditReportTab,
        PeerMultiplesTab,
        SOTPBreakdownTab,
        ScenarioAnalysisTab,
        HistoricalBacktestTab,
        MonteCarloDistributionTab,
    ]

    def __init__(self):
        self._tabs: List[ResultTabBase] = [TabClass() for TabClass in self._ALL_TABS]

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche les onglets avec gestion optimisée du cache."""
        _init_session_cache()
        _should_invalidate_cache(result)

        if result.simulation_results:
            cache_monte_carlo_data(result)

        cached_mc = get_cached_mc_stats()
        if cached_mc:
            kwargs["cached_mc_stats"] = cached_mc

        visible_tabs = [tab for tab in self._tabs if tab.is_visible(result)]

        if not visible_tabs:
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
            return

        visible_tabs.sort(key=lambda t: t.ORDER)

        tab_labels = [tab.get_display_label() for tab in visible_tabs]
        st_tabs = st.tabs(tab_labels)

        for st_tab, tab_instance in zip(st_tabs, visible_tabs):
            with st_tab:
                try:
                    tab_instance.render(result, **kwargs)
                except Exception as e:
                    st.error(f"Erreur dans l'onglet {tab_instance.LABEL}: {str(e)}")

    def get_visible_count(self, result: ValuationResult) -> int:
        return sum(1 for tab in self._tabs if tab.is_visible(result))

    def clear_cache(self) -> None:
        st.session_state[SESSION_KEY_RESULT_HASH] = None
        st.session_state[SESSION_KEY_MC_DATA] = None
        st.session_state[SESSION_KEY_RENDER_CONTEXT] = {}