"""
src/interfaces/ui_handlers.py

INTERFACES UI ABSTRAITES — DT-016/017 Resolution

Version : V1.1
Pattern : Strategy + Null Object (GoF)
Style : Numpy Style docstrings

Responsabilité:
    Définit les interfaces abstraites pour la communication UI.
    Ces interfaces permettent de découpler src/ (core financier) de app/ (UI Streamlit).

Architecture (Inversion de Dépendances):
    - Interfaces abstraites définies ICI dans src/interfaces/
    - Implémentations concrètes dans app/adapters/
    - Injection optionnelle avec fallback vers NullObject

Usage dans app/ (Production):
    >>> from app.adapters import StreamlitProgressHandler
    >>> handler = StreamlitProgressHandler()
    
Usage dans tests/ (Headless):
    >>> from src.interfaces import NullProgressHandler
    >>> handler = NullProgressHandler()  # Ne fait rien

RISQUES FINANCIERS:
    - Aucun impact direct sur les calculs de valorisation
    - Interface de présentation uniquement

Note Étanchéité:
    Ce fichier fait partie de src/ et ne doit JAMAIS importer de app/ ou streamlit.
    Les exemples ci-dessus montrent l'usage DEPUIS app/, pas DANS ce fichier.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models import ValuationResult
    from types import TracebackType


# ==============================================================================
# 1. PROTOCOLS POUR TYPAGE STRUCTUREL (Évite les dépendances circulaires)
# ==============================================================================

class DataProviderProtocol(Protocol):
    """Protocol définissant l'interface minimale d'un fournisseur de données."""
    
    def get_company_name(self, ticker: str) -> str:
        """Retourne le nom de l'entreprise."""
        ...


# ==============================================================================
# 2. INTERFACE PROGRESS HANDLER (DT-017)
# ==============================================================================

class IUIProgressHandler(ABC):
    """
    Interface pour la gestion de la progression UI.
    
    Permet de découpler infra/ de Streamlit en définissant un contrat
    abstrait que les implémentations concrètes (Streamlit, CLI, tests) 
    doivent respecter.

    Financial Impact
    ----------------
    Aucun impact direct sur les calculs de valorisation.
    Interface de présentation uniquement.
    """
    
    @abstractmethod
    def start_status(self, label: str) -> IUIProgressHandler:
        """Démarre un indicateur de statut."""
        ...
    
    @abstractmethod
    def update_status(self, message: str) -> None:
        """Met à jour le message de progression."""
        ...
    
    @abstractmethod
    def complete_status(self, label: str, state: str = "complete") -> None:
        """Finalise l'indicateur de statut."""
        ...
    
    @abstractmethod
    def error_status(self, label: str) -> None:
        """Indique une erreur."""
        ...
    
    def __enter__(self) -> IUIProgressHandler:
        return self
    
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
        pass


class NullProgressHandler(IUIProgressHandler):
    """
    Implémentation Null Object pour les tests et modes headless.
    
    Ne fait rien mais respecte l'interface.
    Utilisé pour les tests unitaires et les exécutions sans UI.
    """
    
    def start_status(self, label: str) -> NullProgressHandler:
        return self
    
    def update_status(self, message: str) -> None:
        pass
    
    def complete_status(self, label: str, state: str = "complete") -> None:
        pass
    
    def error_status(self, label: str) -> None:
        pass


# ==============================================================================
# 3. INTERFACE RESULT RENDERER (DT-016)
# ==============================================================================

class IResultRenderer(ABC):
    """
    Interface pour le rendu des résultats de valorisation.
    
    Permet de découpler workflow.py de ui_kpis en définissant un contrat
    abstrait pour l'affichage des résultats.

    Financial Impact
    ----------------
    Aucun impact direct sur les calculs de valorisation.
    Interface de présentation uniquement.

    Notes
    -----
    ST 1.2 Naming Blueprint: La méthode principale est désormais `render_results`.
    `display_valuation_details` est conservée pour rétrocompatibilité.
    """
    
    @abstractmethod
    def render_executive_summary(self, result: ValuationResult) -> None:
        """
        Affiche le résumé exécutif de la valorisation.
        
        Args
        ----
        result : ValuationResult
            Résultat complet de la valorisation à afficher.
        """
        ...

    @abstractmethod
    def render_results(
        self,
        result: ValuationResult,
        provider: DataProviderProtocol | None = None
    ) -> None:
        """
        Affiche les résultats de valorisation complets.
        
        Méthode principale de rendu (ST 1.2 Naming Blueprint).
        
        Args
        ----
        result : ValuationResult
            Résultat complet de la valorisation à afficher.
        provider : DataProviderProtocol | None
            Fournisseur de données optionnel pour les informations complémentaires.
        """
        ...
    
    @abstractmethod
    def display_valuation_details(
        self, 
        result: ValuationResult, 
        provider: DataProviderProtocol
    ) -> None:
        """
        Affiche les détails de valorisation.
        
        .. deprecated::
            Utilisez :meth:`render_results` à la place.
        
        Args
        ----
        result : ValuationResult
            Résultat complet de la valorisation.
        provider : DataProviderProtocol
            Fournisseur de données pour les informations complémentaires.
        """
        ...
    
    @abstractmethod
    def display_error(self, message: str, details: Optional[str] = None) -> None:
        """
        Affiche une erreur à l'utilisateur.
        
        Args
        ----
        message : str
            Message d'erreur principal.
        details : Optional[str]
            Détails techniques optionnels.
        """
        ...


class NullResultRenderer(IResultRenderer):
    """
    Implémentation Null Object pour les tests.
    
    Stocke les résultats pour vérification sans affichage.
    Utile pour les tests unitaires où on veut vérifier ce qui aurait été affiché.
    """
    
    def __init__(self) -> None:
        self.last_result: ValuationResult | None = None
        self.last_error: str | None = None
    
    def render_executive_summary(self, result: ValuationResult) -> None:
        self.last_result = result

    def render_results(
        self,
        result: ValuationResult,
        provider: DataProviderProtocol | None = None
    ) -> None:
        self.last_result = result
    
    def display_valuation_details(
        self, 
        result: ValuationResult, 
        provider: DataProviderProtocol
    ) -> None:
        self.render_results(result, provider)
    
    def display_error(self, message: str, details: Optional[str] = None) -> None:
        self.last_error = message
