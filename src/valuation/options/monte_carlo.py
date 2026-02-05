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

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.results.options import MCResults
from src.models.enums import TerminalValueMethod
from src.valuation.strategies.abstract import ValuationStrategy
from src.computation.financial_math import calculate_wacc
from src.computation.statistics import (
    generate_independent_samples,
    generate_multivariate_samples,
)
from src.config.constants import MonteCarloDefaults
from src.exceptions import (
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

    def __init__(self, strategy: ValuationStrategy):
        """
        Parameters
        ----------
        strategy : ValuationStrategy
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

        # 1. Economic Clamping Reference (Guardrail)
        try:
            # We calculate WACC once to establish the ceiling for growth (g < WACC)
            base_wacc_obj = calculate_wacc(financials, params)
            base_wacc = base_wacc_obj.wacc
        except VALUATION_ERRORS:
            base_wacc = 0.085  # Fallback to avoid crash before simulation

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
            simulation_values=sim_values,  # Can be truncated for UI perf in the View layer
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

        # --- A. Extract Volatilities (Dynamic or Default) ---
        # Default safety values
        sig_b = 0.10   # Beta volatility
        sig_g = 0.015  # Growth volatility
        sig_y0 = 0.05  # Base flow volatility
        sig_gn = 0.005 # Terminal growth volatility

        # Dynamic extraction from polymorphic shocks
        if mc_shocks:
            if getattr(mc_shocks, 'beta_volatility', None):
                sig_b = mc_shocks.beta_volatility
            if getattr(mc_shocks, 'growth_volatility', None):
                sig_g = mc_shocks.growth_volatility

            # Specific fields depending on shock type (standard, graham, etc.)
            if hasattr(mc_shocks, 'fcf_volatility') and mc_shocks.fcf_volatility:
                 sig_y0 = mc_shocks.fcf_volatility
            elif hasattr(mc_shocks, 'eps_volatility') and mc_shocks.eps_volatility:
                 sig_y0 = mc_shocks.eps_volatility

        # --- B. Determine Mean Growth ---
        # Try to find the short-term growth rate from the strategy parameters
        mu_growth = 0.03  # Default
        if hasattr(params.strategy, 'growth_rate') and params.strategy.growth_rate is not None:
             mu_growth = params.strategy.growth_rate

        # --- C. Determine Terminal Growth Volatility ---
        # Only simulate terminal growth if we are in Gordon Growth model
        if g_params.method != TerminalValueMethod.GORDON_GROWTH:
            sig_gn = 0.0

        # --- 1. Correlated Beta/Growth Sampling ---
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta or 1.0,
            sigma_beta=sig_b,
            mu_growth=mu_growth,
            sigma_growth=sig_g,
            rho=MonteCarloDefaults.DEFAULT_RHO,
            num_simulations=num_simulations
        )

        # --- 2. Terminal Growth Sampling (Clipped) ---
        # Ensures g < WACC - 1% to prevent mathematical explosion
        terminal_growths = generate_independent_samples(
            mean=g_params.perpetual_growth_rate or 0.02,
            sigma=sig_gn,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=max(0.0, min(0.04, base_wacc - 0.01))
        )

        # --- 3. Base Flow Disturbance (Y0) ---
        # Multiplier centered on 1.0 (e.g., 0.95 to 1.05)
        base_flows = np.random.normal(1.0, sig_y0, num_simulations)

        return betas, growths, terminal_growths, base_flows

    @staticmethod
    def _run_simulations(
        strategy: ValuationStrategy,
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
        Applies the generated vectors to the parameters and runs the engine.
        """
        sim_values = []

        # Disable Audit for speed (Critical for performance)
        strategy.glass_box_enabled = False

        for i in range(num_simulations):
            try:
                # 1. Clone Parameters (Deep Copy is safer for nested objects)
                s_par = params.model_copy(deep=True)

                # 2. Apply Beta Shock (Capital Structure)
                # We force the manual beta override to take precedence
                if hasattr(s_par.common.rates, 'manual_beta'):
                     s_par.common.rates.manual_beta = float(betas[i])

                # 3. Apply Growth Shocks (Strategy Specifics)
                # Note: We rely on attribute existence to support multiple strategy types
                if hasattr(s_par.strategy, 'growth_rate'):
                    s_par.strategy.growth_rate = float(growths[i])

                if hasattr(s_par.strategy, 'terminal_value'):
                    s_par.strategy.terminal_value.perpetual_growth_rate = float(terminal_growths[i])

                # 4. Apply Base Flow Shock (Y0)
                # We scale the anchor (e.g. FCF Base, EPS Base) by the factor
                factor = float(base_flows[i])

                # Check for common anchor names in StrategyUnionParameters
                if hasattr(s_par.strategy, 'fcf_anchor') and s_par.strategy.fcf_anchor is not None:
                    s_par.strategy.fcf_anchor *= factor
                elif hasattr(s_par.strategy, 'fcfe_anchor') and s_par.strategy.fcfe_anchor is not None:
                     s_par.strategy.fcfe_anchor *= factor
                elif hasattr(s_par.strategy, 'dividend_per_share') and s_par.strategy.dividend_per_share is not None:
                     s_par.strategy.dividend_per_share *= factor
                elif hasattr(s_par.strategy, 'eps_normalized') and s_par.strategy.eps_normalized is not None:
                     s_par.strategy.eps_normalized *= factor

                # 5. Execute
                iv = strategy.execute(financials, s_par).intrinsic_value_per_share

                # 6. Sanity Filter (Ignore negative or infinite values)
                if 0.0 < iv < 1_000_000:
                    sim_values.append(iv)

            except VALUATION_ERRORS:
                # Skip failed iterations (divergence)
                continue

        # Re-enable Audit for the main run
        strategy.glass_box_enabled = True

        return sim_values

    @staticmethod
    def _compute_quantiles(sim_values: List[float]) -> Dict[str, float]:
        """Calculates standard distribution statistics."""
        return {
            "P10": float(np.percentile(sim_values, 10)),
            "P50": float(np.percentile(sim_values, 50)),
            "P90": float(np.percentile(sim_values, 90))
        }