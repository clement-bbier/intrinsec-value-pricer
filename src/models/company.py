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
from pydantic import BaseModel, ConfigDict


class Company(BaseModel):
    """
    Represents the persistent identity of a company.

    This class is stored in Parameters.structure. It contains only
    descriptive metadata used for UI display and audit reports,
    ensuring no calculation data is duplicated.
    """
    model_config = ConfigDict(frozen=True)

    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    current_price: Optional[float] = None


class CompanySnapshot(BaseModel):
    """
    Ephemeral Financial Snapshot (Rich DTO).

    This object acts as a 'Data Bag' that aggregates raw Micro (Accounting)
    and Macro (Market) data. It is used exclusively as a bridge between
    Data Providers and the Resolver.
    """
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

    # --- 3. Knowledge Base Fallbacks ---
    sector_pe_fallback: Optional[float] = None
    sector_ev_ebitda_fallback: Optional[float] = None
    sector_ev_rev_fallback: Optional[float] = None

    # --- 3. Raw Macro Context (Macro) ---
    # Aggregated from MacroProvider to provide a single source for the Resolver
    risk_free_rate: Optional[float] = None
    market_risk_premium: Optional[float] = None
    tax_rate: Optional[float] = None
    perpetual_growth_rate: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None