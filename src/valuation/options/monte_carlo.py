from __future__ import annotations
import logging
import numpy as np
from typing import Optional

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.results.options import MCResults
from src.valuation.strategies.interface import IValuationRunner
from src.computation.financial_math import calculate_cost_of_equity_capm
from src.computation.statistics import generate_independent_samples, generate_multivariate_samples

from src.config.constants import MonteCarloDefaults, ModelDefaults, MacroDefaults
from src.core.exceptions import CalculationError, ModelDivergenceError

logger = logging.getLogger(__name__)

class MonteCarloRunner:
    """Orchestrates the stochastic simulation lifecycle."""

    def __init__(self, strategy: IValuationRunner):
        self.strategy = strategy

    def execute(self, params: Parameters, financials: Company) -> Optional[MCResults]:
        mc_cfg = params.extensions.monte_carlo
        if not mc_cfg or not mc_cfg.enabled:
            return None

        num_simulations = mc_cfg.iterations or MonteCarloDefaults.DEFAULT_SIMULATIONS
        seed = mc_cfg.random_seed if mc_cfg.random_seed is not None else 42

        # 1. Economic Clamping Reference (WACC Guardrail)
        # We need a stable discount rate to cap terminal growth (g < WACC).
        r = params.common.rates

        try:
            if r.wacc:
                base_wacc = r.wacc
            elif r.cost_of_equity:
                base_wacc = r.cost_of_equity
            else:
                rf = r.risk_free_rate if r.risk_free_rate is not None else MacroDefaults.DEFAULT_RISK_FREE_RATE
                beta = r.beta if r.beta is not None else ModelDefaults.DEFAULT_BETA
                mrp = r.market_risk_premium if r.market_risk_premium is not None else MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM

                base_wacc = calculate_cost_of_equity_capm(rf, beta, mrp)

            if base_wacc <= 0:
                base_wacc = ModelDefaults.DEFAULT_WACC

        except (ArithmeticError, TypeError, ValueError) as e:
            logger.warning(f"Failed to calculate base WACC for MC clamping, using default: {e}")
            base_wacc = ModelDefaults.DEFAULT_WACC

        # 2. Sampling
        betas, growths, terminal_growths, base_flows = self._generate_samples(
            financials, params, num_simulations, base_wacc, seed
        )

        # 3. Execution
        sim_values = self._run_simulations(
            financials, params, betas, growths, terminal_growths, base_flows, num_simulations
        )

        if not sim_values: return None

        return MCResults(
            simulation_values=sim_values,
            quantiles={
                "P10": float(np.percentile(sim_values, 10)),
                "P50": float(np.percentile(sim_values, 50)),
                "P90": float(np.percentile(sim_values, 90))
            },
            mean=float(np.mean(sim_values)),
            std_dev=float(np.std(sim_values))
        )

    @staticmethod
    def _generate_samples(financials, params, num_sims, base_wacc, seed: Optional[int] = 42):
        shocks = params.extensions.monte_carlo.shocks

        # Volatilities extraction
        sig_b = getattr(shocks, 'beta_volatility', 0.10) or 0.10
        sig_g = getattr(shocks, 'growth_volatility', 0.015) or 0.015
        sig_gn = 0.005
        sig_y0 = 0.05 # Default flow vol

        # Mean Growth extraction based on strategy mode
        mu_growth = ModelDefaults.DEFAULT_GROWTH_RATE
        st = params.strategy
        if hasattr(st, 'growth_rate_p1'): mu_growth = st.growth_rate_p1 or mu_growth
        elif hasattr(st, 'growth_rate'): mu_growth = st.growth_rate or mu_growth
        elif hasattr(st, 'revenue_growth_rate'): mu_growth = st.revenue_growth_rate or mu_growth

        betas, growths = generate_multivariate_samples(
            mu_beta=params.common.rates.beta or financials.beta or 1.0,
            sigma_beta=sig_b,
            mu_growth=mu_growth,
            sigma_growth=sig_g,
            rho=MonteCarloDefaults.DEFAULT_RHO,
            num_simulations=num_sims,
            seed=seed
        )

        mean_gn = ModelDefaults.DEFAULT_TERMINAL_GROWTH
        if hasattr(st, 'terminal_value'):
            mean_gn = st.terminal_value.perpetual_growth_rate or mean_gn

        terminal_growths = generate_independent_samples(
            mean=mean_gn,
            sigma=sig_gn,
            num_simulations=num_sims,
            clip_min=0.0,
            clip_max=max(0.0, base_wacc - 0.01),
            seed=seed
        )

        # Use modern NumPy RNG for base_flows
        rng = np.random.default_rng(seed)
        base_flows = rng.normal(1.0, sig_y0, num_sims)
        return betas, growths, terminal_growths, base_flows

    def _run_simulations(self, financials, params, betas, growths, t_growths, flows, num_sims):
        sim_values = []
        self.strategy.glass_box_enabled = False

        for i in range(num_sims):
            try:
                s_par = params.model_copy(deep=True)
                st = s_par.strategy
                
                # Apply Shocks
                s_par.common.rates.beta = float(betas[i])
                
                # Growth Dispatch
                g_val = float(growths[i])
                if hasattr(st, 'growth_rate_p1'): st.growth_rate_p1 = g_val
                elif hasattr(st, 'growth_rate'): st.growth_rate = g_val
                elif hasattr(st, 'revenue_growth_rate'): st.revenue_growth_rate = g_val
                elif hasattr(st, 'growth_estimate'): st.growth_estimate = g_val

                # Terminal Value Dispatch
                if hasattr(st, 'terminal_value'):
                    st.terminal_value.perpetual_growth_rate = float(t_growths[i])

                # Anchor Flow Dispatch
                f_val = float(flows[i])
                if hasattr(st, 'fcf_anchor') and st.fcf_anchor: st.fcf_anchor *= f_val
                elif hasattr(st, 'revenue_ttm') and st.revenue_ttm: st.revenue_ttm *= f_val
                elif hasattr(st, 'eps_normalized') and st.eps_normalized: st.eps_normalized *= f_val

                res = self.strategy.execute(financials, s_par)
                iv = res.results.common.intrinsic_value_per_share
                if 0 < iv < 1_000_000:
                    sim_values.append(iv)
            except (CalculationError, ModelDivergenceError, ValueError, ZeroDivisionError):
                continue

        self.strategy.glass_box_enabled = True
        return sim_values