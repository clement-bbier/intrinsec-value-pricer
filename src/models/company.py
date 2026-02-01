"""
src/models/company.py

COMPANY IDENTITY & CLASSIFICATION
=================================
Role: Descriptive and immutable data container.
Scope: Identity, sector, industry, and current market price (as a witness).
Architecture: Pydantic V2. Contains no overrideable calculation data.

Style: Numpy docstrings.
"""

from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class Company(BaseModel):
    """
    Represents the fixed identity of a company.

    This class serves as a reference for display and audit (Pillar 1).
    It contains only descriptive data that is not intended to be
    modified for the financial calculation itself.
    """
    # Immutable to ensure integrity throughout the workflow
    model_config = ConfigDict(frozen=True)

    # --- Identification ---
    ticker: str
    name: str = "Unknown"
    currency: str

    # --- Sectoral Classification ---
    sector: str = "Unknown"
    industry: str = "Unknown"
    country: str = "Unknown"
    headquarters: str = "Unknown"

    # --- Market Witness (Sacred) ---
    current_price: float