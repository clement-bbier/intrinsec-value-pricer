"""
src/models/parameters/input_metadata.py

UI BINDING METADATA
===================
Role: Defines the annotations used to link Pydantic fields to Streamlit keys.
Scope: Domain Layer (No UI dependencies).
Style: Numpy docstrings.
"""

from dataclasses import dataclass
from typing import Literal

# Scaling types supported by the architecture
UIScale = Literal["pct", "million", "raw"]


@dataclass(frozen=True)
class UIKey:
    """
    Metadata container for UI field mapping.

    Acts as a bridge between the rigorous Pydantic domain models and the
    stateful, flat structure of the Streamlit interface.

    Attributes
    ----------
    suffix : str
        The unique identifier suffix used in the Streamlit session_state key.
    scale : UIScale, optional
        The mathematical transformation to apply to the input.
        - "Pct": Converts human-readable percentages (e.g., 5.0) to decimal (0.05).
        - "million": Scales input from millions (e.g., 100) to absolute units (100,000,000).
        - "raw": No transformation applied.
        The default is "raw".
    """

    suffix: str
    scale: UIScale = "raw"
