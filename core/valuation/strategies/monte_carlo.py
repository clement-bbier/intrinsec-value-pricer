"""
core/valuation/strategies/monte_carlo.py
EXTENSION PROBABILISTE — VERSION V5.2 (Audit-Grade)
Rôle : Analyse de risque stochastique avec isolation et pivot déterministe.
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
    """
    Wrapper Monte Carlo standardisé.
    Gère la simulation de scénarios et l'agrégation statistique des résultats.
    Aligné sur le registre technique V6.2.
    """

    DEFAULT_SIMULATIONS = 5000
    MIN_VALID_RATIO = 0.50

    def __init__(self, strategy_cls: Type[ValuationStrategy]):
        super().__init__()
        self.strategy_cls = strategy_cls

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        """Exécution de la simulation avec traçabilité complète et point pivot."""
        num_simulations = params.num_simulations or self.DEFAULT_SIMULATIONS

        # ======================================================================
        # 1. CONFIGURATION (ID: MC_CONFIG)
        # ======================================================================
        # On enregistre les paramètres d'incertitude injectés
        self.add_step(
            step_key="MC_CONFIG",
            result=float(num_simulations),
            numerical_substitution=(
                f"N = {num_simulations} itérations | "
                f"Beta_vol = {params.beta_volatility or 0.10:.2f} | "
                f"Growth_vol = {params.growth_volatility or 0.015:.2f}"
            )
        )

        # ======================================================================
        # 2. GÉNÉRATION DES VARIABLES (ID: MC_SAMPLING)
        # ======================================================================
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=params.beta_volatility or 0.10,
            mu_growth=params.fcf_growth_rate,
            sigma_growth=params.growth_volatility or 0.015,
            rho=-0.30, # Corrélation négative structurelle
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
            numerical_substitution=f"Génération de {num_simulations} vecteurs stochastiques"
        )

        # ======================================================================
        # --- BOUCLE DE SIMULATION (MOTEUR SILENCIEUX) ---
        # ======================================================================
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

                # Filtrage technique des outliers extrêmes
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
            numerical_substitution=f"{len(simulated_values)} / {num_simulations} scénarios convergents"
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            raise CalculationError(f"Instabilité critique : {valid_ratio:.1%} de réussite.")

        # ======================================================================
        # 4. SCÉNARIO PIVOT (ID: MC_PIVOT) - RÉFÉRENCE DÉTERMINISTE
        # ======================================================================
        # On exécute le modèle central (sans hasard) pour l'audit calcul
        ref_strategy = self.strategy_cls(glass_box_enabled=True)
        final_result = ref_strategy.execute(financials, params)

        self.add_step(
            step_key="MC_PIVOT",
            result=final_result.intrinsic_value_per_share,
            numerical_substitution="Valeur centrale calculée sans incertitude"
        )

        # ======================================================================
        # 5. SYNTHÈSE DE LA DISTRIBUTION (ID: MC_MEDIAN)
        # ======================================================================
        p50 = float(np.percentile(simulated_values, 50))

        # Injection des statistiques dans l'objet de résultat final
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
            numerical_substitution=f"Médiane retenue sur {len(simulated_values)} points"
        )

        # FUSION DES TRACES : Core Logic (1-6) + Monte Carlo (7-11)
        # Indispensable pour l'isolation dans ui_kpis.py
        final_result.calculation_trace = final_result.calculation_trace + self.calculation_trace

        return final_result