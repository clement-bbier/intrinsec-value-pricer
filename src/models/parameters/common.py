"""
src/models/parameters/common.py

UNIVERSAL VALUATION LEVERS
==========================
Role: Shared input parameters for financial rates and capital structure.
Architecture: Pydantic V2 with automated scaling via BaseNormalizedModel.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Optional, Annotated, Any
from pydantic import BaseModel, Field, model_validator

from src.models.parameters.input_metadata import UIKey


class BaseNormalizedModel(BaseModel):
    """
    Base class providing automated scaling based on UIKey metadata.

    Introspects field annotations to automatically apply percentage (100x)
    or magnitude (1M x) scaling before validation occurs.
    """

    @model_validator(mode="before") # noqa
    @classmethod
    def apply_ui_scaling(cls, data: Any) -> Any:
        """
        Global pre-validator that scales inputs based on UIKey annotations.

        This runs once for the whole model, satisfying both Pydantic V2
        requirements and IDE static analysis (valid classmethod).

        Parameters
        ----------
        data : Any
            The raw input dictionary.

        Returns
        -------
        Any
            The dictionary with scaled values.
        """
        if not isinstance(data, dict):
            return data

        # Iterate over inputs to find fields needing scaling
        for field_name, value in data.items():
            # Skip empty or non-numeric values
            if value is None or not isinstance(value, (int, float)):
                continue

            # Retrieve field definition from the Pydantic model
            field_def = cls.model_fields.get(field_name)
            if not field_def:
                continue

            # Look for UIKey in the metadata
            ui_meta = next((m for m in field_def.metadata if isinstance(m, UIKey)), None)
            if not ui_meta:
                continue

            # Apply scaling logic
            if ui_meta.scale == "pct":
                # Logic: If user types "5", they mean 5%. If "0.05", it stays 0.05.
                if abs(value) > 1.0:
                    data[field_name] = value / 100.0

            elif ui_meta.scale == "million":
                # Logic: 100 (entered as M) -> 100,000,000
                data[field_name] = value * 1_000_000.0

        return data


class FinancialRatesParameters(BaseNormalizedModel):
    """
    Universal financial discounting and risk parameters.

    Attributes
    ----------
    risk_free_rate : float | None
        The theoretical rate of return of an investment with zero risk.
    market_risk_premium : float | None
        The excess return expected from the market portfolio over the risk-free rate.
    beta : float | None
        A measure of the stock's volatility in relation to the overall market.
    cost_of_debt : float | None
        The effective rate that a company pays on its debt (Pre-tax).
    tax_rate : float | None
        The marginal corporate tax rate used to calculate the tax shield.
    corporate_aaa_yield : float | None
        The benchmark yield for high-grade corporate bonds (used in Graham formulas).
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
    total_debt : float | None
        Total interest-bearing liabilities (Short + Long Term).
    cash_and_equivalents : float | None
        Liquid assets available to offset debt (Cash, Marketable Securities).
    minority_interests : float | None
        Value of the portion of subsidiaries not owned by the parent company.
    pension_provisions : float | None
        Unfunded pension obligations treated as debt-equivalents.
    shares_outstanding : float | None
        Total number of shares used to calculate per-share intrinsic value.
    annual_dilution_rate : float | None
        Expected annual increase in share count due to SBC (Stock-Based Compensation).
    """
    total_debt: Annotated[Optional[float], UIKey("debt", scale="million")] = None
    cash_and_equivalents: Annotated[Optional[float], UIKey("cash", scale="million")] = None
    minority_interests: Annotated[Optional[float], UIKey("min", scale="million")] = None
    pension_provisions: Annotated[Optional[float], UIKey("pen", scale="million")] = None
    shares_outstanding: Annotated[Optional[float], UIKey("shares", scale="million")] = None
    annual_dilution_rate: Annotated[Optional[float], UIKey("sbc_rate", scale="pct")] = None


class CommonParameters(BaseModel):
    """
    Main container for shared valuation inputs.

    Attributes
    ----------
    rates : FinancialRatesParameters
        Discounting and WACC components.
    capital : CapitalStructureParameters
        Equity bridge and share count components.
    """
    rates: FinancialRatesParameters = Field(default_factory=FinancialRatesParameters)
    capital: CapitalStructureParameters = Field(default_factory=CapitalStructureParameters)