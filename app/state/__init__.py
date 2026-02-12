"""
app/state

State management module for the application.
Provides centralized session state management with atomic operations.
"""

from app.state.session_manager import SessionManager

__all__ = ["SessionManager"]
