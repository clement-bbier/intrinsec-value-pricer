"""
core/interfaces/ui_handlers.py
INTERFACES UI — DT-016/017 Resolution

Version : V1.0
Pattern : Strategy + Null Object (GoF)

AVANT (Couplage direct) :
- workflow.py importe ui_kpis.render_executive_summary()
- yahoo_provider.py utilise st.status() directement

APRÈS (Inversion de dépendances) :
- Interfaces abstraites dans core/interfaces
- Implémentations concrètes dans app/
- Injection optionnelle avec fallback vers NullObject

Usage (Production) :
    from app.adapters import StreamlitProgressHandler
    handler = StreamlitProgressHandler()
    
Usage (Tests) :
    from src.interfaces import NullProgressHandler
    handler = NullProgressHandler()  # Ne fait rien
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


# ==============================================================================
# 1. INTERFACE PROGRESS HANDLER (DT-017)
# ==============================================================================

class IUIProgressHandler(ABC):
    """
    Interface pour la gestion de la progression UI.
    Permet de découpler infra/ de Streamlit.
    """
    
    @abstractmethod
    def start_status(self, label: str) -> "IUIProgressHandler":
        """Démarre un indicateur de statut."""
        pass
    
    @abstractmethod
    def update_status(self, message: str) -> None:
        """Met à jour le message de progression."""
        pass
    
    @abstractmethod
    def complete_status(self, label: str, state: str = "complete") -> None:
        """Finalise l'indicateur de statut."""
        pass
    
    @abstractmethod
    def error_status(self, label: str) -> None:
        """Indique une erreur."""
        pass
    
    def __enter__(self) -> "IUIProgressHandler":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class NullProgressHandler(IUIProgressHandler):
    """
    Implémentation Null Object pour les tests et modes headless.
    Ne fait rien mais respecte l'interface.
    """
    
    def start_status(self, label: str) -> "NullProgressHandler":
        return self
    
    def update_status(self, message: str) -> None:
        pass
    
    def complete_status(self, label: str, state: str = "complete") -> None:
        pass
    
    def error_status(self, label: str) -> None:
        pass


# ==============================================================================
# 2. INTERFACE RESULT RENDERER (DT-016)
# ==============================================================================

class IResultRenderer(ABC):
    """
    Interface pour le rendu des résultats.
    Permet de découpler workflow.py de ui_kpis.
    """
    
    @abstractmethod
    def render_executive_summary(self, result: Any) -> None:
        """Affiche le résumé exécutif."""
        pass
    
    @abstractmethod
    def display_valuation_details(self, result: Any, provider: Any) -> None:
        """Affiche les détails de valorisation."""
        pass
    
    @abstractmethod
    def display_error(self, message: str, details: Optional[str] = None) -> None:
        """Affiche une erreur."""
        pass


class NullResultRenderer(IResultRenderer):
    """
    Implémentation Null Object pour les tests.
    Stocke les résultats pour vérification sans affichage.
    """
    
    def __init__(self):
        self.last_result: Any = None
        self.last_error: Optional[str] = None
    
    def render_executive_summary(self, result: Any) -> None:
        self.last_result = result
    
    def display_valuation_details(self, result: Any, provider: Any) -> None:
        pass
    
    def display_error(self, message: str, details: Optional[str] = None) -> None:
        self.last_error = message
