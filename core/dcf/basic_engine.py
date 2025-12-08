import logging
import numpy as np

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.dcf.fcf import project_fcfs
from core.dcf.wacc import compute_wacc, compute_cost_of_equity
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


def run_dcf_simple_fcff(
        financials: CompanyFinancials,
        params: DCFParameters,
) -> DCFResult:
    """
    Moteur de Calcul Méthode 1 : DCF Simple (Snapshot).

    Utilise le dernier FCFF connu (TTM) comme point de départ.
    Idéal pour une première estimation rapide ou pour des entreprises stables.
    """
    ticker = financials.ticker
    logger.info("=== [BasicEngine] Starting Valuation for %s ===", ticker)

    # 1. Calcul du Coût des Capitaux Propres (Ke) via CAPM
    cost_of_equity = compute_cost_of_equity(
        risk_free_rate=params.risk_free_rate,
        beta=financials.beta,
        market_risk_premium=params.market_risk_premium
    )

    # 2. Calcul du WACC
    # Note : Le cost_of_debt est déjà le taux synthétique (Damodaran) calculé par le Provider.
    wacc, after_tax_cost_of_debt = compute_wacc(
        equity_value=financials.current_price * financials.shares_outstanding,
        debt_value=financials.total_debt,
        cost_of_equity=cost_of_equity,
        cost_of_debt=params.cost_of_debt,
        tax_rate=params.tax_rate
    )

    # Sécurité Mathématique : WACC doit être > Croissance Terminale
    if wacc <= params.perpetual_growth_rate:
        msg = f"WACC ({wacc:.2%}) <= Perpetual Growth ({params.perpetual_growth_rate:.2%}). Valuation impossible (Infini)."
        logger.error(msg)
        raise CalculationError(msg)

    # 3. Projection des Flux Futurs (FCFF)
    # C'est ici qu'on active le mode "Multi-Stage" si params.high_growth_years > 0
    projected_fcfs = project_fcfs(
        fcf_last=financials.fcf_last,
        years=params.projection_years,
        growth_rate_start=params.fcf_growth_rate,
        growth_rate_terminal=params.perpetual_growth_rate,
        high_growth_years=params.high_growth_years  # <--- CONNEXION DU TURBO
    )

    # 4. Actualisation des Flux (Discounting)
    discount_factors = []
    discounted_fcfs = []

    for t, fcf in enumerate(projected_fcfs, start=1):
        # Facteur d'actualisation : 1 / (1 + WACC)^t
        factor = 1.0 / ((1.0 + wacc) ** t)
        discount_factors.append(factor)
        discounted_fcfs.append(fcf * factor)

    sum_discounted_fcf = sum(discounted_fcfs)

    # 5. Valeur Terminale (Gordon Shapiro)
    # TV = (FCF_final * (1 + g_inf)) / (WACC - g_inf)
    fcf_final = projected_fcfs[-1]
    terminal_value = (fcf_final * (1.0 + params.perpetual_growth_rate)) / (wacc - params.perpetual_growth_rate)

    # Actualisation de la Valeur Terminale
    discount_factor_terminal = discount_factors[-1]
    discounted_terminal_value = terminal_value * discount_factor_terminal

    # 6. Valeur d'Entreprise (Enterprise Value)
    enterprise_value = sum_discounted_fcf + discounted_terminal_value

    # 7. Passage à l'Equity Value (Equity Bridge)
    # Equity Value = EV - Dette Nette
    # Dette Nette = Dette Totale - Cash
    net_debt = financials.total_debt - financials.cash_and_equivalents
    equity_value = enterprise_value - net_debt

    # 8. Valeur Intrinsèque par Action
    if financials.shares_outstanding <= 0:
        raise CalculationError("Nombre d'actions invalide (<= 0).")

    intrinsic_value_per_share = equity_value / financials.shares_outstanding

    logger.info(
        "[BasicEngine] Done. EV=%.2f | Equity=%.2f | IV/Share=%.2f",
        enterprise_value, equity_value, intrinsic_value_per_share
    )

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
        equity_value=equity_value,
        intrinsic_value_per_share=intrinsic_value_per_share
    )