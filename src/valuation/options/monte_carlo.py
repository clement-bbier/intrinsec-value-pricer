"""
src/valuation/options/monte_carlo.py

MONTE CARLO RUNNER
==================
Role: Probabilistic Risk Analysis.
Logic: Wraps the deterministic strategy to run N simulations across a correlated risk matrix.
Architecture: Runner Pattern (Visitor).

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional

from src.config.settings import MonteCarloSimulationConfig
from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.results.options import MCResults
from src.models.enums import TerminalValueMethod

# Interfaces
from src.valuation.strategies.interface import IValuationRunner

# Math & Stats
from src.computation.financial_math import calculate_cost_of_equity_capm
from src.computation.statistics import (
    generate_independent_samples,
    generate_multivariate_samples,
)

# Config
from src.config.constants import MonteCarloDefaults, ModelDefaults, MacroDefaults

# Exceptions
from src.core.exceptions import (
    CalculationError,
    ModelDivergenceError
)

logger = logging.getLogger(__name__)

# Errors to catch during the loop
VALUATION_ERRORS = (
    CalculationError,
    ModelDivergenceError,
    ValueError,
    ZeroDivisionError,
    AttributeError
)


class MonteCarloRunner:
    """
    Orchestrates the stochastic simulation lifecycle.
    """

    def __init__(self, strategy: IValuationRunner):
        """
        Parameters
        ----------
        strategy : IValuationRunner
            The deterministic engine instance to be simulated.
        """
        self.strategy = strategy

    def execute(self, params: Parameters, financials: Company) -> Optional[MCResults]:
        """
        Runs the N simulations.

        Parameters
        ----------
        params : Parameters
            Configuration containing simulation settings and shocks.
        financials : Company
            Financial data of the target.

        Returns
        -------
        Optional[MCResults]
            Statistical results of the simulation, or None if disabled.
        """
        mc_cfg = params.extensions.monte_carlo

        if not mc_cfg.enabled:
            return None

        num_simulations = mc_cfg.iterations or MonteCarloDefaults.DEFAULT_SIMULATIONS

        # 1. Economic Clamping Reference (WACC Guardrail)
        # We estimate WACC once to establish the ceiling for growth (g < WACC)
        try:
            r = params.common.rates
            rf = r.risk_free_rate or MacroDefaults.DEFAULT_RISK_FREE_RATE
            beta = r.beta or ModelDefaults.DEFAULT_BETA
            mrp = r.market_risk_premium or MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM

            base_ke = calculate_cost_of_equity_capm(rf, beta, mrp)
            base_wacc = base_ke  # Approximation safe for clamping if Debt info missing

        except VALUATION_ERRORS:
            # Fallback only on specific expected failures (Math, Missing Data)
            base_wacc = MonteCarloSimulationConfig.default_wacc_fallback

        # 2. Correlated Sampling
        betas, growths, terminal_growths, base_flows = self._generate_samples(
            financials, params, num_simulations, base_wacc
        )

        # 3. Main Simulation Loop
        sim_values = self._run_simulations(
            self.strategy, financials, params, betas, growths, terminal_growths, base_flows, num_simulations
        )

        # 4. Statistics
        if not sim_values:
            return None

        quantiles = self._compute_quantiles(sim_values)

        return MCResults(
            simulation_values=sim_values,
            quantiles=quantiles,
            mean=float(np.mean(sim_values)),
            std_dev=float(np.std(sim_values))
        )

    @staticmethod
    def _generate_samples(
        financials: Company,
        params: Parameters,
        num_simulations: int,
        base_wacc: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Generates correlated stochastic input vectors.
        """
        mc_shocks = params.extensions.monte_carlo.shocks
        g_params = params.strategy.terminal_value

        # --- A. Extract Volatilities (Default Safety Values) ---
        sig_b = 0.10   # Beta Volatility
        sig_g = 0.015  # Growth Volatility
        sig_gn = 0.005 # Terminal Growth Volatility
        sig_y0 = 0.05  # Base Flow Volatility

        # Dynamic extraction from polymorphic shocks
        if mc_shocks:
            if hasattr(mc_shocks, 'beta_volatility') and mc_shocks.beta_volatility:
                sig_b = mc_shocks.beta_volatility
            if hasattr(mc_shocks, 'growth_volatility') and mc_shocks.growth_volatility:
                sig_g = mc_shocks.growth_volatility

            # Polymorphic field for Flow volatility (FCF or EPS)
            if hasattr(mc_shocks, 'fcf_volatility') and mc_shocks.fcf_volatility:
                 sig_y0 = mc_shocks.fcf_volatility
            elif hasattr(mc_shocks, 'eps_volatility') and mc_shocks.eps_volatility:
                 sig_y0 = mc_shocks.eps_volatility

        # --- B. Determine Mean Growth ---
        # We target the common 'fcf_growth_rate' located in params.growth
        mu_growth = params.growth.fcf_growth_rate or ModelDefaults.DEFAULT_GROWTH_RATE

        # --- C. Terminal Growth Volatility ---
        if g_params.method != TerminalValueMethod.GORDON_GROWTH:
            sig_gn = 0.0

        # --- 1. Correlated Beta/Growth Sampling ---
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta or ModelDefaults.DEFAULT_BETA,
            sigma_beta=sig_b,
            mu_growth=mu_growth,
            sigma_growth=sig_g,
            rho=MonteCarloDefaults.DEFAULT_RHO,
            num_simulations=num_simulations
        )

        # --- 2. Terminal Growth Sampling (Clipped) ---
        # Ensures g < WACC - 1.5% to prevent explosion
        max_g = max(0.0, base_wacc - 0.015)

        terminal_growths = generate_independent_samples(
            mean=g_params.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH,
            sigma=sig_gn,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=max_g
        )

        # --- 3. Base Flow Disturbance (Y0) ---
        # Multiplier centered on 1.0
        base_flows = np.random.normal(1.0, sig_y0, num_simulations)

        return betas, growths, terminal_growths, base_flows

    @staticmethod
    def _run_simulations(
        runner: IValuationRunner,
        financials: Company,
        params: Parameters,
        betas: np.ndarray,
        growths: np.ndarray,
        terminal_growths: np.ndarray,
        base_flows: np.ndarray,
        num_simulations: int
    ) -> List[float]:
        """
        High-performance computation loop.
        """
        sim_values = []

        # Disable Glass Box for speed
        runner.glass_box_enabled = False

        for i in range(num_simulations):
            try:
                # 1. Clone Parameters (Deep Copy)
                s_par = params.model_copy(deep=True)

                # 2. Apply Beta Shock (Common Rates)
                # We overwrite the 'manual_beta' field to force the resolver to take it
                s_par.common.rates.beta = float(betas[i])

                # 3. Apply Growth Shocks
                # We target the shared growth container
                s_par.growth.fcf_growth_rate = float(growths[i])

                # Terminal Growth
                if s_par.strategy.terminal_value:
                    s_par.strategy.terminal_value.perpetual_growth_rate = float(terminal_growths[i])

                # 4. Apply Base Flow Shock (Y0)
                # We check which anchor is active in the strategy parameters and scale it
                factor = float(base_flows[i])

                # Strategies typically store anchor in 'strategy' parameters (e.g. fcf_anchor)
                if hasattr(s_par.strategy, 'fcf_anchor') and s_par.strategy.fcf_anchor:
                    s_par.strategy.fcf_anchor *= factor
                elif hasattr(s_par.strategy, 'dividend_per_share') and s_par.strategy.dividend_per_share:
                    s_par.strategy.dividend_per_share *= factor
                elif hasattr(s_par.strategy, 'fcfe_anchor') and s_par.strategy.fcfe_anchor:
                    s_par.strategy.fcfe_anchor *= factor
                elif hasattr(s_par.strategy, 'eps_normalized') and s_par.strategy.eps_normalized:
                    s_par.strategy.eps_normalized *= factor

                # 5. Execute
                result = runner.execute(financials, s_par)
                iv = result.results.common.intrinsic_value_per_share

                # 6. Sanity Filter
                if 0.0 < iv < 1_000_000: # Simple guardrail
                    sim_values.append(iv)

            except VALUATION_ERRORS:
                continue

        # Re-enable Audit
        runner.glass_box_enabled = True

        return sim_values

    @staticmethod
    def _compute_quantiles(sim_values: List[float]) -> Dict[str, float]:
        """Calculates standard distribution statistics."""
        return {
            "P10": float(np.percentile(sim_values, 10)),
            "P50": float(np.percentile(sim_values, 50)),
            "P90": float(np.percentile(sim_values, 90))
        }