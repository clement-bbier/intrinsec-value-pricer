"""
src/valuation/resolvers/parameter_resolver.py

PARAMETER RESOLVER — Cascade Resolution for Critical Financial Parameters

Version : V1.0 — Phase 2 Data Integrity
Role : Guarantees zero-None outputs for all critical valuation parameters.
Pattern : Chain of Responsibility (Override > Snapshot > Fallback > Default)

Resolution cascade (priority order):
    1. Override (UI)     — Manual expert input from the user
    2. Snapshot (Data)   — Auto-calculated from financial data (Yahoo/API)
    3. Fallback (Macro)  — Sector/macro-level defaults
    4. Default (System)  — Hard-coded system defaults from constants.py

Dependencies:
    - src.domain.models.DCFParameters
    - src.domain.models.CompanyFinancials
    - src.config.constants.SystemDefaults, MacroDefaults
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.domain.models import CompanyFinancials, DCFParameters
from src.config.constants import SystemDefaults, MacroDefaults

logger = logging.getLogger(__name__)


@dataclass
class ResolvedRates:
    """
    Resolved rate parameters with guaranteed non-None values.

    All fields are strict float (never None) after resolution.

    Attributes
    ----------
    risk_free_rate : float
        Risk-free rate (e.g., 10Y Treasury yield).
    market_risk_premium : float
        Equity risk premium above risk-free rate.
    beta : float
        Systematic risk factor.
    cost_of_debt : float
        Pre-tax cost of debt financing.
    tax_rate : float
        Effective corporate tax rate.
    """

    risk_free_rate: float
    market_risk_premium: float
    beta: float
    cost_of_debt: float
    tax_rate: float


@dataclass
class ResolvedGrowth:
    """
    Resolved growth parameters with guaranteed non-None values.

    Attributes
    ----------
    fcf_growth_rate : float
        Phase 1 growth rate for projected cash flows.
    perpetual_growth_rate : float
        Terminal (Gordon) perpetual growth rate.
    """

    fcf_growth_rate: float
    perpetual_growth_rate: float


class ParameterResolver:
    """
    Cascade resolver for critical financial parameters.

    Ensures that the valuation engine never receives None values
    for rate or growth parameters. Applies the resolution cascade:
    Override (UI) > Snapshot (Data) > Fallback (Macro) > Default (System).

    Notes
    -----
    This resolver does NOT mutate the input DCFParameters object.
    It returns resolved dataclasses that the caller can use to
    patch parameters before passing to the engine.

    Examples
    --------
    >>> resolver = ParameterResolver()
    >>> resolved = resolver.resolve_rates(params, financials)
    >>> assert resolved.risk_free_rate is not None
    """

    @staticmethod
    def resolve_rates(
        params: DCFParameters,
        financials: CompanyFinancials,
    ) -> ResolvedRates:
        """
        Resolve all rate parameters through the cascade.

        Parameters
        ----------
        params : DCFParameters
            Parameters with potential None values from UI/auto.
        financials : CompanyFinancials
            Company data snapshot for fallback values.

        Returns
        -------
        ResolvedRates
            Fully resolved rates (guaranteed non-None).
        """
        r = params.rates

        # Risk-free rate: Override > Auto > MacroDefaults > SystemDefaults
        risk_free_rate = _resolve(
            r.risk_free_rate,
            None,  # No snapshot-level override for Rf
            MacroDefaults.FALLBACK_RISK_FREE_RATE_USD,
            SystemDefaults.DEFAULT_RISK_FREE_RATE,
            "risk_free_rate",
        )

        # Market risk premium: Override > MacroDefaults > SystemDefaults
        market_risk_premium = _resolve(
            r.market_risk_premium,
            None,
            MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM,
            SystemDefaults.DEFAULT_MARKET_RISK_PREMIUM,
            "market_risk_premium",
        )

        # Beta: Override > Snapshot (financials) > SystemDefaults
        beta = _resolve(
            r.manual_beta,
            financials.beta,
            None,
            SystemDefaults.DEFAULT_BETA,
            "beta",
        )

        # Cost of debt: Override > SystemDefaults (synthetic rating handled downstream)
        cost_of_debt = _resolve(
            r.cost_of_debt,
            None,
            None,
            SystemDefaults.DEFAULT_COST_OF_DEBT,
            "cost_of_debt",
        )

        # Tax rate: Override > SystemDefaults
        tax_rate = _resolve(
            r.tax_rate,
            None,
            None,
            SystemDefaults.DEFAULT_TAX_RATE,
            "tax_rate",
        )

        logger.debug(
            "Rates resolved: rf=%.4f, mrp=%.4f, beta=%.2f, kd=%.4f, tax=%.4f",
            risk_free_rate, market_risk_premium, beta, cost_of_debt, tax_rate,
        )

        return ResolvedRates(
            risk_free_rate=risk_free_rate,
            market_risk_premium=market_risk_premium,
            beta=beta,
            cost_of_debt=cost_of_debt,
            tax_rate=tax_rate,
        )

    @staticmethod
    def resolve_growth(
        params: DCFParameters,
        financials: CompanyFinancials,
    ) -> ResolvedGrowth:
        """
        Resolve growth parameters through the cascade.

        Parameters
        ----------
        params : DCFParameters
            Parameters with potential None values.
        financials : CompanyFinancials
            Company data snapshot (CAGR, sector data).

        Returns
        -------
        ResolvedGrowth
            Fully resolved growth rates (guaranteed non-None).
        """
        g = params.growth

        # FCF growth: Override > Snapshot (historical CAGR) > SystemDefaults
        fcf_growth_rate = _resolve(
            g.fcf_growth_rate,
            getattr(financials, "historical_cagr", None),
            None,
            SystemDefaults.DEFAULT_PERPETUAL_GROWTH,  # Conservative default
            "fcf_growth_rate",
        )

        # Perpetual growth: Override > SystemDefaults (capped at inflation LT)
        perpetual_growth_rate = _resolve(
            g.perpetual_growth_rate,
            None,
            None,
            SystemDefaults.DEFAULT_PERPETUAL_GROWTH,
            "perpetual_growth_rate",
        )

        logger.debug(
            "Growth resolved: fcf_g=%.4f, perp_g=%.4f",
            fcf_growth_rate, perpetual_growth_rate,
        )

        return ResolvedGrowth(
            fcf_growth_rate=fcf_growth_rate,
            perpetual_growth_rate=perpetual_growth_rate,
        )

    @staticmethod
    def apply_resolved_params(
        params: DCFParameters,
        financials: CompanyFinancials,
    ) -> DCFParameters:
        """
        Apply the full resolution cascade and return patched parameters.

        Creates a deep copy of params with all None values replaced by
        resolved defaults. The returned object is safe for the engine
        (no None on critical fields).

        Parameters
        ----------
        params : DCFParameters
            Original parameters (not mutated).
        financials : CompanyFinancials
            Company data for snapshot-level resolution.

        Returns
        -------
        DCFParameters
            Deep copy with all critical fields resolved (non-None).
        """
        resolved_params = params.model_copy(deep=True)

        # Resolve rates
        rates = ParameterResolver.resolve_rates(params, financials)
        if resolved_params.rates.risk_free_rate is None:
            resolved_params.rates.risk_free_rate = rates.risk_free_rate
        if resolved_params.rates.market_risk_premium is None:
            resolved_params.rates.market_risk_premium = rates.market_risk_premium
        if resolved_params.rates.manual_beta is None and (financials.beta is None or financials.beta == 0):
            resolved_params.rates.manual_beta = rates.beta
        if resolved_params.rates.cost_of_debt is None:
            resolved_params.rates.cost_of_debt = rates.cost_of_debt
        if resolved_params.rates.tax_rate is None:
            resolved_params.rates.tax_rate = rates.tax_rate

        # Resolve growth
        growth = ParameterResolver.resolve_growth(params, financials)
        if resolved_params.growth.fcf_growth_rate is None:
            resolved_params.growth.fcf_growth_rate = growth.fcf_growth_rate
        if resolved_params.growth.perpetual_growth_rate is None:
            resolved_params.growth.perpetual_growth_rate = growth.perpetual_growth_rate

        return resolved_params


def _resolve(
    override: Optional[float],
    snapshot: Optional[float],
    fallback: Optional[float],
    default: float,
    field_name: str,
) -> float:
    """
    Apply the 4-level cascade to resolve a single parameter.

    Parameters
    ----------
    override : float or None
        Level 1 — User/expert override.
    snapshot : float or None
        Level 2 — Data snapshot from API/provider.
    fallback : float or None
        Level 3 — Sector/macro-level fallback.
    default : float
        Level 4 — System default (always non-None).
    field_name : str
        Name for logging purposes.

    Returns
    -------
    float
        Resolved value (guaranteed non-None).
    """
    if override is not None:
        logger.debug("Resolved %s via OVERRIDE: %.6f", field_name, override)
        return override
    if snapshot is not None:
        logger.debug("Resolved %s via SNAPSHOT: %.6f", field_name, snapshot)
        return snapshot
    if fallback is not None:
        logger.debug("Resolved %s via FALLBACK: %.6f", field_name, fallback)
        return fallback
    logger.debug("Resolved %s via DEFAULT: %.6f", field_name, default)
    return default
