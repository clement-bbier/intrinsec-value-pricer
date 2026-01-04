"""
core/valuation/strategies/monte_carlo.py
VERSION SIMPLIFIÉE — ALIGNÉE UI
"""

import logging
import numpy as np
from typing import List, Type
from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    TraceHypothesis
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.computation.statistics import (
    generate_multivariate_samples,
    generate_independent_samples
)

logger = logging.getLogger(__name__)

class MonteCarloGenericStrategy(ValuationStrategy):
    """Wrapper Monte Carlo piloté par IDs d'étapes."""

    def __init__(self, strategy_cls: Type[ValuationStrategy]):
        super().__init__()
        self.strategy_cls = strategy_cls

    DEFAULT_SIMULATIONS = 5000
    MIN_VALID_RATIO = 0.50

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        num_simulations = params.num_simulations or self.DEFAULT_SIMULATIONS

        # 1. CONFIG (ID: MC_CONFIG)
        self.add_step(
            step_key="MC_CONFIG",
            label="Configuration des Incertitudes",
            theoretical_formula=r"\sigma, \rho",
            result=1.0,
            numerical_substitution=f"Itérations : {num_simulations} × Modèle : {self.strategy_cls.__name__}",
            interpretation="Initialisation des paramètres stochastiques pour l'analyse de sensibilité."
        )

        # --- GÉNÉRATION ---
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=params.beta_volatility or 0.10,
            mu_growth=params.fcf_growth_rate,
            sigma_growth=params.growth_volatility or 0.015,
            rho=-0.30,
            num_simulations=num_simulations
        )
        terminal_growths = generate_independent_samples(
            mean=params.perpetual_growth_rate,
            sigma=params.terminal_growth_volatility or 0.005,
            num_simulations=num_simulations,
            clip_min=0.0, clip_max=0.04
        )

        # 2. SAMPLING (ID: MC_SAMPLING)
        self.add_step(
            step_key="MC_SAMPLING",
            label="Génération des Scénarios",
            theoretical_formula=r"Runs_{stochastiques}",
            result=float(num_simulations),
            numerical_substitution=f"Tirage de {num_simulations} vecteurs de probabilités.",
            interpretation="Création de scénarios basés sur la volatilité historique et les corrélations."
        )

        # --- BOUCLE DE SIMULATION ---
        worker = self.strategy_cls(glass_box_enabled=False)
        simulated_values = []
        for i in range(num_simulations):
            try:
                s_fin = financials.model_copy(update={"beta": float(betas[i])})
                s_par = params.model_copy(update={
                    "fcf_growth_rate": float(growths[i]),
                    "perpetual_growth_rate": float(terminal_growths[i])
                })
                res = worker.execute(s_fin, s_par)
                iv = res.intrinsic_value_per_share
                if -500.0 < iv < 50_000.0:
                    simulated_values.append(iv)
            except:
                continue

        # 3. FILTERING (ID: MC_FILTERING)
        valid_ratio = len(simulated_values) / num_simulations
        self.add_step(
            step_key="MC_FILTERING",
            label="Filtrage et Validation",
            theoretical_formula=r"N_{valid} / N_{total}",
            result=valid_ratio,
            numerical_substitution=f"{len(simulated_values)} / {num_simulations} valides",
            interpretation="Élimination des scénarios mathématiquement instables."
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            raise CalculationError(f"Instabilité critique : {valid_ratio:.1%} valides.")

        # 4. SYNTHÈSE & CALCUL RÉFÉRENCE
        ref_strategy = self.strategy_cls(glass_box_enabled=True)
        final_result = ref_strategy.execute(financials, params)

        p50 = float(np.percentile(simulated_values, 50))
        final_result.intrinsic_value_per_share = p50
        final_result.simulation_results = simulated_values
        final_result.quantiles = {
            "P10": float(np.percentile(simulated_values, 10)),
            "P50": p50,
            "P90": float(np.percentile(simulated_values, 90)),
            "Mean": float(np.mean(simulated_values)),
            "Std": float(np.std(simulated_values))
        }

        self.add_step(
            step_key="MC_MEDIAN",
            label="Synthèse de la Distribution",
            theoretical_formula=r"Median(simulations)",
            result=p50,
            numerical_substitution=f"Médiane retenue sur {len(simulated_values)} scénarios valides.",
            interpretation="Valeur intrinsèque stabilisée par la loi des grands nombres."
        )

        # On garde la fusion des traces : l'UI se chargera de les séparer par filtre
        final_result.calculation_trace = self.calculation_trace + final_result.calculation_trace
        return final_result