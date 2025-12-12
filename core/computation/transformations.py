import logging

logger = logging.getLogger(__name__)


def unlever_beta(
        beta_levered: float,
        tax_rate: float,
        debt: float,
        equity: float
) -> float:
    """
    Désendette le Beta (Hamada Equation).
    Beta_u = Beta_l / (1 + (1 - t) * (D / E))
    """
    if equity == 0:
        return beta_levered

    d_e_ratio = debt / equity
    return beta_levered / (1.0 + (1.0 - tax_rate) * d_e_ratio)


def relever_beta(
        beta_unlevered: float,
        tax_rate: float,
        target_debt_weight: float,
        target_equity_weight: float
) -> float:
    """
    Réendette le Beta selon une structure cible.
    Beta_l = Beta_u * (1 + (1 - t) * (D / E))
    """
    if target_equity_weight == 0:
        return beta_unlevered  # Cas extrême, non pertinent pour CAPM

    d_e_ratio = target_debt_weight / target_equity_weight
    return beta_unlevered * (1.0 + (1.0 - tax_rate) * d_e_ratio)


def calculate_total_debt_from_net(net_debt: float, cash: float) -> float:
    """
    Reconstruit la dette brute (Total Debt) nécessaire au WACC.
    Total Debt = Net Debt + Cash
    """
    # Si Net Debt est négative (Cash > Dette), Total Debt peut être 0 ou positive.
    # Mathématiquement : Dette = Net + Cash.
    # On applique un floor à 0 car une dette comptable ne peut être négative.
    return max(0.0, net_debt + cash)