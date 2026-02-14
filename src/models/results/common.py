"""
src/models/results/common.py

UNIVERSAL VALUATION OUTPUTS (PURE CALCULATION)
==============================================
Role: Stores ONLY the generated values from the resolution engines.
Scope: Calculated WACC, Bridge Totals, and Final Synthesis.
Architecture: Pydantic V2. Zero redundancy with Parameters or Company.
Style: Numpy docstrings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.models.glass_box import CalculationStep


class ResolvedRates(BaseModel):
    """
    Calculated financial outcomes for the discounting environment.

    Attributes
    ----------
    cost_of_equity : float
        Calculated Cost of Equity (Ke) via CAPM or Build-Up.
    cost_of_debt_after_tax : float
        Effective Cost of Debt (Kd) after applying the tax shield.
    wacc : float
        Weighted Average Cost of Capital used for discounting FCFF.
    corporate_aaa_yield : float | None
        The benchmark yield used for Graham valuation (if applicable).
    """

    cost_of_equity: float = Field(..., description="Calculated Ke (CAPM result).")
    cost_of_debt_after_tax: float = Field(..., description="Resolved Kd after tax shield.")
    wacc: float = Field(..., description="Final WACC result.")
    corporate_aaa_yield: float | None = None


class ResolvedCapital(BaseModel):
    """
    The numeric outcomes of the Equity Bridge calculation.

    Attributes
    ----------
    market_cap : float
        Market Capitalization (Price x Shares) used as a witness.
    enterprise_value : float
        The core Operating Value derived from the DCF/Model.
    net_debt_resolved : float
        Calculated Net Debt (Total Debt - Cash & Equivalents).
    equity_value_total : float
        Final Intrinsic Equity Value (Enterprise Value - Net Debt).
    """

    market_cap: float = Field(..., description="Price x Shares (Market Witness).")
    enterprise_value: float = Field(..., description="Operating value result from the engine.")
    net_debt_resolved: float = Field(..., description="Calculated Net Debt (Total Debt - Cash).")
    equity_value_total: float = Field(..., description="Final Intrinsic Equity Value.")


class CommonResults(BaseModel):
    """
    Main container for shared valuation outputs.

    Attributes
    ----------
    rates : ResolvedRates
        The WACC and discount rates used in the model.
    capital : ResolvedCapital
        The bridge from Enterprise Value to Equity Value.
    intrinsic_value_per_share : float
        The final value per share (Equity Value / Shares Outstanding).
    upside_pct : float
        The potential upside vs market price (expressed as a decimal, e.g., 0.15 for 15%).
    bridge_trace : List[CalculationStep]
        The step-by-step audit trail of the Equity Bridge calculation.
    """

    rates: ResolvedRates
    capital: ResolvedCapital

    # --- Final Synthesis ---
    intrinsic_value_per_share: float
    upside_pct: float

    # --- Pillar 2: The Audit Trail ---
    bridge_trace: list[CalculationStep] = Field(default_factory=list)
