"""
src/models/parameters/common.py

UNIVERSAL VALUATION LEVERS
==========================
Role: Shared input parameters for financial rates and capital structure.
Architecture: Pydantic V2 with automated scaling via BaseNormalizedModel.
Note: Fixed Pylance "special object" error by removing redundant @classmethod.
"""

from __future__ import annotations
from typing import Optional, Annotated, Any
from pydantic import BaseModel, Field, field_validator, ValidationInfo

from src.models.parameters.ui_bridge import UIKey

class BaseNormalizedModel(BaseModel):
    """
    Base class providing automated scaling based on UIKey metadata.

    This class introspects field annotations to apply percentages
    or millions scaling before Pydantic validation.
    """
    @classmethod
    @field_validator("*", mode="before")
    def _apply_ui_scaling(cls, v: Any, info: ValidationInfo) -> Any:
        """
        Applies mathematical scaling based on UIKey 'scale' attribute.

        Note: Implicitly a class method in Pydantic V2.

        Parameters
        ----------
        v : Any
            The raw value to be scaled.
        info : ValidationInfo
            Pydantic context containing the field name.

        Returns
        -------
        Any
            Scaled value (e.g., 5.0 -> 0.05 for pct).
        """
        if v is None or not isinstance(v, (int, float)):
            return v

        field_def = cls.model_fields.get(info.field_name)
        if not field_def:
            return v

        # Extract UIKey from Annotated metadata
        ui_meta = next((m for m in field_def.metadata if isinstance(m, UIKey)), None)
        if not ui_meta:
            return v

        if ui_meta.scale == "pct":
            # Guard: only divide if value is human-readable (>1 or <-1)
            return v / 100.0 if abs(v) > 1.0 else v
        elif ui_meta.scale == "million":
            return v * 1_000_000.0

        return v

class FinancialRatesParameters(BaseNormalizedModel):
    """
    Universal financial discounting and risk parameters.

    Attributes
    ----------
    risk_free_rate : float, optional
        The theoretical rate of return of an investment with zero risk.
    market_risk_premium : float, optional
        Difference between expected market return and risk-free rate.
    beta : float, optional
        Measure of a stock's volatility in relation to the market.
    """
    risk_free_rate: Annotated[Optional[float], UIKey("rf", scale="pct")] = None
    market_risk_premium: Annotated[Optional[float], UIKey("mrp", scale="pct")] = None
    beta: Annotated[Optional[float], UIKey("beta", scale="raw")] = None
    cost_of_debt: Annotated[Optional[float], UIKey("kd", scale="pct")] = None
    tax_rate: Annotated[Optional[float], UIKey("tax", scale="pct")] = None
    corporate_aaa_yield: Annotated[Optional[float], UIKey("yield_aaa", scale="pct")] = None

class CapitalStructureParameters(BaseNormalizedModel):
    """
    Universal balance sheet and equity bridge components.

    Attributes
    ----------
    total_debt : float, optional
        Total interest-bearing liabilities in absolute units.
    shares_outstanding : float, optional
        Total number of shares for per-share calculation.
    """
    total_debt: Annotated[Optional[float], UIKey("debt", scale="million")] = None
    cash_and_equivalents: Annotated[Optional[float], UIKey("cash", scale="million")] = None
    minority_interests: Annotated[Optional[float], UIKey("min", scale="million")] = None
    pension_provisions: Annotated[Optional[float], UIKey("pen", scale="million")] = None
    shares_outstanding: Annotated[Optional[float], UIKey("shares", scale="million")] = None
    annual_dilution_rate: Annotated[Optional[float], UIKey("sbc_rate", scale="pct")] = None

class CommonParameters(BaseModel):
    """Main container for shared valuation inputs."""
    rates: FinancialRatesParameters = Field(default_factory=FinancialRatesParameters)
    capital: CapitalStructureParameters = Field(default_factory=CapitalStructureParameters)