"""
core/valuation/strategies/monte_carlo.py

EXTENSION PROBABILISTE — MONTE CARLO DCF
Version : V1 Normative (Extension)

Références académiques :
- CFA Institute – Monte Carlo Simulation in Valuation
- Damodaran – Simulation & Uncertainty in DCF

Règle fondamentale :
- Monte Carlo n'est PAS une méthode de valorisation
- Il s’applique UNIQUEMENT à un DCF déterministe valide
- Le résultat pivot reste un scénario déterministe (P50)

Cette classe ne doit JAMAIS apparaître dans ValuationMode.
"""

import logging
import numpy as np
from typing import List, Dict

from dataclasses import replace

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult
)

from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_standard import StandardFCFFStrategy

from core.computation.statistics import (
    generate_multivariate_samples,
    generate_independent_samples
)

logger = logging.getLogger(__name__)


class MonteCarloDCFStrategy(ValuationStrategy):
    """
    Extension Monte Carlo appliquée à un DCF FCFF déterministe.

    Principe :
    1. Génération de scénarios sur les paramètres incertains
    2. Exécution répétée du DCF déterministe
    3. Analyse statistique de la distribution des valeurs

    ⚠️ Le modèle déterministe reste la référence centrale.
    """

    academic_reference = "CFA Institute"
    economic_domain = "Risk analysis / Uncertainty quantification"
    financial_invariants = [
        "Deterministic DCF required",
        "WACC > g_terminal in majority of runs",
        "Sufficient number of valid simulations"
    ]

    DEFAULT_SIMULATIONS = 2000
    MIN_VALID_RATIO = 0.50  # 50 % minimum de runs valides

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Applique une simulation Monte Carlo autour d’un DCF standard.

        Résultat :
        - La valeur intrinsèque retournée = médiane (P50)
        - Les quantiles servent à l’analyse de risque
        """

        num_simulations = (
            params.num_simulations
            if params.num_simulations
            else self.DEFAULT_SIMULATIONS
        )

        logger.info(
            "[Monte Carlo] Extension enabled | ticker=%s | simulations=%d",
            financials.ticker,
            num_simulations
        )

        # ====================================================
        # 1. PARAMÉTRAGE DES INCERTITUDES
        # ====================================================

        sigma_beta = params.beta_volatility if params.beta_volatility > 0 else 0.10
        sigma_growth = params.growth_volatility if params.growth_volatility > 0 else 0.015
        sigma_terminal = (
            params.terminal_growth_volatility
            if params.terminal_growth_volatility > 0
            else 0.005
        )

        rho_beta_growth = -0.30  # corrélation économique standard

        # ====================================================
        # 2. GÉNÉRATION DES SCÉNARIOS
        # ====================================================

        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=sigma_beta,
            mu_growth=params.fcf_growth_rate,
            sigma_growth=sigma_growth,
            rho=rho_beta_growth,
            num_simulations=num_simulations
        )

        terminal_growths = generate_independent_samples(
            mean=params.perpetual_growth_rate,
            sigma=sigma_terminal,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=0.04  # borne macro-économique réaliste
        )

        # ====================================================
        # 3. BOUCLE DE SIMULATION
        # ====================================================

        base_strategy = StandardFCFFStrategy()
        simulated_values: List[float] = []
        valid_runs = 0

        for i in range(num_simulations):
            sim_financials = replace(financials, beta=betas[i])
            sim_params = replace(
                params,
                fcf_growth_rate=growths[i],
                perpetual_growth_rate=terminal_growths[i]
            )

            try:
                res = base_strategy.execute(sim_financials, sim_params)
                iv = res.intrinsic_value_per_share

                # Filtrage anti-explosion
                if 0.0 < iv < 50_000:
                    simulated_values.append(iv)
                    valid_runs += 1

            except CalculationError:
                continue
            except Exception:
                continue

        valid_ratio = valid_runs / num_simulations

        if valid_ratio < self.MIN_VALID_RATIO:
            logger.warning(
                "[Monte Carlo] Instabilité élevée : %.1f%% de runs valides",
                valid_ratio * 100
            )

        # ====================================================
        # 4. SCÉNARIO CENTRAL DÉTERMINISTE (PIVOT)
        # ====================================================

        final_result = base_strategy.execute(financials, params)

        # ====================================================
        # 5. ANALYSE STATISTIQUE
        # ====================================================

        if simulated_values:
            arr = np.array(simulated_values)

            p10 = float(np.percentile(arr, 10))
            p50 = float(np.percentile(arr, 50))
            p90 = float(np.percentile(arr, 90))
            mean = float(np.mean(arr))

            # Alignement de la valeur centrale sur la médiane
            final_result.intrinsic_value_per_share = p50

            final_result.simulation_results = simulated_values
            final_result.quantiles = {
                "P10": p10,
                "P50": p50,
                "P90": p90,
                "Mean": mean
            }

            if final_result.market_price > 0:
                final_result.upside_pct = (
                    final_result.intrinsic_value_per_share
                    / final_result.market_price
                ) - 1.0

        return final_result
