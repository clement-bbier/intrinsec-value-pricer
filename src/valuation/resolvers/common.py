from __future__ import annotations
from pydantic import BaseModel, Field

class FinancialRatesResolvers(BaseModel):
    test: None

class CapitalStructureResolvers(BaseModel):
    test: None

class CommonResolvers(BaseModel):
    """Main container for shared valuation inputs."""
    rates: FinancialRatesResolvers = Field(default_factory=FinancialRatesResolvers)
    capital: CapitalStructureResolvers = Field(default_factory=CapitalStructureResolvers)