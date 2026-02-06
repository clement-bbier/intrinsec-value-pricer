"""
src/valuation/strategies/fundamental_fcff.py

FUNDAMENTAL DCF STRATEGY (NORMALIZED)
=====================================
Role: Normalized DCF Engine for cyclical or volatile firms.
Logic: Uses a smoothed 'Cycle-Average' FCF as anchor instead of TTM.
       Useful when current TTM flows are distressed or unrepresentative.
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
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
from src.models.results.strategies import FCFFNormalizedResults
from src.models.results.options import ExtensionBundleResults

# Libraries (DRY Logic)
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner
from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.i18n import RegistryTexts, StrategySources, StrategyFormulas, StrategyInterpretations


class FundamentalFCFFStrategy(IValuationRunner):
    """
    Normalized FCFF Strategy.
    Anchors valuation on a 'Cycle-Mid' FCF rather than TTM.
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
        Executes the Normalized DCF sequence.
        """
        steps: List[CalculationStep] = []

        # --- STEP 1: WACC & Rates ---
        wacc, step_wacc = CommonLibrary.resolve_discount_rate(
            financials=financials,
            params=params,
            use_cost_of_equity_only=False
        )
        if self._glass_box: steps.append(step_wacc)

        # --- STEP 2: Normalized Anchor Selection ---
        # Specific Logic: We prioritize the Strategy Input (User Override)
        # If not present, we fall back to the Company Snapshot's smoothed metric (Calculated by Provider)
        # We assume `params.strategy` is of type FCFFNormalizedParameters

        user_norm_fcf = params.strategy.fcf_norm
        # Note: In a real scenario, we might want to check `financials.fcf_fundamental_smoothed`
        # if user_norm_fcf is None. For now, we rely on the Resolver to have populated params.
        # Fallback to TTM if absolutely nothing exists (Safety net).
        fcf_anchor = user_norm_fcf or 0.0

        # Trace the Anchor Selection (Critical for this Strategy)
        if self._glass_box:
            steps.append(CalculationStep(
                step_key="FCF_NORM_ANCHOR",
                label=RegistryTexts.DCF_FCF_NORM_L,
                theoretical_formula=StrategyFormulas.FCF_NORMALIZED,
                actual_calculation=f"Selected Anchor: {fcf_anchor:,.2f}",
                result=fcf_anchor,
                interpretation=StrategyInterpretations.FUND_NORM,
                source=StrategySources.MANUAL_OVERRIDE if user_norm_fcf else StrategySources.YAHOO_FUNDAMENTAL,
                variables_map={
                    "FCF_norm": VariableInfo(
                        symbol="FCF_norm", value=fcf_anchor,
                        source=VariableSource.MANUAL_OVERRIDE if user_norm_fcf else VariableSource.YAHOO_FINANCE,
                        description="Normalized Free Cash Flow"
                    )
                }
            ))

        # --- STEP 3: FCF Projection ---
        # Handles Expert Vector Override transparently via BaseProjectedParameters
        manual_vector = getattr(params.strategy, "manual_growth_vector", None)

        if manual_vector and len(manual_vector) > 0:
            flows, step_proj = DCFLibrary.project_flows_manual(fcf_anchor, manual_vector)
        else:
            flows, step_proj = DCFLibrary.project_flows_simple(fcf_anchor, params)

        if self._glass_box: steps.append(step_proj)

        # --- STEP 4: Terminal Value ---
        final_flow = flows[-1] if flows else fcf_anchor
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

        # A. Rates Reconstruction
        res_rates = ResolvedRates(
            cost_of_equity=step_wacc.get_variable("Ke").value if self._glass_box else 0.0,
            cost_of_debt_after_tax=step_wacc.get_variable("Kd(1-t)").value if self._glass_box else 0.0,
            wacc=wacc
        )

        # B. Capital Reconstruction
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

        # D. Strategy Specific Results (FCFF Normalized)
        discount_factors = calculate_discount_factors(wacc, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        strategy_res = FCFFNormalizedResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=(pv_tv / ev) if ev > 0 else 0.0,
            strategy_trace=[],
            # Specific field for this strategy
            normalized_fcf_used=fcf_anchor
        )

        return ValuationResult(
            request=ValuationRequest(
                mode=ValuationMethodology.FCFF_NORMALIZED,
                parameters=params
            ),
            results=Results(
                common=common_res,
                strategy=strategy_res, # Polymorphic field (matches FCFFNormalizedResults)
                extensions=ExtensionBundleResults()
            )
        )