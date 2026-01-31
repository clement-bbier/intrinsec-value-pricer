"""
src/models/results/common.py

UNIVERSAL VALUATION OUTPUTS (PURE CALCULATION)
==============================================
Role: Stores ONLY the generated values from the resolution engines.
Scope: Calculated WACC, Bridge Totals, and Final Synthesis.
Architecture: Pydantic V2. Zero redundancy with Parameters or Company.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.glass_box import CalculationStep

class ResolvedRates(BaseModel):
    """Calculated financial outcomes for the discounting environment."""
    # Ces valeurs sont des RÉSULTATS car elles sont issues de la "danse" (WACC/Ke)
    cost_of_equity: float = Field(..., description="Calculated Ke (CAPM result).")
    cost_of_debt_after_tax: float = Field(..., description="Resolved Kd after tax shield.")
    wacc: float = Field(..., description="Final WACC result.")

    # Graham specific yield (if resolved from market)
    corporate_aaa_yield: Optional[float] = None

class ResolvedCapital(BaseModel):
    """The numeric outcomes of the Equity Bridge calculation."""
    # On ne stocke que les TOTAUX calculés.
    # Les briques (dette, cash) sont dans Company/Parameters.
    market_cap: float = Field(..., description="Price x Shares (Market Witness).")
    enterprise_value: float = Field(..., description="Operating value result from the engine.")
    net_debt_resolved: float = Field(..., description="Calculated Net Debt (Total Debt - Cash).")
    equity_value_total: float = Field(..., description="Final Intrinsic Equity Value.")

class CommonResults(BaseModel):
    """
    Main container for shared valuation outputs.

    To display the bridge details (Minorities, etc.), the UI uses:
    1. bridge_trace (for values used)
    2. result.params (for inputs/overrides)
    """
    rates: ResolvedRates
    capital: ResolvedCapital

    # --- Final Synthesis ---
    intrinsic_value_per_share: float
    upside_pct: float

    # --- Pillar 2: The Audit Trail ---
    bridge_trace: List[CalculationStep] = Field(default_factory=list)