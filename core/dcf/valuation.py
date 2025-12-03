import logging
from typing import List

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.exceptions import CalculationError
from core.dcf.fcf import project_fcfs
from core.dcf.wacc import compute_cost_of_equity, compute_wacc

logger = logging.getLogger(__name__)


def _compute_discount_factors(rate: float, years: int) -> List[float]:
    """
    Returns [ (1+rate)^1, (1+rate)^2, ..., (1+rate)^years ]
    """
    return [(1.0 + rate) ** t for t in range(1, years + 1)]


def run_dcf(financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
    """
    Main DCF engine: projects FCFF, computes WACC, terminal value and IV per share
    with full granular logging.
    """

    logger.info("=== DCF ENGINE START for %s ===", financials.ticker)

    # ---------------------------------------------------------
    # 1) Compute market-based equity value
    # ---------------------------------------------------------
    equity_value_market = financials.current_price * financials.shares_outstanding
    logger.info(
        "[1] Market Equity Value E = Price * Shares = %.2f * %.0f = %.2f",
        financials.current_price,
        financials.shares_outstanding,
        equity_value_market,
    )

    # ---------------------------------------------------------
    # 2) Cost of equity (CAPM)
    # ---------------------------------------------------------
    cost_of_equity = compute_cost_of_equity(
        risk_free_rate=params.risk_free_rate,
        beta=financials.beta,
        market_risk_premium=params.market_risk_premium,
    )

    logger.info(
        "[2] Cost of equity (CAPM) Re = Rf + beta * MRP = %.4f + %.4f * %.4f = %.4f",
        params.risk_free_rate,
        financials.beta,
        params.market_risk_premium,
        cost_of_equity,
    )

    # ---------------------------------------------------------
    # 3) WACC
    # ---------------------------------------------------------
    wacc, after_tax_cost_of_debt = compute_wacc(
        equity_value=equity_value_market,
        debt_value=financials.total_debt,
        cost_of_equity=cost_of_equity,
        cost_of_debt=params.cost_of_debt,
        tax_rate=params.tax_rate,
    )

    logger.info(
        "[3] WACC = (E/(E+D))*Re + (D/(E+D))*Rd(1-T) = %.6f",
        wacc,
    )
    logger.info("[3] After-tax cost of debt Rd(1-T) = %.6f", after_tax_cost_of_debt)

    if wacc <= params.perpetual_growth_rate:
        logger.error(
            "[3] INVALID: WACC (%.6f) <= g∞ (%.6f) → terminal value undefined.",
            wacc,
            params.perpetual_growth_rate,
        )
        raise CalculationError(
            f"WACC ({wacc:.4f}) must be strictly greater than perpetual growth "
            f"rate g ({params.perpetual_growth_rate:.4f})."
        )

    # ---------------------------------------------------------
    # 4) FCFF projections
    # ---------------------------------------------------------
    logger.info(
        "[4] Starting FCFF_last = %.2f | growth rate g = %.4f | years = %d",
        financials.fcf_last,
        params.fcf_growth_rate,
        params.projection_years,
    )

    projected_fcfs = project_fcfs(
        fcf_last=financials.fcf_last,
        years=params.projection_years,
        growth_rate=params.fcf_growth_rate,
    )

    if not projected_fcfs:
        logger.error("[4] No projected FCFF values (projection_years <= 0).")
        raise CalculationError("No projected FCFs – projection_years must be > 0.")

    logger.info("[4] Projected FCFFs: %s", [round(x, 2) for x in projected_fcfs])

    # ---------------------------------------------------------
    # 5) Discount factors & discounted FCFF
    # ---------------------------------------------------------
    discount_factors = _compute_discount_factors(wacc, params.projection_years)
    discounted_fcfs = [fcf / df for fcf, df in zip(projected_fcfs, discount_factors)]
    sum_discounted_fcf = sum(discounted_fcfs)

    logger.info("[5] Discount factors DF_t = (1+WACC)^t : %s",
                [round(df, 4) for df in discount_factors])
    logger.info("[5] Discounted FCFFs: %s",
                [round(x, 2) for x in discounted_fcfs])
    logger.info("[5] Sum of discounted FCFF = %.2f", sum_discounted_fcf)

    # ---------------------------------------------------------
    # 6) Terminal Value (Gordon–Shapiro)
    # ---------------------------------------------------------
    last_fcf = projected_fcfs[-1]
    fcf_terminal = last_fcf * (1.0 + params.perpetual_growth_rate)

    logger.info(
        "[6] FCF_terminal = FCFF_n * (1+g∞) = %.2f * (1 + %.4f) = %.2f",
        last_fcf,
        params.perpetual_growth_rate,
        fcf_terminal,
    )

    terminal_value = fcf_terminal / (wacc - params.perpetual_growth_rate)
    discounted_terminal_value = terminal_value / discount_factors[-1]

    logger.info(
        "[6] Terminal Value TV = FCF_{n+1} / (WACC - g∞) = %.2f / (%.6f - %.6f) = %.2f",
        fcf_terminal,
        wacc,
        params.perpetual_growth_rate,
        terminal_value,
    )
    logger.info(
        "[6] Discounted TV = TV / DF_n = %.2f / %.4f = %.2f",
        terminal_value,
        discount_factors[-1],
        discounted_terminal_value,
    )

    # ---------------------------------------------------------
    # 7) Enterprise Value
    # ---------------------------------------------------------
    enterprise_value = sum_discounted_fcf + discounted_terminal_value
    logger.info(
        "[7] Enterprise Value EV = Sum(DCF) + DTV = %.2f + %.2f = %.2f",
        sum_discounted_fcf,
        discounted_terminal_value,
        enterprise_value,
    )

    # ---------------------------------------------------------
    # 8) Equity Value (model)
    # ---------------------------------------------------------
    equity_value_model = enterprise_value - financials.total_debt + financials.cash_and_equivalents
    logger.info(
        "[8] Equity(model) = EV - Debt + Cash = %.2f - %.2f + %.2f = %.2f",
        enterprise_value,
        financials.total_debt,
        financials.cash_and_equivalents,
        equity_value_model,
    )

    # ---------------------------------------------------------
    # 9) Intrinsic Value per Share
    # ---------------------------------------------------------
    if financials.shares_outstanding <= 0:
        logger.error("[9] Invalid shares outstanding = %.0f", financials.shares_outstanding)
        raise CalculationError("Shares outstanding must be positive.")

    intrinsic_value_per_share = equity_value_model / financials.shares_outstanding
    logger.info(
        "[9] Intrinsic Value per Share = Equity / Shares = %.2f / %.0f = %.4f",
        equity_value_model,
        financials.shares_outstanding,
        intrinsic_value_per_share,
    )

    logger.info("=== DCF ENGINE END for %s ===", financials.ticker)

    return DCFResult(
        wacc=wacc,
        cost_of_equity=cost_of_equity,
        after_tax_cost_of_debt=after_tax_cost_of_debt,
        projected_fcfs=projected_fcfs,
        discount_factors=discount_factors,
        sum_discounted_fcf=sum_discounted_fcf,
        terminal_value=terminal_value,
        discounted_terminal_value=discounted_terminal_value,
        enterprise_value=enterprise_value,
        equity_value=equity_value_model,
        intrinsic_value_per_share=intrinsic_value_per_share,
    )
