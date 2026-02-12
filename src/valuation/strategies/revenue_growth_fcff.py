"""
src/valuation/strategies/revenue_growth_fcff.py

REVENUE-DRIVEN GROWTH STRATEGY RUNNER
=====================================
Role: DCF Engine for high-growth or turnaround firms.
Logic: Projects Revenue -> Converges Margins -> Derives FCF.
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).

Warning
-------
This model uses a simplified approach: FCF_t = Revenue_t × Margin_t.
This assumes the margin already incorporates all operating adjustments
(working capital changes, capex, D&A, tax shield, etc.). For more
granular modeling, use the standard FCFF strategy with explicit
adjustments.
"""

from __future__ import annotations

from typing import cast

import numpy as np

from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.config.constants import ModelDefaults
from src.i18n import RegistryTexts, StrategyFormulas, StrategyInterpretations, StrategySources
from src.models.company import Company
from src.models.enums import ValuationMethodology, VariableSource
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import FCFFGrowthParameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import FCFFGrowthResults

# Models Results (Nested Architecture)
from src.models.valuation import ValuationRequest, ValuationResult

# Libraries (DRY Logic)
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner


class RevenueGrowthFCFFStrategy(IValuationRunner):
    """
    Revenue-Based DCF Strategy.
    Ideal for: Startups, High-Growth Tech, Turnarounds (Negative current margins).
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
        Executes the Revenue-Driven DCF sequence.
        """
        # Type narrowing pour mypy
        strategy_params = cast(FCFFGrowthParameters, params.strategy)

        steps: list[CalculationStep] = []

        # --- STEP 1: WACC & Rates ---
        wacc, step_wacc = CommonLibrary.resolve_discount_rate(
            financials=financials,
            params=params,
            use_cost_of_equity_only=False
        )
        if self._glass_box:
            steps.append(step_wacc)

        # --- STEP 2: Revenue Anchor Selection ---
        user_rev = strategy_params.revenue_ttm
        # Use getattr for Company fields that may not be defined in type annotation
        rev_anchor = user_rev if user_rev is not None else (getattr(financials, 'revenue_ttm', None) or 0.0)

        fcf_ttm = getattr(financials, 'fcf_ttm', None) or 0.0
        current_margin = (fcf_ttm / rev_anchor) if rev_anchor > 0 else 0.0
        target_margin = strategy_params.target_fcf_margin or ModelDefaults.DEFAULT_FCF_MARGIN_TARGET

        if self._glass_box:
            steps.append(CalculationStep(
                step_key="GROWTH_ANCHORS",
                label=RegistryTexts.GROWTH_REV_BASE_L,
                theoretical_formula=StrategyFormulas.REVENUE_BASE,
                actual_calculation=f"Rev: {rev_anchor:,.0f} | Margin: {current_margin:.1%} -> {target_margin:.1%}",
                result=rev_anchor,
                interpretation=StrategyInterpretations.GROWTH_REV,
                source=StrategySources.MANUAL_OVERRIDE if user_rev else StrategySources.YAHOO_TTM_SIMPLE,
                variables_map={
                    "Rev_0": VariableInfo(symbol="Rev_0", value=rev_anchor, source=VariableSource.SYSTEM),
                    "M_0": VariableInfo(symbol="M_0", value=current_margin, source=VariableSource.CALCULATED)
                }
            ))

        # --- STEP 3: Projection ---
        flows, revenues, margins, step_proj = DCFLibrary.project_flows_revenue_model(
            base_revenue=rev_anchor,
            current_margin=current_margin,
            target_margin=target_margin,
            params=params
        )

        if self._glass_box:
            steps.append(step_proj)

        # --- STEP 4: Terminal Value ---
        final_flow = flows[-1] if flows else 0.0
        tv, step_tv = DCFLibrary.compute_terminal_value(final_flow, wacc, params)
        if self._glass_box:
            steps.append(step_tv)

        # --- STEP 5: Discounting ---
        ev, step_ev = DCFLibrary.compute_discounting(flows, tv, wacc)
        if self._glass_box:
            steps.append(step_ev)

        # --- STEP 6: Equity Bridge ---
        equity_value, step_bridge = CommonLibrary.compute_equity_bridge(ev, params)
        if self._glass_box:
            steps.append(step_bridge)

        # --- STEP 7: Per Share ---
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(equity_value, params)
        if self._glass_box:
            steps.append(step_iv)

        # --- RESULT CONSTRUCTION ---
        ke_var = step_wacc.get_variable("Ke")
        kd_var = step_wacc.get_variable("Kd(1-t)")

        res_rates = ResolvedRates(
            cost_of_equity=ke_var.value if ke_var and self._glass_box else 0.0,
            cost_of_debt_after_tax=kd_var.value if kd_var and self._glass_box else 0.0,
            wacc=wacc
        )

        shares = params.common.capital.shares_outstanding or 1.0
        res_capital = ResolvedCapital(
            market_cap=shares * (financials.current_price or 0.0),
            enterprise_value=ev,
            net_debt_resolved=(
                (params.common.capital.total_debt or 0.0)
                - (params.common.capital.cash_and_equivalents or 0.0)
            ),
            equity_value_total=equity_value
        )

        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=(
                ((iv_per_share - (financials.current_price or 0.0)) / (financials.current_price or 1.0))
                if financials.current_price else 0.0
            ),
            bridge_trace=steps if self._glass_box else []
        )

        discount_factors = calculate_discount_factors(wacc, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        strategy_res = FCFFGrowthResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=(pv_tv / ev) if ev > 0 else 0.0,
            strategy_trace=[],
            projected_revenues=revenues,
            projected_margins=margins,
            target_margin_reached=margins[-1] if margins else target_margin
        )

        return ValuationResult(
            request=ValuationRequest(
                mode=ValuationMethodology.FCFF_GROWTH,
                parameters=params
            ),
            results=Results(
                common=common_res,
                strategy=strategy_res,
                extensions=ExtensionBundleResults()
            )
        )

    @staticmethod
    def execute_stochastic(financials: Company, params: Parameters, vectors: dict[str, np.ndarray]) -> np.ndarray:
        """
        Vectorized Revenue-Growth DCF Execution for Monte Carlo.

        Logic:
        1. Project Revenue (using shocked base_flow and growth vector).
        2. Apply Margin Curve (Linear convergence from current to target).
        3. FCF = Revenue * Margin.
        4. Discount.
        """
        # 1. Unpack Vectors
        wacc = vectors['wacc']
        g_p1 = vectors['growth'] # Revenue Growth
        g_n  = vectors['terminal_growth']
        rev_0 = vectors['base_flow'] # Shocked Revenue TTM

        # 2. Resolve Margins (Static Profile applied to Dynamic Revenue)
        # We need to construct the margin curve [Years]
        strategy_params = cast(FCFFGrowthParameters, params.strategy)
        years = strategy_params.projection_years or 5

        # Current Margin (Scalar)
        # We use TTM values from financials as the anchor for margin calculation
        # This keeps the margin profile consistent with the fundamental view
        base_rev_static = getattr(financials, 'revenue_ttm', None) or 1.0
        fcf_ttm = getattr(financials, 'fcf_ttm', None) or 0.0
        current_margin = fcf_ttm / base_rev_static

        target_margin = strategy_params.target_fcf_margin or ModelDefaults.DEFAULT_FCF_MARGIN_TARGET

        # Create Margin Vector [Years] via linear interpolation
        # shape: (Years,) e.g. [0.12, 0.14, 0.16, 0.18, 0.20]
        margin_curve = np.linspace(current_margin, target_margin, years + 1)[1:] # Skip index 0 (current)

        # 3. Vectorized Revenue Projection
        time_exponents = np.arange(1, years + 1)

        # Revenue Factors [N_SIMS, YEARS]
        growth_factors = (1 + g_p1)[:, np.newaxis] ** time_exponents
        projected_revenue = rev_0[:, np.newaxis] * growth_factors

        # 4. Derive FCF [N_SIMS, YEARS]
        # Broadcasting: [N, Y] * [Y] -> [N, Y]
        projected_flows = projected_revenue * margin_curve

        # 5. Discounting
        discount_factors = 1.0 / ((1 + wacc)[:, np.newaxis] ** time_exponents)
        pv_explicit = np.sum(projected_flows * discount_factors, axis=1)

        # 6. Terminal Value
        # Uses last year FCF and Revenue Growth? No, Gordon Growth on FCF.
        final_flow = projected_flows[:, -1]
        denominator = np.maximum(wacc - g_n, 0.001)
        tv_nominal = final_flow * (1 + g_n) / denominator
        pv_tv = tv_nominal / ((1 + wacc) ** years)

        # 7. Equity Bridge
        ev = pv_explicit + pv_tv

        shares = params.common.capital.shares_outstanding or 1.0
        net_debt = (params.common.capital.total_debt or 0.0) - (params.common.capital.cash_and_equivalents or 0.0)

        equity_value = ev - net_debt
        iv_per_share: np.ndarray = equity_value / shares

        return iv_per_share
