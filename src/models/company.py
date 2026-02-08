"""
src/models/company.py

COMPANY MODELS — Identity and Data Transport (DTO)
==================================================
Role: Defines the persistent identity (Company) and the ephemeral
      transport container (CompanySnapshot) for the resolution workflow.

Architecture: Pydantic V2.
- Company: Stays in Parameters.structure (Identity only).
- CompanySnapshot: Rich DTO used by Providers and the Resolver (Not stored).

Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from src.models.enums import CompanySector

class Company(BaseModel):
    """
    Represents the persistent identity of a company.

    This class is stored in Parameters.structure. It contains only
    descriptive metadata used for UI display and audit reports,
    ensuring no calculation data is duplicated.

    Attributes
    ----------
    ticker : str
        Stock symbol (e.g., "AAPL").
    name : str
        Legal entity name.
    sector : CompanySector
        GICS sector classification used for industry multiples fallback.
    current_price : float
        Current share price (Reference Witness).
    """
    model_config = ConfigDict(frozen=True)

    ticker: str
    name: str = "Unknown Entity"
    sector: CompanySector = Field(default=CompanySector.UNKNOWN)
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: str = "USD"
    current_price: float = Field(default=0.0, ge=0)
    last_update: datetime = Field(default_factory=datetime.now)

    @property
    def display_name(self) -> str:
        """Returns a formatted label 'Ticker - Name'."""
        return f"{self.ticker} - {self.name}"


class CompanySnapshot(BaseModel):
    """
    Ephemeral Financial Snapshot (Rich DTO).

    This object acts as a 'Data Bag' that aggregates raw Micro (Accounting)
    and Macro (Market) data. It is used exclusively as a bridge between
    Data Providers and the Resolver.
    """

    model_config = ConfigDict(extra='ignore', arbitrary_types_allowed=True)

    # --- 1. Identity Trace ---
    ticker: str
    name: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: Optional[str] = None
    current_price: Optional[float] = None

    # --- 2. Raw Micro Financials (Micro) ---
    # Used to hydrate Parameters.common.capital
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    minority_interests: Optional[float] = None
    pension_provisions: Optional[float] = None
    shares_outstanding: Optional[float] = None
    interest_expense: Optional[float] = None
    net_borrowing_ttm: Optional[float] = None

    # Used to hydrate Parameters.strategy anchors
    revenue_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    fcf_ttm: Optional[float] = None
    eps_ttm: Optional[float] = None
    dividend_share: Optional[float] = None
    book_value_ps: Optional[float] = None
    beta: Optional[float] = None
    capex_ttm: Optional[float] = None

    # --- 3. Knowledge Base Fallbacks ---
    sector_pe_fallback: Optional[float] = None
    sector_ev_ebitda_fallback: Optional[float] = None
    sector_ev_rev_fallback: Optional[float] = None

    # --- 4. Raw Macro Context (Macro) ---
    risk_free_rate: Optional[float] = None
    market_risk_premium: Optional[float] = None
    tax_rate: Optional[float] = None
    perpetual_growth_rate: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None