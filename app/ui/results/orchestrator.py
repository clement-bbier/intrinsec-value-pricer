"""
app/ui/results/orchestrator.py

ORCHESTRATEUR — GESTION DES 5 PILIERS DE RÉSULTATS (V15.0)
==========================================================
Rôle : Coordination et rendu des onglets thématiques post-calcul.
Garantit l'ordre institutionnel et la pertinence contextuelle (Smart Filtering).

Architecture des 5 Piliers :
    0. Synthèse (Executive Summary)
    1. Configuration (Inputs/Hypothèses)
    2. Trace Mathématique (Glass Box / Preuve de calcul)
    3. Rapport d'Audit (Audit & Fiabilité)
    4. Ingénierie du Risque (Quant : Monte Carlo / Scénarios / Backtest)
    5. Analyse de Marché (Relatif : Triangulation / SOTP)

Pattern : Strategy & Mediator
Style : Numpy docstrings
"""

from __future__ import annotations

import hashlib
import logging
from typing import List, Any, Optional, Dict

import streamlit as st

from src.models import ValuationResult, ValuationMode
from .base_result import ResultTabBase
from src.i18n import UIMessages, PillarLabels

# --- IMPORT DES PILIERS CORE ---
from app.ui.results.core.executive_summary import ExecutiveSummaryTab
from app.ui.results.core.inputs_summary import InputsSummaryTab
from app.ui.results.core.calculation_proof import CalculationProofTab
from app.ui.results.core.audit_report import AuditReportTab

# --- IMPORT DES PILIERS OPTIONNELS ---
from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab
from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
from app.ui.results.optional.peer_multiples import PeerMultiplesTab
from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES DE CACHE & SESSION (ST-3.4)
# ============================================================================

SESSION_KEY_RESULT_HASH = "result_cache_hash"
SESSION_KEY_MC_DATA = "cached_monte_carlo_data"


def _compute_result_hash(result: ValuationResult) -> str:
    """Calcule un hash unique pour détecter un changement de contexte de calcul."""
    key_components = (
        result.ticker,
        result.intrinsic_value_per_share,
        result.mode.value if result.mode else "N/A",
        len(result.simulation_results) if result.simulation_results else 0,
    )
    return hashlib.md5(str(key_components).encode('utf-8')).hexdigest()[:16]


def _handle_cache_invalidation(result: ValuationResult) -> bool:
    """Gère l'invalidation du cache de session si les données sources changent."""
    current_hash = _compute_result_hash(result)
    if st.session_state.get(SESSION_KEY_RESULT_HASH) != current_hash:
        st.session_state[SESSION_KEY_RESULT_HASH] = current_hash
        st.session_state[SESSION_KEY_MC_DATA] = None
        return True
    return False


# ============================================================================
# CLASSE ORCHESTRATEUR
# ============================================================================

class ResultTabOrchestrator:
    """
    Médiateur central pour le rendu des onglets de résultats financiers (ST-5.2).

    Cette classe applique le 'Smart Filtering' pour masquer les analyses
    non pertinentes (ex: Multiples pour Graham) et respecte la hiérarchie
    des 5 piliers de recherche.
    """

    # Séquençage strict des 5 piliers institutionnels
    _THEMATIC_TABS: List[type] = [
        ExecutiveSummaryTab,        # Position 0 : Synthèse Décisionnelle
        InputsSummaryTab,           # Position 1 : Configuration
        CalculationProofTab,        # Position 2 : Trace Mathématique
        AuditReportTab,             # Position 3 : Rapport d'Audit
        # --- Pilier 4 : Ingénierie du Risque ---
        MonteCarloDistributionTab,
        ScenarioAnalysisTab,
        HistoricalBacktestTab,
        # --- Pilier 5 : Analyse de Marché ---
        PeerMultiplesTab,
        SOTPBreakdownTab
    ]

    def __init__(self):
        """Initialise les instances d'onglets thématiques."""
        self._tabs: List[ResultTabBase] = [TabClass() for TabClass in self._THEMATIC_TABS]

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Coordonne le rendu des onglets Streamlit (Logical Path).

        Parameters
        ----------
        result : ValuationResult
            Le résultat complet de la valorisation issue du moteur.
        **kwargs : Any
            Arguments additionnels passés aux fonctions de rendu.
        """
        # 1. Gestion de l'état et du cache (ST-3.4)
        _handle_cache_invalidation(result)
        self._cache_technical_data(result)

        cached_mc = st.session_state.get(SESSION_KEY_MC_DATA)
        if cached_mc:
            kwargs["cached_mc_stats"] = cached_mc

        # 2. Smart Filtering & Visibilité contextuelle (Tâche 1.2.2)
        visible_tabs = self._filter_relevant_tabs(result)

        if not visible_tabs:
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
            return

        # Tri final par propriété ORDER (Double sécurité)
        visible_tabs.sort(key=lambda t: t.ORDER)

        # 3. Rendu de l'interface par onglets natifs
        tab_labels = [tab.get_display_label() for tab in visible_tabs]
        st_tabs = st.tabs(tab_labels)

        for st_tab, tab_instance in zip(st_tabs, visible_tabs):
            with st_tab:
                try:
                    # Chaque onglet reçoit le résultat et le contexte (kwargs)
                    tab_instance.render(result, **kwargs)
                except Exception as e:
                    logger.error("Error rendering tab %s: %s", tab_instance.LABEL, str(e))
                    st.error(f"Affichage momentanément indisponible : {tab_instance.LABEL}")

    def _filter_relevant_tabs(self, result: ValuationResult) -> List[ResultTabBase]:
        """
        Applique les règles métier de filtrage des onglets (ST-5.1).

        Règles :
        - Un onglet doit avoir des données (is_visible).
        - Les multiples sont masqués pour le modèle Graham (Tâche 1.2.2).
        """
        filtered = []
        is_graham = (result.mode == ValuationMode.GRAHAM)

        for tab in self._tabs:
            # 1. Vérification de la présence de données
            if not tab.is_visible(result):
                continue

            # 2. Arbitrage spécifique Graham / Multiples
            if is_graham and isinstance(tab, PeerMultiplesTab):
                continue

            filtered.append(tab)

        return filtered

    def _cache_technical_data(self, result: ValuationResult) -> None:
        """Met en cache les indicateurs statistiques de la simulation Monte Carlo."""
        if result.simulation_results and not st.session_state.get(SESSION_KEY_MC_DATA):
            import numpy as np
            # Nettoyage des None éventuels pour le calcul statistique
            v = np.array([res for res in result.simulation_results if res is not None])
            if len(v) > 0:
                st.session_state[SESSION_KEY_MC_DATA] = {
                    "median": float(np.median(v)),
                    "p10": float(np.percentile(v, 10)),
                    "p90": float(np.percentile(v, 90)),
                    "std": float(np.std(v)),
                    "count": len(v)
                }

    def clear_cache(self) -> None:
        """Réinitialise manuellement les données de cache de session."""
        st.session_state[SESSION_KEY_RESULT_HASH] = None
        st.session_state[SESSION_KEY_MC_DATA] = None