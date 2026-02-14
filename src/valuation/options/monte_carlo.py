"""
src/valuation/options/monte_carlo.py

MONTE CARLO SIMULATION ENGINE
=============================
Role: Orchestrates stochastic simulations using efficient vectorization.
Architecture: Fast-Path NumPy implementation (No loops).
"""

from __future__ import annotations

import logging

import numpy as np

from src.computation.financial_math import calculate_cost_of_equity_capm
from src.config.constants import MacroDefaults, ModelDefaults, MonteCarloDefaults
from src.core.exceptions import CalculationError
from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.results.options import MCResults
from src.valuation.strategies.interface import IValuationRunner

logger = logging.getLogger(__name__)


class MonteCarloRunner:
    """Orchestrates the stochastic simulation lifecycle."""

    def __init__(self, strategy: IValuationRunner):
        self.strategy = strategy

    def execute(self, params: Parameters, financials: Company) -> MCResults | None:
        mc_cfg = params.extensions.monte_carlo
        if not mc_cfg or not mc_cfg.enabled:
            return None

        num_simulations = mc_cfg.iterations or MonteCarloDefaults.DEFAULT_SIMULATIONS
        seed = mc_cfg.random_seed if mc_cfg.random_seed is not None else 42

        # 1. Establish Baselines & Economic Guardrails
        # --------------------------------------------
        r = params.common.rates

        # Fallback logic for Risk Free / MRP if missing
        rf = r.risk_free_rate if r.risk_free_rate is not None else MacroDefaults.DEFAULT_RISK_FREE_RATE
        mrp = r.market_risk_premium if r.market_risk_premium is not None else MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM

        # Handle Beta
        fin_beta = getattr(financials, "beta", None)
        beta_base = r.beta if r.beta is not None else (fin_beta or ModelDefaults.DEFAULT_BETA)

        # --- MERGE: Robust WACC Calculation (From Remote Agent) ---
        # We calculate a robust base_wacc to use as a clamping reference for terminal growth.
        try:
            if r.wacc:
                base_wacc = r.wacc
            elif r.cost_of_equity:
                base_wacc = r.cost_of_equity
            else:
                base_wacc = calculate_cost_of_equity_capm(rf, beta_base, mrp)

            if base_wacc <= 0:
                base_wacc = ModelDefaults.DEFAULT_WACC
        except (ArithmeticError, TypeError, ValueError) as e:
            logger.warning(f"Failed to calculate base WACC for MC clamping, using default: {e}")
            base_wacc = ModelDefaults.DEFAULT_WACC

        # --- FIX: Dynamic Calculation of Weights & Cost of Debt (Local Fix) ---
        # Essential to avoid AttributeError on 'weight_equity' which doesn't exist in params.
        cap = params.common.capital
        shares = cap.shares_outstanding or 0.0
        price = params.structure.current_price or 0.0

        equity_val = shares * price
        debt_val = cap.total_debt or 0.0
        total_val = equity_val + debt_val

        if total_val > 0:
            weight_e = equity_val / total_val
            weight_d = debt_val / total_val
        else:
            weight_e = 0.80  # Fallback
            weight_d = 0.20

        # Calculate Kd Post-Tax dynamically
        kd_pre_tax = r.cost_of_debt if r.cost_of_debt is not None else 0.05
        tax_rate = r.tax_rate if r.tax_rate is not None else 0.25
        kd_post_tax = kd_pre_tax * (1 - tax_rate)
        # -----------------------------------------------------------

        # 2. Generate Stochastic Vectors (NumPy)
        # --------------------------------------
        vectors = self._generate_vectors(params, num_simulations, seed, base_beta=beta_base, base_wacc=base_wacc)

        # 3. Vectorized WACC Calculation
        # ------------------------------
        # Ke_vec = Rf + Beta_vec * MRP
        ke_vec = rf + vectors["beta"] * mrp

        # WACC_vec = Ke_vec * We + Kd * Wd
        wacc_vec = ke_vec * weight_e + kd_post_tax * weight_d

        # Add WACC to vectors bundle for strategy use
        vectors["wacc"] = wacc_vec

        # 4. Fast-Path Execution
        # ----------------------
        if hasattr(self.strategy, "execute_stochastic"):
            sim_values_array = self.strategy.execute_stochastic(financials, params, vectors)
        else:
            # Fallback for strategies not yet optimized (Legacy Loop)
            logger.warning(
                f"Strategy {type(self.strategy).__name__} does not support vectorization. Falling back to slow loop."
            )
            sim_values_array = self._run_legacy_loop(financials, params, vectors, num_simulations)

        # 5. Filtering & Result Packaging
        # -------------------------------
        valid_values = sim_values_array[np.isfinite(sim_values_array)]
        valid_values = valid_values[(valid_values > 0) & (valid_values < 1_000_000)]  # Sanity bounds

        if len(valid_values) == 0:
            return None

        return MCResults(
            simulation_values=valid_values.tolist(),
            quantiles={
                "P10": float(np.percentile(valid_values, 10)),
                "P50": float(np.percentile(valid_values, 50)),
                "P90": float(np.percentile(valid_values, 90)),
            },
            mean=float(np.mean(valid_values)),
            std_dev=float(np.std(valid_values)),
        )

    @staticmethod
    def _generate_vectors(
        params: Parameters, n_sims: int, seed: int, base_beta: float, base_wacc: float
    ) -> dict[str, np.ndarray]:
        """Generates all random vectors in one go using NumPy Generator."""
        rng = np.random.default_rng(seed)
        shocks = params.extensions.monte_carlo.shocks

        # Volatilities
        sig_beta = getattr(shocks, "beta_volatility", 0.10) or 0.10
        sig_growth = getattr(shocks, "growth_volatility", 0.015) or 0.015
        sig_flow = getattr(shocks, "fcf_volatility", 0.10) or 0.10

        # 1. Beta Vector (Normal)
        betas = rng.normal(base_beta, base_beta * sig_beta, n_sims)

        # 2. Growth Vector (Normal)
        st = params.strategy
        base_g = getattr(st, "growth_rate_p1", 0.05) or 0.05
        growths = rng.normal(base_g, sig_growth, n_sims)

        # 3. Terminal Growth Vector (Normal, Clipped)
        base_gn = 0.02
        if hasattr(st, "terminal_value"):
            base_gn = st.terminal_value.perpetual_growth_rate or 0.02

        term_growths = rng.normal(base_gn, 0.005, n_sims)
        # Clip g_n to be < WACC - epsilon (Guardrail)
        term_growths = np.minimum(term_growths, base_wacc - 0.01)

        # 4. Base Flow Shock Vector (Normal centered on 1.0)
        base_flow_mults = rng.normal(1.0, sig_flow, n_sims)
        anchor_val = getattr(st, "fcf_anchor", None) or getattr(st, "revenue_ttm", 0.0) or 100.0
        base_flows = anchor_val * base_flow_mults

        return {"beta": betas, "growth": growths, "terminal_growth": term_growths, "base_flow": base_flows}

    def _run_legacy_loop(self, financials, params, vectors, num_sims):
        """Fallback method for non-vectorized strategies."""
        results = []
        self.strategy.glass_box_enabled = False

        betas = vectors["beta"]
        growths = vectors["growth"]

        for i in range(num_sims):
            try:
                s_par = params.model_copy(deep=True)

                # Apply Shocks
                if s_par.common.rates:
                    s_par.common.rates.beta = float(betas[i])

                # Crude injection with safety checks
                if hasattr(s_par.strategy, "growth_rate_p1"):
                    s_par.strategy.growth_rate_p1 = float(growths[i])
                elif hasattr(s_par.strategy, "growth_rate"):
                    s_par.strategy.growth_rate = float(growths[i])
                elif hasattr(s_par.strategy, "revenue_growth_rate"):
                    s_par.strategy.revenue_growth_rate = float(growths[i])

                res = self.strategy.execute(financials, s_par)
                iv = res.results.common.intrinsic_value_per_share

                if 0 < iv < 1_000_000:
                    results.append(iv)

            except (CalculationError, ValueError, AttributeError, ZeroDivisionError):
                continue

        self.strategy.glass_box_enabled = True
        return np.array(results)
