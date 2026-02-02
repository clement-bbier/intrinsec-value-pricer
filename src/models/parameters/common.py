"""
src/models/params/common.py

UNIVERSAL VALUATION LEVERS
==========================
Role: Shared input parameters for financial rates and capital structure.
Scope: Risk-free rates, beta, market premiums, and balance sheet overrides.
Architecture: Pydantic V2. All fields are optional to allow for provider fallbacks.

Style: Numpy docstrings.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class FinancialRatesParameters(BaseModel):
    """Universal financial discounting and risk parameters."""
    risk_free_rate: Optional[float] = None
    market_risk_premium: Optional[float] = None
    beta: Optional[float] = None
    cost_of_debt: Optional[float] = None
    tax_rate: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None     # Graham specific but kept in common for market context


class CapitalStructureParameters(BaseModel):
    """Universal balance sheet and equity bridge components."""
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    minority_interests: Optional[float] = None
    pension_provisions: Optional[float] = None
    shares_outstanding: Optional[float] = None
    annual_dilution_rate: Optional[float] = None

class CommonParameters(BaseModel):
    """Main container for shared valuation inputs."""
    rates: FinancialRatesParameters = Field(default_factory=FinancialRatesParameters)
    capital: CapitalStructureParameters = Field(default_factory=CapitalStructureParameters)