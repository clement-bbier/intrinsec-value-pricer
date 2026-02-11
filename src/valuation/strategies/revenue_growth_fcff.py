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

from typing import List

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import ValuationMethodology, VariableSource

# Models Results (Nested Architecture)
from src.models.valuation import ValuationResult, ValuationRequest
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedRates, ResolvedCapital
from src.models.results.strategies import FCFFGrowthResults
from src.models.results.options import ExtensionBundleResults

# Libraries (DRY Logic)
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner
from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.config.constants import ModelDefaults
from src.i18n import RegistryTexts, StrategySources, StrategyFormulas, StrategyInterpretations


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
        steps: List[CalculationStep] = []

        # --- STEP 1: WACC & Rates ---
        wacc, step_wacc = CommonLibrary.resolve_discount_rate(
            financials=financials,
            params=params,
            use_cost_of_equity_only=False
        )
        if self._glass_box: steps.append(step_wacc)

        # --- STEP 2: Revenue Anchor Selection ---
        # Prioritize User Input (from Strategy Params) > TTM (Snapshot)
        user_rev = params.strategy.revenue_ttm
        rev_anchor = user_rev if user_rev is not None else (financials.revenue_ttm or 0.0)

        # Calculate Current Implied Margin (for the convergence start point)
        # Note: We use TTM FCF and Revenue. Be careful with negative values.
        fcf_ttm = financials.fcf_ttm or 0.0
        current_margin = (fcf_ttm / rev_anchor) if rev_anchor > 0 else 0.0

        # Target Margin (User Input required for this model usually, else default)
        target_margin = params.strategy.target_fcf_margin or ModelDefaults.DEFAULT_FCF_MARGIN_TARGET

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

        # --- STEP 3: Projection (Revenue & Margin Model) ---
        # Note: manual_growth_vector in params applies to REVENUE growth in this context
        flows, revenues, margins, step_proj = DCFLibrary.project_flows_revenue_model(
            base_revenue=rev_anchor,
            current_margin=current_margin,
            target_margin=target_margin,
            params=params
        )

        if self._glass_box: steps.append(step_proj)

        # --- STEP 4: Terminal Value ---
        # Uses the last projected FCF
        final_flow = flows[-1] if flows else 0.0
        tv, step_tv = DCFLibrary.compute_terminal_value(final_flow, wacc, params)
        if self._glass_box: steps.append(step_tv)

        # --- STEP 5: Discounting ---
        ev, step_ev = DCFLibrary.compute_discounting(flows, tv, wacc)
        if self._glass_box: steps.append(step_ev)

        # --- STEP 6: Equity Bridge ---
        equity_value, step_bridge = CommonLibrary.compute_equity_bridge(ev, params)
        if self._glass_box: steps.append(step_bridge)

        # --- STEP 7: Per Share ---
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(equity_value, params)
        if self._glass_box: steps.append(step_iv)

        # --- RESULT CONSTRUCTION ---

        # A. Rates
        res_rates = ResolvedRates(
            cost_of_equity=step_wacc.get_variable("Ke").value if self._glass_box else 0.0,
            cost_of_debt_after_tax=step_wacc.get_variable("Kd(1-t)").value if self._glass_box else 0.0,
            wacc=wacc
        )

        # B. Capital
        shares = params.common.capital.shares_outstanding or 1.0
        res_capital = ResolvedCapital(
            market_cap=shares * (financials.current_price or 0.0),
            enterprise_value=ev,
            net_debt_resolved=(params.common.capital.total_debt or 0.0) - (params.common.capital.cash_and_equivalents or 0.0),
            equity_value_total=equity_value
        )

        # C. Common Results
        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=((iv_per_share - (financials.current_price or 0.0)) / (financials.current_price or 1.0)) if financials.current_price else 0.0,
            bridge_trace=steps if self._glass_box else []
        )

        # D. Strategy Specific Results (FCFF Growth)
        discount_factors = calculate_discount_factors(wacc, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        strategy_res = FCFFGrowthResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=(pv_tv / ev) if ev > 0 else 0.0,
            strategy_trace=[],
            # Specific fields for Charting
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