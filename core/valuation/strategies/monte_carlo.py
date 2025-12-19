"""
core/valuation/strategies/monte_carlo.py

EXTENSION PROBABILISTE — MONTE CARLO DCF
Version : V1.1 — Chapitre 4 conforme (Glass Box Extension)

Règles non négociables :
- Monte Carlo n’est PAS une méthode de valorisation
- Il s’applique uniquement à un DCF déterministe valide
- Le scénario pivot reste déterministe (P50)
"""

import logging
import numpy as np
from typing import List

from dataclasses import replace

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult,
    TraceHypothesis
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
    Extension Monte Carlo autour d’un DCF FCFF déterministe valide.
    """

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Risk analysis / Uncertainty quantification"
    financial_invariants = [
        "Deterministic DCF required",
        "WACC > g_terminal in majority of runs",
        "Sufficient number of valid simulations"
    ]

    DEFAULT_SIMULATIONS = 2000
    MIN_VALID_RATIO = 0.50

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:

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
        # 1. PARAMÉTRAGE DES INCERTITUDES (GLASS BOX)
        # ====================================================

        sigma_beta = params.beta_volatility if params.beta_volatility > 0 else 0.10
        sigma_growth = params.growth_volatility if params.growth_volatility > 0 else 0.015
        sigma_terminal = (
            params.terminal_growth_volatility
            if params.terminal_growth_volatility > 0
            else 0.005
        )

        rho_beta_growth = -0.30

        self.add_step(
            label="Paramétrage des incertitudes Monte Carlo",
            theoretical_formula="σ, ρ",
            hypotheses=[
                TraceHypothesis("Beta volatility", sigma_beta, "%"),
                TraceHypothesis("Growth volatility", sigma_growth, "%"),
                TraceHypothesis("Terminal growth volatility", sigma_terminal, "%"),
                TraceHypothesis("Correlation beta-growth", rho_beta_growth)
            ],
            numerical_substitution="Définition des paramètres statistiques",
            result=1.0,
            unit="configuration",
            interpretation=(
                "Définition des paramètres d’incertitude utilisés pour la "
                "simulation probabiliste autour du DCF déterministe."
            )
        )

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
            clip_max=0.04
        )

        self.add_step(
            label="Génération des scénarios Monte Carlo",
            theoretical_formula="Sampling multivarié",
            hypotheses=[
                TraceHypothesis("Number of simulations", num_simulations),
                TraceHypothesis("Distribution", "Normal / Correlated")
            ],
            numerical_substitution="Sampling stochastique",
            result=num_simulations,
            unit="runs",
            interpretation=(
                "Génération de scénarios aléatoires corrélés pour les "
                "paramètres clés du DCF."
            )
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

                if 0.0 < iv < 50_000:
                    simulated_values.append(iv)
                    valid_runs += 1

            except Exception:
                continue

        valid_ratio = valid_runs / num_simulations

        self.add_step(
            label="Filtrage des scénarios valides",
            theoretical_formula="Valid runs / Total runs",
            hypotheses=[
                TraceHypothesis("Valid runs", valid_runs),
                TraceHypothesis("Total runs", num_simulations)
            ],
            numerical_substitution=f"{valid_runs} / {num_simulations}",
            result=valid_ratio,
            unit="ratio",
            interpretation=(
                "Filtrage des scénarios instables ou économiquement aberrants."
            )
        )

        # ====================================================
        # 4. SCÉNARIO PIVOT DÉTERMINISTE
        # ====================================================

        final_result = base_strategy.execute(financials, params)

        self.add_step(
            label="Scénario pivot déterministe",
            theoretical_formula="DCF déterministe",
            hypotheses=[
                TraceHypothesis("Method", "Standard FCFF DCF"),
                TraceHypothesis("Role", "Reference scenario (P50)")
            ],
            numerical_substitution="Execution DCF sans stochasticité",
            result=final_result.intrinsic_value_per_share,
            unit=financials.currency,
            interpretation=(
                "Scénario central servant de référence pour la "
                "valorisation et l’analyse de risque."
            )
        )

        # ====================================================
        # 5. ANALYSE STATISTIQUE
        # ====================================================

        if simulated_values:
            arr = np.array(simulated_values)

            p10 = float(np.percentile(arr, 10))
            p50 = float(np.percentile(arr, 50))
            p90 = float(np.percentile(arr, 90))
            mean = float(np.mean(arr))

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

            self.add_step(
                label="Sélection de la valeur centrale (P50)",
                theoretical_formula="Median(simulations)",
                hypotheses=[
                    TraceHypothesis("P10", p10, financials.currency),
                    TraceHypothesis("P50", p50, financials.currency),
                    TraceHypothesis("P90", p90, financials.currency)
                ],
                numerical_substitution="P50 retenu comme valeur centrale",
                result=p50,
                unit=financials.currency,
                interpretation=(
                    "La médiane est retenue comme estimation robuste "
                    "face aux distributions asymétriques."
                )
            )

        final_result.calculation_trace.extend(self.trace)
        return final_result
