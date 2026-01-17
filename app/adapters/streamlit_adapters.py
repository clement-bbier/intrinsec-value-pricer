"""
app/adapters/streamlit_adapters.py
ADAPTATEURS STREAMLIT — DT-016/017 Resolution

Version : V1.0
Pattern : Adapter (GoF)

Ces classes implémentent les interfaces définies dans core/interfaces
en utilisant Streamlit comme framework UI.
"""

from typing import Any, Optional

import streamlit as st

from core.interfaces import IUIProgressHandler, IResultRenderer
import app.ui_components.ui_kpis as ui_kpis


class StreamlitProgressHandler(IUIProgressHandler):
    """
    Adaptateur Streamlit pour la gestion de progression.
    Encapsule st.status pour respecter l'interface IUIProgressHandler.
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
    Adaptateur Streamlit pour le rendu des résultats.
    Délègue vers ui_kpis pour l'affichage réel.
    """
    
    def render_executive_summary(self, result: Any) -> None:
        ui_kpis.render_executive_summary(result)
    
    def display_valuation_details(self, result: Any, provider: Any) -> None:
        ui_kpis.display_valuation_details(result, provider)
    
    def display_error(self, message: str, details: Optional[str] = None) -> None:
        st.error(message)
        if details:
            with st.expander("Détails techniques"):
                st.code(details, language="text")
