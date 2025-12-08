import logging
import numpy as np

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.dcf.fcf import project_fcfs
from core.dcf.wacc import compute_wacc, compute_cost_of_equity
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


def run_dcf_fundamental_fcff(
        financials: CompanyFinancials,
        params: DCFParameters,
) -> DCFResult:
    """
    Moteur de Calcul Méthode 2 : DCF Fondamental (Normatif).

    Philosophie :
    Au lieu de partir du dernier FCF connu (qui peut être exceptionnellement bon ou mauvais),
    ce moteur part d'un FCF 'Lissé' (fcf_fundamental_smoothed) calculé sur l'historique
    récent (Moyenne Pondérée Time-Anchored).

    C'est la méthode la plus robuste pour les investisseurs 'Value'.
    """
    ticker = financials.ticker
    logger.info("=== [FundamentalEngine] Starting Valuation for %s ===", ticker)

    # 1. Validation de l'Input Critique
    # Si le provider n'a pas pu calculer la moyenne pondérée (trop de données manquantes), on arrête.
    if financials.fcf_fundamental_smoothed is None:
        msg = "Impossible de calculer la Méthode 2 : Historique financier insuffisant (EBIT/BFR manquants)."
        logger.warning(msg)
        raise CalculationError(msg)

    fcff_start = financials.fcf_fundamental_smoothed
    logger.info("[FundamentalEngine] Point de départ Normatif (FCFF0) = %.2f", fcff_start)

    # 2. Calcul du Coût des Capitaux Propres (Ke)
    cost_of_equity = compute_cost_of_equity(
        risk_free_rate=params.risk_free_rate,
        beta=financials.beta,
        market_risk_premium=params.market_risk_premium
    )

    # 3. Calcul du WACC
    # On utilise le coût de la dette synthétique (Damodaran) déjà injecté dans params.cost_of_debt
    wacc, after_tax_cost_of_debt = compute_wacc(
        equity_value=financials.current_price * financials.shares_outstanding,
        debt_value=financials.total_debt,
        cost_of_equity=cost_of_equity,
        cost_of_debt=params.cost_of_debt,
        tax_rate=params.tax_rate
    )

    # Sécurité Mathématique
    if wacc <= params.perpetual_growth_rate:
        raise CalculationError(f"WACC ({wacc:.2%}) <= Croissance Terminale ({params.perpetual_growth_rate:.2%}).")

    # 4. Projection des Flux Futurs
    # On applique la croissance (Fade-Down ou Plateau) sur notre base normative solide
    projected_fcfs = project_fcfs(
        fcf_last=fcff_start,
        years=params.projection_years,
        growth_rate_start=params.fcf_growth_rate,
        growth_rate_terminal=params.perpetual_growth_rate,
        high_growth_years=params.high_growth_years  # <--- Activation du Turbo si nécessaire
    )

    # 5. Actualisation (Discounting)
    discount_factors = []
    discounted_fcfs = []

    for t, fcf in enumerate(projected_fcfs, start=1):
        factor = 1.0 / ((1.0 + wacc) ** t)
        discount_factors.append(factor)
        discounted_fcfs.append(fcf * factor)

    sum_discounted_fcf = sum(discounted_fcfs)

    # 6. Valeur Terminale
    fcf_final = projected_fcfs[-1]
    terminal_value = (fcf_final * (1.0 + params.perpetual_growth_rate)) / (wacc - params.perpetual_growth_rate)

    discount_factor_terminal = discount_factors[-1]
    discounted_terminal_value = terminal_value * discount_factor_terminal

    # 7. Valorisation de l'Entreprise (EV)
    enterprise_value = sum_discounted_fcf + discounted_terminal_value

    # 8. Equity Bridge (EV -> Equity Value)
    net_debt = financials.total_debt - financials.cash_and_equivalents
    equity_value = enterprise_value - net_debt

    # 9. Résultat par action
    if financials.shares_outstanding <= 0:
        raise CalculationError("Nombre d'actions invalide.")

    intrinsic_value_per_share = equity_value / financials.shares_outstanding

    logger.info(
        "[FundamentalEngine] Done. EV=%.2f | Equity=%.2f | IV/Share=%.2f",
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