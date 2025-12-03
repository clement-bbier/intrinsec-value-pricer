import logging
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


def compute_cost_of_equity(risk_free_rate: float, beta: float, market_risk_premium: float) -> float:
    """
    CAPM:
        Re = Rf + beta * MRP
    Logs included for transparency.
    """
    re = risk_free_rate + beta * market_risk_premium

    logger.info(
        "[WACC] Cost of Equity (CAPM) = Rf + beta * MRP = %.4f + %.4f * %.4f = %.6f",
        risk_free_rate,
        beta,
        market_risk_premium,
        re,
    )

    return re


def compute_wacc(
    equity_value: float,
    debt_value: float,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float,
) -> tuple[float, float]:
    """
    Computes:
        after_tax_cost_of_debt = Rd * (1 - T)
        weight_equity = E / (E + D)
        weight_debt   = D / (E + D)

        WACC = weight_equity * Re + weight_debt * after_tax_cost_of_debt

    Includes granular logging for auditability.
    """
    total_value = equity_value + debt_value

    if total_value <= 0:
        logger.error(
            "[WACC] INVALID CAPITAL STRUCTURE: E + D = %.2f (must be > 0). E=%.2f | D=%.2f",
            total_value,
            equity_value,
            debt_value,
        )
        raise CalculationError("Total capital (E + D) must be positive to compute WACC.")

    # Compute weights
    weight_equity = equity_value / total_value
    weight_debt = debt_value / total_value

    logger.info(
        "[WACC] Capital Structure: E=%.2f | D=%.2f | Total=%.2f | We=%.4f | Wd=%.4f",
        equity_value,
        debt_value,
        total_value,
        weight_equity,
        weight_debt,
    )

    # After-tax cost of debt
    after_tax_cost_of_debt = cost_of_debt * (1.0 - tax_rate)
    logger.info(
        "[WACC] After-tax Cost of Debt = Rd * (1 - T) = %.4f * (1 - %.4f) = %.6f",
        cost_of_debt,
        tax_rate,
        after_tax_cost_of_debt,
    )

    # WACC formula
    wacc = weight_equity * cost_of_equity + weight_debt * after_tax_cost_of_debt

    logger.info(
        "[WACC] WACC = We * Re + Wd * Rd(1-T) = %.4f * %.6f + %.4f * %.6f = %.6f",
        weight_equity,
        cost_of_equity,
        weight_debt,
        after_tax_cost_of_debt,
        wacc,
    )

    return wacc, after_tax_cost_of_debt
