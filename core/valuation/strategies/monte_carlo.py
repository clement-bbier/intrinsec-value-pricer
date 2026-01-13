"""
core/valuation/strategies/monte_carlo.py
MOTEUR STOCHASTIQUE — VERSION V8.3
Rôle :  Simulation multivariée avec garantie de convergence et transparence d'audit.
Architecture : Écrêtage économique (Sanity Clamping) et paradigme "None = Auto".
"""

from __future__ import annotations

import logging
from typing import List, Type

import numpy as np

from core.computation.financial_math import calculate_wacc
from core.computation.statistics import (
    generate_independent_samples,
    generate_multivariate_samples,
)
from core.exceptions import (
    CalculationError,
    ModelDivergenceError,
    MonteCarloInstabilityError,
)
from core.models import CompanyFinancials, DCFParameters, ValuationResult
from core. valuation.strategies.abstract import ValuationStrategy

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources
)

logger = logging.getLogger(__name__)


class MonteCarloGenericStrategy(ValuationStrategy):
    """
    Wrapper Monte Carlo avec protection contre la divergence économique.

    Encapsule n'importe quelle stratégie de valorisation pour y ajouter
    une dimension stochastique (distribution des valeurs intrinsèques).
    """

    DEFAULT_SIMULATIONS = 5000
    MIN_VALID_RATIO = 0.20
    GROWTH_SAFETY_MARGIN = 0.015  # Marge de sécurité (1.5%) sous le WACC
    SENSITIVITY_SIMULATIONS = 1000
    MAX_IV_FILTER = 100_000.0
    DEFAULT_WACC_FALLBACK = 0.08

    def __init__(
        self,
        strategy_cls: Type[ValuationStrategy],
        glass_box_enabled:  bool = True
    ):
        super().__init__(glass_box_enabled=glass_box_enabled)
        self.strategy_cls = strategy_cls

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ValuationResult:
        """
        Exécute la simulation Monte Carlo sur la stratégie encapsulée.

        Args:
            financials: Données financières de l'entreprise
            params:  Paramètres de valorisation

        Returns:
            Résultat enrichi avec distribution stochastique et quantiles
        """
        num_simulations = params.num_simulations or self.DEFAULT_SIMULATIONS

        # =====================================================================
        # ÉTAPE 0 : SANITY CLAMPING (Écrêtage Économique)
        # =====================================================================
        base_wacc = self._compute_base_wacc(financials, params)
        g_raw, g_clamped, clamping_applied = self._apply_growth_clamping(params, base_wacc)

        if clamping_applied:
            params = params.model_copy(update={"fcf_growth_rate": g_clamped})
            logger.warning(
                "[Monte Carlo] Clamping appliqué sur g:  %s -> %s",
                f"{g_raw:.1%}",
                f"{g_clamped:.1%}"
            )

        # =====================================================================
        # ÉTAPE 1 : CONFIGURATION
        # =====================================================================
        clamping_note = StrategyInterpretations.MC_CLAMP_NOTE.format(g_raw=g_raw) if clamping_applied else ""

        self.add_step(
            step_key="MC_CONFIG",
            label=RegistryTexts.MC_INIT_L,
            theoretical_formula=r"\sigma_{\beta}, \sigma_g, \sigma_{g_n}, \rho",
            result=1.0,
            numerical_substitution=(
                f"Itérations :  {num_simulations} | "
                f"β: 𝒩({financials.beta:.2f}, {(params.beta_volatility or 0.10):.1%}) | "
                f"g: 𝒩({(params.fcf_growth_rate or 0.03):.1%}, {(params.growth_volatility or 0.015):.1%}) | "
                f"ρ(β,g): {params.correlation_beta_growth:.2f}"
            ),
            interpretation=StrategyInterpretations.MC_INIT.format(note=clamping_note)
        )

        # =====================================================================
        # ÉTAPE 2 : GÉNÉRATION DES TIRAGES
        # =====================================================================
        betas, growths, terminal_growths = self._generate_samples(
            financials, params, num_simulations, base_wacc
        )

        self.add_step(
            step_key="MC_SAMPLING",
            label=RegistryTexts.MC_SAMP_L,
            theoretical_formula=r"f(\beta, g, g_n) \to N_{sims}",
            result=float(num_simulations),
            numerical_substitution=StrategyInterpretations.MC_SAMPLING_SUB.format(count=num_simulations),
            interpretation=StrategyInterpretations.MC_SAMPLING_INTERP
        )

        # =====================================================================
        # ÉTAPE 3 : BOUCLE DE SIMULATION PRINCIPALE
        # =====================================================================
        worker = self.strategy_cls(glass_box_enabled=False)
        simulated_values = self._run_simulations(
            worker, financials, params, betas, growths, terminal_growths, num_simulations
        )

        # =====================================================================
        # ÉTAPE 4 : FILTRAGE ET CONVERGENCE
        # =====================================================================
        valid_count = len(simulated_values)
        valid_ratio = valid_count / num_simulations

        self.add_step(
            step_key="MC_FILTERING",
            label=RegistryTexts.MC_FILT_L,
            theoretical_formula=r"\frac{N_{valid}}{N_{total}}",
            result=valid_ratio,
            numerical_substitution=f"{valid_count} valides / {num_simulations} itérations",
            interpretation=StrategyInterpretations.MC_FILTERING
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            raise MonteCarloInstabilityError(valid_ratio, self.MIN_VALID_RATIO)

        # =====================================================================
        # ÉTAPE 5 : EXTRACTION DES QUANTILES
        # =====================================================================
        ref_strategy = self.strategy_cls(glass_box_enabled=True)
        final_result = ref_strategy.execute(financials, params)

        quantiles = self._compute_quantiles(simulated_values)
        p50 = quantiles["P50"]

        final_result.intrinsic_value_per_share = p50
        final_result.simulation_results = simulated_values
        final_result.quantiles = quantiles

        self.add_step(
            step_key="MC_MEDIAN",
            label=RegistryTexts.MC_MED_L,
            theoretical_formula=r"Median(IV_i)",
            result=p50,
            numerical_substitution=f"P50 = {p50:,.2f} {financials. currency}",
            interpretation=RegistryTexts.MC_MED_D
        )

        # =====================================================================
        # ÉTAPE 6 : ANALYSE DE SENSIBILITÉ (RHO)
        # =====================================================================
        self._run_sensitivity_analysis(worker, financials, params, final_result, p50)

        # =====================================================================
        # ÉTAPE 7 : STRESS TEST (BEAR CASE)
        # =====================================================================
        self._run_stress_test(worker, financials, params, final_result)

        # =====================================================================
        # ÉTAPE 8 : INJECTION DES MÉTRIQUES ET RETOUR
        # =====================================================================
        final_result.mc_valid_ratio = valid_ratio
        final_result.mc_clamping_applied = clamping_applied
        final_result.calculation_trace = self. calculation_trace + final_result.calculation_trace

        return final_result

    # ==========================================================================
    # MÉTHODES PRIVÉES
    # ==========================================================================

    def _compute_base_wacc(
        self,
        financials:  CompanyFinancials,
        params: DCFParameters
    ) -> float:
        """Calcule le WACC de base pour le clamping."""
        try:
            return calculate_wacc(financials, params).wacc
        except (ValueError, ZeroDivisionError, AttributeError):
            return self.DEFAULT_WACC_FALLBACK

    def _apply_growth_clamping(
        self,
        params: DCFParameters,
        base_wacc: float
    ) -> tuple[float, float, bool]:
        """
        Applique l'écrêtage économique sur le taux de croissance.

        Returns:
            Tuple (g_raw, g_clamped, clamping_applied)
        """
        g_raw = params.fcf_growth_rate if params.fcf_growth_rate is not None else 0.03
        g_clamped = min(g_raw, base_wacc - self. GROWTH_SAFETY_MARGIN)
        clamping_applied = g_clamped < g_raw

        return g_raw, g_clamped, clamping_applied

    def _generate_samples(
        self,
        financials: CompanyFinancials,
        params: DCFParameters,
        num_simulations: int,
        base_wacc:  float
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Génère les échantillons multivariés pour la simulation."""
        sig_b = params.beta_volatility if params.beta_volatility is not None else 0.10
        sig_g = params.growth_volatility if params.growth_volatility is not None else 0.015
        sig_gn = params.terminal_growth_volatility if params. terminal_growth_volatility is not None else 0.005

        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=sig_b,
            mu_growth=params.fcf_growth_rate if params.fcf_growth_rate is not None else 0.03,
            sigma_growth=sig_g,
            rho=params.correlation_beta_growth,
            num_simulations=num_simulations
        )

        terminal_growths = generate_independent_samples(
            mean=params.perpetual_growth_rate if params.perpetual_growth_rate is not None else 0.02,
            sigma=sig_gn,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=max(0.0, min(0.04, base_wacc - 0.01))
        )

        return betas, growths, terminal_growths

    def _run_simulations(
        self,
        worker: ValuationStrategy,
        financials: CompanyFinancials,
        params:  DCFParameters,
        betas: np.ndarray,
        growths: np.ndarray,
        terminal_growths: np.ndarray,
        num_simulations: int
    ) -> List[float]:
        """Exécute la boucle de simulation principale."""
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

                # Filtrage technique des valeurs aberrantes
                if 0.0 < iv < self.MAX_IV_FILTER:
                    simulated_values.append(iv)

            except (CalculationError, ModelDivergenceError, ValueError, ZeroDivisionError):
                # Scénarios invalides attendus dans une simulation MC
                continue

        return simulated_values

    def _compute_quantiles(self, simulated_values: List[float]) -> dict:
        """Calcule les quantiles de la distribution."""
        return {
            "P10": float(np.percentile(simulated_values, 10)),
            "P50": float(np. percentile(simulated_values, 50)),
            "P90": float(np.percentile(simulated_values, 90)),
            "Mean": float(np.mean(simulated_values)),
            "Std": float(np.std(simulated_values))
        }

    def _run_sensitivity_analysis(
        self,
        worker: ValuationStrategy,
        financials: CompanyFinancials,
        params: DCFParameters,
        final_result: ValuationResult,
        p50_base: float
    ) -> None:
        """Exécute l'analyse de sensibilité à la corrélation (rho)."""
        try:
            b_neutral, g_neutral = generate_multivariate_samples(
                mu_beta=financials.beta,
                sigma_beta=params. beta_volatility if params.beta_volatility is not None else 0.1,
                mu_growth=params.fcf_growth_rate if params.fcf_growth_rate is not None else 0.03,
                sigma_growth=params.growth_volatility if params. growth_volatility is not None else 0.02,
                rho=0.0,
                num_simulations=self. SENSITIVITY_SIMULATIONS
            )

            sims_neutral = []
            for i in range(self.SENSITIVITY_SIMULATIONS):
                try:
                    r_n = worker.execute(
                        financials. model_copy(update={"beta": float(b_neutral[i])}),
                        params.model_copy(update={"fcf_growth_rate":  float(g_neutral[i])})
                    )
                    if 0 < r_n.intrinsic_value_per_share < self.MAX_IV_FILTER:
                        sims_neutral. append(r_n.intrinsic_value_per_share)

                except (CalculationError, ModelDivergenceError, ValueError, ZeroDivisionError):
                    continue

            p50_neutral = float(np.percentile(sims_neutral, 50)) if sims_neutral else p50_base
            final_result. rho_sensitivity = {
                StrategyInterpretations.MC_SENS_NEUTRAL: p50_neutral,
                StrategyInterpretations.MC_SENS_BASE: p50_base
            }

            self.add_step(
                step_key="MC_SENSITIVITY",
                label=RegistryTexts.MC_SENS_L,
                theoretical_formula=r"\frac{\partial P50}{\partial \rho}",
                result=p50_neutral,
                numerical_substitution=f"P50(rho=0) = {p50_neutral:,.2f} vs Base = {p50_base:,.2f}",
                interpretation=StrategyInterpretations.MC_SENS_INTERP
            )

        except (ValueError, RuntimeError) as e:
            logger.error("Erreur calcul sensibilité Rho: %s", e)

    def _run_stress_test(
        self,
        worker: ValuationStrategy,
        financials: CompanyFinancials,
        params: DCFParameters,
        final_result: ValuationResult
    ) -> None:
        """Exécute le stress test (Bear Case déterministe)."""
        try:
            stress_params = params.model_copy(update={
                "fcf_growth_rate": 0.0,
                "perpetual_growth_rate": 0.01,
                "manual_beta": 1.50
            })
            stress_res = worker.execute(financials, stress_params)
            final_result.stress_test_value = stress_res.intrinsic_value_per_share

            self. add_step(
                step_key="MC_STRESS_TEST",
                label=RegistryTexts.MC_STRESS_L,
                theoretical_formula=r"f(g \to 0, \beta \to 1.5)",
                result=final_result. stress_test_value,
                numerical_substitution=StrategyInterpretations.MC_STRESS_SUB.format(
                    val=final_result.stress_test_value,
                    curr=financials.currency
                ),
                interpretation=StrategyInterpretations.MC_STRESS_INTERP
            )

        except (CalculationError, ModelDivergenceError, ValueError) as e:
            logger.error("Erreur calcul Stress Test: %s", e)