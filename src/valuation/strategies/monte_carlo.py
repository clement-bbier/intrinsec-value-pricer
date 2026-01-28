"""
src/valuation/strategies/monte_carlo.py

MONTE CARLO STOCHASTIC STRATEGY WRAPPER
=======================================
Academic Reference: Stochastic Methods in Finance.
Economic Domain: Probabilistic Risk & Sensitivity Analysis.
Invariants: Multivariate sampling with economic convergence clamping.

Role:
-----
Wraps any deterministic strategy (FCFF, DDM, RIM) to run N simulations
across a correlated risk matrix.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import List, Type, Tuple, Dict

import numpy as np

from src.computation.financial_math import calculate_wacc
from src.computation.statistics import (
    generate_independent_samples,
    generate_multivariate_samples,
)
from src.config.settings import SIMULATION_CONFIG
from src.exceptions import (
    CalculationError,
    ModelDivergenceError,
    MonteCarloInstabilityError,
)
from src.models import CompanyFinancials, DCFParameters, ValuationResult, TerminalValueMethod
from src.valuation.strategies.abstract import ValuationStrategy

# Centralized i18n mapping (Zero raw text policy)
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    KPITexts,
    QuantTexts,
    StrategySources
)

logger = logging.getLogger(__name__)

# Standard math/engine errors to catch during iterations
VALUATION_ERRORS = (
    CalculationError,
    ModelDivergenceError,
    ValueError,
    ZeroDivisionError,
    AttributeError
)


def _run_stress_test(
        worker: ValuationStrategy,
    financials: CompanyFinancials,
    params: DCFParameters,
    final_result: ValuationResult
) -> None:
    """Executes a 'Bear Case' stress test (Zero growth, extreme Beta)."""
    try:
        stress_params = params.model_copy(deep=True)
        stress_params.growth.fcf_growth_rate = 0.0
        stress_params.growth.perpetual_growth_rate = 0.01
        stress_params.rates.manual_beta = 1.50

        stress_res = worker.execute(financials, stress_params)
        final_result.stress_test_value = stress_res.intrinsic_value_per_share
    except VALUATION_ERRORS as e:
        logger.error("[MC] Stress test failed: %s", e)


class MonteCarloGenericStrategy(ValuationStrategy):
    """
    Monte Carlo Wrapper with economic divergence protection.

    Encapsulates a standard valuation strategy to perform stochastic
    simulations on Beta, Growth, and Base Cash Flows.
    """

    # Centralized limits from system settings
    DEFAULT_SIMULATIONS = SIMULATION_CONFIG.default_simulations
    MIN_VALID_RATIO = SIMULATION_CONFIG.min_valid_ratio
    GROWTH_SAFETY_MARGIN = SIMULATION_CONFIG.growth_safety_margin
    SENSITIVITY_SIMULATIONS = SIMULATION_CONFIG.sensitivity_simulations
    MAX_IV_FILTER = SIMULATION_CONFIG.max_iv_filter
    DEFAULT_WACC_FALLBACK = SIMULATION_CONFIG.default_wacc_fallback

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
        Executes the full Monte Carlo simulation lifecycle.
        """
        mc_cfg = params.monte_carlo
        num_simulations = mc_cfg.num_simulations or self.DEFAULT_SIMULATIONS

        # 0. Economic Clamping (Sanity check for WACC vs Growth convergence)
        base_wacc = self._compute_base_wacc(financials, params)
        g_raw, g_clamped, clamping_applied = self._apply_growth_clamping(params, base_wacc)

        if clamping_applied:
            params.growth.fcf_growth_rate = g_clamped
            logger.warning("[MC] Clamping g: %.1f%% -> %.1f%%", g_raw*100, g_clamped*100)

        # 1. Initialization (i18n Trace Step)
        clamping_note = StrategyInterpretations.MC_CLAMP_NOTE.format(g_raw=g_raw) if clamping_applied else ""
        sig_y0 = mc_cfg.base_flow_volatility if mc_cfg.base_flow_volatility is not None else 0.05

        self.add_step(
            step_key="MC_CONFIG",
            label=RegistryTexts.MC_INIT_L,
            theoretical_formula=StrategyFormulas.MC_VOLATILITY_MATRIX,
            result=1.0,
            numerical_substitution=QuantTexts.MC_CONFIG_SUB.format(
                sims=num_simulations,
                beta=financials.beta,
                sig_b=mc_cfg.beta_volatility or 0.10,
                g=params.growth.fcf_growth_rate or 0.03,
                sig_g=mc_cfg.growth_volatility or 0.015,
                sig_y0=sig_y0,
                rho=mc_cfg.correlation_beta_growth
            ),
            interpretation=StrategyInterpretations.MC_INIT.format(note=clamping_note),
            source=StrategySources.CALCULATED
        )

        # 2. Correlated Sampling
        betas, growths, terminal_growths, base_flows = self._generate_samples(
            financials, params, num_simulations, base_wacc
        )

        # 3. Main Simulation Loop (Isolated Worker)
        worker = self.strategy_cls(glass_box_enabled=False)
        sim_values = self._run_simulations(
            worker, financials, params, betas, growths, terminal_growths,
            base_flows, num_simulations
        )

        # 4. Convergence & Filtering Logic
        valid_ratio = len(sim_values) / num_simulations
        if valid_ratio < self.MIN_VALID_RATIO:
            raise MonteCarloInstabilityError(valid_ratio, self.MIN_VALID_RATIO)

        # 5. Result Extraction (P50 Median)
        ref_strategy = self.strategy_cls(glass_box_enabled=True)
        final_result = ref_strategy.execute(financials, params)

        quantiles = self._compute_quantiles(sim_values)
        p50 = quantiles["P50"]

        final_result.intrinsic_value_per_share = p50
        final_result.simulation_results = sim_values
        final_result.quantiles = quantiles

        self.add_step(
            step_key="MC_MEDIAN",
            label=RegistryTexts.MC_MED_L,
            theoretical_formula=StrategyFormulas.MC_MEDIAN,
            result=p50,
            numerical_substitution=KPITexts.SUB_P50_VAL.format(val=p50, curr=financials.currency),
            interpretation=RegistryTexts.MC_MED_D,
            source=StrategySources.CALCULATED
        )

        # 6. Sensitivity & Stress Test Post-Processing
        self._run_sensitivity_analysis(worker, financials, params, final_result, p50)
        _run_stress_test(worker, financials, params, final_result)

        # 7. Trace Consolidation & Audit
        final_result.mc_valid_ratio = valid_ratio
        final_result.mc_clamping_applied = clamping_applied
        final_result.calculation_trace = self.calculation_trace + final_result.calculation_trace

        self.generate_audit_report(final_result)
        self.verify_output_contract(final_result)
        return final_result

    # ==========================================================================
    # PRIVATE UTILITIES (Stochastic Core)
    # ==========================================================================

    def _compute_base_wacc(self, financials: CompanyFinancials, params: DCFParameters) -> float:
        """Calculates reference WACC for clamping logic."""
        try:
            return calculate_wacc(financials, params).wacc
        except VALUATION_ERRORS:
            return self.DEFAULT_WACC_FALLBACK

    def _apply_growth_clamping(self, params: DCFParameters, base_wacc: float) -> Tuple[float, float, bool]:
        """Ensures perpetuity growth g < WACC with a safety margin."""
        g_raw = params.growth.fcf_growth_rate or 0.03
        g_clamped = min(g_raw, base_wacc - self.GROWTH_SAFETY_MARGIN)
        return g_raw, g_clamped, (g_clamped < g_raw)

    @staticmethod
    def _generate_samples(
        financials: CompanyFinancials,
        params: DCFParameters,
        num_simulations: int,
        base_wacc: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Generates stochastic vectors using multivariate normal distributions."""
        mc, g = params.monte_carlo, params.growth

        # Volatility Calibration
        sig_b = mc.beta_volatility or 0.10
        sig_g = mc.growth_volatility or 0.015
        sig_y0 = mc.base_flow_volatility or 0.05
        sig_gn = 0.0 if g.terminal_method != TerminalValueMethod.GORDON_GROWTH else (mc.terminal_growth_volatility or 0.005)

        # 1. Correlated Beta/Growth Sampling
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta or 1.0,
            sigma_beta=sig_b,
            mu_growth=g.fcf_growth_rate or 0.03,
            sigma_growth=sig_g,
            rho=mc.correlation_beta_growth,
            num_simulations=num_simulations
        )

        # 2. Independent Terminal Growth Sampling
        terminal_growths = generate_independent_samples(
            mean=g.perpetual_growth_rate or 0.02,
            sigma=sig_gn,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=max(0.0, min(0.04, base_wacc - 0.01))
        )

        # 3. Year 0 Flow Disturbance
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
            base_flows: np.ndarray,
            num_simulations: int
    ) -> List[float]:
        """High-performance computation loop with isolated state."""
        sim_values = []
        original_level = logger.level
        logger.setLevel(logging.WARNING)

        for i in range(num_simulations):
            try:
                # 1. Inject stochastic inputs
                s_fin = financials.model_copy(update={"beta": float(betas[i])})
                s_par = params.model_copy(deep=True)
                s_par.growth.fcf_growth_rate = float(growths[i])
                s_par.growth.perpetual_growth_rate = float(terminal_growths[i])

                # 2. Perturb Year 0 Flow (Y0)
                factor = float(base_flows[i])
                if s_par.growth.manual_fcf_base is not None:
                    s_par.growth.manual_fcf_base *= factor
                elif s_par.growth.manual_dividend_base is not None:
                    s_par.growth.manual_dividend_base *= factor
                elif financials.fcf_last is not None:
                    s_par.growth.manual_fcf_base = financials.fcf_last * factor

                # 3. Calculate IV
                res = worker.execute(s_fin, s_par)
                iv = res.intrinsic_value_per_share

                if 0.0 < iv < self.MAX_IV_FILTER:
                    sim_values.append(iv)

            except VALUATION_ERRORS:
                continue

        logger.setLevel(original_level)
        return sim_values

    @staticmethod
    def _compute_quantiles(sim_values: List[float]) -> Dict[str, float]:
        """Calculates descriptive distribution statistics."""
        return {
            "P10": float(np.percentile(sim_values, 10)),
            "P50": float(np.percentile(sim_values, 50)),
            "P90": float(np.percentile(sim_values, 90)),
            "Mean": float(np.mean(sim_values)),
            "Std": float(np.std(sim_values))
        }

    def _run_sensitivity_analysis(
        self,
        worker: ValuationStrategy,
        financials: CompanyFinancials,
        params: DCFParameters,
        final_result: ValuationResult,
        p50_base: float
    ) -> None:
        """Analyzes Rho correlation impact via neutral ($ \rho = 0 $) baseline."""
        try:
            b_n, g_n = generate_multivariate_samples(
                mu_beta=financials.beta or 1.0,
                sigma_beta=0.1,
                mu_growth=params.growth.fcf_growth_rate or 0.03,
                sigma_growth=0.02,
                rho=0.0,
                num_simulations=self.SENSITIVITY_SIMULATIONS
            )

            sims_n = []
            for i in range(self.SENSITIVITY_SIMULATIONS):
                try:
                    s_fin = financials.model_copy(update={"beta": float(b_n[i])})
                    s_par = params.model_copy(deep=True)
                    s_par.growth.fcf_growth_rate = float(g_n[i])
                    sims_n.append(worker.execute(s_fin, s_par).intrinsic_value_per_share)
                except VALUATION_ERRORS:
                    continue

            p50_neutral = float(np.percentile(sims_n, 50)) if sims_n else p50_base
            final_result.rho_sensitivity = {
                StrategyInterpretations.MC_SENS_NEUTRAL: p50_neutral,
                StrategyInterpretations.MC_SENS_BASE: p50_base
            }
        except VALUATION_ERRORS as e:
            logger.error("[MC] Sensitivity failed: %s", e)

