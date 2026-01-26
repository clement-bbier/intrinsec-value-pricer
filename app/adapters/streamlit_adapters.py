"""
app/adapters/streamlit_adapters.py

ADAPTATEURS STREAMLIT — COUCHE D'ADAPTATION UI
==============================================
Rôle : Implémentation des interfaces core (IResultRenderer, IUIProgressHandler)
Pattern : Adapter (GoF)
Migration : DT-016 (Séparation Calcul / Rendu)
"""

from __future__ import annotations
from typing import Any, Optional

import streamlit as st

from src.interfaces import IUIProgressHandler, IResultRenderer
from src.i18n import UIMessages, WorkflowTexts
from src.models import ValuationResult

# On évite l'import global de l'orchestrateur pour prévenir les imports circulaires
# car l'orchestrateur charge tout l'arbre de l'UI.

class StreamlitProgressHandler(IUIProgressHandler):
    """
    Adaptateur pour la gestion de progression via st.status.

    Encapsule les composants de feedback visuel de Streamlit pour
    isoler la logique métier des APIs de l'interface.
    """

    def __init__(self):
        self._status_container: Optional[Any] = None

    def start_status(self, label: str) -> StreamlitProgressHandler:
        """Initialise le composant de statut Streamlit."""
        self._status_container = st.status(label, expanded=True)
        return self

    def update_status(self, message: str) -> None:
        """Ajoute une ligne d'information dans le statut en cours."""
        if self._status_container:
            self._status_container.write(message)

    def complete_status(self, label: str, state: str = "complete") -> None:
        """Finalise le composant de statut (fermeture automatique)."""
        if self._status_container:
            self._status_container.update(label=label, state=state, expanded=False)

    def error_status(self, label: str) -> None:
        """Bascule le composant de statut en mode erreur."""
        if self._status_container:
            self._status_container.update(label=label, state="error", expanded=True)

    def __enter__(self) -> StreamlitProgressHandler:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Gestion automatique de la fermeture du statut en cas d'exception."""
        if exc_type and self._status_container:
            self.error_status(WorkflowTexts.STATUS_INTERRUPTED)


class StreamlitResultRenderer(IResultRenderer):
    """
    Adaptateur pour le rendu des résultats de valorisation.

    Délègue la complexité de l'affichage à l'Orchestrateur d'onglets.
    Respecte l'interface IResultRenderer (DT-016).
    """

    def render_results(self, result: ValuationResult, provider: Any = None) -> None:
        """
        Point d'entrée principal du rendu (Standard ST-2.2).

        Parameters
        ----------
        result : ValuationResult
            L'objet de résultat riche issu du moteur.
        provider : Any, optional
            Le fournisseur de données utilisé (pour métadonnées additionnelles).
        """
        # Import tardif (Lazy Loading) pour casser les dépendances circulaires
        from app.ui.results.orchestrator import ResultTabOrchestrator

        orchestrator = ResultTabOrchestrator()
        orchestrator.render(result)

    def display_error(self, message: str, details: Optional[str] = None) -> None:
        """Affiche une notification d'erreur formatée avec i18n."""
        st.error(message)
        if details:
            with st.expander(UIMessages.TECHNICAL_DETAILS):
                st.code(details, language="text")

    # --- MÉTHODES DE COMPATIBILITÉ (DEPRECATED) ---

    def render_executive_summary(self, result: Any) -> None:
        """Alias pour render_results (Phase 2 compliance)."""
        self.render_results(result)

    def display_valuation_details(self, result: Any, provider: Any) -> None:
        """Ancien nom de méthode ST-1.2, maintenu pour compatibilité tests."""
        self.render_results(result, provider)