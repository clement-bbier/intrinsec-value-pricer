"""
app/adapters/ui_binder.py

UI BINDER — Automated SessionState to Pydantic extraction.
==========================================================
Role: Introspects models to pull data from Streamlit without manual mapping.
Pattern: Strategy / Adapter.
"""

import logging
from typing import Any, Dict, Type, Optional

import streamlit as st
from pydantic import BaseModel

from src.models.parameters.ui_bridge import UIKey

logger = logging.getLogger(__name__)


class UIBinder:
    """
    Generic binder to hydrate Pydantic models from Streamlit session state.

    This class implements a 'pull' mechanism: it looks at what the model
    requires and searches for the corresponding keys in the UI.
    """

    @staticmethod
    def pull(model_cls: Type[BaseModel], prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Introspects a Pydantic model to extract values from st.session_state.

        Parameters
        ----------
        model_cls : Type[BaseModel]
            The Pydantic class to inspect.
        prefix : str, optional
            A prefix to prepend to the UIKey suffix (e.g., "DDM" -> "DDM_rf").

        Returns
        -------
        Dict[str, Any]
            A dictionary of extracted and pre-scaled values ready for instantiation.
        """
        extracted_payload = {}

        # O(N) complexity over the number of fields in the targeted model
        for field_name, field_info in model_cls.model_fields.items():
            # 1. Look for UIKey in Annotated metadata
            # Annotated stores metadata in the 'metadata' attribute of field_info
            ui_meta = next((m for m in field_info.metadata if isinstance(m, UIKey)), None)

            if not ui_meta:
                continue

            # 2. Reconstruct the full Streamlit key
            full_key = f"{prefix}_{ui_meta.suffix}" if prefix else ui_meta.suffix

            # 3. Safe extraction (O(1) dictionary lookup)
            raw_value = st.session_state.get(full_key)

            if raw_value is not None:
                extracted_payload[field_name] = raw_value

        return extracted_payload