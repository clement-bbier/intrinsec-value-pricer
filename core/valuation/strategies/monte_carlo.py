"""
core/valuation/strategies/monte_carlo.py
EXTENSION PROBABILISTE — VERSION V5.1 (Registry-Driven)
Rôle : Analyse de risque stochastique avec isolation de la trace d'audit.
"""

import logging
import numpy as np
from typing import List, Type
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, ValuationResult, TraceHypothesis
from core.valuation.strategies.abstract import ValuationStrategy
from core.computation.statistics import generate_multivariate_samples, generate_independent_samples

logger = logging.getLogger(__name__)

class MonteCarloGenericStrategy(ValuationStrategy):
    """
    Wrapper Monte Carlo standardisé.
    Gère la simulation de scénarios et l'agrégation statistique des résultats.
    """

    DEFAULT_SIMULATIONS = 5000
    MIN_VALID_RATIO = 0.50

    def __init__(self, strategy_cls: Type[ValuationStrategy]):
        super().__init__()
        self.strategy_cls = strategy_cls

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        """Exécution de la simulation avec traçabilité complète."""
        num_simulations = params.num_simulations or self.DEFAULT_SIMULATIONS

        # ======================================================================
        # 1. CONFIGURATION (ID: MC_CONFIG)
        # ======================================================================
        # On enregistre les paramètres d'entrée de la simulation
        self.add_step(
            step_key="MC_CONFIG",
            result=float(num_simulations),
            numerical_substitution=f"N = {num_simulations} itérations | Modèle: {self.strategy_cls.__name__}"
        )

        # ======================================================================
        # 2. GÉNÉRATION DES VARIABLES (ID: MC_SAMPLING)
        # ======================================================================
        # Création des vecteurs stochastiques pour Beta et Croissance
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=params.beta_volatility or 0.10,
            mu_growth=params.fcf_growth_rate,
            sigma_growth=params.growth_volatility or 0.015,
            rho=-0.30, # Corrélation négative standard
            num_simulations=num_simulations
        )
        terminal_growths = generate_independent_samples(
            mean=params.perpetual_growth_rate,
            sigma=params.terminal_growth_volatility or 0.005,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=0.04
        )

        self.add_step(
            step_key="MC_SAMPLING",
            result=float(num_simulations),
            numerical_substitution=(
                f"Beta (vol={params.beta_volatility or 0.10:.2f}) | "
                f"Growth (vol={params.growth_volatility or 0.015:.2f})"
            )
        )

        # ======================================================================
        # --- BOUCLE DE SIMULATION (MOTEUR SILENCIEUX) ---
        # ======================================================================
        # On utilise une instance "silencieuse" pour ne pas polluer la trace MC
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
                # Filtrage des valeurs aberrantes (outliers extrêmes)
                if -500.0 < iv < 50_000.0:
                    simulated_values.append(iv)
            except Exception:
                continue

        # ======================================================================
        # 3. FILTRAGE ET VALIDATION (ID: MC_FILTERING)
        # ======================================================================
        valid_ratio = len(simulated_values) / num_simulations
        self.add_step(
            step_key="MC_FILTERING",
            result=valid_ratio,
            numerical_substitution=f"{len(simulated_values)} / {num_simulations} scénarios valides"
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            raise CalculationError(f"Instabilité critique du modèle : {valid_ratio:.1%} valides.")

        # ======================================================================
        # 4. SCÉNARIO PIVOT ET MÉDIANE (ID: MC_MEDIAN)
        # ======================================================================
        # On exécute une fois avec la Glass Box pour obtenir la trace centrale
        ref_strategy = self.strategy_cls(glass_box_enabled=True)
        final_result = ref_strategy.execute(financials, params)

        p50 = float(np.percentile(simulated_values, 50))

        # Mise à jour des statistiques dans le résultat final
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
            result=p50,
            numerical_substitution=f"Médiane de la distribution ({len(simulated_values)} points)"
        )

        # Fusion des traces : On place les étapes MC après la logique métier
        # pour un indexage plus naturel dans l'UI (D'abord le calcul, ensuite le risque)
        final_result.calculation_trace = final_result.calculation_trace + self.calculation_trace

        return final_result