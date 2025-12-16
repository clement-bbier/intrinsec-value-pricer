import logging
from typing import List
from dataclasses import dataclass

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTES & TABLES DE RÉFÉRENCE (DAMODARAN)
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
class WACCBreakdown:
    cost_of_equity: float
    cost_of_debt_pre_tax: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    wacc: float
    method: str


# ==============================================================================
# 1. VALEUR TEMPORELLE DE L'ARGENT (TIME VALUE OF MONEY)
# ==============================================================================

def calculate_discount_factors(rate: float, years: int) -> List[float]:
    """
    Génère le vecteur d'actualisation : [1/(1+r)^1, ..., 1/(1+r)^N].
    """
    if rate <= -1.0:
        raise CalculationError(f"Taux d'actualisation invalide : {rate:.2%}")
    return [1.0 / ((1.0 + rate) ** t) for t in range(1, years + 1)]


def calculate_npv(flows: List[float], rate: float) -> float:
    """
    Calcule la Valeur Actuelle Nette (NPV) d'une série de flux futurs.
    NPV = Somme (Flow_t / (1+r)^t)
    """
    factors = calculate_discount_factors(rate, len(flows))
    return sum(f * d for f, d in zip(flows, factors))


def calculate_terminal_value_gordon(final_flow: float, rate: float, g_perp: float) -> float:
    """
    Modèle de Gordon-Shapiro pour la Valeur Terminale.
    TV = CF_n * (1+g) / (r-g)

    Invariant : rate (WACC/Ke) > g_perp
    """
    if rate <= g_perp:
        raise CalculationError(
            f"Convergence impossible : Taux ({rate:.2%}) <= Croissance ({g_perp:.2%}). "
            "La valeur terminale est mathématiquement infinie."
        )
    return (final_flow * (1.0 + g_perp)) / (rate - g_perp)


def calculate_equity_value_bridge(enterprise_value: float, total_debt: float, cash: float) -> float:
    """
    Passage de l'Enterprise Value (EV) à l'Equity Value.
    EqV = EV - Dette + Cash
    """
    return enterprise_value - total_debt + cash


# ==============================================================================
# 2. COÛT DU CAPITAL (WACC / CAPM)
# ==============================================================================

def calculate_cost_of_equity_capm(rf: float, beta: float, mrp: float) -> float:
    """Modèle CAPM : Ke = Rf + Beta * MRP"""
    return rf + (beta * mrp)


def calculate_synthetic_cost_of_debt(
        rf: float,
        ebit: float,
        interest_expense: float,
        market_cap: float
) -> float:
    """
    Estime le coût de la dette basé sur le ratio de couverture des intérêts (ICR).
    Utilise les tables de spreads de Damodaran.
    """
    if interest_expense <= 0:
        return rf + 0.0107  # Spread par défaut (AAA/AA safe)

    icr = ebit / interest_expense
    is_large = market_cap >= 5_000_000_000
    table = SPREADS_LARGE_CAP if is_large else SPREADS_SMALL_MID_CAP

    spread = 0.20  # Default junk/non-rated
    for threshold, val in table:
        if icr >= threshold:
            spread = val
            break

    return rf + spread


def calculate_wacc(financials: CompanyFinancials, params: DCFParameters) -> WACCBreakdown:
    """
    Calcul centralisé du WACC avec gestion des poids cibles vs marché.
    """
    # A. Cost of Equity (Ke)
    if params.manual_cost_of_equity is not None:
        ke = params.manual_cost_of_equity
    else:
        ke = calculate_cost_of_equity_capm(
            params.risk_free_rate,
            financials.beta,
            params.market_risk_premium
        )

    # B. Cost of Debt (Kd)
    kd_gross = params.cost_of_debt
    kd_net = kd_gross * (1.0 - params.tax_rate)

    # C. Weights (We, Wd)
    market_equity = financials.current_price * financials.shares_outstanding

    # Priorité aux poids cibles s'ils sont définis par l'expert
    if params.target_equity_weight > 0 and params.target_debt_weight > 0:
        we = params.target_equity_weight
        wd = params.target_debt_weight
        method = "TARGET"
    else:
        # Poids de marché
        total_cap = market_equity + financials.total_debt
        if total_cap <= 0:
            we, wd = 1.0, 0.0
            method = "FALLBACK_EQUITY"
        else:
            we = market_equity / total_cap
            wd = financials.total_debt / total_cap
            method = "MARKET"

    # D. WACC Formula
    wacc_raw = (we * ke) + (wd * kd_net)

    # Override optionnel
    if params.wacc_override is not None:
        wacc_final = params.wacc_override
        method = "MANUAL_OVERRIDE"
    else:
        wacc_final = wacc_raw

    return WACCBreakdown(
        cost_of_equity=ke,
        cost_of_debt_pre_tax=kd_gross,
        cost_of_debt_after_tax=kd_net,
        weight_equity=we,
        weight_debt=wd,
        wacc=wacc_final,
        method=method
    )