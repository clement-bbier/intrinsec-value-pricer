"""
core/valuation/strategies/monte_carlo.py
MOTEUR STOCHASTIQUE V7.0 — AVEC ÉCRÊTAGE ÉCONOMIQUE (Sanity Clamping)
Rôle : Simulation multivariée avec garantie de convergence et transparence d'audit.
Note : Correction du paradigme "None = Auto" pour les simulations de croissance.
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
from core.computation.financial_math import calculate_wacc

logger = logging.getLogger(__name__)

class MonteCarloGenericStrategy(ValuationStrategy):
    """Wrapper Monte Carlo avec protection contre la divergence économique."""

    def __init__(self, strategy_cls: Type[ValuationStrategy], glass_box_enabled: bool = True):
        super().__init__(glass_box_enabled=glass_box_enabled)
        self.strategy_cls = strategy_cls

    DEFAULT_SIMULATIONS = 5000
    MIN_VALID_RATIO = 0.20
    GROWTH_SAFETY_MARGIN = 0.015 # Marge de sécurité (1.5%) sous le WACC

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        num_simulations = params.num_simulations if params.num_simulations is not None else self.DEFAULT_SIMULATIONS

        # --- ÉTAPE 0 : SANITY CLAMPING (Écrêtage Économique) ---
        # On calcule le WACC de base pour vérifier la cohérence de la croissance
        try:
            base_wacc = calculate_wacc(financials, params).wacc
        except:
            base_wacc = 0.08 # Fallback de sécurité à 8% pour le clamping

        # Si g est trop proche ou supérieur au WACC, on l'écrête pour garantir la convergence
        # Respect du 0.0 : On n'utilise plus 'or 0.03'
        g_raw = params.fcf_growth_rate if params.fcf_growth_rate is not None else 0.03
        g_clamped = min(g_raw, base_wacc - self.GROWTH_SAFETY_MARGIN)
        clamping_note = ""

        if g_clamped < g_raw:
            clamping_note = f" (Écrêté de {g_raw:.1%} pour cohérence WACC)"
            params.fcf_growth_rate = g_clamped # On injecte la valeur sécurisée
            logger.warning(f"[Monte Carlo] Clamping appliqué sur g: {g_raw:.1%} -> {g_clamped:.1%}")

        # 1. CONFIG (ID: MC_CONFIG)
        self.add_step(
            step_key="MC_CONFIG",
            result=1.0,
            numerical_substitution=(
                f"Itérations : {num_simulations} | "
                f"β: 𝒩({financials.beta:.2f}, {(params.beta_volatility or 0.10):.1%}) | "
                f"g: 𝒩({(params.fcf_growth_rate or 0.03):.1%}, {(params.growth_volatility or 0.015):.1%}) | "
                f"ρ(β,g): {params.correlation_beta_growth:.2f}"
            ),
            interpretation=f"Calibration des lois normales multivariées.{clamping_note}"
        )

        # --- GÉNÉRATION DES TIRAGES ---
        sig_b = params.beta_volatility if params.beta_volatility is not None else 0.10
        sig_g = params.growth_volatility if params.growth_volatility is not None else 0.015
        sig_gn = params.terminal_growth_volatility if params.terminal_growth_volatility is not None else 0.005

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
            clip_min=0.0, clip_max=max(0.0, min(0.04, base_wacc - 0.01)) # Sécurité sur gn
        )

        # 2. SAMPLING (ID: MC_SAMPLING)
        self.add_step(
            step_key="MC_SAMPLING",
            result=float(num_simulations),
            numerical_substitution=f"Génération de {num_simulations} vecteurs d'inputs via Décomposition de Cholesky.",
            interpretation="Application des corrélations pour garantir la cohérence économique des scénarios tirés."
        )

        # --- 2. BOUCLE DE SIMULATION PRINCIPALE ---
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

                # Filtrage technique des valeurs aberrantes
                if 0.0 < iv < 100_000.0:
                    simulated_values.append(iv)
            except:
                continue

        # --- 3. FILTRAGE ET CONVERGENCE (GLASS BOX) ---
        valid_count = len(simulated_values)
        valid_ratio = valid_count / num_simulations

        self.add_step(
            step_key="MC_FILTERING",
            result=valid_ratio,
            numerical_substitution=f"{valid_count} valides / {num_simulations} itérations",
            interpretation="Élimination des scénarios de divergence pour stabiliser la distribution."
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            from core.exceptions import MonteCarloInstabilityError
            raise MonteCarloInstabilityError(valid_ratio, self.MIN_VALID_RATIO)

        # --- 4. EXTRACTION DES QUANTILES (BASE) ---
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
            result=p50,
            numerical_substitution=f"P50 = {p50:,.2f} {financials.currency}",
            interpretation="Valeur intrinsèque centrale dérivée de la distribution stochastique."
        )

        # --- 5. ANALYSE DE SENSIBILITÉ RÉELLE (RHO SENSITIVITY) ---
        try:
            b_neutral, g_neutral = generate_multivariate_samples(
                mu_beta=financials.beta,
                sigma_beta=params.beta_volatility if params.beta_volatility is not None else 0.1,
                mu_growth=params.fcf_growth_rate if params.fcf_growth_rate is not None else 0.03,
                sigma_growth=params.growth_volatility if params.growth_volatility is not None else 0.02,
                rho=0.0, num_simulations=1000
            )
            sims_neutral = []
            for i in range(1000):
                try:
                    r_n = worker.execute(financials.model_copy(update={"beta": float(b_neutral[i])}),
                                         params.model_copy(update={"fcf_growth_rate": float(g_neutral[i])}))
                    if 0 < r_n.intrinsic_value_per_share < 100000:
                        sims_neutral.append(r_n.intrinsic_value_per_share)
                except:
                    continue

            p50_neutral = float(np.percentile(sims_neutral, 50)) if sims_neutral else p50
            final_result.rho_sensitivity = {"Neutre (rho=0)": p50_neutral, "Base (rho=-0.3)": p50}

            self.add_step(
                step_key="MC_SENSITIVITY",
                result=p50_neutral,
                numerical_substitution=f"P50(rho=0) = {p50_neutral:,.2f} vs Base = {p50:,.2f}",
                interpretation="Audit de l'impact de la corrélation sur la stabilité de la valeur médiane."
            )
        except Exception as e:
            logger.error(f"Erreur calcul sensibilité Rho: {e}")

        # --- 6. STRESS TEST (BEAR CASE DÉTERMINISTE) ---
        try:
            stress_params = params.model_copy(update={
                "fcf_growth_rate": 0.0,
                "perpetual_growth_rate": 0.01,
                "manual_beta": 1.50
            })
            stress_res = worker.execute(financials, stress_params)
            final_result.stress_test_value = stress_res.intrinsic_value_per_share

            self.add_step(
                step_key="MC_STRESS_TEST",
                result=final_result.stress_test_value,
                numerical_substitution=f"Bear Case = {final_result.stress_test_value:,.2f} {financials.currency}",
                interpretation="Scénario de stress : croissance nulle et risque élevé (Point de rupture)."
            )
        except Exception as e:
            logger.error(f"Erreur calcul Stress Test: {e}")

        # --- 7. FUSION ET RETOUR ---
        final_result.calculation_trace = self.calculation_trace + final_result.calculation_trace
        return final_result

        # --- 8. INJECTION DES MÉTRIQUES STOCHASTIQUES POUR L'AUDIT ---
        # On expose le ratio de validité et l'éventuel clamping
        final_result.mc_valid_ratio = valid_ratio
        final_result.mc_clamping_applied = (g_clamped < g_raw)