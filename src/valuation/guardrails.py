"""
src/valuation/guardrails.py

ECONOMIC GUARDRAILS
===================
Role: Validates key economic constraints to prevent unrealistic valuation assumptions.
Scope: Terminal growth vs. WACC, ROIC spreads, capital structure sanity, scenario probabilities.
Architecture: Pure functions returning structured check results.
Style: Numpy docstrings, type-safe, institutional-grade validations.
"""

from __future__ import annotations

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.parameters.strategies import (
    FCFFStandardParameters,
    FCFFNormalizedParameters,
    FCFFGrowthParameters,
    FCFEParameters,
    DDMParameters,
    RIMParameters,
)


class GuardrailCheckResult(BaseModel):
    """
    Structured result of a guardrail validation check.

    Attributes
    ----------
    type : Literal['error', 'warning', 'info']
        Severity level of the check result.
        - 'error': Blocking issue that prevents valuation.
        - 'warning': Non-blocking concern that should be reviewed.
        - 'info': Informational message for transparency.
    message : str
        Human-readable description of the check result.
    code : str
        Unique identifier for the check (e.g., "GUARDRAIL_TERMINAL_GROWTH_EXCEEDS_WACC").
    extra : dict[str, Any], optional
        Additional contextual data (e.g., {"g": 0.12, "wacc": 0.10}).
    """

    type: Literal["error", "warning", "info"]
    message: str
    code: str
    extra: dict[str, Any] = Field(default_factory=dict)


def validate_terminal_growth(params: Parameters, wacc: float) -> GuardrailCheckResult:
    """
    Validates that the terminal growth rate is economically plausible relative to WACC.

    Economic Rule
    -------------
    The perpetual growth rate (g) must be strictly less than the discount rate (WACC)
    for the Gordon Growth Model to converge. In practice:
    - g >= WACC: Model diverges → ERROR (blocking)
    - g close to WACC (within 0.5%): Risky assumption → WARNING
    - g << WACC: Normal case → INFO (if g > 0)

    Parameters
    ----------
    params : Parameters
        The complete parameter set for the valuation.
    wacc : float
        The calculated Weighted Average Cost of Capital.

    Returns
    -------
    GuardrailCheckResult
        Structured check result with severity level and details.

    Notes
    -----
    - Only applies to strategies with terminal value parameters.
    - If terminal growth is not set (None), returns INFO with no issue.
    - Threshold for "close" is defined as 0.005 (0.5%).
    """
    strategy = params.strategy

    # Extract terminal growth rate from strategy parameters
    g = None
    if hasattr(strategy, "terminal_value") and strategy.terminal_value:
        g = strategy.terminal_value.perpetual_growth_rate

    # If no growth rate is set, nothing to validate
    if g is None:
        return GuardrailCheckResult(
            type="info",
            message="Terminal growth rate not specified (OK).",
            code="GUARDRAIL_TERMINAL_GROWTH_NOT_SET",
            extra={"wacc": wacc},
        )

    # BLOCKING ERROR: g >= WACC (model diverges)
    if g >= wacc:
        return GuardrailCheckResult(
            type="error",
            message=f"Terminal growth rate ({g:.2%}) must be strictly less than WACC ({wacc:.2%}). "
            f"The Gordon Growth Model cannot converge when g ≥ WACC.",
            code="GUARDRAIL_TERMINAL_GROWTH_EXCEEDS_WACC",
            extra={"g": g, "wacc": wacc, "spread": g - wacc},
        )

    # WARNING: g is very close to WACC (within 0.5%)
    threshold = 0.005
    if wacc - g < threshold:
        return GuardrailCheckResult(
            type="warning",
            message=f"Terminal growth rate ({g:.2%}) is dangerously close to WACC ({wacc:.2%}). "
            f"This produces extreme terminal value sensitivity. Consider reducing g.",
            code="GUARDRAIL_TERMINAL_GROWTH_CLOSE_TO_WACC",
            extra={"g": g, "wacc": wacc, "spread": wacc - g, "threshold": threshold},
        )

    # INFO: Normal case (g is positive and reasonable)
    if g > 0:
        return GuardrailCheckResult(
            type="info",
            message=f"Terminal growth rate ({g:.2%}) is below WACC ({wacc:.2%}) with adequate spread "
            f"({wacc - g:.2%}).",
            code="GUARDRAIL_TERMINAL_GROWTH_OK",
            extra={"g": g, "wacc": wacc, "spread": wacc - g},
        )

    # INFO: g is zero or negative (conservative assumption)
    return GuardrailCheckResult(
        type="info",
        message=f"Terminal growth rate ({g:.2%}) is conservative (zero or negative growth).",
        code="GUARDRAIL_TERMINAL_GROWTH_CONSERVATIVE",
        extra={"g": g, "wacc": wacc},
    )


def validate_roic_spread(
    financials: Company, params: Parameters, wacc: float
) -> GuardrailCheckResult:
    """
    Validates the Return on Invested Capital (ROIC) spread relative to WACC.

    Economic Rule
    -------------
    Companies can only sustain growth above their cost of capital if they generate
    returns (ROIC) above WACC. Key checks:
    - If ROIC < WACC and g > 0: Company is destroying value while growing → WARNING
    - If ROIC ≈ WACC: No economic profit, growth is neutral → INFO

    Parameters
    ----------
    financials : Company
        Company identity and market data.
    params : Parameters
        The complete parameter set for the valuation.
    wacc : float
        The calculated Weighted Average Cost of Capital.

    Returns
    -------
    GuardrailCheckResult
        Structured check result with severity level and details.

    Notes
    -----
    - ROIC is approximated as EBIT * (1 - tax_rate) / Invested Capital
    - Invested Capital = Total Debt + Market Equity - Cash
    - If data is insufficient to calculate ROIC, returns INFO (no check).
    - Tolerance for "approximately equal" is 0.01 (1%).
    """
    # Extract financial data for ROIC calculation
    capital = params.common.capital
    rates = params.common.rates

    total_debt = capital.total_debt if capital.total_debt else 0.0
    cash = capital.cash_and_equivalents if capital.cash_and_equivalents else 0.0
    shares = capital.shares_outstanding if capital.shares_outstanding else 1.0
    price = financials.current_price
    tax_rate = rates.tax_rate if rates.tax_rate else 0.21

    # Get EBIT from financials (if available)
    ebit = getattr(financials, "ebit_ttm", None)
    if ebit is None or ebit <= 0:
        return GuardrailCheckResult(
            type="info",
            message="Insufficient data to calculate ROIC (EBIT not available).",
            code="GUARDRAIL_ROIC_DATA_INSUFFICIENT",
            extra={"wacc": wacc},
        )

    # Calculate NOPAT (Net Operating Profit After Tax)
    nopat = ebit * (1.0 - tax_rate)

    # Calculate Invested Capital
    market_equity = price * shares
    invested_capital = total_debt + market_equity - cash

    if invested_capital <= 0:
        return GuardrailCheckResult(
            type="info",
            message="Invalid invested capital calculation (≤ 0). Cannot compute ROIC.",
            code="GUARDRAIL_ROIC_INVALID_CAPITAL",
            extra={"invested_capital": invested_capital, "wacc": wacc},
        )

    # Calculate ROIC
    roic = nopat / invested_capital

    # Extract growth rate from strategy
    g = _extract_growth_rate(params.strategy)
    if g is None or g <= 0:
        # No growth, so ROIC spread is not critical
        return GuardrailCheckResult(
            type="info",
            message=f"ROIC ({roic:.2%}) vs. WACC ({wacc:.2%}). No positive growth assumed, so spread is not critical.",
            code="GUARDRAIL_ROIC_NO_GROWTH",
            extra={"roic": roic, "wacc": wacc, "spread": roic - wacc, "growth": g},
        )

    # WARNING: ROIC < WACC with positive growth (value destruction)
    if roic < wacc:
        return GuardrailCheckResult(
            type="warning",
            message=f"ROIC ({roic:.2%}) is below WACC ({wacc:.2%}) while assuming positive growth ({g:.2%}). "
            f"This implies value destruction. Consider revising growth or margin assumptions.",
            code="GUARDRAIL_ROIC_BELOW_WACC_WITH_GROWTH",
            extra={"roic": roic, "wacc": wacc, "spread": roic - wacc, "growth": g},
        )

    # INFO: ROIC approximately equals WACC (neutral)
    tolerance = 0.01
    if abs(roic - wacc) < tolerance:
        return GuardrailCheckResult(
            type="info",
            message=f"ROIC ({roic:.2%}) approximately equals WACC ({wacc:.2%}). No economic profit.",
            code="GUARDRAIL_ROIC_NEUTRAL",
            extra={"roic": roic, "wacc": wacc, "spread": roic - wacc, "tolerance": tolerance},
        )

    # INFO: ROIC > WACC (value creation)
    return GuardrailCheckResult(
        type="info",
        message=f"ROIC ({roic:.2%}) exceeds WACC ({wacc:.2%}) by {roic - wacc:.2%}. Value creation confirmed.",
        code="GUARDRAIL_ROIC_ABOVE_WACC",
        extra={"roic": roic, "wacc": wacc, "spread": roic - wacc, "growth": g},
    )


def validate_capital_structure(
    financials: Company, params: Parameters
) -> GuardrailCheckResult:
    """
    Validates the sanity of the capital structure (debt, equity, cash).

    Economic Rule
    -------------
    - Total debt and cash should be non-negative.
    - Shares outstanding must be positive.
    - Debt/Equity ratio should be plausible (not exceeding 10x for non-distressed firms).
    - Cash should not exceed total debt by extreme multiples (>5x may indicate holding company).

    Parameters
    ----------
    financials : Company
        Company identity and market data.
    params : Parameters
        The complete parameter set for the valuation.

    Returns
    -------
    GuardrailCheckResult
        Structured check result with severity level and details.

    Notes
    -----
    - Checks are designed for typical operating companies.
    - Financial institutions and holding companies may violate these rules normally.
    """
    capital = params.common.capital

    total_debt = capital.total_debt if capital.total_debt else 0.0
    cash = capital.cash_and_equivalents if capital.cash_and_equivalents else 0.0
    shares = capital.shares_outstanding if capital.shares_outstanding else None

    # ERROR: Negative debt
    if total_debt < 0:
        return GuardrailCheckResult(
            type="error",
            message=f"Total debt is negative ({total_debt:.2f}M). This is not economically valid.",
            code="GUARDRAIL_CAPITAL_NEGATIVE_DEBT",
            extra={"total_debt": total_debt},
        )

    # ERROR: Negative cash
    if cash < 0:
        return GuardrailCheckResult(
            type="error",
            message=f"Cash and equivalents are negative ({cash:.2f}M). This is not valid.",
            code="GUARDRAIL_CAPITAL_NEGATIVE_CASH",
            extra={"cash": cash},
        )

    # ERROR: Non-positive shares outstanding
    if shares is None or shares <= 0:
        return GuardrailCheckResult(
            type="error",
            message=f"Shares outstanding must be positive (got {shares}).",
            code="GUARDRAIL_CAPITAL_INVALID_SHARES",
            extra={"shares_outstanding": shares},
        )

    # WARNING: Extreme debt/equity ratio
    price = financials.current_price
    market_equity = price * shares
    if market_equity > 0:
        debt_equity_ratio = total_debt / market_equity
        if debt_equity_ratio > 10.0:
            return GuardrailCheckResult(
                type="warning",
                message=f"Debt/Equity ratio ({debt_equity_ratio:.2f}x) is extremely high. "
                f"This may indicate financial distress or special situation.",
                code="GUARDRAIL_CAPITAL_EXTREME_DEBT_EQUITY",
                extra={
                    "debt_equity_ratio": debt_equity_ratio,
                    "total_debt": total_debt,
                    "market_equity": market_equity,
                },
            )

    # WARNING: Excessive cash relative to debt
    if total_debt > 0 and cash / total_debt > 5.0:
        return GuardrailCheckResult(
            type="warning",
            message=f"Cash ({cash:.2f}M) is {cash / total_debt:.2f}x total debt ({total_debt:.2f}M). "
            f"This may indicate a holding company or unusual balance sheet.",
            code="GUARDRAIL_CAPITAL_EXCESSIVE_CASH",
            extra={"cash": cash, "total_debt": total_debt, "ratio": cash / total_debt},
        )

    # INFO: Normal capital structure
    net_debt = total_debt - cash
    return GuardrailCheckResult(
        type="info",
        message=f"Capital structure is valid. Net debt: {net_debt:.2f}M, Shares: {shares:.2f}M.",
        code="GUARDRAIL_CAPITAL_OK",
        extra={
            "total_debt": total_debt,
            "cash": cash,
            "net_debt": net_debt,
            "shares_outstanding": shares,
        },
    )


def validate_scenario_probabilities(params: Parameters) -> GuardrailCheckResult:
    """
    Validates that scenario probabilities sum to 1.0 (100%).

    Economic Rule
    -------------
    When multiple scenarios are defined, their probabilities must sum to exactly 1.0
    (within a tolerance of 0.01) to ensure a valid probability distribution.

    Parameters
    ----------
    params : Parameters
        The complete parameter set for the valuation.

    Returns
    -------
    GuardrailCheckResult
        Structured check result with severity level and details.

    Notes
    -----
    - Applies only when scenarios are enabled.
    - Tolerance is set at 0.01 (1%) to allow for rounding.
    - If sum is outside [0.99, 1.01], returns ERROR.
    - If sum is in [0.99, 1.01] but not exactly 1.0, returns WARNING.
    """
    extensions = params.extensions
    scenarios_params = extensions.scenarios

    # If scenarios are not enabled, nothing to check
    if not scenarios_params.enabled or not scenarios_params.cases:
        return GuardrailCheckResult(
            type="info",
            message="Scenarios are not enabled or no cases defined.",
            code="GUARDRAIL_SCENARIOS_NOT_ENABLED",
            extra={},
        )

    # Extract probabilities
    cases = scenarios_params.cases
    probabilities = [
        case.probability if case.probability is not None else 0.0 for case in cases
    ]
    prob_sum = sum(probabilities)

    # Define tolerance
    tolerance = 0.01
    lower_bound = 1.0 - tolerance
    upper_bound = 1.0 + tolerance

    # ERROR: Probabilities sum outside acceptable range
    if prob_sum < lower_bound or prob_sum > upper_bound:
        return GuardrailCheckResult(
            type="error",
            message=f"Scenario probabilities sum to {prob_sum:.4f}, which is outside the acceptable range "
            f"[{lower_bound:.2f}, {upper_bound:.2f}]. They must sum to 1.0 (100%).",
            code="GUARDRAIL_SCENARIOS_PROBABILITIES_INVALID_SUM",
            extra={
                "prob_sum": prob_sum,
                "probabilities": probabilities,
                "num_scenarios": len(cases),
                "tolerance": tolerance,
            },
        )

    # WARNING: Probabilities sum within tolerance but not exact
    if prob_sum != 1.0:
        return GuardrailCheckResult(
            type="warning",
            message=f"Scenario probabilities sum to {prob_sum:.4f}, which is close to 1.0 but not exact. "
            f"Consider adjusting for precision.",
            code="GUARDRAIL_SCENARIOS_PROBABILITIES_INEXACT",
            extra={
                "prob_sum": prob_sum,
                "probabilities": probabilities,
                "num_scenarios": len(cases),
                "difference": prob_sum - 1.0,
            },
        )

    # INFO: Perfect sum
    return GuardrailCheckResult(
        type="info",
        message=f"Scenario probabilities sum to exactly 1.0 across {len(cases)} cases.",
        code="GUARDRAIL_SCENARIOS_PROBABILITIES_OK",
        extra={
            "prob_sum": prob_sum,
            "probabilities": probabilities,
            "num_scenarios": len(cases),
        },
    )


def _extract_growth_rate(strategy: Any) -> Optional[float]:
    """
    Extracts the primary growth rate from a strategy parameter object.

    Parameters
    ----------
    strategy : Any
        The strategy parameters (polymorphic union type).

    Returns
    -------
    float or None
        The extracted growth rate, or None if not applicable.

    Notes
    -----
    - Attempts to extract growth from multiple possible fields:
      - growth_rate_p1 (FCFFStandardParameters)
      - cycle_growth_rate (FCFFNormalizedParameters)
      - revenue_growth_rate (FCFFGrowthParameters)
      - dividend_growth_rate (DDMParameters)
      - Terminal growth rate as fallback
    """
    # Try standard growth rate fields
    if hasattr(strategy, "growth_rate_p1") and strategy.growth_rate_p1 is not None:
        return strategy.growth_rate_p1

    if (
        hasattr(strategy, "cycle_growth_rate")
        and strategy.cycle_growth_rate is not None
    ):
        return strategy.cycle_growth_rate

    if (
        hasattr(strategy, "revenue_growth_rate")
        and strategy.revenue_growth_rate is not None
    ):
        return strategy.revenue_growth_rate

    if (
        hasattr(strategy, "dividend_growth_rate")
        and strategy.dividend_growth_rate is not None
    ):
        return strategy.dividend_growth_rate

    # Fallback: terminal growth rate
    if hasattr(strategy, "terminal_value") and strategy.terminal_value:
        return strategy.terminal_value.perpetual_growth_rate

    return None
