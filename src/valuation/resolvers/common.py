"""
src/models/parameters/common.py

COMMON FINANCIAL PARAMETERS
===========================
Role: Data container for universal valuation inputs (Rates & Capital).
Responsibility: strict data definition (Pydantic). No logic here.
Architecture: Pillar 2 Definition.
Style: Numpy docstrings.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class FinancialRatesParameters(BaseModel):
    """
    Container for market rates, risk metrics, and tax assumptions.

    Attributes
    ----------
    risk_free_rate : float, optional
        The theoretical return of an investment with zero risk.
    market_risk_premium : float, optional
        Excess return expected from the market over the risk-free rate.
    beta : float, optional
        Measure of the stock's volatility in relation to the market.
    cost_of_debt : float, optional
        The effective rate that a company pays on its debt.
    tax_rate : float, optional
        Effective corporate tax rate.
    corporate_aaa_yield : float, optional
        Yield on AAA-rated corporate bonds (Specific to Graham strategy).
    """
    risk_free_rate: Optional[float] = None
    market_risk_premium: Optional[float] = None
    beta: Optional[float] = None
    cost_of_debt: Optional[float] = None
    tax_rate: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None


class CapitalStructureParameters(BaseModel):
    """
    Container for balance sheet items and share count configurations.

    Attributes
    ----------
    total_debt : float, optional
        Sum of short-term and long-term debt.
    cash_and_equivalents : float, optional
        Liquid assets available on the balance sheet.
    shares_outstanding : float, optional
        Total number of shares held by shareholders.
    minority_interests : float, optional
        Value of subsidiary interests not owned by the parent company.
    pension_provisions : float, optional
        Liabilities related to employee pension schemes.
    annual_dilution_rate : float, optional
        Expected annual increase in share count (e.g., Stock Based Comp).
    """
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    shares_outstanding: Optional[float] = None
    minority_interests: Optional[float] = None
    pension_provisions: Optional[float] = None
    annual_dilution_rate: Optional[float] = None


class CommonParameters(BaseModel):
    """
    Main container for shared valuation inputs (Pillar 2).

    Acts as the bridge for universal levers used across all valuation strategies.

    Attributes
    ----------
    rates : FinancialRatesParameters
        Market rates and risk configuration.
    capital : CapitalStructureParameters
        Capital structure and balance sheet configuration.
    """
    rates: FinancialRatesParameters = Field(default_factory=FinancialRatesParameters)
    capital: CapitalStructureParameters = Field(default_factory=CapitalStructureParameters)