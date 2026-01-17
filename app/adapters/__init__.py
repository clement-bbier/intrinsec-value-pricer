"""
app/adapters/
Adaptateurs UI — Implémentations Streamlit des interfaces core.

Version : V1.0 — DT-016/017 Resolution
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
