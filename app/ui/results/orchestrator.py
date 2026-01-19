"""
app/ui/result_tabs/orchestrator.py

ORCHESTRATEUR — GESTION CENTRALISÉE DES ONGLET DE RÉSULTATS

Rôle : Coordination et rendu des onglets de résultats post-calcul
Pattern : Mediator (GoF) + Factory Method
Style : Numpy docstrings

Version : V1.0 — ST-2.2
Risques financiers : Coordination d'affichage, pas de calculs

Dépendances critiques :
- streamlit >= 1.28.0
- core.models.ValuationResult
- app.ui.base.ResultTabBase

Responsabilités :
1. Collecter tous les onglets (core + optional)
2. Filtrer selon la visibilité (conditions métier)
3. Trier par ordre de priorité (ORDER attribute)
4. Rendre avec st.tabs() et gestion d'erreurs

Architecture :
- Core tabs : Toujours visibles (executive, inputs, calculation, audit)
- Optional tabs : Conditionnels (multiples, sotp, scenarios, backtest, mc)
"""

from __future__ import annotations

from typing import List, Any, Optional

import streamlit as st

from src.domain.models import ValuationResult
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


class ResultTabOrchestrator:
    """
    Orchestrateur centralisé des onglets de résultats.

    Implémente le pattern Mediator pour coordonner l'affichage des différents
    onglets de résultats. Gère le cycle de vie complet : instanciation,
    filtrage, tri et rendu avec gestion d'erreurs.

    Attributes
    ----------
    _ALL_TABS : List[type]
        Liste ordonnée des classes d'onglets (core + optional).
    _tabs : List[ResultTabBase]
        Instances des onglets après instanciation.

    Class Attributes
    ----------------
    Core tabs (toujours visibles) :
        - ExecutiveSummaryTab (résumé exécutif)
        - InputsSummaryTab (récapitulatif inputs)
        - CalculationProofTab (preuve de calcul)
        - AuditReportTab (rapport d'audit)

    Optional tabs (conditionnels) :
        - PeerMultiplesTab (triangulation sectorielle)
        - SOTPBreakdownTab (décomposition SOTP)
        - ScenarioAnalysisTab (analyse scénarios)
        - HistoricalBacktestTab (backtest historique)
        - MonteCarloDistributionTab (distribution MC)

    Examples
    --------
    >>> orchestrator = ResultTabOrchestrator()
    >>> orchestrator.render(result, provider=data_provider)

    Notes
    -----
    L'ordre d'affichage est déterminé par l'attribut ORDER de chaque onglet.
    Les erreurs dans un onglet n'affectent pas les autres onglets.
    """
    
    # Tous les onglets disponibles (dans l'ordre souhaité)
    _ALL_TABS: List[type] = [
        # Core (toujours visibles)
        ExecutiveSummaryTab,
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
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
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
