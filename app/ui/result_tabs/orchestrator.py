"""
app/ui/result_tabs/orchestrator.py
ORCHESTRATEUR — Gestion des onglets de résultats.

Responsabilités :
1. Collecter tous les onglets (core + optional)
2. Filtrer selon la visibilité
3. Trier par ordre de priorité
4. Rendre avec st.tabs()
"""

from __future__ import annotations

from typing import List, Any, Optional

import streamlit as st

from core.models import ValuationResult
from app.ui.base import ResultTabBase

# Import des onglets core
from app.ui.result_tabs.core.inputs_summary import InputsSummaryTab
from app.ui.result_tabs.core.calculation_proof import CalculationProofTab
from app.ui.result_tabs.core.audit_report import AuditReportTab

# Import des onglets optionnels
from app.ui.result_tabs.optional.peer_multiples import PeerMultiplesTab
from app.ui.result_tabs.optional.sotp_breakdown import SOTPBreakdownTab
from app.ui.result_tabs.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.result_tabs.optional.historical_backtest import HistoricalBacktestTab
from app.ui.result_tabs.optional.monte_carlo_distribution import MonteCarloDistributionTab


class ResultTabOrchestrator:
    """
    Orchestre l'affichage des onglets de résultats.
    
    L'orchestrateur :
    1. Instancie tous les onglets disponibles
    2. Filtre ceux qui sont visibles
    3. Les affiche dans l'ordre défini
    
    Usage
    -----
    >>> orchestrator = ResultTabOrchestrator()
    >>> orchestrator.render(result, provider=provider)
    """
    
    # Tous les onglets disponibles (dans l'ordre souhaité)
    _ALL_TABS: List[type] = [
        # Core (toujours visibles)
        InputsSummaryTab,
        CalculationProofTab,
        AuditReportTab,
        # Optional (conditionnels)
        PeerMultiplesTab,
        SOTPBreakdownTab,
        ScenarioAnalysisTab,
        HistoricalBacktestTab,
        MonteCarloDistributionTab,
    ]
    
    def __init__(self):
        """Instancie tous les onglets."""
        self._tabs: List[ResultTabBase] = [TabClass() for TabClass in self._ALL_TABS]
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche les onglets visibles.
        
        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation.
        **kwargs
            Contexte additionnel (provider, etc.).
        """
        # Filtrer les onglets visibles
        visible_tabs = [tab for tab in self._tabs if tab.is_visible(result)]
        
        if not visible_tabs:
            st.warning("Aucun onglet à afficher.")
            return
        
        # Trier par ordre de priorité
        visible_tabs.sort(key=lambda t: t.ORDER)
        
        # Créer les onglets Streamlit
        tab_labels = [tab.get_display_label() for tab in visible_tabs]
        st_tabs = st.tabs(tab_labels)
        
        # Rendre chaque onglet
        for st_tab, tab_instance in zip(st_tabs, visible_tabs):
            with st_tab:
                try:
                    tab_instance.render(result, **kwargs)
                except Exception as e:
                    st.error(f"Erreur dans l'onglet {tab_instance.LABEL}: {str(e)}")
    
    def get_visible_count(self, result: ValuationResult) -> int:
        """Nombre d'onglets visibles pour ce résultat."""
        return sum(1 for tab in self._tabs if tab.is_visible(result))
