"""
src/valuation/strategies/fcfe.py

FREE CASH FLOW TO EQUITY (FCFE) STRATEGY RUNNER
===============================================
Role: Direct Equity Valuation engine.
Academic Reference: Damodaran (Category 2: Leveraged Firms / Banks).
Logic: Discounts flows available to shareholders (after debt service) at Cost of Equity (Ke).
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import List

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import ValuationMethodology, VariableSource

# Models Results
from src.models.valuation import ValuationResult, ValuationRequest
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedRates, ResolvedCapital
from src.models.results.strategies import FCFEResults
from src.models.results.options import ExtensionBundleResults

# Libraries
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner
from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.i18n import RegistryTexts, StrategySources, StrategyFormulas, StrategyInterpretations, KPITexts


class FCFEStrategy(IValuationRunner):
    """
    FCFE Strategy (Direct Equity).
    Ideal for: Financial Services, Highly Leveraged Firms, or Stable Debt Ratio firms.
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
        Executes FCFE valuation sequence.
        Note: Discounts at Ke, not WACC.
        """
        steps: List[CalculationStep] = []

        # --- STEP 1: Rate Resolution (Ke ONLY) ---
        # FCFE requires Cost of Equity, not WACC.
        ke, step_ke = CommonLibrary.resolve_discount_rate(
            financials=financials,
            params=params,
            use_cost_of_equity_only=True # Crucial Flag
        )
        if self._glass_box: steps.append(step_ke)

        # --- STEP 2: Anchor Selection ---
        # The Resolver has already populated 'fcfe_anchor' in FCFEParameters.
        # This typically comes from: Net Income + D&A - Capex - dWCR + Net Borrowing
        fcfe_base = params.strategy.fcfe_anchor or 0.0

        if self._glass_box:
            steps.append(CalculationStep(
                step_key="FCFE_ANCHOR",
                label=RegistryTexts.FCFE_BASE_L,
                theoretical_formula=StrategyFormulas.FCFE_RECONSTRUCTION,
                actual_calculation=f"Starting FCFE: {fcfe_base:,.2f}",
                result=fcfe_base,
                interpretation=StrategyInterpretations.FCFE_LOGIC,
                source=StrategySources.SYSTEM,
                variables_map={
                    "FCFE_0": VariableInfo(
                        symbol="FCFE_0", value=fcfe_base,
                        source=VariableSource.SYSTEM, description="Base Year Free Cash Flow to Equity"
                    )
                }
            ))

        # --- STEP 3: Projection ---
        # Checks for manual vector overrides in params
        manual_vector = getattr(params.strategy, "manual_growth_vector", None)

        if manual_vector and len(manual_vector) > 0:
            flows, step_proj = DCFLibrary.project_flows_manual(fcfe_base, manual_vector)
        else:
            flows, step_proj = DCFLibrary.project_flows_simple(fcfe_base, params)

        if self._glass_box: steps.append(step_proj)

        # --- STEP 4: Terminal Value ---
        final_flow = flows[-1] if flows else fcfe_base
        # Important: TV is calculated using Ke, not WACC
        tv, step_tv = DCFLibrary.compute_terminal_value(final_flow, ke, params)
        if self._glass_box: steps.append(step_tv)

        # --- STEP 5: Discounting ---
        # Discount at Ke. Result is PV of Equity (Operating).
        pv_equity, step_ev = DCFLibrary.compute_discounting(flows, tv, ke)
        if self._glass_box: steps.append(step_ev)

        # --- STEP 6: Total Equity Value (No Debt Substraction) ---
        # For FCFE: Total Equity = PV(FCFE) + Non-Operating Assets (Cash)
        # We DO NOT subtract Debt (it's already serviced in the flows).

        cash = params.common.capital.cash_and_equivalents or 0.0
        total_equity_value = pv_equity + cash

        if self._glass_box:
            steps.append(CalculationStep(
                step_key="FCFE_EQUITY_SUM",
                label=RegistryTexts.FCFE_EQUITY_VALUE,
                theoretical_formula="Equity = PV(FCFE) + Cash",
                actual_calculation=f"{pv_equity:,.0f} + {cash:,.0f}",
                result=total_equity_value,
                interpretation="Adding non-operating cash to operating equity value.",
                source=StrategySources.CALCULATED,
                variables_map={
                    "PV_FCFE": VariableInfo(symbol="PV", value=pv_equity, source=VariableSource.CALCULATED),
                    "Cash": VariableInfo(symbol="Cash", value=cash, source=VariableSource.SYSTEM, description=KPITexts.LABEL_CASH)
                }
            ))

        # --- STEP 7: Per Share ---
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(total_equity_value, params)
        if self._glass_box: steps.append(step_iv)

        # --- RESULT CONSTRUCTION ---

        # A. Rates
        res_rates = ResolvedRates(
            cost_of_equity=ke,
            cost_of_debt_after_tax=0.0, # Not relevant for discounting FCFE
            wacc=ke # Effectively acts as the discount rate here
        )

        # B. Capital (Reverse engineered for consistency in UI)
        # We derived Equity directly. EV = Equity + Debt - Cash
        debt = params.common.capital.total_debt or 0.0
        implied_ev = total_equity_value + debt - cash

        shares = params.common.capital.shares_outstanding or 1.0
        res_capital = ResolvedCapital(
            market_cap=shares * (financials.current_price or 0.0),
            enterprise_value=implied_ev, # Calculated backwards for FCFE
            net_debt_resolved=debt - cash,
            equity_value_total=total_equity_value
        )

        # C. Common Results
        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=((iv_per_share - (financials.current_price or 0.0)) / (financials.current_price or 1.0)) if financials.current_price else 0.0,
            bridge_trace=steps if self._glass_box else []
        )

        # D. Strategy Specific
        discount_factors = calculate_discount_factors(ke, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        strategy_res = FCFEResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=(pv_tv / pv_equity) if pv_equity > 0 else 0.0,
            strategy_trace=[],
            projected_net_borrowing=[] # Not projected in simplified FCFE
        )

        return ValuationResult(
            request=ValuationRequest(
                mode=ValuationMethodology.FCFE,
                parameters=params
            ),
            results=Results(
                common=common_res,
                strategy=strategy_res,
                extensions=ExtensionBundleResults()
            )
        )