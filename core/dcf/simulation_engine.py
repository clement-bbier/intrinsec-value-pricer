import logging
import numpy as np
from typing import List

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.dcf.basic_engine import run_dcf_simple_fcff
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)

NUM_SIMULATIONS = 5000


def run_dcf_advanced_simulation(
        financials: CompanyFinancials,
        params: DCFParameters,
) -> DCFResult:
    """
    Méthode 3 – Simulation Monte Carlo Multivariée.
    Utilise une matrice de covariance pour lier Beta (Risque) et Croissance.
    """
    logger.info("=== [DCF_SIMULATION] Starting Multivariate Monte Carlo ===")
    np.random.seed(42)

    # 1. Définition des paramètres moyens et volatilités
    mu_beta = financials.beta
    sigma_beta = params.beta_volatility * abs(mu_beta)  # 10-20% du beta

    mu_growth = params.fcf_growth_rate
    sigma_growth = params.growth_volatility  # ex: 1% absolue

    # 2. Matrice de Corrélation
    # Hypothèse Financière : Corrélation Négative.
    # Si Beta monte (Risque up), la croissance soutenable tend à baisser ou être plus risquée.
    rho = -0.4  # Coefficient de corrélation (ajustable)

    # 3. Construction Matrice de Covariance
    # Cov(X,Y) = rho * sigma_X * sigma_Y
    covariance = rho * sigma_beta * sigma_growth

    cov_matrix = [
        [sigma_beta ** 2, covariance],
        [covariance, sigma_growth ** 2]
    ]
    mean_vector = [mu_beta, mu_growth]

    # 4. Tirage Multivarié (Loi Normale Liée)
    # draws est une matrice [NUM_SIMULATIONS, 2]
    draws = np.random.multivariate_normal(mean_vector, cov_matrix, NUM_SIMULATIONS)

    betas = draws[:, 0]
    growths = draws[:, 1]

    # Tirage indépendant pour g_inf (moins d'impact direct corrélé)
    perpetual_growths = np.random.normal(
        loc=params.perpetual_growth_rate,
        scale=params.terminal_growth_volatility,
        size=NUM_SIMULATIONS
    )

    simulated_values: List[float] = []
    valid_runs = 0

    # 5. Boucle de Simulation
    for i in range(NUM_SIMULATIONS):
        # Clip pour rester réaliste
        g_inf_i = max(0.0, min(0.04, perpetual_growths[i]))
        g_i = growths[i]  # Peut être négatif, c'est ok pour une crise

        params_i = DCFParameters(
            risk_free_rate=params.risk_free_rate,
            market_risk_premium=params.market_risk_premium,
            cost_of_debt=params.cost_of_debt,
            tax_rate=params.tax_rate,
            fcf_growth_rate=g_i,
            perpetual_growth_rate=g_inf_i,
            projection_years=params.projection_years
        )

        original_beta = financials.beta
        financials.beta = betas[i]  # Injection Beta simulé

        try:
            result_i = run_dcf_simple_fcff(financials, params_i)
            simulated_values.append(result_i.intrinsic_value_per_share)
            valid_runs += 1
        except CalculationError:
            pass
        finally:
            financials.beta = original_beta

    # 6. Stats & Sortie
    simulated_values_np = np.array(simulated_values)
    final_result = run_dcf_simple_fcff(financials, params)

    if valid_runs > 0:
        final_result.simulation_results = list(simulated_values_np)
        # On peut logguer les centiles ici
        p10 = np.percentile(simulated_values_np, 10)
        p90 = np.percentile(simulated_values_np, 90)
        logger.info("[DCF_SIMULATION] P10=%.2f | P90=%.2f", p10, p90)
    else:
        logger.error("Simulation failed completely.")

    return final_result