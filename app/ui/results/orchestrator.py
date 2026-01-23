"""
app/ui/results/orchestrator.py

ORCHESTRATEUR — GESTION DES 5 PILIERS DE RÉSULTATS (V14.1)

Rôle : Coordination et rendu des onglets thématiques post-calcul.
Ordre de préséance :
    1. Configuration (Inputs/Hypothèses)
    2. Trace Mathématique (Glass Box / Preuve de calcul)
    3. Rapport d'Audit (Audit & Fiabilité)
    4. Analyse de Marché (Relative / Triangulation)
    5. Ingénierie du Risque (Monte Carlo / Scénarios / Backtest)

Standard de documentation : NumPy style.
"""

from __future__ import annotations

import hashlib
import logging
from typing import List, Any, Optional, Dict

import streamlit as st

from src.models import ValuationResult
from app.ui.base import ResultTabBase
from src.i18n import UIMessages

# Import des onglets piliers (Core & Optionnels)
from app.ui.results.core.inputs_summary import InputsSummaryTab
from app.ui.results.core.calculation_proof import CalculationProofTab
from app.ui.results.core.audit_report import AuditReportTab
from app.ui.results.optional.peer_multiples import PeerMultiplesTab
from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES DE CACHE & SESSION (ST-3.4)
# ============================================================================

SESSION_KEY_RESULT_HASH = "result_cache_hash"
SESSION_KEY_MC_DATA = "cached_monte_carlo_data"
SESSION_KEY_ACTIVE_TAB = "active_result_tab"


def _compute_result_hash(result: ValuationResult) -> str:
    """
    Calcule un hash unique pour détecter un changement de contexte de calcul.

    Parameters
    ----------
    result : ValuationResult
        L'objet de résultat de valorisation à hasher.

    Returns
    -------
    str
        Hash MD5 tronqué à 16 caractères.
    """
    key_components = (
        result.ticker,
        result.intrinsic_value_per_share,
        result.mode.value if result.mode else "N/A",
        len(result.simulation_results) if result.simulation_results else 0,
    )
    return hashlib.md5(str(key_components).encode('utf-8')).hexdigest()[:16]


def _handle_cache_invalidation(result: ValuationResult) -> bool:
    """
    Gère l'invalidation du cache de session si les données sources changent.

    Parameters
    ----------
    result : ValuationResult
        Le nouveau résultat de valorisation.

    Returns
    -------
    bool
        True si le cache a été invalidé, False sinon.
    """
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
    Médiateur central pour le rendu des onglets de résultats financiers.

    Cette classe coordonne l'affichage dynamique des onglets en fonction de
    la visibilité des résultats (ex: masquer Monte Carlo si désactivé)
    et gère la mise en cache des statistiques lourdes.

    Attributes
    ----------
    _THEMATIC_TABS : List[type]
        Liste ordonnée des classes d'onglets (source de vérité pour l'UI).
    """

    # DT-022 : Ordre thématique demandé (Configuration -> Trace -> Audit)
    _THEMATIC_TABS: List[type] = [
        InputsSummaryTab,           # Position 1 : Configuration
        CalculationProofTab,        # Position 2 : Trace Mathématique
        AuditReportTab,             # Position 3 : Rapport d'Audit
        PeerMultiplesTab,           # Position 4 : Analyse de Marché
        MonteCarloDistributionTab,  # Position 5 : Ingénierie du Risque
    ]

    def __init__(self):
        """Initialise les instances d'onglets thématiques."""
        self._tabs: List[ResultTabBase] = [TabClass() for TabClass in self._THEMATIC_TABS]

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Coordonne le rendu des onglets Streamlit.

        Gère l'invalidation du cache, le calcul des statistiques de simulation
        et le rendu séquentiel des onglets visibles.

        Parameters
        ----------
        result : ValuationResult
            Le résultat complet de la valorisation.
        **kwargs : Any
            Arguments additionnels passés aux fonctions de rendu des onglets.
        """
        # 1. Gestion de l'état et du cache
        _handle_cache_invalidation(result)
        self._cache_technical_data(result)

        # Injection des statistiques MC dans le contexte de rendu si existantes
        cached_mc = st.session_state.get(SESSION_KEY_MC_DATA)
        if cached_mc:
            kwargs["cached_mc_stats"] = cached_mc

        # 2. Filtrage des onglets selon la pertinence du résultat
        visible_tabs = [tab for tab in self._tabs if tab.is_visible(result)]
        if not visible_tabs:
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
            return

        # Tri selon la propriété ORDER interne des classes (sécurité additionnelle)
        visible_tabs.sort(key=lambda t: t.ORDER)

        # 3. Rendu de l'interface Streamlit (Tabs natifs)
        tab_labels = [tab.get_display_label() for tab in visible_tabs]
        st_tabs = st.tabs(tab_labels)

        for st_tab, tab_instance in zip(st_tabs, visible_tabs):
            with st_tab:
                try:
                    tab_instance.render(result, **kwargs)
                except Exception as e:
                    logger.error("Error rendering tab %s: %s", tab_instance.LABEL, str(e))
                    st.error(f"Affichage momentanément indisponible : {tab_instance.LABEL}")

    def _cache_technical_data(self, result: ValuationResult) -> None:
        """
        Met en cache les indicateurs statistiques de la simulation Monte Carlo.

        Évite de recalculer les percentiles (p10, p90, etc.) sur de gros volumes
        de données à chaque changement d'onglet utilisateur.

        Parameters
        ----------
        result : ValuationResult
            Le résultat contenant potentiellement des listes de simulation.
        """
        if result.simulation_results and not st.session_state.get(SESSION_KEY_MC_DATA):
            import numpy as np
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