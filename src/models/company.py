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

from typing import Optional

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
    name: Optional[str] = None
    currency: Optional[str] = None

    # --- Sectoral Classification ---
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    headquarters: Optional[str] = None

    # --- Market Witness (Sacred) ---
    current_price: Optional[float] = None