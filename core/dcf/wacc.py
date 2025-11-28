from core.exceptions import CalculationError


def compute_cost_of_equity(risk_free_rate: float, beta: float, market_risk_premium: float) -> float:
    """
    CAPM: Re = Rf + beta * MRP
    """
    return risk_free_rate + beta * market_risk_premium


def compute_wacc(
    equity_value: float,
    debt_value: float,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float,
) -> tuple[float, float]:
    """
    WACC = (E / (E + D)) * Re + (D / (E + D)) * Rd * (1 - T)
    """
    total_value = equity_value + debt_value
    if total_value <= 0:
        raise CalculationError("Total capital (E + D) must be positive to compute WACC.")

    weight_equity = equity_value / total_value
    weight_debt = debt_value / total_value

    after_tax_cost_of_debt = cost_of_debt * (1.0 - tax_rate)

    wacc = weight_equity * cost_of_equity + weight_debt * after_tax_cost_of_debt
    return wacc, after_tax_cost_of_debt
