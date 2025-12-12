import logging
import numpy as np
from dataclasses import replace
from typing import List, Dict

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_simple import SimpleFCFFStrategy
from core.computation.statistics import generate_multivariate_samples, generate_independent_samples

logger = logging.getLogger(__name__)


class MonteCarloDCFStrategy(ValuationStrategy):
    """
    STRATÉGIE 3 : DCF PROBABILISTE (MONTE CARLO).

    Implémentation autonome :
    1. Génère N scénarios (Beta, Croissance, Terminal).
    2. Exécute N fois le moteur déterministe (SimpleFCFFStrategy) en mémoire.
    3. Agrège les résultats (Distribution et Quantiles).
    """

    DEFAULT_SIMULATIONS = 5000

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        # Priorité : Paramètre d'appel > Défaut de la classe
        num_simulations = params.num_simulations or self.DEFAULT_SIMULATIONS

        logger.info(
            "[Strategy] Executing MonteCarloDCFStrategy | ticker=%s | sims=%s",
            financials.ticker,
            num_simulations,
        )

        # 1. Préparation des paramètres statistiques
        beta_mu = float(financials.beta)
        sigma_beta = float(params.beta_volatility) * abs(beta_mu)

        betas, growths = generate_multivariate_samples(
            mu_beta=beta_mu,
            sigma_beta=sigma_beta,
            mu_growth=float(params.fcf_growth_rate),
            sigma_growth=float(params.growth_volatility),
            rho=-0.4,
            num_simulations=num_simulations,
        )

        g_inf_draws = generate_independent_samples(
            mean=float(params.perpetual_growth_rate),
            sigma=float(params.terminal_growth_volatility),
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=0.04,
        )

        # 2. Boucle de Simulation
        simulated_ivs: List[float] = []
        base_strategy = SimpleFCFFStrategy()
        valid_runs = 0

        # Récupération d'un état "propre" pour éviter les effets de bord
        original_beta = float(financials.beta)

        for i in range(num_simulations):
            # Immutabilité : Création d'une copie avec le Beta simulé
            sim_financials = replace(financials, beta=float(betas[i]))

            # Paramètres simulés
            sim_params = replace(params)
            sim_params.fcf_growth_rate = float(growths[i])
            sim_params.perpetual_growth_rate = float(g_inf_draws[i])
            sim_params.normalize_weights()

            try:
                # Exécution sur la copie (moteur SimpleFCFFStrategy)
                result_i = base_strategy.execute(sim_financials, sim_params)
                val = float(result_i.intrinsic_value_per_share)

                # Filtrage technique
                if val > 0 and val < 1_000_000:
                    simulated_ivs.append(val)
                    valid_runs += 1
            except CalculationError:
                continue
            except Exception:
                continue

        if valid_runs < num_simulations * 0.5:
            logger.warning("Monte Carlo instability: < 50% valid runs.")

        # 3. Calcul du Résultat "Pivot" (P50 ou Central)
        # On utilise les paramètres originaux pour le run principal
        final_result = base_strategy.execute(financials, params)

        # 4. Enrichissement
        final_result.simulation_results = simulated_ivs

        if simulated_ivs:
            arr = np.array(simulated_ivs)
            final_result.quantiles = {
                "P10": float(np.percentile(arr, 10)),
                "P50": float(np.percentile(arr, 50)),
                "P90": float(np.percentile(arr, 90)),
                "Mean": float(np.mean(arr))
            }
            # L'alignement de la valeur intrinsèque sur la médiane est une convention standard en MC
            final_result.intrinsic_value_per_share = final_result.quantiles["P50"]

        logger.info(
            "[MonteCarlo] Completed | ticker=%s | valid=%s/%s | P50=%.2f",
            financials.ticker,
            valid_runs,
            num_simulations,
            final_result.intrinsic_value_per_share
        )
        return final_result