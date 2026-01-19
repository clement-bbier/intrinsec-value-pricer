"""
app/adapters/streamlit_adapters.py

ADAPTATEURS STREAMLIT — COUCHE D'ADAPTATION UI

Rôle : Implémentation des interfaces core avec Streamlit
Pattern : Adapter (GoF)
Style : Numpy docstrings

Version : V2.0 — ST-2.2 (Migration ResultTabOrchestrator)
Risques financiers : Coordination d'affichage UI, pas de calculs

Dépendances critiques :
- streamlit >= 1.28.0
- core.interfaces.IUIProgressHandler
- core.interfaces.IResultRenderer
- app.ui.results.orchestrator.ResultTabOrchestrator

Responsabilités :
- StreamlitProgressHandler : Gestion de la progression (st.status)
- StreamlitResultRenderer : Rendu des résultats via orchestrateur

Migration ST-2.2 :
- Ancien : Délégation directe vers ui_kpis.py
- Nouveau : Orchestration centralisée des onglets ResultTabBase
"""

from typing import Any, Optional

import streamlit as st

from src.interfaces import IUIProgressHandler, IResultRenderer
import app.ui.components.ui_kpis as ui_kpis


class StreamlitProgressHandler(IUIProgressHandler):
    """
    Adaptateur Streamlit pour la gestion de progression.

    Encapsule le composant st.status de Streamlit pour implémenter
    l'interface IUIProgressHandler. Fournit un feedback visuel
    pendant les opérations longues.

    Attributes
    ----------
    _status : Optional[st.status]
        Instance Streamlit du status en cours, None si inactif.

    Examples
    --------
    >>> handler = StreamlitProgressHandler()
    >>> with handler.start_status("Calcul en cours..."):
    ...     handler.update_status("Étape 1/3")
    ...     # ... calculs ...
    ...     handler.complete_status("Terminé")
    """
    
    def __init__(self):
        self._status = None
    
    def start_status(self, label: str) -> "StreamlitProgressHandler":
        self._status = st.status(label, expanded=True)
        return self
    
    def update_status(self, message: str) -> None:
        if self._status:
            self._status.write(message)
    
    def complete_status(self, label: str, state: str = "complete") -> None:
        if self._status:
            self._status.update(label=label, state=state, expanded=False)
    
    def error_status(self, label: str) -> None:
        if self._status:
            self._status.update(label=label, state="error", expanded=True)
    
    def __enter__(self) -> "StreamlitProgressHandler":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class StreamlitResultRenderer(IResultRenderer):
    """
    Adaptateur Streamlit pour le rendu des résultats de valorisation.

    Implémente IResultRenderer en utilisant l'architecture ResultTabOrchestrator
    pour une gestion centralisée et modulaire des onglets de résultats.

    Migration ST-2.2 :
    - Ancien : Délégation directe vers ui_kpis.display_valuation_details()
    - Nouveau : Orchestration centralisée avec ResultTabOrchestrator

    Notes
    -----
    L'orchestrateur gère automatiquement :
    - Filtrage des onglets visibles selon les données
    - Tri par ordre de priorité
    - Gestion d'erreurs par onglet
    - Layout avec st.tabs()
    """
    
    def render_executive_summary(self, result: Any) -> None:
        """Utilise la nouvelle architecture ResultTabOrchestrator (Sprint 2 Phase 2)."""
        from app.ui.results.orchestrator import ResultTabOrchestrator
        orchestrator = ResultTabOrchestrator()
        orchestrator.render(result)

    def display_valuation_details(self, result: Any, provider: Any) -> None:
        """Alias pour maintenir la compatibilité - utilise maintenant render_executive_summary."""
        self.render_executive_summary(result)
    
    def display_error(self, message: str, details: Optional[str] = None) -> None:
        st.error(message)
        if details:
            with st.expander("Détails techniques"):
                st.code(details, language="text")
