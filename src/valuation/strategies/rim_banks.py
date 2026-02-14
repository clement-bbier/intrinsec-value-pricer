"""
src/valuation/strategies/rim_banks.py

RESIDUAL INCOME MODEL (RIM) STRATEGY RUNNER
===========================================
Role: Equity Valuation for Financial Institutions.
Academic Reference: Penman / Ohlson.
Logic: Value = Book Value + PV of Residual Incomes (Clean Surplus).
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import cast

import numpy as np

from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.i18n import RegistryTexts, StrategyFormulas, StrategyInterpretations, StrategySources
from src.models.company import Company
from src.models.enums import ValuationMethodology, VariableSource
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import RIMParameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import RIMResults

# Models Results
from src.models.valuation import ValuationRequest, ValuationResult

# Libraries
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary  # Used for Per Share Dilution
from src.valuation.library.rim import RIMLibrary
from src.valuation.strategies.interface import IValuationRunner


class RIMBankingStrategy(IValuationRunner):
    """
    RIM Strategy (Ohlson).
    Ideal for: Banks, Insurance, and firms where Book Value is key.
    Calculates value Per Share directly.
    """

    def __init__(self) -> None:
        self._glass_box: bool = True

    @property
    def glass_box_enabled(self) -> bool:
        return self._glass_box

    @glass_box_enabled.setter
    def glass_box_enabled(self, value: bool) -> None:
        self._glass_box = value

    def execute(self, financials: Company, params: Parameters) -> ValuationResult:
        """
        Executes RIM valuation sequence.
        """
        # Type narrowing for mypy
        strategy_params = cast(RIMParameters, params.strategy)

        steps: list[CalculationStep] = []

        # --- STEP 1: Rate Resolution (Ke ONLY) ---
        # RIM is a Direct Equity method -> Discount at Cost of Equity
        ke, step_ke = CommonLibrary.resolve_discount_rate(
            financials=financials, params=params, use_cost_of_equity_only=True
        )
        if self._glass_box:
            steps.append(step_ke)

        # --- STEP 2: Anchors Selection (BVPS & EPS) ---
        # A. Book Value Per Share (B0)
        # Priority: Strategy Input > TTM Snapshot
        user_bv = strategy_params.book_value_anchor
        bv_anchor = user_bv if user_bv is not None else (getattr(financials, "book_value_ps", None) or 0.0)

        # B. Earnings Per Share (E0)
        # Note: RIMParameters might not have eps_anchor explicit field (inherits from BaseProjectedParameters),
        # but we can check if it exists or fallback to TTM.
        # Ideally, we should add 'eps_anchor' to RIMParameters.
        # Fallback logic: check 'eps_normalized' if Graham params shared, else TTM.
        eps_ttm = getattr(financials, "eps_ttm", None) or 0.0
        # If user overrides net income or EPS via a specific field (to be defined in Model), we use it.
        # Here we use TTM as primary or assume Resolver handled overrides into `eps_ttm` equivalent.
        eps_anchor = eps_ttm

        if self._glass_box:
            steps.append(
                CalculationStep(
                    step_key="RIM_ANCHORS",
                    label=RegistryTexts.RIM_BV_L,
                    theoretical_formula=StrategyFormulas.BV_BASE,
                    actual_calculation=f"BVPS: {bv_anchor:.2f} | EPS: {eps_anchor:.2f}",
                    result=bv_anchor,
                    interpretation=StrategyInterpretations.RIM_BV_D,
                    source=StrategySources.MANUAL_OVERRIDE if user_bv else StrategySources.YAHOO_TTM_SIMPLE,
                    variables_map={
                        "B_0": VariableInfo(symbol="B_0", value=bv_anchor, source=VariableSource.SYSTEM),
                        "E_0": VariableInfo(symbol="E_0", value=eps_anchor, source=VariableSource.SYSTEM),
                    },
                )
            )

        # --- STEP 3: Projection (Clean Surplus) ---
        # Projects RI, BV, and EPS
        ri_flows, bv_flows, eps_flows, step_proj = RIMLibrary.project_residual_income(
            current_book_value=bv_anchor, base_earnings=eps_anchor, cost_of_equity=ke, params=params
        )
        if self._glass_box:
            steps.append(step_proj)

        # --- STEP 4: Terminal Value (Ohlson) ---
        final_ri = ri_flows[-1] if ri_flows else 0.0
        tv, step_tv = RIMLibrary.compute_terminal_value_ohlson(final_ri, ke, params)
        if self._glass_box:
            steps.append(step_tv)

        # --- STEP 5: Aggregation (Total Value) ---
        # Note: The result is directly Value Per Share because inputs were Per Share
        iv_raw, step_agg = RIMLibrary.compute_equity_value(
            current_book_value=bv_anchor, residual_incomes=ri_flows, terminal_value=tv, cost_of_equity=ke
        )
        if self._glass_box:
            steps.append(step_agg)

        # --- STEP 6: Dilution Adjustment ---
        # RIM computes raw equity value. We still need to account for SBC dilution.
        # We reuse DCFLibrary utility for this (Per Share Logic).
        iv_per_share, step_dil = DCFLibrary.compute_value_per_share(
            # Convert to Total for the standard func
            equity_value=iv_raw * (params.common.capital.shares_outstanding or 1.0),
            params=params,
        )
        # Note: compute_value_per_share divides by shares again.
        # Optimization: Call simple dilution utility directly?
        # For consistency, we pass Total Equity to `compute_value_per_share` which handles everything nicely.
        if self._glass_box:
            steps.append(step_dil)

        # --- RESULT CONSTRUCTION ---

        # A. Rates
        res_rates = ResolvedRates(cost_of_equity=ke, cost_of_debt_after_tax=0.0, wacc=ke)

        # B. Capital
        shares = params.common.capital.shares_outstanding or 1.0
        price = financials.current_price or 0.0

        # RIM is direct equity. EV is not primary but we reconstruct a proxy.
        # EV = Equity + Net Debt (Approx)
        equity_total = iv_per_share * shares
        net_debt = (params.common.capital.total_debt or 0.0) - (params.common.capital.cash_and_equivalents or 0.0)

        res_capital = ResolvedCapital(
            market_cap=shares * price,
            enterprise_value=equity_total + net_debt,
            net_debt_resolved=net_debt,
            equity_value_total=equity_total,
        )

        # C. Common Results
        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=((iv_per_share - price) / price) if price > 0 else 0.0,
            bridge_trace=steps if self._glass_box else [],
        )

        # D. Strategy Specific (RIM)
        discount_factors = calculate_discount_factors(ke, len(ri_flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        strategy_res = RIMResults(
            current_book_value=bv_anchor,
            projected_book_values=bv_flows,
            projected_residual_incomes=ri_flows,
            terminal_value_ri=tv,
            discounted_terminal_value=pv_tv,
            strategy_trace=[],
        )

        return ValuationResult(
            request=ValuationRequest(mode=ValuationMethodology.RIM, parameters=params),
            results=Results(common=common_res, strategy=strategy_res, extensions=ExtensionBundleResults()),
        )

    @staticmethod
    def execute_stochastic(financials: Company, params: Parameters, vectors: dict[str, np.ndarray]) -> np.ndarray:
        """
        High-Performance Vectorized Execution for Monte Carlo (RIM).

        Uses recursive vector operations to simulate clean surplus relations
        across projection years for 10,000+ scenarios.

        Parameters
        ----------
        financials : Company
            Source for Book Value / EPS if not overridden.
        params : Parameters
            Valuation settings (Persistence factor, Years).
        vectors : Dict[str, np.ndarray]
            - 'wacc': Cost of Equity (Ke) vector.
            - 'growth': Earnings growth vector.
            - 'base_flow': EPS shock vector (Earnings Power).

        Returns
        -------
        np.ndarray
            Array of Intrinsic Values per Share.
        """
        # Type narrowing for mypy
        strategy_params = cast(RIMParameters, params.strategy)

        # 1. Unpack Vectors
        ke_vec = vectors["wacc"]  # Cost of Equity
        g_p1 = vectors["growth"]  # Growth of EPS/Book

        # 2. Establish Anchors (B0 and EPS0)
        # Note: We use 'financials' here because params might not have the anchor set.
        b0 = strategy_params.book_value_anchor or (getattr(financials, "book_value_ps", None) or 10.0)

        # Base Flow Vector represents the shocked starting Earnings Power (EPS)
        # Assumes vectors['base_flow'] is centered around the TTM EPS or 1.0 multiplier
        eps_vec = vectors["base_flow"]

        # 3. Clean Surplus Recursion
        # We iterate over time (T=5), calculating full vectors at each step.
        years = getattr(params.strategy, "projection_years", 5) or 5
        payout = 0.0  # Conservative assumption: Retain all earnings to grow Book

        # Initialize state vectors [N_SIMS]
        current_b = np.full_like(ke_vec, b0)
        current_eps = eps_vec

        pv_ri_sum = np.zeros_like(ke_vec)

        ri = np.zeros_like(ke_vec)

        for t in range(1, years + 1):
            # A. Project Earnings: EPS_t = EPS_{t-1} * (1 + g)
            current_eps = current_eps * (1 + g_p1)

            # B. Calculate Residual Income: RI_t = EPS_t - (Ke * B_{t-1})
            ri = current_eps - (ke_vec * current_b)

            # C. Discount RI: PV = RI / (1+Ke)^t
            discount_factor = 1.0 / ((1 + ke_vec) ** t)
            pv_ri_sum += ri * discount_factor

            # D. Update Book Value (Clean Surplus): B_t = B_{t-1} + EPS_t - Div_t
            div = current_eps * payout
            current_b = current_b + current_eps - div

        # 4. Terminal Value (Ohlson Persistence)
        # TV = RI_n * omega / (1 + Ke - omega)
        omega = getattr(params.strategy, "persistence_factor", 0.6) or 0.6

        # Guardrail for denominator
        denom = np.maximum(1 + ke_vec - omega, 0.001)

        # Last RI from loop is used here
        tv_nominal = ri * omega / denom
        pv_tv = tv_nominal / ((1 + ke_vec) ** years)

        # 5. Total Value Per Share = B0 + Sum(PV_RI) + PV_TV
        iv_per_share = b0 + pv_ri_sum + pv_tv

        return iv_per_share
