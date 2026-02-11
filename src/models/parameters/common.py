"""
src/models/parameters/common.py

UNIVERSAL VALUATION LEVERS
==========================
Role: Shared input parameters for financial rates and capital structure.
Architecture: Pydantic V2 with automated scaling via BaseNormalizedModel.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Annotated, Any

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
        for field_name, value in data.items():
            if value is None or not isinstance(value, (int, float)):
                continue
            field_def = cls.model_fields.get(field_name)
            if not field_def:
                continue
            ui_meta = next((m for m in field_def.metadata if isinstance(m, UIKey)), None)
            if not ui_meta:
                continue
            if ui_meta.scale == "pct":
                if abs(value) > 1.0:
                    data[field_name] = value / 100.0
            elif ui_meta.scale == "million":
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
    risk_free_rate: Annotated[float | None, UIKey("rf", scale="pct")] = None
    market_risk_premium: Annotated[float | None, UIKey("mrp", scale="pct")] = None
    beta: Annotated[float | None, UIKey("beta", scale="raw")] = None
    cost_of_debt: Annotated[float | None, UIKey("kd", scale="pct")] = None
    tax_rate: Annotated[float | None, UIKey("tax", scale="pct")] = None
    corporate_aaa_yield: Annotated[float | None, UIKey("yield_aaa", scale="pct")] = None
    wacc: Annotated[float | None, UIKey("wacc_override", scale="pct")] = None
    cost_of_equity: Annotated[float | None, UIKey("ke_override", scale="pct")] = None


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
    total_debt: Annotated[float | None, UIKey("debt", scale="million")] = None
    cash_and_equivalents: Annotated[float | None, UIKey("cash", scale="million")] = None
    minority_interests: Annotated[float | None, UIKey("min", scale="million")] = None
    pension_provisions: Annotated[float | None, UIKey("pen", scale="million")] = None
    shares_outstanding: Annotated[float | None, UIKey("shares", scale="million")] = None
    annual_dilution_rate: Annotated[float | None, UIKey("sbc_rate", scale="pct")] = None


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
