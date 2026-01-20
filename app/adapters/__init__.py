"""
app/adapters/
Adaptateurs UI — Implémentations Streamlit des interfaces core.

Résolution DT-017
Pattern : Adapter (GoF)

Objectif :
- Fournir les implémentations concrètes des interfaces core/interfaces
- Isoler toutes les dépendances Streamlit dans app/

Usage :
    from app.adapters import StreamlitProgressHandler, StreamlitResultRenderer
"""

from app.adapters.streamlit_adapters import (
    StreamlitProgressHandler,
    StreamlitResultRenderer,
)

__all__ = [
    "StreamlitProgressHandler",
    "StreamlitResultRenderer",
]
