"""
app/state/session_manager.py

SESSION MANAGER — Centralized State Management (Singleton Pattern)

Version : V1.0 — Phase 1 UX Foundation
Role : Atomic state management for the application lifecycle.
Pattern : Singleton via Streamlit session_state

Principles:
- Single Source of Truth for application state
- Atomic clear_results() to purge stale data on config change
- Type-safe state access via properties
- No direct session_state manipulation outside this module

Dependencies:
- streamlit >= 1.28.0
"""

from __future__ import annotations

import logging
from typing import Optional

import streamlit as st

from src.domain.models import ValuationRequest

logger = logging.getLogger(__name__)


# Session state keys (centralized to avoid magic strings)
_KEY_ACTIVE_REQUEST = "active_request"
_KEY_LAST_CONFIG = "last_config"
_KEY_RESULT_CACHE_HASH = "result_cache_hash"
_KEY_CACHED_MC_DATA = "cached_monte_carlo_data"
_KEY_ACTIVE_TAB = "active_result_tab"
_KEY_RENDER_CONTEXT = "render_context_cache"


class SessionManager:
    """
    Centralized session state manager for the application.

    Manages the lifecycle of the active valuation request and
    associated result caches. Ensures atomic state transitions
    when configuration changes.

    Attributes
    ----------
    SESSION_DEFAULTS : dict
        Default values for all managed session state keys.

    Notes
    -----
    All state access goes through this class to prevent
    scattered session_state manipulation across the codebase.
    """

    SESSION_DEFAULTS = {
        _KEY_ACTIVE_REQUEST: None,
        _KEY_LAST_CONFIG: "",
        _KEY_RESULT_CACHE_HASH: None,
        _KEY_CACHED_MC_DATA: None,
        _KEY_ACTIVE_TAB: 0,
        _KEY_RENDER_CONTEXT: {},
    }

    @staticmethod
    def init() -> None:
        """
        Initialize session state with defaults if not already set.

        Should be called once at application startup (main.py).
        Idempotent — safe to call multiple times.
        """
        for key, default in SessionManager.SESSION_DEFAULTS.items():
            if key not in st.session_state:
                if isinstance(default, dict):
                    st.session_state[key] = default.copy()
                else:
                    st.session_state[key] = default

    @staticmethod
    def clear_results() -> None:
        """
        Purge all result-related state.

        Called when user changes ticker, mode, or source to ensure
        no stale results persist in the UI. This is the atomic
        reset operation that prevents "ghost results".

        Clears:
        - active_request (the pending/completed request)
        - result_cache_hash (forces re-render)
        - cached_monte_carlo_data (stale MC stats)
        - render_context_cache (stale tab context)
        """
        logger.debug("Clearing all result state (config change detected)")
        st.session_state[_KEY_ACTIVE_REQUEST] = None
        st.session_state[_KEY_RESULT_CACHE_HASH] = None
        st.session_state[_KEY_CACHED_MC_DATA] = None
        st.session_state[_KEY_RENDER_CONTEXT] = {}

    @staticmethod
    def get_active_request() -> Optional[ValuationRequest]:
        """
        Get the current active valuation request.

        Returns
        -------
        Optional[ValuationRequest]
            The active request, or None if no analysis is pending.
        """
        return st.session_state.get(_KEY_ACTIVE_REQUEST)

    @staticmethod
    def set_active_request(request: ValuationRequest) -> None:
        """
        Set the active valuation request and trigger a rerun.

        Parameters
        ----------
        request : ValuationRequest
            The valuation request to activate.
        """
        logger.info(
            "Setting active request: ticker=%s, mode=%s",
            request.ticker,
            request.mode.value,
        )
        st.session_state[_KEY_ACTIVE_REQUEST] = request
        st.rerun()

    @staticmethod
    def on_config_change(current_config: str) -> bool:
        """
        Check if configuration changed and clear results if so.

        Parameters
        ----------
        current_config : str
            A fingerprint string representing the current UI configuration
            (e.g., "{ticker}_{is_expert}_{mode}").

        Returns
        -------
        bool
            True if configuration changed (results were cleared).
        """
        last_config = st.session_state.get(_KEY_LAST_CONFIG, "")
        if last_config != current_config:
            SessionManager.clear_results()
            st.session_state[_KEY_LAST_CONFIG] = current_config
            logger.debug(
                "Config changed: '%s' -> '%s', results cleared",
                last_config,
                current_config,
            )
            return True
        return False
