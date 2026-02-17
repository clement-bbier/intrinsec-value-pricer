"""
src/valuation/strategies/standard_fcff.py

STANDARD FCFF STRATEGY RUNNER
=============================
Role: Core DCF Engine using Free Cash Flow to Firm.
Logic: Projects FCF, calculates Terminal Value, Discounts to PV, Bridges to Equity.
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import cast

import numpy as np

from src.computation.financial_math import calculate_discount_factors

# Config
from src.config.constants import ModelDefaults
from src.models.company import Company
from src.models.enums import ValuationMethodology
from src.models.glass_box import CalculationStep
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import FCFFStandardParameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import FCFFStandardResults

# Models Results (Nested Architecture)
from src.models.valuation import ValuationRequest, ValuationResult

# Libraries (DRY Logic)
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner


class StandardFCFFStrategy(IValuationRunner):
    """
    The workhorse of valuation: Discounted Free Cash Flow to Firm.
    Supports both 'Simple Fade-Down' (Auto) and 'Explicit Vector' (Expert) modes.
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
        Executes the DCF Standard sequence (Single Run).
        """
        # Type narrowing for mypy
        strategy_params = cast(FCFFStandardParameters, params.strategy)

        steps: list[CalculationStep] = []

        # --- STEP 1: WACC & Rates ---
        wacc, step_wacc = CommonLibrary.resolve_discount_rate(
            financials=financials, params=params, use_cost_of_equity_only=False
        )
        if self._glass_box:
            steps.append(step_wacc)

        # --- STEP 2: FCF Projection ---
        fcf_base = strategy_params.fcf_anchor or getattr(financials, "fcf_ttm", None) or ModelDefaults.DEFAULT_FCF_TTM
        manual_vector = getattr(params.strategy, "manual_growth_vector", None)

        if manual_vector and len(manual_vector) > 0:
            flows, step_proj = DCFLibrary.project_flows_manual(fcf_base, manual_vector)
        else:
            flows, step_proj = DCFLibrary.project_flows_simple(fcf_base, params)

        if self._glass_box:
            steps.append(step_proj)

        # --- STEP 3: Terminal Value ---
        final_flow = flows[-1] if flows else fcf_base
        tv, step_tv = DCFLibrary.compute_terminal_value(final_flow, wacc, params, financials)
        if self._glass_box:
            steps.append(step_tv)

        # --- STEP 4: Discounting ---
        ev, step_ev = DCFLibrary.compute_discounting(flows, tv, wacc)
        if self._glass_box:
            steps.append(step_ev)

        # --- STEP 5: Equity Bridge ---
        equity_value, step_bridge = CommonLibrary.compute_equity_bridge(ev, params)
        if self._glass_box:
            steps.append(step_bridge)

        # --- STEP 6: Per Share ---
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(equity_value, params)
        if self._glass_box:
            steps.append(step_iv)

        # --- RESULT CONSTRUCTION ---
        r = params.common.rates
        trace_ke = step_wacc.get_variable("Ke")
        trace_kd = step_wacc.get_variable("Kd(1-t)")

        val_ke = trace_ke.value if (self._glass_box and trace_ke) else (r.cost_of_equity or 0.0)
        val_kd = (
            trace_kd.value
            if (self._glass_box and trace_kd)
            else (ModelDefaults.DEFAULT_COST_OF_DEBT * (1 - (r.tax_rate or 0.25)))
        )

        res_rates = ResolvedRates(cost_of_equity=val_ke, cost_of_debt_after_tax=val_kd, wacc=wacc)

        shares = params.common.capital.shares_outstanding or ModelDefaults.DEFAULT_SHARES_OUTSTANDING
        price = financials.current_price or 0.0

        debt = params.common.capital.total_debt or 0.0
        cash = params.common.capital.cash_and_equivalents or 0.0

        res_capital = ResolvedCapital(
            market_cap=shares * price,
            enterprise_value=ev,
            net_debt_resolved=debt - cash,
            equity_value_total=equity_value,
        )

        upside = (iv_per_share - price) / price if price > 0 else 0.0

        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=upside,
            bridge_trace=steps if self._glass_box else [],
        )

        discount_factors = calculate_discount_factors(wacc, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0
        tv_weight = pv_tv / ev if ev > 0 else 0.0

        strategy_res = FCFFStandardResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=tv_weight,
            strategy_trace=[],
        )

        return ValuationResult(
            request=ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params),
            results=Results(common=common_res, strategy=strategy_res, extensions=ExtensionBundleResults()),
        )

    @staticmethod
    def execute_stochastic(_financials: Company, params: Parameters, vectors: dict[str, np.ndarray]) -> np.ndarray:
        """
        High-Performance Vectorized Execution for Monte Carlo.

        Instead of looping through objects, this method uses NumPy algebra to compute
        10,000 valuations in a single CPU cycle.

        Parameters
        ----------
        _financials : Company
            Static financial data (Unused in FCFF Standard as params contains all resolved inputs).
            Prefix '_' indicates intentional non-use to satisfy the interface contract.
        params : Parameters
            Static parameters (Tax rate, Years).
        vectors : Dict[str, np.ndarray]
            Dictionary containing stochastic arrays:
            - 'wacc': Cost of capital vector.
            - 'growth': Phase 1 growth rate vector.
            - 'terminal_growth': Perpetual growth vector.
            - 'base_flow': Initial FCF vector.

        Returns
        -------
        np.ndarray
            Array of Intrinsic Values per Share.
        """
        # 1. Unpack Vectors (All shape: [N_SIMS])
        wacc = vectors["wacc"]
        g_p1 = vectors["growth"]
        g_n = vectors["terminal_growth"]
        fcf_0 = vectors["base_flow"]

        # 2. Vectorized Projection (Phase 1)
        # We assume a fixed projection period (e.g. 5 years) for all sims to allow matrix operations
        years = getattr(params.strategy, "projection_years", 5) or 5

        # Create a time matrix [N_SIMS, YEARS] -> e.g. [1, 2, 3, 4, 5]
        # (1 + g)^t
        time_exponents = np.arange(1, years + 1)

        # Growth factors matrix: [N_SIMS, YEARS]
        # We use outer product or broadcasting
        # flows[i, t] = fcf_0[i] * (1 + g_p1[i])^t
        growth_factors = (1 + g_p1)[:, np.newaxis] ** time_exponents
        projected_flows = fcf_0[:, np.newaxis] * growth_factors

        # 3. Vectorized Discounting
        # Discount factors: 1 / (1 + wacc)^t
        discount_factors = 1.0 / ((1 + wacc)[:, np.newaxis] ** time_exponents)

        # PV of Explicit Flows: Sum(Flow * Discount) along time axis
        pv_explicit = np.sum(projected_flows * discount_factors, axis=1)

        # 4. Vectorized Terminal Value
        # TV = FCF_n * (1 + g_n) / (wacc - g_n)
        final_flow = projected_flows[:, -1]

        # Safety guardrail: Ensure wacc > g_n to avoid infinity/negatives
        # We clip the denominator to a small epsilon
        denominator = np.maximum(wacc - g_n, 0.001)

        tv_nominal = final_flow * (1 + g_n) / denominator

        # Discount TV back to T0: TV / (1 + wacc)^N
        pv_tv = tv_nominal / ((1 + wacc) ** years)

        # 5. Enterprise Value
        ev = pv_explicit + pv_tv

        # 6. Equity Bridge (Vectorized)
        # Equity = EV + Cash - Debt
        # Note: Debt/Cash are scalars here (unless we shock them, but usually we shock Ops/Rates)
        shares = params.common.capital.shares_outstanding or 1.0
        debt = params.common.capital.total_debt or 0.0
        cash = params.common.capital.cash_and_equivalents or 0.0
        net_debt = debt - cash

        equity_value = ev - net_debt

        # 7. Intrinsic Value Per Share
        iv_per_share = equity_value / shares

        return iv_per_share
