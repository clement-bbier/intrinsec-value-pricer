from typing import List

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.exceptions import CalculationError
from core.dcf.fcf import project_fcfs
from core.dcf.wacc import compute_cost_of_equity, compute_wacc


def _compute_discount_factors(rate: float, years: int) -> List[float]:
    """
    Returns [ (1+rate)^1, (1+rate)^2, ..., (1+rate)^years ]
    """
    return [(1.0 + rate) ** t for t in range(1, years + 1)]


def run_dcf(financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
    """
    Main DCF engine: projects FCFF, computes WACC, terminal value and IV per share.
    """
    # 1) Equity value (using current market capitalization)
    equity_value_market = financials.current_price * financials.shares_outstanding

    # 2) Cost of equity (CAPM)
    cost_of_equity = compute_cost_of_equity(
        risk_free_rate=params.risk_free_rate,
        beta=financials.beta,
        market_risk_premium=params.market_risk_premium,
    )

    # 3) WACC
    wacc, after_tax_cost_of_debt = compute_wacc(
        equity_value=equity_value_market,
        debt_value=financials.total_debt,
        cost_of_equity=cost_of_equity,
        cost_of_debt=params.cost_of_debt,
        tax_rate=params.tax_rate,
    )

    if wacc <= params.perpetual_growth_rate:
        raise CalculationError(
            f"WACC ({wacc:.4f}) must be strictly greater than perpetual growth "
            f"rate g ({params.perpetual_growth_rate:.4f})."
        )

    # 4) Project FCFs
    projected_fcfs = project_fcfs(
        fcf_last=financials.fcf_last,
        years=params.projection_years,
        growth_rate=params.fcf_growth_rate,
    )

    if not projected_fcfs:
        raise CalculationError("No projected FCFs – projection_years must be > 0.")

    # 5) Discount factors and discounted cash flows
    discount_factors = _compute_discount_factors(wacc, params.projection_years)
    discounted_fcfs = [fcf / df for fcf, df in zip(projected_fcfs, discount_factors)]
    sum_discounted_fcf = sum(discounted_fcfs)

    # 6) Terminal value (Gordon–Shapiro)
    last_fcf = projected_fcfs[-1]
    fcf_terminal = last_fcf * (1.0 + params.perpetual_growth_rate)
    terminal_value = fcf_terminal / (wacc - params.perpetual_growth_rate)

    discounted_terminal_value = terminal_value / discount_factors[-1]

    # 7) Enterprise value
    enterprise_value = sum_discounted_fcf + discounted_terminal_value

    # 8) Equity value from enterprise value
    equity_value_model = enterprise_value - financials.total_debt + financials.cash_and_equivalents

    # 9) Intrinsic value per share
    if financials.shares_outstanding <= 0:
        raise CalculationError("Shares outstanding must be positive to compute intrinsic value per share.")

    intrinsic_value_per_share = equity_value_model / financials.shares_outstanding

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
