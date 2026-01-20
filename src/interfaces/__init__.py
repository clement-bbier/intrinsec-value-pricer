"""
core/interfaces/
Interfaces et Abstractions pour l'Inversion de Dépendances.

Résolution DT-017
Pattern : Dependency Inversion Principle (SOLID)

Objectif :
- Découpler core/infra de la couche UI (Streamlit)
- Permettre les tests en isolation
- Faciliter la substitution de frameworks UI

Usage :
    from src.interfaces import IUIProgressHandler, NullProgressHandler
"""

from src.interfaces.ui_handlers import (
    IUIProgressHandler,
    NullProgressHandler,
    IResultRenderer,
    NullResultRenderer,
)

__all__ = [
    "IUIProgressHandler",
    "NullProgressHandler",
    "IResultRenderer",
    "NullResultRenderer",
]
