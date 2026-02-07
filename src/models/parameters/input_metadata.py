"""
src/models/parameters/ui_bridge.py

UI BINDING BRIDGE — Metadata for Model-UI synchronization.
==========================================================
Role: Defines the annotations used to link Pydantic fields to Streamlit keys.
Scope: Domain Layer (No UI dependencies).
"""

from dataclasses import dataclass
from typing import Literal

# Scaling types supported by the architecture
UIScale = Literal["pct", "million", "raw"]

@dataclass(frozen=True)
class UIKey:
    """
    Metadata container for UI field mapping.

    Attributes
    ----------
    suffix : str
        The unique part of the Streamlit session_state key.
    scale : UIScale, optional
        The mathematical scale of the input.
        - "pct": Human percentage (5.0) to be normalized (0.05).
        - "million": Scaled from millions to absolute units.
        - "raw": No transformation applied.
        Default is "raw".
    """
    suffix: str
    scale: UIScale = "raw"