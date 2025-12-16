import logging
import numpy as np
from typing import List, Dict, Optional

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult, ValuationResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_standard import SimpleFCFFStrategy
from core.computation.statistics import generate_multivariate_samples, generate_independent_samples

logger = logging.getLogger(__name__)


class MonteCarloDCFStrategy(ValuationStrategy):
    """
    STRATÉGIE 3 : DCF PROBABILISTE (MONTE CARLO).

    Implémentation :
    1. Génère N scénarios de paramètres (Beta, Croissance, etc.).
    2. Exécute N fois le moteur déterministe (SimpleFCFFStrategy) en mémoire.
    3. Agrège les résultats (Distribution, Quantiles).
    """

    DEFAULT_SIMULATIONS = 2000

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        # Priorité : Paramètre d'appel > Défaut de la classe
        num_simulations = params.num_simulations or self.DEFAULT_SIMULATIONS

        logger.info(
            "[Strategy] Executing MonteCarloDCFStrategy | ticker=%s | sims=%s",
            financials.ticker,
            num_simulations,
        )

        # 1. Préparation des paramètres statistiques
        # On utilise les volatilités définies dans params ou des défauts
        sigma_beta = params.beta_volatility if params.beta_volatility > 0 else 0.10
        sigma_growth = params.growth_volatility if params.growth_volatility > 0 else 0.015

        # Corrélation négative standard entre Beta (Risque) et Croissance
        rho = -0.3

        # 2. Génération des Scénarios (Vectorisés)
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=sigma_beta,
            mu_growth=params.fcf_growth_rate,
            sigma_growth=sigma_growth,
            rho=rho,
            num_simulations=num_simulations
        )

        # Génération indépendante pour la Terminal Value (plus incertaine)
        term_growths = generate_independent_samples(
            mean=params.perpetual_growth_rate,
            sigma=params.terminal_growth_volatility if params.terminal_growth_volatility > 0 else 0.005,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=0.04  # Cap de sécurité économique
        )

        # 3. Boucle de Simulation
        base_strategy = SimpleFCFFStrategy()
        simulated_ivs: List[float] = []
        valid_runs = 0

        # On pré-calcule certains invariants pour optimiser (copie légère)
        # Mais ici, on doit réinstancier params à chaque tour ou le modifier.
        # Pour la performance pure, on pourrait vectoriser le moteur complet,
        # mais ici on boucle pour la clarté et la réutilisation de SimpleFCFF.

        for i in range(num_simulations):
            # Construction du contexte de simulation
            # On clone params pour ne pas modifier l'original
            # Note: DCFParameters est une dataclass, replace est propre
            from dataclasses import replace

            # WACC dynamique : le Beta change, donc le WACC change à chaque run
            # On laisse le moteur recalculer le WACC en interne via financial_math

            # On met à jour l'objet financials temporaire pour le Beta
            # (Attention : financials n'est pas frozen, on peut le modifier temporairement
            # mais il vaut mieux cloner si on veut être puriste. Ici on modifie une copie locale params)

            # Astuce : Le Beta est dans financials, pas params.
            # On crée une copie superficielle de financials pour ce run.
            sim_financials = replace(financials, beta=betas[i])

            sim_params = replace(
                params,
                fcf_growth_rate=growths[i],
                perpetual_growth_rate=term_growths[i]
            )

            try:
                # Exécution du moteur "Simple"
                res = base_strategy.execute(sim_financials, sim_params)
                val = res.intrinsic_value_per_share

                # Filtrage des valeurs aberrantes (ex: faillite simulée ou infini)
                if 0 < val < 50_000:  # Cap arbitraire anti-explosion
                    simulated_ivs.append(val)
                    valid_runs += 1

            except CalculationError:
                # Cas où WACC <= g_perp simulé
                continue
            except Exception:
                continue

        if valid_runs < num_simulations * 0.5:
            logger.warning("Monte Carlo instability: < 50% valid runs. Check input assumptions.")

        # 4. Calcul du Résultat "Pivot" (Scénario Central P50)
        # On ré-exécute une fois avec les paramètres centraux pour avoir les détails (FCF, WACC...)
        final_result = base_strategy.execute(financials, params)

        # 5. Enrichissement Statistique
        if simulated_ivs:
            arr = np.array(simulated_ivs)

            # On aligne la valeur intrinsèque finale sur la Médiane (P50) qui est plus robuste
            final_result.intrinsic_value_per_share = float(np.percentile(arr, 50))

            # On peuple les données de simulation pour l'UI
            final_result.simulation_results = simulated_ivs
            final_result.quantiles = {
                "P10": float(np.percentile(arr, 10)),
                "P50": float(np.percentile(arr, 50)),
                "P90": float(np.percentile(arr, 90)),
                "Mean": float(np.mean(arr))
            }

            # Recalcul de l'Upside basé sur le P50
            if final_result.market_price > 0:
                final_result.upside_pct = (final_result.intrinsic_value_per_share / final_result.market_price) - 1.0

        return final_result