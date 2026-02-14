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

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

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
    industry: str | None = None
    country: str | None = None
    currency: str = "USD"
    current_price: float = Field(default=0.0, ge=0)
    last_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    # --- 1. Identity Trace ---
    ticker: str
    name: str | None = None
    country: str | None = None
    sector: str | None = None
    industry: str | None = None
    currency: str | None = None
    current_price: float | None = None

    # --- 2. Raw Micro Financials (Micro) ---
    # Used to hydrate Parameters.common.capital
    total_debt: float | None = None
    cash_and_equivalents: float | None = None
    minority_interests: float | None = None
    pension_provisions: float | None = None
    shares_outstanding: float | None = None
    interest_expense: float | None = None
    net_borrowing_ttm: float | None = None

    # Used to hydrate Parameters.strategy anchors
    revenue_ttm: float | None = None
    ebit_ttm: float | None = None
    net_income_ttm: float | None = None
    fcf_ttm: float | None = None
    eps_ttm: float | None = None
    dividend_share: float | None = None
    book_value_ps: float | None = None
    beta: float | None = None
    capex_ttm: float | None = None

    # Additional TTM metrics for Piotroski calculation
    total_assets_ttm: float | None = None
    current_assets_ttm: float | None = None
    current_liabilities_ttm: float | None = None
    gross_profit_ttm: float | None = None

    # --- Previous Year Data (N-1) for Historical Comparisons ---
    # Used for Piotroski F-Score and other year-over-year metrics
    net_income_prev: float | None = None
    total_assets_prev: float | None = None
    long_term_debt_prev: float | None = None
    current_assets_prev: float | None = None
    current_liabilities_prev: float | None = None
    gross_profit_prev: float | None = None
    revenue_prev: float | None = None
    shares_outstanding_prev: float | None = None

    # --- 3. Knowledge Base Fallbacks ---
    sector_pe_fallback: float | None = None
    sector_ev_ebitda_fallback: float | None = None
    sector_ev_rev_fallback: float | None = None

    # --- 4. Raw Macro Context (Macro) ---
    risk_free_rate: float | None = None
    market_risk_premium: float | None = None
    tax_rate: float | None = None
    perpetual_growth_rate: float | None = None
    corporate_aaa_yield: float | None = None
