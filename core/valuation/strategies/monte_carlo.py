"""
core/valuation/strategies/monte_carlo.py
MOTEUR STOCHASTIQUE — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Simulation multivariée avec garantie de convergence et transparence d'audit.
Architecture : Écrêtage économique (Sanity Clamping) et segmentation des paramètres.
"""

from __future__ import annotations

import logging
from typing import List, Type, Any

import numpy as np
from numpy import ndarray, dtype, floating
from numpy._typing import _64Bit

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
from core.models import CompanyFinancials, DCFParameters, ValuationResult, TerminalValueMethod
from core.valuation.strategies.abstract import ValuationStrategy

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class MonteCarloGenericStrategy(ValuationStrategy):
    """
    Wrapper Monte Carlo avec protection contre la divergence économique.
    Désormais aligné sur la segmentation Rates / Growth / MonteCarloConfig.
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
        glass_box_enabled: bool = True
    ):
        super().__init__(glass_box_enabled=glass_box_enabled)
        self.strategy_cls = strategy_cls

    def execute(
            self,
            financials: CompanyFinancials,
            params: DCFParameters
    ) -> ValuationResult:
        """
        Exécute la simulation Monte Carlo avec prise en compte de l'incertitude Year 0.
        Standard Institutionnel : Simule les variations de Beta, Croissance et Flux de base.
        """
        # Accès au segment Monte Carlo
        mc_cfg = params.monte_carlo
        num_simulations = mc_cfg.num_simulations or self.DEFAULT_SIMULATIONS

        # =====================================================================
        # ÉTAPE 0 : SANITY CLAMPING (Écrêtage Économique)
        # =====================================================================
        base_wacc = self._compute_base_wacc(financials, params)
        g_raw, g_clamped, clamping_applied = self._apply_growth_clamping(params, base_wacc)

        if clamping_applied:
            # Mise à jour du segment growth pour la cohérence de la simulation
            params.growth.fcf_growth_rate = g_clamped
            logger.warning(
                "[Monte Carlo] Clamping appliqué sur g: %s -> %s",
                f"{g_raw:.1%}",
                f"{g_clamped:.1%}"
            )

        # =====================================================================
        # ÉTAPE 1 : CONFIGURATION (Résolution KeyError 'sig_y0')
        # =====================================================================
        clamping_note = StrategyInterpretations.MC_CLAMP_NOTE.format(g_raw=g_raw) if clamping_applied else ""

        # Rigueur : On définit la volatilité Year 0 (Standard Error) utilisée
        sig_y0_val = mc_cfg.base_flow_volatility if mc_cfg.base_flow_volatility is not None else 0.05

        self.add_step(
            step_key="MC_CONFIG",
            label=RegistryTexts.MC_INIT_L,
            # Ajout de sigma_Y0 dans la formule théorique pour la transparence
            theoretical_formula=r"\sigma_{\beta}, \sigma_g, \sigma_{g_n}, \sigma_{Y_0}, \rho",
            result=1.0,
            numerical_substitution=KPITexts.MC_CONFIG_SUB.format(
                sims=num_simulations,
                beta=financials.beta,
                sig_b=mc_cfg.beta_volatility or 0.10,
                g=params.growth.fcf_growth_rate or 0.03,
                sig_g=mc_cfg.growth_volatility or 0.015,
                sig_y0=sig_y0_val,  # <--- Correction du KeyError
                rho=mc_cfg.correlation_beta_growth
            ),
            interpretation=StrategyInterpretations.MC_INIT.format(note=clamping_note)
        )

        # =====================================================================
        # ÉTAPE 2 : GÉNÉRATION DES TIRAGES (Correction Unpacking)
        # =====================================================================
        # On dépaquette maintenant 4 éléments (vitesse, croissance, TV et flux base)
        betas, growths, terminal_growths, base_flows = self._generate_samples(
            financials, params, num_simulations, base_wacc
        )

        self.add_step(
            step_key="MC_SAMPLING",
            label=RegistryTexts.MC_SAMP_L,
            theoretical_formula=r"f(\beta, g, g_n, Y_0) \to N_{sims}",
            result=float(num_simulations),
            numerical_substitution=StrategyInterpretations.MC_SAMPLING_SUB.format(count=num_simulations),
            interpretation=StrategyInterpretations.MC_SAMPLING_INTERP
        )

        # =====================================================================
        # ÉTAPE 3 : BOUCLE DE SIMULATION PRINCIPALE
        # =====================================================================
        # Le travailleur de stratégie ne doit pas générer sa propre trace Glass Box
        worker = self.strategy_cls(glass_box_enabled=False)

        # Transmission de base_flows pour perturber l'ancrage de la valorisation
        simulated_values = self._run_simulations(
            worker, financials, params, betas, growths, terminal_growths,
            base_flows, num_simulations
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
            numerical_substitution=KPITexts.MC_FILTER_SUB.format(
                valid=valid_count,
                total=num_simulations
            ),
            interpretation=StrategyInterpretations.MC_FILTERING
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            raise MonteCarloInstabilityError(valid_ratio, self.MIN_VALID_RATIO)

        # =====================================================================
        # ÉTAPE 5 : EXTRACTION DES QUANTILES (Valeur P50)
        # =====================================================================
        # Exécution de référence avec trace activée pour le rapport final
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
            numerical_substitution=KPITexts.SUB_P50_VAL.format(
                val=p50,
                curr=financials.currency
            ),
            interpretation=RegistryTexts.MC_MED_D
        )

        # =====================================================================
        # ÉTAPE 6 : ANALYSE DE SENSIBILITÉ (RHO) ET STRESS TEST
        # =====================================================================
        self._run_sensitivity_analysis(worker, financials, params, final_result, p50)
        self._run_stress_test(worker, financials, params, final_result)

        # =====================================================================
        # ÉTAPE 7 : SYNTHÈSE DES TRACES
        # =====================================================================
        final_result.mc_valid_ratio = valid_ratio
        final_result.mc_clamping_applied = clamping_applied
        # Fusion de la trace du wrapper Monte Carlo avec la trace du modèle sous-jacent
        final_result.calculation_trace = self.calculation_trace + final_result.calculation_trace

        return final_result

    # ==========================================================================
    # MÉTHODES PRIVÉES (Ajustées pour segmentation et isolation profonde)
    # ==========================================================================

    def _compute_base_wacc(
        self,
        financials: CompanyFinancials,
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
        """Écrêtage économique sur le taux de croissance (Segment growth)."""
        g_raw = params.growth.fcf_growth_rate if params.growth.fcf_growth_rate is not None else 0.03
        g_clamped = min(g_raw, base_wacc - self.GROWTH_SAFETY_MARGIN)
        clamping_applied = g_clamped < g_raw

        return g_raw, g_clamped, clamping_applied

    def _generate_samples(
        self,
        financials: CompanyFinancials,
        params: DCFParameters,
        num_simulations: int,
        base_wacc: float
    ) -> tuple[ndarray, ndarray, ndarray, float | ndarray[Any, dtype[floating[_64Bit]]]]:
        """Génère les échantillons via segments MonteCarlo et Growth."""
        mc = params.monte_carlo
        g = params.growth

        sig_b = mc.beta_volatility if mc.beta_volatility is not None else 0.10
        sig_g = mc.growth_volatility if mc.growth_volatility is not None else 0.015
        sig_gn = mc.terminal_growth_volatility if mc.terminal_growth_volatility is not None else 0.005
        # Protection : Si Multiple, sigma = 0 (valeur fixe).
        if g.terminal_method != TerminalValueMethod.GORDON_GROWTH:
            sig_gn = 0.0
        sig_y0 = mc.base_flow_volatility if mc.base_flow_volatility is not None else 0.05

        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=sig_b,
            mu_growth=g.fcf_growth_rate if g.fcf_growth_rate is not None else 0.03,
            sigma_growth=sig_g,
            rho=mc.correlation_beta_growth,
            num_simulations=num_simulations
        )

        terminal_growths = generate_independent_samples(
            mean=g.perpetual_growth_rate if g.perpetual_growth_rate is not None else 0.02,
            sigma=sig_gn,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=max(0.0, min(0.04, base_wacc - 0.01))
        )

        base_flows = np.random.normal(1.0, sig_y0, num_simulations)

        return betas, growths, terminal_growths, base_flows

    def _run_simulations(
            self,
            worker: ValuationStrategy,
            financials: CompanyFinancials,
            params: DCFParameters,
            betas: np.ndarray,
            growths: np.ndarray,
            terminal_growths: np.ndarray,
            base_flows: np.ndarray,  # <--- Nouvel argument
            num_simulations: int
    ) -> List[float]:
        """Boucle de simulation avec isolation profonde et perturbation Y0."""
        simulated_values = []

        for i in range(num_simulations):
            try:
                # 1. Mise à jour du beta
                s_fin = financials.model_copy(update={"beta": float(betas[i])})

                # 2. Isolation et perturbation des paramètres
                s_par = params.model_copy(deep=True)
                s_par.growth.fcf_growth_rate = float(growths[i])
                s_par.growth.perpetual_growth_rate = float(terminal_growths[i])

                # 3. Application de l'incertitude sur le flux de départ (Y0)
                # On multiplie la valeur de base par le facteur aléatoire généré
                if s_par.growth.manual_fcf_base is not None:
                    s_par.growth.manual_fcf_base *= float(base_flows[i])
                elif s_par.growth.manual_dividend_base is not None:
                    s_par.growth.manual_dividend_base *= float(base_flows[i])
                elif financials.fcf_last is not None:
                    # Fallback pour le mode Auto : on injecte une surcharge manuelle perturbée
                    s_par.growth.manual_fcf_base = financials.fcf_last * float(base_flows[i])

                res = worker.execute(s_fin, s_par)
                iv = res.intrinsic_value_per_share

                if 0.0 < iv < self.MAX_IV_FILTER:
                    simulated_values.append(iv)

            except (CalculationError, ModelDivergenceError, ValueError, ZeroDivisionError):
                continue

        return simulated_values

    def _compute_quantiles(self, simulated_values: List[float]) -> dict:
        """Calcule les statistiques descriptives de la distribution."""
        return {
            "P10": float(np.percentile(simulated_values, 10)),
            "P50": float(np.percentile(simulated_values, 50)),
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
        """Analyse de l'impact de la corrélation (rho) via isolation V9."""
        mc = params.monte_carlo
        g = params.growth

        try:
            b_neutral, g_neutral = generate_multivariate_samples(
                mu_beta=financials.beta,
                sigma_beta=mc.beta_volatility if mc.beta_volatility is not None else 0.1,
                mu_growth=g.fcf_growth_rate if g.fcf_growth_rate is not None else 0.03,
                sigma_growth=mc.growth_volatility if mc.growth_volatility is not None else 0.02,
                rho=0.0, # Test de l'indépendance
                num_simulations=self.SENSITIVITY_SIMULATIONS
            )

            sims_neutral = []
            for i in range(self.SENSITIVITY_SIMULATIONS):
                try:
                    s_par = params.model_copy(deep=True)
                    s_par.growth.fcf_growth_rate = float(g_neutral[i])

                    r_n = worker.execute(
                        financials.model_copy(update={"beta": float(b_neutral[i])}),
                        s_par
                    )
                    if 0 < r_n.intrinsic_value_per_share < self.MAX_IV_FILTER:
                        sims_neutral.append(r_n.intrinsic_value_per_share)

                except (CalculationError, ModelDivergenceError, ValueError, ZeroDivisionError):
                    continue

            p50_neutral = float(np.percentile(sims_neutral, 50)) if sims_neutral else p50_base
            final_result.rho_sensitivity = {
                StrategyInterpretations.MC_SENS_NEUTRAL: p50_neutral,
                StrategyInterpretations.MC_SENS_BASE: p50_base
            }

            self.add_step(
                step_key="MC_SENSITIVITY",
                label=RegistryTexts.MC_SENS_L,
                theoretical_formula=r"\frac{\partial P50}{\partial \rho}",
                result=p50_neutral,
                numerical_substitution=KPITexts.MC_SENS_SUB.format(
                    p50_n=p50_neutral,
                    p50_b=p50_base
                ),
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
        """Exécute le stress test déterministe (Bear Case) via segments V9."""
        try:
            # Création d'un environnement de stress via les segments growth et rates
            stress_params = params.model_copy(deep=True)
            stress_params.growth.fcf_growth_rate = 0.0
            stress_params.growth.perpetual_growth_rate = 0.01
            stress_params.rates.manual_beta = 1.50 # Risque systémique maximum

            stress_res = worker.execute(financials, stress_params)
            final_result.stress_test_value = stress_res.intrinsic_value_per_share

            self.add_step(
                step_key="MC_STRESS_TEST",
                label=RegistryTexts.MC_STRESS_L,
                theoretical_formula=r"f(g \to 0, \beta \to 1.5)",
                result=final_result.stress_test_value,
                numerical_substitution=StrategyInterpretations.MC_STRESS_SUB.format(
                    val=final_result.stress_test_value,
                    curr=financials.currency
                ),
                interpretation=StrategyInterpretations.MC_STRESS_INTERP
            )

        except (CalculationError, ModelDivergenceError, ValueError) as e:
            logger.error("Erreur calcul Stress Test: %s", e)