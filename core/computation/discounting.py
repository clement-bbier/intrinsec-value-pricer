import logging
from typing import Tuple, List
from dataclasses import dataclass

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters

logger = logging.getLogger(__name__)

# ==============================================================================
# TABLES DE SPREAD DAMODARAN (Mise à jour 2024/2025)
# ==============================================================================

SPREADS_LARGE_CAP = [
    (8.5, 0.0069), (6.5, 0.0085), (5.5, 0.0107), (4.25, 0.0118),
    (3.0, 0.0133), (2.5, 0.0171), (2.25, 0.0213), (2.0, 0.0277),
    (1.75, 0.0384), (1.5, 0.0490), (1.25, 0.0597), (0.8, 0.0756),
    (0.65, 0.1060), (0.2, 0.1500), (-999, 0.2000)
]

SPREADS_SMALL_MID_CAP = [
    (12.5, 0.0069), (9.5, 0.0085), (7.5, 0.0107), (6.0, 0.0118),
    (4.5, 0.0133), (4.0, 0.0171), (3.5, 0.0213), (3.0, 0.0277),
    (2.5, 0.0384), (2.0, 0.0490), (1.5, 0.0597), (1.25, 0.0756),
    (0.8, 0.1060), (0.5, 0.1500), (-999, 0.2000)
]


@dataclass
class FullWACCContext:
    cost_of_equity: float
    cost_of_debt_pre_tax: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    wacc: float
    method_used: str


# ==============================================================================
# 1. COÛT DU CAPITAL (WACC) & COMPOSANTES
# ==============================================================================

def calculate_cost_of_equity(
        risk_free_rate: float,
        beta: float,
        market_risk_premium: float
) -> float:
    """Calcule le Ke via le modèle CAPM."""
    return risk_free_rate + (beta * market_risk_premium)


def calculate_synthetic_cost_of_debt(
        risk_free_rate: float,
        ebit: float,
        interest_expense: float,
        equity_value_market: float
) -> float:
    """Détermine le Rd synthétique basé sur l'ICR et la taille de la capitalisation."""
    if interest_expense <= 0:
        return risk_free_rate + 0.0107  # Spread par défaut (AAA/AA)

    icr = ebit / interest_expense
    is_large_cap = equity_value_market >= 5_000_000_000
    table = SPREADS_LARGE_CAP if is_large_cap else SPREADS_SMALL_MID_CAP

    selected_spread = 0.20
    for threshold, spread in table:
        if icr >= threshold:
            selected_spread = spread
            break

    return risk_free_rate + selected_spread


def calculate_wacc_full_context(
        financials: CompanyFinancials,
        params: DCFParameters
) -> FullWACCContext:
    """
    Calcule le WACC avec gestion des overrides et validation des poids.
    """
    # 1. COÛT DES FONDS PROPRES (Ke)
    if params.manual_cost_of_equity is not None:
        cost_equity = params.manual_cost_of_equity
    else:
        cost_equity = calculate_cost_of_equity(
            params.risk_free_rate, financials.beta, params.market_risk_premium
        )

    # 2. COÛT DE LA DETTE (Kd net)
    cost_debt_pre_tax = params.cost_of_debt
    cost_debt_after_tax = cost_debt_pre_tax * (1.0 - params.tax_rate)

    # 3. PONDÉRATIONS (Market Value vs Target)
    market_equity_value = financials.current_price * financials.shares_outstanding

    if params.target_equity_weight > 0.0 and params.target_debt_weight > 0.0:
        # Normalisation de sécurité
        total_w = params.target_equity_weight + params.target_debt_weight
        weight_equity = params.target_equity_weight / total_w
        weight_debt = params.target_debt_weight / total_w
        method_used = "TARGET"
    else:
        # Poids de marché
        total_debt = financials.total_debt
        total_capital = market_equity_value + total_debt

        if total_capital <= 0:
            # Fallback de secours si données manquantes
            weight_equity = 1.0
            weight_debt = 0.0
            method_used = "FORCED_EQUITY"
        else:
            weight_equity = market_equity_value / total_capital
            weight_debt = total_debt / total_capital
            method_used = "MARKET"

    # 4. WACC
    wacc = (weight_equity * cost_equity) + (weight_debt * cost_debt_after_tax)

    # Invariant de sécurité (WACC ne peut être négatif ou nul en nominal)
    if wacc <= 0.001:
        # On ne bloque pas si c'est mathématiquement "juste" (ex: taux négatifs),
        # mais pour un DCF c'est suspect.
        pass

    return FullWACCContext(
        cost_of_equity=cost_equity,
        cost_of_debt_pre_tax=cost_debt_pre_tax,
        cost_of_debt_after_tax=cost_debt_after_tax,
        weight_equity=weight_equity,
        weight_debt=weight_debt,
        wacc=wacc,
        method_used=method_used
    )


# ==============================================================================
# 2. ACTUALISATION & VALEUR TERMINALE
# ==============================================================================

def calculate_discount_factors(wacc: float, years: int) -> List[float]:
    """Retourne la liste des facteurs d'actualisation (1 / (1+r)^t)."""
    return [1.0 / ((1.0 + wacc) ** t) for t in range(1, years + 1)]


def calculate_terminal_value(final_fcf: float, wacc: float, g_perp: float) -> float:
    """
    Calcule la valeur terminale (Gordon Shapiro).
    Invariant BLOQUANT : WACC > g_perp.
    """
    if wacc <= g_perp:
        raise CalculationError(
            f"Convergence impossible : WACC ({wacc:.2%}) <= Croissance Terminale ({g_perp:.2%}). "
            "La valeur terminale est infinie mathématiquement."
        )

    # TV = FCF_n * (1+g) / (WACC - g)
    return (final_fcf * (1.0 + g_perp)) / (wacc - g_perp)


def calculate_equity_value_bridge(enterprise_value: float, total_debt: float, cash: float) -> float:
    """Bridge EV -> Equity Value."""
    return enterprise_value - total_debt + cash